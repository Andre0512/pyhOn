import json
from contextlib import asynccontextmanager

import aiohttp

from pyhon import const
from pyhon.connection.auth import HonAuth, _LOGGER
from pyhon.connection.device import HonDevice
from pyhon.exceptions import HonAuthenticationError


class HonBaseConnectionHandler:
    _HEADERS = {"user-agent": const.USER_AGENT, "Content-Type": "application/json"}

    def __init__(self, session=None):
        self._session = session
        self._auth = None

    async def __aenter__(self):
        return await self.create()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def create(self):
        self._session = aiohttp.ClientSession(headers=self._HEADERS)
        return self

    @asynccontextmanager
    async def _intercept(self, method, *args, loop=0, **kwargs):
        raise NotImplementedError

    @asynccontextmanager
    async def get(self, *args, **kwargs):
        async with self._intercept(self._session.get, *args, **kwargs) as response:
            yield response

    @asynccontextmanager
    async def post(self, *args, **kwargs):
        async with self._intercept(self._session.post, *args, **kwargs) as response:
            yield response

    async def close(self):
        await self._session.close()


class HonConnectionHandler(HonBaseConnectionHandler):
    def __init__(self, email, password, session=None):
        super().__init__(session=session)
        self._device = HonDevice()
        self._email = email
        self._password = password
        if not self._email:
            raise HonAuthenticationError("An email address must be specified")
        if not self._password:
            raise HonAuthenticationError("A password address must be specified")
        self._request_headers = {}

    @property
    def device(self):
        return self._device

    async def create(self):
        await super().create()
        self._auth = HonAuth(self._session, self._email, self._password, self._device)
        return self

    async def _check_headers(self, headers):
        if (
            "cognito-token" not in self._request_headers
            or "id-token" not in self._request_headers
        ):
            if await self._auth.authorize():
                self._request_headers["cognito-token"] = self._auth.cognito_token
                self._request_headers["id-token"] = self._auth.id_token
            else:
                raise HonAuthenticationError("Can't login")
        return {h: v for h, v in self._request_headers.items() if h not in headers}

    @asynccontextmanager
    async def _intercept(self, method, *args, loop=0, **kwargs):
        kwargs["headers"] = await self._check_headers(kwargs.get("headers", {}))
        async with method(*args, **kwargs) as response:
            if response.status == 403 and not loop:
                _LOGGER.info("Try refreshing token...")
                await self._auth.refresh()
                yield await self._intercept(method, *args, loop=loop + 1, **kwargs)
            elif response.status == 403 and loop < 2:
                _LOGGER.warning(
                    "%s - Error %s - %s",
                    response.request_info.url,
                    response.status,
                    await response.text(),
                )
                await self.create()
                yield await self._intercept(method, *args, loop=loop + 1, **kwargs)
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
                    yield {}


class HonAnonymousConnectionHandler(HonBaseConnectionHandler):
    _HEADERS = HonBaseConnectionHandler._HEADERS | {"x-api-key": const.API_KEY}

    @asynccontextmanager
    async def _intercept(self, method, *args, loop=0, **kwargs):
        kwargs["headers"] = kwargs.pop("headers", {}) | self._HEADERS
        async with method(*args, **kwargs) as response:
            if response.status == 403:
                _LOGGER.error("Can't authenticate anymore")
            yield response
