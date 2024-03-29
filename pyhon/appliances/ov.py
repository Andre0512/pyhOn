from typing import Any, Dict

from pyhon.appliances.base import ApplianceBase


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        if not self.parent.connection:
            data["parameters"]["temp"].value = 0
            data["parameters"]["onOffStatus"].value = 0
            data["parameters"]["remoteCtrValid"].value = 0
            data["parameters"]["remainingTimeMM"].value = 0

        data["active"] = data["parameters"]["onOffStatus"].value == 1
        return data
