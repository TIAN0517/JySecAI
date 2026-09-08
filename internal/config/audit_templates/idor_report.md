---
name: IDOR Report Template
description: Template for IDOR vulnerability reports in SRC format
category: access_control
severity: high
trigger: User can access resources belonging to other users via IDOR
---

# IDOR Vulnerability Report

## 1. 漏洞概述
- 漏洞類型：IDOR (Insecure Direct Object Reference)
- 影響範圍：用戶可透過操縱物件 ID 存取他人資料
- 業務影響：跨用戶資料洩露、隱私違規

## 2. 漏洞證明

### 2.1 環境
- 目標：`https://target-app.com`
- 帳號 A：`user_a` (id: 101)；帳號 B：`user_b` (id: 102)
- 受保護資源：`/api/users/{id}/profile`

### 2.2 漏洞鏈路
```
1. 登入 A，存取 /api/users/101/profile → 200（自己的資料）
2. 改 ID 為 102 → /api/users/102/profile → 200（漏洞成立）
3. 續測 103/104 確認可遍歷
```

### 2.3 PoC
```http
GET /api/users/102/profile HTTP/1.1
Host: target-app.com
Cookie: session=<A 的有效 session>
```

### 2.4 預期 vs 實際
- 預期：403 或僅回傳 A 自己的資料
- 實際：回傳 B 的完整個人資料

## 3. 漏洞成因
後端直接用用戶提交的 ID 查詢資料庫，未校驗「當前登入用戶 == 目標 ID」；依賴前端做存取控制。

## 4. 修復建議
```go
// 修復：服務端強制校驗物件所有權
if currentUserID != requestedID {
    http.Error(w, "Forbidden", http.StatusForbidden)
    return
}
```
優先使用不透明 ID（UUID）＋服務端所有權檢查，而非僅隱藏序號。

## 5. 評分與對照
- CVSS: 5.3 (CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N)
- OWASP: A01:2021 Broken Access Control；CWE-639
- src-hunter-skill 底層案例：IDOR 465 例

## 6. 復驗步驟
1. 建立兩個新測試帳號分別登入
2. 互換 ID 存取 → 應回 403
3. 修復未生效則漏洞仍存在

## 7. HITL 審計規則
- 命中 `get_user_by_id`/`query_user` 類工具且無所有權校驗 → 按 config.yaml `audit_agent_prompt` 判定
- 取證紀律：拉 1–3 條樣本即停，不得全表遍歷（對照 src-hunter 紅線規則）
