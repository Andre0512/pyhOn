import importlib
from contextlib import suppress

from pyhon.commands import HonCommand
from pyhon.parameter import HonParameterFixed


class HonAppliance:
    def __init__(self, api, info):
        if attributes := info.get("attributes"):
            info["attributes"] = {v["parName"]: v["parValue"] for v in attributes}
        self._info = info
        self._api = api
        self._appliance_model = {}

        self._commands = {}
        self._statistics = {}
        self._attributes = {}

        try:
            self._extra = importlib.import_module(
                f"pyhon.appliances.{self.appliance_type.lower()}"
            ).Appliance()
        except ModuleNotFoundError:
            self._extra = None

    def __getitem__(self, item):
        if "." in item:
            result = self.data
            for key in item.split("."):
                if all([k in "0123456789" for k in key]) and type(result) is list:
                    result = result[int(key)]
                else:
                    result = result[key]
            return result
        else:
            if item in self.data:
                return self.data[item]
            if item in self.attributes["parameters"]:
                return self.attributes["parameters"].get(item)
            return self.info[item]

    def get(self, item, default=None):
        try:
            return self[item]
        except (KeyError, IndexError):
            return default

    @property
    def appliance_model_id(self):
        return self._info.get("applianceModelId")

    @property
    def appliance_type(self):
        return self._info.get("applianceTypeName")

    @property
    def mac_address(self):
        return self._info.get("macAddress")

    @property
    def model_name(self):
        return self._info.get("modelName")

    @property
    def nick_name(self):
        return self._info.get("nickName")

    @property
    def commands_options(self):
        return self._appliance_model.get("options")

    @property
    def commands(self):
        return self._commands

    @property
    def attributes(self):
        return self._attributes

    @property
    def statistics(self):
        return self._statistics

    @property
    def info(self):
        return self._info

    async def _recover_last_command_states(self, commands):
        command_history = await self._api.command_history(self)
        for name, command in commands.items():
            last = next(
                (
                    index
                    for (index, d) in enumerate(command_history)
                    if d.get("command", {}).get("commandName") == name
                ),
                None,
            )
            if last is None:
                continue
            parameters = command_history[last].get("command", {}).get("parameters", {})
            if command._multi and parameters.get("program"):
                command.set_program(parameters.pop("program").split(".")[-1].lower())
                command = self.commands[name]
            for key, data in command.settings.items():
                if (
                    not isinstance(data, HonParameterFixed)
                    and parameters.get(key) is not None
                ):
                    with suppress(ValueError):
                        data.value = parameters.get(key)

    async def load_commands(self):
        raw = await self._api.load_commands(self)
        self._appliance_model = raw.pop("applianceModel")
        for item in ["settings", "options", "dictionaryId"]:
            raw.pop(item)
        commands = {}
        for command, attr in raw.items():
            if "parameters" in attr:
                commands[command] = HonCommand(command, attr, self._api, self)
            elif "parameters" in attr[list(attr)[0]]:
                multi = {}
                for program, attr2 in attr.items():
                    program = program.split(".")[-1].lower()
                    cmd = HonCommand(
                        command, attr2, self._api, self, multi=multi, program=program
                    )
                    multi[program] = cmd
                    commands[command] = cmd
        self._commands = commands
        await self._recover_last_command_states(commands)

    @property
    def settings(self):
        result = {}
        for name, command in self._commands.items():
            for key, setting in command.settings.items():
                result[f"{name}.{key}"] = setting
        if self._extra:
            return self._extra.settings(result)
        return result

    @property
    def parameters(self):
        result = {}
        for name, command in self._commands.items():
            for key, parameter in command.parameters.items():
                result.setdefault(name, {})[key] = parameter.value
        return result

    async def load_attributes(self):
        self._attributes = await self._api.load_attributes(self)
        for name, values in self._attributes.pop("shadow").get("parameters").items():
            self._attributes.setdefault("parameters", {})[name] = values["parNewVal"]

    async def load_statistics(self):
        self._statistics = await self._api.load_statistics(self)

    async def update(self):
        await self.load_attributes()

    @property
    def data(self):
        result = {
            "attributes": self.attributes,
            "appliance": self.info,
            "statistics": self.statistics,
            **self.parameters,
        }
        if self._extra:
            return self._extra.data(result)
        return result
