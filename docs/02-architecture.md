# 工業 AI Dashboard 入門模板：架構說明

## 核心檔案

- app/main.py：FastAPI、靜態檔案、REST API、WebSocket
- app/data_source.py：模擬 AGV / machines / alerts 資料
- static/index.html：dashboard 頁面
- static/app.js：連線 WebSocket 並渲染資料
- static/style.css：dashboard UI 樣式

## 資料流

1. app/data_source.py 用時間函數模擬 AGV / machines / alerts 狀態（simulated_snapshot）。
2. FastAPI 以 REST 提供 /api/snapshot，回傳目前這一刻的完整快照。
3. /api/ai-summary 是 AI 摘要佔位 API，之後可換成真正的 LLM 呼叫。
4. WebSocket /ws 每秒把同一份模擬狀態推送給前端。
5. static/ 前端（index.html + app.js）連上 /ws，即時渲染 AGV、機台與告警。

## 設計原則

- 先讓流程可跑，再做漂亮抽象。
- 這個 starter 沒有任何 secret；等你接真實資料來源或 LLM 時，token 與 secrets 才放進環境變數，不要寫死在程式裡。
- 每一層保持可以替換：資料來源、AI provider、部署方式。
- 範例程式刻意保持小，方便你看懂後改成自己的版本。
