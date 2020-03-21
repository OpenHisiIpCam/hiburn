#!/usr/bin/env python3
import logging
import argparse
import json
import os
from hiburn.u_boot_client import UBootClient
from hiburn.config import add_arguments_from_config_desc, get_config_from_args
from hiburn import utils
from hiburn import actions


# -------------------------------------------------------------------------------------------------
DEFAULT_CONFIG_DESC = {
    "serial": {
        "port": ("/dev/ttyCAM1", str, "Serial port to interact with"),
        "baudrate": (115200, int, "Baudrate of the serial port")
    },
    "net": {
        "target": ("192.168.10.101", str, "Target IP address"),
        "host": ("192.168.10.2/24", str, "Host IP address and mask's length")
    },
    "mem": {
        "base_addr": ("0x82000000", utils.hsize2int, "Base RAM address"),
        "block_size": ("64K", utils.hsize2int, "Memory block size"),
        "initrd_size": ("16M", utils.hsize2int, "Amount of RAM for initrd"),
        "linux_size": ("256M", utils.hsize2int, "Amount of RAM for Linux"),
        "uboot_size": ("512K", utils.hsize2int, ""),
    },
    "linux_console": ("ttyAMA0,115200", str, "Linux load console")
}


# -------------------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", "-v", action="store_true",
        help="Print debug output"
    )
    parser.add_argument("--no-fetch", "-n", action="store_true",
        help="Assume U-Boot's console is already fetched"
    )
    parser.add_argument("--print-config", action="store_true",
        help="Just print result config"
    )
    add_arguments_from_config_desc(parser, DEFAULT_CONFIG_DESC)
    actions.add_actions(parser,
        actions.printenv,
        actions.ping,
        actions.download,
        actions.upload,
        actions.boot
    )

    args = parser.parse_args()
    logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
    config = get_config_from_args(args, DEFAULT_CONFIG_DESC)

    if args.print_config:
        print(json.dumps(config, indent=2, sort_keys=True))
        exit(0)

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
        print("Nothing to do here...")


if __name__ == "__main__":
    main()

