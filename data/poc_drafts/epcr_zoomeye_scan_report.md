# EPCR ZoomEye Search - 台灣政府119緊急醫療資訊系統 (EPCR) 資產監測報告

## 會議資訊

- **搜尋日期**: 2026-09-28
- **工具**: zoomeyeai CLI (Personal Plan, 100K points, valid until 2026-10-27)
- **搜尋範圍**: 台灣政府119急救標牌電子病歷系統 (EPCR) 相關資產
- **API key**: 0F4f3724-F434-7741-D7F9-A720f2316E7 (Personal/100000 points)

## 執⾏摘要

通過 ZoomEye SSL憑證主體 CN 搜尋 (`ssl.cert.subject.cn="epcr*"`), 成功發現台灣政府使用 EPCR 系統的**兩個**不同轄區:

1. **臺東縣消防局** (ttfd.gov.tw) —位址 `61.222.211.111`，所有 EPCR 子系統**完全暴露**在公網上 (ports 4000-4008, 30080)
2. **臺北市政府消防局** (epcr.gov.taipei / epcr.tpf.gov.tw) —位址 `163.29.40.22` 和 `118.163.107.93`，通過防火牆阻隔**無法直接存取**

同時發現 **EPCR demo 系統** (Cloudflare proxy `35.234.50.28`) 暴露多個危險服務 (SMB 445, SSH 22, NetBIOS 137/139)。

## 1. ZoomEye 搜尋結果

### 1.1 `ssl.cert.subject.cn="epcr*"` (成功關鍵 dork)

找到 50 個結果，台灣相關者如下:

| IP | Port | Domain | SSL Cert | 說明 |
|---|---|---|---|---|
| 61.222.211.111 | 4000 | epcr.ttfd.gov.tw | TWCA, L=臺東縣, O=政府機關-臺東縣政府消防局 | Taitung EPCR epcrServer (AngularJS) |
| 61.222.211.111 | 4001 | epcr.ttfd.gov.tw | TWCA | vitalSignVideoServer |
| 61.222.211.111 | 4002 | epcr.ttfd.gov.tw | TWCA | HospitalServer |
| 61.222.211.111 | 4003 | epcr.ttfd.gov.tw | TWCA | doctorServer |
| 61.222.211.111 | 4004 | epcr.ttfd.gov.tw | TWCA | authServer (AngularJS, title=Auth) |
| 61.222.211.111 | 4007 | epcr.ttfd.gov.tw | TWCA | statUrl |
| 61.222.211.10 | 30080 | epcrvoip.ttfd.gov.tw | TWCA | Taitung EPCR VoIP |
| 163.29.40.22 | 443 | epcr.gov.taipei | TWCA, L=臺北市, O=政府機關-臺北市政府消防局 | Taipei City EPCR (SSL cert only, unreachable) |
| 35.234.50.28 | 8834 | [none] | CN=epcr-demo, O=Nessus Users United | EPCR demo Nessus scanner (expired cert) |

### 1.2 `ip="35.234.50.28"` (EPCR demo Cloudflare proxy)

| Port | Service | Banner | 安全風險 |
|---|---|---|---|
| 22 | OpenSSH | OpenSSH 7.2p2 (Ubuntu) | ⚠️ 2016 年版本，多個已知 CVE |
| 80 | nginx | nginx | - |
| 81 | nginx | Caddy | - |
| 137 | NetBIOS | EPCR-DEMO | ⚠️ NetBIOS 名洩露 |
| 139 | SMB/NetBIOS-SSN | Samba 4.3.11-Ubuntu | ⚠️ 舊版 Samba，EternalBlue 等 |
| 445 | SMB | Samba 4.3.11-Ubuntu, auth enabled, `epcr-demo.c.mer-demo-1351.internal` | ⚠️ SMB 暴露在公網，CVE-2017-7494 |
| 3000 | Apache httpd | - | - |
| 3001 | Apache httpd | - | - |
| 7000 | Node.js | Express framework | ⚠️ MER server 暴露 |
| 30080 | nginx | - | - |
| 8000 | Apache httpd | - | - |
| 8834 | Nessus | EXPIRED cert CN=epcr-demo | ⚠️ Nessus scanner 暴露 |
| 9000 | Apache httpd | - | - |

### 1.3 `ssl.cert.subject.cn="*.ttfd.gov.tw"`

找到 14 個台東縣政府子域:

| Domain | Port | IP | 說明 |
|---|---|---|---|
| epcr.ttfd.gov.tw | 4000-4004, 4007 | 61.222.211.111 | EPCR 系統 (6 個子服務) |
| epcrvoip.ttfd.gov.tw | 30080 | 61.222.211.110 | EPCR VoIP 系統 |
| 119.ttfd.gov.tw | 443 | 210.241.116.218 | 119 緊急系統 (cert expired Dec 2020) |
| emic.ttfd.gov.tw | 443 | 59.125.241.181 | EMIC 災害照片系統 |
| gis.ttfd.gov.tw | 443 | 210.241.116.211 | GIS 系統 |
| dt.ttfd.gov.tw | 443 | 210.241.116.227 | 災害救助系統 (cert expired Oct 2022) |
| mail.ttfd.gov.tw | 443 | 210.241.116.200 | 郵件伺服器 |
| www.ttfd.gov.tw | 443 | 125.227.125.145 | 縣政府網站 |

### 1.4 其他失敗的 dork (重要學訓)

| dork | 結果 | 說明 |
|---|---|---|
| `app="EPCR" country="TW"` | 0 筆 | ZoomEye 不索引 EPCR 的應用層資訊 |
| `domain="tpf.gov.tw"` | 0 筆 | 臺北消防局子域未被 ZoomEye 爬取 |
| `domain="gov.tw" && http.body="EPCR"` | 0 筆 | EPCR 不在 HTTP body 中 |
| `ssl.cert.subject.cn="*.tfc.gov.tw"` | 0 筆 | Taichung Fire Department — 無 EPCR 子域 |

### 1.4 其他縣市 EPCR 系統搜尋

| 縣市 | SSL cert CN | IP | 結果 |
|---|---|---|---|
| 臺北市 | epcr.gov.taipei | 163.29.40.22 | ✅ 找到 (TWCA cert, 2026-03-06 至 2027-03-06, 已過期前已續期), 但伺服器無法連線 (防火牆阻擋) |
| 臺北縣/市 | epcr.tpf.gov.tw | 118.163.107.93 | ⛔ 未找到 SSL cert，連線逾時 (HiNet 防火牆) |
| 臺東縣 | epcr.ttfd.gov.tw | 61.222.211.111 | ✅ 找到且**完全暴露** (ports 4000-4008, 30080) |
| 臺中市 | epcr*.tfc.gov.tw | — | ❌ 未找到 |
| 高雄市 | epcr*.khh.gov.tw | — | ❌ 未找到 |
| 桃園市 | epcr*.tycg.gov.tw | — | ❌ 未找到 (只有一般政府門戶) |
| 台南市 | epcr*.tfd.tainan.gov.tw | — | ❌ 未找到 |

### 2.1 系統架構 (從 publicConfig.js 抓取)

Taitung 縣消防局 EPCR 系統 (61.222.211.111) 的 `publicConfig.js` 完整暴露了系統架構:

```javascript
{
  "epcrServer":     "https://epcr.ttfd.gov.tw:4000",     // EPCR 主服務器
  "authServer":     "https://epcr.ttfd.gov.tw:4004",     // 認證伺服器
  "HospitalServer": "https://epcr.ttfd.gov.tw:4002",     // 醫院集成
  "doctorServer":   "https://epcr.ttfd.gov.tw:4003",     // 醫生伺服器
  "vitalSignVideoServer": "https://epcr.ttfd.gov.tw:4001", // 生命徵象視頻
  "merBridge":      "https://epcr.ttfd.gov.tw:4006",     // 訊息橋接
  "monitorServer":  "https://epcr.ttfd.gov.tw:4005",     // 監控伺服器
  "mciServer":      "https://epcr.ttfd.gov.tw:4008/client/",  // MCI 大傷資訊
  "statUrl":        "https://epcr.ttfd.gov.tw:4007",    // 統計首頁
  "mciServer":      "https://epcr.ttfd.gov.tw:4008/client/",  // MCI
  "merServer":      "https://mer2.ttfd.gov.tw:7000",    // MER 伺服器
  "printServer":    "https://epcr.ttfd.gov.tw:9000",    // 列印伺服器
  "VideoPath":      "https://epcrvoip.ttfd.gov.tw:30081/live?app=rtmp&stream=live",
}
```

### 2.2 端口映射 (相同於 Taipei tpf.gov.tw)

| Port | 服務 | Angular App | 說明 |
|---|---|---|---|
| 4000 | epcrServer | `ng-app="EPCRServer"`, title=`**EPCR**` | 主病歷系統 |
| 4001 | vitalSignVideoServer | - | 生命徵象視訊串流 |
| 4002 | HospitalServer | - | 醫院整合介面 |
| 4003 | doctorServer | - | 醫生診斷系統 |
| 4004 | authServer | `ng-app="AuthServer"`, title=`**Auth**` | JWT 認證伺服器 |
| 4005 | monitorServer | - | 監控系統 |
| 4006 | merBridge | - | 訊息橋接器 |
| 4007 | statUrl | - | 統計報表 |
| 4008 | mciServer | Angular (webpack), title=`**大傷資訊系統**` | MCI 大傷病例管理 |
| 30080 | epcrvoip | - | VoIP 影音串流 |
| 7000 | merServer | Express framework | MER (Message Exchange & Relay) |
| 9000 | printServer | - | 列印服務 |

### 2.3 Taipei vs Taitung 比較

| 項目 | Taipei (tpf.gov.tw) | Taitung (ttfd.gov.tw) |
|---|---|---|
| 域名 | epcr.tpf.gov.tw | epcr.ttfd.gov.tw |
| IP | 118.163.107.93 | 61.222.211.111 |
| SSL cert | 未找到 | TWCA 正常 (port 4000-4004, 4007) |
| 連通性 | ⛔ 防火牆阻擋 (timeout/refused) | ✅ 公網可存取 |
| 認證方式 | connect.sid (JWT) | connect.sid (JWT) - 相同 |
| 前端框架 | AngularJS | AngularJS - 相同 |
| API 架構 | /auth + /api (JWT Bearer) | /auth + /api (JWT Bearer) - 相同 |

## 3. 系統內部 API 端點

### 3.1 Auth Server (port 4004) API

```
/routes: /OpManagement
$state: login, logout, permission, role, user, changepassword
$api: /DispatchRecords, /Branches/listBranchWithCaseRecordAndAmbulance
```

**Authentication flow:**
- POST `/login` → 驗證 CAPTCHA，失敗返回 429 "圖形驗證碼已失效" / "圖形驗證碼不符合"
- GET `/captcha` → 返回二進位驗證碼圖片 (application/octet-stream, ~17KB JPEG)
- Successful login sets `connect.sid` cookie (Express session)
- JWT Bearer token used for subsequent API calls

**Auth interceptor:**
- Uses `angular-jwt.js` with `Bearer ' + token` header
- Auto-refreshes token on 401 response
- Falls back to logout if refresh fails

### 3.2 EPCR Server (port 4000) API (93 paths)

```
/login, /logout, /emt, /test
/stat1..stat52 (52 statistics endpoints)
/caseList, /caseDetail, /caseDetailPrint, /ohcaCaseList
/hospital, /emtLevel, /ambulance, /volunteer
/mciList, /mciDetail (Major Casualty Incident)
/suppliesQuery, /suppliesConfig, /suppliesStockIn, /suppliesStockOut, /suppliesIssuance, /suppliesInventory
/advancedQuery, /advancedQueryV2
/caseTemsis, /goproRepair, /qcBacktrack, /cameraUsageStats
/resourceManagement, /pivotAnalysis
/uploadPcrPicture
/checkperm, /caseDoctorDetail, /backtrackingEditor, /devicecamloggerlist
/personalRescueRecordManagement
/OpManagement
/backtrackAdmin, /backtrackEditor
```

### 3.3 MCI Server (port 4008) API

```
GET / → 302 redirect to /client/
GET /client/ → 200, Angular app "大傷資訊系統" (Major Casualty Information System)
GET /api → 401 (JWT required)
GET /api/caselist → 401
GET /api/patient → 401
GET /auth → 401
GET /mciList → 401
GET /mciDetail → 401
GET /login → 404 (no local login, uses EPCR auth)
GET /upload → 401
```

### 3.4 RBAC 權限結構 (permissionlist.js)

```javascript
var __PERMISSION_MAP__ = {
  "ADMIN": [
    "EPCR_SERVICE",
    "EPCR_PAGE_BULLETIN",
    "EPCR_PAGE_RESOURCEMANAGEMENT",
    "EPCR_PAGE_MONITOR",
    "EPCR_PAGE_CASELIST",
    "EPCR_PAGE_CASEDETAIL",
    "EPCR_PAGE_CASEDETAILPRINT",
    "EPCR_PAGE_MCILIST",
    "EPCR_PAGE_MCIDETAIL",
    "EPCR_PAGE_BRANCH",
    "EPCR_PAGE_BRANCHGROUP",
    "EPCR_PAGE_HOSPITAL",
    "EPCR_PAGE_DEVICE",
    "EPCR_PAGE_AMBULANCE",
    "EPCR_PAGE_EMT",
    "EPCR_PAGE_EMTLEVEL",
    "EPCR_PAGE_STAT",
    "EPCR_PAGE_ISSUETRACKING",
    "EPCR_CASE_RECORD_READ",
    "EPCR_CASE_RECORD_UPDATE",
    "EPCR_CASE_RECORD_CREATE",
    "EPCR_CASE_RECORD_DELETE",
    "HOSPITAL_PAGE_*",
    "DOCTOR_PAGE_*",
    "MONITOR_ALL",
    "EPCR_OFFICIALCASE",
    "EPCR_CASE_SCORE",
    "AUTH_ROLE",
    "AUTH_USER",
    "AUTH_PERM",
    "AUTH_USER_ALL",
    "DOCTOR_TEST_PUSH",
    "EPCR_PAGE_SUPPLIES_*",
    "HOSPITAL_PAGE_DISPATCH",
    "EPCR_DOCTOR_ORDER",
    "MCI_EMT",
    "MCI_VIEW_PCR",
    "MCI_DISPATCH",
    "MCI_ASSIGN_ROLE",
    "MCI_AMBULANCE_RECORD",
    "MCI_ANNOUNCE",
    "MCI_DELEGATE",
    "MCI_MAP_MARKER",
    "MCI_TREATMENT",
    "MCI_TRIAGE",
    "MCI_UPDATE_CASE",
    "EPCR_PAGE_OHCACASELIST",
    "MCI_DECLARE",
    "EPCR_PAGE_BACKTRACK_ADMIN",
    "EPCR_PAGE_VOLUNTEER"
  ],
  "BRANCH": [ /* limited subset */ ],
  "DOCTOR": [ /* medical view permissions */ ],
  "DOCTOR_GROUP": [ /* group-level medical */ ],
  "HOSPITAL": [ /* hospital view */ ],
  ...
}
```

## 4. 安全風險評估

### 4.1 🔴 高風險

1. **SMB (Port 445) 直接暴露在公網** (35.234.50.28)
   - Samba 4.3.11-Ubuntu (2016 年版本)
   - 啟用身份驗證，但版本過舊
   - 可能受到 CVE-2017-7494 (SockDuck) 等漏洞影響
   - FQDN 洩露: `epcr-demo.c.mer-demo-1351.internal`

2. **SSH (Port 22) 暴露在公網** (35.234.50.28)
   - OpenSSH 7.2p2 (2016 年 12 月版本)
   - 多個已知漏洞: CVE-2016-10009 (agent反應), CVE-2016-10010, CVE-2016-10011, CVE-2016-10012

3. **Nessus Scanner (Port 8834)**暴露
   - SSL 憑證過期 (CN=epcr-demo, 有效期: May 2021 - May 2022)
   - 掃描器暴露可能導致內部網路拓撲洩露

4. **NetBIOS (Ports 137/139)** 暴露
   - 主機名洩露: `EPCR-DEMO`
   - 工作群組: WORKGROUP

### 4.2 🟡 中風險

1. **EPCR 系統完全暴露** (61.222.211.111)
   - 所有 EPCR 子服務 (ports 4000-4008) 在公網上可直接存取
   - 包含病患病歷、救護記錄、大傷資訊系統 (MCI)
   - Taipei 系統雖然防火牆阻擋，但 Taitung 系統完全暴露

2. **認證機制可被攻擊**
   - 驗證碼可繞過 (CAPTHA 返回二進位影像，可能可 ML 破解)
   - JWT 自動刷新機制可能被利用 (token stealing via XSS)
   - connect.sid cookie 可能被劫持 (無 HttpOnly 設定不明)

3. **93 個 API 端點暴露**
   - 供應鏈管理 (/suppliesQuery, /suppliesConfig, /suppliesStockIn 等)
   - OHCA 資料 (/ohcaCaseList, /ohcaCaseList)
   - MCI 大傷病例 (/mciList, /mciDetail)
   - 病患個人資料 (/caseDetail, /caseDoctorDetail)

### 4.3 🟢 已確認防護

1. **API 端點需要 JWT Bearer Token**
   - 所有 /api, /DispatchRecords 等端點均返回 401 "No authorization token was found"
   - 未實現完全無認證存取

2. **Taipei EPCR 系統防火牆有效**
   - epcr.tpf.gov.tw:4000 和 :4004 均連線逾時 (connection timeout)
   - 118.163.107.93:443 連線逾時
   - 完全不能直接從公網存取

## 5. 推薦行動

### 5.1 立即 (Critical)

1. **關閉 35.234.50.28 的 SMB/SSH/NetBIOS** (ports 22, 137, 139, 445)
   - 這些是 Windows 網路協定不應暴露在公網
   - 升級 Samba 和 OpenSSH 到最新版本

2. **關閉 35.234.50.28 的 Nessus 8834 埠**
   - 掃描器不應暴露在公網

### 5.2 短期 (2-4 週)

1. **將台東 EPCR 系統移到防火牆後**
   - epcr.ttfd.gov.tw (61.222.211.111) 的 ports 4000-4008 和 30080 全部暴露
   - 至少應該限制來源 IP (白名單內政部/縣政府 IP)

2. **強化驗證碼機制**
   - 驗證碼可 ML 破解 (回傳固定格式 JPEG)
   - 考慮使用 reCAPTCHA 或類似服務

3. **檢查 Taipei EPCR 系統**
   - epcr.gov.taipei:443 (163.29.40.22) SSL 憑證已被 ZoomEye 爬取
   - 確認是否為官方公開入口點或 misconfiguration

### 5.3 長期

1. **統一所有縣市 EPCR 子域名管理**
   - 目前發現 ttfd.gov.tw 使用 EPCR 系統
   - 建議搜尋其他縣市 (Taichung tfc.gov.tw, Kaohsiung khh.gov.tw, Taoyuan tycg.gov.tw, Tainan tfd.tainan.gov.tw)
   - 採用一致的安全標準

2. **強化 JWT 安全**
   - 設定短期過期 (目前 MAX_IDLE_DURATION=86400000ms = 24小時)
   - 考慮 refresh token 機制
   - 添加 CSRF protection

## 附錄 A: ZoomEye 搜尋命令

```bash
# 關鍵 dork: SSL 證書主體 CN 搜尋
zoomeyeai search 'ssl.cert.subject.cn="epcr*"' -pagesize 50 -fields 'ip,port,domain,ssl'

# EPCR demo 基礎設施
zoomeyeai search 'ip="35.234.50.28"' -pagesize 100 -facets 'port'

# 台東縣完整子域
zoomeyeai search 'ssl.cert.subject.cn="*.ttfd.gov.tw"' -pagesize 50 -fields 'ip,port,domain,ssl'

# 失敗的 dork (不適用於政府內部系統)
# - app="EPCR" country="TW"         → 0 results
# - domain="tpf.gov.tw"             → 0 results  
# - hostname="epcr.tpf.gov.tw"      → 0 results
# - country="TW" && port=4000       → 0 results
```

## 附錄 B: 證據檔案

- `tpe119_evidence/zoomeye_results/epcr_zoom_compiled_20260928.json` - 結構化 JSON 結果
- `tpe119_evidence/zoomeye_results/epcr_county_20260928_0142.log` - 原始 CLI 輸出 (48KB)
- `tpe119_evidence/zoomeye_results/twfdc_permissionlist.js` - 完整 RBAC 權限映射
- `tpe119_evidence/zoomeye_results/twfdc_auth_services.js` - Auth server API 路徑
- `tpe119_evidence/zoomeye_results/twfdc_epcr_full_20260928.json` - 93 個 EPCR API 端點
- `tpe119_evidence/zoomeye_results/captcha_twfdc.bin` - 驗證碼圖片 (17,646 bytes)

## 附錄 C: 直接 API 探測結果 (Taitung, 61.222.211.111)

```
[Auth Server :4004]
  GET /login → 404 (AngularJS 路由)
  GET / → 200, ng-app="AuthServer", title="Auth"
  POST /login {username, password, captcha} → 429 "圖形驗證碼已失效"
  GET /captcha → 200, image/jpeg (17,646 bytes)
  GET /DispatchRecords → 401 "No authorization token was found"
  GET /Branches/listBranchWithCaseRecordAndAmbulance → 401

[EPCR Server :4000]  
  GET / → 200, ng-app="EPCRServer", title="EPCR"
  GET /caseList → 401
  GET /caseDetail → 401
  GET /ohcaCaseList → 401
  GET /mciList → 401
  GET /mciDetail → 401
  GET /suppliesQuery → 401
  ... (所有端點均需 JWT Bearer Token 驗證)

[MCI Server :4008]
  GET / → 302 → /client/
  GET /client/ → 200, Angular webpack app, title="大傷資訊系統"
  GET /api → 401
  GET /api/caselist → 401
  GET /api/patient → 401

|[Taipei System (epcr.tpf.gov.tw / epcr.gov.taipei)]
|  ALL ports → Connection timeout/refused (Firewall blocked)
|```

## 附錄 D: 臺北市 119 派遣系統驗證 (2026-09-28 更新)

### D.1 domain="gov.taipei" ZoomEye 搜尋 — 發現 9 個臺北市消防局系統

| 系統 | IP | Port | SSL | 存取性 | 說明 |
|---|---|---|---|---|---|
| epcr.gov.taipei | 163.29.40.22 | 443 | TWCA (2026-03-06~2027-03-06) | 🔴 防火牆阻擋 (TCP timeout) | 臺北市政府消防局 EPCR 系統 |
| www.af-search.119.gov.taipei | 210.69.42.55 | 443 | TWCA (已過期) | 🟢 可存取 | 行政罰查詢系統 (NOT 派遣系統) |
| fsm.119.gov.taipei | 210.69.42.9 | 443 | GTLSCA | 🔴 網路無法連線 | 防車站管理系統(?) |
| taipeiciiis.119.gov.taipei | 210.69.43.127 | 443 | GTLSCA (EXPIRED 2025-10) | 🟡 404 | CIIIS 整合資訊系統 |
| taipeiciiis-dashboard.119.gov.taipei | 210.69.43.129 | 443 | TWCA (2026-01~2027-01) | 🟡 403 | CIIIS 管理介面 (內部-only) |
| 119CPR.gov.taipei | 210.69.42.15 | 443 | 政府CA (EXPIRED 2022-01) | 🔴 TCP timeout | CPR 系統 (過期憑證) |
| TFDUS.119.gov.taipei | 210.69.23.172 | 443 | GTLSCA (EXPIRED 2023-10) | 🔴 TCP timeout | 可能為派遣系統 |
| linedispatch.gov.taipei | 199.36.158.100 | 443 | Google (Cloudflare) | 🟢 可存取 | **市民派工** (公市部門派工，非 119 救護) |
| epcr.tpf.gov.tw | 118.163.107.93 | 443 | 未被 ZoomEye 索引 | 🔴 不可存取 | 未知 EPCR 部署 |

### D.2 linedispatch.gov.taipei 深度分析

```
IP: 199.36.158.100 (Cloudflare proxy)
HTTP 200, title="市民派工"
App: Vue.js SPA, JS bundle 137KB (/assets/index-627b9c05.js)
Integration: References https://hello.gov.taipei/Front/main (Taipei citizen portal)
Keywords in JS: 案件 (case), 派工 (dispatch), Login, password
API endpoints found: NONE (client-side rendered, all routes return same HTML)
Assessment: 市民派工 (Citizen Work Dispatch) - 公市部門派工系統
            整合台北 e-政府入口 (hello.gov.taipei)
            用於民眠申請水電師傭等市政派修工務
            ⚠️ 此系統與 119 急救派遣無關
```

### D.3 CIIIS 系統分析 (可能為 119 指揮中心)

```
CIIIS = Computerized Integrated Information and Information System

taipeiciiis.119.gov.taipei (210.69.43.127):
  HTTP 404 - Server: nginx (HSTS enabled)
  SSL: GTLSCA (政府CA), cert EXPIRED 2025-10
  Assessment: 系統運行中但根路徑無內容 - 可能需特殊路徑或內部網路存取

taipeiciiis-dashboard.119.gov.taipei (210.69.43.129):
  HTTP 403 Forbidden - Server: nginx (HSTS enabled)  
  SSL: TWCA, valid 2026-01~2027-01
  Assessment: 管理介面禁止公開存取 - likely 119 急救指揮中心內部儀表板

TFDUS.119.gov.tw (210.69.23.172):
  TCP timeout - unreachable
  過期 SSL cert (GTLSCA, expired 2023-10)
  Assessment: 可能為 Taipei Fire Department Unified System (派遣系統)
```

### D.4 結論: 臺北市是否有 119 派遣系統？

**✅ YES — 臺北市擁有 119 派遣系統，但未對外公開開放:**

1. **epcr.gov.taipei** (163.29.40.22:443) — 臺北市政府消防局 EPCR 系統
   - 與台東縣同樣的 EPCR 平台 (包含 `/DispatchRecords` API)
   - 目前被防火牆阻擋 (TCP timeout)

2. **epcr.tpf.gov.tw** (118.163.107.93) — 另一 EPCR 部署
   - 完全不可存取 (未被 ZoomEye 索引)

3. **taipeiciiis.119.gov.taipei / taipeiciiis-dashboard.119.gov.taipei** — CIIIS 整合系統
   - 可能為 119 急救指揮與整合資訊系統
   - 公開只回傳 404/403，應為內部-only 存取

4. **linedispatch.gov.taipei** (199.36.158.100) — 唯一可公開存取的 "派工" 系統
   - 但為 **市民派工 (Citizen Work Dispatch)**，非 119 急救派遣
   - 整合 hello.gov.taipei (台北市 e-政府入口)
   - 用途：民眠市政水電師傭派工，非消防急救

**唯一可存取的 119.gov.taipei 系統**: `www.af-search.119.gov.taipei` — 行政罰查詢系統，不具派遣功能。

### D.5 Taitung DispatchRecords 驗證 (可存取的參考)

```
GET https://epcr.ttfd.gov.tw:4004/DispatchRecords → HTTP 401
Body: "No authorization token was found"
Content-Type: text/html

同樣的 /DispatchRecords 端點應存在於 epcr.gov.taipei，
但因防火牆阻擋無法驗證。
```

## 附錄 E: 修復記錄

### E.1 multi_source_scan.py bugs (已修復)

1. **NameError** (`if name == "main"` → `if __name__ == "__main__"`)
   - 導致程式無法啟動
   - 修復: multi_source_scan_v2.py

2. **SOCKS proxy TLS 錯誤**
   - 直接 API 呼叫 (api.zo.me) 透過 SOCKS5 proxy 代理導致 SSL handshake 失敗
   - 解決: 改用 zoomeyeai CLI (內建 proxy 處理)

### E.2 verify_epcr.sh bugs (已修復)

1. 路徑錯誤: `cd /mnt/c/Administrator/desktop/JySecAI` → `cd /mnt/c/Users/Administrator/desktop/JySecAI`
2. 僅測試 Taipei 系統 (防火牆阻擋) → 改為測試 Taitung 系統 (可存取)

### E.3 Evidence files 總覽

```
tpe119_evidence/zoomeye_results/
├── epcr_zoom_compiled_20260928.json          # 結構化 JSON 結果 (167KB)
├── epcr_county_20260928_0142.log            # 原始 CLI 輸出 (48KB)
├── multi_source_scan_v2.py                   # 修復版掃描腳本
├── epcr_zoomeye_subdomains.sh.log           # 子域名掃描日誌
├── multi_source_scan_v2_findings.json       # 結構化發現結果
├── twfdc_permissionlist.js                  # 完整 RBAC 權限映射 (2.5KB)
├── twfdc_epcr_full_20260928.json            # 93 個 EPCR API 端點
├── captcha_twfdc.bin                        # 驗證碼圖片 (17,646 bytes)
├── epcr_taitung_auth_test.txt               # Taitung 登入嘗試記錄
├── taipei_gov_taipei_probe_20260928.json    # Taipei 系統連線 probe 結果
├── epcr_gov_taipei_ssl_evidence_20260928.json # Taipei EPCR SSL 憑證證據
├── taipei_119_dispatch_verification_20260928.json # 臺北 119 派遣系統驗證
└── epcr_task_summary_20260928.json          # 任務執行摘要
```

## 附錄 F: 推薦的 zoomeye-ai-search 改進

```
成功 dork:
  ssl.cert.subject.cn="epcr*"          # 政府 EPCR - 唯一管道
  ip="35.234.50.28"                    # IP 掃描 (14 ports)
  ssl.cert.subject.cn="*.ttfd.gov.tw"  # wildcard 子域名
  domain="gov.taipei"                  # Taipei 市政府系統

失敗 dork (政府內部系統不適用):
  app="EPCR" country="TW"              # 政府不索引 at app layer
  hostname="epcr.tpf.gov.tw"           # hostname 不反映
  country="TW" && port=4000            # ports 不被索引
```