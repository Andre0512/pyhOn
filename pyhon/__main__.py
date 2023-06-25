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

from pyhon import Hon, HonAPI, helper, diagnose

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
    export = subparser.add_parser("export")
    export.add_argument("export", help="export pyhon data", action="store_true")
    export.add_argument("--zip", help="create zip archive", action="store_true")
    export.add_argument("--anonymous", help="anonymize data", action="store_true")
    export.add_argument("directory", nargs="?", default=Path().cwd())
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


def get_login_data(args):
    if not (user := args["user"]):
        user = input("User for hOn account: ")
    if not (password := args["password"]):
        password = getpass("Password for hOn account: ")
    return user, password


async def main():
    args = get_arguments()
    if language := args.get("translate"):
        await translate(language, json_output=args.get("json"))
        return
    async with Hon(*get_login_data(args)) as hon:
        for device in hon.appliances:
            if args.get("export"):
                anonymous = args.get("anonymous", False)
                path = Path(args.get("directory"))
                if not args.get("zip"):
                    for file in await diagnose.appliance_data(device, path, anonymous):
                        print(f"Created {file}")
                else:
                    file = await diagnose.zip_archive(device, path, anonymous)
                    print(f"Created {file}")
                continue
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
                print(diagnose.yaml_export(device))


def start():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
