#!/usr/bin/env python3
"""MQTT ingest smoke (needs the `mqtt` extra). Starts an in-process amqtt broker,
runs the app's subscriber, publishes a known snapshot, and asserts the dashboard
serves it — proving the data source is swappable while the endpoint is unchanged.
No external broker, no API key. Exits non-zero on failure."""
import asyncio, json, os, socket, sys


async def main():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    os.environ["SOURCE_BACKEND"] = "mqtt"
    os.environ["MQTT_URL"] = f"mqtt://127.0.0.1:{port}"
    os.environ["MQTT_TOPIC"] = "dashboard/snapshot"

    from amqtt.broker import Broker
    from amqtt.client import MQTTClient
    from app.ingest_mqtt import start_subscriber, latest
    from app.main import current_snapshot

    broker = Broker({"listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{port}"}}})
    await broker.start()
    sub = asyncio.create_task(start_subscriber())
    await asyncio.sleep(0.4)
    pub = MQTTClient(); await pub.connect(os.environ["MQTT_URL"])
    known = {"timestamp": 1, "agvs": [{"id": "AGV-9", "battery": 77}], "machines": [], "alerts": []}
    await pub.publish("dashboard/snapshot", json.dumps(known).encode(), qos=0)

    got = None
    for _ in range(50):
        if latest() is not None:
            got = latest(); break
        await asyncio.sleep(0.1)

    failures = []
    if got != known:
        failures.append(f"cache != published (got {got!r})")
    if current_snapshot().get("agvs") != known["agvs"]:
        failures.append(f"current_snapshot() not served from MQTT (got {current_snapshot()!r})")

    sub.cancel()
    try:
        await pub.disconnect()
    except Exception:
        pass
    await broker.shutdown()

    if failures:
        print("FAIL:", "; ".join(failures), file=sys.stderr)
        sys.exit(1)
    print("OK: MQTT ingest smoke passed (published snapshot served by dashboard)")


asyncio.run(main())
