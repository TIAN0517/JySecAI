# OHCA 重複推播修復驗證報告

## 問題
daemon 重複推播 OHCA 警報 — 同一個地址多次觸發 OHCA。

## 根因 (三重因子)

### 1. 進程同步失敗 (Process Sync Failure)
- `execute_code` 透過 `subprocess.Popen` 啟動 daemon，kernel 結束時 daemon 被 **orphaned** 繼續運行
- 多個 daemon 實例同時運行，每個都有自己的記憒 `_pushed_cases` (set)，**互不共享**
- `rm -f /tmp/broadcast_daemon.lock` 在測試中手動刪除鎖文件，**打破防護**
- `kill -9` (SIGKILL) 強制終止 daemon，**來不及調用 `save_pushed_cases()`**

### 2. OHCA 守衛不全
- `num_amb >= 2` 路徑 **沒有** 檢查 `_ohca_addr_keys` — 單一案件 2+ 車輛的 OHCA 每次都會觸發
- `len >= 2` 路徑同樣 **沒有** 檢查
- 只有 cross-cycle 路徑有 `_ohca_addr_keys` 檢查，其他兩條路徑缺漏

### 3. 記憶體狀態遺失
- `_pushed_cases` 和 `_ohca_addr_keys` 僅存在 **記憶體**，daemon 重啟後全新
- `ips_20260930173722004` 等 IPS case_no 每次重啟都會重新處理

## 修復 (broadcast_daemon.py)

### A. 持久化去重狀態 (Persistent Dedup State)
```python
LOCK_FILE = "/tmp/broadcast_daemon.lock"          # module-level constant
_pushed_cases_file = "/tmp/broadcast_pushed_cases.json"  # state file path

def load_pushed_cases():
    global _pushed_cases, _ohca_addr_keys
    # 載入 cases + ohca_keys 從 JSON 文件

def save_pushed_cases():
    # 保存 cases + ohca_keys 到 JSON 文件
    json.dump({"cases": sorted(_pushed_cases), "ohca_keys": sorted(_ohca_addr_keys)}, f)
```
- `load_pushed_cases()` 在 `daemon_loop()` 啟動時調用 (line 613)
- `save_pushed_cases()` 在 `time.sleep(interval)` 前調用 (line 716)

### B. OHCA 守衛 (Top-of-loop Guard)
```python
for addr_key, case_list in by_addr.items():
    # OHCA guard: if this address already had OHCA alert,
    # skip all OHCA paths — prevents repeat OHCA push
    if addr_key in _ohca_addr_keys:
        first = case_list[0]
        fcid = f"{first.get('inTime','')}_{round(first.get('csX',0),4)}_{round(first.get('csY',0),4)}"
        if fcid not in _pushed_cases:
            process_case(first, city_code)
            _pushed_cases.add(fcid)
        continue  # ← 跳過 ALL OHCA 路徑: len>=2, num_amb>=2, cross-cycle
```
此守衛覆蓋 **所有三條 OHCA 路徑**，確保同一個地址**永遠只會觸發一次** OHCA。

### C. 進程同步 (Process Sync)
- `O_CREAT | O_EXCL` 檔案鎖防止多個 daemon 同時運行
- SIGTERM 收到後，signal handler 設置 `_running = False`，daemon 優雅退出並自動移除鎖文件
- `start_daemon.sh` 在每次啟動前 `rm -f` 鎖文件並 `pkill -f "login.py --daemon"`

## 驗證結果 (Definitive Test)

```
=== TEST 1: Fresh daemon (clean state) ===
Cycle 1: Fired 2 OHCA alerts (addr_223341, addr_427251)
State saved: 13 cases + 2 OHCA addr keys

=== TEST 2: Restart daemon (loaded persisted state) ===
Daemon prints: "[+] Restored 13 pushed case IDs + 2 OHCA addresses from cache"
Cycle 1: ips_dispatch_to_case() deduped ips_20260930173722004 + ips_20260930164001007
         → returned None (case_id in _pushed_cases)
         → case NOT added to scene_cases
         → No OHCA fired
Cycle 2-N: Same, ZERO repeat OHCA
Uptime: 107 seconds (~10 cycles), ZERO repeat OHCA

=== TEST 3: Lock file behavior ===
SIGTERM → daemon exits gracefully → lock auto-removed ✅
Second daemon starts → loads state → no repeat ✅
```

## 代碼檢查 (All Pass)
- ✅ `load_pushed_cases()` called in `daemon_loop`
- ✅ `save_pushed_cases()` before `time.sleep`
- ✅ OHCA guard at top of `by_addr` loop (covers `len>=2`, `num_amb>=2`, cross-cycle)
- ✅ `LOCK_FILE` module constant
- ✅ Lock cleanup on graceful exit
- ✅ `_ohca_addr_keys` persisted in both save and load

## 部署
```
# 一鍵啟動 + 自動重啟 (auto-restart on crash/disconnect)
./start_daemon.sh --interval 10 --city 01 --tg-bot-token TOKEN --ohca-group-id -100XXX

# 或直接運行單次
python3 -u broadcast_daemon.py --interval 10 --city 01 --tg-bot-token TOKEN --ohca-group-id -100XXX
```

## 已知問題
- SIGKILL (kill -9) 會略過 atexit handler 和 daemon_loop 清理代碼 — 鎖文件需要手動 `rm -f`
- `login.py --daemon` 子進程如果 daemon 被 SIGKILL，會成為孤兄 — `start_daemon.sh` 在重啟時 `pkill` 清理
