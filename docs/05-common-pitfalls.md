# 工業 AI Dashboard 入門模板：常見問題與踩雷清單

## 常見坑

- 工業現場資料通常不乾淨，先定義穩定 JSON schema 比先做漂亮 UI 更重要。
- WebSocket 斷線重連、權限、網路隔離是正式環境必補項。
- Modbus / PLC / ROS2 連線要避免阻塞 event loop，可用背景任務或獨立 adapter。
- Dashboard demo 不等於上線監控，正式版要有 logging、告警與資料保存。
- 現場網路可能不能直接對外，部署要考慮內網、VPN 或 edge gateway。

## Debug 順序

1. 先確認服務有沒有啟動。
2. 再確認 endpoint / webhook URL 是否正確。
3. 檢查環境變數是否有載入。
4. 用 echo / fake provider 排除 AI 服務問題。
5. 查看完整錯誤訊息，不要只看最後一行。
6. 把問題縮到最小可重現案例。

## 問別人前準備

- repo / branch
- 啟動指令
- 完整錯誤訊息
- 你已經檢查過哪些設定
- secret 請遮掉，不要直接貼 token
