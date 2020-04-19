#!/usr/bin/env python3
import logging
import argparse
import json
import os
import subprocess
from hiburn.u_boot_client import UBootClient
from hiburn.config import add_arguments_from_config_desc, get_config_from_args
from hiburn import utils
from hiburn import actions



# -------------------------------------------------------------------------------------------------
DEFAULT_CONFIG_DESC = {
    "net": {
        "device_ip": ("192.168.10.101", str, "Target IP address"),
        "host_ip_mask": ("192.168.10.2/24", str, "Host IP address and mask's length")
    },
    "mem": {
        "start_addr": ("0x80000000", utils.hsize2int, "RAM start address"),
        "alignment": ("64K", utils.hsize2int, "RAM alignment for uploading"),
        "linux_size": ("256M", utils.hsize2int, "Amount of RAM for Linux"),
        "uboot_size": ("512K", utils.hsize2int, ""),
    },
    "linux_console": ("ttyAMA0,115200", str, "Linux load console")
}


# -------------------------------------------------------------------------------------------------
def reset_power(cmd=None):
    if cmd is None:
        print("Please, swith OFF the device's power and press Enter")
        input()
        print("Please, swith ON the device's power")
    else:
        logging.debug("Run '{}' shell command to reset power...".format(cmd))
        subprocess.check_call(cmd, shell=True)


# -------------------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true",
        help="Print debug output"
    )

    mutexg = parser.add_mutually_exclusive_group(required=True)
    mutexg.add_argument("--serial", type=utils.str2serial_kwargs, metavar="V",
        help="Serial port 'port[:baudrate[:DPS]]'")
    mutexg.add_argument("--serial-over-telnet", type=utils.str2endpoint, metavar="V",
        help="Serial-over-telnet endpoint '[host:]port'")

    parser.add_argument("--no-fetch", "-n", action="store_true",
        help="Assume U-Boot's console is already fetched"
    )
    parser.add_argument("--reset-cmd", type=str,
        help="Shell command to reset device's power"
    )

    add_arguments_from_config_desc(parser, DEFAULT_CONFIG_DESC)
    actions.add_actions(parser,
        actions.printenv,
        actions.ping,
        actions.download,
        actions.download_sf,
        actions.upload,
        actions.boot
    )

    args = parser.parse_args()
    logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
    config = get_config_from_args(args, DEFAULT_CONFIG_DESC)

    if args.serial is not None:
        client = UBootClient.create_with_serial(**args.serial)
    else:
        client = UBootClient.create_with_serial_over_telnet(*args.serial_over_telnet)

    if not args.no_fetch:
        reset_power(args.reset_cmd)
        client.fetch_console()

    if hasattr(args, "action"):
        args.action(client, config, args)
    else:
        print("Nothing to do here...")


if __name__ == "__main__":
    main()
