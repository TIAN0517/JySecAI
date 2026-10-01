# 🚀 Dragon-V Triple Bot 部署指南

## 概述

本文档提供 Dragon-V Triple Bot 的完整部署指南，涵盖从环境准备到生产部署的全过程。

## 系统要求

### 硬件要求
- **CPU**: 2核以上（推荐4核）
- **内存**: 4GB以上（推荐8GB）
- **存储**: 10GB可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Windows 10/11, Ubuntu 18.04+, CentOS 7+
- **Python**: 3.8+
- **数据库**: SQLite3（内置）

## 快速开始

### 1. 环境准备

#### Windows 系统
```bash
# 1. 安装 Python 3.8+
# 从 https://www.python.org/downloads/ 下载并安装

# 2. 验证安装
python --version
pip --version
```

#### Linux 系统
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### 2. 项目部署

#### 方法一：使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python -c "import dragon_triple_bot_unified_manager; print('✅ 导入成功')"
```

#### 方法二：直接安装

```bash
# 直接安装所有依赖
pip install -r requirements.txt
```

### 3. 配置设置

#### 基础配置
```bash
# 复制环境配置示例
cp .env.example .env

# 编辑配置文件
# Windows: notepad .env
# Linux: nano .env
```

#### 配置说明
```ini
# .env 文件内容示例
BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
LOG_LEVEL=INFO
DATABASE_PATH=dragon_triple_bot_unified.db
MAX_CONCURRENT_TASKS=10
```

#### 主配置文件
编辑 `config_unified.yaml`：

```yaml
database:
  path: "dragon_triple_bot_unified.db"
  timeout: 30.0

security:
  max_scan_depth: 5
  request_timeout: 30
  user_agent: "Mozilla/5.0 (compatible; Dragon-V-Scanner/1.0)"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "dragon_v.log"
```

## 运行模式

### 1. 开发模式

#### 交互式管理器
```bash
python dragon_triple_bot_unified_manager.py interactive
```

#### 功能模块测试
```bash
python dragon_triple_bot_functional_module.py
```

### 2. 生产模式

#### Telegram Bot 模式
```bash
# 设置环境变量
set BOT_TOKEN=your_telegram_bot_token  # Windows
export BOT_TOKEN=your_telegram_bot_token  # Linux

# 启动 Telegram Bot
python dragon_triple_telegram_bot.py
```

#### 系统服务模式
创建系统服务文件：

**Windows 服务** (`dragon_v_service.bat`):
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python dragon_triple_telegram_bot.py
pause
```

**Linux 服务** (`/etc/systemd/system/dragon-v.service`):
```ini
[Unit]
Description=Dragon-V Triple Bot Service
After=network.target

[Service]
Type=simple
User=dragonv
WorkingDirectory=/opt/dragon-v
Environment=BOT_TOKEN=your_telegram_bot_token
ExecStart=/opt/dragon-v/venv/bin/python dragon_triple_telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable dragon-v.service
sudo systemctl start dragon-v.service
sudo systemctl status dragon-v.service
```

### 3. 一键启动脚本

使用项目提供的启动脚本：

```bash
# Windows
START_TRIPLE_BOT.bat

# Linux (需要赋予执行权限)
chmod +x START_TRIPLE_BOT.bat
./START_TRIPLE_BOT.bat
```

## 数据库配置

### SQLite 数据库
项目使用 SQLite3 作为默认数据库，无需额外配置。

#### 数据库文件
- `dragon_triple_bot_unified.db` - 统一管理器数据库
- `dragon_triple_telegram_bot.db` - Telegram Bot 数据库

#### 数据库维护
```python
import sqlite3
import os

# 检查数据库状态
def check_database_health():
    db_path = "dragon_triple_bot_unified.db"

    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f"✅ 数据库健康检查通过")
        print(f"   表数量: {len(tables)}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库错误: {e}")
        return False
```

## 网络配置

### 防火墙设置

#### Windows 防火墙
```powershell
# 允许 Python 通过防火墙
New-NetFirewallRule -DisplayName "Dragon-V Bot" -Direction Inbound -Program "python.exe" -Action Allow
```

#### Linux 防火墙
```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

### 代理配置
如果需要通过代理访问：

```python
import os

# 设置代理环境变量
os.environ['HTTP_PROXY'] = 'http://proxy.example.com:8080'
os.environ['HTTPS_PROXY'] = 'https://proxy.example.com:8080'
```

## 监控和维护

### 1. 日志监控

#### 查看日志
```bash
# 实时查看日志
tail -f dragon_v.log

# 查看错误日志
grep "ERROR" dragon_v.log
```

#### 日志轮转配置
创建日志轮转配置 (`/etc/logrotate.d/dragon-v`):

```
/opt/dragon-v/dragon_v.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 dragonv dragonv
}
```

### 2. 性能监控

#### 系统状态检查
```python
from scripts.system_monitor import SystemMonitor

monitor = SystemMonitor()
status = monitor.get_system_status()
print(f"CPU使用率: {status['cpu_usage']}%")
print(f"内存使用: {status['memory_usage']}%")
print(f"磁盘使用: {status['disk_usage']}%")
```

#### 数据库监控
```python
import sqlite3

def monitor_database():
    conn = sqlite3.connect('dragon_triple_bot_unified.db')
    cursor = conn.cursor()

    # 检查任务数量
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='running'")
    running_tasks = cursor.fetchone()[0]

    print(f"总任务数: {total_tasks}")
    print(f"运行中任务: {running_tasks}")

    conn.close()
```

### 3. 备份策略

#### 数据库备份
```python
import shutil
import datetime

def backup_database():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/dragon_triple_bot_unified_{timestamp}.db"

    shutil.copy2('dragon_triple_bot_unified.db', backup_file)
    print(f"✅ 数据库备份完成: {backup_file}")
```

#### 配置备份
```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz config_unified.yaml .env
```

## 故障排除

### 常见问题

#### 1. 依赖安装失败
```bash
# 清除缓存并重试
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

#### 2. 数据库锁定
```python
# 增加超时时间
conn = sqlite3.connect('database.db', timeout=30.0)
```

#### 3. 内存不足
```python
# 限制并发任务数
config["max_concurrent_tasks"] = 5
```

#### 4. 网络连接问题
```python
# 增加超时时间
import requests
requests.get(url, timeout=60)
```

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

或设置环境变量：
```bash
export LOG_LEVEL=DEBUG
```

## 安全考虑

### 1. 访问控制
- 使用强密码保护数据库
- 限制文件系统权限
- 定期更新依赖包

### 2. 网络安全
- 使用HTTPS连接
- 配置适当的防火墙规则
- 定期进行安全扫描

### 3. 数据保护
- 加密敏感配置信息
- 定期备份重要数据
- 实施访问日志记录

## 性能优化

### 1. 数据库优化
```python
# 启用WAL模式
conn = sqlite3.connect('database.db')
conn.execute('PRAGMA journal_mode=WAL')
```

### 2. 内存优化
```python
# 限制扫描深度
config["max_scan_depth"] = 3

# 限制并发请求
config["max_concurrent_requests"] = 10
```

### 3. 网络优化
```python
# 使用连接池
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

## 升级指南

### 1. 备份现有数据
```bash
# 备份数据库和配置
cp dragon_triple_bot_unified.db dragon_triple_bot_unified.db.backup
cp config_unified.yaml config_unified.yaml.backup
```

### 2. 更新代码
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
```

### 3. 验证升级
```bash
# 运行测试
python -m pytest tests/ -v

# 检查系统状态
python scripts/system_monitor.py
```

---

**文档版本**: 1.0
**最后更新**: 2025-10-26
**技术支持**: support@dragon-v.com