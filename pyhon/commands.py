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
        programs: Optional[Dict[str, "HonCommand"]] = None,
        program_name: str = "",
    ):
        self._api: HonAPI = api
        self._appliance: "HonAppliance" = appliance
        self._name: str = name
        self._programs: Optional[Dict[str, "HonCommand"]] = programs or {}
        self._program_name: str = program_name
        self._description: str = attributes.get("description", "")
        self._parameters: Dict[str, HonParameter] = self._create_parameters(
            attributes.get("parameters", {})
        )
        self._ancillary_parameters: Dict[str, HonParameter] = self._create_parameters(
            attributes.get("ancillaryParameters", {})
        )

    def __repr__(self) -> str:
        return f"{self._name} command"

    def _create_parameters(self, parameters: Dict) -> Dict[str, HonParameter]:
        result: Dict[str, HonParameter] = {}
        for parameter, attributes in parameters.items():
            if parameter == "zoneMap" and self._appliance.zone:
                attributes["default"] = self._appliance.zone
            match attributes.get("typology"):
                case "range":
                    result[parameter] = HonParameterRange(parameter, attributes)
                case "enum":
                    result[parameter] = HonParameterEnum(parameter, attributes)
                case "fixed":
                    result[parameter] = HonParameterFixed(parameter, attributes)
        if self._programs:
            result["program"] = HonParameterProgram("program", self)
        return result

    @property
    def parameters(self) -> Dict[str, HonParameter]:
        return self._parameters

    @property
    def ancillary_parameters(self) -> Dict[str, HonParameter]:
        return self._ancillary_parameters

    async def send(self) -> bool:
        params = {k: v.value for k, v in self._parameters.items()}
        ancillary_params = {k: v.value for k, v in self._ancillary_parameters.items()}
        return await self._api.send_command(
            self._appliance, self._name, params, ancillary_params
        )

    @property
    def programs(self) -> Dict[str, "HonCommand"]:
        if self._programs is None:
            return {}
        return self._programs

    @property
    def program(self) -> str:
        return self._program_name

    @program.setter
    def program(self, program: str) -> None:
        self._appliance.commands[self._name] = self.programs[program]

    def _get_settings_keys(self, command: Optional["HonCommand"] = None) -> List[str]:
        if command is None:
            command = self
        keys = []
        for key, parameter in (
            command._parameters | command._ancillary_parameters
        ).items():
            if key not in keys:
                keys.append(key)
        return keys

    @property
    def setting_keys(self) -> List[str]:
        if not self._programs:
            return self._get_settings_keys()
        result = [
            key
            for cmd in self._programs.values()
            for key in self._get_settings_keys(cmd)
        ]
        return list(set(result + ["program"]))

    @property
    def settings(self) -> Dict[str, HonParameter]:
        return {
            s: param
            for s in self.setting_keys
            if (param := self._parameters.get(s)) is not None
            or (param := self._ancillary_parameters.get(s)) is not None
        }
