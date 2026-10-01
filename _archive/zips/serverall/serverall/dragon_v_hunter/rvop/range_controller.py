#!/usr/bin/env python3
"""
Dragon-V RVOP Range Controller
专业红队作战平台 - 授权靶场控制器
管理测试环境、靶机配置和网络隔离
"""

import os
import json
import time
import docker
import subprocess
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import uuid
import yaml

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentStatus(Enum):
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    DESTROYED = "destroyed"
    ERROR = "error"

class NetworkType(Enum):
    ISOLATED = "isolated"
    ROUTED = "routed"
    BRIDGED = "bridged"

class VulnerabilityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TargetMachine:
    machine_id: str
    name: str
    image: str
    ip_address: str
    ports: Dict[str, int]
    status: EnvironmentStatus
    operating_system: str
    vulnerabilities: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    network_config: Dict[str, Any] = None

@dataclass
class RangeEnvironment:
    env_id: str
    name: str
    description: str
    network_type: NetworkType
    subnet: str
    target_machines: List[TargetMachine]
    created_at: datetime
    status: EnvironmentStatus = EnvironmentStatus.CREATING

@dataclass
class Operation:
    op_id: str
    name: str
    description: str
    target_env: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "planning"
    participants: List[str] = None
    objectives: List[str] = None

class RangeController:
    def __init__(self, config_path: str = "range_config.yaml"):
        self.config = self.load_config(config_path)
        self.docker_client = None
        self.environments: Dict[str, RangeEnvironment] = {}
        self.operations: Dict[str, Operation] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # 初始化数据库
        self.init_database()

        # 初始化Docker客户端
        self.init_docker()

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "docker_host": "unix:///var/run/docker.sock",
            "network_range": "172.20.0.0/24",
            "default_images": {
                "windows": "mcr.microsoft.com/windows/server:ltsc2022",
                "linux": "ubuntu:22.04",
                "web": "nginx:latest",
                "database": "mysql:8.0"
            },
            "vulnerable_images": [
                "vulhub/metasploit:latest",
                "vulhub/dvwa:latest",
                "vulhub/sqli-labs:latest"
            ],
            "network_isolation": True,
            "logging_level": "INFO"
        }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config:
                    default_config.update(config)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")

        return default_config

    def init_database(self):
        """初始化数据库"""
        os.makedirs("range_db", exist_ok=True)

        conn = sqlite3.connect("range_db/range.db")
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS environments (
                env_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                network_type TEXT,
                subnet TEXT,
                created_at TEXT,
                status TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                machine_id TEXT PRIMARY KEY,
                env_id TEXT,
                name TEXT,
                image TEXT,
                ip_address TEXT,
                ports TEXT,
                status TEXT,
                operating_system TEXT,
                vulnerabilities TEXT,
                created_at TEXT,
                last_used TEXT,
                FOREIGN KEY (env_id) REFERENCES environments (env_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                op_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                target_env TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                participants TEXT,
                objectives TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                op_id TEXT,
                machine_id TEXT,
                start_time TEXT,
                end_time TEXT,
                commands TEXT,
                FOREIGN KEY (op_id) REFERENCES operations (op_id),
                FOREIGN KEY (machine_id) REFERENCES machines (machine_id)
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("靶场数据库初始化完成")

    def init_docker(self):
        """初始化Docker客户端"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except Exception as e:
            logger.error(f"Docker客户端初始化失败: {e}")
            logger.info("将使用模拟模式")

    def create_environment(self, name: str, description: str, network_type: NetworkType = NetworkType.ISOLATED) -> RangeEnvironment:
        """创建靶场环境"""
        env_id = str(uuid.uuid4())
        env = RangeEnvironment(
            env_id=env_id,
            name=name,
            description=description,
            network_type=network_type,
            subnet=self.config["network_range"],
            target_machines=[],
            created_at=datetime.now()
        )

        # 在Docker中创建网络
        if self.docker_client and network_type == NetworkType.ISOLATED:
            try:
                network = self.docker_client.networks.create(
                    name=f"rvop-range-{env_id}",
                    driver="bridge",
                    enable_ipv6=True
                )
                logger.info(f"创建网络: {network.name}")
            except Exception as e:
                logger.error(f"网络创建失败: {e}")

        # 保存到数据库
        self.save_environment(env)

        # 添加默认靶机
        self.add_default_machines(env)

        logger.info(f"靶场环境创建成功: {name}")
        return env

    def add_default_machines(self, env: RangeEnvironment):
        """添加默认靶机"""
        default_machines = [
            {
                "name": "web-server",
                "image": "vulhub/dvwa:latest",
                "os": "linux",
                "vulnerabilities": ["sql_injection", "xss", "csrf"],
                "ports": {"80": 8080, "443": 8443}
            },
            {
                "name": "database-server",
                "image": "mysql:8.0",
                "os": "linux",
                "vulnerabilities": ["mysql_injection", "weak_password"],
                "ports": {"3306": 3306}
            },
            {
                "name": "windows-server",
                "image": "mcr.microsoft.com/windows/server:ltsc2022",
                "os": "windows",
                "vulnerabilities": ["smb_vulnerability", "rdp_weakness"],
                "ports": {"3389": 3389, "445": 445}
            }
        ]

        for machine_config in default_machines:
            machine = self.create_machine(
                env.env_id,
                machine_config["name"],
                machine_config["image"],
                machine_config["os"],
                machine_config["vulnerabilities"],
                machine_config["ports"]
            )
            env.target_machines.append(machine)

    def create_machine(self, env_id: str, name: str, image: str, operating_system: str, vulnerabilities: List[str], ports: Dict[str, int]) -> TargetMachine:
        """创建靶机"""
        machine_id = str(uuid.uuid4())
        ip_address = self.generate_ip_address()

        machine = TargetMachine(
            machine_id=machine_id,
            name=name,
            image=image,
            ip_address=ip_address,
            ports=ports,
            status=EnvironmentStatus.CREATING,
            operating_system=operating_system,
            vulnerabilities=vulnerabilities,
            created_at=datetime.now()
        )

        # 在Docker中创建容器
        if self.docker_client:
            try:
                container = self.docker_client.containers.run(
                    image=image,
                    name=f"rvop-{machine_id}",
                    detach=True,
                    ports={f"{port}/{protocol}": host_port for port, host_port in ports.items()},
                    network=f"rvop-range-{env_id}" if env_id else "bridge",
                    restart_policy="unless-stopped"
                )
                machine.status = EnvironmentStatus.RUNNING
                logger.info(f"创建容器: {container.name}")
            except Exception as e:
                logger.error(f"容器创建失败: {e}")
                machine.status = EnvironmentStatus.ERROR
        else:
            # 模拟创建容器
            machine.status = EnvironmentStatus.RUNNING
            logger.info(f"模拟创建容器: {name}")

        # 保存到数据库
        self.save_machine(env_id, machine)

        return machine

    def generate_ip_address(self) -> str:
        """生成IP地址"""
        # 使用网络范围的随机IP
        subnet = self.config["network_range"]
        base_ip = subnet.split('/')[0]
        octets = base_ip.split('.')

        # 生成主机部分
        last_octet = secrets.randbelow(254) + 1
        ip_address = f"{octets[0]}.{octets[1]}.{octets[2]}.{last_octet}"

        return ip_address

    def start_environment(self, env_id: str) -> bool:
        """启动靶场环境"""
        if env_id not in self.environments:
            return False

        env = self.environments[env_id]

        # 启动所有容器
        for machine in env.target_machines:
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(f"rvop-{machine.machine_id}")
                    container.start()
                    machine.status = EnvironmentStatus.RUNNING
                except Exception as e:
                    logger.error(f"启动容器失败: {e}")
                    machine.status = EnvironmentStatus.ERROR
            else:
                machine.status = EnvironmentStatus.RUNNING

        env.status = EnvironmentStatus.RUNNING
        self.save_environment(env)

        logger.info(f"靶场环境启动成功: {env.name}")
        return True

    def stop_environment(self, env_id: str) -> bool:
        """停止靶场环境"""
        if env_id not in self.environments:
            return False

        env = self.environments[env_id]

        # 停止所有容器
        for machine in env.target_machines:
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(f"rvop-{machine.machine_id}")
                    container.stop()
                    machine.status = EnvironmentStatus.STOPPED
                except Exception as e:
                    logger.error(f"停止容器失败: {e}")
            else:
                machine.status = EnvironmentStatus.STOPPED

        env.status = EnvironmentStatus.STOPPED
        self.save_environment(env)

        logger.info(f"靶场环境停止成功: {env.name}")
        return True

    def destroy_environment(self, env_id: str) -> bool:
        """销毁靶场环境"""
        if env_id not in self.environments:
            return False

        env = self.environments[env_id]

        # 删除所有容器
        for machine in env.target_machines:
            if self.docker_client:
                try:
                    container = self.docker_client.containers.get(f"rvop-{machine.machine_id}")
                    container.remove(force=True)
                except Exception as e:
                    logger.error(f"删除容器失败: {e}")

        # 删除网络
        if self.docker_client:
            try:
                network = self.docker_client.networks.get(f"rvop-range-{env_id}")
                network.remove()
            except Exception as e:
                logger.error(f"删除网络失败: {e}")

        env.status = EnvironmentStatus.DESTROYED
        self.save_environment(env)

        # 从内存中移除
        del self.environments[env_id]

        logger.info(f"靶场环境销毁成功: {env.name}")
        return True

    def create_operation(self, name: str, description: str, target_env: str, participants: List[str], objectives: List[str]) -> Operation:
        """创建操作"""
        op_id = str(uuid.uuid4())
        operation = Operation(
            op_id=op_id,
            name=name,
            description=description,
            target_env=target_env,
            start_time=datetime.now(),
            participants=participants,
            objectives=objectives
        )

        self.operations[op_id] = operation
        self.save_operation(operation)

        logger.info(f"操作创建成功: {name}")
        return operation

    def start_session(self, op_id: str, machine_id: str) -> str:
        """启动会话"""
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "op_id": op_id,
            "machine_id": machine_id,
            "start_time": datetime.now(),
            "end_time": None,
            "commands": []
        }

        self.sessions[session_id] = session
        self.save_session(session)

        logger.info(f"会话启动成功: {session_id}")
        return session_id

    def end_session(self, session_id: str) -> bool:
        """结束会话"""
        if session_id not in self.sessions:
            return False

        session = self.sessions[session_id]
        session["end_time"] = datetime.now()

        self.save_session(session)
        del self.sessions[session_id]

        logger.info(f"会话结束成功: {session_id}")
        return True

    def log_command(self, session_id: str, command: str, output: str = ""):
        """记录命令"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            command_log = {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "output": output
            }
            session["commands"].append(command_log)
            self.save_session(session)

    def list_environments(self) -> List[RangeEnvironment]:
        """列出所有环境"""
        return list(self.environments.values())

    def list_operations(self) -> List[Operation]:
        """列出所有操作"""
        return list(self.operations.values())

    def get_environment_status(self, env_id: str) -> Optional[EnvironmentStatus]:
        """获取环境状态"""
        if env_id in self.environments:
            return self.environments[env_id].status
        return None

    def save_environment(self, env: RangeEnvironment):
        """保存环境到数据库"""
        conn = sqlite3.connect("range_db/range.db")
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO environments
            (env_id, name, description, network_type, subnet, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            env.env_id, env.name, env.description, env.network_type.value,
            env.subnet, env.created_at.isoformat(), env.status.value
        ))

        # 保存靶机
        for machine in env.target_machines:
            self.save_machine(env.env_id, machine)

        conn.commit()
        conn.close()

    def save_machine(self, env_id: str, machine: TargetMachine):
        """保存靶机到数据库"""
        conn = sqlite3.connect("range_db/range.db")
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO machines
            (machine_id, env_id, name, image, ip_address, ports, status,
             operating_system, vulnerabilities, created_at, last_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            machine.machine_id, env_id, machine.name, machine.image,
            machine.ip_address, json.dumps(machine.ports), machine.status.value,
            machine.operating_system, json.dumps(machine.vulnerabilities),
            machine.created_at.isoformat(), machine.last_used.isoformat() if machine.last_used else None
        ))

        conn.commit()
        conn.close()

    def save_operation(self, operation: Operation):
        """保存操作到数据库"""
        conn = sqlite3.connect("range_db/range.db")
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO operations
            (op_id, name, description, target_env, start_time, end_time,
             status, participants, objectives)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            operation.op_id, operation.name, operation.description,
            operation.target_env, operation.start_time.isoformat(),
            operation.end_time.isoformat() if operation.end_time else None,
            operation.status, json.dumps(operation.participants),
            json.dumps(operation.objectives)
        ))

        conn.commit()
        conn.close()

    def save_session(self, session: Dict[str, Any]):
        """保存会话到数据库"""
        conn = sqlite3.connect("range_db/range.db")
        cursor = cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO sessions
            (session_id, op_id, machine_id, start_time, end_time, commands)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session["session_id"], session["op_id"], session["machine_id"],
            session["start_time"].isoformat(), session["end_time"].isoformat() if session["end_time"] else None,
            json.dumps(session["commands"])
        ))

        conn.commit()
        conn.close()

    def generate_range_report(self) -> Dict[str, Any]:
        """生成靶场报告"""
        total_environments = len(self.environments)
        running_environments = sum(1 for env in self.environments.values() if env.status == EnvironmentStatus.RUNNING)
        total_machines = sum(len(env.target_machines) for env in self.environments.values())
        running_machines = sum(sum(1 for machine in env.target_machines if machine.status == EnvironmentStatus.RUNNING) for env in self.environments.values())

        operation_stats = {
            "total_operations": len(self.operations),
            "active_operations": sum(1 for op in self.operations.values() if op.status == "active"),
            "completed_operations": sum(1 for op in self.operations.values() if op.status == "completed")
        }

        recent_activities = []
        for env_id, env in self.environments.items():
            for machine in env.target_machines:
                if machine.last_used and (datetime.now() - machine.last_used).days < 7:
                    recent_activities.append({
                        "machine": machine.name,
                        "environment": env.name,
                        "last_used": machine.last_used.isoformat(),
                        "status": machine.status.value
                    })

        report = {
            "summary": {
                "total_environments": total_environments,
                "running_environments": running_environments,
                "total_machines": total_machines,
                "running_machines": running_machines,
                "total_operations": operation_stats["total_operations"],
                "active_operations": operation_stats["active_operations"],
                "completed_operations": operation_stats["completed_operations"],
                "report_time": datetime.now().isoformat()
            },
            "environments": [
                {
                    "env_id": env.env_id,
                    "name": env.name,
                    "status": env.status.value,
                    "machine_count": len(env.target_machines),
                    "created_at": env.created_at.isoformat()
                }
                for env in self.environments.values()
            ],
            "recent_activities": recent_activities[-10:]  # 最近10个活动
        }

        return report

import secrets

# 示例使用
async def main():
    controller = RangeController()

    # 创建靶场环境
    env = controller.create_environment(
        name="越南电商测试环境",
        description="用于测试越南电商平台安全性的靶场环境",
        network_type=NetworkType.ISOLATED
    )

    # 启动环境
    controller.start_environment(env.env_id)

    # 创建操作
    operation = controller.create_operation(
        name="越南电商渗透测试",
        description="对越南电商平台进行安全渗透测试",
        target_env=env.env_id,
        participants=["红队测试员", "安全工程师"],
        objectives=["发现SQL注入漏洞", "测试WebShell上传", "评估权限提升风险"]
    )

    # 启动会话
    session_id = controller.start_session(operation.op_id, env.target_machines[0].machine_id)

    # 模拟一些命令
    controller.log_command(session_id, "nmap -sV 192.168.1.100")
    controller.log_command(session_id, "sqlmap -u 'http://192.168.1.100/login.php' --batch")
    controller.log_command(session_id, "upload shell.php /var/www/html/")

    # 结束会话
    controller.end_session(session_id)

    # 生成报告
    report = controller.generate_range_report()
    print("靶场报告:", json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())