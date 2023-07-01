from typing import Dict, Any, List

from pyhon.parameter.base import HonParameter


def clean_value(value: str | float) -> str:
    return str(value).strip("[]").replace("|", "_").lower()


class HonParameterEnum(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        super().__init__(key, attributes, group)
        self._default = attributes.get("defaultValue")
        self._value = self._default or "0"
        self._values: List[str] = attributes.get("enumValues", [])
        if self._default and clean_value(self._default.strip("[]")) not in self.values:
            self._values.append(self._default)

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> {self.values})"

    @property
    def values(self) -> List[str]:
        return [clean_value(value) for value in self._values]

    @values.setter
    def values(self, values: List[str]) -> None:
        self._values = values

    @property
    def intern_value(self) -> str:
        return str(self._value) if self._value is not None else str(self.values[0])

    @property
    def value(self) -> str | float:
        return clean_value(self._value) if self._value is not None else self.values[0]

    @value.setter
    def value(self, value: str) -> None:
        if value in self.values:
            self._value = value
            self.check_trigger(value)
        else:
            raise ValueError(f"Allowed values: {self._values} But was: {value}")
