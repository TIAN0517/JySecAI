# 技能市场（Skills Marketplace）

JySecAI 的技能（Skills）存放在 `skills/` 目录，遵循 [agentskills.io](https://agentskills.io) 标准：每个技能一个子目录 + `SKILL.md`（YAML front matter：`name` / `description` / 可选 `metadata`）。多代理会话通过内置 `skill` 工具渐进加载（配置见 `multi_agent.eino_skills`）。

## 当前技能清单

- **内置技能（26 个）**：渗透流程、方法论与输出规范（如 `pentest-blackboard`、`pentest-output-standards`、`web-attack-methods`、`cloud-attack-methods`、`post-exploitation`、`dragon-v-pentest` 等）。
- **市场导入（22 个）**：来源 [SpecterOps/skills](https://github.com/SpecterOps/skills) 与 [trailofbits/skills](https://github.com/trailofbits/skills)。
  - 代码审计：`cwe-code-review`、`openssf-python-review`、`owasp-security-code-review`
  - C2：`cobalt-strike-aggressor-development`、`cobalt-strike-aggressor-reference`、`cobalt-strike-malleable-c2-development`
  - 侦察：`nmap-parse`、`osint-recon`、`shodan`
  - BloodHound / 目录分析：`bloodhound-query`、`bloodhound-analysis`、`bloodhound-ad-analysis`、`bloodhound-opengraph`、`azurehound-analysis`、`openhound-development`、`openhound-github`、`openhound-jamf`、`openhound-okta`
  - 报告时间线：`timeline-consolidator`、`timeline-workflow`
  - TrailOfBits：`burpsuite-project-parser`、`yara-rule-authoring`

导入记录（含来源、提交、依赖 MCP）保存在 `skills/.marketplace-manifest.json`。

## 同步工具

```bash
# 预设集导入（specterops: starter / c2 / recon / bloodhound / timeline / code-review；trailofbits: audit）
python scripts/sync-skill-marketplaces.py --preset starter

# 指定来源全量
python scripts/sync-skill-marketplaces.py --source specterops

# 从本地路径导入（例如自定义技能目录）
python scripts/sync-skill-marketplaces.py --import path/to/skill_dir

# 常用选项
#   --dry-run      只打印将导入的内容，不写盘
#   --update       强制重新拉取市场仓库（默认增量）
#   --skills-dir   目标目录（默认 skills/）
#   --cache-dir    克隆缓存（默认 scripts/.marketplace-cache/，已 gitignore）
```

导入时会自动：目录名 == front matter `name` 规范化；注入 `metadata.marketplace` / `metadata.source` 溯源字段；更新 manifest。

## 依赖 MCP 的技能（重要）

部分市场技能依赖外部 MCP server 才能发挥完整能力，对应关系见 manifest 的 `deps_mcp` 字段：

| MCP | 声明位置（config.yaml） | 对应技能 |
|---|---|---|
| `bloodhound` | `external_mcp.servers.bloodhound` | bloodhound-query / bloodhound-analysis / bloodhound-ad-analysis / azurehound-analysis 等 |
| `dragon-v` | `external_mcp.servers.dragon-v` | dragon-v-pentest（及 agents/dragon-v.md 子代理） |
| `vuln-intel` | `external_mcp.servers.vuln-intel` | CVE/KEV 在线交叉验证 |

### 启用语义（必读）

`config.yaml` 加载时会做归一化：**未设 `disabled: true` 的外部 MCP server 一律视为启用**（见 `internal/config/config.go`）。因此：

- 停用 = `disabled: true`（官方 MCP 字段）
- 启用 = 删除 `disabled` 或改为 `false`（也可在 Web UI「外部 MCP」页管理，UI 会写回 `external_mcp_enable`）

主配置默认声明 6 个 server（`bloodhound` + 仓库自带 5 个 Python MCP：`reverse-shell` / `vuln-intel` / `redteam-knowledge` / `dragon-v` / `pent-claude-agent`），**全部默认停用**。Python MCP 源码在 `mcp-servers/<name>/`，命令支持 `${VAR}` / `${VAR:-default}` 环境变量展开（如 `${JYSECAI_PYTHON:-python}`）。

## 加载规则与供应链建议

- Eino skill loader 只扫描 `skills_dir` **第一层**子目录的 `SKILL.md`（`*/SKILL.md`）；任何一个第一层 SKILL.md 解析失败都会导致整个技能列表加载失败。
- `skills/.marketplace-manifest.json`、`skills/.eino/`（plantask 运行时）均不影响加载。
- 建议导入前审查 SKILL.md 内容与引用的脚本；导入后可用 `python scripts/sync-skill-marketplaces.py --dry-run --update` 对比上游变更再决定升级。
- 技能内容即提示词：市场技能的措辞（含授权假设）会进入会话上下文，接入生产前请人工审阅。
