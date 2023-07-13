from typing import Union, Any, TYPE_CHECKING, Protocol

import aiohttp
from yarl import URL

if TYPE_CHECKING:
    from pyhon.parameter.base import HonParameter
    from pyhon.parameter.enum import HonParameterEnum
    from pyhon.parameter.fixed import HonParameterFixed
    from pyhon.parameter.program import HonParameterProgram
    from pyhon.parameter.range import HonParameterRange


class Callback(Protocol):
    def __call__(
        self, url: str | URL, *args: Any, **kwargs: Any
    ) -> aiohttp.client._RequestContextManager:
        ...


Parameter = Union[
    "HonParameter",
    "HonParameterRange",
    "HonParameterEnum",
    "HonParameterFixed",
    "HonParameterProgram",
]
