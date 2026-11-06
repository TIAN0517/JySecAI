# 2026-10-02 JySecAI 任務恢復與交付紀錄

本次完成使用者授權的文件、只讀預覽、分析與單元測試；沒有執行資料清理、生產部署、restart、憑證輪替或歷史改寫。工作區原有的大量 staged 清理與其他修改均保留，没有提交／推送。

## P0：憑證暴露

檔案：新增 [CREDENTIAL_ROTATION_CHECKLIST.md](../../CREDENTIAL_ROTATION_CHECKLIST.md)、[加密遷移評估](config-secret-migration-assessment.md)；更新 [SECRET_EXPOSURE_REPORT.md](../../SECRET_EXPOSURE_REPORT.md)，加入 `f574d4f39` 與完整欄位表，並遮蔽報告原有的帳密／token 摘錄。`.gitignore` 加入僅針對這份無值文件的例外，避免既有 `*credential*` 規則漏掉輪替清單；秘密檔案的 ignore 規則保持。

7 組輪替操作待供應商／服務管理員執行。embedding key 是否為佔位符待擁有者確認，本次没有讀取值。`.gitignore:12` 已忽略 `config.yaml`，不需要重複補規則；檔案仍被追蹤。**`git rm --cached config.yaml` 待另行授權，尚未執行。** 加密只出設計，未遷移或修改任何值。

驗證：共用 build／vet exit 0；`internal/config` 測試通過。`config.yaml` 的 staged／unstaged diff 均為空。

## P1：資料品質 report 階段

檔案：新增 `cmd/vulnerability-data-quality/main.go`、`internal/vulnquality/{report.go,markdown.go,report_test.go,filter_contract_test.go}`、`configs/vulnerability-type-aliases.json`、[完整預覽與 ID](vulnerability-data-quality-report-2026-10-02.md)、[來源／彙總／severity／回滾分析](vulnerability-data-quality-analysis.md)。

預覽：688 筆、476 個空 target、513 筆髒類型、15 筆 target 正規化提案、13 筆明確別名對映，預計保留 100 個非空類型建議。根網址保留 `/` 並合併缺斜線的表示；非根尾斜線變更需要審閱其路由等價性。不同 port／path／query 不合併，描述式 target 保持原樣。`type`／`target` 查詢语意未改。

只讀來源副本：`/tmp/jysec-quality-report.WpHQuC/conversations.db`，SHA-256 `91ddf43f8d724579aa4a5b0a27d194410eaaddc516a997e047beaa500d66aba4`。這是工作區資料的快照，不宣稱與生產目前狀態完全一致。

`confidence.80` 的歷史來源是 AWVS 匯入器的 `Tags[0]` 誤用；匯入器已於 `3b75ed89d` 移除，現行來源沒有該邏輯。沒有重加已移除功能，也沒有把所有未知類型猜成 CWE。

現行 dashboard 告警取 open critical，副本是 12；open critical+high 是 68，全部 critical+high 是 87。58 的生產實際來源仍缺同時點 API／前端證據，不能宣稱已修正該數字。

**尚未授權或實作 `--fix`。** 回滾 transaction/journal 設計已產出，寫入／回滾工具待報告確認後實作與驗收。未改動任何 DB row；不能把合成測試當成 688 筆已清理。

驗證：共用 build／vet exit 0；`internal/database`、`internal/handler` 全套通過；`internal/vulnquality` 單元與 race 通過。測試涵蓋冪等、尾斜線、port、空值、別名、SQL NULL、實際 filter options、只讀 DB／路徑限制，以及 report output 不得覆寫 DB。

## P2：部署雜湊

檔案：新增 [部署時序／流程](deployment-hash-analysis-2026-10-02.md)。

查明先前 Codex 在 18:46 建 CGO=0，SQLite 啟動失敗後於 18:55 重建 CGO=1、18:56 替換工作區產物，19:11 再建去重版本。三次不同 hash 有明确時序；目前不能證明同一次部署中 gate 被競態繞過。18:46／18:55 建置另有未切入所建 worktree 的追溯性問題。後續流程要求獨立產物＋sidecar＋private snapshot，部署 temporary 與落地檔皆比對同一摘要。

備份 `jysec-core.bak-url-export-20261002` 的目前存在／完整性仍待管理員以文件中的 sudo 只讀指令確認。本次沒有 `/opt` 權限，不把它標記為已驗收。沒有部署。

驗證：文件分析沒有新增 runtime code；共用 build／vet exit 0。工作區 binary 仍為 SHA-256 `1ed27000c2b08ee43293d61a9344a7442864ff6c13315b10b551e98bd172f5d6`。

## P3：Embedding 404

檔案：新增 [診斷與補索引建議](embedding-404-diagnosis.md)、`internal/knowledge/embedder_endpoint_test.go`。

確認實際 SDK 將 `/embeddings` 接在 base URL 後。Gateway 擁有者仍需確認 API prefix、embedding model 與權限；没有猜實際 Gateway 路由或改設定。缺向量項目有既有 missing-index 重試路徑；4/11 是中途計數，不能證明最終恰好只剩四筆。沒有外部請求或生產補索引。

驗證：共用 build／vet exit 0；`internal/knowledge` 與 race 通過，本機合成 HTTP 測試驗證 console HTML 404、正確 API prefix 可回向量。這不是生產 Gateway 驗收。

## P4：External MCP EOF

檔案：新增 [協定與失敗證據分析](external-mcp-eof-diagnosis.md)。

區分 stdio 提早退出、Streamable HTTP、舊 SSE 與認證／代理問題。已確認本機兩個 read-only 資訊服務採 stdio，本機註冊與生產名單不同。health 200 與 tool_execution 筆數不足以證明 MCP initialize 成功或唯一根因。

五個生產註冊的非秘密 metadata、stderr／退出碼或 HTTP 回應仍缺；修正方向已列出，沒有修改設定或接通外部工具。

驗證：共用 build／vet exit 0；`internal/mcp` 全套通過。沒有新增 MCP runtime code。

## WebShell 交接

更新 [prompts/handoff-backlog.md](../../prompts/handoff-backlog.md)，標記來源碼相容需求已解決、保留 CA 與測試、記錄舊 binary 的既有相容開關，明確區分來源碼與生產生效。沒有 sudo、systemd reload/restart 或 runtime 行為修改。

已補正兩點：第三方目標仍有 MITM 與回應可信度風險；`CA_SERVER` 現行只觸發系統信任池，不實作 issuer pinning。`TestNewWebShellTransportModes` 五個子測試通過。

## 最終驗證

| 命令 | Exit code | 結果 |
|---|---:|---|
| `go build -buildvcs=false ./...` | 0 | 通過；未輸出至部署產物檔名 |
| `go vet -buildvcs=false ./...` | 0 | 通過 |
| `go test -buildvcs=false ./internal/database ./internal/handler ./internal/config ./internal/knowledge ./internal/mcp ./internal/vulnquality` | 0 | 六個套件全通過 |
| `go test -race -buildvcs=false ./internal/vulnquality ./internal/knowledge` | 0 | 通過 |
| `go test -buildvcs=false ./internal/handler -run TestNewWebShellTransportModes -count=1 -v` | 0 | 五個子測試通過 |

這次 WSL/Linux 執行没有出現交接所述的 Windows TempDir 既有失敗；沒有修改那些測試。沒有跑與此次變更無關的 logger／security 套件。

## 後續授權：編譯與部署準備

使用者後續已授權部署、停止舊核心服務並重新啟動。已使用當前工作目錄來源執行 `CGO_ENABLED=1 GOOS=linux GOARCH=amd64 go build -buildvcs=false -trimpath`，exit 0；上述六個套件再次測試通過。没有覆寫根目錄既有 `jysec-core-linux`。

可交付產物：`build/releases/core-606c37e901aa8ce5/jysec-core`，106,057,248 bytes，Linux amd64 ELF，CGO=1；旁附 `jysec-core.sha256`，`sha256sum -c` 通過。完整摘要：`606c37e901aa8ce591d4b93b20d55e0a31342bc4d368ff5c52b1ccdf18bc98aa`。該目錄在既有 `build/` ignore 範圍，不進原始碼版控。

**生產尚未部署／停止／重新啟動。** 當前工具環境的 systemctl 回報 PID 1 不是 systemd、system bus 不可用；`sudo -n true` 回報需要密碼。必須先取得正確的生產連線途徑，才能核對服務與備份並完成部署。沒有索取或記錄 sudo 密碼。此部署授權不等於 vulnerabilities `--fix` 或 Git 取消追蹤授權。
