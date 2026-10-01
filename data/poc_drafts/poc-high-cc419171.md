# POC/EXP — 3400 tokenGetter URL 参数注入实测：访问 http://35.234.50.28:3400/?token=<伪造 JWT> → 客户端自动写入 localStorage[AUTH_LOCALSTORAGE_KEY] → 后续 3400 API 调用自动附加此 token — 实战可注入任意伪造 HS256 JWT（含算法 none）

> 漏洞ID: `cc419171-a613-47f9-a9d7-b324248c3f46`  | 嚴重度: **high** | 狀態: open | 目標: ``

**類型**: exploit

## 描述

由项目事实 exploit/3400-tokengetter-localstorage-injection-poc 生成

## POC / 復現步驟

(記錄中無復現步驟,需人工補全)

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
