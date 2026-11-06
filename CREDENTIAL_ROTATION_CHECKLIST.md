# `config.yaml` 憑證輪替清單

產生日期：2026-10-02  
關聯提交：`f574d4f39`（`archive: include complete workspace for vulnerability verification`）

> 本清單只記錄欄位位置與處置步驟，不包含、讀出或複製任何憑證值。Git 歷史中出現過的憑證都應視為已外洩。輪替必須由擁有供應商後台或服務管理權限的人員執行。

## 需輪替的 6 組憑證

| 組別 | `config.yaml` 區段與行號 | 推測供應商／服務 | 輪替步驟 |
|---|---|---|---|
| Jy 共用 API key | `ai.channels.jy-53.api_key` L45、`jy-air` L55、`jy-flash` L65、`jy-gateway` L75、`jy-nano` L85、`jy-think` L95 | 內部 Jy Gateway／OpenAI-compatible gateway | 在 Gateway 管理介面建立替代 key；以安全通道更新六個 channel；逐一做最小模型請求；確認成功後撤銷舊 key；查核舊 key 已無成功請求。 |
| NVIDIA 共用 API key | `ai.channels.nvidia-deepseek-v4.api_key` L105、`nvidia-diffusiongemma` L115、`nvidia-gpt-oss-20b` L125、`nvidia-ising-calibration` L135、`nvidia-llama-33-70b` L145、`nvidia-llama-safety-guard` L155、`nvidia-muse-glimmer` L165、`nvidia-nemotron-120b` L175、`nvidia-nemotron-550b` L185、`nvidia-primary` L195 | NVIDIA API／NIM | 在 NVIDIA 帳戶建立替代 key；更新十個 channel；以非敏感提示逐一 smoke test；撤銷舊 key；檢查用量與稽核紀錄。 |
| Claude API key | `ai.channels.claude-35-sonnet.api_key` L25 | Anthropic Claude | 在 Anthropic Console 建立替代 key；更新該 channel 並測試；撤銷舊 key；檢查異常用量。 |
| Huihui API key | `ai.channels.huihui-cyberstrike.api_key` L35 | 名稱不足以確認，可能是自架或第三方 OpenAI-compatible 服務 | 先由設定擁有者確認實際發卡端；在該端建立替代 key；更新並做最小請求；撤銷舊 key；保存輪替工單。 |
| Zhipu API key | `ai.channels.zhipu-glm-4-flash.api_key` L205 | 智譜／BigModel | 在供應商控制台建立替代 key；更新 channel 並測試；撤銷舊 key；檢查異常用量。 |
| MCP 全域服務憑證 | `mcp.auth_header` L486、`mcp.auth_header_value` L487 | JySecAI 內建 MCP 服務 | 先確認 `allow_global_access` 的必要性；產生新的高熵 token 並安全部署至服務端與合法客戶端；重新啟動後測試授權／拒絕案例；撤銷舊 token。`auth_header` 是 header 名稱，真正的秘密是 `auth_header_value`。 |
| XSS collector token | ~~`xss.token` L726~~ | **已於 2026-10-02 驗證：不是憑證，見下方** | 無須輪替。 |

## 已驗證排除：`xss.token` 不是憑證（2026-10-02 實測）

原清單把 `xss.token` 列為「XSS collector 認證」是**錯的**，已更正。實測證據：

- `internal/handler/xss.go` 全檔搜尋 `h.cfg.*`，實際只讀 `BindHost`、`BindPort`、`Enabled`、`XssCanaryCookieNameEffective`、`XssMaxCaptureBytesEffective`、`XssPublicURLEffective`、`XssRateLimitPerMinuteEffective`、`XssProbeTTLSecondsEffective`。**`cfg.Token` 一次都沒出現。**
- `internal/config/config.go:57` 雖宣告 `XssConfig.Token` 欄位，但全專案無任何讀取處，是死欄位。
- XSS 的實際驗證邊界在資料庫：`xss.go:253` → `GetXssPayloadByToken(token)` 查 `xss_payloads` 表，且要求 `Enabled == 1`、未過期、符合 rate limit。每個 payload 的 token 由 `internal/database/database.go:2120 GenerateXssToken()` 以 `crypto/rand` 產生 20 bytes（40 碼 hex），不是共用的靜態密鑰。
- 結論：輪替 `xss.token` 沒有任何安全效果。要讓已植入的 payload 失效，應停用／刪除對應的 `xss_payloads` 記錄。

## 需先確認、暫不列入 6 組輪替的欄位

- `knowledge.embedding.api_key`（L626）長度只有 10，可能是範例或佔位符。設定擁有者應在不複製值的前提下確認發卡端與有效性；若它可用或曾可用，立刻按相同流程輪替。

## 完成證據

每組輪替至少保留：執行人、時間、供應商或服務、舊 key 撤銷證據、新 key smoke test 結果、異常用量檢查結果。證據中只記錄 key ID 或末四碼，不保存完整值。
