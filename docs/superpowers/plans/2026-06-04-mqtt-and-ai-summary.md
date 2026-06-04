# Real-MQTT-Data + LLM-Summary Second-Half Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second course track that takes the toy dashboard to a real one along two independent axes — data (sim → MQTT) and AI summary (stub → rule-based → LLM) — as a contrast/upgrade lesson.

**Architecture:** Keep `app/data_source.py:simulated_snapshot` (baseline data) and the FastAPI/REST/WebSocket substrate unchanged. Add `app/ingest_mqtt.py` (background MQTT subscriber → in-memory cache) selected by `SOURCE_BACKEND=sim|mqtt`, and `app/summary.py` (`rule_summary` deterministic baseline replacing the stub + `llm_summary` upgrade) selected by `AI_SUMMARY=rule|llm`. Each axis is an optional extra (`mqtt` / `ai`) and is lazy-imported so the base install stays at fastapi+uvicorn. Deterministic tests: MQTT via an in-process amqtt broker; LLM via a local fake OpenAI server.

**Tech Stack:** Python 3.10+, uv, FastAPI 0.115.6 (existing), amqtt 0.11.x (`mqtt` extra), httpx 0.28.x (`ai` extra), GitHub Actions. No pytest — plain-python smoke scripts.

---

## Preconditions / verified facts

Scratch-verified:
- **amqtt 0.11.3** (16 pkgs, pure Python): in-process `Broker` + `MQTTClient` publish/subscribe round-trip works. A background subscriber that updates a module cache + a poll loop on `latest()` is deterministic. (Cleanup logs "Disconnected from broker" on task cancel — harmless.)
- A background subscriber driven as an asyncio task (NOT via FastAPI startup/TestClient) + publish + poll `latest()` is the robust test shape. `current_snapshot()` reads the same module cache, so asserting it directly works.
- LLM summary: `httpx` POST to a local fake OpenAI server returning `{"choices":[{"message":{"content": ...}}]}` works; `rule_summary` is pure-Python deterministic. (Pattern proven in linebot.)
- **This repo's base deps are ONLY fastapi+uvicorn — NO httpx.** Therefore: base smoke must NOT use Starlette `TestClient` (it imports httpx). Base smoke tests functions directly; only the `ai` track (which installs httpx) uses TestClient.
- Lazy imports: `app.main` imports `.summary` (rule_summary has no httpx; llm_summary imports httpx inside), `.data_source`, `.config` — none pull amqtt/httpx at import. `ingest_mqtt` (imports amqtt) is imported only in `SOURCE_BACKEND=mqtt` paths.

**Working dir:** `/home/ct/industrial-ai-dashboard-starter`. Branch `feat/mqtt-and-ai-summary-track` (not main).

---

## File structure

| File | Responsibility |
|---|---|
| `pyproject.toml` (modify) | `mqtt` + `ai` optional extras |
| `app/config.py` (create) | live env getters (source/ai mode, mqtt url/topic, llm endpoint) |
| `app/summary.py` (create) | `rule_summary` (deterministic) + `llm_summary` (lazy httpx) |
| `app/ingest_mqtt.py` (create) | background MQTT subscriber + `latest()` cache |
| `app/main.py` (modify) | `current_snapshot()` source switch; `/api/ai-summary` rule\|llm; startup subscriber |
| `base_smoke_test.py` (create) | base-deps: simulator shape + rule_summary (no TestClient) |
| `mqtt_smoke_test.py` (create) | mqtt extra: in-process broker round-trip → current_snapshot |
| `ai_smoke_test.py` (create) | ai extra: fake OpenAI → /api/ai-summary llm (TestClient) |
| `.github/workflows/ci.yml` (create) | matrix base / mqtt / ai |
| `docs/08-real-data-and-ai-summary.md` (create) | the lesson (two axes + learning recap) |
| `docs/00-overview.md`, `tutorial.html`, `README.md`, `index.html`, `DESIGN.md` (modify) | two-track framing |

---

## Task 1: Add the mqtt + ai optional extras

**Files:** Modify `pyproject.toml`; regenerate `uv.lock`.

- [ ] **Step 1: Edit `pyproject.toml`** — add after the existing `dependencies = [...]` array (keep `[tool.uv] package = false`; do NOT add amqtt/httpx to required deps):

```toml
[project.optional-dependencies]
mqtt = ["amqtt>=0.11,<0.12"]
ai = ["httpx>=0.28,<0.29"]
```

- [ ] **Step 2: Regenerate lock + confirm base excludes both.**

Run: `uv lock && uv sync && uv run python -c "import importlib.util as u; print('amqtt:', u.find_spec('amqtt') is not None, '| httpx:', u.find_spec('httpx') is not None)"`
Expected: `amqtt: False | httpx: False`.

- [ ] **Step 3: Confirm each extra installs.**

Run: `uv sync --extra mqtt && uv run python -c "import amqtt; print('amqtt', amqtt.__version__)"`
Expected: `amqtt 0.11.x`.
Run: `uv sync --extra ai && uv run python -c "import httpx; print('httpx', httpx.__version__)"`
Expected: `httpx 0.28.x`.

- [ ] **Step 4: Restore base env.**

Run: `uv sync`

- [ ] **Step 5: Commit.**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add optional mqtt + ai extras"
```

---

## Task 2: AI axis — config + summary (rule baseline + LLM upgrade)

**Files:** Create `app/config.py`, `app/summary.py`.

- [ ] **Step 1: Create `app/config.py`** (live getters so tests can set env without re-import):

```python
"""Centralised, live env getters (read at call time so tests can flip them)."""
import os


def source_backend() -> str:
    return os.getenv("SOURCE_BACKEND", "sim")


def ai_summary_mode() -> str:
    return os.getenv("AI_SUMMARY", "rule")


def mqtt_url() -> str:
    return os.getenv("MQTT_URL", "mqtt://127.0.0.1:1883")


def mqtt_topic() -> str:
    return os.getenv("MQTT_TOPIC", "dashboard/snapshot")


def llm_endpoint() -> str:
    return os.getenv("HTTP_LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")


def llm_api_key() -> str:
    return os.getenv("HTTP_LLM_API_KEY", "")


def model_name() -> str:
    return os.getenv("MODEL_NAME", "gpt-4o-mini")
```

- [ ] **Step 2: Create `app/summary.py`:**

```python
"""AI summary — Part 2 axis B. rule_summary is the deterministic baseline (it
replaces the old one-line stub); llm_summary is the LLM 班報 upgrade and needs
the `ai` extra. The /api/ai-summary endpoint picks via AI_SUMMARY (rule|llm)."""
import json


def rule_summary(snapshot) -> str:
    """Deterministic rule-based shift report from a dashboard snapshot."""
    agvs = snapshot.get("agvs", [])
    machines = snapshot.get("machines", [])
    alerts = snapshot.get("alerts", [])
    low = [a["id"] for a in agvs if a.get("battery", 100) < 20]
    abnormal = [m["id"] for m in machines if m.get("status") not in ("run", None)]
    parts = [
        f"AGV {len(agvs)} 台在線",
        f"低電量 {len(low)} 台" + (f"({'/'.join(low)})" if low else ""),
        f"異常機台 {len(abnormal)} 台" + (f"({'/'.join(abnormal)})" if abnormal else ""),
        f"告警 {len(alerts)} 則",
    ]
    return "；".join(parts) + "。"


async def llm_summary(snapshot) -> str:
    """LLM shift report via an OpenAI-compatible endpoint. Requires the `ai`
    extra (httpx, imported lazily so the base install stays httpx-free)."""
    import httpx
    from . import config
    payload = {
        "model": config.model_name(),
        "messages": [
            {"role": "system", "content": "你是工廠夜班主管，用繁體中文寫一句簡短班報。"},
            {"role": "user", "content": "現場快照:\n" + json.dumps(snapshot, ensure_ascii=False)},
        ],
    }
    headers = {"Authorization": "Bearer " + (config.llm_api_key() or "x")}
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(config.llm_endpoint(), json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

- [ ] **Step 3: Verify on base deps (rule_summary works, no httpx needed to import).**

Run: `uv sync && PYTHONPATH=. uv run python -c "
from app.summary import rule_summary
print(rule_summary({'agvs':[{'id':'AGV-2','battery':10}],'machines':[{'id':'PLC-2','status':'stop'}],'alerts':[{'level':'w'}]}))
"`
Expected: a line containing `AGV 1 台在線`, `低電量 1 台(AGV-2)`, `異常機台 1 台(PLC-2)`, `告警 1 則`.

- [ ] **Step 4: Commit.**

```bash
git add app/config.py app/summary.py
git commit -m "feat: config getters + rule/LLM summary (axis B)"
```

---

## Task 3: Data axis — MQTT ingest

**Files:** Create `app/ingest_mqtt.py`.

- [ ] **Step 1: Create `app/ingest_mqtt.py`:**

```python
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
```

- [ ] **Step 2: Verify it imports only with the mqtt extra (and not on base).**

Run: `uv sync && PYTHONPATH=. uv run python -c "import app.ingest_mqtt" 2>&1 | tail -1`
Expected: `ModuleNotFoundError: No module named 'amqtt'` (base has no amqtt — correct; it's only used in mqtt mode).
Run: `uv sync --extra mqtt && PYTHONPATH=. uv run python -c "import app.ingest_mqtt; print('ingest imports with mqtt extra: OK')"`
Expected: `ingest imports with mqtt extra: OK`.

- [ ] **Step 3: Commit.**

```bash
git add app/ingest_mqtt.py
git commit -m "feat: MQTT background subscriber + cache (axis A)"
```

---

## Task 4: Rewire main.py for both axes

**Files:** Modify `app/main.py`.

- [ ] **Step 1: Replace the entire `app/main.py` with:**

```python
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
```

- [ ] **Step 2: Verify base import + default (sim+rule) behavior, no extras.**

Run: `uv sync && PYTHONPATH=. uv run python -c "
import importlib.util as u
import app.main as m
print('base import OK | amqtt:', u.find_spec('amqtt') is not None, '| httpx:', u.find_spec('httpx') is not None)
s = m.current_snapshot(); print('sim snapshot agvs:', len(s['agvs']))
from app.summary import rule_summary; print('ai-summary(rule) sample:', rule_summary(s)[:20], '...')
"`
Expected: `base import OK | amqtt: False | httpx: False`, a non-zero agv count, and a rule-summary sample. (Proves base needs neither extra; default source=sim, summary=rule.)

- [ ] **Step 3: Commit.**

```bash
git add app/main.py
git commit -m "feat: current_snapshot source switch + ai-summary rule|llm + startup subscriber"
```

---

## Task 5: Base smoke test (base deps, no TestClient)

**Files:** Create `base_smoke_test.py`.

- [ ] **Step 1: Create `base_smoke_test.py`** (functions only — base has no httpx so no TestClient):

```python
#!/usr/bin/env python3
"""Base smoke (no extra): the built-in simulator produces the expected shape and
the rule-based summary is deterministic. No TestClient (base has no httpx).
Exits non-zero on failure."""
import sys
from app.data_source import simulated_snapshot
from app.summary import rule_summary

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

snap = simulated_snapshot()
check({"agvs", "machines", "alerts", "timestamp"} <= set(snap), f"snapshot shape (got {sorted(snap)})")
check(isinstance(snap["agvs"], list) and len(snap["agvs"]) >= 1, "snapshot has agvs")

fixed = {"agvs": [{"id": "AGV-1", "battery": 88}, {"id": "AGV-2", "battery": 10}],
         "machines": [{"id": "AOI-1", "status": "run"}, {"id": "PLC-2", "status": "stop"}],
         "alerts": [{"level": "warning"}]}
r = rule_summary(fixed)
for piece in ["AGV 2 台在線", "低電量 1 台", "AGV-2", "異常機台 1 台", "PLC-2", "告警 1 則"]:
    check(piece in r, f"rule_summary contains {piece!r} (got {r!r})")

if failures:
    print("FAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("OK: base smoke passed (simulator shape + deterministic rule summary)")
```

- [ ] **Step 2: Run on base deps — must pass.**

Run: `uv sync && PYTHONPATH=. uv run python base_smoke_test.py`
Expected: `OK: base smoke passed (simulator shape + deterministic rule summary)`, exit 0.

- [ ] **Step 3: Commit.**

```bash
git add base_smoke_test.py
git commit -m "test: base smoke (simulator shape + rule summary)"
```

---

## Task 6: MQTT ingest smoke (mqtt extra)

**Files:** Create `mqtt_smoke_test.py`.

- [ ] **Step 1: Create `mqtt_smoke_test.py`:**

```python
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
```

- [ ] **Step 2: Run with the mqtt extra — must pass.**

Run: `uv sync --extra mqtt && PYTHONPATH=. uv run python mqtt_smoke_test.py`
Expected: `OK: MQTT ingest smoke passed (published snapshot served by dashboard)`, exit 0. (amqtt may print harmless "Disconnected from broker" on cleanup.)

- [ ] **Step 3: Commit.**

```bash
git add mqtt_smoke_test.py
git commit -m "test: MQTT ingest smoke (in-process broker round-trip)"
```

---

## Task 7: AI summary smoke (ai extra, fake OpenAI)

**Files:** Create `ai_smoke_test.py`.

- [ ] **Step 1: Create `ai_smoke_test.py`:**

```python
#!/usr/bin/env python3
"""AI summary smoke (needs the `ai` extra). rule_summary is deterministic; the
LLM summary is wired through an OpenAI-compatible endpoint, verified against a
local fake OpenAI server (no API key). The ai extra brings httpx, so TestClient
is available here. Exits non-zero on failure."""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

CANNED = "今日 3 台 AGV 正常運作，1 則低電量告警已處理。"

class _Fake(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"choices": [{"message": {"content": CANNED}}]}).encode())
    def log_message(self, *a): pass

srv = HTTPServer(("127.0.0.1", 0), _Fake)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

# Set before importing app.main (config reads env live, but be explicit).
os.environ["AI_SUMMARY"] = "llm"
os.environ["HTTP_LLM_ENDPOINT"] = f"http://127.0.0.1:{port}/v1/chat/completions"

from starlette.testclient import TestClient
from app.main import app
from app.summary import rule_summary

failures = []
def check(cond, label):
    if not cond:
        failures.append(label)

check("AGV 1 台在線" in rule_summary({"agvs": [{"id": "AGV-1", "battery": 50}], "machines": [], "alerts": []}),
      "rule_summary deterministic")

try:
    out = TestClient(app).get("/api/ai-summary").json()["summary"]
    check(out == CANNED, f"/api/ai-summary llm -> fake server content (got {out!r})")
finally:
    srv.shutdown()

if failures:
    print("FAIL:", "; ".join(failures), file=sys.stderr)
    sys.exit(1)
print("OK: AI summary smoke passed (rule deterministic + llm wired)")
```

- [ ] **Step 2: Run with the ai extra — must pass.**

Run: `uv sync --extra ai && PYTHONPATH=. uv run python ai_smoke_test.py`
Expected: `OK: AI summary smoke passed (rule deterministic + llm wired)`, exit 0.

- [ ] **Step 3: Restore base + confirm base smoke still green.**

Run: `uv sync && PYTHONPATH=. uv run python base_smoke_test.py`
Expected: `OK: base smoke passed ...`.

- [ ] **Step 4: Commit.**

```bash
git add ai_smoke_test.py
git commit -m "test: AI summary smoke (fake OpenAI, no key)"
```

---

## Task 8: CI matrix (base / mqtt / ai)

**Files:** Create `.github/workflows/ci.yml`.

- [ ] **Step 1: Create `.github/workflows/ci.yml`:**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        track: [base, mqtt, ai]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Sync (base)
        if: matrix.track == 'base'
        run: uv sync
      - name: Base smoke
        if: matrix.track == 'base'
        run: PYTHONPATH=. uv run python base_smoke_test.py

      - name: Sync with mqtt extra
        if: matrix.track == 'mqtt'
        run: uv sync --extra mqtt
      - name: MQTT ingest smoke
        if: matrix.track == 'mqtt'
        run: PYTHONPATH=. uv run python mqtt_smoke_test.py

      - name: Sync with ai extra
        if: matrix.track == 'ai'
        run: uv sync --extra ai
      - name: AI summary smoke
        if: matrix.track == 'ai'
        run: PYTHONPATH=. uv run python ai_smoke_test.py
```

- [ ] **Step 2: Validate YAML + simulate all three tracks locally.**

Run: `uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml ok', d['jobs']['smoke-test']['strategy']['matrix']['track'])"`
Expected: `yaml ok ['base', 'mqtt', 'ai']`.
Run:
```bash
uv sync && PYTHONPATH=. uv run python base_smoke_test.py
uv sync --extra mqtt && PYTHONPATH=. uv run python mqtt_smoke_test.py
uv sync --extra ai && PYTHONPATH=. uv run python ai_smoke_test.py
uv sync
```
Expected: three `OK:` lines.

- [ ] **Step 3: Commit.**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: matrix runs base + mqtt + ai tracks"
```

---

## Task 9: Write the lesson `docs/08-real-data-and-ai-summary.md`

**Files:** Create `docs/08-real-data-and-ai-summary.md`.

- [ ] **Step 1: Create the file** with this content (Traditional Chinese; no emoji):

````markdown
# 工業 AI Dashboard 入門模板：接真實資料 + AI 班報(對照組)

前半段你做出了一個會動的 dashboard:`simulated_snapshot()` 產假的 AGV/機台資料,WebSocket 每秒推給前端,`/api/ai-summary` 回一句樣板。它教會你**資料形狀、`/api/snapshot` REST、`/ws` 推送、前端怎麼吃 JSON**。

但它是個**玩具**:資料是假的、摘要是死的。這一段是課程後半 —— 把同一個 dashboard 沿兩個獨立的軸「變成真的」,而且每一步都讓你回頭看清「你到底學到了什麼」。

兩個軸各自可獨立開關(可以只開一個):

| 軸 | Baseline(Part 1) | 升級(Part 2) | 切換 | extra |
|---|---|---|---|---|
| 資料源 | `simulated_snapshot()` | MQTT 真設備餵進來 | `SOURCE_BACKEND=sim\|mqtt` | `mqtt` |
| AI 摘要 | 規則式班報(確定性) | LLM 班報(會講人話) | `AI_SUMMARY=rule\|llm` | `ai` |

## 軸 A:模擬資料 → 真實 MQTT

**Part 1 你手上有什麼**:`/ws` 與 `/api/snapshot` 直接呼叫 `simulated_snapshot()`,資料是 `math`/`random` 算出來的假值。你學會了 dashboard 的資料契約(agvs / machines / alerts)。

**Part 2 換成什麼**:工廠現場的設備(PLC、AGV 控制器、edge gateway)把狀態 publish 到 MQTT broker;`app/ingest_mqtt.py` 一個背景 task 訂閱 topic、把最新一筆存進 cache;`SOURCE_BACKEND=mqtt` 時 dashboard 改從 cache 讀。

```bash
uv sync --extra mqtt
# 終端 A:啟動 dashboard(改吃 MQTT)
SOURCE_BACKEND=mqtt MQTT_URL=mqtt://127.0.0.1:1883 uv run uvicorn app.main:app
# 終端 B:把一筆 snapshot publish 到 dashboard/snapshot topic(用任何 MQTT client)
```

跑對照測試(用 in-process broker,不需要裝 mosquitto):

```bash
PYTHONPATH=. uv run python mqtt_smoke_test.py
```

它起一個 in-process broker、跑 app 的 subscriber、publish 一筆已知 snapshot,然後斷言 `/api/snapshot` 回的就是那筆。成功會看到 `OK: MQTT ingest smoke passed`。

**你因此看清什麼**:資料源是**可抽換的**——`/ws`、`/api/snapshot`、整個前端**一行都不用改**,只是後面餵資料的人從「模擬器」換成「真設備」。這就是「把 PoC 接上真實產線」的第一步,也是為什麼 Part 1 要先把資料契約定清楚。

## 軸 B:樣板摘要 → 規則式 → LLM 班報

**Part 1 你手上有什麼**:原本 `/api/ai-summary` 是一行 f-string。這一段先把它升級成**真.規則式摘要**(`app/summary.py:rule_summary`):數 AGV、列低電量、列異常機台、數告警 —— 確定性、可測、不需要任何外部服務。

**Part 2 換成什麼**:`llm_summary` 把同一份 snapshot 丟給 OpenAI 相容的 LLM,產一句自然語言班報;`AI_SUMMARY=llm` 切換。

```bash
uv sync --extra ai
# .env / 環境變數:AI_SUMMARY=llm, HTTP_LLM_ENDPOINT, HTTP_LLM_API_KEY, MODEL_NAME
AI_SUMMARY=llm uv run uvicorn app.main:app
```

跑對照測試(用本地假 OpenAI server,免 API key):

```bash
PYTHONPATH=. uv run python ai_smoke_test.py
```

它斷言:規則式摘要對固定 snapshot 回確定字串;LLM 路徑接到(假的)OpenAI endpoint 回班報。成功會看到 `OK: AI summary smoke passed`。

**你因此看清什麼**:摘要從「死板模板」變成「會講人話」,但**規則式仍然有用**——它確定、免費、可測,是 LLM 不穩或沒預算時的 fallback。你也看清 LLM 只是一層:餵它的 context(snapshot)還是你自己準備的。

## 回顧:這個 dashboard 你一路學到的

- **Part 1(玩具)**:資料契約、REST + WebSocket、前端吃 JSON —— 先讓整條路會動。
- **軸 A**:資料源可抽換 —— 同一個 UI,假資料換成真 MQTT,學到「PoC → 真產線」怎麼接。
- **軸 B**:摘要從模板 → 規則式 → LLM —— 學到「確定性 baseline」與「LLM 升級」各自的價值與取捨。

兩個軸都用 **optional extra** 隔離(base 安裝只有 fastapi + uvicorn),要哪個能力才裝哪個;預設 `sim` + `rule` 永遠零相依可跑。下一步若要再進階:接 ROS2 / PLC / Modbus(沿用軸 A 的「換資料源」)、多客戶端 pub/sub、把規則式 + LLM 做成 hybrid。
````

- [ ] **Step 2: Verify commands + no emoji.**

Run: `uv sync --extra mqtt && PYTHONPATH=. uv run python mqtt_smoke_test.py && uv sync --extra ai && PYTHONPATH=. uv run python ai_smoke_test.py && uv sync`
Expected: both OK lines.
Run: `grep -nP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/08-real-data-and-ai-summary.md || echo "no emoji"` → `no emoji`.

- [ ] **Step 3: Commit.**

```bash
git add docs/08-real-data-and-ai-summary.md
git commit -m "docs: add real-data + AI-summary second-half lesson (08)"
```

---

## Task 10: Reframe overview + mirror into tutorial/README/index/DESIGN

**Files:** Modify `docs/00-overview.md`, `tutorial.html`, `README.md`, `index.html`, `DESIGN.md`.

- [ ] **Step 1: `docs/00-overview.md`** — read it (`cat docs/00-overview.md`), then insert after the first intro paragraph (before the next `##`), verbatim:

```markdown
## 兩軌:先玩具、再真實

這份教材分兩段:

- **前半段(`01`、`03`)** — 用模擬資料 + 樣板摘要做出會動的 dashboard,看懂資料契約、REST、WebSocket、前端吃 JSON。
- **後半段(`08`)** — 沿兩個獨立軸把它變成真的:資料源 `sim → MQTT`、AI 摘要 `規則式 → LLM 班報`,而前端與 API 一行都不用改。

先用玩具看懂整條路,再逐軸接上真實資料與 AI —— 你會清楚知道哪些是可抽換的、哪些是你自己的責任。
```
If `docs/00-overview.md` lists the doc series, add an entry for `08-real-data-and-ai-summary.md`(`接真實 MQTT 資料 + LLM 班報的對照組`) in the existing list style.

- [ ] **Step 2: `README.md`** — add to Features/功能 list (match style):

```markdown
- 後半段:接真實 MQTT 資料(`mqtt` extra)+ LLM 班報(`ai` extra)— 見 `docs/08-real-data-and-ai-summary.md`
```
After the existing quick-start/run block, add:

````markdown
### 後半段:接真實資料 + AI 班報(對照組)

```bash
uv sync --extra mqtt && PYTHONPATH=. uv run python mqtt_smoke_test.py   # 真資料對照(in-process broker)
uv sync --extra ai   && PYTHONPATH=. uv run python ai_smoke_test.py     # LLM 班報對照(假 OpenAI)
SOURCE_BACKEND=mqtt AI_SUMMARY=llm uv run uvicorn app.main:app          # 兩軸都開
```
````
If README has a docs/ link list, add `- 後半段(真資料 + AI 班報):docs/08-real-data-and-ai-summary.md`.

- [ ] **Step 3: `DESIGN.md`** — in the 功能賣點/features list, add (match style):

```markdown
- 內建後半段對照組(`docs/08`):資料源 sim→MQTT、AI 摘要 規則式→LLM,各為 optional extra、可獨立開關
```
(If DESIGN.md frames MQTT/AI purely as a future direction now made redundant, point it at the built-in docs/08 instead.)

- [ ] **Step 4: `index.html`** — in the features card `<ul>`, add one `<li>` matching sibling structure exactly:

```html
<li><span>後半段接真實 MQTT 資料與 LLM 班報(對照組),各為可獨立開關的 optional extra</span></li>
```

- [ ] **Step 5: `tutorial.html`** — read it (`cat tutorial.html`). (a) Add an `08` TOC anchor after the `07-...` anchor, **matching the exact sibling href format** (relative `docs/08-real-data-and-ai-summary.md` or full GitHub blob URL — match 00-07). (b) If the 總覽 section mirrors `docs/00-overview.md`, add the same 兩軌 subsection there too (keep mirror in sync). (c) Append a Part 2 `<section>` inside `<main>` (before `</main>`) mirroring `docs/08`'s two axes + recap, using the file's element conventions; commands must match docs/08 verbatim; no fabricated output.

- [ ] **Step 6: Verify.**

Run:
```bash
uv run python -c "import html.parser; html.parser.HTMLParser().feed(open('tutorial.html').read()); print('tutorial ok')"
uv run python -c "import html.parser; html.parser.HTMLParser().feed(open('index.html').read()); print('index ok')"
test -f docs/08-real-data-and-ai-summary.md && echo "link target exists"
grep -rnP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/ README.md DESIGN.md tutorial.html index.html || echo "no emoji"
```
Expected: `tutorial ok`, `index ok`, `link target exists`, `no emoji` (the index.html CSS `li:before` ornament, if any, is pre-existing — only flag NEW emoji in added content).

- [ ] **Step 7: Commit.**

```bash
git add docs/00-overview.md tutorial.html README.md index.html DESIGN.md
git commit -m "docs: surface the real-data + AI-summary two-track in overview/tutorial/README/index/DESIGN"
```

---

## Final verification (after all tasks)

- [ ] **Three tracks green:**

```bash
uv sync && PYTHONPATH=. uv run python base_smoke_test.py
uv sync --extra mqtt && PYTHONPATH=. uv run python mqtt_smoke_test.py
uv sync --extra ai && PYTHONPATH=. uv run python ai_smoke_test.py
uv sync
```
Expected: three `OK:` lines.

- [ ] **Base isolation:** `uv sync && PYTHONPATH=. uv run python -c "import app.main; import importlib.util as u; print('amqtt:', u.find_spec('amqtt') is not None, 'httpx:', u.find_spec('httpx') is not None)"` → `amqtt: False httpx: False`, no import error.

- [ ] **No emoji drift:** `grep -rnP "[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}]" docs/ README.md DESIGN.md tutorial.html || echo "clean"`.

---

## Self-review notes (author)

- **Spec coverage:** §2 two axes → Tasks 2/3/4; §3 verified facts → scratch-proven; §4 files → Tasks 1-10; axis A (sim→MQTT) → Tasks 3/4/6; axis B (stub→rule→LLM) → Tasks 2/4/7; optional extras → Task 1; CI 3 tracks → Task 8; docs/08 with the "Part1→Part2→你看清什麼" + 回顧 framing → Task 9; two-track surfacing → Task 10.
- **Placeholder scan:** all code blocks complete and scratch-verified (amqtt round-trip, llm via fake OpenAI, rule_summary, base-no-httpx constraint, lazy imports); doc tasks give exact insert blocks; tutorial/overview tasks read the file first (and Task 10 explicitly flags matching the TOC href format + syncing the 總覽 mirror — the two drift gotchas from prior repos).
- **Base-deps gotcha:** base has NO httpx → base_smoke avoids TestClient (functions only); only the ai track (httpx) uses TestClient. Captured in Tasks 5/7.
- **Name consistency:** `current_snapshot` / `simulated_snapshot` / `rule_summary` / `llm_summary` / `start_subscriber` / `latest` / `_cache` / config getters `source_backend`/`ai_summary_mode`/`mqtt_url`/`mqtt_topic`/`llm_endpoint`/`llm_api_key`/`model_name` / env `SOURCE_BACKEND`/`AI_SUMMARY`/`MQTT_URL`/`MQTT_TOPIC`/`HTTP_LLM_*` / extras `mqtt`,`ai` / tests `base_smoke_test.py`,`mqtt_smoke_test.py`,`ai_smoke_test.py` — consistent across tasks.
