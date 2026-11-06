# JySecAI 独立武器库（Skills + MCP）

把 Grok 侧的渗透技能包和可独立拉起的 MCP 接到 JySecAI，平台自己用，不经过 Grok。

## 已经落到本仓库的

- `skills/`：228 个技能包（原 131 + SecLists 7 + Grok 进攻技能 90）
- 本目录：`external-mcp.json` 是 JySecAI `external_mcp.servers` 片段

`redteam-skills` MCP 会向上查找 `skills/`，新技能会自动进索引。

## 本机（源码树）立刻可用

JySecAI 若以本仓库为 `skills_dir`：

```yaml
skills_dir: /home/BossJy/JySecAI/skills
```

`jysec` 用户已通过 ACL 可读该目录（`/home/BossJy` 仍是 700，只给了 `jysec` 穿越权限）。

## 接到线上 `/opt`（需要 sudo）

```bash
sudo bash /home/BossJy/JySecAI/deploy/arsenal/sync-to-live.sh
```

脚本会：

1. rsync `skills/` → `/opt/jysecai/core/current/skills/`
2. rsync `mcp-servers/` → `/opt/jysecai/core/current/mcp-servers/`
3. 把 `external-mcp.json` 里**尚未存在**的 MCP 合并进 `/var/lib/jysecai/core/config.yaml`
4. `systemctl restart jysec-core`

没有 sudo 时只打印将要执行的命令，不改线上。

## 用 Web API 加 MCP（已登录）

```bash
export JYSEC_TOKEN='登录后的 Bearer'
python3 /home/BossJy/JySecAI/deploy/arsenal/apply-mcp-via-api.py \
  --base http://127.0.0.1:9898 \
  --token "$JYSEC_TOKEN"
```

## JSON 里有哪些 MCP

| 名称 | 传输 | 说明 |
|---|---|---|
| 仓库内 8 个 | stdio | dragon-v / reverse-shell / vuln-intel / assets / pent-claude / redteam-* / kali-gpt |
| github | stdio npx | GitHub 官方 MCP（读 `GITHUB_TOKEN`） |
| cloudflare | HTTP | Cloudflare MCP |
| ida-official | HTTP | Hex-Rays `127.0.0.1:8737/mcp` |
| fetch / memory / time / sequential-thinking / context7 | stdio | 通用 MCP |
| chrome-devtools | stdio | 默认 `disabled`，需要本机 Chrome |

未收录：Windows `wsl.exe` 包装的 kali/hexstrike（线上已有原生 `jysec-kali-api` / `jysec-hexstrike`）、Codex `node_repl`、绑死别人家路径的 filesystem。
