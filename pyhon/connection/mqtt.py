import json
import logging
import secrets
from typing import TYPE_CHECKING

from awscrt import mqtt5
from awsiot import mqtt5_client_builder  # type: ignore[import-untyped]

from pyhon import const
from pyhon.appliance import HonAppliance

if TYPE_CHECKING:
    from pyhon import HonAPI

_LOGGER = logging.getLogger(__name__)

appliances: list[HonAppliance] = []


def on_lifecycle_stopped(lifecycle_stopped_data: mqtt5.LifecycleStoppedData) -> None:
    _LOGGER.info("Lifecycle Stopped: %s", str(lifecycle_stopped_data))


def on_lifecycle_connection_success(
    lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData,
) -> None:
    _LOGGER.info(
        "Lifecycle Connection Success: %s", str(lifecycle_connect_success_data)
    )

def on_lifecycle_attempting_connect(lifecycle_attempting_connect_data):
    _LOGGER.info("Lifecycle Attempting Connect - %s", lifecycle_attempting_connect_data)


def on_lifecycle_connection_failure(lifecycle_connection_failure_data):
    _LOGGER.info("Lifecycle Connection Failure - %s", lifecycle_connection_failure_data)


def on_lifecycle_disconnection(lifecycle_disconnect_data):
    _LOGGER.info("Lifecycle Disconnection - %s", lifecycle_disconnect_data)


def on_publish_received(data: mqtt5.PublishReceivedData) -> None:
    if not (data and data.publish_packet and data.publish_packet.payload):
        return
    payload = json.loads(data.publish_packet.payload.decode())
    topic = data.publish_packet.topic
    if topic and "appliancestatus" in topic:
        appliance = next(
            a for a in appliances if topic in a.info["topics"]["subscribe"]
        )
        for parameter in payload["parameters"]:
            appliance.attributes["parameters"][parameter["parName"]].update(parameter)
        appliance.notify()
    _LOGGER.info("%s - %s", topic, payload)


async def create_mqtt_client(api: "HonAPI") -> mqtt5.Client:
    client: mqtt5.Client = mqtt5_client_builder.websockets_with_custom_authorizer(
        endpoint=const.AWS_ENDPOINT,
        auth_authorizer_name=const.AWS_AUTHORIZER,
        auth_authorizer_signature=await api.load_aws_token(),
        auth_token_key_name="token",
        auth_token_value=api.auth.id_token,
        client_id=f"{const.MOBILE_ID}_{secrets.token_hex(8)}",
        on_lifecycle_stopped=on_lifecycle_stopped,
        on_lifecycle_connection_success=on_lifecycle_connection_success,
        on_lifecycle_attempting_connect=on_lifecycle_attempting_connect,
        on_lifecycle_connection_failure=on_lifecycle_connection_failure,
        on_lifecycle_disconnection=on_lifecycle_disconnection,
        on_publish_received=on_publish_received,
    )
    client.start()
    return client


def subscribe(client: mqtt5.Client, appliance: HonAppliance) -> None:
    for topic in appliance.info.get("topics", {}).get("subscribe", []):
        client.subscribe(mqtt5.SubscribePacket([mqtt5.Subscription(topic)])).result(10)
        _LOGGER.info("Subscribed to topic %s", topic)


async def start(api: "HonAPI", app: list[HonAppliance]) -> mqtt5.Client:
    client = await create_mqtt_client(api)
    global appliances  # pylint: disable=global-statement
    appliances = app
    for appliance in appliances:
        subscribe(client, appliance)
    return client
