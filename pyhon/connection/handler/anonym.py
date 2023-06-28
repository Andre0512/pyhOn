import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Dict, Any

import aiohttp

from pyhon import const
from pyhon.connection.handler.base import ConnectionHandler
from pyhon.typedefs import Callback

_LOGGER = logging.getLogger(__name__)


class HonAnonymousConnectionHandler(ConnectionHandler):
    _HEADERS: Dict[str, str] = ConnectionHandler._HEADERS | {"x-api-key": const.API_KEY}

    @asynccontextmanager
    async def _intercept(
        self, method: Callback, *args: Any, **kwargs: Any
    ) -> AsyncIterator[aiohttp.ClientResponse]:
        kwargs["headers"] = kwargs.pop("headers", {}) | self._HEADERS
        async with method(*args, **kwargs) as response:
            if response.status == 403:
                _LOGGER.error("Can't authenticate anymore")
            yield response
