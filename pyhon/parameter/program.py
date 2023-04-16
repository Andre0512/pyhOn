from typing import List, TYPE_CHECKING, Dict

from pyhon.parameter.enum import HonParameterEnum

if TYPE_CHECKING:
    from pyhon.commands import HonCommand


class HonParameterProgram(HonParameterEnum):
    _FILTER = ["iot_recipe", "iot_guided"]

    def __init__(self, key: str, command: "HonCommand") -> None:
        super().__init__(key, {})
        self._command = command
        self._value: str = command.program
        self._programs: Dict[str, "HonCommand"] = command.programs
        self._typology: str = "enum"

    @property
    def value(self) -> str | float:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if value in self.values:
            self._command.program = value
        else:
            raise ValueError(f"Allowed values {self.values}")

    @property
    def values(self) -> List[str]:
        values = [v for v in self._programs if all(f not in v for f in self._FILTER)]
        return sorted(values)
