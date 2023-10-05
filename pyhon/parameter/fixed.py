from typing import Dict, Any

from pyhon.parameter.base import HonParameter


class HonParameterFixed(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        super().__init__(key, attributes, group)
        self._value: str | float = ""
        self._set_attributes()

    def _set_attributes(self) -> None:
        super()._set_attributes()
        self._value = self._attributes.get("fixedValue", "")

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> fixed)"

    @property
    def value(self) -> str | float:
        return self._value if self._value != "" else "0"

    @value.setter
    def value(self, value: str | float) -> None:
        # Fixed values seems being not so fixed as thought
        self._value = value
        self.check_trigger(value)
