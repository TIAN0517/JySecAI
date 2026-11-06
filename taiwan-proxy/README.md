# 台灣掃描線路接入（JySecAI scan-traffic proxy）

讓**對授權目標的掃描流量**走台灣出口，平台其餘流量（LLM API、授權校驗、系統遙測）維持直連。

---

## 為什麼需要這個

實測結果（2026-10-02）：

| 元件 | 代理支援 |
|---|---|
| `jysec-core`（Go 主程式） | 無 —— `internal/config` 零 proxy 欄位 |
| `jysec-scanner-adapter`（Node） | 無可見設定 |
| `jysec-kali-api`（MCP-Kali-Server） | 無 —— 原始碼 grep 不到 proxy |
| `jysec-hexstrike` | 未提供 |
| `nuclei` / `ffuf` / `subfinder` | **原生支援代理參數** |

結論：平台本身沒有任何代理接入點，但底層工具本來就支援。所以走**指令層 wrapper**，完全不碰平台程式碼。

## 為什麼選這個出口

5 條 SOCKS5 全部在台灣內湖，同屬 AS148996 / SILKERA：

| 出口 | geo 庫標記 |
|---|---|
| 202.160.76.154:11085 | `proxy: true` |
| 202.160.76.155:11084 | `proxy: true` |
| 202.160.76.156:11083 | `proxy: true` |
| 202.160.76.157:11082 | `proxy: true` |
| **202.160.76.165:11081** | **`proxy: false`** ← 採用這個 |

`.165` 是唯一沒被 geo 庫標記為已知代理節點的，反爬系統不容易一眼辨識。
全部 `hosting: false`（非機房 IP），這一點對政府目標很重要。

**固定單一出口，不輪替** —— 5 個同網段的 IP 在短時間輪流打同一個站，本身就是自動化特徵。

---

## 安裝

```bash
cd /mnt/c/Users/Administrator/Desktop/JySecAI/taiwan-proxy
bash ./selftest.sh             # 14 項邏輯自測，不需要 root，不碰任何目標
sudo ./install.sh              # 安裝（不重啟服務）
sudo ./verify.sh               # 驗證（8 項檢查，不碰真實目標）
sudo ./install.sh --restart    # 確認無誤後重啟服務使設定生效
```

`selftest.sh` 已實測 14/14 通過，涵蓋：零行為改變保證、參數注入、呼叫端優先、
未啟用工具不受影響、空白/unicode 參數透傳、對照表註解解析、缺執行檔時的退出碼。

自訂代理或工具：

```bash
sudo ./install.sh --proxy socks5://202.160.76.157:11082 --tools "nuclei ffuf"
```

## 回滾

```bash
sudo ./uninstall.sh            # 移除全部設定，保留日誌
sudo ./uninstall.sh --purge    # 連日誌一起刪
sudo systemctl restart jysec-core jysec-kali-api jysec-hexstrike jysec-scanner-adapter
```

---

## 安全設計

這套東西遵循「不能讓工具變弱」的原則，**三層防護**：

1. **未設定 `JYSSECAI_SCAN_PROXY` 時是 100% 純 pass-through** —— 逐參數原樣傳遞，行為與未安裝時完全相同。`verify.sh` 的 B 項測試就是驗證這點。
2. **呼叫端已自帶代理參數時不覆蓋** —— 你手動指定 `-p` / `-x` / `-proxy` 的優先級最高。
3. **未列入對照表的工具完全不受影響** —— 對照表在 `/etc/jysecai/scan-proxy-map.conf`，一行一個工具。

最壞情況是「沒生效」（服務若用絕對路徑呼叫工具），不可能變弱或壞掉。

## 為什麼 subfinder 預設關閉

subfinder 的 `-proxy` 影響的是它對 **crt.sh / Shodan 等第三方情報源**的查詢，不是對你客戶目標的掃描。把這些查詢集中導到單一出口，反而會讓那些第三方服務看到「同一個台灣 IP 短時間大量查詢」，容易觸發速率限制或濫用封鎖。

要開啟：

```bash
sudo ./install.sh --tools "nuclei ffuf subfinder"
```

---

## 已知限制

**1. 絕對路徑呼叫不會被攔截**
如果 MCP 工具層是用 `/usr/bin/nuclei` 這種絕對路徑呼叫，wrapper 不會生效。`verify.sh` 的 F 項只能驗證 PATH 順序，無法驗證實際呼叫方式。
確認方式：跑一次掃描後檢查

```bash
sudo tail -20 /var/log/jysec-scan-proxy.log
```

有 `event=injected` 就是生效了；空的就是沒生效。

**2. 出口分集度不足**
5 個出口同屬一個 /24。對「單一目標不觸發速率限制」這個目標夠用，但對「需要大量 IP 輪替」的工作量不足。

**3. `httpx` 版本不符**
`/usr/bin/httpx` 不是 ProjectDiscovery 版（是那個做網頁截圖的 Python 工具），沒有代理選項。若需要帶代理的活站探測，需另外安裝 ProjectDiscovery httpx / naabu / katana。

---

## 檔案

```
taiwan-proxy/
├── bin/scan-proxy-wrap   wrapper 本體（依 argv[0] 判斷工具）
├── install.sh            安裝（冪等）
├── verify.sh             8 項安裝後驗證，全程不對真實目標發請求
├── uninstall.sh          完整回滾
├── selftest.sh           14 項邏輯自測（免 root，隨時可跑）
└── README.md             本檔
```

執行後新增於生產機：

```
/usr/local/bin/scan-proxy-wrap
/usr/local/bin/{nuclei,ffuf} -> scan-proxy-wrap
/etc/jysecai/scan-proxy-map.conf
/etc/systemd/system/jysec-{core,kali-api,hexstrike,scanner-adapter}.service.d/10-scan-proxy.conf
/var/log/jysec-scan-proxy.log
```
