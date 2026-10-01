#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP快速分析工具 - 一键启动漏洞分析
"""

import sys
import os
from mcp_integration import get_mcp_integration, generate_mcp_prompt

def quick_analysis(target_url: str, vulnerability_type: str):
    """快速分析目标漏洞"""
    print(f"🔍 快速分析: {target_url}")
    print(f"漏洞类型: {vulnerability_type}")
    print("="*60)
    
    # 根据漏洞类型选择MCP工具
    tool_mapping = {
        'sql注入': 'sqlmap_optimizer',
        'xss': 'penetration_testing', 
        '数据泄露': 'mcp_info_collection',
        '漏洞利用': 'vulnerability_exploitation',
        '综合评估': 'vuln_review'
    }
    
    tool_id = tool_mapping.get(vulnerability_type.lower(), 'penetration_testing')
    
    context = {
        'TargetURL': target_url,
        'VulnerabilityType': vulnerability_type,
        'TestScope': '快速分析',
        'RiskLevel': '待评估'
    }
    
    prompt = generate_mcp_prompt(tool_id, context)
    if prompt:
        print("📋 MCP分析结果:")
        print("-"*60)
        # 显示前1000字符作为摘要
        summary = prompt[:1000] + "..." if len(prompt) > 1000 else prompt
        print(summary)
        print("-"*60)
        
        # 保存完整报告
        filename = f"mcp_analysis_{target_url.replace('https://', '').replace('/', '_')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"目标URL: {target_url}\n")
            f.write(f"漏洞类型: {vulnerability_type}\n")
            f.write(f"使用工具: {tool_id}\n")
            f.write("="*60 + "\n")
            f.write(prompt)
        
        print(f"📄 完整报告已保存: {filename}")
    else:
        print("❌ 无法生成分析报告")

def show_available_tools():
    """显示可用MCP工具"""
    mcp = get_mcp_integration()
    summary = mcp.get_tool_summary()
    
    print("🧠 可用MCP工具:")
    print(f"总工具数: {summary['total_tools']}")
    print("分类工具统计:")
    
    for category, count in summary['tools_by_category'].items():
        tools = mcp.get_tools_by_category(category)
        print(f"  {category}: {count}个工具")
        for tool in tools[:3]:  # 显示前3个
            print(f"    - {tool.name} ({tool.id})")

def main():
    """主函数"""
    print("🐉 Dragon-V MCP快速分析工具")
    print("="*60)
    
    if len(sys.argv) > 2:
        # 命令行参数模式
        target_url = sys.argv[1]
        vuln_type = sys.argv[2]
        quick_analysis(target_url, vuln_type)
    else:
        # 交互模式
        print("使用方法:")
        print("  快速分析: python MCP_快速分析.py <URL> <漏洞类型>")
        print("  示例: python MCP_快速分析.py https://example.com sql注入")
        print()
        
        show_available_tools()
        print()
        
        # 示例分析
        print("💡 示例分析:")
        examples = [
            ("https://peacoop.or.th", "sql注入"),
            ("https://mula-x.com", "xss"),
            ("https://ngoenmun.com", "数据泄露")
        ]
        
        for url, vuln in examples:
            print(f"  python MCP_快速分析.py {url} {vuln}")

if __name__ == "__main__":
    main()