import asyncio
from typing import List

from pyhon import HonAPI
from pyhon.appliance import HonAppliance


class Hon:
    def __init__(self, email, password, session=None):
        self._email = email
        self._password = password
        self._session = session
        self._appliances = []
        self._api = None

    async def __aenter__(self):
        return await self.create()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def create(self):
        self._api = await HonAPI(
            self._email, self._password, session=self._session
        ).create()
        await self.setup()
        return self

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

    async def close(self):
        await self._api.close()
