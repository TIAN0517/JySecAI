#!/usr/bin/env python3
"""
Dragon-V RVOP 平台部署脚本
专业红队作战平台 - 一键部署和初始化
"""

import os
import sys
import json
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('rvop_deploy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RVOPDeployer:
    def __init__(self, config_path: str = "config/rvop_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.project_root = os.path.dirname(os.path.abspath(__file__))

    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "platform": {
                "name": "Dragon-V RVOP",
                "version": "1.0.0",
                "description": "专业红队作战平台"
            },
            "deployment": {
                "target": "development",
                "create_directories": True,
                "setup_virtualenv": True,
                "install_dependencies": True,
                "generate_ssl": False,
                "create_service": False,
                "setup_docker": False
            },
            "directories": {
                "logs": "logs",
                "certs": "certs",
                "payloads": "payloads",
                "ranges": "ranges",
                "backups": "backups",
                "temp": "temp"
            },
            "components": {
                "c2_server": {
                    "enabled": True,
                    "port": 8080,
                    "ssl_port": 8443,
                    "enable_ssl": False
                },
                "web_interface": {
                    "enabled": True,
                    "port": 8081,
                    "host": "0.0.0.0"
                },
                "payload_generator": {
                    "enabled": True,
                    "output_dir": "payloads"
                },
                "exploitation_framework": {
                    "enabled": True,
                    "max_concurrent": 5
                },
                "persistence_manager": {
                    "enabled": True,
                    "database_path": "persistence.db"
                },
                "range_controller": {
                    "enabled": True,
                    "config_path": "config/range_config.yaml"
                }
            },
            "security": {
                "generate_api_keys": True,
                "setup_firewall": False,
                "enable_ssl": False,
                "ssl_country": "CN",
                "ssl_state": "Beijing",
                "ssl_locality": "Beijing",
                "ssl_organization": "Dragon-V RVOP",
                "ssl_email": "admin@dragon-v.com"
            },
            "monitoring": {
                "enable_health_check": True,
                "health_check_interval": 30,
                "enable_performance_monitoring": True,
                "log_rotation": True,
                "max_log_size": "10MB",
                "backup_count": 5
            }
        }

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except FileNotFoundError:
            logger.info(f"配置文件 {self.config_path} 不存在，使用默认配置")

        return default_config

    def _check_prerequisites(self) -> bool:
        """检查部署前置条件"""
        logger.info("检查部署前置条件...")

        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            logger.error(f"需要Python 3.8或更高版本，当前版本: {python_version.major}.{python_version.minor}")
            return False

        # 检查必要的外部程序
        required_programs = [
            ("python", "Python解释器"),
            ("pip", "Python包管理器")
        ]

        if self.config["deployment"]["setup_docker"]:
            required_programs.append(("docker", "Docker"))

        for program, description in required_programs:
            if not self._check_program(program):
                logger.error(f"缺少必要程序: {description} ({program})")
                return False

        # 检查网络连接
        if not self._check_network():
            logger.warning("网络连接检查失败，某些功能可能无法正常工作")

        logger.info("前置条件检查完成")
        return True

    def _check_program(self, program: str) -> bool:
        """检查程序是否存在"""
        try:
            subprocess.run([program, "--version"],
                          capture_output=True,
                          check=True,
                          timeout=10)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_network(self) -> bool:
        """检查网络连接"""
        try:
            subprocess.run(["ping", "-c", "1", "8.8.8.8"],
                          capture_output=True,
                          timeout=10)
            return True
        except subprocess.TimeoutExpired:
            return False

    def _create_directories(self):
        """创建必要的目录"""
        logger.info("创建目录结构...")

        directories = self.config["directories"]
        for dir_name, dir_path in directories.items():
            full_path = os.path.join(self.project_root, dir_path)
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"创建目录: {full_path}")

        # 创建子目录
        subdirectories = [
            "logs/c2", "logs/exploitation", "logs/persistence",
            "payloads/generated", "payloads/templates", "payloads/obfuscated",
            "ranges/environments", "ranges/images", "ranges/backups",
            "backups/data", "backups/config", "backups/logs",
            "temp/downloads", "temp/uploads", "temp/extracted"
        ]

        for subdir in subdirectories:
            full_path = os.path.join(self.project_root, subdir)
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"创建子目录: {full_path}")

        # 创建权限文件
        permission_file = os.path.join(self.project_root, "PERMISSIONS.md")
        with open(permission_file, 'w', encoding='utf-8') as f:
            f.write("""# Dragon-V RVOP 权限说明

## 授权使用声明
本平台仅授权给具备合法授权的红队测试和安全研究人员使用。

## 使用限制
- 不得用于任何未经授权的系统测试
- 不得用于任何非法活动
- 仅在授权的靶场环境中使用
- 必须遵守相关法律法规

## 风险提示
- 本平台包含强大的攻击能力
- 错误使用可能导致严重后果
- 使用前请确保获得适当的授权
- 建议在隔离环境中进行测试

## 联系方式
如需技术支持或授权咨询，请联系:
- Email: security@dragon-v.com
- GitHub: https://github.com/dragon-v/rvop
""")
        logger.info("创建权限文件")

    def _setup_virtualenv(self):
        """设置虚拟环境"""
        logger.info("设置Python虚拟环境...")

        venv_path = os.path.join(self.project_root, "venv")

        # 检查是否已存在虚拟环境
        if os.path.exists(venv_path):
            logger.info("虚拟环境已存在，跳过创建")
            return True

        try:
            subprocess.run([sys.executable, "-m", "venv", venv_path],
                          check=True, capture_output=True)
            logger.info("虚拟环境创建成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"虚拟环境创建失败: {e}")
            return False

    def _install_dependencies(self):
        """安装依赖包"""
        logger.info("安装Python依赖包...")

        requirements = [
            "aiohttp>=3.8.0",
            "jinja2>=3.0.0",
            "pyyaml>=6.0",
            "cryptography>=3.4.0",
            "requests>=2.28.0",
            "asyncio>=3.4.3",
            "sqlalchemy>=1.4.0",
            "psutil>=5.9.0",
            "python-dotenv>=0.19.0",
            "schedule>=1.1.0",
            "colorama>=0.4.0",
            "tqdm>=4.64.0",
            "click>=8.0.0",
            "rich>=12.0.0"
        ]

        pip_install_cmd = [sys.executable, "-m", "pip", "install", "-r", "-"]
        pip_process = subprocess.Popen(pip_install_cmd,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True)

        pip_process.communicate(input='\n'.join(requirements))

        if pip_process.returncode == 0:
            logger.info("依赖包安装完成")
            return True
        else:
            logger.error("依赖包安装失败")
            return False

    def _generate_ssl_certificates(self):
        """生成SSL证书"""
        logger.info("生成SSL证书...")

        if not self.config["security"]["enable_ssl"]:
            logger.info("SSL生成已禁用，跳过")
            return True

        certs_dir = os.path.join(self.project_root, "certs")
        cert_file = os.path.join(certs_dir, "server.crt")
        key_file = os.path.join(certs_dir, "server.key")

        # 检查证书是否已存在
        if os.path.exists(cert_file) and os.path.exists(key_file):
            logger.info("SSL证书已存在，跳过生成")
            return True

        security_config = self.config["security"]
        subject = f"/C={security_config['ssl_country']}/ST={security_config['ssl_state']}/L={security_config['ssl_locality']}/O={security_config['ssl_organization']}/CN=localhost"

        try:
            # 生成私钥
            subprocess.run([
                "openssl", "genrsa", "-out", key_file, "2048"
            ], check=True, capture_output=True)

            # 生成证书签名请求
            subprocess.run([
                "openssl", "req", "-new", "-key", key_file, "-out", f"{cert_file}.csr",
                "-subj", subject
            ], check=True, capture_output=True)

            # 生成自签名证书
            subprocess.run([
                "openssl", "x509", "-req", "-days", "365", "-in", f"{cert_file}.csr",
                "-signkey", key_file, "-out", cert_file
            ], check=True, capture_output=True)

            # 删除临时文件
            os.remove(f"{cert_file}.csr")

            logger.info("SSL证书生成完成")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("OpenSSL未安装，跳过SSL证书生成")
            return False

    def _setup_systemd_service(self):
        """设置系统服务"""
        logger.info("设置系统服务...")

        if not self.config["deployment"]["create_service"]:
            logger.info("系统服务创建已禁用，跳过")
            return True

        # 检查是否为root用户
        if os.geteuid() != 0:
            logger.warning("非root用户，无法创建系统服务")
            return False

        service_content = f"""[Unit]
Description=Dragon-V RVOP Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
ExecStart={os.path.join(self.project_root, "venv", "bin", "python")} {os.path.join(self.project_root, "rvop", "main_orchestrator.py")}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

        service_file = "/etc/systemd/system/rvop.service"

        try:
            with open(service_file, 'w') as f:
                f.write(service_content)

            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "rvop.service"], check=True)
            subprocess.run(["systemctl", "start", "rvop.service"], check=True)

            logger.info("系统服务创建并启动成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"系统服务设置失败: {e}")
            return False

    def _setup_docker(self):
        """设置Docker环境"""
        logger.info("设置Docker环境...")

        if not self.config["deployment"]["setup_docker"]:
            logger.info("Docker设置已禁用，跳过")
            return True

        # 检查Docker是否安装并运行
        if not self._check_program("docker"):
            logger.warning("Docker未安装，跳过Docker设置")
            return False

        # 检查Docker服务是否运行
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=30)
            logger.info("Docker服务运行正常")
        except subprocess.CalledProcessError:
            logger.warning("Docker服务未运行，请手动启动")
            return False

        # 创建Docker Compose配置
        docker_compose_content = """
version: '3.8'

services:
  rvop-platform:
    build: .
    ports:
      - "8080:8080"
      - "8081:8081"
      - "8443:8443"
    volumes:
      - ./logs:/app/logs
      - ./certs:/app/certs
      - ./payloads:/app/payloads
      - ./ranges:/app/ranges
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped
    networks:
      - rvop-network

  target-web-1:
    image: dvwa/dvwa:latest
    ports:
      - "8082:80"
    environment:
      MYSQL_ROOT_PASSWORD: root
      DVWA_SECURITY: low
    restart: unless-stopped
    networks:
      - rvop-network

  target-web-2:
    image: webpwnized/sqli-labs:latest
    ports:
      - "8083:80"
    restart: unless-stopped
    networks:
      - rvop-network

networks:
  rvop-network:
    driver: bridge
"""

        docker_compose_file = os.path.join(self.project_root, "docker-compose.yml")
        with open(docker_compose_file, 'w') as f:
            f.write(docker_compose_content.strip())

        # 创建Dockerfile
        dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 设置虚拟环境
RUN python -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install -r requirements.txt

# 创建非root用户
RUN useradd -m -u 1000 rvop && chown -R rvop:rvop /app
USER rvop

# 暴露端口
EXPOSE 8080 8081 8443

# 启动命令
CMD ["/app/venv/bin/python", "/app/rvop/main_orchestrator.py"]
"""

        dockerfile = os.path.join(self.project_root, "Dockerfile")
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content.strip())

        logger.info("Docker配置文件创建完成")
        return True

    def _create_startup_scripts(self):
        """创建启动脚本"""
        logger.info("创建启动脚本...")

        # 创建启动脚本
        startup_script = f"""#!/bin/bash
# Dragon-V RVOP 启动脚本

cd {self.project_root}

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export PYTHONPATH={self.project_root}
export RVOP_CONFIG={self.config_path}

# 启动平台
echo "正在启动 Dragon-V RVOP 平台..."

# 启动C2服务器
nohup python rvop/c2_server.py > logs/c2_server.log 2>&1 &
C2_PID=$!

# 启动Web界面
nohup python rvop/web_interface.py > logs/web_interface.log 2>&1 &
WEB_PID=$!

# 启动主平台
python rvop/main_orchestrator.py &
MAIN_PID=$!

echo "平台启动完成:"
echo "  C2服务器: http://localhost:8080 (PID: $C2_PID)"
echo "  Web界面: http://localhost:8081 (PID: $WEB_PID)"
echo "  主平台: 运行中 (PID: $MAIN_PID)"

# 保存进程ID
echo $C2_PID > .c2_pid
echo $WEB_PID > .web_pid
echo $MAIN_PID > .main_pid

# 等待用户输入
read -p "按任意键停止平台..." -n 1 -s

echo "正在停止平台..."
kill $C2_PID 2>/dev/null
kill $WEB_PID 2>/dev/null
kill $MAIN_PID 2>/dev/null

rm -f .c2_pid .web_pid .main_pid

echo "平台已停止"
"""

        startup_file = os.path.join(self.project_root, "start.sh")
        with open(startup_file, 'w') as f:
            f.write(startup_script)

        # 设置执行权限
        os.chmod(startup_file, 0o755)

        # 创建停止脚本
        stop_script = """#!/bin/bash
# Dragon-V RVOP 停止脚本

cd {self.project_root}

# 读取进程ID
if [ -f .c2_pid ]; then
    kill $(cat .c2_pid) 2>/dev/null
    rm .c2_pid
fi

if [ -f .web_pid ]; then
    kill $(cat .web_pid) 2>/dev/null
    rm .web_pid
fi

if [ -f .main_pid ]; then
    kill $(cat .main_pid) 2>/dev/null
    rm .main_pid
fi

# 强制杀死相关进程
pkill -f "rvop/main_orchestrator.py" 2>/dev/null
pkill -f "rvop/c2_server.py" 2>/dev/null
pkill -f "rvop/web_interface.py" 2>/dev/null

echo "平台已停止"
"""

        stop_file = os.path.join(self.project_root, "stop.sh")
        with open(stop_file, 'w') as f:
            f.write(stop_script.format(project_root=self.project_root))

        os.chmod(stop_file, 0o755)

        # 创建状态检查脚本
        status_script = f"""#!/bin/bash
# Dragon-V RVOP 状态检查脚本

cd {self.project_root}

echo "=== Dragon-V RVOP 平台状态 ==="

# 检查C2服务器
if ps aux | grep -v grep | grep "rvop/c2_server.py" > /dev/null; then
    echo "  C2服务器: 运行中"
    echo "  访问地址: http://localhost:8080"
else
    echo "  C2服务器: 未运行"
fi

# 检查Web界面
if ps aux | grep -v grep | grep "rvop/web_interface.py" > /dev/null; then
    echo "  Web界面: 运行中"
    echo "  访问地址: http://localhost:8081"
else
    echo "  Web界面: 未运行"
fi

# 检查主平台
if ps aux | grep -v grep | grep "rvop/main_orchestrator.py" > /dev/null; then
    echo "  主平台: 运行中"
else
    echo "  主平台: 未运行"
fi

echo "=== 系统资源使用 ==="
echo "内存使用: $(free -h | grep Mem | awk '{{print $3 "/" $2}}')"
echo "磁盘使用: $(df -h . | tail -1 | awk '{{print $3 "/" $2 " (" $5 ")"}}')"

echo "=== 日志文件 ==="
if [ -f "logs/c2_server.log" ]; then
    echo "  C2日志: logs/c2_server.log ($(wc -l < logs/c2_server.log) 行)"
fi

if [ -f "logs/web_interface.log" ]; then
    echo "  Web日志: logs/web_interface.log ($(wc -l < logs/web_interface.log) 行)"
fi

if [ -f "logs/rvop_orchestrator.log" ]; then
    echo "  平台日志: logs/rvop_orchestrator.log ($(wc -l < logs/rvop_orchestrator.log) 行)"
fi
"""

        status_file = os.path.join(self.project_root, "status.sh")
        with open(status_file, 'w') as f:
            f.write(status_script)

        os.chmod(status_file, 0o755)

        logger.info("启动脚本创建完成")

    def _create_requirements_file(self):
        """创建requirements.txt文件"""
        logger.info("创建requirements.txt文件...")

        requirements = [
            "aiohttp>=3.8.0",
            "jinja2>=3.0.0",
            "pyyaml>=6.0",
            "cryptography>=3.4.0",
            "requests>=2.28.0",
            "asyncio>=3.4.3",
            "sqlalchemy>=1.4.0",
            "psutil>=5.9.0",
            "python-dotenv>=0.19.0",
            "schedule>=1.1.0",
            "colorama>=0.4.0",
            "tqdm>=4.64.0",
            "click>=8.0.0",
            "rich>=12.0.0"
        ]

        requirements_file = os.path.join(self.project_root, "requirements.txt")
        with open(requirements_file, 'w', encoding='utf-8') as f:
            for req in requirements:
                f.write(f"{req}\n")

        logger.info("requirements.txt创建完成")

    def _create_readme_file(self):
        """创建README文件"""
        logger.info("创建README文件...")

        readme_content = f"""# Dragon-V Red Team Operations Platform (RVOP)

## 概述
Dragon-V RVOP 是一个专业的红队作战平台，提供完整的命令控制、载荷生成、自动化利用、持久化管理和靶场控制功能。

## 特性
- **C2服务器**: 完整的命令控制基础设施
- **载荷生成器**: 多种平台和语言的恶意载荷生成
- **自动化利用框架**: 自动化漏洞利用和链式攻击
- **持久化管理**: 多种持久化机制创建和管理
- **靶场控制器**: Docker环境下的靶场管理
- **Web管理界面**: 直观的Web控制台
- **链式攻击**: 多步骤自动化攻击链
- **规避技术**: 先进的安全规避技术

## 系统要求
- Python 3.8+
- Linux/macOS/Windows
- Docker (可选，用于靶场环境)
- OpenSSL (可选，用于SSL证书)

## 快速开始

### 1. 部署平台
```bash
# 运行部署脚本
python rvop/deploy.py

# 或者手动安装
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

### 2. 启动平台
```bash
# 使用启动脚本
./start.sh

# 或直接启动
python rvop/main_orchestrator.py
```

### 3. 访问界面
- **Web管理界面**: http://localhost:8081
- **C2服务器**: http://localhost:8080
- **API接口**: http://localhost:8080/api

## 配置说明
所有配置文件位于 `config/` 目录下：
- `range_config.yaml`: 靶场环境配置
- `exploitation_config.json`: 利用框架配置
- `c2_config.json`: C2服务器配置

## 组件说明

### C2服务器
- 代理注册和管理
- 任务分发和结果收集
- 心跳监控
- HTTPS支持

### 载荷生成器
- PowerShell载荷
- JSP/Servlet载荷
- ELF载荷
- EXE载荷
- 自动混淆和加密

### 利用框架
- SQL注入利用
- 文件上传利用
- XSS利用
- 命令注入利用
- 链式攻击

### 持久化管理
- Windows服务
- Cron任务
- Webshell
- DLL注入

### 靶场控制器
- Docker容器管理
- 靶场环境模板
- 网络配置
- 自动清理

## 使用权限
⚠️ **重要提醒**: 本平台仅授权给具备合法授权的红队测试和安全研究人员使用。严禁用于任何未经授权的系统测试或非法活动。

## 故障排除
- 查看日志文件: `logs/` 目录
- 检查端口占用: `netstat -tulpn`
- 重启平台: `./stop.sh && ./start.sh`
- 重新部署: `python rvop/deploy.py --redeploy`

## 技术支持
- GitHub: https://github.com/dragon-v/rvop
- Email: security@dragon-v.com

## 许可证
本项目仅用于授权的安全测试和研究目的。使用者需自行承担使用风险，并遵守相关法律法规。

---

**注意**: 本平台包含强大的安全测试能力，请仅在合法授权的环境中使用。
"""

        readme_file = os.path.join(self.project_root, "README.md")
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        logger.info("README文件创建完成")

    def deploy(self):
        """执行完整的部署流程"""
        logger.info("=== 开始部署 Dragon-V RVOP 平台 ===")

        start_time = datetime.now()

        try:
            # 1. 检查前置条件
            if not self._check_prerequisites():
                logger.error("前置条件检查失败，部署中止")
                return False

            # 2. 创建目录结构
            if self.config["deployment"]["create_directories"]:
                self._create_directories()

            # 3. 设置虚拟环境
            if self.config["deployment"]["setup_virtualenv"]:
                if not self._setup_virtualenv():
                    logger.error("虚拟环境设置失败")
                    return False

            # 4. 安装依赖
            if self.config["deployment"]["install_dependencies"]:
                if not self._install_dependencies():
                    logger.error("依赖安装失败")
                    return False

            # 5. 创建requirements文件
            self._create_requirements_file()

            # 6. 生成SSL证书
            if not self._generate_ssl_certificates():
                logger.warning("SSL证书生成失败")

            # 7. 设置系统服务
            if not self._setup_systemd_service():
                logger.warning("系统服务设置失败")

            # 8. 设置Docker环境
            if not self._setup_docker():
                logger.warning("Docker设置失败")

            # 9. 创建启动脚本
            self._create_startup_scripts()

            # 10. 创建README文件
            self._create_readme_file()

            # 部署完成
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("=== 部署完成 ===")
            logger.info(f"部署时间: {duration}")
            logger.info("平台访问地址:")
            logger.info(f"  - Web管理界面: http://localhost:8081")
            logger.info(f"  - C2服务器: http://localhost:8080")
            logger.info(f"  - API接口: http://localhost:8080/api")
            logger.info("")
            logger.info("可用的启动脚本:")
            logger.info(f"  - {self.project_root}/start.sh - 启动平台")
            logger.info(f"  - {self.project_root}/stop.sh - 停止平台")
            logger.info(f"  - {self.project_root}/status.sh - 查看状态")
            logger.info("")
            logger.info("重要提醒: 请仅在授权的环境中使用本平台")

            return True

        except Exception as e:
            logger.error(f"部署过程中发生错误: {e}")
            return False

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dragon-V RVOP 平台部署脚本')
    parser.add_argument('--config', '-c', default='config/rvop_config.json',
                       help='配置文件路径')
    parser.add_argument('--redeploy', '-r', action='store_true',
                       help='重新部署（清理现有安装）')

    args = parser.parse_args()

    # 如果重新部署，清理现有文件
    if args.redeploy:
        logger.info("清理现有安装...")
        shutil.rmtree('venv', ignore_errors=True)
        shutil.rmtree('logs', ignore_errors=True)
        shutil.rmtree('certs', ignore_errors=True)
        shutil.rmtree('payloads', ignore_errors=True)
        shutil.rmtree('ranges', ignore_errors=True)

        # 删除可能存在的进程
        subprocess.run(['pkill', '-f', 'rvop/main_orchestrator.py'],
                      capture_output=True)
        subprocess.run(['pkill', '-f', 'rvop/c2_server.py'],
                      capture_output=True)
        subprocess.run(['pkill', '-f', 'rvop/web_interface.py'],
                      capture_output=True)

    # 执行部署
    deployer = RVOPDeployer(args.config)
    success = deployer.deploy()

    if success:
        print("\n✅ 部署完成！可以开始使用 Dragon-V RVOP 平台了。")
        sys.exit(0)
    else:
        print("\n❌ 部署失败！请检查日志文件了解详情。")
        sys.exit(1)

if __name__ == "__main__":
    main()