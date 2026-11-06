# scan-runner — 指定 DNS／URL 的併發探測（跑到次數上限才停）

## 核心語意
1. 併發：固定 worker 數從佇列取件。
2. 不提前停：單一請求失敗只記錄，整輪繼續。
3. 只在預算觸底才停：`--max-requests`（次數）或 `--max-duration`（時間），先到先停，報告會寫停止原因。
4. 任務集用完但預算還有 → 進入下一輪（`--cycle`，預設開），所以「不停止」是真的不停止。

## 用法
```bash
# 單一 URL
/opt/jysecai/core/current/build/releases/scan-runner \
  --url https://target.tld/ --paths /,/api,/admin --max-requests 500 --out /tmp/scan

# 指定 DNS 解析器（多 A 記錄全掃）
... --dns target.tld --dns-server 8.8.8.8:53 --ports 80,443 --concurrency 16 \
    --max-requests 5000 --max-duration 10m --out /tmp/scan

# 走代理出口（住宅代理等）
... --proxy socks5h://user:pass@host:1080 --max-requests 200
```

## 產出 → 入庫
```bash
records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload /tmp/scan/payload_asset.json
records-ingest --db /var/lib/jysecai/core/extracted_records.db --payload /tmp/scan/payload_endpoints.json
```
- `payload_asset.json` → asset 型別（主機／埠／協定／服務／標題）
- `payload_endpoints.json` → generic 型別（主機／路徑／狀態／位元組數）
- `scan_raw.jsonl` → 每一次嘗試一行（成功與失敗都記）
- `scan_report.md` → 摘要與停止原因；`SHA256SUMS` → 雜湊鏈

## 邊界
只做 HTTP GET 探測，不送任何寫入請求；單一目標不掃 exe 後綴路徑；逾時與次數上限預設都有。
