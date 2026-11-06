# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

JySecAI is a single-service AI-native security operations platform in Go (module `jysecai`): a Gin HTTP server, static SPA frontend, SQLite persistence, Eino-based agent orchestration, MCP tooling, and optional high-risk C2 (`internal/c2`) and WebShell subsystems. It is strictly for authorized security operations — many subsystems execute commands by design.

Deeper docs: `docs/en-US/architecture.md`, `docs/en-US/developer-guide.md`, `docs/en-US/testing.md`.

## Live runtime (do not start a second copy)

The site users actually open is the Kali WSL service `jysec-core`, not a Windows `jysecai.exe`.

- Binary: `/opt/jysecai/core/current/jysec-core` (release `20260909-full-feature`)
- Config: `/var/lib/jysecai/core/config.yaml`
- Database: `/var/lib/jysecai/core/conversations.db` (the vulnerability set, POC drafts, conversations)
- Listen: `127.0.0.1:9898` inside WSL — the port comes from `server.port` in `/var/lib/jysecai/core/config.yaml`; never hardcode it in scripts, systemd units, or portproxy rules. **The port has moved twice (8080 → 18082 → 9898)**; as of 2026-11-01 it is `9898`. The public TLS front door is `jysec-edge` on WSL `443`/`18443` (self-signed cert CN `jysecai.utown.cc.cd` for the `utown.cc.cd` zone, Cloudflare Origin CA for the `gofun.cc.cd` zone), behind Cloudflare.
- Windows portproxy (current, verified 2026-11-02): `52.128.238.210:80` → WSL `:18080`, `52.128.238.210:443` → WSL `:443`, `52.128.238.210:8443` → WSL `:8443`, `127.0.0.1:8855` and `[::1]:8855` → the core, **`127.0.0.1:9999` and `[::1]:9999` → the core (canonical console alias, 2026-11-02)**, `172.31.32.1:6689`, `127.0.0.1:11434`, `0.0.0.0:8765` → `:9090`, `0.0.0.0:9444` → `:9777`. `C:\ProgramData\jysecai\core-port.ps1` resolves the core port from the WSL config; `C:\ProgramData\jysecai\restore-portproxy.cmd` re-materialises these at boot.
- **Trap #7 (2026-11-02): the console alias is `:9999`, and `:8080` is gone for good.** 8080 was the single biggest source of churn on this host — the tunnel origin used to be `http://localhost:8080`, and every other agent that touched the stack assumed the console lived there, re-added the portproxy rule, moved the tunnel origin back and broke the public site (visible in `jysecai/tmp/remove_8080.ps1` and `all/raw/ui-analysis/_compact*.ps1` around 00:57). The tunnel ingress is now `http://localhost:9898`, `restore-portproxy.cmd` keeps **delete-only** lines for 8080 (v4+v6) so a stale rule can never come back, and the loopback alias the platform hands out is **`:9999`** — `ensure-stack.ps1` probes it as `win-9999`, so a broken alias is caught in the health check instead of surfacing as a 502 on the public domain. **Do not re-add an 8080 rule and do not point the tunnel origin at 8080.**
- **`:8080` was retired on 2026-11-02 — one name for one thing.** The loopback `127.0.0.1:8080` / `[::1]:8080` portproxy aliases existed only because the Cloudflare tunnel `jysec-vps3` ingress pointed at `http://localhost:8080` (a second name for the same core that `localhost:9898` already reached via `wslrelay`). The tunnel ingress is now `http://localhost:9898`, the two portproxy rules are deleted, and `restore-portproxy.cmd` only keeps the `delete` lines so they cannot come back. `ensure-stack.ps1` probes the core port for the tunnel origin instead of `8080` — otherwise the watchdog reported a false `down=tunnel-origin-8080` every cycle. The `jysec-vps3` ingress (Cloudflare-managed, `cert.pem` API) is: `jysecai.utown.cc.cd` → `http://localhost:9898`, `jysecai.gofun.cc.cd` → `http://localhost:9898`, `console.utown.cc.cd` → `http://localhost:9090`, catch-all → `http_status:404`.
- **The `:8443` entry is script-managed since 2026-11-02** — it used to exist only as a hand-made rule that no script re-created, so it went stale and died silently whenever WSL changed IP (the rules bind a specific WSL address, and WSL2 hands out a new one on every distro restart). `restore-portproxy.cmd` now creates it next to `:80`/`:443` and also rewrites `C:\ProgramData\jysecai\wsl-ip.txt` on every run; that file is a live value, not a source of truth. Two scheduled tasks drive the script — `JySecAI portproxy restore` (boot + every 5 min) and `JySecAI-PortProxy-Fix` (boot). Keep the file ASCII-only: cmd.exe parses non-ASCII comment bytes as commands.
- **The public direct-to-core rules were removed on 2026-11-01**: `52.128.238.210:8080 → core` and `0.0.0.0:6688 → core` exposed the core straight to the internet and bypassed the `jysec-edge` login gate. `restore-portproxy.cmd` no longer re-creates them (only the `delete` lines remain, to clean up stale rules) and the blanket inbound firewall rule "JySecAI HTTP edge 8080" is disabled. Public access must go through `80/443 → jysec-edge → core`.
- Trap #1 (recurred 2026-11-01, same symptom as the 2026-10-24 incident): the core moved to `9898` but **half the stack still said `8080`**. `nginx-gateway.conf` proxied `/api/` to the dead `8080`, so the origin answered **502** — Cloudflare proxied and then cached that 502 (error-cache TTL 300 s), which is why `https://jysecai.utown.cc.cd/api/...` stayed broken for ~15 minutes even after the upstream was fixed. At the same time `jysec-mcp-watchdog` probed `http://127.0.0.1:8080/`, failed three times in a row, and ran `systemctl restart jysec-core` roughly every 90 seconds — each cycle tearing down every external MCP server (Pentester-MCP, Kali, HexStrike, dragon-v, vuln-intel, reverse-shell, redteam). That is what "the scanner did not come up with full features" looks like. Both scripts now derive the port from `server.port`; treat a 502 that does not reproduce locally as a cached edge error, not a live upstream fault.
- Trap #2 (historical): the **user-level** systemd unit `jysec-8080-proxy.service` (a Python TCP bridge) squatted `127.0.0.1:8080` and `jysec-stack-guard.service` re-pulled it via `Wants=`, deadlocking the stack. Both units **no longer exist** (2026-11-01) — do not look for them, and do not recreate a port bridge on any port the core might use. Before touching a port, check who owns the socket: `ss -ltnp | grep :9898`.
- Trap #3: `429` is overloaded. A provider returning `429` with a *quota/plan exhaustion* body (e.g. MiniMax `已达到 Token Plan 用量上限`) is **not** a transient rate limit and must not be retried — `internal/multiagent/eino_transient_retry.go` now separates the two via `isEinoQuotaExhaustedError`. Before treating any 429 as retryable, check the body.
- Trap #4 (2026-11-01): **editing `config.yaml` does not change the running core.** The config is read once at startup, so the console kept showing the *old* 受控端點 (`https://97y.me/hjnej`) for ~36 minutes after the file was changed to `https://97y.me/tjneJ` (mtime 23:13:25, core still the 22:50 process). Any config edit — `server.port`, `redirect.urls`, model providers — needs `systemctl restart jysec-core` to take effect, and the UI/API will otherwise silently serve the stale value. Check `stat -c '%y' /var/lib/jysecai/core/config.yaml` against `systemctl show jysec-core -p ExecMainStartTimestamp` before believing what the screen shows.
- Edge logs: `/var/log/jysecai-edge-access.log` and `/var/log/jysecai-edge-error.log` are rotated by `/etc/logrotate.d/jysecai-edge` (daily, 50 M, 7 generations, copytruncate). Without that rule the access log grew to 303 MB, mostly unknown-Host scanner traffic logged as `444`.
- **`webapp.gofun.cc.cd` is not served by the tunnel and is ~19 s slow** (measured 2026-11-02): the tunnel `jysec-vps3` (`c39d1aa3-58b2-43df-9fa9-62d6b0a420ee`, remotely managed, `cloudflared tunnel run --token-file C:\ProgramData\cloudflared\token`) has ingress for `jysecai.utown.cc.cd`, `jysecai.gofun.cc.cd` and `console.utown.cc.cd` only — `webapp.gofun.cc.cd` is absent, so it falls through to that zone's own proxied A record, and that origin path takes ~19.5 s while the same hostname answered by this edge takes 5–11 ms. `jysecai.gofun.cc.cd` returns **530** because `gofun.cc.cd` is not a zone in this Cloudflare account (only `utown.cc.cd` is), so cloudflared cannot serve it at all. The login gate itself is healthy and does apply through the CDN (`/governance/` → 302 back to `/` for the gofun host, 200 for `jysecai.utown.cc.cd`). Fixing the latency needs `gofun.cc.cd` zone access: point `webapp.gofun.cc.cd` at `52.128.238.210`, or move that zone into this account so the tunnel can serve it.
- **Disk rescue procedure (2026-11-01, verified)**: the WSL ext4 vhdx is `C:\Users\Administrator\AppData\Local\wsl\{4bf9c34b-d08e-4d83-b86c-5d71da06b419}\ext4.vhdx`. It grew to **464 GB on C:** while the guest filesystem only used ~112 GB, which starved the C: drive (894 GB total → 16 GB free) and made the whole platform unbootable. `fstrim` **does** work on this host (`fstrim -v /` reports ~875 GiB trimmed on `/dev/sdd`); the earlier note that `blockdev --getdiscardgranularity /dev/sdd` returned `n/a` was a util-linux version artifact — that subcommand does not exist here. Trim only marks blocks free though; the host file shrinks only once the vhdx is sparse. The working sequence is:
  1. `wsl --shutdown` (all services come back automatically in ~30 s once restarted).
  2. `wsl --manage kali-linux --set-sparse false --allow-unsafe` — turns the sparse flag off, which only allocates the existing holes (~13 GB), *not* the whole file.
  3. `diskpart` → `select vdisk file="<vhdx>"` → `compact vdisk` — this **rejects sparse files** ("must not be sparse"), which is why step 2 must come first.
  4. Restart WSL and let the units come back.
  Result on 2026-11-01: vhdx 464.5 GB → **165.1 GB**, C: free 16 GB → **365 GB**. `wsl --manage --resize` cannot shrink (fails `0xc03a0001`) and `Optimize-VHD` is unavailable (no Hyper-V module in this nested environment), so diskpart is the only path.
- **Leave the sparse flag ON** (2026-11-01): `wsl --manage kali-linux --set-sparse true --allow-unsafe` must be the **last** step, after any diskpart compaction — `compact vdisk` rejects sparse files ("must not be sparse"), so a later rescue runs `set-sparse false` → `compact vdisk` → `set-sparse true` again. With the flag on, blocks freed inside WSL return to the host automatically; with it off (dense) deleted files silently stay allocated on C: and the disk slowly refills — that is the recurrence this note exists to prevent.
- **`wsl --shutdown` is defeated by the scheduled tasks** (2026-11-01): `JySecAI Kali WSL Autostart` (holds `sleep infinity`) and `JySecAI-Healthcheck` / `JySecAI-EnsureStack` (call `wsl.exe -d kali-linux`, which boots the distro) re-kick WSL seconds after a shutdown, so the vhdx stays open and `--manage` fails with `WSL_E_DISTRO_NOT_STOPPED`. Disable those tasks for the window. A reusable script covering the whole cycle (pause tasks → `wsl --shutdown` → `set-sparse true` → re-enable tasks → boot → wait for `core=200` → verify 8855/9898/public 443) lives at `C:\ProgramData\jysecai\reclaim-wsl-space.ps1`; expect ~2-4 min of downtime per run, and the platform self-heals via the same healthcheck.
- **Where the C: space actually goes** (measured 2026-11-01): the vhdx (464 GB), `C:\pagefile.sys` (109 GB, system-managed, shrinks on its own), `C:\Users\Administrator\Videos\wwi.ru\*.zip` (82 GB and growing — downloaded by another assistant), Docker's `docker_data.vhdx` (15 GB), and Claude's `claudevm.bundle` (9 GB). Logs are negligible: `/var/log` is 37 MB and Windows log files are < 1 MB, so "delete all logs" reclaims ~0.5 GB and is never the fix.
- **`Videos\wwi.ru\*.zip` is engagement raw material — do not delete it** (verified 2026-11-01): 79 archives (42 main + 37 `*_sent`), 82 GB, collected 20:10–20:45 for the wwi.ru / Worldwide-Invest booter and DDoS-secrets work (same corpus as `Desktop\all\06_Icepick_DHS資料提取\raw\ddosecrets\mirror\`). The `*_sent` archives are **not** duplicates of their main archive — zip entry lists share **zero** names (e.g. `v-schuka` 22,178 vs 5,435 entries, 0 common; `smirnova` 13,781 vs 13,242, 0 common) and no two files in the folder share a byte size, so there is nothing safe to reclaim from them. Space was recovered instead from the vhdx; keep these unless the engagement owner says otherwise.
- **Leave `pagefile.sys` system-managed** (verified 2026-11-01): RAM is 128 GB, total commit peaked at 65.4 GB, pagefile usage is 9.7 GB now and 54.5 GB at peak, and Windows shrinks a system-managed pagefile on its own. A fixed cap (24/40 GB) would sit below the observed peak and could turn a memory burst into a commit failure, so no cap is set. Re-evaluate only if total commit exceeds ~150 GB or C: free drops below 100 GB again.


## Windows 開機自癒鏈路（2026-11-02 修好並實測）

「wsl 沒啟動網站就啟動不了」＝開機後 WSL 沒起來、或 portproxy 是空的（綁死舊 IP），對外一律 502。四支 Windows 排程構成自癒鏈，**全部必須是 Administrator + S4U**：

| 排程 | 身分/登入 | 觸發器 | 動作 |
|---|---|---|---|
| `JySecAI Kali WSL Autostart` | Administrator / S4U | Logon + Boot (延遲 PT45S) | `wsl.exe ... /bin/sleep infinity` 撐住 distro |
| `JySecAI portproxy restore` | Administrator / S4U | Boot + 每 PT5M | `restore-portproxy.cmd` 重materialise portproxy |
| `JySecAI-EnsureStack` | Administrator / S4U | Boot (PT45S) | `ensure-stack.ps1` 拉起 WSL units |
| `JySecAI-Healthcheck` | Administrator / S4U | 每 PT1M | `ensure-stack.cmd` → 健康檢查 + 拉 unit + 開 WSL |

- **絕對不要用 SYSTEM 或 Interactive**：WSL distro 是註冊在 Administrator 的 HKCU，SYSTEM 看不到它（`wsl.exe` 直接失敗 → portproxy 沒建立 → 全站 502）；Interactive 只在有人登入時才觸發。S4U 能在未登入時執行。
- **portproxy 綁死 WSL IP 是最大單點風險**：WSL2 每次重開 IP 可能改變。`restore-portproxy.cmd` 已改為「等 IP 出現（最多 40 次 × 3 秒）→ 寫入前再讀一次 IP → 才寫規則」，且 sleep 用 `ping -n 4 127.0.0.1` 而非 `timeout`（`timeout` 在 stdin 被重導向時會失敗，正是排程任務情境）。
- **Trap #5（2026-11-02）**：`JySecAI Kali WSL Autostart` 的 `ExecutionTimeLimit` 原本是 `PT10M`，Task Scheduler 會在 10 分鐘後殺掉 `sleep infinity`（`LastTaskResult=3221225786` = `0xC000013A` 就是被強制終止的簽章）。已改成 `PT0S`（無上限）。**任何跑長駐 `sleep`/`while` 的排程都要設 `PT0S`**，否則「撐住服務」只撐 10 分鐘。
- **Trap #6（2026-11-02）**：`ensure-stack.ps1` 裡**沒有任何 `netsh`**，也就是健康檢查只會回報 portproxy 遺失、**不會修**；而 `JySecAI portproxy restore` 原本只有 BootTrigger → 開機那次若失敗，之後完全不會自癒。已加 **PT5M 重複觸發器**，讓 portproxy 連同 WSL IP 一起持續自癒（該腳本第一次 `wsl.exe ... hostname -I` 本身也會把 distro 叫起來）。
- 實測（2026-11-02 冷開機模擬：清空 portproxy + `wsl --shutdown` + 只觸發開機類排程，全程只從 Windows 側用 curl 探測）：**+74 秒** 本地 `127.0.0.1:8855` 與 `https://jysecai.utown.cc.cd/` 同時回到 200，portproxy 全部用當下的 WSL IP 重建；健康日誌 `00:32:09 ALERT down=listen-443,listen-80` → `00:33:19 WSL units pulled up`。（更早一次只做 `wsl --shutdown` 的測試是 +65 秒。）腳本位置：`C:\ProgramData\jysecai\fix-wsl-startup-chain.ps1`（身分/觸發器）、`fix-wsl-resilience.ps1`（PT0S + PT5M 自癒）、`restore-portproxy.cmd`、`ensure-stack.ps1`、健康日誌 `C:\ProgramData\jysecai\jysec-health.log`。
- **誰能把 WSL 殺掉（2026-11-02 實查 → 已結案）**：`wsl --shutdown` / `wsl --terminate` 會讓 WSL 自己的 init 發 `systemctl poweroff`，日誌特徵是 `systemd-logind: poweroff requested from client PID N ('systemctl') (unit init.scope)` ＋ `p9io.cpp:258 (AcceptAsync)`，再用 `journalctl --list-boots` 看 boot ID 切分。**已確認所有登錄的排程與磁碟上的腳本都不含這個呼叫**；那幾次關機（2026-11-02 的 00:09:16、00:10:35、00:11:58、00:12:39）**全部來自共享工作區裡另一個 agent session 的磁碟回收腳本**——`Desktop\all\raw\ui-analysis\` 底下的 `_compact2.ps1`、`_compact_vhdx.ps1`、`_enable_sparse.ps1`、`_enable_sparse2.ps1`、`_resize_or_dense.ps1`、`_sparse_reclaim_test.ps1` 每支都呼叫 `wsl.exe --shutdown`。不是排程、不是隱藏常駐程式。**任何 agent 要壓 vhdx 前，先確認沒有同類腳本同時在跑**，否則會互相把平台踢下线。
- **Console 帳號密碼是帶外重設的，不要從 DB 反推**（2026-11-02）：`admin` / `bossjy` 的 `rbac_users.password_hash` 由外部直接寫入 `/var/lib/jysecai/core/conversations.db`；`internal/database/rbac.go:1293` 會在改雜湊時一併 bump `updated_at`，所以 **`updated_at` 變動 = 有人重設過密碼，不是有人登入**。兩件實測事實：Python `bcrypt.gensalt(rounds=10, prefix=b"2a"|b"2b")` 產生的雜湊 **兩種前綴 Go 端都能驗證通過**（線上實測登入 200；「Go 會拒絕 `$2a$`」的說法是錯的，不要照抄）。另外 `audit.auth_failure_cooldown_seconds: 60` 代表連續幾次密碼錯誤後 `/api/auth/login` 會回 **429** 而不是 401，持續一分鐘才恢復——測試時別把自己的正常登入一起鎖掉。


## Scope Registry（授權範圍登記，2026-11-02）

平台端（Go）現在有**唯一授權權威**：授權不再是那份 Python 端靜態 JSON，而是資料庫裡的三張表（`scope_targets` 常駐集／`scope_grants` 授權券／`scope_denials` 拒絕記憶）。判定引擎在 `internal/scope`，持久化在 `internal/database/scope.go`，操作手冊見 `docs/zh-CN/scope-registry.md`（英文版 `docs/en-US/scope-registry.md`）。

- **`action_classes` 空陣列 ≠ 全部類別**：空陣列只代表四個一般類別（`local_analysis` / `offline_replay` / `harmless_request` / `db_read_extract`）。`credential_enum` / `bulk_scan` / `arbitrary` 必須**明確列出**；`destructive` / `real_transaction` **任何 scope 都解鎖不了**。工具沒宣告 `action_class` 一律視為 `arbitrary`（最嚴格）。
- **禁區永遠優先**：`internal/forbidden`（119／EPCR／消防）命中的目標直接判拒絕，**不列入未覆蓋清單**——即使 `scope_targets` 明確涵蓋、**即使操作者在卡片上按了批准**。不要為了「讓案子能跑」去放寬這條。
- **`scope.enforcement` 預設 `off`**（`off` / `audit` / `enforce`）。registry 是空的就切 `enforce` 會讓每次碰網路的工具呼叫都跳卡片，平台等於被鎖死——正確順序是 `audit` 看缺口 → 匯入授權 → 才切 `enforce`。**改 `config.yaml` 必須 `systemctl restart jysec-core`**（設定只讀一次，見上方 Trap #4）。
- **「抽不到目標」不等於「沒有目標」**：`scope.ExtractTargets` 回傳的 `arbitrary=true` 代表目標藏在指令裡（沒有目標參數、沒有 `-l` 清單檔、沒有 stdin）。此時一律要求操作者逐次宣告目標清單，**沒宣告就不准批准**。目標解析有三個來源：目標參數本身、`additional_args` 的 `-l <file>`（要讀檔展開）、工具的 stdin。
- **`internal/scope` 刻意不 import `internal/database`**（避免 import cycle，也讓它能單獨測試）。兩邊各自寫 SQL，**表名／欄位名就是契約**，改一邊就要同步改另一邊，否則 scope 端會靜默讀不到資料。
- **攔截點 A 在 handler 的 Eino 攔截函式**（`internal/handler` 的 `interceptHITLForEinoTool`）——那是所有 Eino 工具呼叫的單一漏斗。**人工審批受會話開關控制，scope gate 不受**：授權層與人機協同層是分開的，不要把 scope 判定塞進 `shouldInterrupt` 的開關裡。
- **批准順序有競態**：批准時必須**先寫 registry、再原地續跑**。順序反了，續跑時攔截點 B（executor 層兜底，fail closed）會查不到授權而拒絕執行。
- **決策詞彙只對 `scope_extension` 生效**：`approve_permanent` / `approve_once` / `approve_conditional` / `reject`。既有 `approval` / `review_edit` 兩種 mode **仍只接受 `approve` / `reject`**，不要放寬（那條路徑線上正在用）。
- **前端兩處不能漏**：`web/static/js/scope-extension.js` 是獨立的卡片模組；`hitl.js` 的 `hitlModeNormalize` 必須保留 `scope_extension`，否則 mode 會被降級成 `off`（卡片畫不出來、決策送不出去）。前端送出要帶 `scopeConditions` 與 `scopeTargets` 兩個欄位。
- **匯入 CLI 是 `cmd/scopeimport`**，冪等鍵＝`owner` + `target_type` + `target_value`，可重複執行；**禁區目標會被跳過並警告**。先 `--dry-run` 看分類（`*.` 開頭 → wildcard，其餘 → host）再真的匯入。
- **YAML 的 `off`／`on` 是跨語言地雷**：Go 端用 `gopkg.in/yaml.v3`，解進 `string` 欄位時會拿到**原始字串** `"off"`（不報錯）；但 Python 的 PyYAML 走 YAML 1.1，會把 `off` 解成**布林 `False`**。同一份 `config.yaml` 兩邊讀到的值因此可能不同。**任何布林語意的設定值一律加引號**（`enforcement: "off"`），別讓兩邊各自解讀。

`data/conversations.db` in this checkout is not production. It was a smaller divergent copy and has been moved to `C:\ProgramData\jysecai\quarantine-windows-split-20261021\`. Do not recreate it, do not point a server at it, and do not deploy this tree's binary over WSL unless the user explicitly asks for a production release. Editing Go, web, or `config.yaml` here does not change the running site until that release is deployed.

## Commands

```bash
# Run dev server (frontend is static — JS/CSS/template changes only need a browser refresh)
go run ./cmd/server --config config.yaml          # add --https to match run.sh defaults

# Build (CGO is required: mattn/go-sqlite3; production Linux binary uses CGO_ENABLED=1)
go build -o jysecai ./cmd/server

# Vet + tests (CI deliberately runs the WHOLE tree, not one package)
go vet ./...
go test ./...
go test -race ./internal/handler/... ./internal/app/... ./internal/mcp/...

# Single package / single test
go test ./internal/handler
go test ./internal/c2 -run TestValidateBeaconHost -v
```

- If module downloads time out: `go env -w GOPROXY=https://goproxy.cn,direct` (see go.mod).
- CI (`.github/workflows/linux-build.yml`): govet → build → full test → race → gosec/govulncheck/staticcheck (report-only) → **authorization-boundaries job (blocking)**.
- After touching security-sensitive code (RBAC, WebShell, C2 templates, MCP config masking, CSV export, outbound URL/IP validation), run the `authorization-boundaries` job's `go test -run '...'` expression locally — that job, not gosec, is what blocks merges. gosec reports are noisy on C2/WebShell code by design.
- Pre-commit hooks (`.githooks/`, `.pre-commit-config.yaml`) block secret-looking filenames/content and check TLS-verify settings (`harden.py`). Never bypass with `--no-verify`; fix the finding instead.

## Architecture

Big picture (`docs/en-US/architecture.md` has the mermaid diagram):

- **Entry & wiring**: `cmd/server/main.go` → `internal/app.New()` (`internal/app/app.go`) constructs everything and `setupRoutes` wires Gin routes. This file is the map of the whole service.
- **Agent chat path** (`/api/eino-agent/stream`): auth middleware → `internal/handler/agent.go` → Eino runner (`internal/multiagent/`) → tool calls via MCP (`internal/mcp/`, `internal/einomcp/`) → **HITL approval gate sits before tool execution** (`internal/hitl/`) → shell/command execution boundary (`internal/security/`) → results persisted to SQLite → SSE stream to browser. A failure can live in any of these layers.
- **Config hot-apply**: `internal/handler/config.go` applies config changes at runtime across model, KB, C2, robot, and MCP — no restart. Changes there need regression tests across all apply paths.
- **Tools** come in two flavors: declarative YAML command tools in `tools/*.yaml` (~97, preferred for new tools) and built-in Go tools registered in `internal/app/` (e.g., `registerWebshellTools`) when internal state or structured integration is needed.
- **Multi-agent** prompts/orchestration live in `agents/*.md` (orchestrator, plan-execute, supervisor modes) executed by `internal/multiagent/` (streaming, retry, summarization, middleware).
- **C2** (`internal/c2/`): TCP/HTTP/WebSocket listeners, encrypted beacon templates (embedded via `payload_templates/`), HITL context, result security. High test coverage — keep it that way.
- **Database** (`internal/database/`): SQLite with WAL; schema migrations must stay backward-compatible with old data files.
- `internal/handler/` is very large (~50k lines; `openapi.go` alone is 6.4k and serves `/api/openapi/spec`).

### Adding a business module

Per `docs/en-US/developer-guide.md`, a module is not "just a handler". The project's own checklist: data model + SQLite migration, handler, audit logging, monitor state for long-running work, MCP exposure decision, HITL boundary for risky tools, OpenAPI spec update, frontend (incl. i18n), tests, docs. Missing one usually becomes a later usability or safety bug.

### Long-running work convention

Anything slow (scan, indexing, batch, C2, external call) must answer: cancellable? progress queryable? retryable? where are results stored? does state survive refresh? does it block the HTTP request? If not solvable inline, use task tables, event streams, or monitor state — never block the HTTP request.

## Conventions

- **Bilingual everything**: docs exist as `docs/en-US/` + `docs/zh-CN/` pairs (README.md + README_CN.md too) — update both sides. Frontend i18n: `web/static/i18n/zh-CN.json` + `en-US.json` must be updated together; never hardcode new visible UI text.
- **Error responses**: stable JSON `{"error": "machine_readable_code", "message": "human-readable explanation"}`.
- Code comments are commonly written in Chinese (mixed simplified/traditional); match the surrounding style.
- Tool roles are named YAML files in `roles/` (Chinese filenames); skills in `skills/` follow the standard Agent Skill layout.

## Repo safety notes

- `.gitignore` intentionally excludes `config.yaml`, `data/`, `*.db`, and evidence/archive dirs — the working tree contains real credentials and pentest artifacts. Never `git add -f` these, and don't "clean up" untracked root artifacts (evidence/, fofa_*.py, etc.) — they are active working files.
- Remotes: `origin` = TIAN0517/JySecAI (push target); `lstjks` = JyscanAiI (backup branches); `boss` = bossjyaisce. Pushes to `origin` use the `vast_ed25519` key via `core.sshCommand` (already configured).
- `go.mod` says `go 1.25.0`; CI uses Go 1.27.x. Either works locally.
