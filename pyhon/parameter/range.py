from typing import Dict, Any, List

from pyhon.helper import str_to_float
from pyhon.parameter.base import HonParameter


class HonParameterRange(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any], group: str) -> None:
        super().__init__(key, attributes, group)
        self._min: float = 0
        self._max: float = 0
        self._step: float = 0
        self._default: float = 0
        self._value: float = 0
        self._set_attributes()

    def _set_attributes(self) -> None:
        super()._set_attributes()
        self._min = str_to_float(self._attributes.get("minimumValue", 0))
        self._max = str_to_float(self._attributes.get("maximumValue", 0))
        self._step = str_to_float(self._attributes.get("incrementValue", 0))
        self._default = str_to_float(self._attributes.get("defaultValue", self.min))
        self._value = self._default

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> [{self.min} - {self.max}])"

    @property
    def min(self) -> float:
        return self._min

    @min.setter
    def min(self, mini: float) -> None:
        self._min = mini

    @property
    def max(self) -> float:
        return self._max

    @max.setter
    def max(self, maxi: float) -> None:
        self._max = maxi

    @property
    def step(self) -> float:
        if not self._step:
            return 1
        return self._step

    @step.setter
    def step(self, step: float) -> None:
        self._step = step

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else self.min

    @value.setter
    def value(self, value: str | float) -> None:
        value = str_to_float(value)
        if self.min <= value <= self.max and not ((value - self.min) * 100) % (
            self.step * 100
        ):
            self._value = value
            self.check_trigger(value)
        else:
            allowed = f"min {self.min} max {self.max} step {self.step}"
            raise ValueError(f"Allowed: {allowed} But was: {value}")

    @property
    def values(self) -> List[str]:
        result = []
        i = self.min
        while i <= self.max:
            result.append(str(i))
            i += self.step
        return result
