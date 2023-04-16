import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional, Callable, List, Tuple

import aiohttp

from pyhon import const
from pyhon.connection.handler.base import ConnectionHandler

_LOGGER = logging.getLogger(__name__)


class HonAuthConnectionHandler(ConnectionHandler):
    _HEADERS = {"user-agent": const.USER_AGENT}

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        super().__init__(session)
        self._called_urls: List[Tuple[int, str]] = []

    @property
    def called_urls(self) -> List[Tuple[int, str]]:
        return self._called_urls

    @called_urls.setter
    def called_urls(self, called_urls: List[Tuple[int, str]]) -> None:
        self._called_urls = called_urls

    @asynccontextmanager
    async def _intercept(
        self, method: Callable, *args, loop: int = 0, **kwargs
    ) -> AsyncIterator:
        kwargs["headers"] = kwargs.pop("headers", {}) | self._HEADERS
        async with method(*args, **kwargs) as response:
            self._called_urls.append((response.status, response.request_info.url))
            yield response
