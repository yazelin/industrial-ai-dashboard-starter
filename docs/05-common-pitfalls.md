# 工業 AI Dashboard 入門模板：常見問題與踩雷清單

這份清單裡的錯誤訊息，都是實際跑這個 starter 時會遇到、且我這次實測重現過的。每條都附「真實錯誤訊息 → 為什麼 → 怎麼修」。

## 1. 在錯的目錄啟動：`No module named 'app'`

最常見。`uvicorn app.main:app` 是用「import path」找程式，所以你的當前目錄一定要看得到 `app/` 這個資料夾。如果在別的目錄（例如 `/tmp`、或進到 `app/` 裡面）啟動：

```
ModuleNotFoundError: No module named 'app'
```

完整 traceback 結尾就是這行。**修法：** 回到 repo 根目錄（`ls` 看得到 `app/`、`static/`、`pyproject.toml`）再啟動：

```bash
cd /path/to/industrial-ai-dashboard-starter
uv run uvicorn app.main:app --reload --port 8000
```

## 2. 連接埠被占用：`address already in use`

如果 8000 埠已經有別的程式（包括你上一個沒關掉的 uvicorn）在用：

```
ERROR:    [Errno 98] error while attempting to bind on address ('127.0.0.1', 8000): address already in use
```

**修法二選一：**

- 換一個埠：`uv run uvicorn app.main:app --reload --port 8001`，網址也跟著改成 `:8001`。
- 或找出占用的程式關掉：Ubuntu / macOS 用 `lsof -i :8000` 看到 PID 後 `kill <PID>`；Windows PowerShell 用 `Get-NetTCPConnection -LocalPort 8000` 看 PID 後 `Stop-Process -Id <PID>`。

## 3. WebSocket 連不上：前端不更新、路徑打錯

前端 `static/app.js` 連的是 `/ws`。如果你改前端時把路徑打成別的（例如 `/websocket`），瀏覽器 console 會出現連線失敗，畫面停在空白、不再每秒更新。用程式去連錯路徑可以重現伺服器端的拒絕：

```
InvalidStatus: server rejected WebSocket connection: HTTP 403
```

**為什麼：** FastAPI 只在 `@app.websocket("/ws")` 註冊了這一條，連其他路徑就被拒。**修法：** 確認前端的 WebSocket URL 路徑是 `/ws`，且 `ws`/`wss` 的協定要跟頁面一致（http 用 `ws`、https 用 `wss`，`app.js` 已經幫你判斷了）。改完記得在瀏覽器硬重新整理（Ctrl/Cmd+Shift+R）讓舊的 JS 不要被快取。

## 4. 看到空的 `alerts: []`，以為壞了

`/api/snapshot` 有時回傳 `"alerts": []`，這不是 bug。告警是「AGV 電量低於 20」才產生，而電量是隨時間用三角函數擺動的。等幾秒或多刷新幾次，電量降下去就會看到 `low battery` 告警。同理，`03` 章末練習加的 `overheat` 也是溫度超過 80 才出現。

## 5. 終端機「卡住」不動，其實是正常的

啟動後看到 `Application startup complete.` 然後游標停在那裡、不回到提示字元——這是對的。uvicorn 是常駐服務，要一直跑著。**不要** 在這個視窗繼續打指令；另開一個終端機分頁去 `curl` 或做別的事。要停服務就在這個視窗按 `Ctrl+C`。

## 6. `uv: command not found`／`uv` 不是內部或外部命令

還沒裝 uv，或裝完沒重開終端機（uv 安裝後才把自己加進 PATH）：

```
uv: command not found
```

Windows PowerShell 則是 `The term 'uv' is not recognized ...`。**修法：** 照 `01-quickstart.md` 步驟 1 裝 uv（Ubuntu / macOS 用 `curl -LsSf https://astral.sh/uv/install.sh | sh`；Windows 用 `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`），裝完**重開一個新的終端機**，`uv --version` 印得出版本再繼續。

## 7. 忘了 `uv sync` 就直接 `uv run`／改了 `pyproject.toml` 沒重新 sync

在還沒 `uv sync`（環境還沒建好）、或剛 `git pull` 進新依賴卻沒重新 sync 的情況下啟動，會看到找不到套件：

```
ModuleNotFoundError: No module named 'fastapi'
```

**修法：** 先在 repo 根目錄跑一次 `uv sync`（會依 `pyproject.toml` + `uv.lock` 把 `.venv` 補齊），再 `uv run uvicorn app.main:app --reload --port 8000`。其實 `uv run` 通常會自動先同步一次，但若你是用其他方式（例如自己 `python -m uvicorn`）繞過 uv，就會踩到這條——本教學一律用 `uv run`。

## Debug 順序（針對這個 repo）

1. 終端機有沒有停在 `Application startup complete.`？沒有就看 traceback 第一行（多半是第 1 或第 2 條）。
2. `curl http://127.0.0.1:8000/api/snapshot` 有沒有回 JSON？沒有代表服務沒起來或埠不對。
3. 瀏覽器最下方 JSON 有沒有每秒在跳？沒跳就是 WebSocket（第 3 條），開 DevTools 看 console 與 Network 的 WS 分頁。
4. 改了 `data_source.py` 後出錯？看 uvicorn 視窗，`--reload` 會把語法錯誤直接印出來。
5. 把問題縮到最小可重現，再看完整錯誤訊息，不要只看最後一行。

## 問別人前準備

- repo / branch、你的 uv 版本（`uv --version`）與 Python 版本（`uv run python --version`）
- 你在哪個目錄、用什麼指令啟動
- 完整的錯誤訊息（整段 traceback，不是只貼最後一行）
- 你預期看到什麼、實際看到什麼
- 這個 starter 沒有 secret / token，不用擔心遮蔽；但養成習慣，未來接真服務時別把 key 貼出來
