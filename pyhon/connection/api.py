import json
import logging
from datetime import datetime
from typing import Dict, Optional

from aiohttp import ClientSession
from typing_extensions import Self

from pyhon import const, exceptions
from pyhon.appliance import HonAppliance
from pyhon.connection.auth import HonAuth
from pyhon.connection.handler.anonym import HonAnonymousConnectionHandler
from pyhon.connection.handler.hon import HonConnectionHandler

_LOGGER = logging.getLogger()


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

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def auth(self) -> HonAuth:
        if self._hon is None or self._hon.auth is None:
            raise exceptions.NoAuthenticationException
        return self._hon.auth

    @property
    def _hon(self):
        if self._hon_handler is None:
            raise exceptions.NoAuthenticationException
        return self._hon_handler

    @property
    def _hon_anonymous(self):
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

    async def load_appliances(self) -> Dict:
        async with self._hon.get(f"{const.API_URL}/commands/v1/appliance") as resp:
            return await resp.json()

    async def load_commands(self, appliance: HonAppliance) -> Dict:
        params: Dict = {
            "applianceType": appliance.appliance_type,
            "code": appliance.info["code"],
            "applianceModelId": appliance.appliance_model_id,
            "firmwareId": appliance.info["eepromId"],
            "macAddress": appliance.mac_address,
            "fwVersion": appliance.info["fwVersion"],
            "os": const.OS,
            "appVersion": const.APP_VERSION,
            "series": appliance.info["series"],
        }
        url: str = f"{const.API_URL}/commands/v1/retrieve"
        async with self._hon.get(url, params=params) as response:
            result: Dict = (await response.json()).get("payload", {})
            if not result or result.pop("resultCode") != "0":
                return {}
            return result

    async def command_history(self, appliance: HonAppliance) -> Dict:
        url: str = (
            f"{const.API_URL}/commands/v1/appliance/{appliance.mac_address}/history"
        )
        async with self._hon.get(url) as response:
            result: Dict = await response.json()
            if not result or not result.get("payload"):
                return {}
            return result["payload"]["history"]

    async def last_activity(self, appliance: HonAppliance) -> Dict:
        url: str = f"{const.API_URL}/commands/v1/retrieve-last-activity"
        params: Dict = {"macAddress": appliance.mac_address}
        async with self._hon.get(url, params=params) as response:
            result: Dict = await response.json()
            if result and (activity := result.get("attributes")):
                return activity
        return {}

    async def load_attributes(self, appliance: HonAppliance) -> Dict:
        params: Dict = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
            "category": "CYCLE",
        }
        url: str = f"{const.API_URL}/commands/v1/context"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def load_statistics(self, appliance: HonAppliance) -> Dict:
        params: Dict = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
        }
        url: str = f"{const.API_URL}/commands/v1/statistics"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def send_command(
        self,
        appliance: HonAppliance,
        command: str,
        parameters: Dict,
        ancillary_parameters: Dict,
    ) -> bool:
        now: str = datetime.utcnow().isoformat()
        data: Dict = {
            "macAddress": appliance.mac_address,
            "timestamp": f"{now[:-3]}Z",
            "commandName": command,
            "transactionId": f"{appliance.mac_address}_{now[:-3]}Z",
            "applianceOptions": appliance.commands_options,
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
            json_data: Dict = await response.json()
            if json_data.get("payload", {}).get("resultCode") == "0":
                return True
            _LOGGER.error(await response.text())
        return False

    async def appliance_configuration(self) -> Dict:
        url: str = f"{const.API_URL}/config/v1/appliance-configuration"
        async with self._hon_anonymous.get(url) as response:
            result: Dict = await response.json()
            if result and (data := result.get("payload")):
                return data
        return {}

    async def app_config(self, language: str = "en", beta: bool = True) -> Dict:
        url: str = f"{const.API_URL}/app-config"
        payload_data: Dict = {
            "languageCode": language,
            "beta": beta,
            "appVersion": const.APP_VERSION,
            "os": const.OS,
        }
        payload: str = json.dumps(payload_data, separators=(",", ":"))
        async with self._hon_anonymous.post(url, data=payload) as response:
            if (result := await response.json()) and (data := result.get("payload")):
                return data
        return {}

    async def translation_keys(self, language: str = "en") -> Dict:
        config = await self.app_config(language=language)
        if url := config.get("language", {}).get("jsonPath"):
            async with self._hon_anonymous.get(url) as response:
                if result := await response.json():
                    return result
        return {}

    async def close(self) -> None:
        if self._hon_handler is not None:
            await self._hon_handler.close()
        if self._hon_anonymous_handler is not None:
            await self._hon_anonymous_handler.close()
