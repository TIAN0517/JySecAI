# 部署雜湊時序與後續流程

日期：2026-10-02。這次只查工作區與既有 Codex 執行紀錄，沒有部署、重新啟動服务或讀取需 sudo 的生產檔案。

## 查明的時序（Asia/Taipei）

| 時間 | 證據與事件 | 結果 |
|---|---|---|
| 18:46:30 | 先前 Codex 執行 `CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -o .../jysec-core-linux ./cmd/server` 完成 | SHA-256 `98c2e8b638fa3ac469798dd698dca8f58605ffde5d8dbfba8195a176ca014372` |
| 18:51–18:54 | 既有 session 保存的服務日誌 | 明確失敗：`Binary was compiled with 'CGO_ENABLED=0', go-sqlite3 requires cgo to work. This is a stub` |
| 18:55:38 | 同一 Codex session 改建 `CGO_ENABLED=1 ... -o jysec-core-linux.cgo` | SHA-256 `cd5683d9197bfe8f921d8b3de1d4726e86b23bbb7faa959a82f4a99b25c205da` |
| 18:56:00 | Codex 執行 `install ... jysec-core-linux.new`、`mv ... jysec-core-linux` | 明確覆換工作區原本的輸出檔 |
| 約 19:00 | 使用者回傳的第二次部署輸出 | `/opt` 為 cd5683…，服務 active、HTTP 200 |
| 19:11:54 | Codex 在 `/tmp/jysecai-dedupe-204a3c24` 以 CGO=1 建置去重版本，仍輸出至同一工作區檔名 | SHA-256 `1ed27000c2b08ee43293d61a9344a7442864ff6c13315b10b551e98bd172f5d6` |

目前工作區 `jysec-core-linux`：106,174,704 bytes，mtime 19:11:53，雜湊為上表最後一筆。本次驗證用 `go build -buildvcs=false ./...`，沒有 `-o`，不覆寫該檔。

來源：`/home/bossjy/.codex/sessions/2026/10/02/rollout-2026-10-02T05-28-08-01a0f95e-16e8-7100-a359-48e2c56f8417.jsonl`；建置 execution IDs 分別為 `exec-24e4aa56-d84f-4d40-9bdf-9997d7c976ee`、`exec-56011f7d-20c0-4764-8d3f-88f6a7f47b70`、`exec-97821e11-2559-422f-b316-a1080fcfd076`。沒有把整份私有 session 搬進 repo。

## 結論與需更正的推論

確實是先前 Codex／建置工具重建了本機檔案；第一次是修正 CGO 建置失敗，第二次是去重功能建置。這不是服務端自行編譯。**比較 18:46 的第一次驗證值與約 19:00 的第二次部署值，不能證明同一次部署的 hash gate 被競態繞過**：中間有失敗、回滾與明確 CGO 重建，而且第二次指令另核對 cd5683…。

原流程仍有可重現的設計缺口：先 hash 可變動的 `jysec-core-linux` 路徑，再由 `install` 重新開啟同一路徑；兩者之間若有建置覆寫，檢查與安裝就可能取得不同內容。必須把驗證綁定到部署快照，而非長期可變的工作區檔名。

另有建置可追溯性缺口：18:46／18:55 指令雖建立指定 commit 的 worktree，`go build` 的 cwd 仍是原工作目錄，沒有切入 worktree。因此不能僅憑命令中的 `commit=7bc3a6f4a...` 宣称產物就是該 commit。19:11 的 cwd 則確實在去重 worktree，且有 HEAD 檢查。

## 可審閱的建置流程（未执行）

建置必須進入已確認且無未提交變更的來源目錄。禁止與部署共用 root 的固定輸出檔名；以新目錄保存完整的一次產物。

```bash
set -euo pipefail
# 在已確認的來源 worktree 裡執行；先記錄 commit 與 dirty 狀態。
release_dir=$(mktemp -d /tmp/jysec-release.XXXXXX)
CGO_ENABLED=1 GOOS=linux GOARCH=amd64 \
  go build -buildvcs=false -trimpath -o "$release_dir/jysec-core" ./cmd/server
(cd "$release_dir" && sha256sum jysec-core > jysec-core.sha256)
go version -m "$release_dir/jysec-core" > "$release_dir/build-info.txt"
chmod 0555 "$release_dir/jysec-core"
chmod 0444 "$release_dir/jysec-core.sha256" "$release_dir/build-info.txt"
```

Sidecar 必須隨該產物保存，檔名固定為 `jysec-core.sha256`，內容是一行 `<64位hex>  jysec-core`。它證明與建置時摘要一致，不是數位簽章；對供應鏈真偽的保證另需簽章或可信發布渠道。不要從目前可變檔案隨手生成 sidecar 然後聲稱是先前已驗證版本。

## 部署流程設計（管理員下一次部署時採用）

1. 取得單一部署鎖（例如 `/run/lock/jysec-core-deploy.lock` 的 flock），覆蓋安裝、restart、健康檢查與可能的回滾全程。解析並固定實際 release 目錄，避免 `current` 被另一個部署改指向。
2. 先將產物與 sidecar 複製到新的 private snapshot 目錄；以固定檔名讀取 sidecar，嚴格驗證一行、64 位 hex、檔名 `jysec-core`，拒絕其他格式。重新計算 snapshot 雜湊並比對 sidecar。後续只讀這份 snapshot，不再讀工作區的檔案。
3. 檢查架構、CGO 建置 metadata 與系統相容性。以離線 build-info 或隔離 smoke test 確認 SQLite 可用；不能再發布 CGO=0 的 go-sqlite3 stub。
4. 保存現行 binary 至帶唯一時間戳的備份，記錄備份 SHA-256、大小、owner/mode，不覆寫既有回滾備份。
5. 在目的地同一檔案系統建立唯一 temporary 檔，用 `install -o jysec -g jysec -m 0750` 從 snapshot 複製。驗證 temporary 雜湊等於 sidecar；不同則中止，現行 binary 保持原樣。
6. sync temporary 檔，再以 atomic rename 替換 binary、sync 父目錄。立即以 sudo 計算落地檔雜湊；**必須再次等於同一個 sidecar 值**。部署中的編譯只能產生另一個 release，不能影響 snapshot。
7. 由管理員執行 restart、確認 active 與預先指定的健康檢查。必要時核對 `/proc/<MainPID>/exe` 雜湊，避免僅驗證磁碟上新檔卻仍跑舊程序。
8. 任何落地驗證、restart 或健康檢查失敗，從已驗證的備份以同樣 temporary→verify→rename 流程回滾，再 restart 並驗證；保留失敗版本與兩次雜湊供調查。服務未恢復則明確報錯，不打印「成功」。

驗收應注入三個情境：source 在 snapshot 後被重建、安裝途中 snapshot 被破壞、健康檢查失敗。第一個應仍安裝 sidecar 指定版本；第二個應驗證失敗並停止／回滾；第三個應回滾到備份且 hash 正確。本次只有流程設計，沒有執行這些生產測試。

## 回滾備份：尚待管理員檢查

目前沒有 `/opt/jysecai` 讀取權限，不能把 `jysec-core.bak-url-export-20261002` 標記成「已確認存在且完整」。歷史部署命令包含建立它，但命令歷史不是目前檔案狀態證據。請由管理員執行以下只讀檢查：

```bash
sudo test -f /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
sudo stat -c '%n size=%s owner=%U:%G mode=%a modified=%y' \
  /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
sudo sha256sum /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
sudo file /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
sudo readelf -h /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
sudo go version -m /opt/jysecai/core/current/jysec-core.bak-url-export-20261002
```

大小、ELF header 與 metadata 可排除空檔／明顯截斷，但 byte-for-byte 完整性必須對照當時已保存的備份雜湊或可信原始產物；本次沒有該基準。不要執行備份 binary 來試探，避免它連上生產 DB。
