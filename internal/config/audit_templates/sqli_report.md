---
name: SQLi Report Template
description: Template for SQL Injection vulnerability reports in SRC format
category: injection
severity: critical
trigger: User input executed as part of SQL query
---

# SQL Injection Vulnerability Report

## 1. 漏洞概述
- 漏洞類型：SQL Injection (SQLi)
- 業務影響：資料庫讀寫、認證繞過、潛在 DB 檔案寫入導致 RCE

## 2. 漏洞證明

### 2.1 環境
- 目標：`https://target-app.com/search`，參數 `q`
- 資料庫：MySQL 5.7

### 2.2 漏洞鏈路
```
1. 輸入 ' OR 1=1 -- → 回傳全量結果（注入成立）
2. UNION SELECT 探欄位數與顯示位
3. information_schema 讀表名 → 指向 users 表
```

### 2.3 取證紀律（對照 src-hunter 紅線）
- 拿到資料庫名/版本/表名即停
- 僅讀 1–3 條樣本證明可達，禁止 dump 全表
- 禁止 file_priv 寫檔、禁止 stacking 改資料

### 2.4 預期 vs 實際
- 預期：輸入被參數化，payload 無效
- 實際：payload 進入 SQL 語法，可控查詢邏輯

## 3. 漏洞成因
用戶輸入字串拼接進 SQL；未使用 Prepared Statement；錯誤訊息回顯資料庫結構。

## 4. 修復建議
```go
// 修復：一律參數化查詢
rows, err := db.Query("SELECT * FROM products WHERE name LIKE ?", "%"+keyword+"%")
```
輔以最小權限 DB 帳號、關閉詳細錯誤回顯。

## 5. 評分與對照
- CVSS: 9.1 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N)
- OWASP: A03:2021 Injection；CWE-89
- src-hunter-skill 底層案例：SQLi 335 例

## 6. 復驗步驟
1. 重放 payload 確認無注入回顯
2. 確認時間盲注/布林盲注亦失效

## 7. HITL 審計規則
- 常規速率的注入探測 payload 屬 approve 範圍（audit_agent_prompt「必須 approve」清單）
- 任何 DROP/TRUNCATE/DELETE 全表操作 → 必須 reject
