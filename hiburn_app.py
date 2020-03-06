#!/usr/bin/env python3
import logging
import argparse
from hiburn.u_boot_client import UBootClient
from hiburn.config import add_arguments_from_config, get_config_from_args


DEFAULT_CONFIG = {
    "serial": {
        "port": "/dev/ttyCAM1",
        "baudrate": 115200
    },
    "net": {
        "target": "192.168.1.100",
        "host": "192.168.1.1/24"
    }
}


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


if __name__ == "__main__":
    main()
