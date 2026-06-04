"""MQTT ingest — Part 2 axis A. A background subscriber keeps the latest snapshot
in an in-memory cache; main.py serves from it when SOURCE_BACKEND=mqtt. Requires
the `mqtt` extra (amqtt)."""
import json
from amqtt.client import MQTTClient
from . import config

_cache = {}


def latest():
    """Return the most recent snapshot received over MQTT, or None."""
    return _cache.get("snapshot")


async def start_subscriber():
    """Connect to MQTT_URL, subscribe to MQTT_TOPIC, and update the cache with
    each received JSON snapshot. Runs forever — use as a background task."""
    client = MQTTClient()
    await client.connect(config.mqtt_url())
    await client.subscribe([(config.mqtt_topic(), 0)])
    while True:
        message = await client.deliver_message()
        try:
            _cache["snapshot"] = json.loads(message.publish_packet.payload.data.decode())
        except (json.JSONDecodeError, AttributeError):
            continue
