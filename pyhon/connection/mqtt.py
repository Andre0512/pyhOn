import json
import logging
import secrets
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from paho.mqtt.client import Client, MQTTv5

from pyhon import const

if TYPE_CHECKING:
    from paho.mqtt.client import MQTTMessage, _UserData

    from pyhon import Hon
    from pyhon.appliance import HonAppliance

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, hon: "Hon", mobile_id: str) -> None:
        self._client: Client | None = None
        self._hon = hon
        self._mobile_id = mobile_id or const.MOBILE_ID
        self._api = hon.api
        self._appliances = hon.appliances

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        raise AttributeError("Client is not set")

    async def create(self) -> "MQTTClient":
        await self._start()
        self._subscribe_appliances()
        return self

    def _on_message(
        self,
        client: Client, # pylint: disable=unused-argument
        userdata: "_UserData", # pylint: disable=unused-argument
        message: "MQTTMessage",
    ) -> None:
        if not message.payload or not message.topic:
            return

        payload = json.loads(message.payload)
        topic = message.topic
        appliance = next(
            a for a in self._appliances if topic in a.info["topics"]["subscribe"]
        )

        topic_parts = topic.split("/")
        if "appliancestatus" in topic_parts:
            for parameter in payload["parameters"]:
                appliance.attributes["parameters"][parameter["parName"]].update(
                    parameter
                )
            appliance.sync_params_to_command("settings")
        elif "disconnected" in topic_parts:
            _LOGGER.info(
                "Disconnected %s: %s",
                appliance.nick_name,
                payload.get("disconnectReason"),
            )
            appliance.connection = False
        elif "connected" in topic_parts:
            appliance.connection = True
            _LOGGER.info("Connected %s", appliance.nick_name)
        elif "discovery" in topic_parts:
            _LOGGER.info("Discovered %s", appliance.nick_name)

        self._hon.notify()

    async def _start(self) -> None:
        self._client = Client(
            client_id=f"{self._mobile_id}_{secrets.token_hex(8)}",
            protocol=MQTTv5,
            reconnect_on_failure=True,
        )

        self._client.on_message = self._on_message
        self._client.enable_logger(_LOGGER)

        query_params = urlencode(
            {
                "x-amz-customauthorizer-name": const.AWS_AUTHORIZER,
                "x-amz-customauthorizer-signature": await self._api.load_aws_token(),
                "token": self._api.auth.id_token,
            }
        )

        self._client.username_pw_set(f"?{query_params}")

        self._client.connect_async(const.AWS_ENDPOINT, 443)
        self._client.loop_start()

    def _subscribe_appliances(self) -> None:
        for appliance in self._appliances:
            self._subscribe(appliance)

    def _subscribe(self, appliance: "HonAppliance") -> None:
        for topic in appliance.info.get("topics", {}).get("subscribe", []):
            if self._client:
                self._client.subscribe(topic)
                _LOGGER.info("Subscribed to topic %s", topic)
