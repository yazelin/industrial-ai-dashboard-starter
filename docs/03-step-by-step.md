# 工業 AI Dashboard 入門模板：完整操作流程

`01-quickstart.md` 讓你把東西跑起來。這份文件帶你「真的改一次資料來源」，並在章末做一個你自己動手、可驗證的小練習。

前提：你已照 quickstart 把服務跑起來，且用的是 `--reload`（這樣存檔就自動重載，不用手動重啟）。

## 全貌：資料怎麼從 Python 流到瀏覽器

```
app/data_source.py        app/main.py                 static/app.js
simulated_snapshot()  -->  /api/snapshot (REST)   -->  fetch
                      -->  /ws (WebSocket, 每秒)   -->  ws.onmessage --> 重畫畫面
```

整個 starter 的核心只有一個函式：`simulated_snapshot()`。它回傳一個 dict，前端只認得這個 dict 的「形狀」。**你要做的事，就是把這個函式換成讀真實資料，但保持回傳的形狀不變。**

## 先看清楚「形狀」是什麼

打開 `app/data_source.py`，`simulated_snapshot()` 回傳的結構長這樣（欄位名稱與型別才是契約，數值會變）：

```json
{
  "timestamp": 1780342125.22,
  "agvs":     [ {"id": "AGV-1", "x": 47.0, "y": 17.2, "battery": 46.5, "status": "loading"} ],
  "machines": [ {"id": "AOI-1", "status": "warn", "ng_rate": 0.52} ],
  "alerts":   [ {"level": "warning", "message": "AGV-2 low battery"} ]
}
```

前端 `static/app.js` 只依賴這幾個 key：`d.agvs`（要有 `id`/`x`/`y`/`status`/`battery`）、`d.machines`（`id`/`status`）、`d.alerts`（`level`/`message`）。只要你回傳同樣形狀，前端一行都不用改。

## 步驟 1：把模擬來源換成真實來源（before / after）

假設你要從一支內部 HTTP API（或 MQTT、Modbus、ROS2 bridge…任何能讀到現場資料的東西）取得 AGV 狀態。原則是：**只改 `data_source.py`，把外部資料「轉成」上面那個形狀。**

**改之前**（節錄，模擬版）：

```python
def simulated_snapshot():
    t = time.time() - START
    agvs = []
    for i in range(1, 4):
        b = round(5 + 85 * (0.5 + 0.5 * math.cos(t/30 + i)), 1)
        agvs.append({"id": f"AGV-{i}", ..., "battery": b, "status": ...})
    ...
    return {"timestamp": time.time(), "agvs": agvs, "machines": machines, "alerts": alerts}
```

**改成這樣**（示意：從真實來源讀，再 map 成同樣欄位）：

```python
import time
import requests  # 記得 uv add requests（會同時更新 pyproject.toml 與 uv.lock）

FLEET_API = "http://10.0.0.5:9000/agvs"  # 換成你的現場端點

def real_snapshot():
    raw = requests.get(FLEET_API, timeout=2).json()   # 你的現場資料，欄位是它自己的命名
    agvs = [
        {
            "id":      r["agv_name"],          # 把現場欄位 map 到契約欄位
            "x":       r["pos_x"],
            "y":       r["pos_y"],
            "battery": r["soc"],               # 例如現場叫 soc (state of charge)
            "status":  r["mode"],
        }
        for r in raw["units"]
    ]
    machines = []  # 同理：把機台來源 map 成 {"id","status",...}
    alerts = [{"level": "warning", "message": f'{a["id"]} low battery'}
              for a in agvs if a["battery"] < 20]
    return {"timestamp": time.time(), "agvs": agvs, "machines": machines, "alerts": alerts}
```

接著在 `app/main.py` 把 `from .data_source import simulated_snapshot` 換成你的新函式（或直接讓 `simulated_snapshot` 內部改讀真實來源）。前端、WebSocket、REST 路由都不用動。

> 實務提醒：`requests.get(...)` 是「阻塞」呼叫，放在 `/ws` 的迴圈裡會卡住 event loop。正式接線時請改用背景任務定時更新一份 cache，handler 只讀 cache。這部分在 `05-common-pitfalls.md` 與 `06-customize-for-your-use-case.md` 有展開。

**改完跑出來會變這樣：** `/api/snapshot` 的 JSON 形狀完全一樣，只是 `agvs` 裡的數字變成你現場的真實值；前端畫面照常每秒更新，不需要改任何前端程式。

## 步驟 2：加入歷史與 AI summary（方向）

- 歷史：在背景任務裡把每次 snapshot 存進記憶體 ring buffer 或時序資料庫，再多開一個 `GET /api/history` 回傳近 N 筆。
- AI summary：目前 `/api/ai-summary` 回傳的是樣板字串。要接真 LLM，就把 `app/main.py` 的 `summary()` 改成把當前 `alerts` 丟給模型生成一句班報。
  - 需要你自己的 LLM API key，本文不實跑這段。設好金鑰後，你會看到 `summary` 從固定樣板變成模型寫的句子。

---

## 動手練習：新增一台機台 + 一條告警規則（我已實跑驗證）

目標：在 `machines` 多一台 `CNC-3`，並新增「機台溫度過高就發 critical 告警」的規則。完成後不用改前端，畫面與 `/api/snapshot` 就會多出新機台與新告警。

### Before

`app/data_source.py` 原本的 `machines` 與 `alerts`：

```python
machines = [
    {"id": "AOI-1", "status": random.choice(["run","run","warn"]), "ng_rate": round(random.random()*3, 2)},
    {"id": "PLC-Press-2", "status": random.choice(["run","run","stop"]), "temperature": round(45+random.random()*20, 1)},
]
alerts = [{"level": "warning", "message": a["id"]+" low battery"} for a in agvs if a["battery"] < 20]
```

### After

加一台 `CNC-3`（溫度刻意偏高，會在 60~90 之間），並加一條「溫度 > 80 發 critical」的規則：

```python
machines = [
    {"id": "AOI-1", "status": random.choice(["run","run","warn"]), "ng_rate": round(random.random()*3, 2)},
    {"id": "PLC-Press-2", "status": random.choice(["run","run","stop"]), "temperature": round(45+random.random()*20, 1)},
    {"id": "CNC-3", "status": random.choice(["run","run","stop"]), "temperature": round(60+random.random()*30, 1)},
]
alerts = [{"level": "warning", "message": a["id"]+" low battery"} for a in agvs if a["battery"] < 20]
alerts += [{"level": "critical", "message": m["id"]+" overheat"} for m in machines if m.get("temperature", 0) > 80]
```

### 驗證

存檔（`--reload` 會自動重載），刷新 `/api/snapshot`。**這是我實跑擷取的真實輸出**（剛好遇到 `CNC-3` 89.4 度，觸發了 critical 告警）：

```json
{
    "machines": [
        {"id": "AOI-1", "status": "run", "ng_rate": 1.54},
        {"id": "PLC-Press-2", "status": "stop", "temperature": 54.1},
        {"id": "CNC-3", "status": "run", "temperature": 89.4}
    ],
    "alerts": [
        {"level": "warning", "message": "AGV-3 low battery"},
        {"level": "critical", "message": "CNC-3 overheat"}
    ]
}
```

打開瀏覽器，「Machines」卡片會多一列 `CNC-3`；當溫度衝破 80，最上方告警條會多一條 `critical: CNC-3 overheat`。

> 溫度是隨機的，所以不是每次刷新都會超過 80。多刷幾次（或等幾秒）就會看到 overheat 告警出現又消失。

做完這個練習，你就完整體驗了這個 starter 的擴充方式：**改 `data_source.py` 的回傳內容 → 前端自動跟著變**。把同樣手法套到真實資料來源，就是把它變成你工廠的監控雛形。

## 完整流程後的下一步

把最小流程跑通、練習做完之後，先別急著堆功能。挑一個你手上真實、但很小的情境（例如「我只想監看這一條線的兩台 AGV 電量」），讓這個 starter 先把那一個問題解乾淨，再往外長。
