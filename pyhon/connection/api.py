import json
import logging
from datetime import datetime

from pyhon import const
from pyhon.appliance import HonAppliance
from pyhon.connection.handler import HonConnectionHandler, HonAnonymousConnectionHandler

_LOGGER = logging.getLogger()


class HonAPI:
    def __init__(self, email="", password="", anonymous=False, session=None) -> None:
        super().__init__()
        self._email = email
        self._password = password
        self._anonymous = anonymous
        self._hon = None
        self._hon_anonymous = None
        self._session = session

    async def __aenter__(self):
        return await self.create()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def create(self):
        self._hon_anonymous = await HonAnonymousConnectionHandler(
            self._session
        ).create()
        if not self._anonymous:
            self._hon = await HonConnectionHandler(
                self._email, self._password, self._session
            ).create()
        return self

    async def load_appliances(self):
        async with self._hon.get(f"{const.API_URL}/commands/v1/appliance") as resp:
            return await resp.json()

    async def load_commands(self, appliance: HonAppliance):
        params = {
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
        url = f"{const.API_URL}/commands/v1/retrieve"
        async with self._hon.get(url, params=params) as response:
            result = (await response.json()).get("payload", {})
            if not result or result.pop("resultCode") != "0":
                return {}
            return result

    async def command_history(self, appliance: HonAppliance):
        url = f"{const.API_URL}/commands/v1/appliance/{appliance.mac_address}/history"
        async with self._hon.get(url) as response:
            result = await response.json()
            if not result or not result.get("payload"):
                return {}
            return result["payload"]["history"]

    async def last_activity(self, appliance: HonAppliance):
        url = f"{const.API_URL}/commands/v1/retrieve-last-activity"
        params = {"macAddress": appliance.mac_address}
        async with self._hon.get(url, params=params) as response:
            result = await response.json()
            if result and (activity := result.get("attributes")):
                return activity
        return {}

    async def load_attributes(self, appliance: HonAppliance):
        params = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
            "category": "CYCLE",
        }
        url = f"{const.API_URL}/commands/v1/context"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def load_statistics(self, appliance: HonAppliance):
        params = {
            "macAddress": appliance.mac_address,
            "applianceType": appliance.appliance_type,
        }
        url = f"{const.API_URL}/commands/v1/statistics"
        async with self._hon.get(url, params=params) as response:
            return (await response.json()).get("payload", {})

    async def send_command(self, appliance, command, parameters, ancillary_parameters):
        now = datetime.utcnow().isoformat()
        data = {
            "macAddress": appliance.mac_address,
            "timestamp": f"{now[:-3]}Z",
            "commandName": command,
            "transactionId": f"{appliance.mac_address}_{now[:-3]}Z",
            "applianceOptions": appliance.commands_options,
            "appliance": self._hon.device.get(),
            "attributes": {
                "channel": "mobileApp",
                "origin": "standardProgram",
                "energyLabel": "0",
            },
            "ancillaryParameters": ancillary_parameters,
            "parameters": parameters,
            "applianceType": appliance.appliance_type,
        }
        url = f"{const.API_URL}/commands/v1/send"
        async with self._hon.post(url, json=data) as resp:
            json_data = await resp.json()
            if json_data.get("payload", {}).get("resultCode") == "0":
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
            "os": const.OS,
        }
        payload = json.dumps(payload, separators=(",", ":"))
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

    async def close(self):
        if self._hon:
            await self._hon.close()
        if self._hon_anonymous:
            await self._hon_anonymous.close()
