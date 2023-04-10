import re


def str_to_float(string):
    return float(string.replace(",", "."))


class HonParameter:
    def __init__(self, key, attributes):
        self._key = key
        self._category = attributes.get("category")
        self._typology = attributes.get("typology")
        self._mandatory = attributes.get("mandatory")
        self._value = ""

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value if self._value is not None else "0"

    @property
    def category(self):
        return self._category

    @property
    def typology(self):
        return self._typology

    @property
    def mandatory(self):
        return self._mandatory


class HonParameterFixed(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes.get("fixedValue", None)

    def __repr__(self):
        return f"{self.__class__} (<{self.key}> fixed)"

    @property
    def value(self):
        return self._value if self._value is not None else "0"

    @value.setter
    def value(self, value):
        if not value == self._value:
            raise ValueError("Can't change fixed value")


class HonParameterRange(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._min = str_to_float(attributes["minimumValue"])
        self._max = str_to_float(attributes["maximumValue"])
        self._step = str_to_float(attributes["incrementValue"])
        self._default = str_to_float(attributes.get("defaultValue", self._min))
        self._value = self._default

    def __repr__(self):
        return f"{self.__class__} (<{self.key}> [{self._min} - {self._max}])"

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def step(self):
        return self._step

    @property
    def value(self):
        return self._value if self._value is not None else self._min

    @value.setter
    def value(self, value):
        value = str_to_float(value)
        if self._min <= value <= self._max and not value % self._step:
            self._value = value
        else:
            raise ValueError(
                f"Allowed: min {self._min} max {self._max} step {self._step}"
            )


class HonParameterEnum(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._default = attributes.get("defaultValue")
        self._value = self._default or "0"
        self._values = attributes.get("enumValues")

    def __repr__(self):
        return f"{self.__class__} (<{self.key}> {self.values})"

    @property
    def values(self):
        return [str(value) for value in self._values]

    @property
    def value(self):
        return self._value if self._value is not None else self.values[0]

    @value.setter
    def value(self, value):
        if value in self.values:
            self._value = value
        else:
            raise ValueError(f"Allowed values {self._value}")


class HonParameterProgram(HonParameterEnum):
    def __init__(self, key, command):
        super().__init__(key, {})
        self._command = command
        self._value = command._program
        self._values = command._multi
        self._typology = "enum"
        self._filter = ""

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value in self.values:
            self._command.set_program(value)
        else:
            raise ValueError(f"Allowed values {self._values}")

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, filter):
        self._filter = filter

    @property
    def values(self):
        values = []
        for value in self._values:
            if not self._filter or re.findall(self._filter, str(value)):
                values.append(str(value))
        return sorted(values)
