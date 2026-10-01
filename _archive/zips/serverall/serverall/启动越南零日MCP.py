#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南零日漏洞挖掘MCP服务器启动器
Vietnam Zero-Day Vulnerability Discovery MCP Server Launcher

一键启动越南零日漏洞挖掘系统
演示所有功能模块
"""

import asyncio
import json
import sys
import os
from datetime import datetime
import logging

# 导入我们的模块
from vietnam_zero_day_mcp_integration import VietnamZeroDayMCPIntegration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_mcp_launcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vietnam_mcp_launcher")

class VietnamZeroDayMCPLauncher:
    """越南零日MCP启动器"""

    def __init__(self):
        self.integration = None

    async def start(self):
        """启动MCP服务器"""
        print("🇻🇳 越南零日漏洞挖掘MCP服务器")
        print("🐉 Dragon-V Security Team 出品")
        print("🎯 专门针对越南快递、物流、电商、订单系统")
        print("=" * 60)

        # 初始化集成系统
        self.integration = VietnamZeroDayMCPIntegration()
        await self.integration.initialize()

        print("✅ 越南零日MCP系统初始化完成!")
        print("📝 可用的MCP工具:")

        tools = [
            "vietnam_identify_target - 识别越南目标系统",
            "vietnam_comprehensive_scan - 综合漏洞扫描",
            "vietnam_generate_payload - 生成专用载荷",
            "vietnam_generate_exploitation_chain - 生成利用链",
            "vietnam_get_scan_report - 获取扫描报告",
            "vietnam_list_supported_systems - 列出支持系统"
        ]

        for tool in tools:
            print(f"   🔧 {tool}")

        return self.integration

    async def demo_scan(self):
        """演示扫描功能"""
        print("\n" + "="*60)
        print("🎬 功能演示")
        print("="*60)

        # 测试目标列表
        demo_targets = [
            {"url": "https://shopee.vn", "name": "Shopee Vietnam", "type": "ecommerce"},
            {"url": "https://vnpost.vn", "name": "VNPost", "type": "express_delivery"},
            {"url": "https://momo.vn", "name": "MoMo Wallet", "type": "payment"}
        ]

        for target in demo_targets:
            print(f"\n🔍 演示目标: {target['name']} ({target['url']})")

            try:
                # 1. 目标识别
                print("   📡 步骤1: 识别目标系统...")
                identify_result = await self.integration.mcp_vietnam_identify_target(target['url'])
                result_data = json.loads(identify_result)

                if result_data.get('success'):
                    system_info = result_data['system_info']
                    print(f"   ✅ 识别成功: {system_info['name']}")
                    print(f"   📊 类别: {system_info['category']}")
                    print(f"   🎯 置信度: {system_info['confidence']}")
                    print(f"   🇻🇳 越南特色: {'是' if system_info['vietnam_specific'] else '否'}")
                else:
                    print(f"   ❌ 识别失败: {result_data.get('error', '未知错误')}")
                    continue

                # 2. 生成载荷
                print("   🔧 步骤2: 生成攻击载荷...")
                payload_result = await self.integration.mcp_vietnam_generate_payload(
                    target['type'],
                    "sql_injection",
                    f"针对{target['name']}"
                )
                payload_data = json.loads(payload_result)

                if payload_data.get('success'):
                    payloads = payload_data['vietnam_specific_payloads']
                    print(f"   ✅ 生成了 {len(payloads)} 个专用载荷")
                    for i, payload in enumerate(payloads[:2]):  # 显示前2个
                        print(f"      • {payload['description']}: {payload['payload'][:50]}...")

                # 3. 生成利用链
                print("   ⛓️ 步骤3: 生成漏洞利用链...")
                chain_result = await self.integration.mcp_vietnam_generate_exploitation_chain({
                    "system_name": system_info['name'],
                    "system_type": system_info['category'],
                    "url": target['url']
                })
                chain_data = json.loads(chain_result)

                if chain_data.get('success'):
                    chains = chain_data['exploitation_chains']
                    print(f"   ✅ 生成了 {len(chains)} 个利用链")
                    for chain in chains[:1]:  # 显示第1个
                        print(f"      • {chain['chain_name']}: {len(chain['steps'])} 个步骤")

                print(f"   🎯 {target['name']} 演示完成!")

            except Exception as e:
                print(f"   ❌ 演示失败: {e}")
                continue

        # 4. 显示支持系统
        print(f"\n📋 步骤4: 列出所有支持的越南系统...")
        systems_result = await self.integration.mcp_vietnam_list_supported_systems()
        systems_data = json.loads(systems_result)

        if systems_data.get('success'):
            print(f"   ✅ 总共支持 {systems_data['total_supported']} 个越南系统:")
            for category, systems in systems_data['categories'].items():
                print(f"      📂 {category}: {systems}")

    async def interactive_mode(self):
        """交互模式"""
        print("\n" + "="*60)
        print("🎮 交互模式")
        print("="*60)
        print("输入 'help' 查看可用命令")
        print("输入 'exit' 退出程序")

        while True:
            try:
                command = input("\n🔧 请输入命令: ").strip().lower()

                if command == 'exit' or command == 'quit':
                    print("👋 再见!")
                    break
                elif command == 'help':
                    self.show_help()
                elif command.startswith('scan '):
                    url = command[5:].strip()
                    if url:
                        await self.interactive_scan(url)
                    else:
                        print("❌ 请提供URL: scan <url>")
                elif command.startswith('identify '):
                    url = command[9:].strip()
                    if url:
                        await self.interactive_identify(url)
                    else:
                        print("❌ 请提供URL: identify <url>")
                elif command == 'systems':
                    await self.interactive_list_systems()
                elif command == 'payload':
                    await self.interactive_generate_payload()
                elif command == 'demo':
                    await self.demo_scan()
                else:
                    print("❌ 未知命令，输入 'help' 查看帮助")

            except KeyboardInterrupt:
                print("\n👋 程序被中断")
                break
            except Exception as e:
                print(f"❌ 命令执行失败: {e}")

    def show_help(self):
        """显示帮助信息"""
        help_text = """
🔧 可用命令:
  help                           - 显示此帮助信息
  demo                          - 运行功能演示
  scan <url>                    - 综合扫描目标
  identify <url>                - 识别目标系统
  systems                       - 列出支持的系统
  payload                       - 生成攻击载荷
  exit/quit                     - 退出程序

示例:
  scan https://shopee.vn
  identify https://vnpost.vn
  systems
        """
        print(help_text)

    async def interactive_scan(self, url: str):
        """交互式扫描"""
        print(f"\n🔍 开始扫描: {url}")

        scan_types = ["full", "zero_day", "business_logic"]
        print("请选择扫描类型:")
        for i, scan_type in enumerate(scan_types, 1):
            print(f"  {i}. {scan_type}")

        try:
            choice = input("请输入选择 (1-3): ").strip()
            if choice in ['1', '2', '3']:
                scan_type = scan_types[int(choice) - 1]
                print(f"🚀 开始 {scan_type} 扫描...")

                result = await self.integration.mcp_vietnam_comprehensive_scan(url, scan_type)
                result_data = json.loads(result)

                if result_data.get('success'):
                    scan_results = result_data['scan_results']
                    print(f"✅ 扫描完成!")
                    print(f"   📊 总漏洞数: {scan_results['total_vulnerabilities']}")
                    print(f"   🚨 严重漏洞: {scan_results['critical_count']}")
                    print(f"   ⚠️ 高危漏洞: {scan_results['high_count']}")
                    print(f"   🆔 扫描ID: {scan_results['scan_id']}")

                    # 显示漏洞详情
                    for vuln in scan_results['vulnerabilities'][:3]:
                        print(f"   • {vuln['category']}: {vuln['description']}")
                else:
                    print(f"❌ 扫描失败: {result_data.get('error')}")
            else:
                print("❌ 无效选择")
        except Exception as e:
            print(f"❌ 扫描过程出错: {e}")

    async def interactive_identify(self, url: str):
        """交互式识别"""
        print(f"\n🔍 识别目标: {url}")

        result = await self.integration.mcp_vietnam_identify_target(url)
        result_data = json.loads(result)

        if result_data.get('success'):
            system_info = result_data['system_info']
            print(f"✅ 识别成功!")
            print(f"   🏷️ 系统名称: {system_info['name']}")
            print(f"   📂 系统类别: {system_info['category']}")
            print(f"   🎯 置信度: {system_info['confidence']}")
            print(f"   🇻🇳 越南特色: {'是' if system_info['vietnam_specific'] else '否'}")
            print(f"   📝 描述: {system_info['description']}")

            recommendations = result_data.get('vulnerability_recommendations', [])
            if recommendations:
                print(f"   🔍 建议测试:")
                for rec in recommendations[:3]:
                    print(f"      • {rec}")
        else:
            print(f"❌ 识别失败: {result_data.get('error')}")

    async def interactive_list_systems(self):
        """交互式列出系统"""
        print("\n📋 支持的越南系统:")

        result = await self.integration.mcp_vietnam_list_supported_systems()
        systems_data = json.loads(result)

        if systems_data.get('success'):
            categories = {}
            for system in systems_data['supported_systems']:
                category = system['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(system)

            for category, systems in categories.items():
                print(f"\n📂 {category.upper()}:")
                for system in systems:
                    vip_status = "🇻🇳" if system['vietnam_specific'] else "🌐"
                    print(f"   {vip_status} {system['name']}")
                    print(f"      {system['description']}")
                    print(f"      常见漏洞: {', '.join(system['common_vulnerabilities'][:2])}")

    async def interactive_generate_payload(self):
        """交互式生成载荷"""
        print("\n🔧 生成攻击载荷")

        # 系统类型
        system_types = ["ecommerce", "express_delivery", "payment", "logistics"]
        print("选择系统类型:")
        for i, stype in enumerate(system_types, 1):
            print(f"  {i}. {stype}")

        try:
            choice = input("请输入选择 (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                system_type = system_types[int(choice) - 1]

                # 漏洞类型
                vuln_types = ["sql_injection", "xss", "price_manipulation", "shipping_bypass", "payment_bypass"]
                print("选择漏洞类型:")
                for i, vtype in enumerate(vuln_types, 1):
                    print(f"  {i}. {vtype}")

                vchoice = input("请输入选择 (1-5): ").strip()
                if vchoice in ['1', '2', '3', '4', '5']:
                    vuln_type = vuln_types[int(vchoice) - 1]

                    print(f"🚀 为 {system_type} 系统生成 {vuln_type} 载荷...")

                    result = await self.integration.mcp_vietnam_generate_payload(
                        system_type,
                        vuln_type,
                        "交互式生成"
                    )

                    result_data = json.loads(result)
                    if result_data.get('success'):
                        payloads = result_data['vietnam_specific_payloads']
                        print(f"✅ 生成了 {len(payloads)} 个载荷:")
                        for payload in payloads:
                            print(f"   • {payload['description']}")
                            if isinstance(payload['payload'], dict):
                                print(f"     {json.dumps(payload['payload'], ensure_ascii=False)}")
                            else:
                                print(f"     {payload['payload']}")
                    else:
                        print(f"❌ 生成失败: {result_data.get('error')}")
                else:
                    print("❌ 无效漏洞类型选择")
            else:
                print("❌ 无效系统类型选择")
        except Exception as e:
            print(f"❌ 生成过程出错: {e}")

    async def cleanup(self):
        """清理资源"""
        if self.integration:
            await self.integration.cleanup()

async def main():
    """主程序"""
    launcher = VietnamZeroDayMCPLauncher()

    try:
        # 启动系统
        integration = await launcher.start()

        # 询问用户模式
        print("\n" + "="*60)
        print("🎯 请选择运行模式:")
        print("1. 演示模式 - 自动演示所有功能")
        print("2. 交互模式 - 手动操作各个功能")
        print("3. 退出程序")
        print("="*60)

        choice = input("请输入选择 (1-3): ").strip()

        if choice == '1':
            await launcher.demo_scan()
        elif choice == '2':
            await launcher.interactive_mode()
        elif choice == '3':
            print("👋 再见!")
        else:
            print("❌ 无效选择，启动交互模式")
            await launcher.interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"❌ 程序运行出错: {e}")
    finally:
        await launcher.cleanup()

if __name__ == "__main__":
    print("🚀 启动越南零日漏洞挖掘MCP服务器...")
    asyncio.run(main())