import asyncio, json
from pathlib import Path
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .data_source import simulated_snapshot
from .summary import rule_summary
from . import config
BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Industrial AI Dashboard Starter")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def current_snapshot():
    """Snapshot from the active data source: live MQTT cache (SOURCE_BACKEND=mqtt)
    or the built-in simulator (default). The endpoint/UI is unchanged either way."""
    if config.source_backend() == "mqtt":
        from .ingest_mqtt import latest  # lazy: base install has no amqtt
        snap = latest()
        if snap is not None:
            return snap
        return {"timestamp": 0, "agvs": [], "machines": [], "alerts": [], "pending": True}
    return simulated_snapshot()


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/snapshot")
def snapshot():
    return current_snapshot()


@app.get("/api/ai-summary")
async def ai_summary():
    snap = current_snapshot()
    if config.ai_summary_mode() == "llm":
        from .summary import llm_summary  # lazy: needs the ai extra (httpx)
        return {"summary": await llm_summary(snap)}
    return {"summary": rule_summary(snap)}


@app.on_event("startup")
async def _startup():
    if config.source_backend() == "mqtt":
        from .ingest_mqtt import start_subscriber  # lazy
        asyncio.create_task(start_subscriber())


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_text(json.dumps(current_snapshot()))
        await asyncio.sleep(1)
