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

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        raise ValueError("fixed value")


class HonParameterRange(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._min = int(attributes["minimumValue"])
        self._max = int(attributes["maximumValue"])
        self._step = int(attributes["incrementValue"])
        self._default = int(attributes.get("defaultValue", self._min))
        self._value = self._default

    def __repr__(self):
        return f"{self.key} [{self._min} - {self._max}]"

    @property
    def value(self):
        return self._value if self._value is not None else self._min

    @value.setter
    def value(self, value):
        if self._min < value < self._max and not value % self._step:
            self._value = self._value
        raise ValueError(f"min {self._min} max {self._max} step {self._step}")


class HonParameterEnum(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes.get("defaultValue", "0")
        self._default = attributes.get("defaultValue")
        self._values = attributes.get("enumValues")

    def __repr__(self):
        return f"{self.key} {self._values}"

    @property
    def values(self):
        return self._values

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value in self._values:
            self._value = self._value
        raise ValueError(f"values {self._value}")


class HonParameterProgram(HonParameterEnum):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes["current"]
        self._values = attributes["values"]
