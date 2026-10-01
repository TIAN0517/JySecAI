#!/usr/bin/env python3
"""
Dragon-V Triple Bot 基础使用示例
展示如何使用核心功能进行安全扫描
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

# 导入核心模块
try:
    from dragon_triple_bot_unified_manager import DragonTripleBotUnifiedManager
    from dragon_triple_bot_functional_module import DragonTripleBotFunctionalModule
    from security_stability_enhancer import SecurityStabilityEnhancer
    from enhanced_waf_bypass_ultimate import EnhancedWAFBypassUltimate
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装所有依赖")
    exit(1)


class DragonVExample:
    """Dragon-V 使用示例类"""

    def __init__(self):
        self.manager = DragonTripleBotUnifiedManager()
        self.functional_module = DragonTripleBotFunctionalModule()
        self.scanner = SecurityStabilityEnhancer()
        self.waf_bypass = EnhancedWAFBypassUltimate()

    def example_1_basic_scan(self) -> Dict[str, Any]:
        """示例1: 基础扫描"""
        print("\n" + "="*50)
        print("示例1: 基础安全扫描")
        print("="*50)

        target = "https://example.com"

        # 执行SQL注入扫描
        print("🔍 执行SQL注入扫描...")
        sqli_results = self.scanner.scan_sql_injection(target)

        # 执行XSS扫描
        print("🔍 执行XSS扫描...")
        xss_results = self.scanner.scan_xss(target)

        # 合并结果
        all_vulnerabilities = sqli_results + xss_results

        return {
            "target": target,
            "total_vulnerabilities": len(all_vulnerabilities),
            "sqli_vulnerabilities": len(sqli_results),
            "xss_vulnerabilities": len(xss_results),
            "vulnerabilities": all_vulnerabilities
        }

    def example_2_waf_bypass(self) -> Dict[str, Any]:
        """示例2: WAF绕过"""
        print("\n" + "="*50)
        print("示例2: WAF绕过技术")
        print("="*50)

        original_payload = "' OR '1'='1"
        waf_type = "cloudflare"

        # 生成绕过payload
        print(f"🎯 生成 {waf_type} WAF绕过payload...")
        bypass_payloads = self.waf_bypass.generate_bypass_payloads(
            original_payload=original_payload,
            waf_type=waf_type
        )

        # 测试绕过效果
        print("🧪 测试绕过效果...")
        test_results = []
        for i, payload in enumerate(bypass_payloads[:3]):  # 测试前3个
            result = self.waf_bypass.test_payload_effectiveness(payload)
            test_results.append({
                "payload": payload,
                "effectiveness": result
            })

        return {
            "original_payload": original_payload,
            "waf_type": waf_type,
            "bypass_payloads_generated": len(bypass_payloads),
            "test_results": test_results
        }

    def example_3_task_management(self) -> Dict[str, Any]:
        """示例3: 任务管理"""
        print("\n" + "="*50)
        print("示例3: 任务管理系统")
        print("="*50)

        # 创建扫描任务
        print("📝 创建扫描任务...")
        task_id = self.manager.create_task(
            task_type="web_scan",
            target="https://testphp.vulnweb.com",
            scan_types=["sqli", "xss", "idor"]
        )

        print(f"✅ 任务创建成功: {task_id}")

        # 模拟任务执行
        print("⏳ 模拟任务执行中...")
        time.sleep(2)

        # 获取任务状态
        task_status = self.manager.get_task_status(task_id)

        return {
            "task_id": task_id,
            "task_status": task_status,
            "created_at": datetime.now().isoformat()
        }

    def example_4_functional_module(self) -> Dict[str, Any]:
        """示例4: 功能模块使用"""
        print("\n" + "="*50)
        print("示例4: 功能模块")
        print("="*50)

        # 企业级管理功能
        print("🏢 执行企业级管理...")
        enterprise_result = self.functional_module.enterprise_management(
            command="system_status",
            action="get_status"
        )

        # 专业扫描功能
        print("🔧 执行专业扫描...")
        professional_result = self.functional_module.professional_scanning(
            target="https://example.com",
            scan_type="quick"
        )

        return {
            "enterprise_management": enterprise_result,
            "professional_scanning": professional_result
        }

    async def example_5_async_operations(self) -> Dict[str, Any]:
        """示例5: 异步操作"""
        print("\n" + "="*50)
        print("示例5: 异步操作")
        print("="*50)

        # 模拟异步扫描多个目标
        targets = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]

        print(f"🚀 异步扫描 {len(targets)} 个目标...")

        async def scan_target(target: str) -> Dict[str, Any]:
            """异步扫描单个目标"""
            # 模拟扫描时间
            await asyncio.sleep(1)
            return {
                "target": target,
                "status": "completed",
                "vulnerabilities_found": 2,  # 模拟结果
                "scan_time": 1.0
            }

        # 并发执行所有扫描
        tasks = [scan_target(target) for target in targets]
        results = await asyncio.gather(*tasks)

        return {
            "total_targets": len(targets),
            "scan_results": results,
            "total_time": len(targets)  # 由于并发，总时间约等于单个扫描时间
        }

    def run_all_examples(self):
        """运行所有示例"""
        print("🐉 Dragon-V Triple Bot 使用示例")
        print("开始运行所有示例...\n")

        all_results = {}

        try:
            # 示例1: 基础扫描
            all_results["basic_scan"] = self.example_1_basic_scan()

            # 示例2: WAF绕过
            all_results["waf_bypass"] = self.example_2_waf_bypass()

            # 示例3: 任务管理
            all_results["task_management"] = self.example_3_task_management()

            # 示例4: 功能模块
            all_results["functional_module"] = self.example_4_functional_module()

            # 示例5: 异步操作
            all_results["async_operations"] = asyncio.run(self.example_5_async_operations())

        except Exception as e:
            print(f"❌ 示例执行错误: {e}")
            return None

        print("\n" + "="*50)
        print("🎉 所有示例执行完成!")
        print("="*50)

        # 汇总结果
        total_vulnerabilities = all_results["basic_scan"]["total_vulnerabilities"]
        total_tasks = 1  # 示例3创建了1个任务
        total_async_scans = all_results["async_operations"]["total_targets"]

        print(f"\n📊 执行汇总:")
        print(f"   发现漏洞: {total_vulnerabilities} 个")
        print(f"   创建任务: {total_tasks} 个")
        print(f"   异步扫描: {total_async_scans} 个目标")
        print(f"   WAF绕过: {all_results['waf_bypass']['bypass_payloads_generated']} 种技术")

        return all_results


def main():
    """主函数"""
    example = DragonVExample()
    results = example.run_all_examples()

    if results:
        print("\n✅ 示例程序运行成功!")
        print("💡 查看 docs/ 目录获取完整API文档")
    else:
        print("\n❌ 示例程序运行失败!")
        print("🔧 请检查依赖安装和配置")


if __name__ == "__main__":
    main()