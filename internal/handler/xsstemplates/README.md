# XSS Payload 模組庫

From the audited 2020 PHP XSS platform package (see `C:\xss-src-audit\` — **do not deploy that package**; it contains webshell JPGs and a credential-stealing `authtest.php`). Only the clean, well-understood parts were ported here, rewritten from scratch after a full line-by-line review of the 47KB payload wrapper.

/ 從 2020 PHP XSS 平台包審計後移植（原始包含 webshell 與憑證竊取後門，**不可部署**）。此處全部重寫，僅保留經逐行審計確認的行為。

## Modules / 模組

| Name | Title | Default | Sensitive | Notes |
|---|---|---|---|---|
| `metadata` | 基本資訊 | on | no | location / referrer / title / screen 等；**不含 cookie、不含 outerHTML** |
| `screenshot` | 頁面截圖 | on | no | html2canvas（同源服務，受害者不向第三方發請求），JPEG q0.6 |
| `keepsession` | Keep-session 心跳 | on | no | 定時 GIF beacon，只送 url；原版送 cookie 的行為已移除 |
| `formhook` | 表單攔截 | **off** | **yes** | 密碼欄位預設打碼；arming 需 HITL 核准 |
| `fullcookie` | 完整 Cookie | **off** | **yes** | 例外路徑：勾選 + HITL + 專屬稽核署名，三關全過才渲染 |

Deliberately dropped / 刻意不移植：`htmlyuanma`（整頁 outerHTML — 體積大、極易夾帶第三方 PII）、`chainload`/`eval_remote_source`（執行期遠端載入第二段程式碼）、2020 原版的模組串接機制（衝突與供應鏈風險來源）。

## Template variables / 模板變數

`{{.Token}}` `{{.ProjectID}}` `{{.CaptureBase}}` `{{.BeaconBase}}` `{{.MaxBytes}}` `{{.KeepSessionSeconds}}` `{{.Html2CanvasURL}}` `{{.FormHookNoMask}}`

## Wire contract / 傳輸契約

All modules POST urlencoded bodies to `{{.CaptureBase}}/{{.Token}}` with a `kind` field
(`metadata` / `screenshot` / `keepsession` / `formhook` / `fullcookie`); keepsession uses the
GIF beacon `{{.BeaconBase}}/{{.Token}}?kind=keepsession`. The server side (stage 2 of this
integration) dispatches on `kind`, keeps the existing invariants — one-shot payload tokens,
per-token+IP rate limit, byte caps — and routes hits into the `vulnerabilities` queue where
auto-triage picks them up.

/ 伺服器端（整合第二階）依 `kind` 分派，保留既有不變量（一次性 token、限流、位元組上限），hit 進 `vulnerabilities` 佇列交給自動分流。

## html2canvas vendoring / html2canvas 引入

Screenshot module lazy-loads `{{.Html2CanvasURL}}` served from the collector origin.
Vendor the official build (1.4.1, MPL-2.0, github.com/niklasvh/html2canvas) at
`web/static/vendor/html2canvas-1.4.1.min.js` before enabling the module.
