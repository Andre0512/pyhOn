from typing import Dict, Any

from pyhon.parameter.base import HonParameter


class HonParameterFixed(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        super().__init__(key, attributes, group)
        self._value = attributes.get("fixedValue", None)

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> fixed)"

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else "0"

    @value.setter
    def value(self, value: str | float) -> None:
        # Fixed values seems being not so fixed as thought
        self._value = value
        self.check_trigger(value)
