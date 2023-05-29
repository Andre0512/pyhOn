from pyhon.appliances.base import ApplianceBase
from pyhon.parameter.fixed import HonParameterFixed


class Appliance(ApplianceBase):
    def data(self, data):
        super().data(data)
        if data["attributes"]["lastConnEvent"]["category"] == "DISCONNECTED":
            data["attributes"]["parameters"]["machMode"] = "0"
        data["active"] = bool(data.get("attributes", {}).get("activity"))
        data["pause"] = data["attributes"]["parameters"]["machMode"] == "3"
        return data

    def settings(self, settings):
        dry_level = settings.get("startProgram.dryLevel")
        if isinstance(dry_level, HonParameterFixed) and dry_level.value == "11":
            settings.pop("startProgram.dryLevel", None)
        return settings
