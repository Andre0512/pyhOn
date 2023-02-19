from pyhon.commands import HonCommand


class HonDevice:
    def __init__(self, connector, appliance):
        self._appliance = appliance
        self._connector = connector
        self._appliance_model = {}

        self._commands = {}
        self._statistics = {}
        self._attributs = {}

    @property
    def appliance_id(self):
        return self._appliance.get("applianceId")

    @property
    def appliance_model_id(self):
        return self._appliance.get("applianceModelId")

    @property
    def appliance_status(self):
        return self._appliance.get("applianceStatus")

    @property
    def appliance_type_id(self):
        return self._appliance.get("applianceTypeId")

    @property
    def appliance_type_name(self):
        return self._appliance.get("applianceTypeName")

    @property
    def brand(self):
        return self._appliance.get("brand")

    @property
    def code(self):
        return self._appliance.get("code")

    @property
    def connectivity(self):
        return self._appliance.get("connectivity")

    @property
    def coords(self):
        return self._appliance.get("coords")

    @property
    def eeprom_id(self):
        return self._appliance.get("eepromId")

    @property
    def eeprom_name(self):
        return self._appliance.get("eepromName")

    @property
    def enrollment_date(self):
        return self._appliance.get("enrollmentDate")

    @property
    def first_enrollment(self):
        return self._appliance.get("firstEnrollment")

    @property
    def first_enrollment_tbc(self):
        return self._appliance.get("firstEnrollmentTBC")

    @property
    def fw_version(self):
        return self._appliance.get("fwVersion")

    @property
    def id(self):
        return self._appliance.get("id")

    @property
    def last_update(self):
        return self._appliance.get("lastUpdate")

    @property
    def mac_address(self):
        return self._appliance.get("macAddress")

    @property
    def model_name(self):
        return self._appliance.get("modelName")

    @property
    def nick_name(self):
        return self._appliance.get("nickName")

    @property
    def purchase_date(self):
        return self._appliance.get("purchaseDate")

    @property
    def serial_number(self):
        return self._appliance.get("serialNumber")

    @property
    def series(self):
        return self._appliance.get("series")

    @property
    def water_hard(self):
        return self._appliance.get("waterHard")

    @property
    def commands_options(self):
        return self._appliance_model.get("options")

    @property
    def commands(self):
        return self._commands

    @property
    def attributes(self):
        return self._attributs

    @property
    def statistics(self):
        return self._statistics

    async def load_commands(self):
        raw = await self._connector.load_commands(self)
        self._appliance_model = raw.pop("applianceModel")
        for item in ["settings", "options", "dictionaryId"]:
            raw.pop(item)
        commands = {}
        for command, attr in raw.items():
            if "parameters" in attr:
                commands[command] = HonCommand(command, attr, self._connector, self)
            elif "parameters" in attr[list(attr)[0]]:
                multi = {}
                for category, attr2 in attr.items():
                    cmd = HonCommand(command, attr2, self._connector, self, multi=multi, category=category)
                    multi[category] = cmd
                    commands[command] = cmd
        self._commands = commands

    @property
    def settings(self):
        result = {}
        for name, command in self._commands.items():
            for key, setting in command.settings.items():
                result[f"{name}.{key}"] = setting
        return result

    @property
    def parameters(self):
        result = {}
        for name, command in self._commands.items():
            for key, parameter in command.parameters.items():
                result[f"{name}.{key}"] = parameter
        return result

    async def load_attributes(self):
        data = await self._connector.load_attributes(self)
        for name, values in data.get("shadow").get("parameters").items():
            self._attributs[name] = values["parNewVal"]

    async def load_statistics(self):
        self._statistics = await self._connector.load_statistics(self)

    async def update(self):
        await self.load_attributes()
