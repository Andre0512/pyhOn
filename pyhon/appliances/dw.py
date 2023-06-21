from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data):
        data = super().attributes(data)
        if data.get("lastConnEvent", {}).get("category", "") == "DISCONNECTED":
            data["parameters"]["machMode"] = "0"
        data["active"] = bool(data.get("activity"))
        return data
