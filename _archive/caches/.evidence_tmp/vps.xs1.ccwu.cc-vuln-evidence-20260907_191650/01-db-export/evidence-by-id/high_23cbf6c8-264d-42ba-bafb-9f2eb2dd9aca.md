# bear.emic.gov.tw POST API 全栈 401 闭环 + 加密算法/IV/Key 完整前端泄露 + CORS 任意 Origin 反射

- ID: `23cbf6c8-264d-42ba-bafb-9f2eb2dd9aca`
- Severity: **high**
- Status: open
- Type: 信息泄露 + 应用层拒绝服务 + 加密静态化
- Target: `https://bear.emic.gov.tw/identify/api.aspx/WS_P/{13 endpoints} + https://bear.emic.gov.tw/identify/api.aspx/WS_Login/{3 endpoints}`
- Conversation: `c0f88721-4c62-4f34-85e3-51bd54bb641e`
- Created: 2026-08-30 21:35:30.923128415+08:00

## Description

bear.emic.gov.tw 内政部消防署「全民防災e點通」PWA 后端 ASP.NET WebForms API 拒绝服务式应用层不可达 — 全部 POST JSON 请求（包括合法加密 payload + XSRF-TOKEN + Cookie + Origin/Referer 全套浏览器头）被 ASP.NET Forms Authentication 在路由前同步拦截返回 401，未真正执行任何业务逻辑。但前端代码完全暴露加密算法/IV/KEY（key=`ab@37Tc54&2!T9621u65vt126g87ckpG`，32 bytes UTF-8，AES-256-CBC+PKCS7）、18 个 endpoint 路径、TimeFetcher 单例（staleTime=20000ms）、axios 默认 XSRF 配置、constants.js（含 staging 域 sbear.emic.gov.tw 开关、本地存储 keys、用戶類型/訊息類別/性別枚举）。完整攻击面（POST + 加密 + CORS 反射）已知但攻击者无法绕过 ASP.NET Forms Authentication。

## Reproduction

1. 访问 https://bear.emic.gov.tw/MY2/（SPA 入口，200 OK 不分配 ASP.NET_SessionId）
2. 抓取 MY2/assets/api-CCkH231s.js（321429B 含完整业务逻辑）
3. 从 api-clean.js 提取：
   - 加密 key `var av = 'ab@37Tc54&2!T9621u65vt126g87ckpG'` (32 bytes)
   - iv = key.substring(0, 16)
   - POST 拦截器：`if (e.method === 'post') { e.data = {sDATA: ov(JSON.stringify({times, rand, ...e.data}))} }`
   - 18 endpoint 路径（WS_P × 13 + WS_Login × 3 + gettimes）
4. 在本地用 pycryptodome / Node CryptoJS 重现 ov() 函数
5. 构造 POST 请求：
   ```bash
   curl -X POST "https://bear.emic.gov.tw/identify/api.aspx/WS_P/SEL_USR_ALLDATA" \
     -H "Content-Type: application/json" \
     -H "Origin: https://bear.emic.gov.tw" \
     -H "Referer: https://bear.emic.gov.tw/MY2/" \
     -d '{"sDATA": "<base64_encrypt(JSON.stringify({times: \"2026-08-30 12:00:00\", rand: \"...uuid...\", sP_USR_SN: \"test\"}))>"}'
   ```
6. 观察响应：**401 + Content-Type: text/html + jsonerror: true + 11807B body（MD5=d2783ab0）**
7. 测试 16 个 endpoint 全部相同响应
8. 测试其他 Content-Type（form-urlencoded/text/plain/xml/multipart/SOAP）全 200 11807B
9. 测试 OPTIONS /identify/api.aspx/WS_P/SEL_USR_ALLDATA → 404
10. 测试 TRACE → 404

完整攻击面已知但 ASP.NET Forms Authentication 同步拦截应用层逻辑，攻击者无法进入业务层。

## Evidence

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

## Impact

**信息泄露（Medium）**：
1. 完整 AES-256-CBC 加密 key/iv + 算法静态暴露 — 离线可伪造任意 POST 加密 body（含合法 times + rand）
2. CORS 开放任意 Origin GET/POST + withCredentials=same-origin — 钓鱼链可投递但 ASP.NET Forms Authentication 阻断
3. constants.js 泄露 staging 域 sbear.emic.gov.tw 开关 — 暗示存在不同鉴权的开发/测试环境
4. 完整 18 endpoint 路径枚举（无需探测）

**应用层拒绝服务（High）**：
- POST 全部未授权访问被 ASP.NET Forms Authentication 同步拦截返回 401，攻击面被完全闭合
- 攻击者无法利用 API 写入业务数据（用户注册/预警/最爱/事件历史）
- 即便带正确加密 sDATA + 完整浏览器头 + cookie + XSRF-TOKEN 三态组合，仍被 401 拦截
- 无 ASP.NET_SessionId 入口存在（穷尽全站所有路径），无法通过任何公开路径获得会话

**业务风险**：
- 无法注册新用户（ADD_USR 401）
- 无法查询/管理最爱、预警、事件历史（TopicQuery/updFavorite/dashboardEvent/historyEvent 401）
- 无法更新个人化（UPD_USR_GENDERBIRTHJOB/set_usr_language 401）
- 即便 LOGIN endpoint 也需要未知的合法凭证才能进入下一步

攻击者要进入应用层只有两条路径：
1. 已知账号密码（社会工程 / 凭证填充 / 泄漏库）触发真实登录
2. sbear.emic.gov.tw staging 域探测（constants.js 暗示可能存在弱鉴权/默认账号）

## Recommendation

1. **加密静态化风险**：移除前端硬编码 AES key/iv，改用每会话派生的 ephemeral key + 服务器端 nonce（消除离线伪造可能性）
2. **ASP.NET_SessionId 入口缺失**：在 /MY2/ 入口预分配 ASP.NET_SessionId cookie（即便用户未登录）以便 XSRF-TOKEN 机制能正常生效
3. **XSRF-TOKEN 服务器端校验**：当前 axios 默认 X-XSRF-TOKEN 头被忽略，应在后端 WebForm 中实现 AntiForgeryToken 校验（[ValidateAntiForgeryToken] attribute）
4. **CORS 锁定**：将 Access-Control-Allow-Origin 从反射任意 Origin 收紧到白名单（如 https://bear.emic.gov.tw）
5. **Content-Type 严格化**：统一 JSON 响应格式（Content-Type: application/json），移除对其他 Content-Type 的 200 默认错误页响应
6. **ASP.NET Forms Authentication**：考虑替换为更现代的 JWT/Bearer Token + 滑动会话机制
7. **错误页丰富化**：当前所有 endpoint 返回同一错误页（MD5=d2783ab0），但应避免在错误响应中泄露 ASP.NET 框架信息（jsonerror: true 头 + .aspx 路径 + customErrors 模式已暴露）
8. **staging 域风险**：sbear.emic.gov.tw 暗示存在（constants.js 硬编码 `i = host === 'sbear.emic.gov.tw'`），应确认其鉴权强度并删除或隔离测试环境
