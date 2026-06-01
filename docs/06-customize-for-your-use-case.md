# 工業 AI Dashboard 入門模板：改成你的使用場景

## 可延伸方向

- 接 MQTT：背景 task 訂閱 topic，更新最新狀態 cache。
- 接 ROS2：把 ROS topic bridge 成 dashboard JSON。
- 接 PLC：用 adapter 讀取 tag，再轉成 agvs / machines / alerts。
- 加 AI：把異常告警與歷史摘要交給 LLM 生成班報。

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
