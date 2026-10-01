# 新北 119 推播

所有來源（EPCR / E1）都走同一套出勤通報模板，不輸出「來源：E1」、案號或裸座標。

**主源**：EPCR `GET /DispatchRecords` StatusId **5/6**（已派遣／已出動＝剛接案）。MonitorCtrl 是每 10 秒拉這支 REST，不是聽 socket。  
要帳號：`EPCR_USER` / `EPCR_PASSWORD`。登入走 captcha OCR（`python3 -m epcr login`），之後 `refreshToken` 在到期前 180 秒續期。續期 HTTP 400 就停，等重新 login 寫入 `data/tokens.json`，不要每 10 秒刷死 token。

**備援**（沒有活 JWT 時才走）：E1 `https://e1.ntpc.gov.tw/v3/api/map/dynamic/layer/rescue` 推 `Ambulance` / `AmbulanceBack`（有車在跑；門牌弱）。EMIC 378 預設關閉（KML 已停在 8/19，不能當這一分鐘主源）。

emic-push 的 `NTPC_E1_ENABLED=0`，改由本服務 `erpc.service` 推：

- 客戶：`cust_ntpc_spacex_0010`（新北）
- 鏡像：試車群 `@JyTian_bot` `-1004487319117`
- 已刪：`cust_ntpc_jytian`

| | |
|--|--|
| 單位 | 新北市政府消防局 智慧雲端動態救護系統 |
| 主服務 | `https://epcr.tpf.gov.tw:4000` |
| 監控 | `https://epcr.tpf.gov.tw:4005` |
| 版本 | 1.6.26080 |
| 代理 | SOCKS5（見 `.env` `EPCR_PROXY`） |

```bash
# .env 填 EPCR_USER / EPCR_PASSWORD（只給明確 login 用，run 不會空轉 OCR）
python3 -m epcr login             # OCR 解 captcha，寫 data/tokens.json
python3 -m epcr token             # 看 JWT 剩餘秒數（不登入）
EPCR_DRY_RUN=1 python3 -m epcr run
# systemd: erpc.service
```

同一 `caseNo` 內容沒變不重推。預設只推新北地址（`EPCR_NTPC_ONLY=1`）。出發卡不把跨縣市醫院當現場。

## 連線

推播**不要**綁 Socket.IO。先前 listen 30 秒 websocket 0 筆 42 event，xhr-polling 30 秒被 CLOSE。

1. 有活 JWT：每 10 秒 `GET /DispatchRecords?StatusId[$in][0]=5&StatusId[$in][1]=6`
2. 沒 JWT：`DispatchRecords` / `listCoords` = 401 → 改拉 E1（正文仍走同一模板）
3. `tokens.json` 一寫入且 JWT 未過期：下一輪切回 EPCR 主源

## 推播格式

```
【119 出勤通報】
案件類別：緊急救護・後送
派遣時間：2026/08/28 09:50:43
車號描述：重陽93（專責救護車）
案件地址：新北市…區…路…號
```

按鈕列：`📋 一鍵複製地址`　`🗺️ 案發地圖`（座標只在地圖 URL）。`disable_web_page_preview=true`。
