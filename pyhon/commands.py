from typing import Optional, Dict, Any, List, TYPE_CHECKING, Union

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
        appliance: "HonAppliance",
        categories: Optional[Dict[str, "HonCommand"]] = None,
        category_name: str = "",
    ):
        self._api: HonAPI = appliance.api
        self._appliance: "HonAppliance" = appliance
        self._name: str = name
        self._categories: Optional[Dict[str, "HonCommand"]] = categories
        self._category_name: str = category_name
        self._description: str = attributes.pop("description", "")
        self._protocol_type: str = attributes.pop("protocolType", "")
        self._parameters: Dict[str, HonParameter] = {}
        self._data: Dict[str, Any] = {}
        self._available_settings: Dict[str, HonParameter] = {}
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

    @property
    def settings(self) -> Dict[str, HonParameter]:
        return self._parameters

    @property
    def parameter_groups(self) -> Dict[str, Dict[str, Union[str, float]]]:
        result: Dict[str, Dict[str, Union[str, float]]] = {}
        for name, parameter in self._parameters.items():
            result.setdefault(parameter.group, {})[name] = parameter.value
        return result

    @property
    def parameter_value(self) -> Dict[str, Union[str, float]]:
        return {n: p.value for n, p in self._parameters.items()}

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
            name = "program" if "PROGRAM" in self._category_name else "category"
            self._parameters[name] = HonParameterProgram(name, self, "custom")

    async def send(self) -> bool:
        params = self.parameter_groups.get("parameters", {})
        ancillary_params = self.parameter_groups.get("ancillaryParameters", {})
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

    @staticmethod
    def _more_options(first: HonParameter, second: HonParameter):
        if isinstance(first, HonParameterFixed) and not isinstance(
            second, HonParameterFixed
        ):
            return second
        if len(second.values) > len(first.values):
            return second
        return first

    @property
    def available_settings(self) -> Dict[str, HonParameter]:
        result: Dict[str, HonParameter] = {}
        for command in self.categories.values():
            for name, parameter in command.parameters.items():
                if name in result:
                    result[name] = self._more_options(result[name], parameter)
                result[name] = parameter
        return result
