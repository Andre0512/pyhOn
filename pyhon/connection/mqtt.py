import functools
import json
import logging
import secrets
import ssl
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from paho.mqtt.client import Client, MQTTv5

from pyhon import const

if TYPE_CHECKING:
    from paho.mqtt.client import MQTTMessage, _UserData, ReasonCodes, Properties

    from pyhon import Hon, HonAPI
    from pyhon.appliance import HonAppliance

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, hon: "Hon", mobile_id: str) -> None:
        self._client: Client | None = None
        self._hon = hon
        self._mobile_id = mobile_id or const.MOBILE_ID

    @property
    def _appliances(self) -> list["HonAppliance"]:
        return self._hon.appliances

    @property
    def _api(self) -> "HonAPI":
        return self._hon.api

    @property
    def client(self) -> Client:
        if self._client is not None:
            return self._client
        raise AttributeError("Client is not set")

    async def create(self) -> "MQTTClient":
        await self._start()
        return self

    async def _start(self) -> None:
        self._client = Client(
            client_id=f"{self._mobile_id}_{secrets.token_hex(8)}",
            protocol=MQTTv5,
            reconnect_on_failure=True,
        )

        ssl_context = ssl.create_default_context()
        ssl_context.set_alpn_protocols([const.ALPN_PROTOCOL])

        self.client.tls_set_context(ssl_context)
        self.client.enable_logger(_LOGGER)
        self.client.on_connect = self._subscribe_appliances

        query_params = urlencode(
            {
                "x-amz-customauthorizer-name": const.AWS_AUTHORIZER,
                "x-amz-customauthorizer-signature": await self._api.load_aws_token(),
                "token": self._api.auth.id_token,
            }
        )

        self.client.username_pw_set("?" + query_params)

        self.client.connect_async(const.AWS_ENDPOINT, 443)
        self.client.loop_start()

    def _subscribe_appliances(
        self,
        client: Client,
        userdata: "_UserData",
        flags: dict[str, int],
        rc: "ReasonCodes",
        properties: "Properties|None",
    ) -> None:
        del client, userdata, flags, rc, properties
        for appliance in self._appliances:
            self._subscribe(appliance)

    def _appliance_status_callback(
        self,
        appliance: "HonAppliance",
        client: Client,
        userdata: "_UserData",
        message: "MQTTMessage",
    ) -> None:
        del client, userdata
        payload = json.loads(message.payload)
        for parameter in payload["parameters"]:
            appliance.attributes["parameters"][parameter["parName"]].update(parameter)
        appliance.sync_params_to_command("settings")

        self._hon.notify()

    def _appliance_disconnected_callback(
        self,
        appliance: "HonAppliance",
        client: Client,
        userdata: "_UserData",
        message: "MQTTMessage",
    ) -> None:
        del client, userdata, message
        appliance.connection = False

        self._hon.notify()

    def _appliance_connected_callback(
        self,
        appliance: "HonAppliance",
        client: Client,
        userdata: "_UserData",
        message: "MQTTMessage",
    ) -> None:
        del client, userdata, message
        appliance.connection = True

        self._hon.notify()

    def _subscribe(self, appliance: "HonAppliance") -> None:
        topic_part_to_callback_mapping = {
            "appliancestatus": self._appliance_status_callback,
            "disconnected": self._appliance_disconnected_callback,
            "connected": self._appliance_connected_callback,
        }
        for topic in appliance.info.get("topics", {}).get("subscribe", []):
            for topic_part, callback in topic_part_to_callback_mapping.items():
                if topic_part in topic:
                    self.client.message_callback_add(
                        topic, functools.partial(callback, appliance)
                    )
                    self.client.subscribe(topic)
                    _LOGGER.info("Subscribed to topic %s", topic)
