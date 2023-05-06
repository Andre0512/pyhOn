from typing import Optional, Dict, Any, List, TYPE_CHECKING

from pyhon.parameter.base import HonParameter
from pyhon.parameter.enum import HonParameterEnum
from pyhon.parameter.fixed import HonParameterFixed
from pyhon.parameter.program import HonParameterProgram
from pyhon.parameter.range import HonParameterRange

if TYPE_CHECKING:
    from pyhon import HonAPI
    from pyhon.appliance import HonAppliance


class HonCommand:
    def __init__(
        self,
        name: str,
        attributes: Dict[str, Any],
        api: "HonAPI",
        appliance: "HonAppliance",
        categories: Optional[Dict[str, "HonCommand"]] = None,
        category_name: str = "",
    ):
        self._api: HonAPI = api
        self._appliance: "HonAppliance" = appliance
        self._name: str = name
        self._categories: Optional[Dict[str, "HonCommand"]] = categories
        self._category_name: str = category_name
        self._description: str = attributes.pop("description", "")
        self._protocol_type: str = attributes.pop("protocolType", "")
        self._parameters: Dict[str, HonParameter] = {}
        self._data = {}
        self._load_parameters(attributes)

    def __repr__(self) -> str:
        return f"{self._name} command"

    @property
    def name(self):
        return self._name

    @property
    def data(self):
        return self._data

    @property
    def parameters(self) -> Dict[str, HonParameter]:
        return self._parameters

    def _load_parameters(self, attributes):
        for key, items in attributes.items():
            for name, data in items.items():
                self._create_parameters(data, name, key)

    def _create_parameters(self, data: Dict, name: str, parameter: str) -> None:
        if name == "zoneMap" and self._appliance.zone:
            data["default"] = self._appliance.zone
        match data.get("typology"):
            case "range":
                self._parameters[name] = HonParameterRange(name, data, parameter)
            case "enum":
                self._parameters[name] = HonParameterEnum(name, data, parameter)
            case "fixed":
                self._parameters[name] = HonParameterFixed(name, data, parameter)
            case _:
                self._data[name] = data
                return
        if self._category_name:
            if not self._categories:
                self._parameters["program"] = HonParameterProgram("program", self, name)

    def _parameters_by_group(self, group):
        return {
            name: v.value for name, v in self._parameters.items() if v.group == group
        }

    async def send(self) -> bool:
        params = self._parameters_by_group("parameters")
        ancillary_params = self._parameters_by_group("ancillary_parameters")
        return await self._api.send_command(
            self._appliance, self._name, params, ancillary_params
        )

    @property
    def categories(self) -> Dict[str, "HonCommand"]:
        if self._categories is None:
            return {"_": self}
        return self._categories

    @property
    def category(self) -> str:
        return self._category_name

    @category.setter
    def category(self, category: str) -> None:
        self._appliance.commands[self._name] = self.categories[category]

    @property
    def setting_keys(self) -> List[str]:
        return list(
            {param for cmd in self.categories.values() for param in cmd.parameters}
        )

    @property
    def settings(self) -> Dict[str, HonParameter]:
        result = {}
        for command in self.categories.values():
            for name, parameter in command.parameters.items():
                if name in result:
                    continue
                result[name] = parameter
        return result
