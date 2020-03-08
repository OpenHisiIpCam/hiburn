#!/usr/bin/env python3
import logging
import argparse
import ipaddress
from hiburn.u_boot_client import UBootClient
from hiburn.config import add_arguments_from_config, get_config_from_args


DEFAULT_CONFIG = {
    "serial": {
        "port": "/dev/ttyCAM1",
        "baudrate": 115200
    },
    "net": {
        "target": ipaddress.IPv4Address("192.168.10.101"),
        "host": ipaddress.IPv4Interface("192.168.10.2/24")
    }
}


def upload(client: UBootClient, config):
    # 1. set network parameters
    client.setenv(
        ipaddr=config["net"]["target"],
        netmask=config["net"]["host"].netmask,
        serverip=config["net"]["host"].ip
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--verbose", "-v", action="store_true",
        help="Print debug output"
    )
    add_arguments_from_config(parser, DEFAULT_CONFIG)

    args = parser.parse_args()
    config = get_config_from_args(args, DEFAULT_CONFIG)

    logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))
    client = UBootClient(
        port=config["serial"]["port"],
        baudrate=config["serial"]["baudrate"]
    )

    print("Please, swith OFF the device's power press Enter")
    input()
    print("Please, swith ON the device's power")

    client.fetch_console()

    print("\n".join(client.printenv()))
    upload(client, config)
    print("\n".join(client.printenv()))


if __name__ == "__main__":
    main()
