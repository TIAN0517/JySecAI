# POC/EXP — 4004 POST /ssoLogin 端點暴露單點登錄認證邏輯（無需認證）

> 漏洞ID: `f70ce4a0-868b-4a92-9117-b7a7f331e828`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/ssoLogin`

**類型**: 認證系統信息洩露

## 描述

4004 認證系統的 POST /ssoLogin 端點接受任意 sessionId 輸入並響應，明確區分「無效格式」(400) 與「無效用戶」(403)。雖然 JWT 認證攻擊失敗，但這個端點暴露了單點登錄的邏輯入口，且接受 NoSQL 操作符和 JWT 格式字符串，可能被用於認證旁路或會話固定攻擊。

## 前置條件

無需認證。直接訪問 https://epcr.tpf.gov.tw:4004/ssoLogin 即可。

## POC / 復現步驟

```
**測試結果**：
- POST /ssoLogin `{"sessionId":""}` → 400 "invalid sessionId"（純文本）
- POST /ssoLogin `{}` → 400 "invalid sessionId"
- POST /ssoLogin `{"sessionId":null}` → 400 "invalid sessionId"
- POST /ssoLogin `{"sessionId":"abc123"}` → 403 `{"name":"ErrorWithStatusCode","message":"無法辨識使用者","code":403}`
- POST /ssoLogin `{"sessionId":"eyJ.eyJ.sig"}` → 403 同上（JWT-like）
- POST /ssoLogin `{"sessionId":{"$ne":1}}` → 403 同上（NoSQL 嵌套）
- POST /ssoLogin `{"sessionId":["a","b"]}` → 403 同上（數組）

**其他端點對照**：
- POST /login → 500 "TypeError"
- POST /refreshToken → 400 "Invalid refresh token"
- POST /Activities/logoutRecord → 401 "No authorization token was found"

**源碼確認**：AuthService.js 第 73-83 行明確包含 ssoLogin(sessionId) 函數。

**重要**：這是除 /login 外**唯一**接受任意輸入並返回業務邏輯錯誤的端點，暴露了認證系統的內部結構。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
