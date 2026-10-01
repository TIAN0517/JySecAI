#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V MCP集成启动脚本
演示如何通过Bot使用MCP工具
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_mcp_tools():
    """显示MCP工具信息"""
    print("🐉 Dragon-V MCP工具集成")
    print("=" * 50)
    
    try:
        from mcp_integration import get_mcp_summary
        from mcp_tools_menu import get_mcp_menu
        
        # 获取MCP工具摘要
        summary = get_mcp_summary()
        
        print(f"📊 MCP工具统计:")
        print(f"   总工具数: {summary['total_tools']}")
        print(f"   分类数量: {len(summary['categories'])}")
        
        print("\n📁 分类统计:")
        for category, count in summary['tools_by_category'].items():
            category_name = category if category else "未分类"
            print(f"   {category_name}: {count} 个工具")
        
        # 获取MCP菜单
        menu = get_mcp_menu()
        
        print("\n🧠 可用工具:")
        all_tools = menu.get_all_tools()
        for tool in all_tools:
            category = tool.category if tool.category else "未分类"
            print(f"   🔧 {tool.name} ({category})")
            print(f"      描述: {tool.description}")
        
        print("\n🚀 启动Bot命令:")
        print("   python dragon_triple_telegram_bot.py interactive")
        print("\n💡 使用方法:")
        print("   1. 启动Bot交互模式")
        print("   2. 选择'安全工具'菜单")
        print("   3. 选择'MCP工具集'选项")
        print("   4. 浏览和使用各种MCP工具")
        
    except Exception as e:
        print(f"❌ 显示MCP工具信息失败: {e}")

def main():
    """主函数"""
    show_mcp_tools()
    
    print("\n" + "=" * 50)
    print("🎉 MCP集成已完成！")
    print("\n📋 集成功能:")
    print("  ✅ 20个专业MCP工具")
    print("  ✅ 分类管理 (渗透测试、漏洞利用、安全工具等)")
    print("  ✅ Telegram Bot界面集成")
    print("  ✅ 提示词生成和预览")
    print("  ✅ 工具统计和状态监控")
    
    print("\n🔧 主要工具类别:")
    print("  🔍 渗透测试工具")
    print("  ⚡ 漏洞利用工具")
    print("  🛡️ 安全分析工具")
    print("  🔓 越狱和绕过工具")
    print("  📊 信息收集工具")
    
    print("\n🚀 开始使用:")
    print("   运行 'python dragon_triple_telegram_bot.py interactive' 启动Bot")

if __name__ == "__main__":
    main()