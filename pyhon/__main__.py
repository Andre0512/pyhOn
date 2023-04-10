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

from pyhon import Hon, HonAPI

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


# yaml.dump() would be done the same, but needs an additional dependency...
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
        print(
            f"{'  ' * intend}{'- ' if is_list else ''}{key}{': ' if key else ''}{data}"
        )


def key_print(data, key="", start=True):
    if type(data) is list:
        for i, value in enumerate(data):
            key_print(value, key=f"{key}.{i}", start=False)
    elif type(data) is dict:
        for k, value in sorted(data.items()):
            key_print(value, key=k if start else f"{key}.{k}", start=False)
    else:
        print(f"{key}: {data}")


def create_command(commands, concat=False):
    result = {}
    for name, command in commands.items():
        if not concat:
            result[name] = {}
        for parameter, data in command.parameters.items():
            if data.typology == "enum":
                value = data.values
            elif data.typology == "range":
                value = {"min": data.min, "max": data.max, "step": data.step}
            else:
                continue
            if not concat:
                result[name][parameter] = value
            else:
                result[f"{name}.{parameter}"] = value
    return result


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
        pretty_print(keys)


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
                key_print(data["attributes"].__getattribute__(attr)("parameters"))
                key_print(data.__getattribute__(attr)("appliance"))
                key_print(data)
                pretty_print(create_command(device.commands, concat=True))
            else:
                pretty_print({"data": device.data})
                pretty_print({"settings": create_command(device.commands)})


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
