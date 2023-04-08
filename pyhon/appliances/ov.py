from pyhon.parameter import HonParameterEnum


class Appliance:
    def __init__(self):
        filters = ["receipt", "standard, special"]
        data = {'defaultValue': filters[0], 'enumValues': filters}
        self._program_filter = HonParameterEnum("program_filter", data)

    def data(self, data):
        return data

    def settings(self, settings):
        settings["program_filter"] = self._program_filter
        settings["startProgram.program"].filter = self._program_filter.value
        return settings
