from typing import Dict, Any, TYPE_CHECKING, List

from pyhon.parameter.enum import HonParameterEnum
from pyhon.parameter.range import HonParameterRange

if TYPE_CHECKING:
    from pyhon.commands import HonCommand


def key_print(data: Any, key: str = "", start: bool = True) -> str:
    result = ""
    if isinstance(data, list):
        for i, value in enumerate(data):
            result += key_print(value, key=f"{key}.{i}", start=False)
    elif isinstance(data, dict):
        for k, value in sorted(data.items()):
            result += key_print(value, key=k if start else f"{key}.{k}", start=False)
    else:
        result += f"{key}: {data}\n"
    return result


# yaml.dump() would be done the same, but needs an additional dependency...
def pretty_print(
    data: Any,
    key: str = "",
    intend: int = 0,
    is_list: bool = False,
    whitespace: str = "  ",
) -> str:
    result = ""
    if isinstance(data, list):
        if key:
            result += f"{whitespace * intend}{'- ' if is_list else ''}{key}:\n"
            intend += 1
        for i, value in enumerate(data):
            result += pretty_print(
                value, intend=intend, is_list=True, whitespace=whitespace
            )
    elif isinstance(data, dict):
        if key:
            result += f"{whitespace * intend}{'- ' if is_list else ''}{key}:\n"
            intend += 1
        for i, (key, value) in enumerate(sorted(data.items())):
            if is_list and not i:
                result += pretty_print(
                    value, key=key, intend=intend, is_list=True, whitespace=whitespace
                )
            elif is_list:
                result += pretty_print(
                    value, key=key, intend=intend + 1, whitespace=whitespace
                )
            else:
                result += pretty_print(
                    value, key=key, intend=intend, whitespace=whitespace
                )
    else:
        result += f"{whitespace * intend}{'- ' if is_list else ''}{key}{': ' if key else ''}{data}\n"
    return result


def create_commands(
    commands: Dict[str, "HonCommand"], concat: bool = False
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name, command in commands.items():
        for parameter, data in command.available_settings.items():
            if isinstance(data, HonParameterEnum):
                value: List[str] | Dict[str, str | float] = data.values
            elif isinstance(data, HonParameterRange):
                value = {"min": data.min, "max": data.max, "step": data.step}
            else:
                continue
            if not concat:
                result.setdefault(name, {})[parameter] = value
            else:
                result[f"{name}.{parameter}"] = value
    return result


def create_rules(
    commands: Dict[str, "HonCommand"], concat: bool = False
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name, command in commands.items():
        for parameter, data in command.available_settings.items():
            value = data.triggers
            if not value:
                continue
            if not concat:
                result.setdefault(name, {})[parameter] = value
            else:
                result[f"{name}.{parameter}"] = value
    return result
