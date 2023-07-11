import json
import logging
from datetime import datetime
from pathlib import Path
from pprint import pformat
from types import TracebackType
from typing import Dict, Optional, Any, List, no_type_check, Type

from aiohttp import ClientSession
from typing_extensions import Self

from pyhon import const, exceptions
from pyhon.appliance import HonAppliance
from pyhon.connection.auth import HonAuth
from pyhon.connection.handler.anonym import HonAnonymousConnectionHandler
from pyhon.connection.handler.hon import HonConnectionHandler

_LOGGER = logging.getLogger(__name__)


class HonAPI:
    def __init__(
        self,
        email: str = "",
        password: str = "",
        anonymous: bool = False,
        session: Optional[ClientSession] = None,
    ) -> None:
        super().__init__()
        self._email: str = email
        self._password: str = password
        self._anonymous: bool = anonymous
        self._hon_handler: Optional[HonConnectionHandler] = None
        self._hon_anonymous_handler: Optional[HonAnonymousConnectionHandler] = None
        self._session: Optional[ClientSession] = session

    async def __aenter__(self) -> Self:
        return await self.create()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self.close()

    @property
    def auth(self) -> HonAuth:
        if self._hon is None or self._hon.auth is None:
            raise exceptions.NoAuthenticationException
        return self._hon.auth

    @property
    def _hon(self) -> HonConnectionHandler:
        if self._hon_handler is None:
            raise exceptions.NoAuthenticationException
        return self._hon_handler

    @property
    def _hon_anonymous(self) -> HonAnonymousConnectionHandler:
        if self._hon_anonymous_handler is None:
            raise exceptions.NoAuthenticationException
        return self._hon_anonymous_handler

    async def create(self) -> Self:
        self._hon_anonymous_handler = await HonAnonymousConnectionHandler(
            self._session
        ).create()
        if not self._anonymous:
            self._hon_handler = await HonConnectionHandler(
                self._email, self._password, self._session
            ).create()
        return self

    async def load_appliances(self) -> List[Dict[str, Any]]:
        async with self._hon.get(f"{const.API_URL}/commands/v1/appliance") as resp:
            result = await resp.json()
        if result:
            appliances: List[Dict[str, Any]] = result.get("payload", {}).get(
                "appliances", {}
            )
            return appliances
        return []

    async def load_commands(self, appliance: HonAppliance) -> Dict[str, Any]:
        params: Dict[str, str | int] = {
            "applianceType": appliance.appliance_type,
            "applianceModelId": appliance.appliance_model_id,
            "macAddress": appliance.mac_address,
            "os": const.OS,
            "appVersion": const.APP_VERSION,
            "code": appliance.code,
        }
        if firmware_id := appliance.info.get("eepromId"):
            params["firmwareId"] = firmware_id
        if firmware_version := appliance.info.get("fwVersion"):
            params["fwVersion"] = firmware_version
        if series := appliance.info.get("series"):
            params["series"] = series
        url: str = f"{const.API_URL}/commands/v1/retrieve"
        async with self._hon.get(url, params=params) as response:
            result: Dict[str, Any] = (await response.json()).get("payload", {})
            if not result or result.pop("resultCode") != "0":
                _LOGGER.error(await response.json())
                return {}
            return result

    async def load_command_history(
        self, appliance: HonAppliance
    ) -> List[Dict[str, Any]]:
        url: str = (
            f"{const.API_URL}/commands/v1/appliance/{appliance.mac_address}/history"
        )
        async with self._hon.get(url) as response:
            result: Dict[str, Any] = await response.json()
        if not result or not result.get("payload"):
            return []
        command_history: List[Dict[str, Any]] = result["payload"]["history"]
        return command_history

    async def load_favourites(self, appliance: HonAppliance) -> List[Dict[str, Any]]:
        url: str = (
            f"{const.API_URL}/commands/v1/appliance/{appliance.mac_address}/favourite"
        )
        async with self._hon.get(url) as response:
            result: Dict[str, Any] = await response.json()
        if not result or not result.get("payload"):
            return []
        favourites: List[Dict[str, Any]] = result["payload"]["favourites"]
        return favourites

    async def load_last_activity(self, appliance: HonAppliance) -> Dict[str, Any]:
        url: str = f"{const.API_URL}/commands/v1/retrieve-last-activity"
        params: Dict[str, str] = {"macAddress": appliance.mac_address}
        async with self._hon.get(url, params=params) as response:
            result: Dict[str, Any] = await response.json()
            if result:
                activity: Dict[str, Any] = result.get("attributes", "")
                if activity:
                    return activity
        return {}

    async def load_appliance_data(self, appliance: HonAppliance) -> Dict[str, Any]:
        url: str = f"{const.API_URL}/commands/v1/appliance-model"
        params: Dict[str, str] = {
            "code": appliance.code,
            "macAddress": appliance.mac_address,
        }
        async with self._hon.get(url, params=params) as response:
            result: Dict[str, Any] = await response.json()
            if result:
                appliance_data: Dict[str, Any] = result.get("payload", {}).get(
                    "applianceModel", {}
                )
                return appliance_data
        return {}

    async def load_attributes(self, appliance: HonAppliance) -> Dict[str, Any]:
        params: Dict[str, str] = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
            "category": "CYCLE",
        }
        url: str = f"{const.API_URL}/commands/v1/context"
        async with self._hon.get(url, params=params) as response:
            attributes: Dict[str, Any] = (await response.json()).get("payload", {})
        return attributes

    async def load_statistics(self, appliance: HonAppliance) -> Dict[str, Any]:
        params: Dict[str, str] = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
        }
        url: str = f"{const.API_URL}/commands/v1/statistics"
        async with self._hon.get(url, params=params) as response:
            statistics: Dict[str, Any] = (await response.json()).get("payload", {})
        return statistics

    async def load_maintenance(self, appliance: HonAppliance) -> Dict[str, Any]:
        url = f"{const.API_URL}/commands/v1/maintenance-cycle"
        params = {"macAddress": appliance.mac_address}
        async with self._hon.get(url, params=params) as response:
            maintenance: Dict[str, Any] = (await response.json()).get("payload", {})
        return maintenance

    async def send_command(
        self,
        appliance: HonAppliance,
        command: str,
        parameters: Dict[str, Any],
        ancillary_parameters: Dict[str, Any],
    ) -> bool:
        now: str = datetime.utcnow().isoformat()
        data: Dict[str, Any] = {
            "macAddress": appliance.mac_address,
            "timestamp": f"{now[:-3]}Z",
            "commandName": command,
            "transactionId": f"{appliance.mac_address}_{now[:-3]}Z",
            "applianceOptions": appliance.options,
            "device": self._hon.device.get(mobile=True),
            "attributes": {
                "channel": "mobileApp",
                "origin": "standardProgram",
                "energyLabel": "0",
            },
            "ancillaryParameters": ancillary_parameters,
            "parameters": parameters,
            "applianceType": appliance.appliance_type,
        }
        url: str = f"{const.API_URL}/commands/v1/send"
        async with self._hon.post(url, json=data) as response:
            json_data: Dict[str, Any] = await response.json()
            if json_data.get("payload", {}).get("resultCode") == "0":
                return True
            _LOGGER.error(await response.text())
            _LOGGER.error("%s - Payload:\n%s", url, pformat(data))
        return False

    async def appliance_configuration(self) -> Dict[str, Any]:
        url: str = f"{const.API_URL}/config/v1/program-list-rules"
        async with self._hon_anonymous.get(url) as response:
            result: Dict[str, Any] = await response.json()
        data: Dict[str, Any] = result.get("payload", {})
        return data

    async def app_config(
        self, language: str = "en", beta: bool = True
    ) -> Dict[str, Any]:
        url: str = f"{const.API_URL}/app-config"
        payload_data: Dict[str, str | int] = {
            "languageCode": language,
            "beta": beta,
            "appVersion": const.APP_VERSION,
            "os": const.OS,
        }
        payload: str = json.dumps(payload_data, separators=(",", ":"))
        async with self._hon_anonymous.post(url, data=payload) as response:
            result = await response.json()
        data: Dict[str, Any] = result.get("payload", {})
        return data

    async def translation_keys(self, language: str = "en") -> Dict[str, Any]:
        config = await self.app_config(language=language)
        if not (url := config.get("language", {}).get("jsonPath")):
            return {}
        async with self._hon_anonymous.get(url) as response:
            result: Dict[str, Any] = await response.json()
        return result

    async def close(self) -> None:
        if self._hon_handler is not None:
            await self._hon_handler.close()
        if self._hon_anonymous_handler is not None:
            await self._hon_anonymous_handler.close()


class TestAPI(HonAPI):
    def __init__(self, path: Path):
        super().__init__()
        self._anonymous = True
        self._path: Path = path

    def _load_json(self, appliance: HonAppliance, file: str) -> Dict[str, Any]:
        directory = f"{appliance.appliance_type}_{appliance.appliance_model_id}".lower()
        if not (path := self._path / directory / f"{file}.json").exists():
            _LOGGER.warning("Can't open %s", str(path))
            return {}
        with open(path, "r", encoding="utf-8") as json_file:
            text = json_file.read()
        try:
            data: Dict[str, Any] = json.loads(text)
            return data
        except json.decoder.JSONDecodeError as error:
            _LOGGER.error("%s - %s", str(path), error)
            return {}

    async def load_appliances(self) -> List[Dict[str, Any]]:
        result = []
        for appliance in self._path.glob("*/"):
            with open(
                appliance / "appliance_data.json", "r", encoding="utf-8"
            ) as json_file:
                result.append(json.loads(json_file.read()))
        return result

    async def load_commands(self, appliance: HonAppliance) -> Dict[str, Any]:
        return self._load_json(appliance, "commands")

    @no_type_check
    async def load_command_history(
        self, appliance: HonAppliance
    ) -> List[Dict[str, Any]]:
        return self._load_json(appliance, "command_history")

    async def load_favourites(self, appliance: HonAppliance) -> List[Dict[str, Any]]:
        return []

    async def load_last_activity(self, appliance: HonAppliance) -> Dict[str, Any]:
        return {}

    async def load_appliance_data(self, appliance: HonAppliance) -> Dict[str, Any]:
        return self._load_json(appliance, "appliance_data")

    async def load_attributes(self, appliance: HonAppliance) -> Dict[str, Any]:
        return self._load_json(appliance, "attributes")

    async def load_statistics(self, appliance: HonAppliance) -> Dict[str, Any]:
        return self._load_json(appliance, "statistics")

    async def load_maintenance(self, appliance: HonAppliance) -> Dict[str, Any]:
        return self._load_json(appliance, "maintenance")

    async def send_command(
        self,
        appliance: HonAppliance,
        command: str,
        parameters: Dict[str, Any],
        ancillary_parameters: Dict[str, Any],
    ) -> bool:
        return True
