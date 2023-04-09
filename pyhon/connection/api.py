import asyncio
import json
import logging
from datetime import datetime
from typing import List

from pyhon import const
from pyhon.appliance import HonAppliance
from pyhon.connection.connection import HonConnectionHandler, HonAnonymousConnectionHandler

_LOGGER = logging.getLogger()


class HonAPI:
    def __init__(self, email="", password="") -> None:
        super().__init__()
        self._email = email
        self._password = password
        self._devices = []
        self._hon = None
        self._hon_anonymous = HonAnonymousConnectionHandler()

    async def __aenter__(self):
        self._hon = HonConnectionHandler(self._email, self._password)
        await self._hon.create()
        await self.setup()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._hon.close()

    @property
    def devices(self) -> List[HonAppliance]:
        return self._devices

    async def setup(self):
        async with self._hon.get(f"{const.API_URL}/commands/v1/appliance") as resp:
            try:
                appliances = (await resp.json())["payload"]["appliances"]
                for appliance in appliances:
                    device = HonAppliance(self, appliance)
                    if device.mac_address is None:
                        continue
                    await asyncio.gather(*[
                        device.load_attributes(),
                        device.load_commands(),
                        device.load_statistics()])
                    self._devices.append(device)
            except json.JSONDecodeError:
                _LOGGER.error("No JSON Data after GET: %s", await resp.text())
                return False
        return True

    async def load_commands(self, device: HonAppliance):
        params = {
            "applianceType": device.appliance_type,
            "code": device.appliance["code"],
            "applianceModelId": device.appliance_model_id,
            "firmwareId": device.appliance["eepromId"],
            "macAddress": device.mac_address,
            "fwVersion": device.appliance["fwVersion"],
            "os": const.OS,
            "appVersion": const.APP_VERSION,
            "series": device.appliance["series"],
        }
        url = f"{const.API_URL}/commands/v1/retrieve"
        async with self._hon.get(url, params=params) as response:
            result = (await response.json()).get("payload", {})
            if not result or result.pop("resultCode") != "0":
                return {}
            return result

    async def command_history(self, device: HonAppliance):
        url = f"{const.API_URL}/commands/v1/appliance/{device.mac_address}/history"
        async with self._hon.get(url) as response:
            result = await response.json()
            if not result or not result.get("payload"):
                return {}
            return result["payload"]["history"]

    async def last_activity(self, device: HonAppliance):
        url = f"{const.API_URL}/commands/v1/retrieve-last-activity"
        params = {"macAddress": device.mac_address}
        async with self._hon.get(url, params=params) as response:
            result = await response.json()
            if result and (activity := result.get("attributes")):
                return activity
        return {}

    async def load_attributes(self, device: HonAppliance):
        params = {
            "macAddress": device.mac_address,
            "applianceType": device.appliance_type,
            "category": "CYCLE"
        }
        url = f"{const.API_URL}/commands/v1/context"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def load_statistics(self, device: HonAppliance):
        params = {
            "macAddress": device.mac_address,
            "applianceType": device.appliance_type
        }
        url = f"{const.API_URL}/commands/v1/statistics"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def send_command(self, device, command, parameters, ancillary_parameters):
        now = datetime.utcnow().isoformat()
        data = {
            "macAddress": device.mac_address,
            "timestamp": f"{now[:-3]}Z",
            "commandName": command,
            "transactionId": f"{device.mac_address}_{now[:-3]}Z",
            "applianceOptions": device.commands_options,
            "device": self._hon.device.get(),
            "attributes": {
                "channel": "mobileApp",
                "origin": "standardProgram",
                "energyLabel": "0"
            },
            "ancillaryParameters": ancillary_parameters,
            "parameters": parameters,
            "applianceType": device.appliance_type
        }
        url = f"{const.API_URL}/commands/v1/send"
        async with self._hon.post(url, json=data) as resp:
            try:
                json_data = await resp.json()
            except json.JSONDecodeError:
                return False
            if json_data["payload"]["resultCode"] == "0":
                return True
        return False

    async def appliance_configuration(self):
        url = f"{const.API_URL}/config/v1/appliance-configuration"
        async with self._hon_anonymous.get(url) as response:
            result = await response.json()
            if result and (data := result.get("payload")):
                return data
        return {}

    async def app_config(self, language="en", beta=True):
        url = f"{const.API_URL}/app-config"
        payload = {
            "languageCode": language,
            "beta": beta,
            "appVersion": const.APP_VERSION,
            "os": const.OS
        }
        payload = json.dumps(payload, separators=(',', ':'))
        async with self._hon_anonymous.post(url, data=payload) as response:
            if (result := await response.json()) and (data := result.get("payload")):
                return data
        return {}

    async def translation_keys(self, language="en"):
        config = await self.app_config(language=language)
        if url := config.get("language", {}).get("jsonPath"):
            async with self._hon_anonymous.get(url) as response:
                if result := await response.json():
                    return result
        return {}
