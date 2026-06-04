# Design: industrial-ai-dashboard Part 2 — 真實 MQTT 資料 + LLM 班報(對照組)

- **Date:** 2026-06-04
- **Repo:** `industrial-ai-dashboard-starter`
- **Status:** Approved design (pending written-spec review)

## 1. 目標與動機

前半段是一個**玩具 dashboard**:`simulated_snapshot()` 產隨機/時間驅動的 AGV/機台資料,WebSocket 每秒推給前端;`/api/ai-summary` 是一行 f-string stub。它教會了資料形狀、`/api/snapshot` REST、`/ws` 推送、前端怎麼吃 JSON。

這個 repo 的「完全手刻 → 框架」對照不適用(單一薄實作)。後半段改走它真正適合、且 repo 自己 roadmap(docs/06)就列的方向:**把玩具變成「真的」**,沿兩個獨立升級軸。對照的價值在於讓學員回頭看清「一路學下來學到什麼」。

非目標:不引 pytest;前端 `static/` 不大改(資料來源對 UI 透明);不做 ROS2/PLC/Modbus(MQTT 一條代表);不做多客戶端 pub/sub(另一條軸,不混)。

## 2. 架構:1 baseline vs 2 獨立升級軸

REST + FastAPI 是 Part 1 底座(不動)。兩軸各自可獨立開關:

| | Baseline（Part 1） | 升級（Part 2） | 切換 | 隔離 |
|---|---|---|---|---|
| **軸 A 資料源** | `simulated_snapshot()`(隨機/時間) | MQTT 背景訂閱 → cache | `SOURCE_BACKEND=sim\|mqtt` | optional `mqtt` extra |
| **軸 B AI 摘要** | 規則式摘要(確定性) | LLM 班報(OpenAI 相容) | `AI_SUMMARY=rule\|llm` | optional `ai` extra |

注意:Part 1 的 `/api/ai-summary` 目前是 4 行 stub —— 本案先把它**升級成真.規則式摘要**(才有「兩個真實作」的誠實對照,不是填空)。

## 3. 已驗證的技術事實

- **amqtt 0.11.3**(16 套件,純 Python):in-process `Broker` + `MQTTClient` 的 publish/subscribe round-trip 實測成功 → MQTT 軸的確定性、免外部 mosquitto 的 CI 測試可行(app 當 client、測試當 broker)。
- LLM 軸的確定性測試沿用 linebot 已驗證模式:app 用 httpx POST 到 OpenAI 相容 endpoint;測試把 endpoint 指向**本地假 OpenAI server**(回 canned `choices[0].message.content`),斷接線、免 key。
- 規則式摘要是純 Python,對固定 snapshot 確定性。
- 現有 deps 只有 fastapi + uvicorn(連 httpx 都沒有)→ `ai` extra 需帶 httpx。

## 4. 檔案清單

### 程式碼
- **`app/summary.py`(新)**:
  - `rule_summary(snapshot) -> str`:確定性規則式班報(AGV 線上數、低電量清單、異常機台、警告數)。
  - `llm_summary(snapshot) -> str`:httpx 對 `HTTP_LLM_ENDPOINT` 發 OpenAI 相容 chat completions,把 snapshot 摘要丟進 prompt,回 `choices[0].message.content`。
- **`app/ingest_mqtt.py`(新)**:
  - in-memory `_cache`(最新 snapshot)。
  - `start_subscriber()`:背景 task,amqtt client 連 `MQTT_URL`、訂閱 `MQTT_TOPIC`(預設 `dashboard/snapshot`),收到 JSON 就更新 `_cache`。
  - `latest() -> snapshot | None`:回 cache。
- **`app/config.py`(新,集中 env)**:`SOURCE_BACKEND`(預設 sim)、`AI_SUMMARY`(預設 rule)、`MQTT_URL`、`MQTT_TOPIC`、`HTTP_LLM_ENDPOINT`/`HTTP_LLM_API_KEY`/`MODEL_NAME`。(目前 env 散落;集中以利兩軸切換)
- **`app/main.py`(改)**:
  - `/api/snapshot` 與 `/ws`:`SOURCE_BACKEND=mqtt` 時讀 `ingest_mqtt.latest()`(無資料則退回 sim 或回空),否則 `simulated_snapshot()`。lazy import ingest_mqtt(只有 mqtt 模式才碰 amqtt)。
  - startup:`SOURCE_BACKEND=mqtt` 時起 `start_subscriber()` 背景 task。
  - `/api/ai-summary`:依 `AI_SUMMARY` 走 `rule_summary` 或 `llm_summary`(llm lazy import httpx)。
- **`pyproject.toml`(改)**:`[project.optional-dependencies] mqtt = ["amqtt>=0.11,<0.12"]`、`ai = ["httpx>=0.28,<0.29"]`。`package = false` 不變。
- **`uv.lock`（重產）**。

### 測試 / CI
- **`base_smoke_test.py`(新,base)**:不裝 extra。斷言 `simulated_snapshot()` 形狀;`rule_summary(<固定 snapshot>)` 回確切字串。
- **`mqtt_smoke_test.py`(新,mqtt extra)**:起 in-process amqtt broker → 起 app 的 subscriber → publish 一筆已知 snapshot → 斷言 `ingest_mqtt.latest()` / `/api/snapshot`(`SOURCE_BACKEND=mqtt`,TestClient)回那筆。
- **`ai_smoke_test.py`(新,ai extra)**:起本地假 OpenAI server → `AI_SUMMARY=llm` 指向它 → 呼叫 `/api/ai-summary`(TestClient)→ 斷言回假 server 的 canned 班報;另斷 `rule_summary` 確定性。
- **`.github/workflows/ci.yml`(新)**:matrix 3 軌 `base` / `mqtt` / `ai`,各裝對應 extra 跑對應 smoke。

### 文件(對照 + 回顧框架)
- **`docs/08-real-data-and-ai-summary.md`(新)**:兩節(資料軸、AI 軸),每節用「**Part 1 你手上有什麼 → Part 2 換成什麼 → 你因此看清什麼**」框架,結尾一段「回顧:這個 dashboard 你學到的」串起整條路(玩具 → 真資料 + 真 AI)。
- **`docs/00-overview.md`、`tutorial.html`(含 TOC 補 08)、`README.md`、`index.html`、`DESIGN.md`(改)**:兩軌/兩軸化;真實資料源 + AI 班報從「可延伸」升格為「內建後半段」。

## 5. 對照測試(這軌是「baseline vs 升級」對照,非「兩版行為相同」)

- 軸 A:sim 是隨機/時間;mqtt 是「真的 publish 什麼,dashboard 就顯示什麼」。測試發已知 payload → 斷言 dashboard 回該 payload(證明資料源可抽換、UI 不動)。
- 軸 B:`rule_summary` 對固定 snapshot 回確切模板字串(確定性);`llm_summary` 對本地假 OpenAI 回 canned 自然語言(證明接線、免 key)。對照=模板 vs 會講人話。

## 6. 錯誤處理 / 邊界

- `SOURCE_BACKEND=mqtt` 但 cache 尚無資料(broker 還沒推):`/api/snapshot` 回上一筆或空結構(明確、不 500);文件註明要先有 publisher。
- `ingest_mqtt` / `llm_summary` 的相依只在各自模式 lazy import,base(sim+rule)匯入鏈不碰 amqtt/httpx。
- 假 OpenAI server 回 `{"choices":[{"message":{"content":"<班報>"}}]}`;llm_summary 讀該欄位。

## 7. 風險與待確認(writing-plans 前 scratch 驗)

- **app subscriber + in-process broker + TestClient 整合**:已驗 amqtt 純 round-trip;app 啟動背景 task + cache + TestClient 讀 `/api/snapshot` 的整合於 plan 前 scratch 驗(時序:publish 後等 cache 更新)。
- **amqtt client API 形狀**(connect/subscribe/deliver_message)寫進 app 前以 scratch 定版;deprecation warnings 為良性。
- **假 OpenAI server for llm_summary**:沿用 linebot 已驗模式,plan 前快速 scratch 確認 summary 路徑。
- 版本鎖:`amqtt>=0.11,<0.12`、`httpx>=0.28,<0.29`;smoke + CI 為防線。

## 8. 不做（YAGNI）

- ROS2 / PLC / Modbus(MQTT 一條代表)。
- 多客戶端 pub/sub(獨立軸,不混本案)。
- 不引 pytest(plain-python smoke script)。
- 前端 `static/` 不大改(資料來源對 UI 透明)。
- 不動 `simulated_snapshot()`(保留為 baseline)。
- 跨 5-repo 的「課程地圖」總覽是獨立可選項,不混進本 repo。
