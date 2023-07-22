import asyncio
from contextlib import suppress
from copy import copy
from typing import Dict, Any, Optional, TYPE_CHECKING, List, Collection

from pyhon.commands import HonCommand
from pyhon.parameter.fixed import HonParameterFixed
from pyhon.parameter.program import HonParameterProgram

if TYPE_CHECKING:
    from pyhon import HonAPI, exceptions
    from pyhon.appliance import HonAppliance


class HonCommandLoader:
    """Loads and parses hOn command data"""

    def __init__(self, api: "HonAPI", appliance: "HonAppliance") -> None:
        self._api_commands: Dict[str, Any] = {}
        self._favourites: List[Dict[str, Any]] = []
        self._command_history: List[Dict[str, Any]] = []
        self._commands: Dict[str, HonCommand] = {}
        self._api: "HonAPI" = api
        self._appliance: "HonAppliance" = appliance
        self._appliance_data: Dict[str, Any] = {}
        self._additional_data: Dict[str, Any] = {}

    @property
    def api(self) -> "HonAPI":
        """api connection object"""
        if self._api is None:
            raise exceptions.NoAuthenticationException("Missing hOn login")
        return self._api

    @property
    def appliance(self) -> "HonAppliance":
        """appliance object"""
        return self._appliance

    @property
    def commands(self) -> Dict[str, HonCommand]:
        """Get list of hon commands"""
        return self._commands

    @property
    def appliance_data(self) -> Dict[str, Any]:
        """Get command appliance data"""
        return self._appliance_data

    @property
    def additional_data(self) -> Dict[str, Any]:
        """Get command additional data"""
        return self._additional_data

    async def load_commands(self) -> None:
        """Trigger loading of command data"""
        await self._load_data()
        self._appliance_data = self._api_commands.pop("applianceModel", {})
        self._get_commands()
        self._add_favourites()
        self._recover_last_command_states()

    async def _load_commands(self) -> None:
        self._api_commands = await self._api.load_commands(self._appliance)

    async def _load_favourites(self) -> None:
        self._favourites = await self._api.load_favourites(self._appliance)

    async def _load_command_history(self) -> None:
        self._command_history = await self._api.load_command_history(self._appliance)

    async def _load_data(self) -> None:
        """Callback parallel all relevant data"""
        await asyncio.gather(
            *[
                self._load_commands(),
                self._load_favourites(),
                self._load_command_history(),
            ]
        )

    @staticmethod
    def _is_command(data: Dict[str, Any]) -> bool:
        """Check if dict can be parsed as command"""
        return (
            data.get("description") is not None and data.get("protocolType") is not None
        )

    @staticmethod
    def _clean_name(category: str) -> str:
        """Clean up category name"""
        if "PROGRAM" in category:
            return category.split(".")[-1].lower()
        return category

    def _get_commands(self) -> None:
        """Generates HonCommand dict from api data"""
        commands = []
        for name, data in self._api_commands.items():
            if command := self._parse_command(data, name):
                commands.append(command)
        self._commands = {c.name: c for c in commands}

    def _parse_command(
        self,
        data: Dict[str, Any] | str,
        command_name: str,
        categories: Optional[Dict[str, "HonCommand"]] = None,
        category_name: str = "",
    ) -> Optional[HonCommand]:
        """Try to crate HonCommand object"""
        if not isinstance(data, dict):
            self._additional_data[command_name] = data
            return None
        if self._is_command(data):
            return HonCommand(
                command_name,
                data,
                self._appliance,
                category_name=category_name,
                categories=categories,
            )
        if category := self._parse_categories(data, command_name):
            return category
        return None

    def _parse_categories(
        self, data: Dict[str, Any], command_name: str
    ) -> Optional[HonCommand]:
        """Parse categories and create reference to other"""
        categories: Dict[str, HonCommand] = {}
        for category, value in data.items():
            if command := self._parse_command(
                value, command_name, category_name=category, categories=categories
            ):
                categories[self._clean_name(category)] = command
        if categories:
            # setParameters should be at first place
            if "setParameters" in categories:
                return categories["setParameters"]
            return list(categories.values())[0]
        return None

    def _get_last_command_index(self, name: str) -> Optional[int]:
        """Get index of last command execution"""
        return next(
            (
                index
                for (index, d) in enumerate(self._command_history)
                if d.get("command", {}).get("commandName") == name
            ),
            None,
        )

    def _set_last_category(
        self, command: HonCommand, name: str, parameters: Dict[str, Any]
    ) -> HonCommand:
        """Set category to last state"""
        if command.categories:
            if program := parameters.pop("program", None):
                command.category = self._clean_name(program)
            elif category := parameters.pop("category", None):
                command.category = category
            else:
                return command
            return self.commands[name]
        return command

    def _recover_last_command_states(self) -> None:
        """Set commands to last state"""
        for name, command in self.commands.items():
            if (last_index := self._get_last_command_index(name)) is None:
                continue
            last_command = self._command_history[last_index]
            parameters = last_command.get("command", {}).get("parameters", {})
            command = self._set_last_category(command, name, parameters)
            for key, data in command.settings.items():
                if parameters.get(key) is None:
                    continue
                with suppress(ValueError):
                    data.value = parameters.get(key)

    def _add_favourites(self) -> None:
        """Patch program categories with favourites"""
        for favourite in self._favourites:
            name = favourite.get("favouriteName", {})
            command = favourite.get("command", {})
            command_name = command.get("commandName", "")
            program_name = self._clean_name(command.get("programName", ""))
            if not (base := self.commands[command_name].categories.get(program_name)):
                continue
            base_command: HonCommand = copy(base)
            for data in command.values():
                if isinstance(data, str):
                    continue
                for key, value in data.items():
                    if parameter := base_command.parameters.get(key):
                        with suppress(ValueError):
                            parameter.value = value
            extra_param = HonParameterFixed("favourite", {"fixedValue": "1"}, "custom")
            base_command.parameters.update(favourite=extra_param)
            program = base_command.parameters["program"]
            if isinstance(program, HonParameterProgram):
                program.set_value(name)
            self.commands[command_name].categories[name] = base_command
