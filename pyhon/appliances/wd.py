from typing import Dict, Any

from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        if data.get("lastConnEvent", {}).get("category", "") == "DISCONNECTED":
            data["parameters"]["machMode"].value = "0"
        data["active"] = bool(data.get("activity"))
        data["pause"] = data["parameters"]["machMode"] == "3"
        return data

    def settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        return settings
