from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data):
        data = super().attributes(data)
        if data["lastConnEvent"]["category"] == "DISCONNECTED":
            data["parameters"]["machMode"] = "0"
        data["active"] = bool(data.get("activity"))
        data["pause"] = data["parameters"]["machMode"] == "3"
        return data

    def settings(self, settings):
        return settings
