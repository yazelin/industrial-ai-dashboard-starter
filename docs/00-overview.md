# 工業 AI Dashboard 入門模板：總覽

先用模擬 AGV / machine data 做出 dashboard，再替換成 MQTT、ROS2、Modbus 或 PLC API。

## 兩軌:先玩具、再真實

這份教材分兩段:

- **前半段(`01`、`03`)** — 用模擬資料 + 樣板摘要做出會動的 dashboard,看懂資料契約、REST、WebSocket、前端吃 JSON。
- **後半段(`08`)** — 沿兩個獨立軸把它變成真的:資料源 `sim → MQTT`、AI 摘要 `規則式 → LLM 班報`,而前端與 API 一行都不用改。

先用玩具看懂整條路,再逐軸接上真實資料與 AI —— 你會清楚知道哪些是可抽換的、哪些是你自己的責任。

## 適合誰

自動化、AGV、PLC、工業 IoT 工程師，想先做出可展示的 Web 監控介面。

## 你會做出什麼

- AGV 狀態監控 demo
- 機台狀態 dashboard
- 工廠資料 WebSocket 推播骨架
- PoC 展示與客戶需求訪談

## 建議學習方式

1. 先照 `01-quickstart.md` 跑起來。
2. 再看 `02-architecture.md` 理解每個檔案負責什麼。
3. 照 `03-step-by-step.md` 做一次完整流程。
4. 準備部署時看 `04-deployment.md`。
5. 卡住時先查 `05-common-pitfalls.md`。
6. 想改成自己的場景，看 `06-customize-for-your-use-case.md`。
7. 接真實 MQTT 資料 + LLM 班報的對照組，看 `08-real-data-and-ai-summary.md`。

## 免費與付費怎麼分

這個 repo 會公開最小可跑版本與完整操作步驟。真正適合工作坊或顧問的部分，是陪你 debug、改成你的情境、處理部署與實務安全邊界。

- 免費：可重現的 starter、教學文件、基本部署方向。
- 付費工作坊：手把手解問題、看你的程式與設定、一起改成你的使用場景。
- 企業顧問：需求訪談、PoC、部署、權限、安全與維運規劃。
