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


class HonParameterFixed(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes["fixedValue"]

    def __repr__(self):
        return f"{self.__class__} (<{self.key}> fixed)"

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if not value == self._value:
            raise ValueError("Can't change fixed value")


class HonParameterRange(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._min = int(attributes["minimumValue"])
        self._max = int(attributes["maximumValue"])
        self._step = int(attributes["incrementValue"])
        self._default = int(attributes.get("defaultValue", self._min))
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
        if self._min <= value <= self._max and not value % self._step:
            self._value = self._value
        else:
            raise ValueError(f"Allowed: min {self._min} max {self._max} step {self._step}")


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
        return self._value

    @value.setter
    def value(self, value):
        if value in self.values:
            self._value = self._value
        else:
            raise ValueError(f"Allowed values {self._value}")


class HonParameterProgram(HonParameterEnum):
    def __init__(self, key, command):
        super().__init__(key, {})
        self._command = command
        self._value = command._category
        self._values = command._multi

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value in self.values:
            self._command.set_program(value)
        else:
            raise ValueError(f"Allowed values {self._value}")
