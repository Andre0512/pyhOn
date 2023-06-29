import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

import aiohttp
from typing_extensions import Self
from yarl import URL

from pyhon.connection.auth import HonAuth
from pyhon.connection.device import HonDevice
from pyhon.connection.handler.base import ConnectionHandler
from pyhon.exceptions import HonAuthenticationError, NoAuthenticationException
from pyhon.typedefs import Callback

_LOGGER = logging.getLogger(__name__)


class HonConnectionHandler(ConnectionHandler):
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
        self._auth: Optional[HonAuth] = None

    @property
    def auth(self) -> HonAuth:
        if self._auth is None:
            raise NoAuthenticationException()
        return self._auth

    @property
    def device(self) -> HonDevice:
        return self._device

    async def create(self) -> Self:
        await super().create()
        self._auth = HonAuth(self.session, self._email, self._password, self._device)
        return self

    async def _check_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        if not (self.auth.cognito_token and self.auth.id_token):
            await self.auth.authenticate()
        headers["cognito-token"] = self.auth.cognito_token
        headers["id-token"] = self.auth.id_token
        return self._HEADERS | headers

    @asynccontextmanager
    async def _intercept(
        self, method: Callback, url: str | URL, *args: Any, **kwargs: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        loop: int = kwargs.pop("loop", 0)
        kwargs["headers"] = await self._check_headers(kwargs.get("headers", {}))
        async with method(url, *args, **kwargs) as response:
            if (
                self.auth.token_expires_soon or response.status in [401, 403]
            ) and loop == 0:
                _LOGGER.info("Try refreshing token...")
                await self.auth.refresh()
                async with self._intercept(
                    method, url, *args, loop=loop + 1, **kwargs
                ) as result:
                    yield result
            elif (
                self.auth.token_is_expired or response.status in [401, 403]
            ) and loop == 1:
                _LOGGER.warning(
                    "%s - Error %s - %s",
                    response.request_info.url,
                    response.status,
                    await response.text(),
                )
                await self.create()
                async with self._intercept(
                    method, url, *args, loop=loop + 1, **kwargs
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
