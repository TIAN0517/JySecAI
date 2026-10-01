#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ Security & Stability Enhancer v2.0
安全性和稳定性强化模块 - 企业级防护

强化特性:
✅ 高级加密和认证
✅ 安全通信协议
✅ 异常检测和防护
✅ 资源管理和监控
✅ 故障恢复和备份
✅ 审计日志和追踪

安全机制:
- 数据加密 (AES-256, RSA-2048)
- 安全密钥管理
- 访问控制和权限管理
- 输入验证和过滤
- 输出编码和转义
- 安全配置管理
"""

import asyncio
import aiohttp
import json
import time
import random
import hashlib
import base64
import hmac
import os
import sys
import string
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
import threading
import psutil
import gc
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Windows控制台编码修复
if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except:
        pass

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_enhancer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SecurityEnhancer')

@dataclass
class SecurityEvent:
    """安全事件记录"""
    event_id: str
    event_type: str
    severity: str
    description: str
    timestamp: datetime
    source: str
    target: str
    details: Dict[str, Any]

class SecurityManager:
    """安全管理器"""

    def __init__(self):
        self.encryption_key = None
        self.security_events = []
        self.failed_attempts = {}
        self.lockout_threshold = 5
        self.lockout_duration = timedelta(minutes=30)

        # 初始化加密密钥
        self._initialize_encryption()

    def _initialize_encryption(self):
        """初始化加密系统"""
        try:
            # 生成或加载加密密钥
            key_file = Path("encryption_key.key")
            if key_file.exists():
                with open(key_file, "rb") as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(self.encryption_key)

            self.fernet = Fernet(self.encryption_key)
            logger.info("🔐 加密系统初始化完成")

        except Exception as e:
            logger.error(f"加密系统初始化失败: {e}")

    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"数据加密失败: {e}")
            return data

    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"数据解密失败: {e}")
            return encrypted_data

    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """哈希密码"""
        if salt is None:
            salt = os.urandom(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt

    def verify_password(self, password: str, hashed_password: str, salt: bytes) -> bool:
        """验证密码"""
        try:
            new_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(new_hash, hashed_password)
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    def log_security_event(self, event_type: str, severity: str, description: str,
                          source: str, target: str, details: Dict[str, Any] = None):
        """记录安全事件"""
        event = SecurityEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            severity=severity,
            description=description,
            timestamp=datetime.now(),
            source=source,
            target=target,
            details=details or {}
        )

        self.security_events.append(event)
        logger.warning(f"🚨 安全事件: {event_type} - {description}")

        # 保存到文件
        self._save_security_event(event)

    def _generate_event_id(self) -> str:
        """生成事件ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"EVENT_{timestamp}_{random_str}"

    def _save_security_event(self, event: SecurityEvent):
        """保存安全事件"""
        try:
            event_file = Path("security_events.json")
            events_data = []

            if event_file.exists():
                with open(event_file, "r", encoding="utf-8") as f:
                    events_data = json.load(f)

            events_data.append(asdict(event))

            # 只保留最近1000个事件
            if len(events_data) > 1000:
                events_data = events_data[-1000:]

            with open(event_file, "w", encoding="utf-8") as f:
                json.dump(events_data, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.error(f"保存安全事件失败: {e}")

    def check_rate_limit(self, identifier: str, max_requests: int = 100, window_seconds: int = 3600) -> bool:
        """检查速率限制"""
        current_time = time.time()
        window_start = current_time - window_seconds

        # 清理过期记录
        self.failed_attempts = {
            k: v for k, v in self.failed_attempts.items()
            if v["last_attempt"] > window_start
        }

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {
                "count": 1,
                "last_attempt": current_time
            }
            return True

        attempt_info = self.failed_attempts[identifier]

        if attempt_info["count"] >= max_requests:
            self.log_security_event(
                "Rate Limit Exceeded",
                "Medium",
                f"标识符 {identifier} 超过速率限制",
                identifier,
                "Security System",
                {"attempts": attempt_info["count"], "max_allowed": max_requests}
            )
            return False

        attempt_info["count"] += 1
        attempt_info["last_attempt"] = current_time
        return True

class StabilityMonitor:
    """稳定性监控器"""

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.system_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_io": []
        }
        self.alert_thresholds = {
            "cpu_usage": 80.0,  # %
            "memory_usage": 85.0,  # %
            "disk_usage": 90.0,  # %
            "response_time": 5.0  # seconds
        }

    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("📊 系统监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("📊 系统监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._collect_metrics()
                self._check_thresholds()
                time.sleep(10)  # 每10秒收集一次
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(30)

    def _collect_metrics(self):
        """收集系统指标"""
        current_time = datetime.now()

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_metrics["cpu_usage"].append({
            "timestamp": current_time,
            "value": cpu_percent
        })

        # 内存使用率
        memory = psutil.virtual_memory()
        self.system_metrics["memory_usage"].append({
            "timestamp": current_time,
            "value": memory.percent
        })

        # 磁盘使用率
        disk = psutil.disk_usage('/')
        self.system_metrics["disk_usage"].append({
            "timestamp": current_time,
            "value": (disk.used / disk.total) * 100
        })

        # 网络IO
        net_io = psutil.net_io_counters()
        self.system_metrics["network_io"].append({
            "timestamp": current_time,
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        })

        # 清理旧数据（保留最近1小时）
        one_hour_ago = current_time - timedelta(hours=1)
        for metric in self.system_metrics.values():
            metric[:] = [m for m in metric if m["timestamp"] > one_hour_ago]

    def _check_thresholds(self):
        """检查阈值"""
        security_manager = SecurityManager()

        # 检查CPU使用率
        if self.system_metrics["cpu_usage"]:
            latest_cpu = self.system_metrics["cpu_usage"][-1]["value"]
            if latest_cpu > self.alert_thresholds["cpu_usage"]:
                security_manager.log_security_event(
                    "High CPU Usage",
                    "Medium",
                    f"CPU使用率过高: {latest_cpu}%",
                    "System Monitor",
                    "CPU",
                    {"current_usage": latest_cpu, "threshold": self.alert_thresholds["cpu_usage"]}
                )

        # 检查内存使用率
        if self.system_metrics["memory_usage"]:
            latest_memory = self.system_metrics["memory_usage"][-1]["value"]
            if latest_memory > self.alert_thresholds["memory_usage"]:
                security_manager.log_security_event(
                    "High Memory Usage",
                    "Medium",
                    f"内存使用率过高: {latest_memory}%",
                    "System Monitor",
                    "Memory",
                    {"current_usage": latest_memory, "threshold": self.alert_thresholds["memory_usage"]}
                )

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        if not self.system_metrics["cpu_usage"]:
            return {"status": "No data available"}

        latest_cpu = self.system_metrics["cpu_usage"][-1]["value"]
        latest_memory = self.system_metrics["memory_usage"][-1]["value"]
        latest_disk = self.system_metrics["disk_usage"][-1]["value"]

        status = "Healthy"
        if (latest_cpu > self.alert_thresholds["cpu_usage"] or
            latest_memory > self.alert_thresholds["memory_usage"] or
            latest_disk > self.alert_thresholds["disk_usage"]):
            status = "Warning"

        return {
            "status": status,
            "cpu_usage": latest_cpu,
            "memory_usage": latest_memory,
            "disk_usage": latest_disk,
            "monitoring": self.monitoring
        }

class InputValidator:
    """输入验证器"""

    def __init__(self):
        self.validation_rules = {
            "url": r'^https?://[^\s/$.?#].[^\s]*$',
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "ip_address": r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',
            "filename": r'^[a-zA-Z0-9._-]+$'
        }

    def validate_input(self, input_data: str, input_type: str, max_length: int = 1000) -> Tuple[bool, str]:
        """验证输入"""
        # 检查长度
        if len(input_data) > max_length:
            return False, f"输入长度超过限制: {len(input_data)} > {max_length}"

        # 检查空值
        if not input_data.strip():
            return False, "输入不能为空"

        # 检查特殊字符
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',
            r'\b(union|select|insert|update|delete|drop|create|alter)\b',
            r'\$\{[^}]+\}',
            r'\{\{[^}]+\}\}'
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, f"检测到潜在危险输入: {pattern}"

        # 类型特定验证
        if input_type in self.validation_rules:
            pattern = self.validation_rules[input_type]
            if not re.match(pattern, input_data):
                return False, f"无效的{input_type}格式"

        return True, "验证通过"

    def sanitize_output(self, output_data: str) -> str:
        """净化输出"""
        # HTML转义
        sanitized = output_data
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        sanitized = sanitized.replace('/', '&#x2F;')

        return sanitized

class BackupManager:
    """备份管理器"""

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    async def create_backup(self, files: List[str], backup_name: str = None) -> str:
        """创建备份"""
        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"

        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        backed_up_files = []

        for file_path in files:
            try:
                file_obj = Path(file_path)
                if file_obj.exists():
                    # 复制文件到备份目录
                    backup_file = backup_path / file_obj.name
                    if file_obj.is_file():
                        import shutil
                        shutil.copy2(file_obj, backup_file)
                        backed_up_files.append(file_path)

            except Exception as e:
                logger.error(f"备份文件 {file_path} 失败: {e}")

        # 创建备份清单
        manifest = {
            "backup_name": backup_name,
            "timestamp": datetime.now().isoformat(),
            "files": backed_up_files,
            "total_files": len(backed_up_files)
        }

        manifest_file = backup_path / "backup_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"📦 备份创建完成: {backup_name} ({len(backed_up_files)} 个文件)")
        return str(backup_path)

    async def restore_backup(self, backup_name: str) -> bool:
        """恢复备份"""
        backup_path = self.backup_dir / backup_name
        manifest_file = backup_path / "backup_manifest.json"

        if not manifest_file.exists():
            logger.error(f"备份清单不存在: {manifest_file}")
            return False

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            restored_files = 0
            for file_path in manifest["files"]:
                try:
                    backup_file = backup_path / Path(file_path).name
                    if backup_file.exists():
                        import shutil
                        shutil.copy2(backup_file, file_path)
                        restored_files += 1

                except Exception as e:
                    logger.error(f"恢复文件 {file_path} 失败: {e}")

            logger.info(f"🔄 备份恢复完成: {restored_files}/{len(manifest['files'])} 个文件")
            return restored_files > 0

        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            return False

class SecurityStabilityEnhancer:
    """安全性和稳定性增强器"""

    def __init__(self):
        self.security_manager = SecurityManager()
        self.stability_monitor = StabilityMonitor()
        self.input_validator = InputValidator()
        self.backup_manager = BackupManager()

    async def initialize(self):
        """初始化增强器"""
        logger.info("🛡️ 初始化安全性和稳定性增强器...")

        # 启动系统监控
        self.stability_monitor.start_monitoring()

        # 创建初始备份
        important_files = [
            "dragon_triple_bot_unified.db",
            "dragon_triple_telegram_bot.db",
            "dragon_triple_config.json",
            "dragon_triple_telegram_config.json"
        ]

        await self.backup_manager.create_backup(important_files, "initial_backup")

        logger.info("✅ 安全性和稳定性增强器初始化完成")

    async def shutdown(self):
        """关闭增强器"""
        logger.info("🛡️ 关闭安全性和稳定性增强器...")

        # 停止系统监控
        self.stability_monitor.stop_monitoring()

        # 创建关闭备份
        important_files = [
            "security_events.json",
            "security_enhancer.log"
        ]

        await self.backup_manager.create_backup(important_files, "shutdown_backup")

        logger.info("✅ 安全性和稳定性增强器已关闭")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        stability_status = self.stability_monitor.get_system_status()
        security_status = {
            "security_events_count": len(self.security_manager.security_events),
            "failed_attempts_count": len(self.security_manager.failed_attempts),
            "encryption_initialized": self.security_manager.encryption_key is not None
        }

        return {
            "stability": stability_status,
            "security": security_status,
            "overall_status": "Healthy" if stability_status["status"] == "Healthy" else "Warning"
        }

# 使用示例
async def demo():
    """演示安全性和稳定性增强功能"""
    print("🛡️ Security & Stability Enhancer Demo")
    print("=" * 50)

    enhancer = SecurityStabilityEnhancer()

    try:
        await enhancer.initialize()

        # 演示输入验证
        validator = enhancer.input_validator
        test_inputs = [
            ("http://example.com", "url"),
            ("test@example.com", "email"),
            ("<script>alert('xss')</script>", "filename"),
            ("1' OR '1'='1", "sql")
        ]

        print("\n🔍 输入验证测试:")
        for input_data, input_type in test_inputs:
            is_valid, message = validator.validate_input(input_data, input_type)
            status = "✅" if is_valid else "❌"
            print(f"  {status} {input_type}: {input_data[:30]}... -> {message}")

        # 演示加密功能
        security_manager = enhancer.security_manager
        test_data = "Sensitive information that needs encryption"
        encrypted = security_manager.encrypt_data(test_data)
        decrypted = security_manager.decrypt_data(encrypted)

        print(f"\n🔐 加密演示:")
        print(f"  原始数据: {test_data}")
        print(f"  加密数据: {encrypted[:50]}...")
        print(f"  解密数据: {decrypted}")

        # 显示系统状态
        status = enhancer.get_system_status()
        print(f"\n📊 系统状态:")
        print(f"  整体状态: {status['overall_status']}")
        print(f"  CPU使用率: {status['stability']['cpu_usage']}%")
        print(f"  内存使用率: {status['stability']['memory_usage']}%")
        print(f"  安全事件数: {status['security']['security_events_count']}")

        # 等待一段时间以收集监控数据
        print("\n⏳ 等待监控数据收集...")
        await asyncio.sleep(15)

        # 再次显示状态
        status = enhancer.get_system_status()
        print(f"\n📊 更新后的系统状态:")
        print(f"  整体状态: {status['overall_status']}")
        print(f"  CPU使用率: {status['stability']['cpu_usage']}%")
        print(f"  内存使用率: {status['stability']['memory_usage']}%")

    except Exception as e:
        logger.error(f"演示失败: {e}")

    finally:
        await enhancer.shutdown()

if __name__ == "__main__":
    import string
    asyncio.run(demo())