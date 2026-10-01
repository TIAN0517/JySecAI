#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus CLI管理界面 - 命令行界面
Nessus CLI Management Interface - Command Line Interface

功能特性:
- 交互式Nessus扫描管理
- 实时状态监控
- 报告生成和查看
- 与现有系统集成
"""

import asyncio
import sys
import argparse
from nessus_manager import nessus_manager
from nessus_config import nessus_config

class NessusCLI:
    """Nessus命令行界面"""
    
    def __init__(self):
        self.manager = nessus_manager
        self.config = nessus_config
    
    async def run_interactive(self):
        """运行交互式CLI"""
        print("🚀 Nessus CLI管理界面")
        print("=" * 50)
        
        while True:
            print("\n请选择操作:")
            print("1. 启动Nessus扫描")
            print("2. 查看扫描历史")
            print("3. 查看漏洞详情")
            print("4. 生成扫描报告")
            print("5. 配置管理")
            print("6. 测试连接")
            print("0. 退出")
            
            choice = input("\n请输入选项编号: ").strip()
            
            if choice == "1":
                await self.start_scan()
            elif choice == "2":
                self.view_scan_history()
            elif choice == "3":
                self.view_vulnerability_details()
            elif choice == "4":
                self.generate_report()
            elif choice == "5":
                self.manage_config()
            elif choice == "6":
                await self.test_connection()
            elif choice == "0":
                print("👋 再见!")
                break
            else:
                print("❌ 无效选项，请重新选择")
    
    async def start_scan(self):
        """启动扫描"""
        print("\n🔍 启动Nessus扫描")
        print("-" * 30)
        
        target = input("请输入扫描目标 (IP/域名): ").strip()
        if not target:
            print("❌ 目标不能为空")
            return
        
        print("\n请选择扫描策略:")
        policies = self.config.config.get('scan_policies', {})
        for i, (key, policy) in enumerate(policies.items(), 1):
            print(f"{i}. {policy['name']} - {policy['description']}")
        
        try:
            policy_choice = int(input("\n请选择策略编号: ").strip())
            policy_keys = list(policies.keys())
            if 1 <= policy_choice <= len(policy_keys):
                policy_name = policy_keys[policy_choice - 1]
            else:
                print("❌ 无效的选项")
                return
        except ValueError:
            print("❌ 请输入有效的数字")
            return
        
        scan_name = input("请输入扫描名称 (可选，回车使用默认名称): ").strip()
        
        print(f"\n📡 开始扫描 {target}...")
        result = await self.manager.schedule_scan(target, policy_name, scan_name)
        
        if result.get("success"):
            print("✅ 扫描启动成功")
            print(f"扫描ID: {result.get('scan_id')}")
            print(f"实际Nessus扫描ID: {result.get('actual_scan_id')}")
        else:
            print(f"❌ 扫描启动失败: {result.get('error')}")
    
    def view_scan_history(self):
        """查看扫描历史"""
        print("\n📊 扫描历史")
        print("-" * 50)
        
        limit = input("显示最近多少条记录? (默认10): ").strip()
        try:
            limit = int(limit) if limit else 10
        except ValueError:
            limit = 10
        
        scans = self.manager.get_scan_history(limit)
        
        if not scans:
            print("📭 没有扫描记录")
            return
        
        for i, scan in enumerate(scans, 1):
            print(f"\n{i}. {scan['scan_name']}")
            print(f"   目标: {scan['target']}")
            print(f"   状态: {scan['status']}")
            print(f"   时间: {scan['start_time']}")
            print(f"   漏洞: 严重({scan['vulnerabilities_critical']}) 高危({scan['vulnerabilities_high']}) 中危({scan['vulnerabilities_medium']}) 低危({scan['vulnerabilities_low']})")
            print(f"   风险评分: {scan['risk_score']}")
    
    def view_vulnerability_details(self):
        """查看漏洞详情"""
        print("\n🔍 查看漏洞详情")
        print("-" * 30)
        
        scan_id = input("请输入扫描ID: ").strip()
        if not scan_id:
            print("❌ 扫描ID不能为空")
            return
        
        vulnerabilities = self.manager.get_vulnerability_details(scan_id)
        
        if not vulnerabilities:
            print("📭 未找到漏洞记录")
            return
        
        print(f"\n📋 发现 {len(vulnerabilities)} 个漏洞:")
        
        for i, vuln in enumerate(vulnerabilities[:10], 1):  # 显示前10个
            severity_str = "严重" if vuln['severity'] >= 4 else "高危" if vuln['severity'] == 3 else "中危" if vuln['severity'] == 2 else "低危"
            print(f"\n{i}. {vuln['plugin_name']} [{severity_str}]")
            print(f"   风险因素: {vuln['risk_factor']}")
            print(f"   CVSS评分: {vuln['cvss_score']}")
            print(f"   端口/协议: {vuln['port']}/{vuln['protocol']}")
            print(f"   描述: {vuln['description'][:100]}...")
        
        if len(vulnerabilities) > 10:
            print(f"\n... 还有 {len(vulnerabilities) - 10} 个漏洞未显示")
    
    def generate_report(self):
        """生成扫描报告"""
        print("\n📄 生成扫描报告")
        print("-" * 30)
        
        scan_id = input("请输入扫描ID: ").strip()
        if not scan_id:
            print("❌ 扫描ID不能为空")
            return
        
        print("\n请选择报告格式:")
        print("1. HTML报告")
        print("2. 文本报告")
        
        format_choice = input("请选择格式 (默认1): ").strip()
        format_type = "html" if format_choice != "2" else "text"
        
        print(f"\n📋 生成{format_type.upper()}报告...")
        report_file = self.manager.generate_scan_report(scan_id, format_type)
        
        if report_file:
            print(f"✅ 报告已生成: {report_file}")
        else:
            print("❌ 报告生成失败")
    
    def manage_config(self):
        """配置管理"""
        print("\n⚙️ 配置管理")
        print("-" * 30)
        
        while True:
            print("\n配置选项:")
            print("1. 查看当前配置")
            print("2. 验证配置")
            print("3. 导出配置")
            print("4. 导入配置")
            print("0. 返回")
            
            choice = input("\n请选择选项: ").strip()
            
            if choice == "1":
                self.view_config()
            elif choice == "2":
                self.validate_config()
            elif choice == "3":
                self.export_config()
            elif choice == "4":
                self.import_config()
            elif choice == "0":
                break
            else:
                print("❌ 无效选项")
    
    def view_config(self):
        """查看配置"""
        print("\n📋 当前配置:")
        print("-" * 30)
        
        servers = self.config.config.get('nessus_servers', {})
        print("\n服务器配置:")
        for name, server in servers.items():
            print(f"  {name}: {server.get('host')}:{server.get('port')} {'✅ 启用' if server.get('enabled') else '❌ 禁用'}")
        
        policies = self.config.config.get('scan_policies', {})
        print("\n扫描策略:")
        for name, policy in policies.items():
            print(f"  {name}: {policy.get('name')}")
    
    def validate_config(self):
        """验证配置"""
        print("\n🔍 验证配置...")
        validation = self.config.validate_config()
        
        if validation['valid']:
            print("✅ 配置有效")
        else:
            print("❌ 配置无效")
        
        if validation['errors']:
            print("\n错误:")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print("\n警告:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
    
    def export_config(self):
        """导出配置"""
        filename = input("请输入导出文件名 (可选): ").strip()
        export_file = self.config.export_config(filename)
        if export_file:
            print(f"✅ 配置已导出到: {export_file}")
        else:
            print("❌ 导出失败")
    
    def import_config(self):
        """导入配置"""
        filename = input("请输入要导入的配置文件名: ").strip()
        if not filename:
            print("❌ 文件名不能为空")
            return
        
        if self.config.import_config(filename):
            print("✅ 配置导入成功")
        else:
            print("❌ 配置导入失败")
    
    async def test_connection(self):
        """测试连接"""
        print("\n🔌 测试Nessus连接...")
        
        from nessus_integration import nessus_integrations
        
        for server_name, server in nessus_integrations.items():
            print(f"\n测试服务器: {server_name}")
            try:
                if await server.authenticate():
                    print("  ✅ 认证成功")
                    
                    # 测试获取模板
                    templates = await server.get_scan_templates()
                    if templates:
                        print(f"  ✅ 获取到 {len(templates)} 个扫描模板")
                    else:
                        print("  ⚠️  无法获取扫描模板")
                else:
                    print("  ❌ 认证失败")
            except Exception as e:
                print(f"  ❌ 连接错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Nessus CLI管理界面')
    parser.add_argument('--target', help='扫描目标')
    parser.add_argument('--policy', default='web_application', help='扫描策略')
    parser.add_argument('--scan-name', help='扫描名称')
    parser.add_argument('--list-history', action='store_true', help='显示扫描历史')
    parser.add_argument('--generate-report', help='为指定扫描ID生成报告')
    parser.add_argument('--format', default='html', choices=['html', 'text'], help='报告格式')
    
    args = parser.parse_args()
    
    cli = NessusCLI()
    
    if args.target:
        # 命令行模式
        asyncio.run(cli.manager.schedule_scan(args.target, args.policy, args.scan_name))
    elif args.list_history:
        # 显示历史
        cli.view_scan_history()
    elif args.generate_report:
        # 生成报告
        report_file = cli.manager.generate_scan_report(args.generate_report, args.format)
        if report_file:
            print(f"报告已生成: {report_file}")
        else:
            print("报告生成失败")
    else:
        # 交互模式
        asyncio.run(cli.run_interactive())

if __name__ == "__main__":
    main()