import asyncio
import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

from pyhon import printer

if TYPE_CHECKING:
    from pyhon.appliance import HonAppliance


def anonymize_data(data: str) -> str:
    default_date = "1970-01-01T00:00:00.0Z"
    default_mac = "xx-xx-xx-xx-xx-xx"
    data = re.sub("[0-9A-Fa-f]{2}(-[0-9A-Fa-f]{2}){5}", default_mac, data)
    data = re.sub("[\\d-]{10}T[\\d:]{8}(.\\d+)?Z", default_date, data)
    for sensible in [
        "serialNumber",
        "code",
        "nickName",
        "mobileId",
        "PK",
        "SK",
        "lat",
        "lng",
    ]:
        for match in re.findall(f'"{sensible}.*?":\\s"?(.+?)"?,?\\n', data):
            replace = re.sub("[a-z]", "x", match)
            replace = re.sub("[A-Z]", "X", replace)
            replace = re.sub("\\d", "1", replace)
            data = data.replace(match, replace)
    return data


async def load_data(appliance: "HonAppliance", topic: str) -> Tuple[str, str]:
    return topic, await getattr(appliance.api, f"load_{topic}")(appliance)


def write_to_json(data: str, topic: str, path: Path, anonymous: bool = False) -> Path:
    json_data = json.dumps(data, indent=4)
    if anonymous:
        json_data = anonymize_data(json_data)
    file = path / f"{topic}.json"
    with open(file, "w", encoding="utf-8") as json_file:
        json_file.write(json_data)
    return file


async def appliance_data(
    appliance: "HonAppliance", path: Path, anonymous: bool = False
) -> List[Path]:
    requests = [
        "commands",
        "attributes",
        "command_history",
        "statistics",
        "maintenance",
        "appliance_data",
    ]
    path /= f"{appliance.appliance_type}_{appliance.model_id}".lower()
    path.mkdir(parents=True, exist_ok=True)
    api_data = await asyncio.gather(*[load_data(appliance, name) for name in requests])
    return [write_to_json(data, topic, path, anonymous) for topic, data in api_data]


async def zip_archive(
    appliance: "HonAppliance", path: Path, anonymous: bool = False
) -> str:
    data = await appliance_data(appliance, path, anonymous)
    archive = data[0].parent
    shutil.make_archive(str(archive), "zip", archive)
    shutil.rmtree(archive)
    return f"{archive.stem}.zip"


def yaml_export(appliance: "HonAppliance", anonymous: bool = False) -> str:
    data = {
        "attributes": appliance.attributes.copy(),
        "appliance": appliance.info,
        "statistics": appliance.statistics,
        "additional_data": appliance.additional_data,
    }
    data |= {n: c.parameter_groups for n, c in appliance.commands.items()}
    extra = {n: c.data for n, c in appliance.commands.items() if c.data}
    if extra:
        data |= {"extra_command_data": extra}
    if anonymous:
        for sensible in ["serialNumber", "coords"]:
            data.get("appliance", {}).pop(sensible, None)
    result = printer.pretty_print({"data": data})
    if commands := printer.create_commands(appliance.commands):
        result += printer.pretty_print({"commands": commands})
    if rules := printer.create_rules(appliance.commands):
        result += printer.pretty_print({"rules": rules})
    if anonymous:
        result = anonymize_data(result)
    return result
