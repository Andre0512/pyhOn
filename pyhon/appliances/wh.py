from typing import Any, Dict

from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        data["active"] = data["parameters"]["onOffStatus"] == "1"

        return data
