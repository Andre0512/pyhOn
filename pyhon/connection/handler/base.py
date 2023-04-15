import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional, Callable, Dict

import aiohttp
from typing_extensions import Self

from pyhon import const, exceptions

_LOGGER = logging.getLogger(__name__)


class ConnectionHandler:
    _HEADERS: Dict = {
        "user-agent": const.USER_AGENT,
        "Content-Type": "application/json",
    }

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._create_session: bool = session is None
        self._session: Optional[aiohttp.ClientSession] = session

    async def __aenter__(self) -> Self:
        return await self.create()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def create(self) -> Self:
        if self._create_session:
            self._session = aiohttp.ClientSession()
        return self

    @asynccontextmanager
    def _intercept(self, method: Callable, *args, loop: int = 0, **kwargs):
        raise NotImplementedError

    @asynccontextmanager
    async def get(self, *args, **kwargs) -> AsyncIterator[aiohttp.ClientResponse]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: aiohttp.ClientResponse
        async with self._intercept(self._session.get, *args, **kwargs) as response:
            yield response

    @asynccontextmanager
    async def post(self, *args, **kwargs) -> AsyncIterator[aiohttp.ClientResponse]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: aiohttp.ClientResponse
        async with self._intercept(self._session.post, *args, **kwargs) as response:
            yield response

    async def close(self) -> None:
        if self._create_session and self._session is not None:
            await self._session.close()
