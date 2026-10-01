## OHCA 資料結論 - 最終報告

### 問題: 系統會輸入 OHCA 資料嗎?

**答案: ❌ 不會**

### 調查方法
1. GET /Login → 取得 session cookies (ASP.NET_SessionId + DisaRescue)
2. 進入所有可存取的頁面並提取表單欄位:
   - `/Dispatch/CaseUnitMgt.aspx` (案件派遣) — 即時案件列表
   - `/Drafting/CaseEdit` (案件編輯 + 點擊編輯按鈕進入案件詳細編輯表單)
   - `/IPS_v3/ViewMgt.aspx` (人員定位) — 即時 GPS 定位
   - `/IPS_v3/VPathMgt.aspx` (人員路徙) — 人員軌跡
   - `/Common/JsonData.ashx` — AJAX JSON API (測試多種參數均返回空)

### 所有可存取的表單欄位

**案件派遣 (CaseUnitMgt):**
- 案號 (案件編號)
- 案件日期
- 地點 (地址)
- 派遣單位
- 狀態 (處理中 / 未結案 / 已結案)
- 最後修改時間

**案件編輯 (CaseEdit) 編輯模式:**
- 案件編號 (TB_CaseNo)
- 地址 (TB_Addr)
- 樓層
- 樓層備註
- 底圖類型 (RB_BmapType_Img / RB_BmapType_Svg)
- 上傳圖檔
- 線上繪圖
- HF_Lat / HF_Lng (地圖座標)
- Btn_Save / Btn_Qry

**人員定位 / 路徙:**
- 日期範圍 (Txt_ApplyDtS / Txt_ApplyDtE)
- 單位 (DDL_UnitId)
- 狀態 (DDL_Status)
- 查詢 (Btn_Qry)

### OHCA/Medical 搜尋結果
- `心臟`, `驪停`, `ohca`, `cardiac`, `病人`, `患者`, `呼吸`, `除顫`, `診斷`, `症狀`, `病房`, `心電`, `心跳`, `病史`, `過敏`, `藥物`, `病人姓名`, `身分證`, `聯絡人` → **0 hits**
- `icu`, `aed` → **2 hits / 1 hit** 皆為 base64 圖片二進位資料 (false positive)
- `/Common/JsonData.ashx` POST with 10+ parameter combos → all **empty (len=0)**

### 分析
此系統為**消防派達 + GPS 定位系統**，資料模型僅包含:
- 事件地址 (現場地址，非病人家庭地址)
- 派遣單位 (含救護大隊 9 個子分隊)
- 案件狀態
- 地圖座標 / 樓層資訊

**無病患醫療資料欄位** — OHCA 的病患醫療資訊 (心臟驪停類型、病患狀況、除顫次數、急救過程) 屬於獨立的 **EMS Patient Care Report (PCR) 系統**，不在此消防派遣介面。

### 已找到的即時資料 (Real-time Data)
- **2 筆活躍案件** (案號結構: YYYYMMDDHHMMSS+序號)
  - `20260929235312003` — 臺北市萬華區華西街14號2樓 → 4 個EMS單位
  - `20260929233719002` — 臺北市萬華區萬大路533號 → 中正中隊
- **即時 GPS 定位**: 人員定位 + 人員路徙頁面有 setInterval 自動刷新
