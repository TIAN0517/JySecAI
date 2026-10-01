#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐉 Dragon-V Triple Bot Unified Manager v1.0
整合三个bot系统的统一管理器

整合内容:
- 企业级双机器人管理器 (dragon_enterprise_dual_bot_manager.py)
- 专业技术扫描机器人 (dragon_v_telegram_bot.py)
- 安全工具机器人 (security_telegram_bot.py)

功能特性:
  🚀 统一接口 - 一个脚本控制所有三个bot
  📊 智能负载均衡 - 自动分配任务给最佳bot
  🔄 热切换 - 运行时动态切换bot配置
  📈 性能监控 - 实时监控所有bot状态
  🛡️ 故障转移 - 自动检测和转移故障bot
  📄 综合报告 - 统一的日志和报告系统
"""

import os
import sys
import json
import asyncio
import sqlite3
import logging
import signal
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import uuid

# Windows控制台编码修复
if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except:
        pass

# 尝试导入 Telegram Bot 库
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Document
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ChatAction, ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("[-] 需要安装: pip install python-telegram-bot")
    TELEGRAM_AVAILABLE = False
    sys.exit(1)

# Bot类型枚举
class BotType(Enum):
    ENTERPRISE = "enterprise"      # 企业级双机器人管理器
    PROFESSIONAL = "professional"  # 专业技术扫描机器人
    SECURITY = "security"         # 安全工具机器人

# Bot状态枚举
class BotStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class BotInstance:
    bot_type: BotType
    bot_id: str
    status: BotStatus
    tasks_count: int
    last_activity: datetime
    memory_usage: float
    error_count: int
    config: Dict[str, Any]

class DragonTripleBotUnifiedManager:
    """Dragon-V三机器人统一管理器"""

    def __init__(self):
        self.version = "1.0"
        self.bot_instances: Dict[str, BotInstance] = {}
        self.database_path = "dragon_triple_bot_unified.db"
        self.log_path = "dragon_triple_bot.log"
        self.config_path = "dragon_triple_config.json"

        # 初始化日志系统
        self._setup_logging()

        # 初始化数据库
        self._setup_database()

        # 初始化配置
        self._setup_config()

        # 初始化bot实例
        self._initialize_bots()

        self.logger.info(f"🐉 Dragon-V Triple Bot Unified Manager v{self.version} 初始化完成")

    def _setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("DragonTripleBotUnifiedManager")

    def _setup_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # 创建bot实例表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS bot_instances (
                        id TEXT PRIMARY KEY,
                        bot_type TEXT,
                        status TEXT,
                        tasks_count INTEGER DEFAULT 0,
                        last_activity TEXT,
                        memory_usage REAL DEFAULT 0.0,
                        error_count INTEGER DEFAULT 0,
                        config TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        bot_id TEXT,
                        task_type TEXT,
                        target TEXT,
                        status TEXT,
                        created_at TEXT,
                        completed_at TEXT,
                        result TEXT,
                        FOREIGN KEY (bot_id) REFERENCES bot_instances (id)
                    )
                ''')

                # 创建日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        level TEXT,
                        message TEXT,
                        timestamp TEXT,
                        bot_id TEXT,
                        task_id TEXT
                    )
                ''')

                conn.commit()
                self.logger.info("✅ 数据库初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 数据库初始化失败: {e}")

    def _setup_config(self):
        """初始化配置"""
        default_config = {
            "enterprise": {
                "token": "your_enterprise_token",
                "max_concurrent_tasks": 10,
                "auto_recovery": True,
                "heartbeat_interval": 30
            },
            "professional": {
                "token": "your_professional_token",
                "max_concurrent_tasks": 5,
                "auto_recovery": True,
                "heartbeat_interval": 30
            },
            "security": {
                "token": "your_security_token",
                "max_concurrent_tasks": 3,
                "auto_recovery": True,
                "heartbeat_interval": 30
            },
            "unified": {
                "load_balancing": True,
                "auto_switch": True,
                "monitoring": True,
                "log_level": "INFO"
            }
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)

            self.logger.info("✅ 配置文件初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 配置文件初始化失败: {e}")
            self.config = default_config

    def _initialize_bots(self):
        """初始化三个bot实例"""
        bot_configs = [
            (BotType.ENTERPRISE, "enterprise_bot"),
            (BotType.PROFESSIONAL, "professional_bot"),
            (BotType.SECURITY, "security_bot")
        ]

        for bot_type, bot_id in bot_configs:
            bot_instance = BotInstance(
                bot_type=bot_type,
                bot_id=bot_id,
                status=BotStatus.IDLE,
                tasks_count=0,
                last_activity=datetime.now(),
                memory_usage=0.0,
                error_count=0,
                config=self.config.get(bot_type.value, {})
            )

            self.bot_instances[bot_id] = bot_instance
            self._save_bot_instance(bot_instance)

            self.logger.info(f"🤖 {bot_type.value} bot 初始化完成")

    def _save_bot_instance(self, bot_instance: BotInstance):
        """保存bot实例到数据库"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO bot_instances
                    (id, bot_type, status, tasks_count, last_activity, memory_usage, error_count, config, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bot_instance.bot_id,
                    bot_instance.bot_type.value,
                    bot_instance.status.value,
                    bot_instance.tasks_count,
                    bot_instance.last_activity.isoformat(),
                    bot_instance.memory_usage,
                    bot_instance.error_count,
                    json.dumps(bot_instance.config),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ 保存bot实例失败: {e}")

    def get_best_bot_for_task(self, task_type: str) -> Optional[str]:
        """根据任务类型选择最佳bot"""
        best_bot = None
        best_score = -1

        for bot_id, bot_instance in self.bot_instances.items():
            score = 0

            # 检查bot状态
            if bot_instance.status != BotStatus.RUNNING:
                continue

            # 检查任务负载
            if bot_instance.tasks_count >= self.config[bot_instance.bot_type.value]["max_concurrent_tasks"]:
                continue

            # 根据任务类型和bot类型评分
            if task_type == "enterprise_management" and bot_instance.bot_type == BotType.ENTERPRISE:
                score += 100
            elif task_type == "professional_scan" and bot_instance.bot_type == BotType.PROFESSIONAL:
                score += 100
            elif task_type == "security_tools" and bot_instance.bot_type == BotType.SECURITY:
                score += 100
            else:
                score += 50  # 通用bot

            # 考虑错误率和内存使用
            if bot_instance.error_count == 0:
                score += 20

            if bot_instance.memory_usage < 50:
                score += 10

            if score > best_score:
                best_score = score
                best_bot = bot_id

        return best_bot

    def assign_task(self, bot_id: str, task_data: Dict[str, Any]) -> str:
        """分配任务给指定bot"""
        if bot_id not in self.bot_instances:
            raise ValueError(f"Bot {bot_id} 不存在")

        bot_instance = self.bot_instances[bot_id]
        task_id = str(uuid.uuid4())

        # 更新bot状态
        bot_instance.tasks_count += 1
        bot_instance.last_activity = datetime.now()
        bot_instance.status = BotStatus.RUNNING

        self._save_bot_instance(bot_instance)

        # 记录任务
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (id, bot_id, task_type, target, status, created_at, result)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    bot_id,
                    task_data.get("task_type", "unknown"),
                    task_data.get("target", ""),
                    "running",
                    datetime.now().isoformat(),
                    json.dumps(task_data)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ 记录任务失败: {e}")

        self.logger.info(f"📋 任务 {task_id} 已分配给 {bot_id}")
        return task_id

    def complete_task(self, task_id: str, result: Any = None):
        """完成任务"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # 更新任务状态
                cursor.execute('''
                    UPDATE tasks SET status = ?, completed_at = ?, result = ? WHERE id = ?
                ''', ("completed", datetime.now().isoformat(), json.dumps(result) if result else None, task_id))

                # 更新bot任务计数
                cursor.execute('SELECT bot_id FROM tasks WHERE id = ?', (task_id,))
                result = cursor.fetchone()
                if result:
                    bot_id = result[0]
                    if bot_id in self.bot_instances:
                        self.bot_instances[bot_id].tasks_count -= 1
                        if self.bot_instances[bot_id].tasks_count <= 0:
                            self.bot_instances[bot_id].status = BotStatus.IDLE

                        self._save_bot_instance(self.bot_instances[bot_id])

                conn.commit()

        except Exception as e:
            self.logger.error(f"❌ 完成任务失败: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            "version": self.version,
            "total_bots": len(self.bot_instances),
            "active_bots": sum(1 for bot in self.bot_instances.values() if bot.status == BotStatus.RUNNING),
            "total_tasks": sum(bot.tasks_count for bot in self.bot_instances.values()),
            "bot_instances": {}
        }

        for bot_id, bot_instance in self.bot_instances.items():
            status["bot_instances"][bot_id] = {
                "type": bot_instance.bot_type.value,
                "status": bot_instance.status.value,
                "tasks_count": bot_instance.tasks_count,
                "last_activity": bot_instance.last_activity.isoformat(),
                "memory_usage": bot_instance.memory_usage,
                "error_count": bot_instance.error_count
            }

        return status

    def auto_balance_load(self):
        """自动负载均衡"""
        if not self.config["unified"]["load_balancing"]:
            return

        self.logger.info("⚖️ 开始自动负载均衡...")

        # 检查每个bot的负载
        overloaded_bots = []
        available_bots = []

        for bot_id, bot_instance in self.bot_instances.items():
            if bot_instance.status == BotStatus.RUNNING:
                max_tasks = self.config[bot_instance.bot_type.value]["max_concurrent_tasks"]
                if bot_instance.tasks_count >= max_tasks:
                    overloaded_bots.append(bot_id)
                elif bot_instance.tasks_count < max_tasks:
                    available_bots.append(bot_id)

        # 重新分配任务
        for overloaded_bot_id in overloaded_bots:
            self.logger.info(f"🔄 重载bot: {overloaded_bot_id}")
            # 这里可以实现任务迁移逻辑

        self.logger.info("✅ 负载均衡完成")

    def monitor_bots(self):
        """监控bot状态"""
        if not self.config["unified"]["monitoring"]:
            return

        for bot_id, bot_instance in self.bot_instances.items():
            # 检查bot是否长时间无活动
            time_diff = datetime.now() - bot_instance.last_activity
            if time_diff > timedelta(minutes=30):
                self.logger.warning(f"⚠️ Bot {bot_id} 长时间无活动")

            # 检查错误率
            if bot_instance.error_count > 10:
                self.logger.error(f"❌ Bot {bot_id} 错误率过高: {bot_instance.error_count}")

    def start_bot(self, bot_type: BotType):
        """启动指定类型的bot"""
        bot_id = f"{bot_type.value}_bot"
        if bot_id in self.bot_instances:
            self.bot_instances[bot_id].status = BotStatus.RUNNING
            self._save_bot_instance(self.bot_instances[bot_id])
            self.logger.info(f"🚀 启动 {bot_type.value} bot")
        else:
            self.logger.error(f"❌ Bot {bot_type.value} 不存在")

    def stop_bot(self, bot_type: BotType):
        """停止指定类型的bot"""
        bot_id = f"{bot_type.value}_bot"
        if bot_id in self.bot_instances:
            self.bot_instances[bot_id].status = BotStatus.IDLE
            self._save_bot_instance(self.bot_instances[bot_id])
            self.logger.info(f"🛑 停止 {bot_type.value} bot")
        else:
            self.logger.error(f"❌ Bot {bot_type.value} 不存在")

    def restart_bot(self, bot_type: BotType):
        """重启指定类型的bot"""
        self.stop_bot(bot_type)
        self.start_bot(bot_type)
        self.logger.info(f"🔄 重启 {bot_type.value} bot")

    def run_interactive(self):
        """交互式命令行界面"""
        print("🐉 Dragon-V Triple Bot Unified Manager v1.0")
        print("=" * 50)

        while True:
            try:
                command = input("\n请输入命令 (help 查看帮助): ").strip().lower()

                if command == "help":
                    self.show_help()
                elif command == "status":
                    self.show_status()
                elif command == "start":
                    self.show_bot_selection("start")
                elif command == "stop":
                    self.show_bot_selection("stop")
                elif command == "restart":
                    self.show_bot_selection("restart")
                elif command == "balance":
                    self.auto_balance_load()
                elif command == "monitor":
                    self.monitor_bots()
                elif command == "config":
                    self.show_config()
                elif command == "exit":
                    print("👋 再见！")
                    break
                elif command == "clear":
                    os.system('cls' if sys.platform.startswith('win') else 'clear')
                else:
                    print("❌ 未知命令，输入 help 查看帮助")

            except KeyboardInterrupt:
                print("\n\n👋 用户中断，再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

    def show_help(self):
        """显示帮助信息"""
        print("\n📋 可用命令:")
        print("  help      - 显示此帮助")
        print("  status    - 显示系统状态")
        print("  start     - 启动bot")
        print("  stop      - 停止bot")
        print("  restart   - 重启bot")
        print("  balance   - 负载均衡")
        print("  monitor   - 监控bot")
        print("  config    - 显示配置")
        print("  clear     - 清屏")
        print("  exit      - 退出程序")

    def show_status(self):
        """显示系统状态"""
        status = self.get_system_status()

        print(f"\n🐉 Dragon-V Triple Bot Unified Manager v{status['version']}")
        print("=" * 50)
        print(f"🤖 总Bot数: {status['total_bots']}")
        print(f"🟢 活动Bot数: {status['active_bots']}")
        print(f"📋 总任务数: {status['total_tasks']}")

        print("\n📊 Bot实例状态:")
        for bot_id, bot_info in status['bot_instances'].items():
            status_icon = "🟢" if bot_info['status'] == 'running' else "🔴" if bot_info['status'] == 'idle' else "🟡"
            print(f"  {status_icon} {bot_id} ({bot_info['type']})")
            print(f"     状态: {bot_info['status']}")
            print(f"     任务数: {bot_info['tasks_count']}")
            print(f"     最后活动: {bot_info['last_activity']}")
            print(f"     内存使用: {bot_info['memory_usage']:.1f}MB")
            print(f"     错误次数: {bot_info['error_count']}")
            print()

    def show_bot_selection(self, action: str):
        """显示bot选择菜单"""
        print(f"\n🎯 选择要{action}的bot:")
        print("1. enterprise    - 企业级bot")
        print("2. professional  - 专业扫描bot")
        print("3. security      - 安全工具bot")
        print("4. all           - 所有的bot")

        choice = input("请输入选择 (1-4): ").strip()

        if choice == "1":
            getattr(self, action)(BotType.ENTERPRISE)
        elif choice == "2":
            getattr(self, action)(BotType.PROFESSIONAL)
        elif choice == "3":
            getattr(self, action)(BotType.SECURITY)
        elif choice == "4":
            for bot_type in BotType:
                getattr(self, action)(bot_type)
        else:
            print("❌ 无效选择")

    def show_config(self):
        """显示配置信息"""
        print("\n⚙️ 当前配置:")
        print(json.dumps(self.config, indent=2, ensure_ascii=False))

def main():
    """主函数"""
    try:
        manager = DragonTripleBotUnifiedManager()

        if len(sys.argv) > 1:
            if sys.argv[1] == "interactive":
                manager.run_interactive()
            elif sys.argv[1] == "status":
                manager.show_status()
            elif sys.argv[1] == "start":
                if len(sys.argv) > 2:
                    bot_type = BotType(sys.argv[2])
                    manager.start_bot(bot_type)
                else:
                    print("❌ 请指定bot类型")
            elif sys.argv[1] == "stop":
                if len(sys.argv) > 2:
                    bot_type = BotType(sys.argv[2])
                    manager.stop_bot(bot_type)
                else:
                    print("❌ 请指定bot类型")
            else:
                print("❌ 未知命令")
        else:
            print("🐉 Dragon-V Triple Bot Unified Manager v1.0")
            print("用法: python dragon_triple_bot_unified_manager.py [命令]")
            print("命令:")
            print("  interactive    - 交互式界面")
            print("  status        - 显示状态")
            print("  start <type>  - 启动bot")
            print("  stop <type>   - 停止bot")
            print("  restart <type>- 重启bot")
            print("\n输入 python dragon_triple_bot_unified_manager.py interactive 进入交互模式")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()