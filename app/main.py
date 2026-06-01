import asyncio, json
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .data_source import simulated_snapshot
app=FastAPI(title="Industrial AI Dashboard Starter")
app.mount("/static",StaticFiles(directory="static"),name="static")
@app.get("/")
def index(): return FileResponse("static/index.html")
@app.get("/api/snapshot")
def snapshot(): return simulated_snapshot()
@app.get("/api/ai-summary")
def summary():
    d=simulated_snapshot()
    return {"summary":f"{len(d['agvs'])} AGVs online, {len(d['alerts'])} alerts."}
@app.websocket("/ws")
async def ws(websocket:WebSocket):
    await websocket.accept()
    while True:
        await websocket.send_text(json.dumps(simulated_snapshot()))
        await asyncio.sleep(1)
