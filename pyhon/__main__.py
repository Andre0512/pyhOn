#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import sys
from getpass import getpass
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pyhon import Hon, HonAPI, helper

_LOGGER = logging.getLogger(__name__)


def get_arguments():
    """Get parsed arguments."""
    parser = argparse.ArgumentParser(description="pyhOn: Command Line Utility")
    parser.add_argument("-u", "--user", help="user for haier hOn account")
    parser.add_argument("-p", "--password", help="password for haier hOn account")
    subparser = parser.add_subparsers(title="commands", metavar="COMMAND")
    keys = subparser.add_parser("keys", help="print as key format")
    keys.add_argument("keys", help="print as key format", action="store_true")
    keys.add_argument("--all", help="print also full keys", action="store_true")
    translate = subparser.add_parser(
        "translate", help="print available translation keys"
    )
    translate.add_argument(
        "translate", help="language (de, en, fr...)", metavar="LANGUAGE"
    )
    translate.add_argument("--json", help="print as json", action="store_true")
    return vars(parser.parse_args())


async def translate(language, json_output=False):
    async with HonAPI(anonymous=True) as hon:
        keys = await hon.translation_keys(language)
    if json_output:
        print(json.dumps(keys, indent=4))
    else:
        clean_keys = (
            json.dumps(keys)
            .replace("\\n", "\\\\n")
            .replace("\\\\r", "")
            .replace("\\r", "")
        )
        keys = json.loads(clean_keys)
        print(helper.pretty_print(keys))


async def main():
    args = get_arguments()
    if language := args.get("translate"):
        await translate(language, json_output=args.get("json"))
        return
    if not (user := args["user"]):
        user = input("User for hOn account: ")
    if not (password := args["password"]):
        password = getpass("Password for hOn account: ")
    async with Hon(user, password) as hon:
        for device in hon.appliances:
            print("=" * 10, device.appliance_type, "-", device.nick_name, "=" * 10)
            if args.get("keys"):
                data = device.data.copy()
                attr = "get" if args.get("all") else "pop"
                print(
                    helper.key_print(
                        data["attributes"].__getattribute__(attr)("parameters")
                    )
                )
                print(helper.key_print(data.__getattribute__(attr)("appliance")))
                print(helper.key_print(data))
                print(
                    helper.pretty_print(
                        helper.create_command(device.commands, concat=True)
                    )
                )
            else:
                print(helper.pretty_print({"data": device.data}))
                print(
                    helper.pretty_print(
                        {"settings": helper.create_command(device.commands)}
                    )
                )


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
