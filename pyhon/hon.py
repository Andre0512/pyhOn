import asyncio
from typing import List

from pyhon import HonAPI
from pyhon.appliance import HonAppliance


class Hon:
    def __init__(self, email, password):
        self._email = email
        self._password = password
        self._appliances = []
        self._api = None

    async def __aenter__(self):
        self._api = await HonAPI(self._email, self._password).create()
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._api.close()

    @property
    def appliances(self) -> List[HonAppliance]:
        return self._appliances

    async def setup(self):
        for appliance in (await self._api.load_appliances())["payload"]["appliances"]:
            appliance = HonAppliance(self._api, appliance)
            if appliance.mac_address is None:
                continue
            await asyncio.gather(
                *[
                    appliance.load_attributes(),
                    appliance.load_commands(),
                    appliance.load_statistics(),
                ]
            )
            self._appliances.append(appliance)
