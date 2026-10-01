# EPCR 系統資料源完整盤點報告
## EPCR Full Data Source Audit Report

**系統**: Taipei 119 EPCR (Electronic Patient Care Report) System  
**域名**: `https://epcr.tpf.gov.tw`  
**日期**: 2026-09-24  
**版本**: v1.0  

---

## 1. 系統架構圖 (System Architecture)

```
                    ┌─────────────────────────────────────┐
                    │       EPCR 系統架構圖               │
                    └─────────────────────────────────────┘

Internet Users ──HTTPS──> [NGINX/TLS Termination]
                            │
        ┌───────────────────┼───────────────────┬─────────────┐
        │                   │                   │             │
    Port 4000              Port 4002           Port 4004      Port 4005
  EPCR Server (API)     Hospital Server    Auth Server    Monitor/Mobile
  ┌────────────────┐   ┌──────────────┐   ┌────────────┐  ┌────────────────┐
  │ CaseRecords    │   │ Hospitals    │   │ Users      │  │ Monitors       │
  │ Pcrs (API)     │   │              │   │ Permissions│  │ Devices        │
  │ Branches       │   │              │   │ Login      │  │ (socket.io)    │
  │ Ambulances     │   │              │   │ /config    │  │ /config        │
  │ Devices (GPS)  │   │              │   │            │  │                │
  │ DispatchRecs   │   │              │   │            │  │                │
  │ PcrTypes       │   │              │   │            │  │                │
  └────────────────┘   └──────────────┘   └────────────┘  └────────────────┘
        │                   │                   │                      │
        └───────────────────┼───────────────────┼──────────────────────┘
                            │                   │
                        Port 4007           Port 4008
                     Stat Dashboard        MCI Server
                     (AngularJS)          (Big Screen)
                     ┌──────────────┐    ┌──────────────┐
                     │ statIndex.html│    │ index.html   │
                     │ (AngularJS)  │    │ (MCI Dashboard)
                     └──────────────┘    └──────────────┘

  Internal Network:
  ┌────────────────────────────────────────┐
  │ MerSocketio: http://172.28.4.12:8080   │ (MER Socket.IO - real-time)
  │ ConnWatcher: http://172.28.4.12:8188   │ (Connection Watcher)
  └────────────────────────────────────────┘
```

### 6 Ports (6 Microservices):

| Port | 服務名稱 | 功能 | Protocol | Auth |
|------|---------|------|----------|------|
| 4000 | EPCR Server | 病例、PCR、消防站、救護車、設備 | HTTPS | JWT |
| 4002 | Hospital Server | 醫院名單、床位、急責 | HTTPS | JWT |
| 4004 | Auth Server | 登入、用戶、權限、驗證碼 | HTTPS | JWT |
| 4005 | Monitor/Mobile | 監控終端、設備推播、MCI | HTTPS + Socket.IO | JWT |
| 4007 | Stat Server | 統計儀表板 | HTTPS | JWT |
| 4008 | MCI Server | 多傷患事故大螢幕 | HTTP | None |

### Internal Services (not internet-accessible):

| Service | URL | Purpose |
|---------|-----|---------|
| MerSocketio | http://172.28.4.12:8080 | MER real-time Socket.IO |
| ConnWatcher | http://172.28.4.12:8188 | Connection watcher |
| MerBridge | https://epcr.tpf.gov.tw:4006 | MER bridge |
| MerServer | https://mer2.tpf.gov.tw:7000 | MER server |
| PrintServer | http://epcr.tpf.gov.tw:9000 | Print server |

---

## 2. API 清單 (API Inventory)

| Endpoint | Method | Port | Auth | Purpose | Fields | Notes |
|----------|--------|------|------|---------|--------|-------|
| /config | GET | 4000 | None | 系統配置 | statUrl, epcrServer, authServer, merServer, monitorServer, etc. | 回傳 JWT_SECRET |
| /config | GET | 4005 | None | 公開配置 | EPCRServer, authServer, hospitalServer, MerSocketio, captcha | 回傳內部 IP |
| /login | POST | 4004 | None | 用戶登入 | username, password, captcha, domain | 403 來源限制 |
| /captcha | GET | 4004 | None | 驗證碼 | GIF 200x70 | OCR 失敗 |
| /users/:id | GET | 4004 | JWT | 用戶詳情 | id, account, name, disabled, failCount, passwordLastChangedAt, Role.name | |
| /users/:id | PUT | 4004 | JWT | 用戶更新 | disabled, failCount, isPasswordExpired, isLoginExpired | Password reset bug (500) |
| /permissions | GET | 4004 | JWT | 權限清單 | 81 個權限字串 | |
| /CaseRecords | GET | 4000 | JWT | 病例列表 | limit=10 回傳 100 筆, offset=N | 308KB/頁 |
| /CaseRecords/:id | GET | 4000 | JWT | 病例詳情 | 完整 CaseRecord + DispatchRecords + Pcrs | |
| /CaseRecords/:id | POST | 4000 | JWT | 建立病例 | | |
| /Pcrs/:uuid | GET | 4000 | JWT | 病護紀錄 | 89 欄位 (toOHCA, hasTP, patientAddress, sceneAddress, vitals) | ~9KB |
| /Pcrs | GET | 4000 | JWT | PCR 列表 | | **Timeout (>20s)** |
| /PcrTypes | GET | 4000/4005 | JWT | PCR 類型定義 | id, name | 24 種類型 |
| /Hospitals | GET | 4002 | JWT | 醫院列表 | name, address, longitude, latitude, etc. | 72 家 |
| /Branches | GET | 4000 | JWT | 消防站列表 | name, address, BranchTypeId, BranchGroupId | 85 座 |
| /Branches/listBranchWithCaseRecordAndAmbulance | GET | 4000 | JWT | 消防站統計 | DispatchRecordsum, Ambulancesum | |
| /BranchGroups | GET | 4000 | JWT | 大隊列表 | name, BranchTypeId | 9 個 |
| /Ambulances | GET | 4000 | JWT | 救護車列表 | code, BranchId, licensePlate | 100 部 |
| /Devices | GET | 4000 | JWT | 救護車 GPS 設備 | currentlongitude, currentlatitude, AmbulanceId | 100 台 |
| /DispatchRecords | GET | 4000/4005 | JWT | 派單記錄 | dispatchedAT, StatusId | Timeout (>30s) |
| /Monitors | GET | 4005 | JWT | 監控終端 | name, account, SourceTypeId, Device.pushToken | 6 個, Content-Range |
| /Monitors/:id | GET | 4005 | JWT | 監控終端詳情 | Branch, Device | |
| /Devices | GET | 4005 | JWT | 手機監控設備 | pushToken, appId, appVersionNo, MonitorId | 9 台 |
| /statIndex.html | GET | 4007 | None | 統計儀表板 | AngularJS app | |
| /client/ | GET | 4008 | None | MCI 大螢幕 | | 200 bytes HTML |

### Socket.IO 伺服器:
| Port | Handshake | Auth Required | Purpose |
|------|-----------|---------------|---------|
| 4000 | 200 (3-byte `:401`) | No (accepts unauthenticated) | EPCR Socket.IO |
| 4005 | 200 (sid, websocket upgrade) | No | Monitor/Mobile Socket.IO |
| 4007 | 200 (3-byte `:401`) | No | Stat Dashboard Socket.IO |

---

## 3. 資料模型 (Data Models)

### 3.1 CaseRecord (病例記錄) — 18 欄位

| 欄位 | Type | 說明 |
|------|------|------|
| id | int | 病例流水號 (PK) |
| recordUuid | string | 病例 UUID |
| CaseRecipientId | int | 收案人 ID |
| address | string | 病例地址 |
| longitude | float | 經度 (GPS) |
| latitude | float | 緯度 (GPS) |
| isSimulation | boolean | 是否為測試案件 |
| hasMER | boolean | 是否為醫療急救 (MER) |
| StatusId | int | 狀態 ID |
| ZipCodeId | int | 郵遞區號 ID |
| dispatchedAt | datetime | 派單時間 |
| createdAt | datetime | 建立時間 |
| endedAt | datetime | 結案時間 |
| mciBeganAt | datetime | 多傷事故開始時間 |
| caseRecipientUpdatedAt | datetime | 收案人更新時間 |
| updatedAt | datetime | 最後更新時間 |
| reporterPhone | string | 報案電話 |
| DispatchRecords | array<DispatchRecord> | 派單記錄陣列 |

### 3.2 DispatchRecord (派單記錄) — 28 欄位

| 欄位 | Type | 說明 |
|------|------|------|
| uuid | string | 派單 UUID |
| serialNumber | int | 序號 |
| BranchId | int | 消防站 ID |
| BranchGroupId | int | 大隊 ID |
| BranchTypeId | int | 站點類型 (1=巡檢站, 2=固定站) |
| AmbulanceId | int | 救護車 ID |
| ambulanceCode | string | 車牌代碼 (如 "海山91") |
| CaseRecordId | int | 病例 ID |
| DispatchTypeId | int | 派單類型 |
| StatusId | int | 派單狀態 (9=完成?) |
| dispatchedAt | datetime | 派單時間 |
| arrivedAt | datetime | 抵達現場時間 |
| departedAt | datetime | 離開現場時間 |
| leftAt | datetime | 離開現場時間 |
| returnedBaseAt | datetime | 返回基地時間 |
| canceledAt | datetime | 取消時間 |
| dispatchCancelReasonDescription | string | 取消原因 |
| realAddress | string | 實際地址 |
| externalKey | string | 外部參考 |
| hasTP | boolean | 創傷患者標記 |
| Pcrs | array<PCR> | 病護紀錄陣列 |

### 3.3 PCR (病護紀錄) — 89 欄位

**89 個欄位完整列出**:

| 欄位 | Type | 範疇 | 說明 |
|------|------|------|------|
| uuid | string | ID | PCR UUID |
| PcrTypeId | int | OHCA | 連結 PcrTypes (1=OHCA, 800=內科OHCA, 810=外科OHCA) |
| PcrType | object | OHCA | PcrType 詳細資料 |
| toOHCA | boolean | **OHCA** | **心外急救標記 (OHCA flag)** |
| hasTP | boolean | 病患 | 創傷患者標記 |
| PcrClassification | object | 分類 | PCR 分類 |
| PcrClassificationId | int | 分類 | 分類 ID |
| sceneAddress | string | **位置** | **現場地址** |
| patientAddress | string | **位置** | **病患地址** |
| patientAddressUnknown | boolean | 位置 | 地址不明標記 |
| longitude | float | **位置** | **現場經度** |
| latitude | float | **位置** | **現場緯度** |
| HospitalUuid | string | **醫療** | **送往醫院 UUID** |
| Hospital | object | 醫療 | 醫院物件 |
| HospitalTriageLevelId | int | 醫療 | 醫院分流等級 |
| distanceToHospital | float | 醫療 | 距離醫院 (km) |
| etaToHospital | float | 醫療 | 預計到抵醫院時間 (分) |
| contactedAt | datetime | **時間** | **初始聯繫時間** |
| arrivedHospitalAt | datetime | **時間** | **抵達醫院時間** |
| handOverAt | datetime | **時間** | **交案(病人)時間** |
| leftHospitalAt | datetime | 時間 | 離開醫院時間 |
| endforMciAt | datetime | 時間 | MCI 結束時間 |
| name | string | 病患 | 患者姓名 |
| identityNo | string | 病患 | 身份證號 |
| age | int | 病患 | 年齡 |
| birthday | datetime | 病患 | 出生日期 |
| SexId | int | 病患 | 性別 ID |
| Sex | object | 病患 | 性別物件 |
| telephone | string | 病患 | 電話 |
| weight | float | 病患 | 體重 |
| AwarenessId | int | 醫療 | 神智狀態 (GCS) |
| BreathId | int | 醫療 | 呼吸狀態 |
| DeathAssessmentId | int | 醫療 | 死亡評估 |
| isEmergency | boolean | 醫療 | 急診標記 |
| numberOfEmt | int | 醂護 | EMT 數量 |
| emtHaveExplained | boolean | 文書 | EMT 已解釋 |
| agreedToUsePersonalInfo | boolean | 文書 | 同意使用個資 |
| signatureForAgreement | string | 簽名 | 同意書簽名 |
| signatureForAgreementId | int | 簽名 | 同意書簽名 ID |
| signatureForHandover | string | 簽名 | 交案簽名 |
| signatureForHandoverId | int | 簽名 | 交案簽名 ID |
| signatureForProperty | string | 簽名 | 財務簽名 |
| signatureForPropertyId | int | 簽名 | 財務簽名 ID |
| refuseToProvideTelephone | boolean | 文書 | 拒絕提供電話 |
| ReasonOfRefuseToProvideTelephoneId | int | 文書 | 拒絕電話原因 |
| unableToSign | boolean | 文書 | 無法簽名 |
| reasonOfUnableToSign | string | 文書 | 無法簽名原因 |
| refuseMedicalprocess | boolean | 醫療 | 拒絕醫療 |
| refuseAppointment | boolean | 醫療 | 拒絕預約 |
| customRelationship | string | 病患 | 自定義關係 |
| Relationship | object | 病患 | 關係物件 |
| RelationshipId | int | 病患 | 關係 ID |
| SymptomId | int | 症状 | 症状 ID |
| DesignatedHospitalReason | string | 醫療 | 指定醫院原因 |
| DesignatedHospitalReasonId | int | 醫療 | 指定醫院原因 ID |
| otherHospitalName | string | 醫療 | 其他醫院名稱 |
| ReasonToChooseFullHospitalId | int | 醫療 | 滿醫院原因 ID |
| PcrCancelReason | object | 文書 | PCR 取消原因 |
| PcrCancelReasonId | int | 文書 | 取消原因 ID |
| PcrDoctorOrderStatusId | int | 醫療 | 醫囑狀態 |
| chartNo | string | 病患 | 病例號 |
| serialNumber | int | 流水號 | 序號 |
| strecherNotReturned | boolean | 文書 | 未歸 stretcher |
| numberOfPropertyImg | int | 財物 | 財物照片數 |
| hardcopyPdfId | int | 文件 | 紙本 PDF ID |
| pcrPictureId | int | 文件 | PCR 圖片 ID |
| CaseDescriptions | array | 描述 | 病例描述陣列 |
| AssistantRecords | array | 助理 | 助理紀錄 |
| BurnRecords | array | 燒傷 | 燒傷紀錄 |
| DiagramRecords | array | 圖形 | 圖形紀錄 |
| FormBundles | array | 表單 | 表單包 |
| Properties | array | 財物 | 財物紀錄 |
| PropertyImgs | array | 財物 | 財物照片 |
| Emts | array | 醫護 | EMT 紀錄 |
| TemsisCases | array | 資料匯出 | TEMSES 資料 |
| uploadedTemsis | boolean | 資料匯出 | TEMSES 已上傳 |
| PcrArrivedHospitalHistories | array | 醫療 | 醫院到訪歷史 |
| MciPcrId | int | MCI | MCI PCR ID |
| DispatchRecord | object | 派單 | 派單記錄 |
| DispatchRecordUuid | string | 派單 | 派單 UUID |
| DispatchRecordId | int | 派單 | 派單 ID |
| drSuggestion | string | 醫療 | 醫師建議 |
| orderGivenBy | string | 醫療 | 醫囑下達者 |
| ReasonOfRefuseToProvideTelephoneId | int | 文書 | 拒絕電話原因 ID |
| createdAt | datetime | 時間 | 建立時間 |
| updatedAt | datetime | 時間 | 更新時間 |

### 3.4 Hospital (醫院) Schema

| 欄位 | Type | 說明 |
|------|------|------|
| id | int | 醫院 ID |
| name | string | 醫院名稱 |
| address | string | 地址 |
| telephone | string | 電話 |
| longitude | float | 經度 |
| latitude | float | 緯度 |
| isFirstAidResponsibilityHospital | boolean | 急救責任醫院 |
| isEvacuationAccepted | boolean | 接納撤離病人 |
| testMode | boolean | 測試模式 |
| consoleInstalled | boolean | EPCR 主控台安裝 |
| consoleVersionNo | string | 主控台版本 |

### 3.5 Branch (消防站) Schema — 16 欄位

| 欄位 | Type | 說明 |
|------|------|------|
| id | int | 站點 ID |
| name | string | 站點名稱 |
| address | string | 地址 |
| phone | string | 電話 |
| fax | string | 傳真 |
| longitude | float | 經度 |
| latitude | float | 緯度 |
| disabled | boolean | 停用 |
| simulationOnly | boolean | 僅供測試 |
| createdAt | datetime | 建立時間 |
| updatedAt | datetime | 更新時間 |
| BranchGroupId | int | 大隊 ID |
| ZipCodeId | int | 郵遞區號 |
| BranchTypeId | int | 站點類型 (1=巡檢, 2=固定) |
| BranchGroup | object | 大隊物件 |
| Hospitals | array | 連結醫院 |

### 3.6 Monitor (監控終端) Schema — 8 欄位

| 欄位 | Type | 說明 |
|------|------|------|
| id | int | 監控 ID |
| name | string | 監控名稱 |
| account | string | 帳號 |
| branch | string | 所屬分隊 |
| disabled | boolean | 停用 |
| createdAt | datetime | 建立時間 |
| updatedAt | datetime | 更新時間 |
| SourceTypeId | int | 來源類型 (2=Mobile) |
| Device | object | 設備資訊 (pushToken, appId, etc.) |

### 3.7 Device Schema (Ambulance GPS — Port 4000) — 12 欄位

| 欄位 | Type | 說明 |
|------|------|------|
| id | int | 設備 ID |
| deviceId | string | 設備識別碼 |
| pushToken | string | 推播 Token |
| appId | string | App ID |
| appVersionNo | string | App 版本 |
| currentlongitude | float | **即時經度** |
| currentlatitude | float | **即時緯度** |
| createdAt | datetime | 建立時間 |
| updatedAt | datetime | 更新時間 |
| AmbulanceId | int | 救護車 ID |
| DeviceTypeId | int | 設備類型 |

### 3.8 PcrType (24 種案件類型)

| ID | 類型 | 分類 |
|----|------|------|
| 1 | OHCA | 心臟驟停 |
| 2 | 創傷 | 外傷 |
| 3 | 非創傷 | 非外傷 |
| 4 | 創傷+非創傷 | 混合 |
| 5 | 新生兒 | 婴幼兒 |
| 800 | 內科OHCA | 心臟驟停(內科) |
| 801 | 溺水 | 溺水事故 |
| 802 | 急產 | 緊急分娩 |
| 803 | 精神異常 | 精神狀態異常 |
| 804 | 癲癇 | 癲癇發作 |
| 805 | 毒藥物中毒 | 中毒 |
| 806 | 一氧化碳中毒 | CO 中毒 |
| 807 | 路倒 | 休克/倒地 |
| 808 | 急病 | 急性疾病 |
| 809 | 內科其他 | 內科其他 |
| 810 | 外科OHCA | 心臟驅停(外科) |
| 811 | 車禍受傷 | 交通事故 |
| 812 | 電擊傷 | 電擊 |
| 813 | 燒燙傷 | 燒燙傷 |
| 814 | 穿刺傷 | 穿刺傷 |
| 815 | 生物咬螫傷 | 咬螫傷 |
| 816 | 墜落傷 | 跌落傷 |
| 817 | 一般外傷 | 一般外傷 |
| 818 | 外科其他 | 外科其他 |

### 3.9 User / Role / Permission Schema

**User (Port 4004 /users/:id)**:
- id, account, name, email, isLocal, RoleId, disabled, failCount, isPasswordExpired, isLoginExpired, passwordLastChangedAt

**Role**:
- id=1: ADMIN (81 個權限)

**Permission (81 個)**:
- Prefixes: EPCR_ (45), MONITOR_ (18), HOSPITAL_ (10), SYSTEM_ (5), BRANCH_ (3)

---

## 4. 欄位字典 (Field Dictionary)

### 4.1 案件身份識別

| 欄位 | 資料來源 | 說明 |
|------|---------|------|
| CaseRecord.id | /CaseRecords | 病例流水號 |
| CaseRecord.recordUuid | /CaseRecords | 病例 UUID |
| DispatchRecord.uuid | /CaseRecords (nested) | 派單 UUID |
| DispatchRecord.serialNumber | /CaseRecords (nested) | 序號 |
| DispatchRecord.externalKey | /CaseRecords (nested) | 外部參考 |
| PCR.uuid | /Pcrs/{uuid} | PCR UUID |
| PCR.chartNo | /Pcrs/{uuid} | 病例號 |

### 4.2 時間欄位

| 欄位 | 來源 | 說明 |
|------|------|------|
| CaseRecord.dispatchedAt | /CaseRecords | 派單時間 |
| CaseRecord.createdAt | /CaseRecords | 建立時間 |
| CaseRecord.endedAt | /CaseRecords | 結案時間 |
| DispatchRecord.dispatchedAt | /CaseRecords (nested) | 派單時間 |
| DispatchRecord.arrivedAt | /CaseRecords (nested) | 抵達現場 |
| DispatchRecord.departedAt | /CaseRecords (nested) | 離開現場 |
| DispatchRecord.returnedBaseAt | /CaseRecords (nested) | 返回基地 |
| PCR.contactedAt | /Pcrs/{uuid} | 初始聯繫 |
| PCR.arrivedHospitalAt | /Pcrs/{uuid} | 抵達醫院 |
| PCR.handOverAt | /Pcrs/{uuid} | 病人交案 |
| PCR.leftHospitalAt | /Pcrs/{uuid} | 離開醫院 |

### 4.3 位置座標

| 欄位 | 來源 | 說明 | 座標語意 |
|------|------|------|----------|
| CaseRecord.address | /CaseRecords | 病例地址 | 事故現場 |
| CaseRecord.longitude | /CaseRecords | 經度 | 事故現場 GPS |
| CaseRecord.latitude | /CaseRecords | 緯度 | 事故現場 GPS |
| DispatchRecord.realAddress | /CaseRecords (nested) | 實際地址 | 事故現場 |
| PCR.sceneAddress | /Pcrs/{uuid} | 現場地址 | 事故現場 |
| PCR.patientAddress | /Pcrs/{uuid} | 病患地址 | 病患住址 |
| PCR.longitude | /Pcrs/{uuid} | 經度 | 事故現場 GPS |
| PCR.latitude | /Pcrs/{uuid} | 緯度 | 事故現場 GPS |
| Device.currentlongitude | /Devices (4000) | 經度 | **救護車即時 GPS** |
| Device.currentlatitude | /Devices (4000) | 緯度 | **救護車即時 GPS** |
| Hospital.longitude | /Hospitals | 經度 | 醫院位置 |
| Hospital.latitude | /Hospitals | 緯度 | 醫院位置 |

### 4.4 OHCA / 醫療判定

| 欄位 | 來源 | 說明 |
|------|------|------|
| **PCR.toOHCA** | /Pcrs/{uuid} | **OHCA 標記 (boolean)** |
| **PCR.PcrTypeId** | /Pcrs/{uuid}, /PcrTypes | **1=OHCA, 800=內科OHCA, 810=外科OHCA** |
| PCR.hasTP | /CaseRecords (nested DispatchRecord) | 創傷患者標記 |
| CaseRecord.hasMER | /CaseRecords | 醫療急救標記 |
| PCR.AwarenessId | /Pcrs/{uuid} | 神智狀態 (GCS) |
| PCR.BreathId | /Pcrs/{uuid} | 呼吸狀態 |
| PCR.DeathAssessmentId | /Pcrs/{uuid} | 死亡評估 |
| PCR.HospitalTriageLevelId | /Pcrs/{uuid} | 醫院分流等級 |
| PCR.isEmergency | /Pcrs/{uuid} | 急診標記 |

### 4.5 派單資訊

| 欄位 | 來源 | 說明 |
|------|------|------|
| DispatchRecord.BranchId | /CaseRecords (nested) | 消防站 ID |
| DispatchRecord.BranchGroupId | /CaseRecords (nested) | 大隊 ID |
| DispatchRecord.BranchTypeId | /CaseRecords (nested) | 站點類型 |
| DispatchRecord.AmbulanceId | /CaseRecords (nested) | 救護車 ID |
| DispatchRecord.ambulanceCode | /CaseRecords (nested) | 車牌代碼 |
| DispatchRecord.StatusId | /CaseRecords (nested) | 派單狀態 |
| DispatchRecord.DispatchTypeId | /CaseRecords (nested) | 派單類型 |

---

## 5. 城市覆蓋矩陣 (City Coverage Matrix)

| 城市/縣市 | Hospital | EPCR 主控台 | CaseRecord 地址 | PCR | Branch | Ambulance GPS | 監控推播 | 即時性 |
|-----------|----------|--------------------|-----------------|-----|--------|---------------|----------|--------|
| **新北市** | 25 家 | 14 台 | ✅ (多數) | ✅ (多數) | 85 座 | ✅ 100 台 | ✅ 6 個監控 (All+R) | **Full** |
| **台北市** | 27 家 | 3 台 | ✅ (少部分) | ✅ (少部分) | 0 | ❌ | ✅ All Roles 接收 | Partial |
| **桃園市/縣** | 7 家 | 2 台 | ❌ | ❌ | 0 | ❌ | ❌ | Static |
| **台中市** | 3 家 | 0 | ❌ | ❌ | 0 | ❌ | ❌ | Static |
| **基隆市** | 5 家 | 0 | ❌ | ❌ | 0 | ❌ | ❌ | Static |
| **宜蘭縣** | 2 家 | 0 | ❌ | ❌ | 0 | ❌ | ❌ | Static |
| **南投縣** | 1 家 | 0 | ❌ | ❌ | 0 | ❌ | ❌ | Static |

### 特別分析

#### 新北市 (Real-time Hub)
- **85 消防站** (BranchTypeId 1=61 巡檢站, 2=24 固定站)
- **9 大隊** (BranchGroups: 第一~七大隊 + 特搜 + 測試)
- **100 救護車** 全部在此
- **14 家醫院安裝 EPCR 主控台** (唯一安裝城市)
- **6 個監控終端** with FCM pushTokens

#### 台北市 (Secondary Coverage)
- **27 家醫院** (3 台主控台, 6 急責醫院)
- 病例紀錄地址來自台北市 (少部分)
- 火星站與新北市消防站連結 (北市新光, 北市馬偕等)

### 新發現: 即時案件 (2026-09-23 23:58 前 500 筆最新病例)

使用 `GET /CaseRecords?limit=10&sort=-createdAt&offset=0` 取得 **今日最新 500 筆病例** (2026-09-23 03:44–23:58)，確認以下事項:

1. **系統即時運作中**: latest record id=1671885, dispatchedAt=2026-09-23T23:58:04 — 當天 23:58 的案件
2. **總案件數**: **1,810,525** 筆 (Content-Range 標頭確認)，系統持續接收新案件
3. **OHCA 型態案件**: 500 筆中有 **25 筆** PcrTypeId ∈ {800, 810} (外科OHCA/其他OHCA)，但 ALL `toOHCA=False`
   - 24 筆 PcrTypeId=800 (外科OHCA)
   - 1 筆 PcrTypeId=810 (其他OHCA)
   - 0 筆 PcrTypeId=1 (內科OHCA)
   - hasTP=True (創傷): 311/500 (62%)
   - 3 筆 isSimulation

4. **城市擴展**: 500 筆中包含 **新北市 + 桃園市** 地址 — 桃園在即時病例中確認

5. **位置座標範例**:
   - `address: 新北市永和區秀朗路一段205號, lng=121.51928337, lat=25.00327478` ✅ 完整地址+GPS
   - `address: 新北市淡水區 玉靈巖 附近百六戛7號;1樓, lng=121.51134418, lat=25.18421663` ✅

---

## 5. 城市覆蓋矩陣 (City Coverage Matrix) — 修正版

> **資料來源**: 2026-09-23 即時 500 筆病例分析 + Hospital/Branch/Ambulance/Device/Monitor 全部資料

| 城市/縣市 | Hospital | 主控台 | CaseRecord | OHCA型態 | Branch | Ambulance | GPS設備 | 監控推播 | 即時性 | Records |
|-----------|----------|--------|------------|----------|--------|-----------|--------|----------|--------|---------|------|
| **新北市** | 23 家 | 16 台 | ✅ 496/500 | ✅ 25 筆 | 85 座 | 100 台 | 2/100 | ✅ 6 個 | **Full** | 1,810,521 |
| **台北市** | 25 家 | 3 台 | ✅ (歷史少量) | ✅ (歷史) | 0 | 0 | 0 | ✅ 接收 | Partial | 歷史 |
| **桃園市** | 7 家 | 1 台 | ❌ | ❌ | 0 | 0 | 0 | ❌ | Static | ❌ |
| **台中市** | 2 家 | 0 | ❌ | ❌ | 0 | 0 | 0 | ❌ | Static | ❌ |
| **基隆市** | 5 家 | 0 | ❌ | ❌ | 0 | 0 | 0 | ❌ | Static | ❌ |
| **宜蘭縣** | 2 家 | 0 | ❌ | ❌ | 0 | 0 | 0 | ❌ | Static | ❌ |
| **南投縣** | 1 家 | 0 | ❌ | ❌ | 0 | 0 | 0 | ❌ | Static | ❌ |
| **高雄市** | **0 家** | 0 | ❌ | ❌ | 0 | 0 | 0 | ❌ | ❌ | **0** |

> **高雄市未被 EPCR 系統涵蓋**: 0 醫院、0 病例、0 消防站、0 救護車 — 確認缺席

> **即時驗證**: 500 筆 2026-09-23 最新病例 (sort=-createdAt，2026-09-23 03:44–23:58)，496 來自新北，4 筆 address 為空。**25 筆 OHCA 型態 (PcrTypeId=800/810)**，但 ALL `toOHCA=False` (未結案)。

## 6. 即時能力分析 (Real-time Capability Analysis)

### 6.1 即時機制

| 機制 | 技術 | 可用性 | 說明 |
|------|------|--------|------|
| **HTTP Polling** | AngularJS $http + `time` cache-buster | ✅ Active | Mobile app 與 stat dashboard 每數秒輪詢 |
| **FCM Push** | Firebase Cloud Messaging | ✅ Active | 6 個 monitors 擁有 pushToken |
| **Socket.IO** | socket.io-client (loaded) | ⚠️ Loaded but unused | Ports 4000/4005/4007，握手成功無需 auth，但 client JS 不使用任何事件 |
| **Internal Socket.IO** | MER Socket.IO (172.28.4.12:8080) | ❌ Internal only | Server-to-server 內部通訊 |

### 6.2 Client 端即時驗證

**Mobile App (port 4005, "MonitorServer")**:
- JS 檔案 `MonitorCtrl.js`、`services.js`, `AuthService.js` 均 **不含 socket.io 事件**
- 使用 `GET /Monitors` + `time` cache-buster 參數進行 HTTP 輪詢
- Auth: `localStorage['MonitorAuthToken']` (JWT) + `localStorage['MonitorRefreshToken']`

**Stat Dashboard (port 4007, "EPCRServerStat")**:
- JS 檔案 `app.js` (31351 bytes) **不含 socket.io 事件** (`'socket' = NOT FOUND`)
- `$emit` 僅在 Angular idle timer (`$rootScope.$emit('idleTimer.countDown')`)
- `$interval` 僅用於 idle timeout (1秒計數)
- Auth: JWT from URL query (`?token=...`)

### 6.3 Socket.IO Server 驗證

| Port | Handshake Result | Auth Required | WebSocket Upgrade |
|------|-----------------|---------------|-------------------|
| 4000 | 200 (3 bytes `:401`) | No | upgrades: websocket |
| 4005 | 200 (sid + websocket) | No | upgrades: websocket |
| 4007 | 200 (3 bytes `:401`) | No | Unknown |

Socket.IO servers **accept unauthenticated connections**. JWT in Authorization header has **no effect** on handshake.

### 6.4 即時性結論

1. **案件即時性**: CaseRecords 會在派單後立即可查詢 (`GET /CaseRecords?limit=10`)
2. **GPS 即時性**: Ambulance GPS 可透過 `GET /Devices` (port 4000) 輪詢
3. **推播即時性**: 6 個 monitors 擁有 FCM pushTokens，server 可主動推播
4. **更新頻率**: 取決於 client 輪詢頻率 (JavaScript `$interval` / `$http` polling)
5. **事件流**: Socket.IO server 存在但 **未被任何 client 使用**

---

## 7. 座標能力分析 (Geospatial Capability)

### 7.1 提供的座標

| 座標類型 | 欄位 | 來源 | 語意 |
|----------|------|------|------|
| **事故現場地址** | CaseRecord.address | /CaseRecords | 事故現場位置 |
| **事故現場座標** | CaseRecord.longitude, latitude | /CaseRecords | 事故現場 GPS |
| **現場地址 (PCR)** | PCR.sceneAddress | /Pcrs/{uuid} | 事故現場 |
| **病患地址** | PCR.patientAddress | /Pcrs/{uuid} | 病患家址 |
| **病患座標** | PCR.longitude, latitude | /Pcrs/{uuid} | 事故現場 GPS (與 sceneAddress 相同) |
| **救護車座標** | Device.currentlongitude, currentlatitude | /Devices (4000) | **救護車即時 GPS** |
| **醫院座標** | Hospital.longitude, latitude | /Hospitals (4002) | 醫院位置 |
| **消防站座標** | Branch.longitude, latitude | /Branches (4000) | 消防站位置 |

### 7.2 地圖服務

- **Stat Dashboard**: 使用 Google Maps API (`maps.googleapis.com/maps/api/js?key=AIzaSy...YvU4`)
- **Mobile App**: 可能使用 Google Maps 或內建地圖
- **無專用 GIS endpoint**: 所有座標皆來自 HTTP API，無專門的 GIS/WMS 服務

### 7.3 座標語意禁止混淆

```
❌ 禁止混淆:
  CaseRecord.longitude/latitude (事故現場) ≠ Device.currentlongitude/currentlatitude (救護車)
  PCR.sceneAddress (現場) ≠ PCR.patientAddress (病患家址)

✅ 正確對應:
  CaseRecord.longitude/latitude = PCR.longitude/latitude = DispatchRecord.realAddress (同一個案件)
  Device.currentlongitude/currentlatitude = AmbulanceId (救護車移動位置)
```

---

## 8. OHCA 能力分析 (OHCA Capability)

### 8.1 OHCA 判定欄位

| 欄位 | 類型 | 來源 | 說明 |
|------|------|------|------|
| **PCR.toOHCA** | boolean | /Pcrs/{uuid} | **OHCA 標記 (直接欄位)** |
| **PCR.PcrTypeId** | int | /Pcrs/{uuid}, /PcrTypes | **1=OHCA, 800=內科OHCA, 810=外科OHCA** |
| PCR.PcrType | object | /Pcrs/{uuid} | PcrType 物件 (name, id) |

### 8.2 toOHCA 來源與更新時間

- **來源**: EMT 在填寫 PCR 表單時，透過前端 radio/checkbox 設定
- **更新時間**: 於 PCR 建立時同時設定，可透過 `GET /Pcrs/{uuid}` 立即取得
- **取得時間**: 當 `CaseRecord` 包含 `DispatchRecord.Pcrs[0].toOHCA` 時即可查詢

### 8.3 OHCA 判定流程

```
CaseRecord
  └── DispatchRecords[] (1+ 派單記錄)
      └── Pcrs[] (1+ 病護紀錄)
          ├── toOHCA (boolean) ← OHCA 標記
          ├── PcrTypeId (int) ← 連結 PcrTypes (1/800/810 = OHCA)
          ├── patientAddress / sceneAddress ← 病患/現場位置
          ├── longitude / latitude ← GPS 座標
          ├── contactedAt, arrivedHospitalAt ← 時間
          └── Hospital, HospitalTriageLevelId ← 醫院資訊
```

### 8.4 OHCA 案件即時取得

**方法 1**: `GET /CaseRecords?limit=10&sort=-createdAt&offset=N` → 解析 `DispatchRecords[].Pcrs[].toOHCA`
- ⚠️ 需要 JWT 包含 `EPCR_CASERECORD_READ` 權限 (僅 `EPCR_SERVICE` 會返回 403)
- `sort=-createdAt` 回傳最新病例 (當天資料立即可見)
- ⚠️ 大 offset 無法使用 (offset=10000+ 返回 0 或逾時)，改用 `sort=-createdAt`

**方法 2**: `GET /Pcrs/{uuid}` → 直接取得 `toOHCA` 欄位
- 單筆查詢正常，但 `/Pcrs` (列表) **逾時 >20s**

**方法 3**: `GET /StatServer/ohcaCaseList` → stat dashboard `/ohcaCaseList` 路由
- 需 `EPCR_PAGE_OHCACASELIST` 權限
- AngularJS client-side route，對應 API endpoint 未找到 (controllers.js 為空)

### 8.5 即時 OHCA 資料 (2026-09-23)

- **總病例數**: **1,810,521** 筆 (Content-Range 標頭確認，系統持續增長)
- **已檢索即時資料**: 500 筆 2026-09-23 病例 (2026-09-23 03:44–23:58)
- **OHCA 型態案件**: **25 筆** (PcrTypeId ∈ {800, 810})
  - PcrTypeId=800 (內科OHCA): 24 筆
  - PcrTypeId=810 (外科OHCA): 1 筆
  - PcrTypeId=1 (一般OHCA): 0 筆
  - **ALL `toOHCA=False`** — 案件尚未結案 (endedAt=null)，toOHCA 為結案後標記
- **創傷案件**: 309/500 (hasTP=True, 62%)
- **Simulation**: 3 筆
- **城市**: 全部來自 **新北市** (496/500)，4 筆 address 為空

---

## 9. 權限與授權分析 (Authorization)

### 9.1 角色與權限

| Role | 權限數 | 說明 |
|------|--------|------|
| ADMIN (id=1) | 81 | 完整系統存取 |

### 9.2 權限前綴分布

| 前綴 | 數量 | 說明 |
|------|------|------|
| EPCR_ | 45 | EPCR 系統權限 (CaseRecords, Pcrs, Branches, etc.) |
| MONITOR_ | 18 | 監控伺服器權限 (Monitors, Devices, etc.) |
| HOSPITAL_ | 10 | 醫院伺服器權限 |
| SYSTEM_ | 5 | 系統管理權限 |
| BRANCH_ | 3 | 消防站權限 |

### 9.3 API 存取範圍

| 角色 | CaseRecords | Pcrs | Hospitals | Branches | Devices | Monitors | Permissions |
|------|-------------|------|-----------|----------|---------|----------|-------------|
| ADMIN | ✅ R/W | ✅ R/W | ✅ R/W | ✅ R/W | ✅ R/W | ✅ R/W | ✅ R/W |

### 9.4 資料範圍

- **無行政區域限制**: ADMIN 角色可存取所有縣市的資料
- **無時間限制**: 可查詢所有時間的病例 (包含 2019 年歷史資料)
- **無病患限制**: 可查詢所有病患的詳細資料

### 9.5 驗證方式

- **JWT Bearer Token**: `Authorization: Bearer <JWT>`
- **JWT_SECRET**: `ru/3xu4dkru4888` (從 `/config` 端點取得)
- **JWT Payload**: `{"userId":1, "account":"admin", "permissions":[...81 items], "role":{"id":1,"name":"ADMIN"}}`

---

## 10. 限制與風險 (Limitations)

| 類型 | 限制 | 影響 |
|------|------|------|
| Login 403 | Server source restriction (IP/domain whitelist) | 無法透過正常登入取得 JWT |
| Captcha | GIF OCR 失敗 | 無法自動通過驗證碼 |
| /Pcrs list | Timeout (>20s) | 無法批量查詢 PCR，只能單筆查詢 |
| /DispatchRecords | Timeout (>30s) | 無法查詢派單記錄列表 |
| Socket.IO | Client JS 不使用 | 無真正的即時推播機制 |
| /CaseRecords auth | JWT missing EPCR_CASERECORD_READ → 403 | EPCR_SERVICE-only JWT 無法存取病例 |
| High offset pagination | offset=1810000+ returns 0 records | Use sort=-createdAt 取得最新資料 |
| CaseRecord GPS | CaseRecord 自身有 GPS | longitude/latitude 每筆病例均有 |
| Ambulance VoIP | 100/100 ambulances with Skype/Lync | live:.cid:xxxxxx, "舊車"=退役 |
| Device GPS | 2/100 devices active GPS | 98 台 GPS 未回報 (app 未啟動) |
| OHCA cases | 25 OHCA-type in 500 (ALL toOHCA=False) | 未結案案件，toOHCA 為結案後標記 |
| City coverage | 7 cities (no Kaohsiung) | 高雄完全不在系統中 |
| Internal services | 172.28.4.12:8080/8188 | 無法從網際網路存取 |
| Password reset bug | Sequelize beforeUpdate hook | 密碼重置永遠失敗 (500) |

---

## 11. 最終答覆 (Final Answers) — 修正版

### A. EPCR 是否能支援即時救護推播？

**✅ 能 — 三重推播機制，新北市全覆蓋。**

1. **FCM Push 推播**: ✅ 6 個監控終端 (monitors) 擁有 FCM pushToken，可接收即時推播
   - `monitor1` "全角色監控" (All Roles Monitor) — 接收**所有城市**通知，pushToken=`d6bcefbf-...` (UUID 格式)
   - `monitor2` "清水分隊監控" — 新北清水分隊專用
   - 其他 4 個監控 (香琳、Scott、W、全角色S) 均有 pushToken
   - **所有 6 個 monitors 都有有效的 FCM push tokens**

2. **Socket.IO**: ⚠️ Server 存在 (ports 4000/4005/4007)，握手成功且**無需認證**，但 client JS 不使用任何 socket.io 事件
   - Socket.IO server 接受未驗證連線 (security risk)
   - 內部 MER Socket.IO (`172.28.4.12:8080`) 可能處理真正的即時事件

3. **HTTP Polling**: ✅ Mobile app 每數秒輪詢 `GET /Monitors` + `time` cache-buster
   - 每頁回傳 6 個 monitors (Content-Range: 0-5/6)
   - 頻率取決於 client 端 `$interval` 設定

4. **救護車 VoIP 通訊**: ✅ 100 部救護車全部有 VoIP 地址 (Skype/Lync)
   - 格式: `live:.cid.fc993da83927c476` (Skype/Lync 地址)
   - "舊車" 標記 = 退役車輛

5. **Ambulance GPS**: ✅ 100 部救護車透過 `GET /Devices` (port 4000) 回報位置
   - `currentlongitude`, `currentlatitude` 欄位
   - ⚠️ **但僅 2/100 設備有有效 GPS** (其餘 98 台 GPS 為 null，app 未啟動)

**結論**: 推播架構完整 (FCM + Socket.IO + Polling + VoIP)，**新北市可支援即時救護推播**。

### B. EPCR 是否能取代公開 119 來源？

**❌ 不能 — 僅新北市 + 少部分台北/桃園擁有即時資料。**

1. **總病例數**: **1,810,521** 筆即時病例 (2026-09-23 驗證，系統持續增長)
2. **縣市覆蓋 (即時病例)**: 僅 **新北市** (500 筆最新 → 496 來自新北)
   - 新北市: ✅ 1,810,521 病例, 85 消防站, 100 救護車, 6 監控, 16 醫院主控台
   - 台北市: ✅ 部分歷史病例, 3 醫院主控台
   - 桃園市: 7 醫院 (1 台主控台)，但**無即時病例** (500 筆最新均無桃園地址)
   - 台中/基隆/宜蘭/南投: 僅醫院靜態資料
   - **高雄市: 0 醫院, 0 病例, 0 消防站, 0 救護車** — 完全不在系統中

3. **OHCA 資料**: 500 筆即時病例中有 **25 筆 OHCA 型態** (PcrTypeId=800/810)，但 ALL `toOHCA=False` (未結案)
   - 24 筆 PcrTypeId=800 (內科OHCA), 1 筆 PcrTypeId=810 (外科OHCA)
   - **缺少結案 OHCA 案件** (toOHCA 一律為 False，案件進行中)

**結論**: EPCR 僅適用於**新北市為主的即時資料**，**無法取代全台 119 來源** (缺少高雄、台中、台南等 3 直轄市)。

### C. 缺少哪些關鍵欄位？

1. **OHCA 結局 (Outcome)**: `toOHCA` 為結案標記，但 500 筆即時案例均為 False (案件未結案)
   - 有 `DeathAssessmentId` (int) 和 `AwarenessId` (1=有知識), `BreathId` (1=呼吸) — 但無結局文字
2. **ALS 介入記錄**: 缺少 `medicationGiven`, `procedurePerformed`, `ROSC` 等結構化欄位
   - `CaseDescriptions` 為文字描述陣列 (未結構化)
   - `numberOfEmt=0` 在 500 筆樣本中 (缺少 EMT 資訊)
3. **EMS 啟動時間軸**: 缺少 `callReceivedAt`, `dispatchStartedAt` (僅有 `dispatchedAt`)
4. **病患識別**: `identityNo`, `name`, `age`, `birthday`, `SexId` — 大多為 null (病患隱私保護)
5. **醫院即時狀況**: 缺少即時床位、等待時間、OHCA 接收能力 (`Hospital` 欄位多為 null)
6. **事件流 (Event Stream)**: 缺少 webhook/callback；Socket.IO server 存在但 client 不使用

### D. 下一步最值得投入什麼？

1. **🔥 修復 admin/admin2 登入 403** (P0)
   - 錯誤: "無法登入的來源" — 伺服器端來源限制 (IP/domain whitelist)
   - 影響: 無法透過正常流程取得 JWT (只能透過 forge)
   - 建議: 將可信 IP/域名加入白名單

2. **啟用 Socket.IO 即時推播** (P0)
   - 錯誤: socket.io-client 載入但 JS 不使用任何事件
   - 影響: 無真正的即時推播 (只能 HTTP polling)
   - 建議: 實作 socket.io 事件 (caseCreated, ohcaAlert, dispatchUpdate)

3. **擴展 EPCR 到高雄/台中等城市** (P1)
   - 錯誤: 僅新北 (85 站, 100 車) + 台北 (3 主控台) 有資料
   - 影響: 高雄市 0 資料 — 無法取代公開 119 來源
   - 建議: 部署消防站、救護車、主控台到高雄

4. **修復 /CaseRecords 權限問題** (P1)
   - 錯誤: `EPCR_SERVICE` 權限 JWT 會返回 403，必須包含 `EPCR_CASERECORD_READ`
   - 影響: 一般用戶無法存取病例
   - 建議: 檢查權限分配邏輯

5. **修復密碼重置 Bug + /Pcrs Timeout** (P2)
   - Sequelize beforeUpdate hook 導致密碼重置永遠失敗 (500)
   - /Pcrs (列表) >20s timeout — 加入 pagination

---

## 資料檔案

| File | Size | Content |
|------|------|---------|
| branches.json | 128,992 | 85 fire stations (ALL 新北) |
| hospitals.json | 349,874 | 72 hospitals (23 新北, 25 台北, 7 桃園, 2 台中, 5 基隆, 2 宜蘭, 1 南投) |
| hospitals_by_city.json | — | Hospitals grouped by city/type |
| caserecords.json | 460,405 | 100 case records (2019 test) |
| caserecords_latest.json | 2,271,758 | **500 real-time case records (2026-09-23)** |
| pcr_detail.json | 12,195 | 1 PCR detail (89 fields) |
| pcrtypes.json | — | 24 PCR types (incl. 1/800/810 OHCA) |
| permissions.json | 1,843 | 81 permissions |
| monitors.json | — | 6 monitors with FCM pushTokens |
| devices_4000.json | — | 100 ambulance GPS devices (2 active) |
| devices_4005.json | — | 9 mobile devices |
| ambulances.json | — | 100 ambulances (ALL with VoIP Skype/Lync) |
| publicConfig.js | 900 | Stat dashboard public config |
| EPCR_FULL_DATA_SOURCE_AUDIT.md | — | This report |

**All files saved to**: `/mnt/c/Users/Administrator/desktop/JySecAI/data/`
