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
