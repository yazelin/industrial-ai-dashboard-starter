# 工業 AI Dashboard 入門模板：快速開始

## 前置需求

- Python 3.10+
- Git
- 可以使用終端機
- 如果要接真實 AI 或平台 token，請準備對應帳號與 API key。

## 最短路徑

1. 啟動 FastAPI
2. 打開 dashboard UI
3. 觀察 WebSocket 即時資料
4. 把 simulated_snapshot 替換成真實資料來源

## 安裝與啟動

```bash
git clone https://github.com/yazelin/industrial-ai-dashboard-starter.git
cd industrial-ai-dashboard-starter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# open http://127.0.0.1:8000/
```

## 健康檢查

```bash
curl http://127.0.0.1:8000/api/snapshot
```

## 常用入口

- GET /：dashboard UI
- GET /api/snapshot：目前 AGV / machines / alerts 快照
- GET /api/ai-summary：簡單 AI summary 佔位 API
- WebSocket /ws：每秒推送即時資料

## 第一次成功的標準

- 服務能啟動
- 基本 endpoint 有回應
- 範例流程能跑通
- 秘密 token 沒有 commit 到 GitHub
