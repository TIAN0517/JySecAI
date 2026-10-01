#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
漏洞分析脚本 - 使用MCP工具分析零时差验证结果
"""

import sys
import json
from mcp_integration import generate_mcp_prompt, get_mcp_integration

def analyze_sql_injection():
    """分析SQL注入漏洞"""
    print("\n" + "="*80)
    print("🔍 分析 peacoop.or.th 的SQL注入漏洞")
    print("="*80)
    
    context = {
        'TargetURL': 'https://peacoop.or.th',
        'VulnerabilityType': 'SQL注入',
        'TestScope': '深度利用',
        'DatabaseType': 'MySQL/PostgreSQL',
        'InjectionPoints': 'GET/POST参数',
        'WAFPresent': '已绕过(泰语载荷)',
        'PayloadType': '布尔盲注/时间盲注'
    }
    
    # 使用SQLMap优化器
    prompt = generate_mcp_prompt('sqlmap_optimizer', context)
    if prompt:
        print("\n=== SQL注入利用方案 ===")
        print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
    else:
        print("❌ 无法生成SQL注入提示词")
    
    # 使用漏洞利用助手
    exploit_prompt = generate_mcp_prompt('vulnerability_exploitation', context)
    if exploit_prompt:
        print("\n=== 漏洞利用策略 ===")
        print(exploit_prompt[:1500] + "..." if len(exploit_prompt) > 1500 else exploit_prompt)

def analyze_xss_vulnerability():
    """分析XSS漏洞"""
    print("\n" + "="*80)
    print("🔍 分析 mula-x.com 的XSS漏洞")
    print("="*80)
    
    context = {
        'TargetURL': 'https://mula-x.com',
        'VulnerabilityType': 'XSS跨站脚本',
        'TestScope': '多端点测试',
        'XSSType': '反射型/存储型',
        'WAFBypass': '泰语载荷绕过成功',
        'AttackVectors': '表单输入/URL参数'
    }
    
    # 使用渗透测试工具
    prompt = generate_mcp_prompt('penetration_testing', context)
    if prompt:
        print("\n=== XSS漏洞利用方案 ===")
        print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
    else:
        print("❌ 无法生成XSS漏洞分析")

def analyze_data_leakage():
    """分析数据泄露漏洞"""
    print("\n" + "="*80)
    print("🔍 分析 ngoenmun.com 的数据泄露漏洞")
    print("="*80)
    
    context = {
        'TargetURL': 'https://ngoenmun.com',
        'VulnerabilityType': '数据泄露',
        'LeakedData': '敏感数据 (29,817字节)',
        'Endpoint': '/admin/data',
        'DataSize': '29,817字节',
        'SecurityLevel': '高危'
    }
    
    # 使用信息收集工具
    prompt = generate_mcp_prompt('mcp_info_collection', context)
    if prompt:
        print("\n=== 数据泄露分析方案 ===")
        print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
    else:
        print("❌ 无法生成数据泄露分析")
    
    # 使用代码信息收集工具
    code_prompt = generate_mcp_prompt('code_info_collection', context)
    if code_prompt:
        print("\n=== 代码安全分析 ===")
        print(code_prompt[:1500] + "..." if len(code_prompt) > 1500 else code_prompt)

def generate_comprehensive_report():
    """生成综合渗透测试报告"""
    print("\n" + "="*80)
    print("📊 综合渗透测试报告")
    print("="*80)
    
    context = {
        'Targets': [
            {
                'url': 'https://peacoop.or.th',
                'vulnerability': 'SQL注入',
                'severity': '高危',
                'status': '已验证'
            },
            {
                'url': 'https://mula-x.com', 
                'vulnerability': 'XSS跨站脚本',
                'severity': '中危',
                'status': '已验证'
            },
            {
                'url': 'https://ngoenmun.com',
                'vulnerability': '数据泄露',
                'severity': '高危',
                'status': '已验证'
            }
        ],
        'OverallRisk': '高危',
        'Recommendations': '立即修复',
        'ReportType': '专业渗透测试'
    }
    
    # 使用漏洞审查工具
    prompt = generate_mcp_prompt('vuln_review', context)
    if prompt:
        print("\n=== 综合安全评估 ===")
        print(prompt[:2500] + "..." if len(prompt) > 2500 else prompt)
    else:
        print("❌ 无法生成综合报告")

def main():
    """主函数"""
    print("🐉 Dragon-V MCP漏洞分析工具")
    print("="*80)
    
    # 初始化MCP集成
    mcp = get_mcp_integration()
    summary = mcp.get_tool_summary()
    print(f"📊 可用MCP工具: {summary['total_tools']} 个")
    print(f"📁 分类: {', '.join(summary['categories'])}")
    
    # 执行分析
    analyze_sql_injection()
    analyze_xss_vulnerability()
    analyze_data_leakage()
    generate_comprehensive_report()
    
    print("\n" + "="*80)
    print("✅ 漏洞分析完成")
    print("="*80)

if __name__ == "__main__":
    main()