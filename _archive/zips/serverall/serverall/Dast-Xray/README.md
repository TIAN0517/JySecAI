> 随着敏捷开发和 CI/CD 的广泛应用，传统的人工渗透测试已经难以满足快速迭代的 Web 应用安全需求。动态应用安全测试（DAST）因此成为保障运行时安全的重要手段。本文将对比几款主流开源 DAST 工具，并介绍 **Xray-web**，展示它如何通过 Web 面板和 API 无缝融入 CI/CD 流程，实现自动化安全扫描。
>

  市面上有不少开源 DAST 工具，例如 **OWASP ZAP**、**Wapiti**、**Arachni** 等，它们在漏洞扫描能力上各有优势，但在自动化集成和可视化管理方面仍存在不足。闭源的如果使用商业版，则会增加法律合规风险，为了更好地支持快速迭代的开发流程，以及扫描器图形化， **Xray-web **应孕而生 ——一个基于 **Xray + CrawlerGo** 的 Web 面板，提供统一的扫描管理界面，同时通过 API 与 CI/CD 流程对接，实现自动化安全扫描和报告生成。




**Docker：**[**https://github.com/7uup/Dast-Xray-docker**](https://github.com/7uup/Dast-Xray-docker)**  (linux-amd64)**

**后端源码：**[**https://github.com/7uup/Dast-Xray**](https://github.com/7uup/Dast-Xray)

**前端源码：**[**https://github.com/7uup/Dast-Xray-web**](https://github.com/7uup/Dast-Xray-web)



## 一、主流开源 DAST 工具对比
| 工具 | 主要功能 | 优点 | 局限性 |
| --- | --- | --- | --- |
| **OWASP ZAP** | Web 漏洞扫描、API 扫描 | 活跃社区、规则丰富、可扩展 | 爬虫深度有限，动态页面抓取能力不足 |
| **Wapiti** | 扫描表单、参数漏洞 | 轻量、易用 | 不支持 JS 渲染页面，漏扫率低 |
| **Arachni** | 高级漏洞扫描 | 多线程、可生成报告 | 停止维护，缺少 CI/CD 集成方案 |
| **Xray + CrawlerGo** | 漏洞扫描 + 高级爬虫 | 覆盖全站、支持 JS 渲染 | 需要额外部署爬虫组件 |


从对比表可以看出，传统开源 DAST 工具的核心问题在于爬虫能力不足，无法全面覆盖现代 Web 应用。





## 二、开源 DAST 爬虫的局限性
大多数开源 DAST 工具自带爬虫，但存在明显问题：

1. **深度受限**：默认只抓取浅层链接，容易遗漏深层接口或隐藏页面。
2. **动态页面漏扫**：现代 Web 广泛使用 JavaScript 渲染内容，传统爬虫无法处理 SPA 或 AJAX 请求。
3. **参数覆盖不足**：表单、API 请求的参数组合较少，未能全面触发业务逻辑。



## 三、CrawlerGo + Xray 的组合优势
### <font style="color:rgb(255, 255, 255);background-color:rgb(33, 33, 34);">xray简介</font>
xray 是一款功能强大的安全评估工具，由多名经验丰富的一线安全从业者呕心打造而成，主要特性有:

+ <font style="color:rgb(1, 1, 1);">检测速度快,包速度快; 漏洞检测算法高效。</font>
+ <font style="color:rgb(1, 1, 1);">支持范围广,大至 OWASP Top 10 通用漏洞检测，小至各种 CMS 框架 POC，均可以支持。</font>
+ <font style="color:rgb(1, 1, 1);">代码质量高,编写代码的人员素质高, 通过 Code Review、单元测试、集成测试等多层验证来提高代码可靠性。</font>
+ <font style="color:rgb(1, 1, 1);">高级可定制,通过配置文件暴露了引擎的各种参数，通过修改配置文件可以极大的客制化功能。</font>
+ <font style="color:rgb(1, 1, 1);">安全无威胁,xray 定位为一款安全辅助评估工具，而不是攻击工具，内置的所有 payload 和 poc 均为无害化检查。</font>

目前支持的漏洞检测类型包括:

+ <font style="color:rgb(1, 1, 1);">XSS漏洞检测 (key: xss)</font>
+ <font style="color:rgb(1, 1, 1);">SQL 注入检测 (key: sqldet)</font>
+ <font style="color:rgb(1, 1, 1);">命令/代码注入检测 (key: cmd-injection)</font>
+ <font style="color:rgb(1, 1, 1);">目录枚举 (key: dirscan)</font>
+ <font style="color:rgb(1, 1, 1);">路径穿越检测 (key: path-traversal)</font>
+ <font style="color:rgb(1, 1, 1);">XML 实体注入检测 (key: xxe)</font>
+ <font style="color:rgb(1, 1, 1);">文件上传检测 (key: upload)</font>
+ <font style="color:rgb(1, 1, 1);">弱口令检测 (key: brute-force)</font>
+ <font style="color:rgb(1, 1, 1);">jsonp 检测 (key: jsonp)</font>
+ <font style="color:rgb(1, 1, 1);">ssrf 检测 (key: ssrf)</font>
+ <font style="color:rgb(1, 1, 1);">基线检查 (key: baseline)</font>
+ <font style="color:rgb(1, 1, 1);">任意跳转检测 (key: redirect)</font>
+ <font style="color:rgb(1, 1, 1);">CRLF 注入 (key: crlf-injection)</font>
+ <font style="color:rgb(1, 1, 1);">Struts2 系列漏洞检测 (高级版，key: struts)</font>
+ <font style="color:rgb(1, 1, 1);">Thinkphp系列漏洞检测 (高级版，key: thinkphp)</font>
+ <font style="color:rgb(1, 1, 1);">POC 框架 (key: phantasm)</font>

其中 POC 框架默认内置 Github 上贡献的 poc，用户也可以根据需要自行构建 poc 并运行。



## <font style="color:rgb(255, 255, 255);background-color:rgb(33, 33, 34);">crawlergo简介</font>
crawlergo是一个使用chrome headless模式进行URL收集的浏览器爬虫。

它对整个网页的关键位置与DOM渲染阶段进行HOOK，自动进行表单填充并提交，配合智能的JS事件触发，尽可能的收集网站暴露出的入口。

内置URL去重模块，过滤掉了大量伪静态URL，对于大型网站仍保持较快的解析与抓取速度，最后得到高质量的请求结果集合。

crawlergo 目前支持以下特性：

+ <font style="color:rgb(1, 1, 1);">原生浏览器环境，协程池调度任务</font>
+ <font style="color:rgb(1, 1, 1);">表单智能填充、自动化提交</font>
+ <font style="color:rgb(1, 1, 1);">完整DOM事件收集，自动化触发</font>
+ <font style="color:rgb(1, 1, 1);">智能URL去重，去掉大部分的重复请求</font>
+ <font style="color:rgb(1, 1, 1);">全面分析收集，包括javascript文件内容、页面注释、robots.txt文件和常见路径Fuzz</font>
+ <font style="color:rgb(1, 1, 1);">支持Host绑定，自动添加Referer</font>
+ <font style="color:rgb(1, 1, 1);">支持请求代理，支持爬虫结果主动推送</font>





Xray-web 使用 **CrawlerGo** 做爬虫，结合 **Xray** 做漏洞扫描，解决了传统开源 DAST 的不足：

1. **深度爬取，覆盖全站**
    - CrawlerGo 能够智能解析网站的内部链接，支持多层嵌套抓取。
    - 可配置爬取深度和并发量，保证扫描完整性，同时控制对目标的压力。
2. **动态渲染支持**
    - 自动执行 JavaScript，抓取 SPA 和 AJAX 页面。
    - 捕获动态生成的接口、隐藏参数和异步请求，提升漏洞发现率。
3. **表单和 API 参数自动化探索**
    - 支持多种请求方法（GET/POST/PUT/DELETE）自动填充表单。
    - 能够尝试不同参数组合，发现传统爬虫漏掉的业务逻辑漏洞。
4. **扫描效率与稳定性兼顾**
    - 可限制并发线程，减少对目标的压力，避免因请求过快被阻断。
    - 爬虫结果直接交给 Xray 扫描，实现“发现即扫描”，提高整个流程效率。
5. **可与 CI/CD 集成**
    - 爬虫和扫描结果通过 API 提供给 Web 面板或 CI/CD 流程。
    - 支持自动化触发扫描，实现开发-测试-安全的一体化。

简而言之，**CrawlerGo 负责全面发现页面与接口，Xray 负责深度漏洞扫描**，两者结合比单独使用开源 DAST 工具覆盖面更广、发现率更高、稳定性更好。



## 四、系统搭建
使用 Docker 方式快速部署 Xray-web：

```plain
git clone https://github.com/7uup/Dast-Xray-docker.git
cd Dast-Xray-docker
docker-compose up -d
```

+ 搭建成功后访问：`http://<服务器IP>:9528/`

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761321985129-305e8062-a0db-4715-85db-cb1d9941a3f8.png)

+ 默认账号密码：`admin/admin123admin`
+ 初次登录请务必修改默认密码，保证安全。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322206209-7d710a75-92e1-4862-8bc4-5be99085eaf8.png)

### 扫描模块
1. **添加扫描任务**
    - 在面板中点击 **添加任务**。
    - 可选择添加单个 URL 或批量 URL 进行扫描。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322177355-3dcc65e3-a82d-47a3-ace6-51e06f26ae8e.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322370242-9957a884-83d4-440d-a479-8173216e902c.png)

2. **查看任务列表**
    - 添加成功后，可在 **管理列表** 查看所有任务及详情。
    - 此时状态为 **待扫描**。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322409025-2a87ebe4-a29e-432a-8cf7-22b658410bd3.png)

3. **开始扫描**
    - 点击任务 **操作按钮 → 开始扫描**。
    - 状态会变为 **扫描中**，表示 Xray + CrawlerGo 正在执行扫描。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322464950-6cd2a67c-8dc0-4374-b7db-06d11bceed24.png)

4. **查看实时日志**
    - 点击任务 **详情按钮**，可查看 Xray + CrawlerGo 的实时扫描日志，方便监控扫描进度。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322476994-1339a2e3-3c3e-40da-a8ca-d533c5e205a9.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322592430-6e36c227-e94f-4ca3-bbba-ec84172fddac.png)

5. **扫描完成**
    - 扫描完成后，任务状态自动变为 **已完成**，可以查看最终扫描结果。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322722965-ad90c296-92c0-4037-909f-103194cfd0d0.png)



**Openapi扫描(CI/CD)**

1. **添加扫描任务**
    - 这里添加扫描任务主要是通过api进行添加的，添加之前需要到 **配置设置-apiSecret设置** 中生成一个secret

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761322984938-1ca45518-483d-4acf-bce9-65fbd90da702.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323063054-99c63bfc-fc2f-4ca8-983a-f4ab21c6af99.png)

    - 以后通过Openapi添加扫描任务都需要带上这个Secret值,可选择添加单个 URL 或批量 URL 进行扫描。

```shell
POST /api/openapi/scans?secret=c32a61366eb84ba8b0f1618e9c9c6d6c HTTP/1.1
Host: xxxx:9528
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Pragma: no-cache
Upgrade-Insecure-Requests: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: zh,zh-CN;q=0.9
Cache-Control: no-cache
Content-Type: application/json
Content-Length: 39

{"tasks":["http://www.testfire.net/"],"scan":1} //这里为1为即刻开始扫描，否则为添加任务不扫描
```

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323387109-230210b9-0ff4-467e-92d4-f5207a93551d.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323413903-42f947c8-f42d-4a7f-91d9-af59b6486ee3.png)





### 漏洞报告模块
+ 点击侧边栏的 **扫描报告**，可以看到所有已完成任务组对应的 Xray 扫描报告。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323538480-adacb560-be72-4f58-9719-ad712da0087a.png)

+ 在报告列表中，你可以：
+ **查看**：点击报告即可查看详细扫描结果，包括漏洞类型、风险等级和发现位置。
+ **删除**：不需要的报告可以直接删除，保持面板整洁。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323576150-165fdecc-f359-44e2-87d3-bfa4e2f09dfe.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323589357-d3b84b3a-5acc-4e55-9b68-469d8135b2c9.png)

### 系统设置模块


#### Xray 配置
+ 在 **Xray 配置** 页面，可以在线修改 Xray 的配置文件，支持自定义扫描策略和规则，使扫描更灵活、更多样化。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323752795-e1dfffa5-804f-40f8-80d2-fab52dfa937d.png)

#### 工具配置
+ **工具配置** 用于设置扫描所需的工作路径等参数。
+ 修改后需要 **先保存再加载**，才能生效。
+ ![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323785185-cacaec38-a0ab-427d-bba7-1fdc67fe57ee.png)

#### Webhook 配置
+ 在 **Webhook 配置** 页面，可以设置扫描结果的通知方式，支持 **钉钉** 和 **飞书**。
+ 机器人安全属性需要开启 **验签**，确保通知安全可靠。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323824747-069d8370-9529-4faa-bf4c-91335572ee53.png)

设置好Webhook后，即可在扫描中添加上通知啦

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323964271-c2b4462d-bf2b-4088-bb11-650bfef94011.png)

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761323981573-aa5fc746-b0d4-4685-aa51-6bb02fe997b0.png)



openapi处在json请求体中增加个 "webhookid":""即可

```shell
POST /api/openapi/scans?secret=0b02ee237f7a481fa2cbb4078ed7c094 HTTP/1.1
Host: 127.0.0.1:8087
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36
Pragma: no-cache
Upgrade-Insecure-Requests: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: zh,zh-CN;q=0.9
Cache-Control: no-cache
Content-Type: application/json
Content-Length: 39

{"tasks":["http://www.testfire.net/"],"webhookid":"111111"}
```

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761324032919-af9783ca-1fbb-472a-877a-26a6777c6a47.png)



#### apiSecret配置
+ 如果你希望通过 OpenAPI 对接 CI/CD 或其他系统，必须进行 **鉴权配置**。
+ 否则 OpenAPI 调用会被权限拦截，无法访问扫描任务或报告数据。

![](https://cdn.nlark.com/yuque/0/2025/png/22513278/1761324188871-a0fdc9ce-43d0-4391-9769-333e529cd60a.png)



> 当然，Dast-Xray 还有很多小想法和功能，未来还会不断优化和扩展，带来更全面
>



