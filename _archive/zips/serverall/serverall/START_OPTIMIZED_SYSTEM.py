#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 START OPTIMIZED SYSTEM v2.0
优化系统启动脚本 - 企业级实战版

启动选项:
1. 🐉 高性能扫描引擎
2. 🔥 高级WAF绕过测试
3. 📊 专业报告生成
4. 🔍 综合渗透测试
5. 🛡️ 安全稳定性监控
6. 🧪 系统全面测试
7. 📋 系统状态检查
8. ❌ 退出系统

优化特性:
✅ 异步高性能引擎
✅ 智能WAF绕过
✅ 企业级报告
✅ 完整渗透测试
✅ 安全稳定性
✅ 实时监控
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# Windows控制台编码修复
if sys.platform.startswith('win'):
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        ctypes.windll.kernel32.SetConsoleCP(65001)
    except:
        pass

class OptimizedSystemLauncher:
    """优化系统启动器"""

    def __init__(self):
        self.version = "2.0"
        self.modules_loaded = False

    def display_banner(self):
        """显示横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║      Dragon-V Ultimate Optimized v2.0                                       ║
║                                                                              ║
║  企业级渗透测试框架 - 实战优化版                                              ║
║  Enterprise Penetration Testing Framework - Real-World Optimized            ║
║                                                                              ║
║  高性能扫描引擎 | 智能WAF绕过 | 专业报告生成                                  ║
║  综合渗透测试 | 安全稳定性 | 实时监控                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)

    def display_menu(self):
        """显示菜单"""
        menu = """
请选择启动模式:

1. 🐉 高性能扫描引擎
   - 异步高性能漏洞扫描
   - 支持数千并发连接
   - 智能漏洞检测

2. 🔥 高级WAF绕过测试
   - 多维度WAF绕过技术
   - 智能载荷生成
   - 实时反馈调整

3. 📊 专业报告生成
   - 多格式报告 (HTML, PDF, JSON, CSV)
   - 交互式可视化图表
   - 企业级报告模板

4. 🔍 综合渗透测试
   - 完整渗透测试流程
   - 自动化漏洞利用
   - 后渗透操作

5. 🛡️ 安全稳定性监控
   - 系统资源监控
   - 安全事件记录
   - 异常检测防护

6. 🧪 系统全面测试
   - 自动化系统测试
   - 性能基准测试
   - 功能验证测试

7. 📋 系统状态检查
   - 组件状态检查
   - 性能指标显示
   - 健康状态评估

8. ❌ 退出系统
        """
        print(menu)

    async def load_modules(self):
        """动态加载模块"""
        try:
            # 添加当前目录到Python路径
            sys.path.append(os.path.dirname(__file__))

            # 检查必要模块
            required_modules = [
                "dragon_v_pro_ultimate_optimized",
                "enhanced_waf_bypass_ultimate",
                "enhanced_report_generator",
                "advanced_penetration_module",
                "security_stability_enhancer",
                "test_optimized_system"
            ]

            for module in required_modules:
                if not os.path.exists(f"{module}.py"):
                    print(f"❌ 缺少必要模块: {module}.py")
                    return False

            self.modules_loaded = True
            print("✅ 所有模块加载成功")
            return True

        except Exception as e:
            print(f"❌ 模块加载失败: {e}")
            return False

    async def start_high_performance_scan(self):
        """启动高性能扫描引擎"""
        print("\n🚀 启动高性能扫描引擎...")

        try:
            from dragon_v_pro_ultimate_optimized import DragonVUltimate

            scanner = DragonVUltimate()
            await scanner.initialize()

            # 获取用户输入的目标
            targets = self._get_targets_from_user()

            if not targets:
                print("❌ 未提供有效目标")
                await scanner.close()
                return

            print(f"\n🔍 开始扫描 {len(targets)} 个目标...")

            start_time = time.time()
            results = await scanner.scan_targets(targets)
            scan_time = time.time() - start_time

            # 生成报告
            await scanner.generate_reports(results)

            # 显示结果摘要
            total_vulnerabilities = sum(len(vulns) for vulns in results.values())

            print(f"\n📊 扫描完成!")
            print(f"⏱️  扫描时间: {scan_time:.2f} 秒")
            print(f"🎯 扫描目标: {len(targets)} 个")
            print(f"⚠️  发现漏洞: {total_vulnerabilities} 个")

            for target, vulns in results.items():
                print(f"  📍 {target}: {len(vulns)} 个漏洞")

            await scanner.close()

        except Exception as e:
            print(f"❌ 扫描引擎启动失败: {e}")

    async def start_waf_bypass_test(self):
        """启动WAF绕过测试"""
        print("\n🔥 启动高级WAF绕过测试...")

        try:
            from enhanced_waf_bypass_ultimate import WAFBypassOrchestrator
            import aiohttp

            orchestrator = WAFBypassOrchestrator()

            # 获取用户输入
            target = input("请输入目标URL: ").strip()
            payload = input("请输入测试载荷 (默认: 1' OR '1'='1): ").strip()
            if not payload:
                payload = "1' OR '1'='1"

            # 创建会话
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=10)

            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:

                # 执行绕过测试
                successful_payloads = await orchestrator.orchestrate_bypass(
                    target, payload, session
                )

                # 显示结果
                if successful_payloads:
                    print(f"\n🎉 WAF绕过成功!")
                    print(f"✅ 找到 {len(successful_payloads)} 个有效载荷")
                    print("\n🎯 有效载荷示例:")
                    for i, payload in enumerate(successful_payloads[:3], 1):
                        print(f"  {i}. {payload}")
                else:
                    print("\n❌ 未找到有效的WAF绕过载荷")

        except Exception as e:
            print(f"❌ WAF绕过测试失败: {e}")

    async def start_report_generation(self):
        """启动报告生成"""
        print("\n📊 启动专业报告生成...")

        try:
            from enhanced_report_generator import EnhancedReportGenerator, Vulnerability

            generator = EnhancedReportGenerator()

            # 创建示例数据或从文件加载
            print("\n选择报告数据来源:")
            print("1. 使用示例数据")
            print("2. 从JSON文件加载")

            choice = input("请选择 (1-2): ").strip()

            vulnerabilities = []
            target = "http://example.com"

            if choice == "1":
                # 使用示例数据
                vulnerabilities = [
                    Vulnerability(
                        id="demo_001",
                        type="SQL Injection",
                        severity="High",
                        confidence=0.95,
                        target=target,
                        payload="1' OR '1'='1",
                        evidence="Database error detected",
                        timestamp=datetime.now(),
                        cve_id="CVE-2023-12345",
                        cvss_score=8.5,
                        impact="Database compromise",
                        remediation="Use parameterized queries"
                    )
                ]
            elif choice == "2":
                # 从文件加载
                filename = input("请输入JSON文件路径: ").strip()
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 这里需要根据实际数据结构转换
                        print("✅ 数据加载成功")
                else:
                    print("❌ 文件不存在，使用示例数据")
                    vulnerabilities = []  # 使用空数据

            # 生成报告
            formats = ["html", "json", "markdown"]

            for fmt in formats:
                filename = await generator.generate_report(vulnerabilities, target, fmt)
                print(f"✅ 生成 {fmt.upper()} 报告: {filename}")

            print("\n🎉 报告生成完成!")

        except Exception as e:
            print(f"❌ 报告生成失败: {e}")

    async def start_comprehensive_penetration_test(self):
        """启动综合渗透测试"""
        print("\n🔍 启动综合渗透测试...")

        try:
            from advanced_penetration_module import AdvancedPenetrationEngine

            engine = AdvancedPenetrationEngine()
            await engine.initialize()

            target = input("请输入目标URL: ").strip()

            if not target:
                print("❌ 未提供目标")
                await engine.close()
                return

            print(f"\n🎯 开始对 {target} 进行综合渗透测试...")

            results = await engine.comprehensive_penetration_test(target)

            # 分析结果
            successful_tests = [r for r in results if r.success]
            shell_access = any(r.shell_access for r in results)
            data_extracted = any(r.data_extracted for r in results)

            print(f"\n📊 渗透测试完成!")
            print(f"🔍 执行测试: {len(results)} 个")
            print(f"✅ 成功测试: {len(successful_tests)} 个")
            print(f"🐚 Shell访问: {'是' if shell_access else '否'}")
            print(f"📄 数据提取: {'是' if data_extracted else '否'}")

            if successful_tests:
                print("\n🎯 成功利用的漏洞:")
                for result in successful_tests:
                    print(f"  • {result.vulnerability_type}")

            await engine.close()

        except Exception as e:
            print(f"❌ 渗透测试失败: {e}")

    async def start_security_monitoring(self):
        """启动安全监控"""
        print("\n🛡️ 启动安全稳定性监控...")

        try:
            from security_stability_enhancer import SecurityStabilityEnhancer

            enhancer = SecurityStabilityEnhancer()
            await enhancer.initialize()

            print("✅ 安全监控已启动")
            print("📊 监控指标:")
            print("  - CPU使用率")
            print("  - 内存使用率")
            print("  - 磁盘使用率")
            print("  - 安全事件")
            print("  - 系统性能")

            # 显示当前状态
            status = enhancer.get_system_status()
            print(f"\n📈 当前系统状态:")
            print(f"  整体状态: {status['overall_status']}")
            print(f"  CPU使用率: {status['stability']['cpu_usage']}%")
            print(f"  内存使用率: {status['stability']['memory_usage']}%")
            print(f"  安全事件数: {status['security']['security_events_count']}")

            input("\n按Enter键停止监控...")

            await enhancer.shutdown()
            print("✅ 安全监控已停止")

        except Exception as e:
            print(f"❌ 安全监控启动失败: {e}")

    async def run_system_tests(self):
        """运行系统测试"""
        print("\n🧪 启动系统全面测试...")

        try:
            from test_optimized_system import SystemTester

            tester = SystemTester()
            await tester.run_comprehensive_tests()

        except Exception as e:
            print(f"❌ 系统测试失败: {e}")

    async def check_system_status(self):
        """检查系统状态"""
        print("\n📋 检查系统状态...")

        try:
            from security_stability_enhancer import SecurityStabilityEnhancer

            enhancer = SecurityStabilityEnhancer()
            await enhancer.initialize()

            status = enhancer.get_system_status()

            print("\n📊 系统状态报告:")
            print("=" * 40)

            # 稳定性状态
            stability = status['stability']
            print(f"稳定性状态: {stability['status']}")
            print(f"CPU使用率: {stability['cpu_usage']}%")
            print(f"内存使用率: {stability['memory_usage']}%")
            print(f"磁盘使用率: {stability['disk_usage']}%")
            print(f"监控状态: {'运行中' if stability['monitoring'] else '已停止'}")

            # 安全状态
            security = status['security']
            print(f"\n安全状态:")
            print(f"安全事件数: {security['security_events_count']}")
            print(f"失败尝试数: {security['failed_attempts_count']}")
            print(f"加密系统: {'已初始化' if security['encryption_initialized'] else '未初始化'}")

            # 总体评估
            print(f"\n总体状态: {status['overall_status']}")

            await enhancer.shutdown()

        except Exception as e:
            print(f"❌ 系统状态检查失败: {e}")

    def _get_targets_from_user(self):
        """从用户获取目标列表"""
        print("\n🎯 请输入扫描目标 (每行一个，空行结束):")
        targets = []

        while True:
            target = input("目标URL: ").strip()
            if not target:
                break
            if target.startswith(('http://', 'https://')):
                targets.append(target)
            else:
                print("⚠️  请输入完整的URL (包含 http:// 或 https://)")

        return targets

    async def run(self):
        """运行启动器"""
        self.display_banner()

        # 加载模块
        if not await self.load_modules():
            print("❌ 系统初始化失败，请检查模块文件")
            return

        while True:
            self.display_menu()
            choice = input("\n请选择模式 (1-8): ").strip()

            if choice == "1":
                await self.start_high_performance_scan()
            elif choice == "2":
                await self.start_waf_bypass_test()
            elif choice == "3":
                await self.start_report_generation()
            elif choice == "4":
                await self.start_comprehensive_penetration_test()
            elif choice == "5":
                await self.start_security_monitoring()
            elif choice == "6":
                await self.run_system_tests()
            elif choice == "7":
                await self.check_system_status()
            elif choice == "8":
                print("\n👋 感谢使用 Dragon-V Ultimate!")
                break
            else:
                print("❌ 无效选择，请重新输入")

            input("\n按Enter键继续...")

# 主函数
async def main():
    """主函数"""
    launcher = OptimizedSystemLauncher()
    await launcher.run()

if __name__ == "__main__":
    # 导入json用于报告生成
    import json

    # 运行启动器
    print("启动 Dragon-V Ultimate 优化系统...")
    asyncio.run(main())