#!/usr/bin/env python3
"""
Dragon-V RVOP 主平台编排器
专业红队作战平台 - 中央指挥中心
整合所有RVOP模块，提供统一的作战指挥能力
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os
import sys
import signal

# 导入RVOP核心模块
from c2_server import C2Server, AgentStatus, TaskStatus
from payload_generator import PayloadGenerator
from exploitation_framework import ExploitationFramework
from persistence_manager import PersistenceManager
from range_controller import RangeController

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('rvop_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlatformStatus(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class OperationMode(Enum):
    TRAINING = "training"
    ASSESSMENT = "assessment"
    SIMULATION = "simulation"
    LIVE = "live"

@dataclass
class RVOPConfig:
    platform_name: str = "Dragon-V RVOP"
    version: str = "1.0.0"
    operation_mode: OperationMode = OperationMode.SIMULATION
    c2_host: str = "0.0.0.0"
    c2_port: int = 8080
    c2_ssl_port: int = 8443
    enable_ssl: bool = True
    max_concurrent_agents: int = 50
    max_concurrent_tasks: int = 100
    database_path: str = "rvop.db"
    log_level: str = "INFO"
    payload_dir: str = "payloads"
    range_config_path: str = "range_config.yaml"
    persistence_db_path: str = "persistence.db"
    exploitation_config_path: str = "exploitation_config.json"

class RVOPPlatform:
    def __init__(self, config: RVOPConfig):
        self.config = config
        self.status = PlatformStatus.INITIALIZING
        self.start_time = None

        # 核心组件
        self.c2_server = None
        self.payload_generator = None
        self.exploitation_framework = None
        self.persistence_manager = None
        self.range_controller = None

        # 平台数据
        self.platform_stats = {
            "total_agents": 0,
            "active_agents": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "successful_exploits": 0,
            "total_persistence": 0,
            "active_operations": []
        }

        # 会话管理
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.operations: Dict[str, Dict[str, Any]] = {}

        # 事件监听器
        self.event_listeners = {
            "agent_connected": [],
            "agent_disconnected": [],
            "task_completed": [],
            "exploit_success": [],
            "exploit_failed": [],
            "data_exfiltrated": []
        }

        # 初始化信号处理
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到信号 {signum}，正在关闭平台...")
        self.shutdown()
        sys.exit(0)

    async def initialize(self):
        """初始化RVOP平台"""
        logger.info("=== Dragon-V RVOP 主平台初始化 ===")
        logger.info(f"平台名称: {self.config.platform_name}")
        logger.info(f"版本: {self.config.version}")
        logger.info(f"运行模式: {self.config.operation_mode.value}")

        try:
            # 创建必要的目录
            os.makedirs("logs", exist_ok=True)
            os.makedirs("certs", exist_ok=True)
            os.makedirs("payloads", exist_ok=True)
            os.makedirs("ranges", exist_ok=True)

            # 初始化核心组件
            logger.info("初始化C2服务器...")
            self.c2_server = C2Server()

            logger.info("初始化载荷生成器...")
            self.payload_generator = PayloadGenerator(self.config.payload_dir)

            logger.info("初始化自动化利用框架...")
            self.exploitation_framework = ExploitationFramework()

            logger.info("初始化持久化管理器...")
            self.persistence_manager = PersistenceManager(self.config.persistence_db_path)

            logger.info("初始化靶场控制器...")
            self.range_controller = RangeController(self.config.range_config_path)

            # 初始化C2服务器配置
            await self._configure_c2_server()

            # 启动平台监控
            self._start_platform_monitor()

            self.status = PlatformStatus.RUNNING
            self.start_time = datetime.now()

            logger.info("RVOP平台初始化完成")
            logger.info(f"C2服务器启动在 http://{self.config.c2_host}:{self.config.c2_port}")

        except Exception as e:
            logger.error(f"平台初始化失败: {e}")
            self.status = PlatformStatus.ERROR
            raise

    async def _configure_c2_server(self):
        """配置C2服务器"""
        # 设置C2服务器配置
        c2_config = {
            "host": self.config.c2_host,
            "port": self.config.c2_port,
            "ssl_port": self.config.c2_ssl_port,
            "enable_ssl": self.config.enable_ssl,
            "max_concurrent_agents": self.config.max_concurrent_agents,
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "operation_mode": self.config.operation_mode.value
        }

        # 保存配置
        with open("c2_config.json", "w", encoding="utf-8") as f:
            json.dump(c2_config, f, indent=2, ensure_ascii=False)

    def _start_platform_monitor(self):
        """启动平台监控"""
        def monitor():
            while self.status == PlatformStatus.RUNNING:
                try:
                    # 更新平台统计
                    self._update_platform_stats()

                    # 检查组件状态
                    self._check_component_status()

                    # 生成健康报告
                    self._generate_health_report()

                    time.sleep(30)  # 30秒监控间隔

                except Exception as e:
                    logger.error(f"监控错误: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("平台监控已启动")

    def _update_platform_stats(self):
        """更新平台统计信息"""
        if self.c2_server and hasattr(self.c2_server, 'agents'):
            self.platform_stats["total_agents"] = len(self.c2_server.agents)
            self.platform_stats["active_agents"] = len([
                agent for agent in self.c2_server.agents.values()
                if agent.status == AgentStatus.ONLINE
            ])

        if self.c2_server and hasattr(self.c2_server, 'completed_tasks'):
            self.platform_stats["total_tasks"] = len(self.c2_server.tasks) + len(self.c2_server.completed_tasks)
            self.platform_stats["completed_tasks"] = len(self.c2_server.completed_tasks)

    def _check_component_status(self):
        """检查组件状态"""
        components = [
            ("C2服务器", self.c2_server),
            ("载荷生成器", self.payload_generator),
            ("利用框架", self.exploitation_framework),
            ("持久化管理器", self.persistence_manager),
            ("靶场控制器", self.range_controller)
        ]

        for name, component in components:
            if component is None:
                logger.warning(f"{name} 未初始化")
            elif hasattr(component, 'status'):
                logger.debug(f"{name} 状态: {component.status}")

    def _generate_health_report(self):
        """生成健康报告"""
        if self.start_time:
            uptime = datetime.now() - self.start_time
            uptime_str = str(uptime).split('.')[0]  # 去掉微秒

            health_data = {
                "platform_status": self.status.value,
                "uptime": uptime_str,
                "stats": self.platform_stats.copy(),
                "timestamp": datetime.now().isoformat()
            }

            # 保存健康报告
            with open("logs/health_report.json", "w", encoding="utf-8") as f:
                json.dump(health_data, f, indent=2, ensure_ascii=False)

    def start(self):
        """启动RVOP平台"""
        try:
            # 异步初始化
            asyncio.run(self.initialize())

            # 启动C2服务器
            if self.c2_server:
                logger.info("启动C2服务器...")
                asyncio.run(self.c2_server.start())

        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭平台...")
            self.shutdown()
        except Exception as e:
            logger.error(f"平台启动失败: {e}")
            self.status = PlatformStatus.ERROR
            raise

    def shutdown(self):
        """关闭RVOP平台"""
        logger.info("正在关闭RVOP平台...")
        self.status = PlatformStatus.STOPPING

        # 关闭所有组件
        if self.c2_server:
            # 这里需要正确的异步关闭逻辑
            pass

        if self.payload_generator:
            self.payload_generator.cleanup()

        if self.persistence_manager:
            self.persistence_manager.cleanup()

        if self.range_controller:
            self.range_controller.cleanup()

        # 生成关闭报告
        self._generate_shutdown_report()

        logger.info("RVOP平台已关闭")

    def _generate_shutdown_report(self):
        """生成关闭报告"""
        shutdown_report = {
            "platform_name": self.config.platform_name,
            "version": self.config.version,
            "shutdown_time": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.start_time).split('.')[0] if self.start_time else "N/A",
            "final_stats": self.platform_stats,
            "operations_completed": len(self.operations)
        }

        with open("logs/shutdown_report.json", "w", encoding="utf-8") as f:
            json.dump(shutdown_report, f, indent=2, ensure_ascii=False)

    # 平台操作接口
    def create_operation(self, name: str, description: str, targets: List[str],
                        operation_type: str = "exploitation") -> str:
        """创建新操作"""
        operation_id = f"op_{int(time.time())}"

        operation = {
            "id": operation_id,
            "name": name,
            "description": description,
            "targets": targets,
            "type": operation_type,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "tasks": [],
            "results": {}
        }

        self.operations[operation_id] = operation
        logger.info(f"创建操作: {name} (ID: {operation_id})")

        return operation_id

    def update_operation_status(self, operation_id: str, status: str):
        """更新操作状态"""
        if operation_id in self.operations:
            self.operations[operation_id]["status"] = status
            if status == "running":
                self.operations[operation_id]["started_at"] = datetime.now().isoformat()
            elif status == "completed":
                self.operations[operation_id]["completed_at"] = datetime.now().isoformat()

            logger.info(f"操作 {operation_id} 状态更新为: {status}")

    def get_platform_status(self) -> Dict[str, Any]:
        """获取平台状态"""
        return {
            "status": self.status.value,
            "uptime": str(datetime.now() - self.start_time).split('.')[0] if self.start_time else "N/A",
            "stats": self.platform_stats,
            "operations": len(self.operations),
            "config": {
                "platform_name": self.config.platform_name,
                "version": self.config.version,
                "operation_mode": self.config.operation_mode.value
            }
        }

    def get_operations_list(self) -> List[Dict[str, Any]]:
        """获取操作列表"""
        return [
            {
                "id": op_id,
                "name": op["name"],
                "description": op["description"],
                "status": op["status"],
                "created_at": op["created_at"],
                "targets": op["targets"]
            }
            for op_id, op in self.operations.items()
        ]

    # 事件通知
    def add_event_listener(self, event_type: str, callback):
        """添加事件监听器"""
        if event_type in self.event_listeners:
            self.event_listeners[event_type].append(callback)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"事件监听器错误: {e}")

    def export_platform_config(self, output_path: str):
        """导出平台配置"""
        config_data = {
            "platform": {
                "name": self.config.platform_name,
                "version": self.config.version,
                "operation_mode": self.config.operation_mode.value,
                "status": self.status.value
            },
            "components": {
                "c2": {
                    "host": self.config.c2_host,
                    "port": self.config.c2_port,
                    "ssl_port": self.config.c2_ssl_port,
                    "enable_ssl": self.config.enable_ssl
                },
                "payload_generator": {
                    "output_dir": self.config.payload_dir
                },
                "exploitation": {
                    "max_concurrent": self.config.max_concurrent_tasks
                },
                "persistence": {
                    "database_path": self.config.persistence_db_path
                },
                "range_controller": {
                    "config_path": self.config.range_config_path
                }
            },
            "stats": self.platform_stats,
            "operations": self.operations
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"平台配置已导出到: {output_path}")

def main():
    """主函数"""
    print("=== Dragon-V RVOP 主平台 ===")
    print("专业红队作战平台 - 中央指挥中心")
    print("正在初始化平台...")

    # 创建配置
    config = RVOPConfig(
        platform_name="Dragon-V RVOP",
        version="1.0.0",
        operation_mode=OperationMode.SIMULATION,
        c2_host="0.0.0.0",
        c2_port=8080,
        enable_ssl=False,  # 简化测试
        max_concurrent_agents=10,
        max_concurrent_tasks=20
    )

    # 创建平台实例
    platform = RVOPPlatform(config)

    try:
        # 启动平台
        platform.start()
    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭平台...")
        platform.shutdown()
    except Exception as e:
        print(f"平台启动失败: {e}")
        platform.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    main()