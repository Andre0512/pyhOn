import importlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

from pyhon import diagnose
from pyhon.attributes import HonAttribute
from pyhon.command_loader import HonCommandLoader
from pyhon.commands import HonCommand
from pyhon.parameter.base import HonParameter
from pyhon.parameter.range import HonParameterRange

if TYPE_CHECKING:
    from pyhon import HonAPI

_LOGGER = logging.getLogger(__name__)


class HonAppliance:
    _MINIMAL_UPDATE_INTERVAL = 5  # seconds

    def __init__(
        self, api: Optional["HonAPI"], info: Dict[str, Any], zone: int = 0
    ) -> None:
        if attributes := info.get("attributes"):
            info["attributes"] = {v["parName"]: v["parValue"] for v in attributes}
        self._info: Dict = info
        self._api: Optional[HonAPI] = api
        self._appliance_model: Dict = {}

        self._commands: Dict[str, HonCommand] = {}
        self._statistics: Dict = {}
        self._attributes: Dict = {}
        self._zone: int = zone
        self._additional_data: Dict[str, Any] = {}
        self._last_update = None
        self._default_setting = HonParameter("", {}, "")

        try:
            self._extra = importlib.import_module(
                f"pyhon.appliances.{self.appliance_type.lower()}"
            ).Appliance(self)
        except ModuleNotFoundError:
            self._extra = None

    def __getitem__(self, item):
        if self._zone:
            item += f"Z{self._zone}"
        if "." in item:
            result = self.data
            for key in item.split("."):
                if all(k in "0123456789" for k in key) and isinstance(result, list):
                    result = result[int(key)]
                else:
                    result = result[key]
            return result
        if item in self.data:
            return self.data[item]
        if item in self.attributes["parameters"]:
            return self.attributes["parameters"][item].value
        return self.info[item]

    def get(self, item, default=None):
        try:
            return self[item]
        except (KeyError, IndexError):
            return default

    def _check_name_zone(self, name: str, frontend: bool = True) -> str:
        middle = " Z" if frontend else "_z"
        if (attribute := self._info.get(name, "")) and self._zone:
            return f"{attribute}{middle}{self._zone}"
        return attribute

    @property
    def appliance_model_id(self) -> str:
        return self._info.get("applianceModelId", "")

    @property
    def appliance_type(self) -> str:
        return self._info.get("applianceTypeName", "")

    @property
    def mac_address(self) -> str:
        return self.info.get("macAddress", "")

    @property
    def unique_id(self) -> str:
        return self._check_name_zone("macAddress", frontend=False)

    @property
    def model_name(self) -> str:
        return self._check_name_zone("modelName")

    @property
    def brand(self) -> str:
        return self._check_name_zone("brand")

    @property
    def nick_name(self) -> str:
        return self._check_name_zone("nickName")

    @property
    def code(self) -> str:
        if code := self.info.get("code"):
            return code
        serial_number = self.info.get("serialNumber", "")
        return serial_number[:8] if len(serial_number) < 18 else serial_number[:11]

    @property
    def model_id(self) -> int:
        return self._info.get("applianceModelId", 0)

    @property
    def options(self):
        return self._appliance_model.get("options", {})

    @property
    def commands(self) -> Dict[str, HonCommand]:
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

    @property
    def additional_data(self):
        return self._additional_data

    @property
    def zone(self) -> int:
        return self._zone

    @property
    def api(self) -> Optional["HonAPI"]:
        return self._api

    async def load_commands(self):
        command_loader = HonCommandLoader(self.api, self)
        await command_loader.load_commands()
        self._commands = command_loader.commands
        self._additional_data = command_loader.additional_data
        self._appliance_model = command_loader.appliance_data

    async def load_attributes(self):
        self._attributes = await self.api.load_attributes(self)
        for name, values in self._attributes.pop("shadow").get("parameters").items():
            if name in self._attributes.get("parameters", {}):
                self._attributes["parameters"][name].update(values)
            else:
                self._attributes.setdefault("parameters", {})[name] = HonAttribute(
                    values
                )
        if self._extra:
            self._attributes = self._extra.attributes(self._attributes)

    async def load_statistics(self):
        self._statistics = await self.api.load_statistics(self)
        self._statistics |= await self.api.load_maintenance(self)

    async def update(self, force=False):
        now = datetime.now()
        if (
            force
            or not self._last_update
            or self._last_update
            < now - timedelta(seconds=self._MINIMAL_UPDATE_INTERVAL)
        ):
            self._last_update = now
            await self.load_attributes()

    @property
    def command_parameters(self):
        return {n: c.parameter_value for n, c in self._commands.items()}

    @property
    def settings(self):
        result = {}
        for name, command in self._commands.items():
            for key in command.setting_keys:
                setting = command.settings.get(key, self._default_setting)
                result[f"{name}.{key}"] = setting
        if self._extra:
            return self._extra.settings(result)
        return result

    @property
    def available_settings(self):
        result = []
        for name, command in self._commands.items():
            for key in command.setting_keys:
                result.append(f"{name}.{key}")
        return result

    @property
    def data(self):
        result = {
            "attributes": self.attributes,
            "appliance": self.info,
            "statistics": self.statistics,
            "additional_data": self._additional_data,
            **self.command_parameters,
            **self.attributes,
        }
        return result

    @property
    def diagnose(self) -> str:
        return diagnose.yaml_export(self, anonymous=True)

    async def data_archive(self, path: Path) -> str:
        return await diagnose.zip_archive(self, path, anonymous=True)

    def sync_to_params(self, command_name):
        command: HonCommand = self.commands.get(command_name)
        for key, value in self.attributes.get("parameters", {}).items():
            if isinstance(value, str) and (new := command.parameters.get(key)):
                self.attributes["parameters"][key].update(
                    str(new.intern_value), shield=True
                )

    def sync_command(self, main, target=None) -> None:
        base: Optional[HonCommand] = self.commands.get(main)
        if not base:
            return
        for command, data in self.commands.items():
            if command == main or target and command not in target:
                continue
            for name, parameter in data.parameters.items():
                if base_value := base.parameters.get(name):
                    if isinstance(base_value, HonParameterRange) and isinstance(
                        parameter, HonParameterRange
                    ):
                        parameter.max = base_value.max
                        parameter.min = base_value.min
                        parameter.step = base_value.step
                    elif isinstance(parameter, HonParameterRange):
                        parameter.max = int(base_value.value)
                        parameter.min = int(base_value.value)
                        parameter.step = 1
                    parameter.value = base_value.value
