class HonParameter:
    def __init__(self, key, attributes):
        self._key = key
        self._category = attributes.get("category")
        self._typology = attributes.get("typology")
        self._mandatory = attributes.get("mandatory")
        self._value = ""

    @property
    def value(self):
        return self._value if self._value is not None else "0"


class HonParameterFixed(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes["fixedValue"]


class HonParameterRange(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes.get("defaultValue")
        self._default = attributes.get("defaultValue")
        self._min = attributes["minimumValue"]
        self._max = attributes["maximumValue"]
        self._step = attributes["incrementValue"]


class HonParameterEnum(HonParameter):
    def __init__(self, key, attributes):
        super().__init__(key, attributes)
        self._value = attributes.get("defaultValue", "0")
        self._default = attributes["defaultValue"]
        self._values = attributes["enumValues"]
