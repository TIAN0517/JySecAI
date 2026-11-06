# XSS Payload 模組庫

From the audited 2020 PHP XSS platform package (see `C:\xss-src-audit\` — **do not deploy that package**; it contains webshell JPGs and a credential-stealing `authtest.php`). Only the clean, well-understood parts were ported here, rewritten from scratch after a full line-by-line review of the 47KB payload wrapper.

/ 從 2020 PHP XSS 平台包審計後移植（原始包含 webshell 與憑證竊取後門，**不可部署**）。此處全部重寫，僅保留經逐行審計確認的行為。

## Modules / 模組

| Name | Title | Default | Sensitive | Notes |
|---|---|---|---|---|
| `metadata` | 基本資訊 | on | no | location / referrer / title / screen 等；**不含 cookie、不含 outerHTML** |
| `keepsession` | Keep-session 心跳 | on | no | 定時 GIF beacon，只送 url；原版送 cookie 的行為已移除 |
| `screenshot` | 頁面截圖 | **off（未接上）** | no | 模板保留；renderer 未納入它，且 `Html2CanvasURL` 未注入 → 現況不會被渲染 |
| `formhook` | 表單攔截 | **off（未接上）** | **yes** | 模板保留；API 沒有勾選路徑，伺服器端 `kind=formhook` 直接 400 拒收、不落地 |
| `fullcookie` | 完整 Cookie | **off（未接上）** | **yes** | 模板保留；API 沒有勾選路徑，伺服器端 `kind=fullcookie` 直接 400 拒收、不落地 → **整包 session cookie 目前不會被收集** |

Deliberately dropped / 刻意不移植：`htmlyuanma`（整頁 outerHTML — 體積大、極易夾帶第三方 PII）、`chainload`/`eval_remote_source`（執行期遠端載入第二段程式碼）、2020 原版的模組串接機制（衝突與供應鏈風險來源）。

## Template variables / 模板變數

`{{.Token}}` `{{.ProjectID}}` `{{.CaptureBase}}` `{{.BeaconBase}}` `{{.MaxBytes}}` `{{.KeepSessionSeconds}}` `{{.FormHookNoMask}}`

`{{.Html2CanvasURL}}` 目前**沒有任何注入點**（`renderDefaultModules` 未設定它）—— `screenshot` 模組若要接上，
必須先補上注入與 vendor 路徑，否則渲染出來是空字串。

## Wire contract / 傳輸契約

All modules POST urlencoded bodies to `{{.CaptureBase}}/{{.Token}}` with a `kind` field
(`metadata` / `screenshot` / `keepsession` / `formhook` / `fullcookie`); keepsession uses the
GIF beacon `{{.BeaconBase}}/{{.Token}}?kind=keepsession`. The server side (stage 2 of this
integration) dispatches on `kind`, keeps the existing invariants — one-shot payload tokens,
per-token+IP rate limit, byte caps — and routes hits into the `vulnerabilities` queue where
auto-triage picks them up.

/ 伺服器端（整合第二階）依 `kind` 分派，保留既有不變量（一次性 token、限流、位元組上限），hit 進 `vulnerabilities` 佇列交給自動分流。

## Enforced invariants / 目前強制的不變量

這一段描述的是**程式實際強制的行為**，不是設計意圖。文件寫得比程式多做的部分，
一律以這裡為準。

- **只有兩種模組會被渲染**：`metadata`、`keepsession`（one-time payload 只渲染 `metadata`）。
  渲染清單寫在 `internal/handler/xss_modules.go` 的 `defaultXSSModules`。
- **cookie 只走 canary 通道**：`renderCollectorJS` 產生的 canary 片段只比對**專用名稱**的 cookie
  （`xss.canary_cookie_name`，預設 `jysec_xss_canary`），且只取該 cookie 本身的值。
  取不到有效 canary → `400 valid JySec canary required`，不落地。
  `metadata`／`keepsession`／`screenshot` 三支模板一律不讀 `document.cookie`。
- **`fullcookie` / `formhook` 目前無法被啟用**：
  1. `POST /api/xss/payloads` 沒有 `modules` 欄位 → 沒有「勾選」路徑；
  2. `POST /xss/capture/:token` 只接受 `kind=metadata`／`kind=keepsession`，
     其餘一律 `400 unsupported callback`、**不寫入 capture 佇列**。
  換句話說：即使受害端真的把整包 session cookie 送過來，平台也會直接丟掉。
- **敏感資料的判定**：`fullcookie` / `formhook` 在 `xsstemplates.Registry` 標為 `Sensitive: true`、
  `DefaultEnabled: false`；`xsstemplates_test.go` 會斷言這兩條不變量。

測試釘死的位置：`internal/handler/xss_safety_test.go`
（`TestRenderCollectorJSOnlySendsJySecCanary`、`TestNormalizeCanaryCookieRejectsSessionCookie`、
`TestXSSModuleRejectsFullCookie`、`TestRenderCollectorJSIncludesMetadataNotSessionCookie`）。

## html2canvas vendoring / html2canvas 引入

Screenshot module lazy-loads `{{.Html2CanvasURL}}` served from the collector origin.
Vendor the official build (1.4.1, MPL-2.0, github.com/niklasvh/html2canvas) at
`web/static/vendor/html2canvas-1.4.1.min.js` before enabling the module.
