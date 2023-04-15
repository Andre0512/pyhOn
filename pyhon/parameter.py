from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from pyhon.commands import HonCommand


def str_to_float(string: str | float) -> float:
    try:
        return int(string)
    except ValueError:
        return float(str(string).replace(",", "."))


class HonParameter:
    def __init__(self, key: str, attributes: Dict[str, Any]) -> None:
        self._key = key
        self._category: str = attributes.get("category", "")
        self._typology: str = attributes.get("typology", "")
        self._mandatory: int = attributes.get("mandatory", 0)
        self._value: str | float = ""

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else "0"

    @property
    def category(self) -> str:
        return self._category

    @property
    def typology(self) -> str:
        return self._typology

    @property
    def mandatory(self) -> int:
        return self._mandatory


class HonParameterFixed(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any]) -> None:
        super().__init__(key, attributes)
        self._value = attributes.get("fixedValue", None)

    def __repr__(self) -> str:
        return f"{self.__class__} (<{self.key}> fixed)"

    @property
    def value(self) -> str | float:
        return self._value if self._value is not None else "0"

    @value.setter
    def value(self, value):
        if not value == self._value:
            raise ValueError("Can't change fixed value")


class HonParameterRange(HonParameter):
    def __init__(self, key: str, attributes: Dict[str, Any]) -> None:
        super().__init__(key, attributes)
        self._min: float = str_to_float(attributes["minimumValue"])
        self._max: float = str_to_float(attributes["maximumValue"])
        self._step: float = str_to_float(attributes["incrementValue"])
        self._default: float = str_to_float(attributes.get("defaultValue", self._min))
        self._value: float = self._default

    def __repr__(self):
        return f"{self.__class__} (<{self.key}> [{self._min} - {self._max}])"

    @property
    def min(self) -> float:
        return self._min

    @property
    def max(self) -> float:
        return self._max

    @property
    def step(self) -> float:
        return self._step

    @property
    def value(self) -> float:
        return self._value if self._value is not None else self._min

    @value.setter
    def value(self, value: float) -> None:
        value = str_to_float(value)
        if self._min <= value <= self._max and not value % self._step:
            self._value = value
        else:
            raise ValueError(
                f"Allowed: min {self._min} max {self._max} step {self._step}"
            )


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


class HonParameterProgram(HonParameterEnum):
    _FILTER = ["iot_recipe", "iot_guided"]

    def __init__(self, key: str, command: "HonCommand") -> None:
        super().__init__(key, {})
        self._command = command
        self._value: str = command.program
        self._values: List[str] = list(command.programs)
        self._typology: str = "enum"

    @property
    def value(self) -> str | float:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if value in self.values:
            self._command.program = value
        else:
            raise ValueError(f"Allowed values {self._values}")

    @property
    def values(self) -> List[str]:
        values = [v for v in self._values if all(f not in v for f in self._FILTER)]
        return sorted(values)
