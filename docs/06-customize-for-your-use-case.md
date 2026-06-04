# 工業 AI Dashboard 入門模板：改成你的使用場景

## 可延伸方向

> 接 MQTT 與 LLM 班報**已內建為後半段對照組**（見 `docs/08-real-data-and-ai-summary.md`）：`SOURCE_BACKEND=mqtt`、`AI_SUMMARY=llm` 即可切換，不用自己重寫。本節列的是再往外延伸的方向。

- 接 ROS2：把 ROS topic bridge 成 dashboard JSON（沿用後半段「換資料源」的做法）。
- 接 PLC / Modbus：用 adapter 讀取 tag，再轉成 agvs / machines / alerts。
- hybrid 摘要：把規則式 + LLM 合併排序（規則式當 fallback）。

## 改造原則

- 一次只改一個層次：先改資料來源，再改 UI，再改部署。
- 先保留原本可跑的範例，另開 branch 做實驗。
- 每加一個外部服務，就加一個健康檢查或 smoke test。
- 先做 PoC，再決定要不要產品化。

## 適合拿來做課程 / 工作坊的題目

- 從零跑起這個 starter。
- 改成自己的真實場景。
- 加入權限、部署與監控。
- 現場 debug 學員遇到的問題。
