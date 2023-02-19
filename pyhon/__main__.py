#!/usr/bin/env python
import argparse
import asyncio
import logging
import sys
import time
from getpass import getpass
from pathlib import Path
from pprint import pprint

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pyhon import HonConnection

_LOGGER = logging.getLogger(__name__)


def get_arguments():
    """Get parsed arguments."""
    parser = argparse.ArgumentParser(description="hOn: Command Line Utility")
    parser.add_argument("-u", "--user", help="user of haier hOn account")
    parser.add_argument("-p", "--password", help="password of haier hOn account")
    return vars(parser.parse_args())


async def main():
    args = get_arguments()
    if not (user := args["user"]):
        user = input("User of hOn account: ")
    if not (password := args["password"]):
        password = getpass("Password of hOn account: ")
    async with HonConnection(user, password) as hon:
        await hon.setup()
        for device in hon.devices:
            print(10 * "=", device.nick_name, 10 * "=")
            print(10 * "-", "attributes", 10 * "-")
            pprint(device.attributes)
            print(10 * "-", "statistics", 10 * "-")
            pprint(device.statistics)
            print(10 * "-", "commands", 10 * "-")
            pprint(device.parameters)
            print(10 * "-", "settings", 10 * "-")
            pprint(device.settings)


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == '__main__':
    start()
