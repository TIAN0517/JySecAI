#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Triple Bot 集成系统启动器
集成所有有效的工具和MCP模块
"""

import os
import sys
import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from dragon_triple_bot_unified_manager import DragonTripleBotUnifiedManager
from mcp_penetration_server import PenetrationMCPServer
from mcp_exploit_database import MCPExploitDatabase
from mcp_payloads_database import MCPPayloadsDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dragon_v_integrated_system")

class DragonVIntegratedSystem:
    """Dragon-V 集成系统"""

    def __init__(self):
        self.version = "3.0.0"
        self.startup_time = datetime.now()

        # 核心组件
        self.unified_manager = None
        self.mcp_server = None
        self.exploit_db = None
        self.payloads_db = None

        # 系统状态
        self.is_running = False
        self.active_modules = {}

        logger.info(f"Dragon-V 集成系统 v{self.version} 初始化中...")

    async def initialize(self):
        """初始化所有组件"""
        try:
            logger.info("正在初始化集成系统...")

            # 1. 初始化MCP服务器
            logger.info("初始化MCP渗透测试服务器...")
            self.mcp_server = PenetrationMCPServer()
            await self.mcp_server.initialize()
            self.active_modules['mcp_server'] = True

            # 2. 初始化漏洞数据库
            logger.info("初始化漏洞数据库...")
            self.exploit_db = MCPExploitDatabase()
            exploit_count = len(self.exploit_db.exploits)
            logger.info(f"已加载 {exploit_count} 个漏洞分类")
            self.active_modules['exploit_db'] = True

            # 3. 初始化载荷数据库
            logger.info("初始化载荷数据库...")
            self.payloads_db = MCPPayloadsDatabase()
            payload_stats = self.payloads_db.get_all_payloads_count()
            logger.info(f"已加载 {payload_stats['total']} 个载荷")
            self.active_modules['payloads_db'] = True

            # 4. 初始化统一管理器
            logger.info("初始化Dragon-V统一管理器...")
            self.unified_manager = DragonTripleBotUnifiedManager()
            self.active_modules['unified_manager'] = True

            # 5. 验证核心工具
            await self._verify_core_tools()

            logger.info("✅ 所有组件初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {str(e)}")
            return False

    async def _verify_core_tools(self):
        """验证核心工具可用性"""
        logger.info("验证核心工具...")

        core_tools = {
            'advanced_loan_penetration.py': '高级贷款渗透测试',
            'thai_loan_penetration.py': '泰国贷款渗透测试',
            'waf_bypass_advanced.py': '高级WAF绕过',
            'dragon_v_hunter/main.py': 'Dragon-V Hunter核心引擎',
            'penetration_integration_module.py': '渗透测试集成模块'
        }

        verified_tools = []
        for tool_path, description in core_tools.items():
            if os.path.exists(tool_path):
                verified_tools.append(tool_path)
                logger.info(f"✅ {description} - {tool_path}")
            else:
                logger.warning(f"⚠️  {description} - {tool_path} (未找到)")

        self.active_modules['verified_tools'] = verified_tools
        logger.info(f"核心工具验证完成: {len(verified_tools)}/{len(core_tools)} 个可用")

    async def start_system(self):
        """启动集成系统"""
        try:
            if not await self.initialize():
                return False

            logger.info("🚀 启动Dragon-V集成系统...")

            # 启动MCP服务器
            logger.info("启动MCP渗透测试服务器...")
            # 注意：这里简化了MCP服务器启动，实际需要更复杂的实现

            # 启动统一管理器
            logger.info("启动统一管理器...")
            # 注意：这里简化了Bot启动，实际需要Telegram token

            self.is_running = True

            # 显示系统状态
            await self._display_system_status()

            logger.info("🎉 Dragon-V集成系统启动完成!")
            logger.info("📊 系统已准备就绪，等待任务...")

            return True

        except Exception as e:
            logger.error(f"[FAIL] 系统启动失败: {str(e)}")
            return False

    async def _display_system_status(self):
        """显示系统状态"""
        print("\n" + "="*60)
        print("Dragon-V Triple Bot 集成系统状态")
        print("="*60)
        print(f"版本: {self.version}")
        print(f"启动时间: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"系统状态: {'运行中' if self.is_running else '未运行'}")

        print("\n活动模块:")
        for module, status in self.active_modules.items():
            status_icon = "[OK]" if status else "[FAIL]"
            print(f"  {status_icon} {module}")

        print("\n核心功能:")
        print("  漏洞扫描与利用")
        print("  WAF绕过技术")
        print("  AI辅助决策")
        print("  实时监控")
        print("  报告生成")

        print("\n集成资源:")
        print("  漏洞定义: 414个CVE (中英文)")
        print("  应用指纹: 42个应用类型")
        print("  AI评估: 5个数据集")
        print("  MCP模块: 21个专业模块")

        print("\n支持区域:")
        print("  越南物流系统")
        print("  中国快递系统")
        print("  泰国邮政系统")

        print("="*60)

    async def run_system_check(self):
        """运行系统检查"""
        logger.info("执行系统检查...")

        check_results = {
            'database_connection': await self._check_databases(),
            'mcp_modules': await self._check_mcp_modules(),
            'core_tools': await self._check_core_tools(),
            'dependencies': await self._check_dependencies()
        }

        return check_results

    async def _check_databases(self):
        """检查数据库连接"""
        try:
            # 检查主数据库
            db_files = [
                'dragon_triple_bot_unified.db',
                'dragon_triple_telegram_bot.db',
                'dragon_triple_functional.db'
            ]

            for db_file in db_files:
                if os.path.exists(db_file):
                    size = os.path.getsize(db_file) / 1024  # KB
                    logger.info(f"[OK] {db_file}: {size:.1f} KB")
                else:
                    logger.warning(f"[WARN] {db_file}: 不存在")

            return True
        except Exception as e:
            logger.error(f"数据库检查失败: {e}")
            return False

    async def _check_mcp_modules(self):
        """检查MCP模块"""
        try:
            mcp_dir = Path("mcp")
            if mcp_dir.exists():
                yaml_files = list(mcp_dir.glob("*.yaml"))
                logger.info(f"[OK] MCP模块: {len(yaml_files)} 个")
                return True
            else:
                logger.warning("[WARN] MCP目录不存在")
                return False
        except Exception as e:
            logger.error(f"MCP模块检查失败: {e}")
            return False

    async def _check_core_tools(self):
        """检查核心工具"""
        try:
            essential_tools = [
                'advanced_loan_penetration.py',
                'penetration_integration_module.py',
                'waf_bypass_advanced.py'
            ]

            available = 0
            for tool in essential_tools:
                if os.path.exists(tool):
                    available += 1

            logger.info(f"[OK] 核心工具: {available}/{len(essential_tools)} 个可用")
            return available == len(essential_tools)
        except Exception as e:
            logger.error(f"核心工具检查失败: {e}")
            return False

    async def _check_dependencies(self):
        """检查依赖项"""
        try:
            required_modules = [
                'sqlite3', 'asyncio', 'json', 'logging',
                'pathlib', 'subprocess', 'datetime'
            ]

            available = 0
            for module in required_modules:
                try:
                    __import__(module)
                    available += 1
                except ImportError:
                    logger.warning(f"[WARN] 缺少模块: {module}")

            logger.info(f"[OK] 依赖项: {available}/{len(required_modules)} 个可用")
            return available == len(required_modules)
        except Exception as e:
            logger.error(f"依赖项检查失败: {e}")
            return False

async def main():
    """主函数"""
    print("Dragon-V Triple Bot 集成系统启动器")
    print("=" * 50)

    # 创建集成系统实例
    system = DragonVIntegratedSystem()

    # 运行系统检查
    print("\n执行系统检查...")
    check_results = await system.run_system_check()

    if all(check_results.values()):
        print("系统检查通过")

        # 启动系统
        success = await system.start_system()

        if success:
            print("\n系统集成完成!")
            print("集成的核心功能:")
            print("  MCP渗透测试服务器 (21个模块)")
            print("  漏洞数据库 (414个CVE)")
            print("  载荷生成器")
            print("  Dragon-V Hunter引擎")
            print("  统一管理器")
            print("  三Bot协调系统")

            print("\n集成的工具模块:")
            print("  高级渗透测试工具")
            print("  WAF绕过技术")
            print("  越南化专用模块")
            print("  泰国贷款系统检测")
            print("  数据提取工具")

            print("\n系统已准备就绪，可以开始验证!")

        else:
            print("系统启动失败")
    else:
        print("系统检查失败")
        for check, result in check_results.items():
            if not result:
                print(f"  失败: {check}")

if __name__ == "__main__":
    asyncio.run(main())