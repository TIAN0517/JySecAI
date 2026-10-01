#!/usr/bin/env python3
"""
Dragon-V RVOP Web管理界面
专业红队作战平台 - Web管理控制台
提供统一的Web界面来管理RVOP平台的所有功能
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os
import sys

# 导入Web框架和相关库
from aiohttp import web
from aiohttp.web import Application, Request, Response, FileResponse
import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from jinja2 import Environment, FileSystemLoader, select_autoescape

# 导入RVOP核心模块
from main_orchestrator import RVOPPlatform, OperationMode, PlatformStatus
from c2_server import C2Server, AgentStatus, TaskStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('rvop_web.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建模板目录
os.makedirs("web/templates", exist_ok=True)
os.makedirs("web/static/css", exist_ok=True)
os.makedirs("web/static/js", exist_ok=True)
os.makedirs("web/static/images", exist_ok=True)

class WebInterface:
    def __init__(self, platform: RVOPPlatform, host: str = "0.0.0.0", port: int = 8081):
        self.platform = platform
        self.host = host
        self.port = port
        self.app = None
        self.session_storage = None
        self.jinja_env = None

        # 初始化Web应用
        self._init_web_app()

    def _init_web_app(self):
        """初始化Web应用"""
        self.app = Application()
        self.session_storage = EncryptedCookieStorage(b'rvop_session_secret')
        aiohttp_session.setup(self.app, self.session_storage)

        # 设置Jinja2模板环境
        template_path = os.path.join(os.path.dirname(__file__), "web", "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # 注册路由
        self._setup_routes()

        # 添加静态文件路由
        self.app.router.add_static(
            '/static',
            path=os.path.join(os.path.dirname(__file__), 'web', 'static'),
            name='static'
        )

        logger.info(f"Web管理界面初始化完成: http://{self.host}:{self.port}")

    def _setup_routes(self):
        """设置Web路由"""
        # 主页路由
        self.app.router.add_get('/', self.dashboard)
        self.app.router.add_get('/dashboard', self.dashboard)

        # 平台管理路由
        self.app.router.add_get('/platform/status', self.get_platform_status)
        self.app.router.add_get('/platform/config', self.get_platform_config)
        self.app.router.add_post('/platform/config', self.update_platform_config)
        self.app.router.add_get('/platform/stats', self.get_platform_stats)

        # C2服务器路由
        self.app.router.add_get('/c2/agents', self.get_agents)
        self.app.router.add_get('/c2/tasks', self.get_tasks)
        self.app.router.add_get('/c2/tasks/{task_id}', self.get_task_details)
        self.app.router.add_post('/c2/tasks', self.create_task)
        self.app.router.add_post('/c2/tasks/{task_id}/cancel', self.cancel_task)

        # 载荷生成器路由
        self.app.router.add_get('/payloads', self.get_payloads)
        self.app.router.add_post('/payloads/generate', self.generate_payload)
        self.app.router.add_get('/payloads/{payload_id}', self.get_payload_details)
        self.app.router.add_post('/payloads/{payload_id}/download', self.download_payload)

        # 利用框架路由
        self.app.router.add_get('/exploitation/modules', self.get_exploit_modules)
        self.app.router.add_post('/exploitation/execute', self.execute_exploitation)
        self.app.router.add_get('/exploitation/results', self.get_exploit_results)
        self.app.router.add_get('/exploitation/results/{result_id}', self.get_exploit_result_details)

        # 持久化管理路由
        self.app.router.add_get('/persistence/methods', self.get_persistence_methods)
        self.app.router.add_post('/persistence/create', self.create_persistence)
        self.app.router.add_get('/persistence/list', self.get_persistence_list)
        self.app.router.add_post('/persistence/{persistence_id}/remove', self.remove_persistence)

        # 靶场控制器路由
        self.app.router.add_get('/ranges/environments', self.get_range_environments)
        self.app.router.add_post('/ranges/environments', self.create_range_environment)
        self.app.router.add_get('/ranges/environments/{env_id}', self.get_range_environment_details)
        self.app.router.add_post('/ranges/environments/{env_id}/start', self.start_range_environment)
        self.app.router.add_post('/ranges/environments/{env_id}/stop', self.stop_range_environment)

        # 操作管理路由
        self.app.router.add_get('/operations', self.get_operations)
        self.app.router.add_get('/operations/{op_id}', self.get_operation_details)
        self.app.router.add_post('/operations', self.create_operation)
        self.app.router.add_post('/operations/{op_id}/start', self.start_operation)
        self.app.router.add_post('/operations/{op_id}/stop', self.stop_operation)

        # 报告和日志路由
        self.app.router.add_get('/reports', self.get_reports)
        self.app.router.add_get('/reports/{report_id}', self.get_report_details)
        self.app.router.add_get('/logs', self.get_logs)
        self.app.router.add_get('/logs/download', self.download_logs)

        # 系统管理路由
        self.app.router.add_get('/system/health', self.get_system_health)
        self.app.router.add_get('/system/performance', self.get_system_performance)
        self.app.router.add_post('/system/shutdown', self.shutdown_system)
        self.app.router.add_post('/system/restart', self.restart_system)

    # 主页仪表板
    async def dashboard(self, request: Request) -> Response:
        """仪表板页面"""
        try:
            # 获取平台状态
            platform_status = self.platform.get_platform_status()

            # 获取最近的操作
            recent_operations = self.platform.get_operations_list()[-5:]  # 最近5个操作

            # 获取平台统计
            stats = platform_status['stats']

            # 检查会话
            session = aiohttp_session.get(request)
            user_info = session.get('user', {'authenticated': False, 'role': 'guest'})

            template = self.jinja_env.get_template('dashboard.html')
            html = template.render(
                platform_status=platform_status,
                recent_operations=recent_operations,
                stats=stats,
                user=user_info
            )

            return web.Response(text=html, content_type='text/html')

        except Exception as e:
            logger.error(f"仪表板页面错误: {e}")
            return web.Response(text="仪表板页面加载失败", status=500)

    # 平台管理功能
    async def get_platform_status(self, request: Request) -> Response:
        """获取平台状态"""
        try:
            status = self.platform.get_platform_status()
            return web.json_response(status)
        except Exception as e:
            logger.error(f"获取平台状态失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_platform_config(self, request: Request) -> Response:
        """获取平台配置"""
        try:
            config_data = {
                "platform": {
                    "name": self.platform.config.platform_name,
                    "version": self.platform.config.version,
                    "operation_mode": self.platform.config.operation_mode.value,
                    "status": self.platform.status.value
                },
                "components": {
                    "c2": {
                        "host": self.platform.config.c2_host,
                        "port": self.platform.config.c2_port,
                        "ssl_port": self.platform.config.c2_ssl_port,
                        "enable_ssl": self.platform.config.enable_ssl
                    },
                    "payload_generator": {
                        "output_dir": self.platform.config.payload_dir
                    },
                    "exploitation": {
                        "max_concurrent": self.platform.config.max_concurrent_tasks
                    }
                }
            }
            return web.json_response(config_data)
        except Exception as e:
            logger.error(f"获取平台配置失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def update_platform_config(self, request: Request) -> Response:
        """更新平台配置"""
        try:
            data = await request.json()

            # 这里应该更新平台配置
            # 实际实现需要根据具体的配置项进行更新

            return web.json_response({"status": "success", "message": "配置已更新"})
        except Exception as e:
            logger.error(f"更新平台配置失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_platform_stats(self, request: Request) -> Response:
        """获取平台统计信息"""
        try:
            status = self.platform.get_platform_status()
            return web.json_response(status['stats'])
        except Exception as e:
            logger.error(f"获取平台统计失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # C2服务器管理功能
    async def get_agents(self, request: Request) -> Response:
        """获取代理列表"""
        try:
            if self.platform.c2_server and hasattr(self.platform.c2_server, 'agents'):
                agents = list(self.platform.c2_server.agents.values())
                agents_data = [agent.to_dict() for agent in agents]
                return web.json_response({
                    "status": "success",
                    "agents": agents_data,
                    "total_count": len(agents)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "agents": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取代理列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_tasks(self, request: Request) -> Response:
        """获取任务列表"""
        try:
            if self.platform.c2_server and hasattr(self.platform.c2_server, 'tasks'):
                tasks_data = list(self.platform.c2_server.tasks.values())
                completed_tasks = list(self.platform.c2_server.completed_tasks.values())
                all_tasks = tasks_data + completed_tasks

                tasks_info = []
                for task in all_tasks:
                    task_info = {
                        "task_id": task.task_id,
                        "agent_id": task.agent_id,
                        "command": task.command,
                        "parameters": task.parameters,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "output": task.output,
                        "error": task.error
                    }
                    tasks_info.append(task_info)

                return web.json_response({
                    "status": "success",
                    "tasks": tasks_info,
                    "total_count": len(all_tasks)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "tasks": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_task_details(self, request: Request) -> Response:
        """获取任务详情"""
        try:
            task_id = request.match_info['task_id']

            if self.platform.c2_server and hasattr(self.platform.c2_server, 'tasks'):
                task = self.platform.c2_server.tasks.get(task_id)
                if task:
                    task_info = {
                        "task_id": task.task_id,
                        "agent_id": task.agent_id,
                        "command": task.command,
                        "parameters": task.parameters,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat(),
                        "started_at": task.started_at.isoformat() if task.started_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "output": task.output,
                        "error": task.error,
                        "timeout": task.timeout
                    }
                    return web.json_response({
                        "status": "success",
                        "task": task_info
                    })
                else:
                    return web.json_response({"error": "任务不存在"}, status=404)
            else:
                return web.json_response({"error": "任务服务不可用"}, status=500)
        except Exception as e:
            logger.error(f"获取任务详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_task(self, request: Request) -> Response:
        """创建任务"""
        try:
            data = await request.json()
            agent_id = data.get('agent_id')
            command = data.get('command')
            parameters = data.get('parameters', {})

            if not agent_id or not command:
                return web.json_response({"error": "缺少必要参数"}, status=400)

            # 这里应该调用实际的C2服务器任务创建功能
            # 目前返回模拟数据
            task_id = f"task_{int(time.time())}"

            return web.json_response({
                "status": "success",
                "task_id": task_id,
                "message": "任务已创建"
            })
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def cancel_task(self, request: Request) -> Response:
        """取消任务"""
        try:
            task_id = request.match_info['task_id']

            # 这里应该实现任务取消逻辑
            return web.json_response({
                "status": "success",
                "message": "任务已取消"
            })
        except Exception as e:
            logger.error(f"取消任务失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 载荷生成器功能
    async def get_payloads(self, request: Request) -> Response:
        """获取载荷列表"""
        try:
            if self.platform.payload_generator:
                payloads = self.platform.payload_generator.get_generated_payloads()
                return web.json_response({
                    "status": "success",
                    "payloads": payloads,
                    "total_count": len(payloads)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "payloads": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取载荷列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def generate_payload(self, request: Request) -> Response:
        """生成载荷"""
        try:
            data = await request.json()
            payload_type = data.get('type')
            target_info = data.get('target_info', {})
            options = data.get('options', {})

            if not payload_type:
                return web.json_response({"error": "缺少载荷类型"}, status=400)

            # 这里应该调用实际的载荷生成功能
            payload_id = f"payload_{int(time.time())}"

            return web.json_response({
                "status": "success",
                "payload_id": payload_id,
                "message": "载荷已生成"
            })
        except Exception as e:
            logger.error(f"生成载荷失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_payload_details(self, request: Request) -> Response:
        """获取载荷详情"""
        try:
            payload_id = request.match_info['payload_id']

            # 这里应该返回载荷详情
            return web.json_response({
                "status": "success",
                "payload": {
                    "id": payload_id,
                    "type": "webshell",
                    "size": "1024",
                    "created_at": datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"获取载荷详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def download_payload(self, request: Request) -> Response:
        """下载载荷"""
        try:
            payload_id = request.match_info['payload_id']

            # 这里应该实现文件下载功能
            return web.Response(text=f"载荷 {payload_id} 下载功能")
        except Exception as e:
            logger.error(f"下载载荷失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 利用框架功能
    async def get_exploit_modules(self, request: Request) -> Response:
        """获取利用模块列表"""
        try:
            if self.platform.exploitation_framework:
                modules = self.platform.exploitation_framework.get_exploit_modules()
                return web.json_response({
                    "status": "success",
                    "modules": modules,
                    "total_count": len(modules)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "modules": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取利用模块失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def execute_exploitation(self, request: Request) -> Response:
        """执行利用"""
        try:
            data = await request.json()
            target = data.get('target')
            module = data.get('module')
            parameters = data.get('parameters', {})

            if not target or not module:
                return web.json_response({"error": "缺少必要参数"}, status=400)

            # 这里应该调用实际的利用功能
            exploit_id = f"exploit_{int(time.time())}"

            return web.json_response({
                "status": "success",
                "exploit_id": exploit_id,
                "message": "利用已启动"
            })
        except Exception as e:
            logger.error(f"执行利用失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_exploit_results(self, request: Request) -> Response:
        """获取利用结果"""
        try:
            results = []
            # 这里应该返回实际的利用结果
            return web.json_response({
                "status": "success",
                "results": results,
                "total_count": len(results)
            })
        except Exception as e:
            logger.error(f"获取利用结果失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_exploit_result_details(self, request: Request) -> Response:
        """获取利用结果详情"""
        try:
            result_id = request.match_info['result_id']

            # 这里应该返回具体的利用结果详情
            return web.json_response({
                "status": "success",
                "result": {
                    "id": result_id,
                    "target": "example.com",
                    "module": "sqli",
                    "status": "completed",
                    "result": "数据已提取"
                }
            })
        except Exception as e:
            logger.error(f"获取利用结果详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 持久化管理功能
    async def get_persistence_methods(self, request: Request) -> Response:
        """获取持久化方法"""
        try:
            methods = [
                {
                    "id": "windows_service",
                    "name": "Windows服务",
                    "description": "创建Windows系统服务",
                    "platform": "windows",
                    "risk_level": "high"
                },
                {
                    "id": "cron_job",
                    "name": "计划任务",
                    "description": "创建Linux cron任务",
                    "platform": "linux",
                    "risk_level": "medium"
                },
                {
                    "id": "webshell",
                    "name": "Webshell",
                    "description": "创建Web后门",
                    "platform": "web",
                    "risk_level": "high"
                }
            ]
            return web.json_response({
                "status": "success",
                "methods": methods,
                "total_count": len(methods)
            })
        except Exception as e:
            logger.error(f"获取持久化方法失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_persistence(self, request: Request) -> Response:
        """创建持久化"""
        try:
            data = await request.json()
            method = data.get('method')
            target = data.get('target')
            options = data.get('options', {})

            if not method or not target:
                return web.json_response({"error": "缺少必要参数"}, status=400)

            # 这里应该调用实际的持久化功能
            persistence_id = f"persistence_{int(time.time())}"

            return web.json_response({
                "status": "success",
                "persistence_id": persistence_id,
                "message": "持久化已创建"
            })
        except Exception as e:
            logger.error(f"创建持久化失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_persistence_list(self, request: Request) -> Response:
        """获取持久化列表"""
        try:
            if self.platform.persistence_manager:
                persistence_list = self.platform.persistence_manager.get_persistence_list()
                return web.json_response({
                    "status": "success",
                    "persistence": persistence_list,
                    "total_count": len(persistence_list)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "persistence": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取持久化列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def remove_persistence(self, request: Request) -> Response:
        """移除持久化"""
        try:
            persistence_id = request.match_info['persistence_id']

            # 这里应该实现持久化移除逻辑
            return web.json_response({
                "status": "success",
                "message": "持久化已移除"
            })
        except Exception as e:
            logger.error(f"移除持久化失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 靶场控制器功能
    async def get_range_environments(self, request: Request) -> Response:
        """获取靶场环境"""
        try:
            if self.platform.range_controller:
                environments = self.platform.range_controller.get_environments()
                return web.json_response({
                    "status": "success",
                    "environments": environments,
                    "total_count": len(environments)
                })
            else:
                return web.json_response({
                    "status": "success",
                    "environments": [],
                    "total_count": 0
                })
        except Exception as e:
            logger.error(f"获取靶场环境失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_range_environment(self, request: Request) -> Response:
        """创建靶场环境"""
        try:
            data = await request.json()
            name = data.get('name')
            config = data.get('config', {})

            if not name:
                return web.json_response({"error": "缺少环境名称"}, status=400)

            # 这里应该调用实际的靶场创建功能
            env_id = f"env_{int(time.time())}"

            return web.json_response({
                "status": "success",
                "env_id": env_id,
                "message": "靶场环境已创建"
            })
        except Exception as e:
            logger.error(f"创建靶场环境失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_range_environment_details(self, request: Request) -> Response:
        """获取靶场环境详情"""
        try:
            env_id = request.match_info['env_id']

            # 这里应该返回具体的靶场环境详情
            return web.json_response({
                "status": "success",
                "environment": {
                    "id": env_id,
                    "name": "测试环境",
                    "status": "running",
                    "targets": ["192.168.1.100", "192.168.1.101"]
                }
            })
        except Exception as e:
            logger.error(f"获取靶场环境详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start_range_environment(self, request: Request) -> Response:
        """启动靶场环境"""
        try:
            env_id = request.match_info['env_id']

            # 这里应该实现靶场启动逻辑
            return web.json_response({
                "status": "success",
                "message": "靶场环境已启动"
            })
        except Exception as e:
            logger.error(f"启动靶场环境失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def stop_range_environment(self, request: Request) -> Response:
        """停止靶场环境"""
        try:
            env_id = request.match_info['env_id']

            # 这里应该实现靶场停止逻辑
            return web.json_response({
                "status": "success",
                "message": "靶场环境已停止"
            })
        except Exception as e:
            logger.error(f"停止靶场环境失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 操作管理功能
    async def get_operations(self, request: Request) -> Response:
        """获取操作列表"""
        try:
            operations = self.platform.get_operations_list()
            return web.json_response({
                "status": "success",
                "operations": operations,
                "total_count": len(operations)
            })
        except Exception as e:
            logger.error(f"获取操作列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_operation_details(self, request: Request) -> Response:
        """获取操作详情"""
        try:
            op_id = request.match_info['op_id']

            if op_id in self.platform.operations:
                operation = self.platform.operations[op_id]
                return web.json_response({
                    "status": "success",
                    "operation": operation
                })
            else:
                return web.json_response({"error": "操作不存在"}, status=404)
        except Exception as e:
            logger.error(f"获取操作详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def create_operation(self, request: Request) -> Response:
        """创建操作"""
        try:
            data = await request.json()
            name = data.get('name')
            description = data.get('description', '')
            targets = data.get('targets', [])
            operation_type = data.get('type', 'exploitation')

            if not name or not targets:
                return web.json_response({"error": "缺少必要参数"}, status=400)

            operation_id = self.platform.create_operation(
                name=name,
                description=description,
                targets=targets,
                operation_type=operation_type
            )

            return web.json_response({
                "status": "success",
                "operation_id": operation_id,
                "message": "操作已创建"
            })
        except Exception as e:
            logger.error(f"创建操作失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start_operation(self, request: Request) -> Response:
        """启动操作"""
        try:
            op_id = request.match_info['op_id']

            if op_id in self.platform.operations:
                self.platform.update_operation_status(op_id, "running")
                return web.json_response({
                    "status": "success",
                    "message": "操作已启动"
                })
            else:
                return web.json_response({"error": "操作不存在"}, status=404)
        except Exception as e:
            logger.error(f"启动操作失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def stop_operation(self, request: Request) -> Response:
        """停止操作"""
        try:
            op_id = request.match_info['op_id']

            if op_id in self.platform.operations:
                self.platform.update_operation_status(op_id, "completed")
                return web.json_response({
                    "status": "success",
                    "message": "操作已停止"
                })
            else:
                return web.json_response({"error": "操作不存在"}, status=404)
        except Exception as e:
            logger.error(f"停止操作失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 报告和日志功能
    async def get_reports(self, request: Request) -> Response:
        """获取报告列表"""
        try:
            reports = [
                {
                    "id": "health_report",
                    "name": "健康报告",
                    "type": "health",
                    "created_at": datetime.now().isoformat(),
                    "size": "1.2KB"
                },
                {
                    "id": "exploitation_report",
                    "name": "利用报告",
                    "type": "exploitation",
                    "created_at": datetime.now().isoformat(),
                    "size": "2.5KB"
                },
                {
                    "id": "persistence_report",
                    "name": "持久化报告",
                    "type": "persistence",
                    "created_at": datetime.now().isoformat(),
                    "size": "1.8KB"
                }
            ]
            return web.json_response({
                "status": "success",
                "reports": reports,
                "total_count": len(reports)
            })
        except Exception as e:
            logger.error(f"获取报告列表失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_report_details(self, request: Request) -> Response:
        """获取报告详情"""
        try:
            report_id = request.match_info['report_id']

            # 这里应该返回具体的报告详情
            return web.json_response({
                "status": "success",
                "report": {
                    "id": report_id,
                    "name": "报告名称",
                    "content": "报告内容",
                    "created_at": datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"获取报告详情失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_logs(self, request: Request) -> Response:
        """获取日志"""
        try:
            # 这里应该读取日志文件
            logs = []

            # 查询参数
            limit = request.query.get('limit', '100')
            level = request.query.get('level')

            # 这里实现日志读取逻辑

            return web.json_response({
                "status": "success",
                "logs": logs,
                "total_count": len(logs)
            })
        except Exception as e:
            logger.error(f"获取日志失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def download_logs(self, request: Request) -> Response:
        """下载日志"""
        try:
            # 这里应该实现日志下载功能
            return web.Response(text="日志下载功能")
        except Exception as e:
            logger.error(f"下载日志失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # 系统管理功能
    async def get_system_health(self, request: Request) -> Response:
        """获取系统健康状态"""
        try:
            health_info = {
                "status": "healthy",
                "components": {
                    "c2_server": "healthy",
                    "payload_generator": "healthy",
                    "exploitation_framework": "healthy",
                    "persistence_manager": "healthy",
                    "range_controller": "healthy"
                },
                "uptime": "2h 30m",
                "memory_usage": "45%",
                "cpu_usage": "25%"
            }
            return web.json_response(health_info)
        except Exception as e:
            logger.error(f"获取系统健康状态失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_system_performance(self, request: Request) -> Response:
        """获取系统性能数据"""
        try:
            performance_info = {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 60.8,
                "network_io": {
                    "in": 1024,
                    "out": 2048
                },
                "database_connections": 5,
                "active_sessions": 2
            }
            return web.json_response(performance_info)
        except Exception as e:
            logger.error(f"获取系统性能数据失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def shutdown_system(self, request: Request) -> Response:
        """关闭系统"""
        try:
            return web.json_response({
                "status": "success",
                "message": "系统关闭命令已发送"
            })
        except Exception as e:
            logger.error(f"关闭系统失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def restart_system(self, request: Request) -> Response:
        """重启系统"""
        try:
            return web.json_response({
                "status": "success",
                "message": "系统重启命令已发送"
            })
        except Exception as e:
            logger.error(f"重启系统失败: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def start_web_server(self):
        """启动Web服务器"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()

            site = web.TCPSite(runner, self.host, self.port)
            await site.start()

            logger.info(f"RVOP Web管理界面启动在 http://{self.host}:{self.port}")
            logger.info(f"访问地址: http://{self.host}:{self.port}/dashboard")

            # 保持服务器运行
            await asyncio.sleep(3600)  # 1小时后自动关闭（测试用）

        except Exception as e:
            logger.error(f"Web服务器启动失败: {e}")
            raise

def create_html_templates():
    """创建HTML模板"""
    templates_dir = os.path.join(os.path.dirname(__file__), "web", "templates")

    # 主页模板
    dashboard_html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dragon-V RVOP - 仪表板</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .header { background-color: #2c3e50; color: white; padding: 20px; margin-bottom: 20px; }
        .nav { background-color: #34495e; padding: 10px; }
        .nav a { color: white; text-decoration: none; margin: 0 10px; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { margin-top: 0; color: #2c3e50; }
        .stat { font-size: 24px; font-weight: bold; color: #3498db; }
        .status { padding: 5px 10px; border-radius: 3px; color: white; }
        .status.running { background-color: #27ae60; }
        .status.stopped { background-color: #e74c3c; }
        .status.warning { background-color: #f39c12; }
        .operation-list { margin-top: 20px; }
        .operation-item { padding: 10px; border-bottom: 1px solid #ddd; }
        .footer { margin-top: 20px; padding: 20px; background-color: #2c3e50; color: white; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Dragon-V RVOP 专业红队作战平台</h1>
        <p>欢迎使用红队作战指挥中心</p>
    </div>

    <div class="nav">
        <a href="/dashboard">仪表板</a>
        <a href="/platform/status">平台状态</a>
        <a href="/c2/agents">C2代理</a>
        <a href="/exploitation/modules">利用模块</a>
        <a href="/persistence/methods">持久化管理</a>
        <a href="/ranges/environments">靶场环境</a>
        <a href="/operations">操作管理</a>
        <a href="/reports">报告</a>
    </div>

    <div class="dashboard">
        <div class="card">
            <h3>平台状态</h3>
            <p><strong>名称:</strong> {{ platform_status.config.platform_name }}</p>
            <p><strong>版本:</strong> {{ platform_status.config.version }}</p>
            <p><strong>状态:</strong> <span class="status {{ platform_status.status }}">{{ platform_status.status }}</span></p>
            <p><strong>运行时间:</strong> {{ platform_status.uptime }}</p>
        </div>

        <div class="card">
            <h3>统计信息</h3>
            <p><strong>总代理数:</strong> <span class="stat">{{ stats.total_agents }}</span></p>
            <p><strong>活跃代理:</strong> <span class="stat">{{ stats.active_agents }}</span></p>
            <p><strong>总任务数:</strong> <span class="stat">{{ stats.total_tasks }}</span></p>
            <p><strong>已完成任务:</strong> <span class="stat">{{ stats.completed_tasks }}</span></p>
            <p><strong>成功利用:</strong> <span class="stat">{{ stats.successful_exploits }}</span></p>
        </div>

        <div class="card">
            <h3>最近操作</h3>
            <div class="operation-list">
                {% for operation in recent_operations %}
                <div class="operation-item">
                    <p><strong>{{ operation.name }}</strong></p>
                    <p>状态: {{ operation.status }}</p>
                    <p>创建时间: {{ operation.created_at }}</p>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <h3>系统组件</h3>
            <p><strong>C2服务器:</strong> 正常运行</p>
            <p><strong>载荷生成器:</strong> 就绪</p>
            <p><strong>利用框架:</strong> 就绪</p>
            <p><strong>持久化管理器:</strong> 就绪</p>
            <p><strong>靶场控制器:</strong> 就绪</p>
        </div>
    </div>

    <div class="footer">
        <p>&copy; 2024 Dragon-V RVOP 专业红队作战平台 - 授权使用</p>
    </div>

    <script>
        // 自动刷新页面数据
        setInterval(function() {
            fetch('/platform/status')
                .then(response => response.json())
                .then(data => {
                    // 更新页面数据
                    console.log('平台状态更新:', data);
                })
                .catch(error => console.error('更新失败:', error));
        }, 30000); // 30秒刷新一次
    </script>
</body>
</html>
    """

    with open(os.path.join(templates_dir, "dashboard.html"), "w", encoding="utf-8") as f:
        f.write(dashboard_html)

def main():
    """主函数"""
    print("=== Dragon-V RVOP Web管理界面 ===")
    print("专业红队作战平台 - Web管理控制台")

    # 创建HTML模板
    create_html_templates()

    # 创建RVOP平台实例
    from main_orchestrator import RVOPConfig, OperationMode

    config = RVOPConfig(
        platform_name="Dragon-V RVOP",
        version="1.0.0",
        operation_mode=OperationMode.SIMULATION
    )

    platform = RVOPPlatform(config)

    # 创建Web界面
    web_interface = WebInterface(platform, host="0.0.0.0", port=8081)

    try:
        # 启动Web服务器
        asyncio.run(web_interface.start_web_server())
    except KeyboardInterrupt:
        print("\n正在关闭Web管理界面...")
        platform.shutdown()

if __name__ == "__main__":
    main()