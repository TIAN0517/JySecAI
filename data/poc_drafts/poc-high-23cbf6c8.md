# POC/EXP — bear.emic.gov.tw POST API 全栈 401 闭环 + 加密算法/IV/Key 完整前端泄露 + CORS 任意 Origin 反射

> 漏洞ID: `23cbf6c8-264d-42ba-bafb-9f2eb2dd9aca`  | 嚴重度: **high** | 狀態: open | 目標: `https://bear.emic.gov.tw/identify/api.aspx/WS_P/{13 endpoints} + https://bear.emic.gov.tw/identify/api.aspx/WS_Login/{3 endpoints}`

**類型**: 信息泄露 + 应用层拒绝服务 + 加密静态化

## 描述

bear.emic.gov.tw 内政部消防署「全民防災e點通」PWA 后端 ASP.NET WebForms API 拒绝服务式应用层不可达 — 全部 POST JSON 请求（包括合法加密 payload + XSRF-TOKEN + Cookie + Origin/Referer 全套浏览器头）被 ASP.NET Forms Authentication 在路由前同步拦截返回 401，未真正执行任何业务逻辑。但前端代码完全暴露加密算法/IV/KEY（key=`ab@37Tc54&2!T9621u65vt126g87ckpG`，32 bytes UTF-8，AES-256-CBC+PKCS7）、18 个 endpoint 路径、TimeFetcher 单例（staleTime=20000ms）、axios 默认 XSRF 配置、constants.js（含 staging 域 sbear.emic.gov.tw 开关、本地存储 keys、用戶類型/訊息類別/性別枚举）。完整攻击面（POST + 加密 + CORS 反射）已知但攻击者无法绕过 ASP.NET Forms Authentication。

## POC / 復現步驟

```
关键证据：
1. 完整 16 endpoint POST 矩阵：WS_P/{ADD_ALERT, DEL_LOCATION_ALERT, SEL_ALERT, TopicQuery, updFavorite, SEL_USR_ALLDATA, UPD_USR_GENDERBIRTHJOB, set_usr_language, ADD_USR, DEL_USR, LOGINOUT, dashboardEvent, historyEvent} + WS_Login/{LOGINUP, DOUBLE_VERIFY, LOGIN}
2. 所有 endpoint 响应 401 + Content-Type: text/html + jsonerror: true 头 + 11807B body，**唯一 MD5 = d2783ab0**
3. Content-Type 矩阵：仅 application/json 触发 401；form-urlencoded/text/plain/application/xml/multipart/SOAP 全 200 (11807B 默认错误页)
4. 加密算法 + key/iv 完整提取：`av = 'ab@37Tc54&2!T9621u65vt126g87ckpG'`，iv = 前 16 字节，CryptoJS AES-256-CBC + PKCS7 + base64(Hex)
5. TimeFetcher staleTime=20000ms 完整逆向，crypto.randomUUID() 防重放
6. 时序测试：POST-JSON 168.8ms vs GET 185.6ms — 同步拦截
7. 全站无 ASP.NET_SessionId 下发：/, /MY/, /MY2/, /err.html, /identify/, /identify/api.aspx, /Account/Login.aspx, /admin, /login, /index.aspx, /default.aspx, /elmah.axd 全不分配
8. XSRF-TOKEN 三态测试全 401：无 XSRF / 仅 cookie+header / 仅 header
9. Cookie 解锁测试全 401：sP_USR_SN=test, Vt=test, AntiForgeryToken=test, ASP.NET_SessionId=test123
10. OPTIONS /identify/api.aspx/WS_P/{SEL_USR_ALLDATA, LOGIN, ADD_USR} 全 404（IIS ASPX handler 不支持 OPTIONS method）
11. CORS 反射（Access-Control-Allow-Origin: <Origin>）已确认但 ASP.NET Forms Authentication 在路由前拦截
12. constants-BsMEeloe.js 完整解析：含 staging 域开关、localStorage keys、用戶類型/訊息類別/性別枚举
```

---

## 驗證要點

- [ ] 僅在授權範圍內驗證
- [ ] 最小化請求逐步驗證,留存原始請求/回應
- [ ] 失敗需記錄負結果,避免誤報
- [ ] 未實際驗證前狀態不得改為 confirmed

> 本文件由 JySecAI 自動生成,狀態:**草稿(未驗證)**
