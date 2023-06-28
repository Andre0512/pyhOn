import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Optional, Dict, Type, Any, Protocol

import aiohttp
from typing_extensions import Self
from yarl import URL

from pyhon import const, exceptions
from pyhon.typedefs import Callback

_LOGGER = logging.getLogger(__name__)


class ConnectionHandler:
    _HEADERS: Dict[str, str] = {
        "user-agent": const.USER_AGENT,
        "Content-Type": "application/json",
    }

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._create_session: bool = session is None
        self._session: Optional[aiohttp.ClientSession] = session

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
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise exceptions.NoSessionException
        return self._session

    async def create(self) -> Self:
        if self._create_session:
            self._session = aiohttp.ClientSession()
        return self

    @asynccontextmanager
    def _intercept(
        self, method: Callback, url: str | URL, *args: Any, **kwargs: Dict[str, Any]
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        raise NotImplementedError

    @asynccontextmanager
    async def get(
        self, *args: Any, **kwargs: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: aiohttp.ClientResponse
        async with self._intercept(self._session.get, *args, **kwargs) as response:  # type: ignore[arg-type]
            yield response

    @asynccontextmanager
    async def post(
        self, *args: Any, **kwargs: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: aiohttp.ClientResponse
        async with self._intercept(self._session.post, *args, **kwargs) as response:  # type: ignore[arg-type]
            yield response

    async def close(self) -> None:
        if self._create_session and self._session is not None:
            await self._session.close()
