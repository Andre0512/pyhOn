from typing import Any, Dict

from pyhon.appliances.base import ApplianceBase
from pyhon.parameter.base import HonParameter


class Appliance(ApplianceBase):
    def attributes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        data = super().attributes(data)
        parameter = data.get("parameters", {}).get("onOffStatus")
        is_class = isinstance(parameter, HonParameter)
        data["active"] = parameter.value == 1 if is_class else parameter == 1
        return data

    def settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        return settings
