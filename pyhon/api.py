import asyncio
import json
import logging
import secrets
from datetime import datetime
from typing import List

import aiohttp as aiohttp

from pyhon import const
from pyhon.auth import HonAuth
from pyhon.device import HonDevice

_LOGGER = logging.getLogger()


class HonConnection:
    def __init__(self, email, password, session=None) -> None:
        super().__init__()
        self._email = email
        self._password = password
        self._request_headers = {"Content-Type": "application/json"}
        self._session = session
        self._devices = []
        self._mobile_id = secrets.token_hex(8)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._session.close()

    @property
    def devices(self) -> List[HonDevice]:
        return self._devices

    @property
    async def _headers(self):
        if "cognito-token" not in self._request_headers or "id-token" not in self._request_headers:
            auth = HonAuth()
            if await auth.authorize(self._email, self._password, self._mobile_id):
                self._request_headers["cognito-token"] = auth.cognito_token
                self._request_headers["id-token"] = auth.id_token
            else:
                raise PermissionError("Can't Login")
        return self._request_headers

    async def setup(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{const.API_URL}/commands/v1/appliance",
                                   headers=await self._headers) as resp:
                try:
                    appliances = (await resp.json())["payload"]["appliances"]
                    for appliance in appliances:
                        device = HonDevice(self, appliance)
                        await asyncio.gather(*[
                            device.load_attributes(),
                            device.load_commands(),
                            device.load_statistics()])
                    self._devices.append(device)
                except json.JSONDecodeError:
                    _LOGGER.error("No JSON Data after GET: %s", await resp.text())
                    return False
        return True

    async def load_commands(self, device: HonDevice):
        params = {
            "applianceType": device.appliance_type_name,
            "code": device.code,
            "applianceModelId": device.appliance_model_id,
            "firmwareId": "41",
            "macAddress": device.mac_address,
            "fwVersion": device.fw_version,
            "os": const.OS,
            "appVersion": const.APP_VERSION,
            "series": device.series,
        }
        url = f"{const.API_URL}/commands/v1/retrieve"
        async with self._session.get(url, params=params, headers=await self._headers) as response:
            result = (await response.json()).get("payload", {})
            if not result or result.pop("resultCode") != "0":
                return {}
            return result

    async def load_attributes(self, device: HonDevice):
        params = {
            "macAddress": device.mac_address,
            "applianceType": device.appliance_type_name,
            "category": "CYCLE"
        }
        url = f"{const.API_URL}/commands/v1/context"
        async with self._session.get(url, params=params, headers=await self._headers) as response:
            return (await response.json()).get("payload", {})

    async def load_statistics(self, device: HonDevice):
        params = {
            "macAddress": device.mac_address,
            "applianceType": device.appliance_type_name
        }
        url = f"{const.API_URL}/commands/v1/statistics"
        async with self._session.get(url, params=params, headers=await self._headers) as response:
            return (await response.json()).get("payload", {})

    async def send_command(self, device, command, parameters, ancillary_parameters):
        now = datetime.utcnow().isoformat()
        data = {
            "macAddress": device.mac_address,
            "timestamp": f"{now[:-3]}Z",
            "commandName": command,
            "transactionId": f"{device.mac_address}_{now[:-3]}Z",
            "applianceOptions": device.commands_options,
            "device": {
                "mobileId": self._mobile_id,
                "mobileOs": const.OS,
                "osVersion": const.OS_VERSION,
                "appVersion": const.APP_VERSION,
                "deviceModel": const.DEVICE_MODEL
            },
            "attributes": {
                "channel": "mobileApp",
                "origin": "standardProgram",
                "energyLabel": "0"
            },
            "ancillaryParameters": ancillary_parameters,
            "parameters": parameters,
            "applianceType": device.appliance_type_name
        }
        url = f"{const.API_URL}/commands/v1/send"
        async with self._session.post(url, headers=await self._headers, json=data) as resp:
            try:
                json_data = await resp.json()
            except json.JSONDecodeError:
                return False
            if json_data["payload"]["resultCode"] == "0":
                return True
        return False
