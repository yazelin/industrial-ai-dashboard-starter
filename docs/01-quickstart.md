# 工業 AI Dashboard 入門模板：快速開始

這份文件帶你「從 clone 到看見即時儀表板」走一遍。每一步都有：要打的指令 → 跑完的真實輸出 → 「成功的話你會看到：…」。照著做到最後，你會有一個每秒更新的 AGV / 機台監控頁面在瀏覽器上跑。

## 前置需求

- Python 3.10 以上（本文以 Python 3.12 實測）
- Git
- 會用終端機
- 不需要任何 API key、token 或 `.env`。這個 starter 全部用模擬資料，開箱即可跑。

## 它在做什麼（30 秒版）

- `app/data_source.py` 產生一份模擬快照（3 台 AGV、2 台機台、依電量產生告警）。
- `app/main.py` 用 FastAPI 把這份快照開成 REST API 與 WebSocket。
- `static/` 是一個 zero-build 的前端，連上 `/ws` 每秒重畫畫面。

## 步驟 1：取得程式碼並安裝

```bash
git clone https://github.com/yazelin/industrial-ai-dashboard-starter.git
cd industrial-ai-dashboard-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 只有兩個套件，安裝很快：

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
```

**成功的話你會看到：** `pip` 結束時印出 `Successfully installed ...`，而且終端機提示字元前面多了 `(.venv)`。

## 步驟 2：啟動服務

**注意：一定要在 repo 根目錄（看得到 `app/` 資料夾的那層）執行**，否則會 `ModuleNotFoundError: No module named 'app'`（見 `05-common-pitfalls.md`）。

```bash
uvicorn app.main:app --reload --port 8000
```

**成功的話你會看到：**

```
INFO:     Will watch for changes in these directories: ['/.../industrial-ai-dashboard-starter']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [787819] using WatchFiles
INFO:     Started server process [787821]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

看到 `Application startup complete.` 就代表服務起來了。終端機會停在這裡持續執行，不會跳回提示字元，這是正常的。

## 步驟 3：打開儀表板

瀏覽器開 <http://127.0.0.1:8000/>。

**成功的話你會看到：** 一個深藍底的單頁儀表板，標題是「Industrial AI Dashboard」，右上有一顆「AI Summary」按鈕。畫面分成：

- 最上方一排橘色邊框的告警條（例如 `warning: AGV-3 low battery`），會隨電量變化出現或消失。
- 中段兩張卡片：左邊「AGVs」列出三台 AGV 的座標、狀態與電量百分比；右邊「Machines」列出 `AOI-1` 與 `PLC-Press-2` 的狀態。
- 最下方一塊黑底的原始 JSON，每秒跳一次數字——那是 WebSocket 即時推進來的。

數字每秒在動，就代表 WebSocket 串流通了。

## 步驟 4：用 curl 驗證 API（不靠瀏覽器也能確認）

```bash
curl http://127.0.0.1:8000/api/snapshot
```

**真實輸出**（這是實跑擷取的，剛好兩台 AGV 電量低於 20，所以 `alerts` 真的有東西）：

```json
{
    "timestamp": 1780342125.2277737,
    "agvs": [
        {"id": "AGV-1", "x": 47.0, "y": 17.2, "battery": 46.5, "status": "loading"},
        {"id": "AGV-2", "x": 19.0, "y": 21.9, "battery": 11.2, "status": "charging"},
        {"id": "AGV-3", "x": 19.5, "y": 52.4, "battery": 9.3, "status": "charging"}
    ],
    "machines": [
        {"id": "AOI-1", "status": "warn", "ng_rate": 0.52},
        {"id": "PLC-Press-2", "status": "stop", "temperature": 49.2}
    ],
    "alerts": [
        {"level": "warning", "message": "AGV-2 low battery"},
        {"level": "warning", "message": "AGV-3 low battery"}
    ]
}
```

> 電量是用三角函數隨時間擺動的，所以你跑的時候 `alerts` 可能是空陣列 `[]`，多刷新幾次（或等幾秒）就會看到電量低於 20 的告警冒出來。

再試 AI summary 佔位 API：

```bash
curl http://127.0.0.1:8000/api/ai-summary
```

**真實輸出：**

```json
{"summary":"3 AGVs online, 2 alerts."}
```

這個 summary 目前是一句樣板字串（`app/main.py` 裡組出來的），之後要接真的 LLM 就改這裡。

## 步驟 5（選做）：直接看 WebSocket 串流

不想開瀏覽器也能確認 `/ws` 有在推。先裝 `websockets`（只是測試用，不是專案相依）：

```bash
pip install websockets
python - <<'PY'
import asyncio, json
from websockets.asyncio.client import connect
async def main():
    async with connect("ws://127.0.0.1:8000/ws") as ws:
        for i in range(3):
            msg = json.loads(await ws.recv())
            print(f"frame {i}: ts={msg['timestamp']:.0f} agvs={len(msg['agvs'])} alerts={len(msg['alerts'])}")
asyncio.run(main())
PY
```

**真實輸出：**

```
frame 0: ts=1780342126 agvs=3 alerts=2
frame 1: ts=1780342127 agvs=3 alerts=2
frame 2: ts=1780342128 agvs=3 alerts=2
```

三個 frame 的 timestamp 一秒差一個，代表伺服器確實每秒推一次。

## 整體 OK 的判斷標準

全部成立就代表這一輪成功：

1. 終端機停在 `Application startup complete.`，沒有 traceback。
2. <http://127.0.0.1:8000/> 打得開，最下方 JSON 每秒在跳。
3. `curl http://127.0.0.1:8000/api/snapshot` 回傳含 `agvs` / `machines` / `alerts` 的 JSON。
4. `curl http://127.0.0.1:8000/api/ai-summary` 回傳一句 `summary`。

接著看 `03-step-by-step.md`，把模擬資料換成你自己的來源，並動手做一個小練習。

## 常用入口一覽

- `GET /`：dashboard UI
- `GET /api/snapshot`：目前 AGV / machines / alerts 快照
- `GET /api/ai-summary`：AI summary 佔位 API
- `WebSocket /ws`：每秒推送即時快照
