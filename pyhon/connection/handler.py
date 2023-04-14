import json
from collections.abc import Generator, AsyncIterator, Coroutine
from contextlib import asynccontextmanager
from typing import Optional, Callable, Dict
from typing_extensions import Self

import aiohttp

from pyhon import const, exceptions
from pyhon.connection.auth import HonAuth, _LOGGER
from pyhon.connection.device import HonDevice
from pyhon.exceptions import HonAuthenticationError


class HonBaseConnectionHandler:
    _HEADERS: Dict = {
        "user-agent": const.USER_AGENT,
        "Content-Type": "application/json",
    }

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._create_session: bool = session is None
        self._session: Optional[aiohttp.ClientSession] = session
        self._auth: Optional[HonAuth] = None

    async def __aenter__(self) -> Self:
        return await self.create()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def auth(self) -> Optional[HonAuth]:
        return self._auth

    async def create(self) -> Self:
        if self._create_session:
            self._session = aiohttp.ClientSession()
        return self

    @asynccontextmanager
    def _intercept(self, method: Callable, *args, loop: int = 0, **kwargs):
        raise NotImplementedError

    @asynccontextmanager
    async def get(self, *args, **kwargs) -> AsyncIterator[Callable]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: Callable
        async with self._intercept(self._session.get, *args, **kwargs) as response:
            yield response

    @asynccontextmanager
    async def post(self, *args, **kwargs) -> AsyncIterator[Callable]:
        if self._session is None:
            raise exceptions.NoSessionException()
        response: Callable
        async with self._intercept(self._session.post, *args, **kwargs) as response:
            yield response

    async def close(self) -> None:
        if self._create_session and self._session is not None:
            await self._session.close()


class HonConnectionHandler(HonBaseConnectionHandler):
    def __init__(
        self, email: str, password: str, session: Optional[aiohttp.ClientSession] = None
    ) -> None:
        super().__init__(session=session)
        self._device: HonDevice = HonDevice()
        self._email: str = email
        self._password: str = password
        if not self._email:
            raise HonAuthenticationError("An email address must be specified")
        if not self._password:
            raise HonAuthenticationError("A password address must be specified")

    @property
    def device(self) -> HonDevice:
        return self._device

    async def create(self) -> Self:
        await super().create()
        self._auth: HonAuth = HonAuth(
            self._session, self._email, self._password, self._device
        )
        return self

    async def _check_headers(self, headers: Dict) -> Dict:
        if not (self._auth.cognito_token and self._auth.id_token):
            await self._auth.authenticate()
        headers["cognito-token"] = self._auth.cognito_token
        headers["id-token"] = self._auth.id_token
        return self._HEADERS | headers

    @asynccontextmanager
    async def _intercept(
        self, method: Callable, *args, loop: int = 0, **kwargs
    ) -> AsyncIterator:
        kwargs["headers"] = await self._check_headers(kwargs.get("headers", {}))
        async with method(*args, **kwargs) as response:
            if (
                self._auth.token_expires_soon or response.status in [401, 403]
            ) and loop == 0:
                _LOGGER.info("Try refreshing token...")
                await self._auth.refresh()
                async with self._intercept(
                    method, *args, loop=loop + 1, **kwargs
                ) as result:
                    yield result
            elif (
                self._auth.token_is_expired or response.status in [401, 403]
            ) and loop == 1:
                _LOGGER.warning(
                    "%s - Error %s - %s",
                    response.request_info.url,
                    response.status,
                    await response.text(),
                )
                await self.create()
                async with self._intercept(
                    method, *args, loop=loop + 1, **kwargs
                ) as result:
                    yield result
            elif loop >= 2:
                _LOGGER.error(
                    "%s - Error %s - %s",
                    response.request_info.url,
                    response.status,
                    await response.text(),
                )
                raise HonAuthenticationError("Login failure")
            else:
                try:
                    await response.json()
                    yield response
                except json.JSONDecodeError:
                    _LOGGER.warning(
                        "%s - JsonDecodeError %s - %s",
                        response.request_info.url,
                        response.status,
                        await response.text(),
                    )
                    raise HonAuthenticationError("Decode Error")


class HonAnonymousConnectionHandler(HonBaseConnectionHandler):
    _HEADERS: Dict = HonBaseConnectionHandler._HEADERS | {"x-api-key": const.API_KEY}

    @asynccontextmanager
    async def _intercept(
        self, method: Callable, *args, loop: int = 0, **kwargs
    ) -> AsyncIterator:
        kwargs["headers"] = kwargs.pop("headers", {}) | self._HEADERS
        async with method(*args, **kwargs) as response:
            if response.status == 403:
                _LOGGER.error("Can't authenticate anymore")
            yield response
