# IDA MCP 逆向工程接入

本方案使用 Hex-Rays 官方 `ida-mcp`，由一个仅监听本机回环地址的 Streamable HTTP 服务同时提供给 JySecAI 与 Hermes。共享服务避免重复启动 worker，也让两个客户端看到同一组 IDA 数据库实例。

## 前置条件

- Python 3.11 或更高版本、Git 与 `uv`。
- IDA Home 或 Pro 9.4+，并具备有效授权与 IDAlib。
- IDA Free 不含 IDAPython/IDAlib，不能作为官方 IDA MCP 的分析后端。

官方资料：

- [Hex-Rays IDA MCP](https://github.com/HexRaysSA/ida-mcp)
- [IDA MCP 文档](https://docs.hex-rays.com/core/mcp)
- [IDA Domain / IDAlib 初始化](https://ida-domain.docs.hex-rays.com/getting_started/)
- [Hermes MCP 配置](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md)

## 安装与启动共享服务

为确保可重建，建议固定已经验证的版本：

```bash
uv tool install --python 3.11 'ida-mcp==20260930.0.1'
```

如果 IDA 安装程序尚未初始化 IDAlib，执行安装目录中的激活脚本：

```bash
python3 /path/to/ida/idalib/python/py-activate-idalib.py
```

安装并启动 user systemd 服务：

```bash
install -D -m 0644 deploy/systemd/user/jysec-ida-mcp.service \
  "$HOME/.config/systemd/user/jysec-ida-mcp.service"
systemctl --user daemon-reload
systemctl --user enable --now jysec-ida-mcp.service
systemctl --user status jysec-ida-mcp.service --no-pager
```

服务只监听 `127.0.0.1:8737`，不要直接暴露到公网。如需跨主机使用，应在前方加入 TLS、认证与来源限制。

若要让服务附着到 IDA GUI 中已经打开的数据库，可安装官方 GUI 插件：

```bash
uvx ida-hcli plugin install ida-mcp@https://github.com/HexRaysSA/ida-mcp
```

## 接入 Hermes

在 `~/.hermes/config.yaml` 中加入：

```yaml
mcp_servers:
  ida:
    url: http://127.0.0.1:8737/mcp
    timeout: 120
    enabled: true
```

验证：

```bash
hermes mcp test ida
```

预期发现六个工具：`open_database`、`execute_python`、`reference`、`list_databases`、`save_database`、`close_database`。

## 接入 JySecAI

在“设置 → MCP 管理 → 添加外部 MCP”的 JSON 输入框贴入：

```json
{
  "ida-official": {
    "type": "http",
    "url": "http://127.0.0.1:8737/mcp",
    "description": "Official Hex-Rays IDA MCP shared with Hermes",
    "timeout": 120,
    "keep_alive": 30,
    "max_retries": 5,
    "tool_enabled": {
      "open_database": true,
      "execute_python": true,
      "reference": true,
      "list_databases": true,
      "save_database": true,
      "close_database": true
    }
  }
}
```

保存后确认状态为“已连接”、工具数为 6。使用这些工具的角色需要 `mcp:external:execute` 权限且 Scope 为 `all`。

也可直接写入 `config.yaml` 的 `external_mcp.servers`；完整 YAML 见根目录 `config.example.yaml`。

## 安全边界

`execute_python` 不只是查询接口，也能重命名、注释、套用类型和修改字节。生产环境应：

- 只让明确授权的角色取得 `mcp:external:execute`。
- 通过 JySecAI Tool Guard/HITL 对 `ida-official::execute_python` 的写入类请求要求人工确认。
- 只分析已经授权的样本，并将样本及 `.i64` 数据库存放在受控工作目录。
- 保留 JySecAI 审计日志；不要对官方工具设置无条件自动批准。

## 验证与排错

先验证传输和工具发现：

```bash
systemctl --user is-active jysec-ida-mcp.service
ss -ltnp | grep '127.0.0.1:8737'
hermes mcp test ida
go run ./cmd/test-external-mcp /path/to/config.yaml
```

如果 `open_database` 返回 `cannot load IDA library`：

1. 确认安装的是含 IDAlib 的 IDA 9.4+，不是 IDA Free。
2. 执行 `py-activate-idalib.py`，或为服务设置正确的 `IDADIR`。
3. 重启服务：`systemctl --user restart jysec-ida-mcp.service`。
4. 查看日志：`journalctl --user -u jysec-ida-mcp.service -n 100 --no-pager`。

## 回退

```bash
systemctl --user disable --now jysec-ida-mcp.service
rm "$HOME/.config/systemd/user/jysec-ida-mcp.service"
systemctl --user daemon-reload
```

随后从 Hermes 与 JySecAI 的 MCP 管理中删除对应配置即可；这不会删除 IDA 数据库或样本。
