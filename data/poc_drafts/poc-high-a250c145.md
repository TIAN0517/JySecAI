# POC/EXP — 真實病歷 CaseID=180817092350fed7 已被注入污染事件 id=567232 Systolic=999（臨床決策數據已遭竄改），GET /events?CaseID=180817092350fed7 直接返回該污染事件與真實事件混雜

> 漏洞ID: `a250c145-2122-474b-ad20-0e1dfc691c83`  | 嚴重度: **high** | 狀態: open | 目標: ``

**類型**: exploit

## 描述

由项目事实 exploit/clinical-data-tampering-verified 生成

## POC / 復現步驟

(記錄中無復現步驟,需人工補全)

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
