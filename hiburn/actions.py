import logging
import ipaddress
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
    def host_ip_interface(self):
        return ipaddress.ip_interface(self.config["net"]["host"])

    @property
    def device_ip(self):
        return ipaddress.ip_address(self.config["net"]["target"])

    def configure_network(self):
        self.client.setenv(
            ipaddr=self.device_ip,
            netmask=self.host_ip_interface.netmask,
            serverip=self.host_ip_interface.ip
        )


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
        result = self.client.ping(self.host_ip_interface.ip)[-1]
        if not result.endswith("is alive"):
            raise RuntimeError("network is unavailable")


# -------------------------------------------------------------------------------------------------
class download(Action):
    """ Download data from device's memory via TFTP
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
        ), listen_ip=str(self.host_ip_interface.ip))


class upload(Action):
    """ Upload data to device's memory via TFTP
    """
    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("--src", type=str, required=True, help="File to be uploaded")
        parser.add_argument("--addr", type=utils.hsize2int, required=True, help="Destination address in device's memory")

    def run(self, args):
        self.configure_network()
        utils.upload_files_via_tftp(self.client, (
            (args.src, args.addr),
        ), listen_ip=str(self.host_ip_interface.ip))
