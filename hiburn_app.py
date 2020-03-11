#!/usr/bin/env python3
import logging
import argparse
import json
import ipaddress
import os
import inspect
from hiburn.u_boot_client import UBootClient
from hiburn.config import add_arguments_from_config_desc, get_config_from_args
from hiburn import utils
from hiburn import actions


# -------------------------------------------------------------------------------------------------
DEFAULT_CONFIG_DESC = {
    "serial": {
        "port": "/dev/ttyCAM1",
        "baudrate": 115200
    },
    "net": {
        "target": ("192.168.10.101", str, "Target IP address"),
        "host": ("192.168.10.2/24", str, "Host IP address and mask's length")
    },
    "memory": {
        "base_addr": (0x82000000, utils.hsize2int, "Base RAM address"),
        "block_size": ("64K", utils.hsize2int, "Memory block size")
    }
}


# -------------------------------------------------------------------------------------------------
def upload(client: UBootClient, config):
    """ Upload data to device's memory via TFTP
    """

    # 1. set network parameters
    configure_network(client, config)

    # 2. upload images
    block_size = config["memory"]["block_size"]
    base_addr = config["memory"]["base_addr"]

    uimage_addr = base_addr
    rootfs_addr = utils.aligned_address(block_size, uimage_addr + os.path.getsize(config["uimage"]))
    utils.upload_files_via_tftp(client, (
        (config["uimage"], uimage_addr),
        (config["rootfs"], rootfs_addr)
    ), listen_ip=str(ip_interface.ip))


# -------------------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", "-v", action="store_true",
        help="Print debug output"
    )
    parser.add_argument("--no-fetch", "-n", action="store_true",
        help="Assume U-Boot's consoel is already fetched"
    )
    add_arguments_from_config_desc(parser, DEFAULT_CONFIG_DESC)
    actions.add_actions(parser,
        actions.ping,
        actions.download,
        actions.printenv,
        actions.upload
    )

    args = parser.parse_args()
    config = get_config_from_args(args, DEFAULT_CONFIG_DESC)

    logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
    client = UBootClient(
        port=config["serial"]["port"],
        baudrate=config["serial"]["baudrate"]
    )

    if not args.no_fetch:
        print("Please, swith OFF the device's power press Enter")
        input()
        print("Please, swith ON the device's power")
        client.fetch_console()

    if hasattr(args, "action"):
        args.action(client, config, args)
    else:
        print("U-Boot console is fetched")


if __name__ == "__main__":
    main()

