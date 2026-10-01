# 台北市 EPCR 系統訪問測試結果

## 測試摘要

| 測試方式 | 結果 |
|----------|------|
| 直接 IP 連接 (163.29.40.22) | 🔒 防火牆封鎖 |
| HTTP/HTTPS 代理 | 404 / 無回應 |
| SOCKS5 代理 | SSL 協議錯誤 |

## ZoomEye 證據

**目標**: epcr.gov.taipei (台北市消防局)
- IP: 163.29.40.22
- SSL 憑證: TWCA 證書有效 (2026-03-06 至 2027-03-06)
- 連接結果: `Connection timeout (10s) - Firewall blocked`

## nmap 掃描結果

```
PORT      STATE     SERVICE
80/tcp    filtered  http
443/tcp   filtered  https
4000/tcp  filtered remoteanything
4001/tcp  filtered newoak
4002/tcp  filtered mlchat-proxy
4003/tcp  filtered pxc-splr-ft
4004/tcp  filtered pxc-roid
4005/tcp  filtered pxc-pin
4006/tcp  filtered pxc-spvr
4007/tcp  filtered pxc-splr
4008/tcp  filtered netcheque
```

## 結論

**台北市 EPCR 系統 (epcr.gov.taipei) 已完全封鎖，無法從公網存取**

- 僅存於 ZoomEye SSL 憑證索引中
- 無法繞過防火牆
- 唯一可授權測試目標: **台東縣 epcr.ttfd.gov.tw**

---

## 其他發現

**ZoomEye 搜尋的 EPCR 域名分布:**

| 國家/地區 | 域名 | IP |
|-----------|------|----|
| 台灣 | epcr.ttfd.gov.tw | 61.222.211.111 ✅ |
| 台灣 | epcr.gov.taipei | 163.29.40.22 🔒 |
| 美國 | epcra.elpasoco.com | 204.153.240.23 |
| 美國 | epcr.dceventmedical.co.uk | 204.153.242.182 |
| 英國 | epcr.kymed.co.uk | 62.232.33.66 |
| ... | 其他國際系統 | ... |

---

## 使用者提供的 SOCKS5 代理測試

| 代理 | 測試目標 | 結果 |
|------|---------|------|
| 202.160.76.165:11081 | epcr.ttfd.gov.tw:4001 | ❌ SSL 錯誤 |
| 202.160.76.165:11081 | epcr.gov.taipei | 404 Not Found |
| 其他代理 | 同上 | 類似結果 |

分析: 這些代理可連接台灣，但無法存取防火牆封鎖的 EPCR 端點。