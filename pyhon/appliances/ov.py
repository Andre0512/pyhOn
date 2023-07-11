from typing import Any, Dict

from pyhon.appliances.base import ApplianceBase
from pyhon.parameter.program import HonParameterProgram


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        if data.get("lastConnEvent", {}).get("category", "") == "DISCONNECTED":
            data["parameters"]["temp"].value = "0"
            data["parameters"]["onOffStatus"].value = "0"
            data["parameters"]["remoteCtrValid"].value = "0"
            data["parameters"]["remainingTimeMM"].value = "0"

        data["active"] = data["parameters"]["onOffStatus"] == "1"
        return data
