from parameter import HonParameterFixed, HonParameterEnum, HonParameterRange


class HonCommand:
    def __init__(self, name, attributes, connector, device, multi=None):
        self._connector = connector
        self._device = device
        self._name = name
        self._description = attributes.get("description", "")
        self._parameters = self._create_parameters(attributes.get("parameters", {}))
        self._ancillary_parameters = self._create_parameters(attributes.get("ancillaryParameters", {}))
        self._multi = multi

    def _create_parameters(self, parameters):
        result = {}
        for parameter, attributes in parameters.items():
            match attributes.get("typology"):
                case "range":
                    result[parameter] = HonParameterRange(parameter, attributes)
                case "enum":
                    result[parameter] = HonParameterEnum(parameter, attributes)
                case "fixed":
                    result[parameter] = HonParameterFixed(parameter, attributes)
        return result

    @property
    def parameters(self):
        return {key: parameter.value for key, parameter in self._parameters.items()}

    @property
    def ancillary_parameters(self):
        return {key: parameter.value for key, parameter in self._ancillary_parameters.items()}

    async def send(self):
        return await self._connector.send_command(self._device, self._name, self.parameters,
                                                  self.ancillary_parameters)

    async def get_programs(self):
        return self._multi

    async def set_program(self, program):
        self._device.commands[self._name] = self._multi[program]
