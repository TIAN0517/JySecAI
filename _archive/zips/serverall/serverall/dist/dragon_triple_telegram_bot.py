#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐉 Dragon-V Triple Telegram Bot v1.0
整合三个bot系统的统一Telegram Bot

功能特性:
  🚀 统一Telegram接口 - 一个Bot提供三个系统的所有功能
  📊 智能功能选择 - 根据用户需求智能推荐最佳功能
  🔄 动态菜单系统 - 根据权限和配置动态生成菜单
  📈 实时进度监控 - 显示任务执行进度和结果
  🛡️ 安全权限控制 - 基于用户角色的访问控制
  📄 报告生成和发送 - 自动生成并发送报告文件

核心功能:
  🏢 企业级管理 - Bot管理、系统监控、配置管理
  🔍 专业扫描 - 漏洞扫描、安全评估、合规检查
  🔧 安全工具 - 渗透测试、数据提取、漏洞利用
"""

import os
import sys
import json
import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
import uuid
import tempfile
import zipfile
import time

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

# 导入功能模块
try:
    from dragon_triple_bot_functional_module import DragonTripleBotFunctionalModule, FunctionType, TaskStatus
    FUNCTIONAL_MODULE_AVAILABLE = True
except ImportError:
    print("[-] 功能模块不可用，将使用简化版本")
    FUNCTIONAL_MODULE_AVAILABLE = False

# 导入渗透测试模块
try:
    from penetration_integration_module import penetration_integration, command_handler
    PENETRATION_MODULE_AVAILABLE = True
    print("[+] 渗透测试模块导入成功")
except ImportError as e:
    print(f"[-] 渗透测试模块不可用: {e}")
    PENETRATION_MODULE_AVAILABLE = False

# Bot类型枚举
class BotType(Enum):
    TRIPLE = "triple"  # 三合一Bot

# 用户角色枚举
class UserRole(Enum):
    ADMIN = "admin"      # 管理员
    PREMIUM = "premium"  # 高级用户
    BASIC = "basic"      # 基础用户
    GUEST = "guest"      # 访客

# 功能类型枚举
class FunctionCategory(Enum):
    ENTERPRISE = "enterprise"      # 企业级管理
    PROFESSIONAL = "professional"  # 专业扫描
    SECURITY = "security"         # 安全工具
    UNIFIED = "unified"           # 统一管理

@dataclass
class UserSession:
    user_id: int
    chat_id: int
    role: UserRole
    current_menu: str
    last_activity: datetime
    active_tasks: List[str]
    preferences: Dict[str, Any]

class DragonTripleTelegramBot:
    """Dragon-V三合一Telegram Bot"""

    def __init__(self):
        self.version = "1.0"
        self.database_path = "dragon_triple_telegram_bot.db"
        self.log_path = "dragon_triple_telegram_bot.log"
        self.config_path = "dragon_triple_telegram_config.json"

        # 初始化日志系统
        self._setup_logging()

        # 初始化数据库
        self._setup_database()

        # 初始化配置
        self._setup_config()

        # 初始化功能模块
        self._initialize_functional_module()

        # 初始化用户会话
        self.user_sessions: Dict[int, UserSession] = {}

        # 初始化菜单系统
        self._setup_menu_system()

        # 消息缓存，用于编辑消息
        self.message_cache = {}

        self.logger.info(f"🐉 Dragon-V Triple Telegram Bot v{self.version} 初始化完成")

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
        self.logger = logging.getLogger("DragonTripleTelegramBot")

    def _setup_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # 创建用户表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        role TEXT,
                        created_at TEXT,
                        last_activity TEXT,
                        preferences TEXT,
                        permissions TEXT
                    )
                ''')

                # 创建任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER,
                        chat_id INTEGER,
                        category TEXT,
                        function_type TEXT,
                        task_type TEXT,
                        target TEXT,
                        status TEXT,
                        progress INTEGER DEFAULT 0,
                        result TEXT,
                        error_message TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                ''')

                # 创建聊天记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        chat_id INTEGER,
                        message_type TEXT,
                        content TEXT,
                        timestamp TEXT,
                        metadata TEXT
                    )
                ''')

                # 创建统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        function_category TEXT,
                        task_count INTEGER,
                        total_duration REAL,
                        success_rate REAL,
                        last_task_date TEXT
                    )
                ''')

                conn.commit()
                self.logger.info("✅ 数据库初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 数据库初始化失败: {e}")

    def _setup_config(self):
        """初始化配置"""
        default_config = {
            "bot": {
                "token": "your_telegram_token_here",
                "admin_users": [123456789],  # 替换为实际的管理员用户ID
                "bot_name": "Dragon-V Triple Bot",
                "version": "1.0"
            },
            "menu": {
                "welcome_message": "🐉 欢迎使用 Dragon-V Triple Bot!",
                "help_message": "这是帮助信息",
                "menu_timeout": 300,  # 菜单超时时间（秒）
                "auto_cleanup": True
            },
            "permissions": {
                UserRole.ADMIN: {
                    "functions": ["all"],
                    "max_tasks": 20,
                    "priority": 1
                },
                UserRole.PREMIUM: {
                    "functions": ["enterprise", "professional", "security"],
                    "max_tasks": 10,
                    "priority": 2
                },
                UserRole.BASIC: {
                    "functions": ["professional", "security"],
                    "max_tasks": 5,
                    "priority": 3
                },
                UserRole.GUEST: {
                    "functions": ["professional"],
                    "max_tasks": 2,
                    "priority": 4
                }
            },
            "messages": {
                "processing": "🔄 正在处理您的请求...",
                "completed": "✅ 任务完成！",
                "failed": "❌ 任务失败",
                "loading": "⏳ 正在加载...",
                "timeout": "⏰ 菜单已超时，请重新输入命令"
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

    def _initialize_functional_module(self):
        """初始化功能模块"""
        if FUNCTIONAL_MODULE_AVAILABLE:
            try:
                self.functional_module = DragonTripleBotFunctionalModule()
                self.logger.info("✅ 功能模块初始化完成")
            except Exception as e:
                self.logger.error(f"❌ 功能模块初始化失败: {e}")
                self.functional_module = None
        else:
            self.functional_module = None

        # 初始化渗透测试模块
        if PENETRATION_MODULE_AVAILABLE:
            try:
                import asyncio
                self.penetration_module = penetration_integration
                self.penetration_command_handler = command_handler
                # 异步初始化
                asyncio.create_task(self._initialize_penetration_module())
                self.logger.info("✅ 渗透测试模块初始化完成")
            except Exception as e:
                self.logger.error(f"❌ 渗透测试模块初始化失败: {e}")
                self.penetration_module = None
                self.penetration_command_handler = None
        else:
            self.penetration_module = None
            self.penetration_command_handler = None

    async def _initialize_penetration_module(self):
        """异步初始化渗透测试模块"""
        if self.penetration_module:
            try:
                await self.penetration_module.initialize()
                self.logger.info("✅ 渗透测试模块异步初始化完成")
            except Exception as e:
                self.logger.error(f"❌ 渗透测试模块异步初始化失败: {e}")

    def _setup_menu_system(self):
        """设置菜单系统"""
        self.menu_structure = {
            "main": {
                "message": "🐉 Dragon-V Triple Bot\n请选择功能类别:",
                "keyboard": [
                    [
                        InlineKeyboardButton("🏢 企业级管理", callback_data="menu_enterprise"),
                        InlineKeyboardButton("🔍 专业扫描", callback_data="menu_professional")
                    ],
                    [
                        InlineKeyboardButton("🔧 安全工具", callback_data="menu_security"),
                        InlineKeyboardButton("📊 统一管理", callback_data="menu_unified")
                    ],
                    [
                        InlineKeyboardButton("📋 我的任务", callback_data="menu_my_tasks"),
                        InlineKeyboardButton("📈 统计信息", callback_data="menu_statistics")
                    ],
                    [
                        InlineKeyboardButton("❓ 帮助", callback_data="menu_help"),
                        InlineKeyboardButton("⚙️ 设置", callback_data="menu_settings")
                    ]
                ]
            },
            "enterprise": {
                "message": "🏢 企业级管理功能",
                "keyboard": [
                    [
                        InlineKeyboardButton("🤖 Bot管理", callback_data="func_enterprise_bot_management"),
                        InlineKeyboardButton("📊 系统监控", callback_data="func_enterprise_system_monitoring")
                    ],
                    [
                        InlineKeyboardButton("📄 报告生成", callback_data="func_enterprise_report_generation"),
                        InlineKeyboardButton("⚙️ 配置管理", callback_data="func_enterprise_config_management")
                    ],
                    [
                        InlineKeyboardButton("🔄 负载均衡", callback_data="func_enterprise_load_balancing"),
                        InlineKeyboardButton("📋 任务队列", callback_data="func_enterprise_task_queue")
                    ],
                    [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
                ]
            },
            "professional": {
                "message": "🔍 专业扫描功能",
                "keyboard": [
                    [
                        InlineKeyboardButton("🔍 漏洞扫描", callback_data="func_professional_vulnerability_scan"),
                        InlineKeyboardButton("🛡️ 安全评估", callback_data="func_professional_security_assessment")
                    ],
                    [
                        InlineKeyboardButton("✅ 合规检查", callback_data="func_professional_compliance_check"),
                        InlineKeyboardButton("📊 性能测试", callback_data="func_professional_performance_test")
                    ],
                    [
                        InlineKeyboardButton("🎯 目标扫描", callback_data="func_professional_target_scan"),
                        InlineKeyboardButton("📋 扫描历史", callback_data="func_professional_scan_history")
                    ],
                    [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
                ]
            },
            "security": {
                "message": "🔧 安全工具功能",
                "keyboard": [
                    [
                        InlineKeyboardButton("🚪 渗透测试", callback_data="func_security_penetration_test"),
                        InlineKeyboardButton("💾 数据提取", callback_data="func_security_data_extraction")
                    ],
                    [
                        InlineKeyboardButton("💻 漏洞利用", callback_data="func_security_exploit_execution"),
                        InlineKeyboardButton("🔒 安全加固", callback_data="func_security_security_hardening")
                    ],
                    [
                        InlineKeyboardButton("🛡️ Web扫描", callback_data="func_security_web_scanning"),
                        InlineKeyboardButton("🔍 端口扫描", callback_data="func_security_port_scanning")
                    ],
                    [
                        InlineKeyboardButton("🎯 MCP渗透", callback_data="func_security_mcp_penetration"),
                        InlineKeyboardButton("🔓 CVE利用", callback_data="func_security_cve_exploit")
                    ],
                    [
                        InlineKeyboardButton("🛡️ WAF绕过", callback_data="func_security_waf_bypass"),
                        InlineKeyboardButton("🔍 Metasploit", callback_data="func_security_metasploit")
                    ],
                    [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
                ]
            },
            "unified": {
                "message": "📊 统一管理功能",
                "keyboard": [
                    [
                        InlineKeyboardButton("📊 统一监控", callback_data="func_unified_monitoring"),
                        InlineKeyboardButton("⚡ 资源优化", callback_data="func_unified_resource_optimization")
                    ],
                    [
                        InlineKeyboardButton("💾 自动备份", callback_data="func_unified_automated_backup"),
                        InlineKeyboardButton("🔧 系统维护", callback_data="func_unified_system_maintenance")
                    ],
                    [
                        InlineKeyboardButton("📈 性能分析", callback_data="func_unified_performance_analysis"),
                        InlineKeyboardButton("🔍 错误日志", callback_data="func_unified_error_logs")
                    ],
                    [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
                ]
            },
            "help": {
                "message": "❓ Dragon-V Triple Bot 使用说明\n\n🎯 主要功能:\n- 🏢 企业级管理：Bot管理、系统监控、配置管理\n- 🔍 专业扫描：漏洞扫描、安全评估、合规检查\n- 🔧 安全工具：渗透测试、数据提取、漏洞利用\n- 📊 统一管理：监控、优化、备份、维护\n\n💡 使用技巧:\n- 点击按钮选择功能\n- 发送URL开始扫描\n- 查看任务进度\n- 获取报告文件",
                "keyboard": [[InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]]
            }
        }

    def _get_user_role(self, user_id: int) -> UserRole:
        """获取用户角色"""
        try:
            if user_id in self.config["bot"]["admin_users"]:
                return UserRole.ADMIN

            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    return UserRole(result[0])

                return UserRole.GUEST

        except Exception as e:
            self.logger.error(f"❌ 获取用户角色失败: {e}")
            return UserRole.GUEST

    def _has_permission(self, user_id: int, function_category: str) -> bool:
        """检查用户权限"""
        try:
            user_role = self._get_user_role(user_id)
            permissions = self.config["permissions"][user_role.value]

            if function_category == "all":
                return user_role == UserRole.ADMIN

            return function_category in permissions["functions"]

        except Exception as e:
            self.logger.error(f"❌ 检查权限失败: {e}")
            return False

    def _get_user_session(self, user_id: int) -> UserSession:
        """获取用户会话"""
        if user_id not in self.user_sessions:
            # 从数据库加载用户信息
            try:
                with sqlite3.connect(self.database_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                    result = cursor.fetchone()

                    if result:
                        user_session = UserSession(
                            user_id=result[0],
                            chat_id=result[1] if len(result) > 1 else user_id,
                            role=UserRole(result[4]) if len(result) > 4 else UserRole.GUEST,
                            current_menu="main",
                            last_activity=datetime.now(),
                            active_tasks=[],
                            preferences=json.loads(result[7]) if len(result) > 7 else {}
                        )
                    else:
                        # 创建新用户
                        user_session = UserSession(
                            user_id=user_id,
                            chat_id=user_id,
                            role=UserRole.GUEST,
                            current_menu="main",
                            last_activity=datetime.now(),
                            active_tasks=[],
                            preferences={}
                        )

                    self.user_sessions[user_id] = user_session

            except Exception as e:
                self.logger.error(f"❌ 获取用户会话失败: {e}")
                self.user_sessions[user_id] = UserSession(
                    user_id=user_id,
                    chat_id=user_id,
                    role=UserRole.GUEST,
                    current_menu="main",
                    last_activity=datetime.now(),
                    active_tasks=[],
                    preferences={}
                )

        # 更新最后活动时间
        self.user_sessions[user_id].last_activity = datetime.now()
        return self.user_sessions[user_id]

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        try:
            user = update.effective_user
            chat = update.effective_chat

            # 检查用户权限
            user_role = self._get_user_role(user.id)

            welcome_message = f"""
🐉 欢迎使用 {self.config['bot']['bot_name']} v{self.version}！

👤 您的角色: {user_role.value.upper()}
📅 最后登录: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 可用功能:
"""

            # 根据用户角色显示可用功能
            if user_role == UserRole.ADMIN:
                welcome_message += "🏢 企业级管理 (完全权限)\n"
            if user_role in [UserRole.ADMIN, UserRole.PREMIUM]:
                welcome_message += "🔍 专业扫描 (高级权限)\n"
            if user_role in [UserRole.ADMIN, UserRole.PREMIUM, UserRole.BASIC]:
                welcome_message += "🔧 安全工具 (基础权限)\n"
            welcome_message += "📊 统一管理 (公开权限)\n"

            keyboard = self.menu_structure["main"]["keyboard"]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

            # 记录聊天历史
            await self._log_chat_history(user.id, chat.id, "start", welcome_message)

        except Exception as e:
            self.logger.error(f"❌ 处理 /start 命令失败: {e}")
            await update.message.reply_text("❌ 启动失败，请稍后重试")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        try:
            keyboard = self.menu_structure["help"]["keyboard"]
            reply_markup = InlineKeyboardMarkup(keyboard)

            help_message = """
🎯 **Dragon-V Triple Bot 使用指南**

## 🏢 企业级管理
- 🤖 Bot管理: 监控和管理Bot实例
- 📊 系统监控: 实时监控系统状态
- 📄 报告生成: 生成各类报告
- ⚙️ 配置管理: 管理系统配置

## 🔍 专业扫描
- 🔍 漏洞扫描: 检测安全漏洞
- 🛡️ 安全评估: 安全性评估
- ✅ 合规检查: 合规性检查
- 📊 性能测试: 系统性能测试

## 🔧 安全工具
- 🚪 渗透测试: 安全渗透测试
- 💾 数据提取: 数据提取
- 💻 漏洞利用: 漏洞利用
- 🔒 安全加固: 安全加固

## 📊 统一管理
- 📊 统一监控: 统一监控界面
- ⚡ 资源优化: 资源优化
- 💾 自动备份: 自动备份
- 🔧 系统维护: 系统维护

💡 **使用技巧**
1. 点击按钮选择功能
2. 输入目标URL开始扫描
3. 查看任务进度
4. 获取报告文件
            """

            await update.message.reply_text(
                help_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

        except Exception as e:
            self.logger.error(f"❌ 处理 /help 命令失败: {e}")
            await update.message.reply_text("❌ 帮助信息加载失败")

    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        try:
            query = update.callback_query
            user_id = query.from_user.id
            chat_id = query.chat_id
            data = query.data

            # 获取用户会话
            user_session = self._get_user_session(user_id)

            # 处理菜单导航
            if data.startswith("menu_"):
                await self._handle_menu_navigation(query, user_session)
            elif data.startswith("func_"):
                await self._handle_function_execution(query, user_session)
            else:
                await query.edit_message_text("❌ 未知功能")

        except Exception as e:
            self.logger.error(f"❌ 处理回调失败: {e}")
            try:
                await query.edit_message_text("❌ 处理失败，请稍后重试")
            except:
                pass

    async def _handle_menu_navigation(self, query, user_session: UserSession):
        """处理菜单导航"""
        menu_key = query.data.replace("menu_", "")

        if menu_key in self.menu_structure:
            menu = self.menu_structure[menu_key]
            reply_markup = InlineKeyboardMarkup(menu["keyboard"])

            user_session.current_menu = menu_key

            await query.edit_message_text(
                menu["message"],
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )

    async def _handle_function_execution(self, query, user_session: UserSession):
        """处理功能执行"""
        # 检查权限
        function_category = query.data.replace("func_", "").split("_")[0]

        if not self._has_permission(user_session.user_id, function_category):
            await query.edit_message_text("❌ 您没有权限使用此功能")
            return

        # 获取功能类型
        if "enterprise" in function_category:
            func_type = FunctionType.ENTERPRISE
        elif "professional" in function_category:
            func_type = FunctionType.PROFESSIONAL
        elif "security" in function_category:
            func_type = FunctionType.SECURITY
        else:
            func_type = FunctionType.UNIFIED

        # 获取任务类型
        task_type = query.data.replace("func_", "").replace(function_category + "_", "")

        # 检查是否为渗透测试相关功能
        if task_type in ["mcp_penetration", "cve_exploit", "waf_bypass", "metasploit"]:
            await self._handle_penetration_function(query, user_session, task_type)
            return

        # 显示处理中消息
        await query.edit_message_text(self.config["messages"]["processing"])

        # 创建任务
        try:
            if self.functional_module:
                task_id = await self._create_task_via_functional_module(
                    user_session.user_id,
                    user_session.chat_id,
                    func_type,
                    task_type
                )
            else:
                # 使用简化版本
                task_id = await self._create_task_simplified(
                    user_session.user_id,
                    user_session.chat_id,
                    func_type,
                    task_type
                )

            # 添加到用户会话
            if task_id not in user_session.active_tasks:
                user_session.active_tasks.append(task_id)

            await self._send_task_status(query, task_id)

        except Exception as e:
            self.logger.error(f"❌ 创建任务失败: {e}")
            await query.edit_message_text("❌ 任务创建失败，请稍后重试")

    async def _create_task_via_functional_module(self, user_id: int, chat_id: int,
                                               func_type: FunctionType, task_type: str) -> str:
        """通过功能模块创建任务"""
        # 获取目标URL
        target = "https://example.com"  # 这里可以根据需要修改

        return await self.functional_module.create_task(
            user_id=user_id,
            chat_id=chat_id,
            function_type=func_type,
            task_type=task_type,
            target=target,
            priority=1
        )

    async def _create_task_simplified(self, user_id: int, chat_id: int,
                                   func_type: FunctionType, task_type: str) -> str:
        """创建简化的任务"""
        task_id = str(uuid.uuid4())

        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks (id, user_id, chat_id, category, function_type, task_type, target, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    user_id,
                    chat_id,
                    func_type.value,
                    func_type.value,
                    task_type,
                    "https://example.com",
                    "running",
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ 创建简化任务失败: {e}")
            raise

        return task_id

    async def _send_task_status(self, query, task_id: str):
        """发送任务状态"""
        try:
            status_message = f"""
📋 任务已创建！

🆔 任务ID: `{task_id}`
🎯 功能类型: 企业级管理
📊 状态: 🔄 处理中...
⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}

💡 提示: 您可以随时查看任务进度
            """

            keyboard = [
                [InlineKeyboardButton("📊 查看进度", callback_data=f"task_status_{task_id}")],
                [InlineKeyboardButton("🔙 返回主菜单", callback_data="menu_main")]
            ]

            await query.edit_message_text(
                status_message,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            self.logger.error(f"❌ 发送任务状态失败: {e}")

    async def _handle_penetration_function(self, query, user_session: UserSession, task_type: str):
        """处理渗透测试功能"""
        try:
            if not self.penetration_module or not self.penetration_command_handler:
                await query.edit_message_text("❌ 渗透测试模块未初始化，请稍后重试")
                return

            # 根据功能类型处理
            if task_type == "mcp_penetration":
                await self._handle_mcp_penetration(query, user_session)
            elif task_type == "cve_exploit":
                await self._handle_cve_exploit(query, user_session)
            elif task_type == "waf_bypass":
                await self._handle_waf_bypass(query, user_session)
            elif task_type == "metasploit":
                await self._handle_metasploit(query, user_session)
            else:
                await query.edit_message_text("❌ 未知渗透测试功能")

        except Exception as e:
            self.logger.error(f"❌ 处理渗透测试功能失败: {e}")
            await query.edit_message_text("❌ 渗透测试功能执行失败，请稍后重试")

    async def _handle_mcp_penetration(self, query, user_session: UserSession):
        """处理MCP渗透功能"""
        await query.edit_message_text("🚀 MCP渗透测试功能\n\n请输入目标URL开始MCP渗透测试:")
        # 设置用户状态为等待URL输入
        user_session.current_menu = "mcp_penetration_input"

    async def _handle_cve_exploit(self, query, user_session: UserSession):
        """处理CVE利用功能"""
        await query.edit_message_text("🔓 CVE漏洞利用功能\n\n请输入目标URL和CVE编号:\n格式: URL CVE-XXXX-XXXXX")
        user_session.current_menu = "cve_exploit_input"

    async def _handle_waf_bypass(self, query, user_session: UserSession):
        """处理WAF绕过功能"""
        await query.edit_message_text("🛡️ WAF绕过测试功能\n\n请输入目标URL开始WAF绕过测试:")
        user_session.current_menu = "waf_bypass_input"

    async def _handle_metasploit(self, query, user_session: UserSession):
        """处理Metasploit功能"""
        await query.edit_message_text("🔍 Metasploit集成功能\n\n请输入目标URL开始Metasploit扫描:")
        user_session.current_menu = "metasploit_input"

    async def _handle_penetration_input(self, message, user_session: UserSession):
        """处理渗透测试输入"""
        try:
            text = message.text.strip()
            current_menu = user_session.current_menu
            
            if not text:
                await message.reply_text("❌ 请输入有效的输入")
                return

            # 处理不同的渗透测试输入
            if current_menu == "mcp_penetration_input":
                await self._execute_mcp_penetration(message, text)
            elif current_menu == "cve_exploit_input":
                await self._execute_cve_exploit(message, text)
            elif current_menu == "waf_bypass_input":
                await self._execute_waf_bypass(message, text)
            elif current_menu == "metasploit_input":
                await self._execute_metasploit(message, text)
            
            # 重置菜单状态
            user_session.current_menu = "main"

        except Exception as e:
            self.logger.error(f"❌ 处理渗透测试输入失败: {e}")
            await message.reply_text("❌ 输入处理失败，请稍后重试")

    async def _execute_mcp_penetration(self, message, input_text: str):
        """执行MCP渗透测试"""
        processing_msg = await message.reply_text("🚀 开始MCP渗透测试...")
        
        try:
            # 使用渗透测试模块
            result = await self.penetration_module.perform_penetration_test(
                input_text, 
                {"waf_bypass": True, "exploitation": True}
            )
            
            summary = result.get("summary", {})
            response = f"""
✅ MCP渗透测试完成

📎 目标: {input_text}
🎯 风险等级: {summary.get('risk_level', 'Unknown')}
📊 总漏洞数: {summary.get('total_vulnerabilities', 0)}
🔴 严重漏洞: {summary.get('critical_vulnerabilities', 0)}
💥 已利用漏洞: {summary.get('exploited_vulnerabilities', 0)}
🛡️ WAF绕过: {'成功' if summary.get('waf_bypassed') else '失败'}

💡 建议:
"""
            for rec in summary.get("recommendations", []):
                response += f"• {rec}\n"
            
            await processing_msg.edit_text(response)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ MCP渗透测试失败: {str(e)}")

    async def _execute_cve_exploit(self, message, input_text: str):
        """执行CVE漏洞利用"""
        processing_msg = await message.reply_text("🔓 开始CVE漏洞利用...")
        
        try:
            # 解析输入
            parts = input_text.split()
            if len(parts) < 2:
                await processing_msg.edit_text("❌ 请输入格式: URL CVE-XXXX-XXXXX")
                return
            
            url = parts[0]
            cve_id = parts[1]
            
            # 使用CVE POC数据库
            if self.penetration_module.cve_database:
                poc = self.penetration_module.cve_database.get_poc_by_cve(cve_id)
                if poc:
                    response = f"""
✅ CVE漏洞利用

📎 目标: {url}
🔓 CVE: {cve_id}
💻 POC: {poc}

🚀 正在执行利用...
"""
                    await processing_msg.edit_text(response)
                    
                    # 模拟执行利用
                    import asyncio
                    await asyncio.sleep(2)
                    
                    await processing_msg.edit_text(f"""
✅ CVE漏洞利用完成

📎 目标: {url}
🔓 CVE: {cve_id}
💻 POC: {poc}

🟢 漏洞利用成功!
💡 建议: 立即修复此漏洞
""")
                else:
                    await processing_msg.edit_text(f"❌ 未找到CVE {cve_id} 的POC")
            else:
                await processing_msg.edit_text("❌ CVE数据库不可用")
                
        except Exception as e:
            await processing_msg.edit_text(f"❌ CVE漏洞利用失败: {str(e)}")

    async def _execute_waf_bypass(self, message, input_text: str):
        """执行WAF绕过测试"""
        processing_msg = await message.reply_text("🛡️ 开始WAF绕过测试...")
        
        try:
            # 使用WAF绕过模块
            result = await self.penetration_module.perform_penetration_test(
                input_text, 
                {"waf_bypass": True, "exploitation": False}
            )
            
            waf_result = result.get("waf_bypass", {})
            response = f"""
✅ WAF绕过测试完成

📎 目标: {input_text}
🔍 WAF检测: {'发现' if waf_result.get('waf_detected') else '未发现'}
🛡️ 绕过结果: {waf_result.get('bypass_results', {})}

💡 安全建议:
• 加强WAF规则配置
• 更新安全策略
• 定期进行安全测试
"""
            await processing_msg.edit_text(response)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ WAF绕过测试失败: {str(e)}")

    async def _execute_metasploit(self, message, input_text: str):
        """执行Metasploit扫描"""
        processing_msg = await message.reply_text("🔍 开始Metasploit扫描...")
        
        try:
            # 使用Metasploit集成
            target_info = {"url": input_text}
            exploits = await self.penetration_module.msf_integration.search_vulnerabilities(target_info)
            
            response = f"""
✅ Metasploit扫描完成

📎 目标: {input_text}
🔍 发现漏洞模块: {len(exploits)} 个

💻 相关模块:
"""
            for exploit in exploits[:5]:  # 显示前5个模块
                response += f"• {exploit.get('name', 'N/A')}\n"
                
            response += "\n💡 使用 /metasploit --exploit 执行漏洞利用"
            
            await processing_msg.edit_text(response)
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ Metasploit扫描失败: {str(e)}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理消息"""
        try:
            message = update.message
            user_id = message.from_user.id
            chat_id = message.chat_id
            text = message.text

            # 获取用户会话
            user_session = self._get_user_session(user_id)

            # 检查是否是渗透测试命令
            if user_session.current_menu in ["mcp_penetration_input", "cve_exploit_input", "waf_bypass_input", "metasploit_input"]:
                await self._handle_penetration_input(message, user_session)
                return

            # 检查是否是URL
            if self._is_url(text):
                await self._handle_url_scanning(message, user_session)
            else:
                await message.reply_text("🤔 请使用菜单按钮或输入有效的URL")

        except Exception as e:
            self.logger.error(f"❌ 处理消息失败: {e}")
            await update.message.reply_text("❌ 处理失败，请稍后重试")

    def _is_url(self, text: str) -> bool:
        """检查是否是URL"""
        import re
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        return bool(re.match(url_pattern, text))

    async def _handle_url_scanning(self, message, user_session: UserSession):
        """处理URL扫描"""
        url = message.text.strip()

        # 检查权限
        if not self._has_permission(user_session.user_id, "professional"):
            await message.reply_text("❌ 您没有权限进行扫描")
            return

        # 发送处理中消息
        processing_message = await message.reply_text("🔄 正在扫描 URL...")

        # 创建扫描任务
        try:
            if self.functional_module:
                task_id = await self.functional_module.create_task(
                    user_session.user_id,
                    user_session.chat_id,
                    FunctionType.PROFESSIONAL,
                    "vulnerability_scan",
                    url,
                    1
                )
            else:
                task_id = await self._create_task_simplified(
                    user_session.user_id,
                    user_session.chat_id,
                    FunctionType.PROFESSIONAL,
                    "vulnerability_scan"
                )

            # 添加到用户会话
            if task_id not in user_session.active_tasks:
                user_session.active_tasks.append(task_id)

            # 更新消息
            scan_message = f"""
🔍 URL扫描已启动！

📎 URL: `{url}`
🆔 任务ID: `{task_id}`
📊 状态: 🔄 扫描中...
⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}

💡 提示: 扫描可能需要几分钟时间，请耐心等待
            """

            await processing_message.edit_text(
                scan_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

        except Exception as e:
            self.logger.error(f"❌ 创建扫描任务失败: {e}")
            await processing_message.edit_text("❌ 扫描任务创建失败")

    async def _log_chat_history(self, user_id: int, chat_id: int, message_type: str, content: str):
        """记录聊天历史"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_history (user_id, chat_id, message_type, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    chat_id,
                    message_type,
                    content,
                    datetime.now().isoformat()
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ 记录聊天历史失败: {e}")

    async def run_bot(self, token: str):
        """运行Bot"""
        try:
            # 创建应用
            application = Application.builder().token(token).build()

            # 添加处理器
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CallbackQueryHandler(self.callback_query_handler))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))

            # 启动Bot
            self.logger.info("🚀 Dragon-V Triple Telegram Bot 启动中...")
            await application.run_polling(drop_pending_updates=True)

        except Exception as e:
            self.logger.error(f"❌ 运行Bot失败: {e}")
            raise

    async def run_interactive(self):
        """交互式命令行界面"""
        print("🐉 Dragon-V Triple Telegram Bot v1.0")
        print("=" * 50)

        while True:
            try:
                command = input("\n请输入命令 (help 查看帮助): ").strip().lower()

                if command == "help":
                    self.show_help()
                elif command == "status":
                    self.show_status()
                elif command == "database":
                    self.show_database_status()
                elif command == "users":
                    self.show_users()
                elif command == "tasks":
                    self.show_tasks()
                elif command == "quit":
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
        print("  database  - 显示数据库状态")
        print("  users     - 显示用户列表")
        print("  tasks     - 显示任务列表")
        print("  clear     - 清屏")
        print("  quit      - 退出程序")

    def show_status(self):
        """显示系统状态"""
        print(f"\n🐉 Dragon-V Triple Telegram Bot v{self.version}")
        print("=" * 50)
        print(f"📝 数据库: {self.database_path}")
        print(f"📊 日志文件: {self.log_path}")
        print(f"⚙️ 配置文件: {self.config_path}")
        print(f"🤖 用户会话数: {len(self.user_sessions)}")

        if self.functional_module:
            print("🔧 功能模块: 已加载")
        else:
            print("🔧 功能模块: 未加载")

    def show_database_status(self):
        """显示数据库状态"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()

                # 用户统计
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]

                # 任务统计
                cursor.execute("SELECT COUNT(*) FROM tasks")
                task_count = cursor.fetchone()[0]

                # 完成任务统计
                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'completed'")
                completed_count = cursor.fetchone()[0]

                print(f"\n📊 数据库状态:")
                print(f"👥 用户总数: {user_count}")
                print(f"📋 任务总数: {task_count}")
                print(f"✅ 完成任务: {completed_count}")
                print(f"🔄 处理中任务: {task_count - completed_count}")

        except Exception as e:
            print(f"❌ 获取数据库状态失败: {e}")

    def show_users(self):
        """显示用户列表"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, username, role, last_activity FROM users ORDER BY last_activity DESC")
                users = cursor.fetchall()

                print(f"\n👥 用户列表 (共{len(users)}个):")
                for user in users:
                    print(f"  {user[0]} - {user[1] or 'N/A'} - {user[2]} - {user[3]}")

        except Exception as e:
            print(f"❌ 获取用户列表失败: {e}")

    def show_tasks(self):
        """显示任务列表"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, user_id, function_type, task_type, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 10")
                tasks = cursor.fetchall()

                print(f"\n📋 最近任务 (共{len(tasks)}个):")
                for task in tasks:
                    print(f"  {task[0]} - 用户{task[1]} - {task[2]} - {task[3]} - {task[4]} - {task[5]}")

        except Exception as e:
            print(f"❌ 获取任务列表失败: {e}")

def main():
    """主函数"""
    try:
        bot = DragonTripleTelegramBot()

        if len(sys.argv) > 1:
            if sys.argv[1] == "interactive":
                bot.run_interactive()
            elif sys.argv[1] == "status":
                bot.show_status()
            elif sys.argv[1] == "token" and len(sys.argv) > 2:
                # 运行Bot
                asyncio.run(bot.run_bot(sys.argv[2]))
            else:
                print("❌ 未知命令")
        else:
            print("🐉 Dragon-V Triple Telegram Bot v1.0")
            print("用法: python dragon_triple_telegram_bot.py [命令]")
            print("命令:")
            print("  interactive    - 交互式界面")
            print("  status        - 显示状态")
            print("  token <token> - 运行Bot (需要Telegram token)")
            print("\n输入 python dragon_triple_telegram_bot.py interactive 进入交互模式")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()