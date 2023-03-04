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
    parser = argparse.ArgumentParser(description="pyhOn: Command Line Utility")
    parser.add_argument("-u", "--user", help="user for haier hOn account")
    parser.add_argument("-p", "--password", help="password for haier hOn account")
    return vars(parser.parse_args())


# yaml.dump() would be done the same, but needs an additional import...
def pretty_print(data, key="", intend=0, is_list=False):
    if type(data) is list:
        if key:
            print(f"{'  ' * intend}{'- ' if is_list else ''}{key}:")
            intend += 1
        for i, value in enumerate(data):
            pretty_print(value, intend=intend, is_list=True)
    elif type(data) is dict:
        if key:
            print(f"{'  ' * intend}{'- ' if is_list else ''}{key}:")
            intend += 1
        for i, (key, value) in enumerate(sorted(data.items())):
            if is_list and not i:
                pretty_print(value, key=key, intend=intend, is_list=True)
            elif is_list:
                pretty_print(value, key=key, intend=intend + 1)
            else:
                pretty_print(value, key=key, intend=intend)
    else:
        print(f"{'  ' * intend}{'- ' if is_list else ''}{key}{': ' if key else ''}{data}")


async def main():
    args = get_arguments()
    if not (user := args["user"]):
        user = input("User for hOn account: ")
    if not (password := args["password"]):
        password = getpass("Password for hOn account: ")
    async with HonConnection(user, password) as hon:
        for device in hon.devices:
            print("=" * 10, device.nick_name, "=" * 10)
            pretty_print({"commands": device.commands})
            pretty_print({"data": device.data})


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == '__main__':
    start()
