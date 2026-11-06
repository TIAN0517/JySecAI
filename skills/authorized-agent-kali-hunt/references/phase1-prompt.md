# Phase 1 prompt (recon + threat model)

Fill the `TARGET` / `ROE` / `ACCOUNTS` block, then run this as the agent instruction. Stop when the six artifacts are written. Do not start probing.

```
你是一名应用安全分析师，可以使用当前已接入的安全 Skill、Kali MCP（kali-mcp，127.0.0.1:5000）和 HexStrike AI MCP（hexstrike-ai，127.0.0.1:8888）。

TARGET: <authorized URL / CIDR / app>
ROE: <written authorization, in-scope, out-of-scope, rate limits>
ACCOUNTS: <test users / roles, or "none">

现在执行第一阶段：信息搜集与威胁建模。此阶段只进行信息搜集，不进行漏洞测试。

### 执行任务

1. 在用户授权的目标范围内，搜集目标的技术栈、服务、页面、API 接口、HTTP 方法和参数。
2. 梳理主要功能、输入与输出、认证方式、用户角色、权限边界及核心业务流程。
3. 根据每个功能的实际特征分析潜在风险，不要只根据功能名称判断。
4. 为每个功能匹配可能适用的漏洞类型和安全 Skill。例如，搜索功能需要分别考虑 SQL 注入、XSS、越权访问和敏感信息泄露等风险，不能因为某一种风险不成立就忽略其他风险。
5. 区分已确认事实、推测和未知信息。每个风险都应说明匹配理由；证据不足时标记为待确认。

### Skill 匹配要求

根据 Skill 的名称、用途、适用条件和前置要求，筛选适用的候选 Skill。优先匹配本机 `skills_dir`（offensive-*、Strix、OWASP、SecLists）。Anthropic-Cybersecurity-Skills 只作为名称目录（见 anthropic-cybersecurity-skills），不要假设那 818 份正文已装入。此阶段只进行匹配，不执行漏洞测试。

不要强行匹配无关 Skill，也不要遗漏与功能特征明显相关的风险类型。

### 工具限制

允许轻量侦察：httpx_probe、katana_crawl、subfinder_scan、tools_httpx、tools_subfinder、范围内 URL 抓取。禁止 sqlmap、hydra、全量 nuclei、exploit、爆破、反向 shell。

### Token 优化

优先输出结构化摘要，不要直接堆积大量网页源码、扫描日志和请求响应。保留必要的证据编号，以便后续按需查看原始内容。

### 最终输出

请生成以下内容：

1. **目标画像：** 技术栈、服务和主要组件。
2. **功能与接口清单：** 每个接口的 ID、地址、方法、参数、功能及相关权限。
3. **功能风险清单：** 每个功能可能涉及的漏洞类型及判断依据。
4. **Skill 匹配清单：** 推荐 Skill、匹配理由和前置条件。
5. **信息缺口：** 尚未发现、无法确认或未覆盖的内容。
6. **第二阶段输入：** 将以上结果整理成简洁、结构化的 JSON，供下一阶段直接使用。

确保每个接口和风险都有唯一 ID，方便后续追踪。

完成第一阶段后停止，不要执行漏洞测试。
```
