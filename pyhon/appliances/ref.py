from pyhon.parameter.fixed import HonParameterFixed


class Appliance:
    def __init__(self, appliance):
        self.parent = appliance

    def data(self, data):
        if data["attributes"]["parameters"]["holidayMode"] == "1":
            data["modeZ1"] = "holiday"
        elif data["attributes"]["parameters"]["intelligenceMode"] == "1":
            data["modeZ1"] = "auto_set"
        elif data["attributes"]["parameters"]["quickModeZ1"] == "1":
            data["modeZ1"] = "super_cool"
        else:
            data["modeZ1"] = "no_mode"

        if data["attributes"]["parameters"]["quickModeZ2"] == "1":
            data["modeZ2"] = "super_freeze"
        elif data["attributes"]["parameters"]["intelligenceMode"] == "1":
            data["modeZ2"] = "auto_set"
        else:
            data["modeZ2"] = "no_mode"

        return data

    def settings(self, settings):
        return settings
