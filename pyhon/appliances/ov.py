from pyhon.parameter import HonParameterEnum


class Appliance:
    _FILTERS = {
        "default": "^(?!iot_(?:recipe|guided))\\S+$",
        "recipe": "iot_recipe_",
        "guided": "iot_guided_",
    }

    def __init__(self):
        filters = list(self._FILTERS.values())
        data = {"defaultValue": filters[0], "enumValues": filters}
        self._program_filter = HonParameterEnum("program_filter", data)

    def data(self, data):
        return data

    def settings(self, settings):
        settings["program_filter"] = self._program_filter
        value = self._FILTERS[self._program_filter.value]
        settings["startProgram.program"].filter = value
        return settings
