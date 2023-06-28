import asyncio
import logging
from pathlib import Path
from types import TracebackType
from typing import List, Optional, Dict, Any, Type

from aiohttp import ClientSession
from typing_extensions import Self

from pyhon import HonAPI, exceptions
from pyhon.appliance import HonAppliance
from pyhon.connection.api import TestAPI

_LOGGER = logging.getLogger(__name__)


class Hon:
    def __init__(
        self,
        email: Optional[str] = "",
        password: Optional[str] = "",
        session: Optional[ClientSession] = None,
        test_data_path: Optional[Path] = None,
    ):
        self._email: Optional[str] = email
        self._password: Optional[str] = password
        self._session: ClientSession | None = session
        self._appliances: List[HonAppliance] = []
        self._api: Optional[HonAPI] = None
        self._test_data_path: Path = test_data_path or Path().cwd()

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
    def api(self) -> HonAPI:
        if self._api is None:
            raise exceptions.NoAuthenticationException
        return self._api

    @property
    def email(self) -> str:
        if not self._email:
            raise ValueError("Missing email")
        return self._email

    @property
    def password(self) -> str:
        if not self._password:
            raise ValueError("Missing password")
        return self._password

    async def create(self) -> Self:
        self._api = await HonAPI(
            self.email, self.password, session=self._session
        ).create()
        await self.setup()
        return self

    @property
    def appliances(self) -> List[HonAppliance]:
        return self._appliances

    @appliances.setter
    def appliances(self, appliances: List[HonAppliance]) -> None:
        self._appliances = appliances

    async def _create_appliance(
        self, appliance_data: Dict[str, Any], api: HonAPI, zone: int = 0
    ) -> None:
        appliance = HonAppliance(api, appliance_data, zone=zone)
        if appliance.mac_address == "":
            return
        try:
            await asyncio.gather(
                *[
                    appliance.load_attributes(),
                    appliance.load_commands(),
                    appliance.load_statistics(),
                ]
            )
        except (KeyError, ValueError, IndexError) as error:
            _LOGGER.exception(error)
            _LOGGER.error("Device data - %s", appliance_data)
        self._appliances.append(appliance)

    async def setup(self) -> None:
        appliances = await self.api.load_appliances()
        for appliance in appliances:
            if (zones := int(appliance.get("zone", "0"))) > 1:
                for zone in range(zones):
                    await self._create_appliance(
                        appliance.copy(), self.api, zone=zone + 1
                    )
            await self._create_appliance(appliance, self.api)
        if (
            test_data := self._test_data_path / "hon-test-data" / "test_data"
        ).exists() or (test_data := test_data / "test_data").exists():
            api = TestAPI(test_data)
            for appliance in await api.load_appliances():
                await self._create_appliance(appliance, api)

    async def close(self) -> None:
        await self.api.close()
