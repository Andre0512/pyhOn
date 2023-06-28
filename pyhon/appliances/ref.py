from typing import Dict, Any

from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        if data["parameters"]["holidayMode"] == "1":
            data["modeZ1"] = "holiday"
        elif data["parameters"]["intelligenceMode"] == "1":
            data["modeZ1"] = "auto_set"
        elif data["parameters"]["quickModeZ1"] == "1":
            data["modeZ1"] = "super_cool"
        else:
            data["modeZ1"] = "no_mode"

        if data["parameters"]["quickModeZ2"] == "1":
            data["modeZ2"] = "super_freeze"
        elif data["parameters"]["intelligenceMode"] == "1":
            data["modeZ2"] = "auto_set"
        else:
            data["modeZ2"] = "no_mode"

        return data
