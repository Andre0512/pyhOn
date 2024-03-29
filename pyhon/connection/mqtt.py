import asyncio
import json
import logging
import secrets
from typing import TYPE_CHECKING

from awscrt import mqtt5
from awsiot import mqtt5_client_builder  # type: ignore[import-untyped]

from pyhon import const
from pyhon.appliance import HonAppliance

if TYPE_CHECKING:
    from pyhon import Hon

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, hon: "Hon"):
        self._client: mqtt5.Client | None = None
        self._hon = hon
        self._api = hon.api
        self._appliances = hon.appliances
        self._connection = False
        self._watchdog_task: asyncio.Task[None] | None = None

    @property
    def client(self) -> mqtt5.Client:
        if self._client is not None:
            return self._client
        raise AttributeError("Client is not set")

    async def create(self) -> "MQTTClient":
        await self._start()
        self._subscribe_appliances()
        return self

    def _on_lifecycle_stopped(
        self, lifecycle_stopped_data: mqtt5.LifecycleStoppedData
    ) -> None:
        _LOGGER.info("Lifecycle Stopped: %s", str(lifecycle_stopped_data))

    def _on_lifecycle_connection_success(
        self,
        lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData,
    ) -> None:
        self._connection = True
        _LOGGER.info(
            "Lifecycle Connection Success: %s", str(lifecycle_connect_success_data)
        )

    def _on_lifecycle_attempting_connect(
        self,
        lifecycle_attempting_connect_data: mqtt5.LifecycleAttemptingConnectData,
    ) -> None:
        _LOGGER.info(
            "Lifecycle Attempting Connect - %s", str(lifecycle_attempting_connect_data)
        )

    def _on_lifecycle_connection_failure(
        self,
        lifecycle_connection_failure_data: mqtt5.LifecycleConnectFailureData,
    ) -> None:
        _LOGGER.info(
            "Lifecycle Connection Failure - %s", str(lifecycle_connection_failure_data)
        )

    def _on_lifecycle_disconnection(
        self,
        lifecycle_disconnect_data: mqtt5.LifecycleDisconnectData,
    ) -> None:
        self._connection = False
        _LOGGER.info("Lifecycle Disconnection - %s", str(lifecycle_disconnect_data))

    def _on_publish_received(self, data: mqtt5.PublishReceivedData) -> None:
        if not (data and data.publish_packet and data.publish_packet.payload):
            return
        payload = json.loads(data.publish_packet.payload.decode())
        topic = data.publish_packet.topic
        appliance = next(
            a for a in self._appliances if topic in a.info["topics"]["subscribe"]
        )
        if topic and "appliancestatus" in topic:
            for parameter in payload["parameters"]:
                appliance.attributes["parameters"][parameter["parName"]].update(
                    parameter
                )
            appliance.sync_params_to_command("settings")
            self._hon.notify()
        elif topic and "connected" in topic:
            _LOGGER.info("Connected %s", appliance.nick_name)
        elif topic and "disconnected" in topic:
            _LOGGER.info("Disconnected %s", appliance.nick_name)
        elif topic and "discovery" in topic:
            _LOGGER.info("Discovered %s", appliance.nick_name)
        _LOGGER.info("%s - %s", topic, payload)

    async def _start(self) -> None:
        self._client = mqtt5_client_builder.websockets_with_custom_authorizer(
            endpoint=const.AWS_ENDPOINT,
            auth_authorizer_name=const.AWS_AUTHORIZER,
            auth_authorizer_signature=await self._api.load_aws_token(),
            auth_token_key_name="token",
            auth_token_value=self._api.auth.id_token,
            client_id=f"{const.MOBILE_ID}_{secrets.token_hex(8)}",
            on_lifecycle_stopped=self._on_lifecycle_stopped,
            on_lifecycle_connection_success=self._on_lifecycle_connection_success,
            on_lifecycle_attempting_connect=self._on_lifecycle_attempting_connect,
            on_lifecycle_connection_failure=self._on_lifecycle_connection_failure,
            on_lifecycle_disconnection=self._on_lifecycle_disconnection,
            on_publish_received=self._on_publish_received,
        )
        self.client.start()

    def _subscribe_appliances(self) -> None:
        for appliance in self._appliances:
            self._subscribe(appliance)

    def _subscribe(self, appliance: HonAppliance) -> None:
        for topic in appliance.info.get("topics", {}).get("subscribe", []):
            self.client.subscribe(
                mqtt5.SubscribePacket([mqtt5.Subscription(topic)])
            ).result(10)
            _LOGGER.info("Subscribed to topic %s", topic)

    async def start_watchdog(self) -> None:
        if not self._watchdog_task or self._watchdog_task.done():
            await asyncio.create_task(self._watchdog())

    async def _watchdog(self) -> None:
        while True:
            await asyncio.sleep(5)
            if not self._connection:
                _LOGGER.info("Restart mqtt connection")
                await self._start()
                self._subscribe_appliances()
