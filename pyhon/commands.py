from pyhon.parameter import (
    HonParameterFixed,
    HonParameterEnum,
    HonParameterRange,
    HonParameterProgram,
)


class HonCommand:
    def __init__(self, name:str, attributes, connector, device, programs=None, program_name=""):
        self._connector = connector
        self._device = device
        self._name = name
        self._programs = programs or {}
        self._program_name = program_name
        self._description = attributes.get("description", "")
        self._parameters = self._create_parameters(attributes.get("parameters", {}))
        self._ancillary_parameters = self._create_parameters(
            attributes.get("ancillaryParameters", {})
        )

    def __repr__(self):
        return f"{self._name} command"

    def _create_parameters(self, parameters):
        result = {}
        for parameter, attributes in parameters.items():
            if parameter == "zoneMap" and self._device.zone:
                attributes["default"] = self._device.zone
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
    def parameters(self):
        return self._parameters

    @property
    def ancillary_parameters(self):
        return {
            key: parameter.value
            for key, parameter in self._ancillary_parameters.items()
        }

    async def send(self):
        parameters = {
            name: parameter.value for name, parameter in self._parameters.items()
        }
        return await self._connector.send_command(
            self._device, self._name, parameters, self.ancillary_parameters
        )

    @property
    def programs(self):
        return self._programs

    @property
    def program(self):
        return self._program_name

    @program.setter
    def program(self, program):
        self._device.commands[self._name] = self._programs[program]

    def _get_settings_keys(self, command=None):
        command = command or self
        keys = []
        for key, parameter in command._parameters.items():
            if isinstance(parameter, HonParameterFixed):
                continue
            if key not in keys:
                keys.append(key)
        return keys

    @property
    def setting_keys(self):
        if not self._programs:
            return self._get_settings_keys()
        result = [
            key for cmd in self._programs.values() for key in self._get_settings_keys(cmd)
        ]
        return list(set(result + ["program"]))

    @property
    def settings(self):
        """Parameters with typology enum and range"""
        return {
            s: self._parameters.get(s)
            for s in self.setting_keys
            if self._parameters.get(s) is not None
        }
