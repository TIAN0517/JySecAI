# MCP Kali Server 部署指南

## 项目概述

MCP Kali Server 是一个轻量级的API桥接器，连接MCP客户端（如Claude Desktop、5ire）到Kali Linux工具API服务器，允许在Linux终端上执行命令。

## 系统要求

- Python 3.8+
- Kali Linux 或具有渗透测试工具的Linux系统
- MCP兼容的客户端（Claude Desktop、5ire等）

## 快速开始

### 1. 安装依赖

```bash
cd MCP-Kali-Server
pip install -r requirements.txt
```

### 2. 启动Kali API服务器

#### Windows系统
双击运行：`start_kali_server.bat`

#### Linux系统
```bash
python kali_server.py --debug
```

服务器将在 http://localhost:5000 启动

### 3. 配置MCP客户端

#### Claude Desktop配置
1. 将 `claude_desktop_config.json` 复制到：
   - Windows: `C:\Users\[用户名]\AppData\Roaming\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. 重启Claude Desktop

#### 5ire配置
1. 在5ire中添加MCP服务器：
   ```
   python mcp_server.py --server http://localhost:5000
   ```

### 4. 启动MCP客户端

#### Windows系统
双击运行：`start_mcp_client.bat`

#### Linux系统
```bash
python mcp_server.py --server http://localhost:5000
```

## 配置说明

### Kali服务器配置

编辑 `config.json` 文件：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "mcp": {
    "timeout": 300,
    "kali_server_url": "http://localhost:5000"
  }
}
```

### 环境变量

- `API_PORT`: API服务器端口（默认5000）
- `DEBUG_MODE`: 调试模式（默认false）

## 可用工具

### 支持的渗透测试工具

1. **Nmap** - 网络扫描
2. **Gobuster** - 目录爆破
3. **Dirb** - Web内容扫描
4. **Nikto** - Web服务器扫描
5. **SQLMap** - SQL注入测试
6. **Metasploit** - 漏洞利用框架
7. **Hydra** - 密码破解
8. **John the Ripper** - 密码破解
9. **WPScan** - WordPress扫描
10. **Enum4linux** - Windows/Samba枚举

### 通用命令执行

支持执行任意Linux命令，适用于：
- 自定义脚本执行
- 系统信息收集
- 文件操作
- 网络工具使用

## API端点

### 健康检查
```
GET /health
```

### 通用命令执行
```
POST /api/command
{
    "command": "ls -la"
}
```

### 工具专用端点

- `POST /api/tools/nmap` - Nmap扫描
- `POST /api/tools/gobuster` - Gobuster扫描
- `POST /api/tools/dirb` - Dirb扫描
- `POST /api/tools/nikto` - Nikto扫描
- `POST /api/tools/sqlmap` - SQLMap扫描
- `POST /api/tools/metasploit` - Metasploit模块
- `POST /api/tools/hydra` - Hydra密码破解
- `POST /api/tools/john` - John密码破解
- `POST /api/tools/wpscan` - WPScan扫描
- `POST /api/tools/enum4linux` - Enum4linux枚举

## 使用示例

### 通过MCP客户端使用

在支持MCP的AI客户端中，可以直接调用工具：

```python
# Nmap扫描
result = nmap_scan("192.168.1.1", "-sV", "80,443,22")

# Gobuster目录扫描
result = gobuster_scan("https://example.com", "dir", "/usr/share/wordlists/dirb/common.txt")

# SQLMap注入测试
result = sqlmap_scan("https://example.com/page.php?id=1")
```

### 直接API调用

```bash
# Nmap扫描
curl -X POST http://localhost:5000/api/tools/nmap \
  -H "Content-Type: application/json" \
  -d '{"target": "192.168.1.1", "scan_type": "-sV", "ports": "80,443"}'

# 通用命令执行
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{"command": "whoami"}'
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查Kali服务器是否运行
   - 确认端口5000未被占用
   - 检查防火墙设置

2. **工具不可用**
   - 确保所有工具在Kali系统中已安装
   - 检查工具路径是否正确

3. **权限问题**
   - 某些工具可能需要root权限
   - 考虑使用sudo运行服务器

### 日志查看

启用调试模式查看详细日志：
```bash
python kali_server.py --debug
```

## 安全注意事项

⚠️ **重要安全提醒**：

- 仅在授权测试环境中使用
- 确保API服务器仅在内网或安全网络中使用
- 定期更新依赖包
- 监控服务器日志
- 使用强认证机制

## 许可证

本项目基于MIT许可证开源。详见LICENSE文件。