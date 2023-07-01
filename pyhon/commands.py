import logging
from typing import Optional, Dict, Any, List, TYPE_CHECKING, Union

from pyhon import exceptions
from pyhon.exceptions import ApiError, NoAuthenticationException
from pyhon.parameter.base import HonParameter
from pyhon.parameter.enum import HonParameterEnum
from pyhon.parameter.fixed import HonParameterFixed
from pyhon.parameter.program import HonParameterProgram
from pyhon.parameter.range import HonParameterRange
from pyhon.rules import HonRuleSet
from pyhon.typedefs import Parameter

if TYPE_CHECKING:
    from pyhon import HonAPI
    from pyhon.appliance import HonAppliance

_LOGGER = logging.getLogger(__name__)


class HonCommand:
    def __init__(
        self,
        name: str,
        attributes: Dict[str, Any],
        appliance: "HonAppliance",
        categories: Optional[Dict[str, "HonCommand"]] = None,
        category_name: str = "",
    ):
        self._api: Optional[HonAPI] = appliance.api
        self._appliance: "HonAppliance" = appliance
        self._name: str = name
        self._categories: Optional[Dict[str, "HonCommand"]] = categories
        self._category_name: str = category_name
        self._description: str = attributes.pop("description", "")
        self._protocol_type: str = attributes.pop("protocolType", "")
        self._parameters: Dict[str, HonParameter] = {}
        self._data: Dict[str, Any] = {}
        self._available_settings: Dict[str, HonParameter] = {}
        self._rules: List[HonRuleSet] = []
        self._load_parameters(attributes)

    def __repr__(self) -> str:
        return f"{self._name} command"

    @property
    def name(self) -> str:
        return self._name

    @property
    def api(self) -> "HonAPI":
        if self._api is None:
            raise exceptions.NoAuthenticationException("Missing hOn login")
        return self._api

    @property
    def appliance(self) -> "HonAppliance":
        return self._appliance

    @property
    def data(self) -> Dict[str, Any]:
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
            result.setdefault(parameter.group, {})[name] = parameter.intern_value
        return result

    @property
    def parameter_value(self) -> Dict[str, Union[str, float]]:
        return {n: p.value for n, p in self._parameters.items()}

    def _load_parameters(self, attributes: Dict[str, Dict[str, Any]]) -> None:
        for key, items in attributes.items():
            for name, data in items.items():
                self._create_parameters(data, name, key)
        for rule in self._rules:
            rule.patch()

    def _create_parameters(
        self, data: Dict[str, Any], name: str, parameter: str
    ) -> None:
        if name == "zoneMap" and self._appliance.zone:
            data["default"] = self._appliance.zone
        if data.get("category") == "rule":
            if "fixedValue" not in data:
                _LOGGER.error("Rule not supported: %s", data)
            else:
                self._rules.append(HonRuleSet(self, data["fixedValue"]))
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
        ancillary_params.pop("programRules", None)
        self.appliance.sync_command_to_params(self.name)
        try:
            result = await self.api.send_command(
                self._appliance, self._name, params, ancillary_params
            )
            if not result:
                _LOGGER.error(result)
                raise ApiError("Can't send command")
        except NoAuthenticationException:
            _LOGGER.error("No Authentication")
            return False
        return result

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
        if category in self.categories:
            self._appliance.commands[self._name] = self.categories[category]

    @property
    def setting_keys(self) -> List[str]:
        return list(
            {param for cmd in self.categories.values() for param in cmd.parameters}
        )

    @staticmethod
    def _more_options(first: Parameter, second: Parameter) -> Parameter:
        if isinstance(first, HonParameterFixed) and not isinstance(
            second, HonParameterFixed
        ):
            return second
        if len(second.values) > len(first.values):
            return second
        return first

    @property
    def available_settings(self) -> Dict[str, Parameter]:
        result: Dict[str, Parameter] = {}
        for command in self.categories.values():
            for name, parameter in command.parameters.items():
                if name in result:
                    result[name] = self._more_options(result[name], parameter)
                else:
                    result[name] = parameter
        return result
