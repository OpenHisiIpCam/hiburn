#!/usr/bin/env python3
import logging
from hiburn.u_boot_client import UBootClient


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    client = UBootClient(
        port="/dev/ttyCAM3",
        baudrate=115200
    )

    print("Please, swith OFF the device's power press Enter")
    input()
    print("Please, swith ON the device's power")

    client.fetch_console()

    print("\n".join(client.printenv()))
