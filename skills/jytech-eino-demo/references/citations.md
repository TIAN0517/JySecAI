# 引用与外链

本文件有两个用途：

1. 验证技能包内 **`references/`** 目录是否被列表 API、HTTP `resource_path`
   及多代理本机文件工具正常识别。
2. 记录平台上两组渗透推理能力的**外部来源**，让后续知道这些功能是照着哪几份
   公开资料做的、对应到哪个实现位置。

## 测试方式（授权环境内）

1. `GET /api/skills/jytech-eino-demo` 响应中的 `package_files` 应包含 `references/citations.md`。
2. `GET /api/skills/jytech-eino-demo?resource_path=references/citations.md` 应返回本文内容。
3. 多代理且开启 `eino_skills.filesystem_tools` 时，可通过相对路径读取本文件。

## 外部来源与对应实现

| # | 来源文章 | 对应功能 | 实现位置 |
|---|---|---|---|
| 1 | [6个月6.2k星！78个技能包让Claude秒变红队专家](https://mp.weixin.qq.com/s/9aPUVEuXyM_DmHl7aWAnsw)（Matrix 安全情报 · Claude-Red / SnailSploit 开源红队技能库） | 技能库 MCP：合并上游 78 技能／23 类目与本机 131 技能，共 209 技能／24 类目；可按触发词比对应加载哪些技能 | `mcp-servers/redteam_skills/` |
| 2 | [把Claude变成红队操作员：8k星攻击技能库Claude-Red](https://mp.weixin.qq.com/s/dXoeDEKiTvC1Kr2e7Sr3Lg)（赤雪攻防实验室 · Claude-Red） | 同上（第二份来源文） | `mcp-servers/redteam_skills/` |
| 3 | [Kali GPT - 人工智能渗透测试助手Linux部署](https://mp.weixin.qq.com/s/MqZYRT-OkXrJTJpMuCKPbA)（知晓守望 · Kali GPT） | 渗透推理 MCP：工具→ATT&CK 映射、依发现动态推荐工具链、PTES 阶段计划、案件经验记忆；完全离线、只规划不执行 | `mcp-servers/kali_gpt/` |
| 4 | [给 AI Agent装上安全武器库：7 个 Skill 接管你的安全测试](https://mp.weixin.qq.com/s/tXThZB2hYkx979187bPytA)（YsCode · awesome-skills-security / SecLists 精选） | 7 个授权测试字典技能：fuzzing、passwords、patterns、payloads、usernames、webshells、llm-testing | `skills/security-*`、`skills/llm-testing` |
| 5 | [装了 200 个安全工具，先跑哪个全靠翻手册？12.4k Star 的 HexStrike](https://mp.weixin.qq.com/s/p099ln4b7oc3m3CGBo5ySg)（Agent技能库 · HexStrike AI） | HexStrike v6.0 决策层：150+ 工具 / 12+ agent，MCP 接 127.0.0.1:8888；`alwaysAllow` 空 | `skills/hexstrike-ai/`、`third_party/hexstrike-ai/`、MCP `hexstrike-ai`、`jysec-hexstrike.service` |
| 6 | [HexStrike AI MCP Agents v6.0](https://github.com/0x4m4/hexstrike-ai)（0x4m4 / OTT Cybersecurity LLC · MIT） | 上游源码与 MCP 注册（151 `@mcp.tool`）。现网 Kali apt 同版本，绑定 loopback | 同上 |
| 7 | [如何通过 Agent+Skill+Kali 进行漏洞挖掘](https://mp.weixin.qq.com/s/_s-QWJtWlLnJvtCq9_MXDw)（小枣信安） | 两阶段：信息搜集+威胁建模 → Skill 探测（不利用）；Kali MCP + HexStrike + 本地 Skill | `skills/authorized-agent-kali-hunt/`、MCP `kali-mcp`、`skills/acs-skill-catalog/` |

### 说明

- 上游 Claude-Red 以 MIT 许可开源；本平台只读取其技能清单与内容，不改动上游。
- 两个 MCP 都**不执行任何命令、不主动连网**（kali_gpt 完全离线）、不接触目标；
  真正落地动作仍要走平台的 HITL 与授权范围闸门。
- HexStrike / Kali MCP **会**调本机工具，仅限授权目标；默认两阶段流程只探测不利用。
- Anthropic-Cybersecurity-Skills 只装目录与渗透子集映射，不把 818 份正文灌进默认 `skills_dir`。
- 平台自己的**受控跳转验证 + 自动上链**（复测站点、站点清单自动从漏洞库／资产库提取）
  不来自这四篇，实现见 `internal/redirect/` 与 `internal/database/redirect_seeds.go`，
  操作说明见 `docs/zh-CN/redirect-batch-verify.md`
  （控制台路径：「资产 / 安全防护」→「批次跳转验证」，路由 `redirect-verify`）。

## 占位引用

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)（仅作链接格式示例）
