from typing import Dict, Any, List

from pyhon.parameter.base import HonParameter


class HonParameterEnum(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any]) -> None:
        super().__init__(key, attributes)
        self._default = attributes.get("defaultValue")
        self._value = self._default or "0"
        self._values: List[str] = attributes.get("enumValues", [])

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> {self.values})"

    @property
    def values(self) -> List[str]:
        return [str(value) for value in self._values]

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else self.values[0]

    @value.setter
    def value(self, value: str) -> None:
        if value in self.values:
            self._value = value
        else:
            raise ValueError(f"Allowed values {self._value}")
