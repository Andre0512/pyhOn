#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import sys
from getpass import getpass
from pathlib import Path
from typing import Tuple, Dict, Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pyhon import Hon, HonAPI, diagnose, printer

_LOGGER = logging.getLogger(__name__)


def get_arguments() -> Dict[str, Any]:
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
    parser.add_argument(
        "-i", "--import", help="import pyhon data", nargs="?", default=Path().cwd()
    )
    return vars(parser.parse_args())


async def translate(language: str, json_output: bool = False) -> None:
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
        print(printer.pretty_print(keys))


def get_login_data(args: Dict[str, str]) -> Tuple[str, str]:
    if not (user := args["user"]):
        user = input("User for hOn account: ")
    if not (password := args["password"]):
        password = getpass("Password for hOn account: ")
    return user, password


async def main() -> None:
    args = get_arguments()
    if language := args.get("translate"):
        await translate(language, json_output=args.get("json", ""))
        return
    async with Hon(
        *get_login_data(args), test_data_path=Path(args.get("import", ""))
    ) as hon:
        for device in hon.appliances:
            if args.get("export"):
                anonymous = args.get("anonymous", False)
                path = Path(args.get("directory", "."))
                if not args.get("zip"):
                    for file in await diagnose.appliance_data(device, path, anonymous):
                        print(f"Created {file}")
                else:
                    archive = await diagnose.zip_archive(device, path, anonymous)
                    print(f"Created {archive}")
                continue
            print("=" * 10, device.appliance_type, "-", device.nick_name, "=" * 10)
            if args.get("keys"):
                data = device.data.copy()
                attr = "get" if args.get("all") else "pop"
                print(
                    printer.key_print(
                        data["attributes"].__getattribute__(attr)("parameters")
                    )
                )
                print(printer.key_print(data.__getattribute__(attr)("appliance")))
                print(printer.key_print(data))
                print(
                    printer.pretty_print(
                        printer.create_commands(device.commands, concat=True)
                    )
                )
            else:
                print(diagnose.yaml_export(device))


def start() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Aborted.")


if __name__ == "__main__":
    start()
