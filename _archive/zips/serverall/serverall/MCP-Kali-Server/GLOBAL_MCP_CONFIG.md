# MCP Kali Server 全局配置指南

## 支持的MCP客户端

### 1. Claude Desktop

#### 配置位置
- **Windows**: `C:\Users\[用户名]\AppData\Roaming\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### 配置文件内容
```json
{
    "mcpServers": {
        "kali_mcp": {
            "command": "python",
            "args": [
                "C:\\Users\\Administrator\\Desktop\\serverall\\MCP-Kali-Server\\mcp_server.py",
                "--server",
                "http://localhost:5000/"
            ]
        }
    }
}
```

#### 配置步骤
1. 创建或编辑配置文件
2. 重启Claude Desktop

### 2. 5ire Desktop

#### 配置方式
在5ire中添加MCP服务器：
- 命令: `python C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server\mcp_server.py --server http://localhost:5000`

### 3. 其他MCP客户端

#### 通用配置
```json
{
    "mcpServers": {
        "kali_tools": {
            "command": "python",
            "args": [
                "C:\\Users\\Administrator\\Desktop\\serverall\\MCP-Kali-Server\\mcp_server.py",
                "--server",
                "http://localhost:5000",
                "--timeout",
                "300"
            ]
        }
    }
}
```

## 环境变量配置

### 创建环境变量脚本

#### Windows (PowerShell)
```powershell
# 设置MCP服务器环境变量
$env:MCP_KALI_SERVER="C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server"
$env:MCP_SERVER_URL="http://localhost:5000"

# 添加到系统环境变量（需要管理员权限）
[System.Environment]::SetEnvironmentVariable("MCP_KALI_SERVER", $env:MCP_KALI_SERVER, "Machine")
[System.Environment]::SetEnvironmentVariable("MCP_SERVER_URL", $env:MCP_SERVER_URL, "Machine")
```

#### Windows (批处理)
```batch
REM 设置MCP环境变量
setx MCP_KALI_SERVER "C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server"
setx MCP_SERVER_URL "http://localhost:5000"
```

#### Linux/macOS
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export MCP_KALI_SERVER="/path/to/MCP-Kali-Server"
export MCP_SERVER_URL="http://localhost:5000"
```

## 系统服务配置（可选）

### Windows服务配置

#### 创建Kali服务器服务
```batch
REM 以管理员身份运行
sc create "MCPKaliServer" binPath= "C:\Python311\python.exe C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server\kali_server.py" start= auto
echo "服务创建成功，启动服务..."
sc start MCPKaliServer
```

#### 创建MCP客户端服务
```batch
REM 以管理员身份运行
sc create "MCPKaliClient" binPath= "C:\Python311\python.exe C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server\mcp_server.py --server http://localhost:5000" start= auto
echo "客户端服务创建成功，启动服务..."
sc start MCPKaliClient
```

### Linux系统服务

#### 创建systemd服务文件
```ini
# /etc/systemd/system/mcp-kali-server.service
[Unit]
Description=MCP Kali Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/MCP-Kali-Server
ExecStart=/usr/bin/python3 kali_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 自动化启动脚本

### Windows启动脚本

#### 完整启动脚本 (`start_all.bat`)
```batch
@echo off
echo Starting MCP Kali Server System...

REM 启动Kali API服务器
start "MCP Kali Server" cmd /k "cd /d C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server && python kali_server.py"

REM 等待服务器启动
timeout /t 5 /nobreak > nul

REM 启动MCP客户端
start "MCP Client" cmd /k "cd /d C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server && python mcp_server.py --server http://localhost:5000 --debug"

echo MCP Kali Server system started successfully!
echo - Kali API Server: http://localhost:5000
echo - MCP Client: Running in background
echo.
echo Press any key to close this window...
pause > nul
```

### Linux启动脚本

#### 完整启动脚本 (`start_all.sh`)
```bash
#!/bin/bash
echo "Starting MCP Kali Server System..."

# 启动Kali API服务器
cd /opt/MCP-Kali-Server
python3 kali_server.py &
SERVER_PID=$!

# 等待服务器启动
sleep 5

# 启动MCP客户端
python3 mcp_server.py --server http://localhost:5000 --debug &
CLIENT_PID=$!

echo "MCP Kali Server system started successfully!"
echo "- Kali API Server: http://localhost:5000 (PID: $SERVER_PID)"
echo "- MCP Client: Running (PID: $CLIENT_PID)"
echo ""
echo "Press Ctrl+C to stop all services"

# 等待中断信号
trap 'kill $SERVER_PID $CLIENT_PID; exit' INT
wait
```

## 验证配置

### 健康检查脚本
```python
#!/usr/bin/env python3
import requests
import sys

def check_mcp_health():
    try:
        # 检查Kali服务器
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Kali API Server is running")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Tools available: {health_data.get('all_essential_tools_available', False)}")
        else:
            print("❌ Kali API Server is not responding")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Kali API Server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if check_mcp_health():
        print("\n✅ MCP system is ready for use!")
        sys.exit(0)
    else:
        print("\n❌ MCP system configuration issues detected")
        sys.exit(1)
```

## 故障排除

### 常见问题

1. **端口冲突**
   - 修改 `config.json` 中的端口设置
   - 检查端口5000是否被占用

2. **权限问题**
   - 确保Python有执行权限
   - 检查防火墙设置

3. **依赖问题**
   - 运行 `pip install -r requirements.txt`
   - 检查Python版本兼容性

4. **连接问题**
   - 验证服务器是否正在运行
   - 检查网络连接和防火墙

### 日志查看

#### Kali服务器日志
```bash
# 启用调试模式
python kali_server.py --debug
```

#### MCP客户端日志
```bash
# 启用调试模式
python mcp_server.py --server http://localhost:5000 --debug
```

## 安全配置

### 生产环境建议

1. **网络隔离**
   - 仅在内部网络运行
   - 使用防火墙限制访问

2. **认证机制**
   - 添加API密钥认证
   - 使用HTTPS加密

3. **监控**
   - 启用详细日志
   - 监控系统资源使用

4. **备份**
   - 定期备份配置文件
   - 保存重要日志

---

**配置文件位置**: `C:\Users\Administrator\Desktop\serverall\MCP-Kali-Server\GLOBAL_MCP_CONFIG.md`