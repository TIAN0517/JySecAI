# POC/EXP — S0 Critical: 3400 /config JWT_PASSWORD=ru/3xu4dkru4888 硬编码泄露 → 本地伪造 admin JWT 

> 漏洞ID: `5603db94-b7fe-4fbd-be66-6d5acba20d45`  | 嚴重度: **high** | 狀態: open | 目標: ``

**類型**: exploit

## 描述

由项目事实 exploit/3400-jwt-password-leaked-full-takeover 生成

## POC / 復現步驟

(記錄中無復現步驟,需人工補全)

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
