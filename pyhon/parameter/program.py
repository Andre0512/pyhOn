from typing import List, TYPE_CHECKING, Dict

from pyhon.parameter.enum import HonParameterEnum

if TYPE_CHECKING:
    from pyhon.commands import HonCommand


class HonParameterProgram(HonParameterEnum):
    _FILTER = ["iot_recipe", "iot_guided"]

    def __init__(self, key: str, command: "HonCommand", group: str) -> None:
        super().__init__(key, {}, group)
        self._command = command
        if "PROGRAM" in command.category:
            self._value = command.category.split(".")[-1].lower()
        else:
            self._value = command.category
        self._programs: Dict[str, "HonCommand"] = command.categories
        self._typology: str = "enum"

    @property
    def value(self) -> str | float:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if value in self.values:
            self._command.category = value
        else:
            raise ValueError(f"Allowed values: {self.values} But was: {value}")

    @property
    def values(self) -> List[str]:
        values = [v for v in self._programs if all(f not in v for f in self._FILTER)]
        return sorted(values)

    @values.setter
    def values(self, values: List[str]) -> None:
        raise ValueError("Cant set values {values}")

    @property
    def ids(self) -> Dict[int, str]:
        values: Dict[int, str] = {}
        for name, parameter in self._programs.items():
            if "iot_" in name:
                continue
            if parameter.parameters.get("prCode"):
                continue
            if (fav := parameter.parameters.get("favourite")) and fav.value == "1":
                continue
            values[int(parameter.parameters["prCode"].value)] = name
        return dict(sorted(values.items()))

    def set_value(self, value: str) -> None:
        self._value = value
