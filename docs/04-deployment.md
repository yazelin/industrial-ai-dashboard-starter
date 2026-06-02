# 工業 AI Dashboard 入門模板：部署筆記

## 部署前檢查

- 本機流程已經跑通（`/api/snapshot` 有回 JSON、儀表板每秒更新）。
- README 的啟動指令與實際程式一致。
- 確認 `requirements.txt` 已被部署平台安裝。
- 這個 starter 本身沒有 `.env`、沒有 secret、沒有 webhook，也沒有 `/health` endpoint，所以這幾項先不用煩惱。等你照 `03-step-by-step.md` 接了真實資料來源（可能帶 API key 或內網位址），再回頭把這些秘密放進部署平台的 secrets，不要 commit 進 repo。

## 啟動指令

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 常見部署選項

- Render / Railway / Fly.io：適合快速 demo。
- VPS + Docker / systemd：適合長期自管。
- 公司內網主機：適合企業內部工具，但要處理網路與權限。
- NAS / edge gateway：適合工業或內部自動化場景。

## 部署後驗證

```bash
curl http://127.0.0.1:8000/api/snapshot
```

本機驗證的真實輸出可參考 `01-quickstart.md` 步驟 4。接著再測真正的業務流程，不要只看服務有沒有啟動。

## 實務提醒

部署不是最後一步。正式使用前至少要補：log、錯誤告警、權限控管、備份策略、secret rotation，以及基本監控。
