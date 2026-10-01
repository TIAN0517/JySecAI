# POC/EXP — 4004 AuthServer /login 端点对所有输入返回 500 TypeError（登录不可用）

> 漏洞ID: `5a8242b3-59b2-494e-8bc0-99035392d5f4`  | 嚴重度: **high** | 狀態: open | 目標: `https://epcr.tpf.gov.tw:4004/login`

**類型**: 可用性/服务端错误

## 描述

4004 AuthServer 的 /login 端点对所有 POST 输入（含有效 captcha 会话 connect.sid cookie）均返回 HTTP 500，响应体为 "TypeError"（11B）。这表明登录流程在服务端存在未捕获的 TypeError（可能因用户查询、密码比对或 token 生成环节引用了 undefined），导致认证功能对所有用户不可用（可用性缺陷）。同时 /refreshToken、/ssoLogin 等认证相关端点未鉴权即可探测，泄露服务端错误信息。

## POC / 復現步驟

```
# 1. 取得有效 captcha 会话
curl -sS -k -c /tmp/cj.txt "https://epcr.tpf.gov.tw:4004/captcha"  # 17646B GIF, 设置 connect.sid
# 2. 带有效会话 POST /login
curl -sS -k -b /tmp/cj.txt -X POST "https://epcr.tpf.gov.tw:4004/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","captcha":"1234"}'
# 输出: HTTP 500, body = "TypeError" (11B)
# 无会话时同样 500 "TypeError"。所有 username/password/captcha 组合均 500。
# 对照: /ssoLogin 返回 403 "無法辨識使用者"，/refreshToken 返回 400 "Invalid refresh token"，均正常处理。
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
