import logging
import ipaddress
import os
from . import utils
from . import ymodem


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

    def upload_y_files(self, *args):
        for fname, addr in args:
            with open(fname, "rb") as f:
                data = f.read()
            self.client.loady(addr, data)


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
        parser.add_argument("--ymodem", action="store_true",
            help="Upload via serial (ymodem protocol)")

        bootargs_group = parser.add_argument_group("bootargs", "Kernel's boot arguments")
        bootargs_group.add_argument("--bootargs-ip", metavar="IP", type=str,
            help="Literal value for `ip=` parameter")
        bootargs_group.add_argument("--bootargs-ip-gw", metavar="IP",type=str,
            help="Value for <gw-ip> of `ip=` parameter")
        bootargs_group.add_argument("--bootargs-ip-hostname", metavar="HOSTNAME", type=str,
            help="Value for <hostname> of `ip=` parameter")
        bootargs_group.add_argument("--bootargs-ip-dns1", metavar="IP", type=str,
            help="Value for <dns0-ip> of `ip=` parameter")
        bootargs_group.add_argument("--bootargs-ip-dns2", metavar="IP", type=str,
            help="Value for <dns1-ip> of `ip=` parameter")

    def get_bootargs_ip(self, args):
        if args.bootargs_ip is not None:
            return args.bootargs_ip
        fmt = "{client_ip}:{server_ip}:{gw_ip}:{netmask}:{hostname}:{device}:{autoconf}:{dns0_ip}:{dns1_ip}:{ntp0_ip}"
        return fmt.format(
            client_ip=self.device_ip,
            server_ip=self.host_ip,
            gw_ip=args.bootargs_ip_gw or self.host_ip,
            netmask=self.host_netmask,
            hostname=args.bootargs_ip_hostname or "camera1",
            device="",
            autoconf="off",
            dns0_ip=args.bootargs_ip_dns1 or self.host_ip,
            dns1_ip=args.bootargs_ip_dns2 or "",
            ntp0_ip=""
        )

    def run(self, args):
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

        if args.ymodem:
            self.upload_y_files((args.uimage, uimage_addr), (args.rootfs, rootfs_addr))
        else:
            self.configure_network()
            self.upload_files((args.uimage, uimage_addr), (args.rootfs, rootfs_addr))

        bootargs = ""
        bootargs += "mem={} ".format(self.config["mem"]["linux_size"])
        bootargs += "console={} ".format(self.config["linux_console"])
        bootargs += "ip=" + self.get_bootargs_ip(args) + " "

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


# -------------------------------------------------------------------------------------------------
class upload_y(Action):
    """ Upload data to device's RAM via serial (ymodem)
    """
    @classmethod
    def add_arguments(cls, parser):
        pass
        # parser.add_argument("--src", type=str, required=True, help="File to be uploaded")
        # parser.add_argument("--addr", type=utils.hsize2int, required=True, help="Destination address in device's memory")

    def run(self, args):
        self.client.loady(b"bla bla bla!")

# -------------------------------------------------------------------------------------------------
class fastboot(Action):
    """ TODO
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--fastboot-bin", type=str, required=True, help="Fastboot.bin TODO")
        parser.add_argument("--uboot-bin", type=str, required=True, help="Uboot.bib TODO")

    def run(self, args):
        test="TODO"
