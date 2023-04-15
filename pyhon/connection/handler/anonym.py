import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Callable, Dict

from pyhon import const
from pyhon.connection.handler.base import ConnectionHandler

_LOGGER = logging.getLogger(__name__)


class HonAnonymousConnectionHandler(ConnectionHandler):
    _HEADERS: Dict = ConnectionHandler._HEADERS | {"x-api-key": const.API_KEY}

    @asynccontextmanager
    async def _intercept(self, method: Callable, *args, **kwargs) -> AsyncIterator:
        kwargs["headers"] = kwargs.pop("headers", {}) | self._HEADERS
        async with method(*args, **kwargs) as response:
            if response.status == 403:
                _LOGGER.error("Can't authenticate anymore")
            yield response
