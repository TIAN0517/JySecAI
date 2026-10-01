# 安全加固指南

[English](../en-US/security-hardening.md)

本文给出 JySecAI 上线前和持续运行中的安全加固清单。

## 上线前必做

- 首次部署后立即修改 `admin` 初始密码（Web 界面或平台权限 → 用户管理）。
- 使用 HTTPS，或放在可信反向代理之后。
- 限制来源 IP、VPN 或堡垒机访问。
- 开启 `audit.enabled`。
- 不需要 C2 时设置 `c2.enabled: false`。
- 不暴露独立 HTTP MCP，除非设置强认证和网络隔离。
- 外部 MCP 只接可信服务。
- 备份 `config.yaml`、`data/`、自定义资源目录。

## 反向代理建议

Nginx 基线：

```nginx
client_max_body_size 200m;
proxy_buffering off;
proxy_http_version 1.1;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

建议额外加：

```nginx
add_header X-Content-Type-Options nosniff;
add_header Referrer-Policy no-referrer;
add_header X-Frame-Options DENY;
```

## HITL 白名单基线

推荐最小白名单：

```yaml
hitl:
  tool_whitelist:
    - read_file
    - glob
    - grep
    - tool_search
```

不要默认加入：

- `execute`
- WebShell 写入/执行工具
- C2 任务和 payload 工具
- 外部 MCP 高风险工具
- 删除、写入、上传、持久化相关工具

## 文件权限

建议：

```bash
chmod 600 config.yaml
chmod 700 data
```

生产环境使用独立系统用户运行：

```text
jysecai:jysecai
```

避免 root 运行，除非明确需要绑定低端口或访问特殊资源。

## 外部 MCP 审查

接入前确认：

- 工具是否能执行命令。
- 是否能读写本机文件。
- 是否会把数据发往第三方。
- 是否有自己的认证。
- 是否会返回不可信网页或模型内容。
- 是否需要容器隔离。

接入后：

- 高风险工具不进白名单。
- 定期检查工具列表变化。
- 审计配置变更。

## C2 和 WebShell

C2：

- 默认关闭。
- 演练窗口临时开启。
- Listener 端口与管理端口分离。
- `allow_legacy_shell` 与 `allow_plaintext_checkin` 默认关闭。开启任一项都会让会话或 beacon 流量以明文过链路 —— 主机名、账号、内网 IP 与下发的任务指令将对链路上的任何人可读。除实验网段外请保持关闭。
- 结束后清理 payload、session、task、event。

WebShell：

- 只保存授权目标。
- 使用清晰命名。
- 写入/删除/执行必须审批。
- 项目结束删除连接。

## 机密字段落盘加密

C2 listener 的 `encryption_key` / `implant_token` 与 WebShell 的 `password` 以 AES-256-GCM 加密后存入 SQLite。主密钥来自环境变量 `JY_SECMASTER_KEY`：32 字节、64 位十六进制字符，例如 `openssl rand -hex 32`。

- 启动服务前设置 `JY_SECMASTER_KEY`；密钥不会写入配置文件、数据库、版本库或备份。
- 密钥必须与数据库**分开**备份：没有密钥的数据库备份无法解密，只有密钥没有数据库则毫无用处。
- 全新安装且尚无任何机密值时，不设置该变量也能启动。一旦存在机密值，密钥缺失、格式错误或与既有密文不符都会导致**启动失败**，绝不回退到明文。
- 密钥错误不会损坏数据：受影响的记录读取时报错，而不是返回错误内容。
- 主密钥不会进入任何子进程。所有子进程环境（外部 MCP、交互式 shell、工具执行、C2 payload 编译）在启动前都会先剔除该变量，被攻破的第三方进程无法解密数据库。子进程没有正当理由需要它；即使在配置中显式指定，也一样不会送出。
- 旧的明文数据会在启动时原地迁移，并加上 `v1:` 前缀；迁移可重复执行，且每筆重寫後都會回讀驗證。

密钥轮换没有自动化流程。若在已有密文的情况下更换 `JY_SECMASTER_KEY`，服务会按设计拒绝启动；轮换需要在带外重新加密这些记录（用旧密钥导出，换新密钥重启后再导入）。

## 数据保留

建议：

- 审计：30-90 天。
- 工具监控：90-180 天。
- 上传附件：项目结束清理。
- C2/WebShell 输出：只保留报告需要的证据。
- 知识库：不放真实凭证和客户私密数据。

## 周期巡检

每周：

- 登录失败和异常 IP。
- 配置变更。
- 外部 MCP 增删改。
- 长时间运行工具。
- C2 是否被意外开启。
- WebShell 连接是否过期。
- 磁盘空间和数据库大小。

每个项目结束：

- 清理临时 workspace。
- 删除无用附件。
- 归档必要证据。
- 删除过期 WebShell/C2 资源。
- 导出审计记录。
