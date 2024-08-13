import asyncio
from functools import cached_property, partial
import json
import logging
import pprint
import secrets
import ssl
from typing import Any, TYPE_CHECKING, cast
from urllib.parse import urlencode

from aiomqtt import Client as aiomqttClient, MqttError, ProtocolVersion, Topic
from pyhon import const

if TYPE_CHECKING:
    from aiomqtt import Message
    from pyhon import Hon, HonAPI
    from pyhon.appliance import HonAppliance

_LOGGER = logging.getLogger(__name__)


class _Payload(dict[Any, Any]):
    def __str__(self) -> str:
        return pprint.pformat(self)


class Client(aiomqttClient):
    def set_username(self, username: str) -> None:
        self._client.username_pw_set(username=username)


class MQTTClient:
    def __init__(self, hon: "Hon", mobile_id: str = const.MOBILE_ID) -> None:
        self._task: asyncio.Task[None] | None = None
        self._hon = hon
        self._mobile_id = mobile_id
        self._connected_event = asyncio.Event()

    @property
    def _appliances(self) -> list["HonAppliance"]:
        return self._hon.appliances

    @property
    def _api(self) -> "HonAPI":
        return self._hon.api

    async def create(self) -> "MQTTClient":
        self._task = asyncio.create_task(self.loop())
        await self._connected_event.wait()
        return self

    @cached_property
    def _subscription_handlers(self) -> dict[Topic, partial[None]]:

        handlers = {}

        for appliance in self._appliances:

            handler_protos = {
                "appliancestatus": partial(self._status_handler, appliance),
                "disconnected": partial(self._connection_handler, appliance, False),
                "connected": partial(self._connection_handler, appliance, True),
            }

            for topic in appliance.info.get("topics", {}).get("subscribe", []):
                topic_parts = topic.split("/")
                for topic_part, callback in handler_protos.items():
                    if topic_part in topic_parts:
                        handlers[Topic(topic)] = callback

        return handlers

    async def _get_mqtt_username(self) -> str:
        query_params = {
            "x-amz-customauthorizer-name": const.AWS_AUTHORIZER,
            "x-amz-customauthorizer-signature": await self._api.load_aws_token(),
            "token": self._api.auth.id_token,
        }
        return "?" + urlencode(query_params)

    @staticmethod
    def _status_handler(appliance: "HonAppliance", message: "Message") -> None:
        payload = _Payload(json.loads(cast(str | bytes | bytearray, message.payload)))
        for parameter in payload["parameters"]:
            appliance.attributes["parameters"][parameter["parName"]].update(parameter)
        appliance.sync_params_to_command("settings")

        _LOGGER.debug("On topic '%s' received: \n %s", message.topic, payload)

    @staticmethod
    def _connection_handler(
        appliance: "HonAppliance", connection_status: bool, __message: "Message"
    ) -> None:
        appliance.connection = connection_status

    async def loop(self) -> None:
        delay_min, delay_max = 5, 120

        tls_context = ssl.create_default_context()
        tls_context.set_alpn_protocols([const.ALPN_PROTOCOL])

        client = Client(
            hostname=const.AWS_ENDPOINT,
            port=const.AWS_PORT,
            identifier=f"{self._mobile_id}_{secrets.token_hex(8)}",
            protocol=ProtocolVersion.V5,
            logger=logging.getLogger(f"{__name__}.paho"),
            tls_context=tls_context,
        )

        reconnect_interval = delay_min

        while True:
            client.set_username(await self._get_mqtt_username())
            try:
                async with client:
                    self._connected_event.set()
                    reconnect_interval = delay_min

                    for topic in self._subscription_handlers:
                        await client.subscribe(str(topic))

                    async for message in client.messages:
                        handler = self._subscription_handlers[message.topic]

                        handler(message)

                        self._hon.notify()
            except MqttError:
                self._connected_event.clear()
                _LOGGER.warning(
                    "Connection to MQTT broker lost. Reconnecting in %s seconds",
                    reconnect_interval,
                )
                await asyncio.sleep(reconnect_interval)
                reconnect_interval = min(reconnect_interval * 2, delay_max)
