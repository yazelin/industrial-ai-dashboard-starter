# 工業 AI Dashboard 入門模板：完整操作流程

## 步驟

1. 先啟動 uvicorn，打開 http://127.0.0.1:8000。
2. 確認 AGV、machines、alerts 每秒更新。
3. 查看 /api/snapshot 的 JSON 形狀。
4. 把 app/data_source.py 的 simulated_snapshot 改成讀 MQTT、ROS2、Modbus 或 PLC API。
5. 保留 JSON 欄位形狀，讓前端不用大改。
6. 再加入歷史資料、告警規則與 AI summary。

## 建議紀錄

- 你使用的 Python 版本
- 啟動指令
- `.env` 裡有哪些 key 已設定；不要貼出 secret 值
- webhook / endpoint URL
- 錯誤訊息完整內容
- 你預期發生什麼、實際發生什麼

## 下一個里程碑

完成最小流程後，不要急著加功能。先找一個真實情境，讓這個 starter 解決一個很小但明確的問題。
