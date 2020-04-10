import logging
import ipaddress
import os
from . import utils


# -------------------------------------------------------------------------------------------------
class Action:
    @classmethod
    def _run(cls, client, config, args):
        return cls(client, config).run(args)

    def __init__(self, client, config):
        self.client = client
        self.config = config

    @classmethod
    def add_arguments(cls, parser):
        pass

    def run(self, args):
        raise NotImplementedError()

    # some helper methods are below
    @property
    def host_ip(self):
        return ipaddress.ip_interface(self.config["net"]["host_ip_mask"]).ip

    @property
    def host_netmask(self):
        return ipaddress.ip_interface(self.config["net"]["host_ip_mask"]).netmask

    @property
    def device_ip(self):
        return ipaddress.ip_address(self.config["net"]["device_ip"])

    def configure_network(self):
        """ Common method to configure network on target device
        """
        self.client.setenv(
            ipaddr=self.device_ip,
            serverip=self.host_ip,
            netmask=self.host_netmask
        )
    
    def upload_files(self, *args):
        utils.upload_files_via_tftp(self.client, args, listen_ip=str(self.host_ip))


def add_actions(parser, *actions):
    subparsers = parser.add_subparsers(title="Action")
    for action in actions:
        action_parser = subparsers.add_parser(action.__name__,
            help=action.__doc__.strip() if action.__doc__ else None
        )
        action.add_arguments(action_parser)
        action_parser.set_defaults(action=action._run)


# -------------------------------------------------------------------------------------------------
class printenv(Action):
    """ Print U-Boot environment variables
    """
    def run(self, args):
        result = self.client.printenv()
        print("\n".join(result))


# -------------------------------------------------------------------------------------------------
class ping(Action):
    """ Configure network on device and ping host
    """
    def run(self, args):
        self.configure_network()
        result = self.client.ping(self.host_ip)[-1]
        if not result.endswith("is alive"):
            raise RuntimeError("network is unavailable")
        print("Network is fine")


# -------------------------------------------------------------------------------------------------
class download(Action):
    """ Download data from device's RAM via TFTP
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--dst", type=str, default="./dump", help="Destination file")
        parser.add_argument("--addr", type=utils.hsize2int, required=True, help="Address to start downloading from")
        parser.add_argument("--size", type=utils.hsize2int, required=True, help="Amount of bytes to be downloaded")

    def run(self, args):
        self.configure_network()
        utils.download_files_via_tftp(self.client, (
            (args.dst, args.addr, args.size),
        ), listen_ip=str(self.host_ip))


# -------------------------------------------------------------------------------------------------
class upload(Action):
    """ Upload data to device's RAM via TFTP
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--src", type=str, required=True, help="File to be uploaded")
        parser.add_argument("--addr", type=utils.hsize2int, required=True, help="Destination address in device's memory")

    def run(self, args):
        self.configure_network()
        self.upload_files((args.src, args.addr))


# -------------------------------------------------------------------------------------------------
class boot(Action):
    """ Upload Kernel and RootFS images into device's RAM and boot it
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--uimage", type=str, required=True, help="Kernel UImage file")
        parser.add_argument("--rootfs", type=str, required=True, help="RootFS image file")
        parser.add_argument("--upload-addr", type=utils.hsize2int,
            help="Start address to upload into")
        parser.add_argument("--initrd-size", type=utils.hsize2int,
            help="Amount of RAM for initrd (actual size of RootFS image file by default)")
        parser.add_argument("--no-wait", action="store_true",
            help="Don't wait end of serial output and exit immediately after sending 'bootm' command")

    def run(self, args):
        self.configure_network()

        uimage_size = os.path.getsize(args.uimage)
        rootfs_size = os.path.getsize(args.rootfs) if args.initrd_size is None else args.initrd_size

        alignment = self.config["mem"]["alignment"]
        if args.upload_addr is None:
            mem_end_addr = self.config["mem"]["start_addr"] + self.config["mem"]["linux_size"]
            rootfs_addr = utils.align_address_down(alignment, mem_end_addr - rootfs_size)
            uimage_addr = utils.align_address_down(alignment, rootfs_addr - uimage_size)
        else:
            uimage_addr = utils.align_address_up(alignment, args.upload_addr)  # to ensure alignment
            rootfs_addr = utils.align_address_up(alignment, uimage_addr + uimage_size)

        logging.info("Kernel uImage upload addr {:#x}; RootFS image upload addr {:#x}".format(
            uimage_addr, rootfs_addr
        ))

        self.upload_files((args.uimage, uimage_addr), (args.rootfs, rootfs_addr))

        bootargs = ""
        bootargs += "mem={} ".format(self.config["mem"]["linux_size"])
        bootargs += "console={} ".format(self.config["linux_console"])
        bootargs += "ip={}:{}:{}:{}:camera1::off; ".format(
            self.device_ip, self.host_ip, self.host_ip, self.host_netmask
        )
        bootargs += "mtdparts=hi_sfc:512k(boot) "
        bootargs += "root=/dev/ram0 ro initrd={:#x},{}".format(rootfs_addr, rootfs_size)

        logging.info("Load kernel with bootargs: {}".format(bootargs))

        self.client.setenv(bootargs=bootargs)
        resp = self.client.bootm(uimage_addr, wait=(not args.no_wait))
        if resp is None:
            print("'bootm' command has been sent. Hopefully booting is going on well...")
        else:
            print(
                "Output ended with next lines:\n" +
                "... {} lines above\n".format(len(resp)) +
                "----------------------------------------\n" +
                "\n".join("  {}".format(l.strip()) for l in resp[-10:]) +
                "\n----------------------------------------"
            )


# -------------------------------------------------------------------------------------------------
class download_sf(Action):
    """ Download data from device's SPI flasg via TFTP
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--probe", type=str, required=True, help="'sf probe' arguments")
        parser.add_argument("--size", type=utils.hsize2int, required=True, help="Amount of bytes to be downloaded")
        parser.add_argument("--offset", type=utils.hsize2int, default=0, help="Flash offset")
        parser.add_argument("--dst", type=str, default="./dump.bin", help="Destination file")
        parser.add_argument("--addr", type=utils.hsize2int, help="Devices's RAM address read data from flash into")

    def run(self, args):
        DEFAULT_MEM_ADDR = self.config["mem"]["start_addr"] + (1 << 20)  # 1Mb

        self.configure_network()
        self.client.sf_probe(args.probe)

        mem_addr = DEFAULT_MEM_ADDR if args.addr is None else args.addr
        logging.info("Read {} bytes from {} offset of SPI flash into memory at {}...".format(args.size, args.offset, mem_addr))
        self.client.sf_read(mem_addr, args.offset, args.size)

        utils.download_files_via_tftp(self.client, (
            (args.dst, mem_addr, args.size),
        ), listen_ip=str(self.host_ip))
