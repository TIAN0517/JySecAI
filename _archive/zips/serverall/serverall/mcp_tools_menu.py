#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP工具菜单集成
为Dragon-V Triple Bot提供MCP工具菜单功能
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, List, Optional, Any
from mcp_integration import get_mcp_integration, get_all_mcp_tools, get_mcp_tools_by_category, MCPToolInfo

class MCPToolsMenu:
    """MCP工具菜单管理器"""
    
    def __init__(self):
        self.mcp_integration = get_mcp_integration()
        self.categories = {
            "penetration": "🔍 渗透测试",
            "exploitation": "⚡ 漏洞利用", 
            "security": "🛡️ 安全工具",
            "analysis": "📊 分析工具",
            "general": "🔧 通用工具"
        }
    
    def get_main_menu(self) -> InlineKeyboardMarkup:
        """获取MCP工具主菜单"""
        keyboard = []
        
        # 按分类显示工具
        for category_id, category_name in self.categories.items():
            tools = get_mcp_tools_by_category(category_id)
            if tools:
                keyboard.append([
                    InlineKeyboardButton(
                        f"{category_name} ({len(tools)})", 
                        callback_data=f"mcp_category_{category_id}"
                    )
                ])
        
        # 添加所有工具和返回按钮
        keyboard.append([
            InlineKeyboardButton("📋 所有工具", callback_data="mcp_all_tools"),
            InlineKeyboardButton("📊 工具统计", callback_data="mcp_stats")
        ])
        keyboard.append([
            InlineKeyboardButton("🔙 返回主菜单", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_category_menu(self, category_id: str) -> Optional[InlineKeyboardMarkup]:
        """获取指定分类的工具菜单"""
        tools = get_mcp_tools_by_category(category_id)
        if not tools:
            return None
        
        keyboard = []
        
        # 添加工具按钮
        for tool in tools:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔧 {tool.name}", 
                    callback_data=f"mcp_tool_{tool.id}"
                )
            ])
        
        # 添加返回按钮
        keyboard.append([
            InlineKeyboardButton("🔙 返回MCP菜单", callback_data="mcp_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_all_tools_menu(self) -> InlineKeyboardMarkup:
        """获取所有工具菜单"""
        tools = get_all_mcp_tools()
        if not tools:
            return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回MCP菜单", callback_data="mcp_menu")]])
        
        keyboard = []
        
        # 按分类分组显示工具
        current_category = None
        for tool in tools:
            # 处理category可能是列表的情况，取第一个分类
            category_key = tool.category[0] if isinstance(tool.category, list) else tool.category
            if category_key != current_category:
                current_category = category_key
                category_name = self.categories.get(current_category, "其他工具")
                keyboard.append([
                    InlineKeyboardButton(
                        f"📁 {category_name}", 
                        callback_data=f"mcp_category_{current_category}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton(
                    f"  └ {tool.name}", 
                    callback_data=f"mcp_tool_{tool.id}"
                )
            ])
        
        # 添加返回按钮
        keyboard.append([
            InlineKeyboardButton("🔙 返回MCP菜单", callback_data="mcp_menu")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_tool_categories(self) -> List[str]:
        """获取所有工具分类
        
        Returns:
            List[str]: 分类列表
        """
        return get_mcp_integration().get_tool_categories()
    
    def get_tools_by_category(self, category: str) -> List[MCPToolInfo]:
        """根据分类获取MCP工具
        
        Args:
            category: 工具分类
            
        Returns:
            List[MCPToolInfo]: 工具列表
        """
        return get_mcp_tools_by_category(category)
    
    def get_all_tools(self) -> List[MCPToolInfo]:
        """获取所有MCP工具
        
        Returns:
            List[MCPToolInfo]: 所有工具列表
        """
        return get_all_mcp_tools()
    
    def get_tool_info(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息"""
        tool = self.mcp_integration.get_tool_by_id(tool_id)
        if not tool:
            return None
        
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "author": tool.author,
            "category": tool.category,
            "category_name": self.categories.get(tool.category, "其他"),
            "is_active": tool.is_active
        }
    
    def get_tool_prompt_preview(self, tool_id: str, context: Dict[str, Any] = None) -> Optional[str]:
        """获取工具提示词预览"""
        return self.mcp_integration.generate_prompt(tool_id, context)
    
    def get_stats_message(self) -> str:
        """获取工具统计信息"""
        summary = self.mcp_integration.get_tool_summary()
        
        message = "📊 MCP工具统计\n\n"
        message += f"总工具数: {summary['total_tools']}\n"
        message += f"分类数量: {len(summary['categories'])}\n\n"
        
        message += "📁 分类统计:\n"
        for category, count in summary['tools_by_category'].items():
            category_name = self.categories.get(category, category)
            message += f"  {category_name}: {count}个工具\n"
        
        return message
    
    def get_tool_selection_menu(self, tool_id: str) -> InlineKeyboardMarkup:
        """获取工具选择菜单"""
        keyboard = [
            [
                InlineKeyboardButton("🚀 使用工具", callback_data=f"mcp_use_{tool_id}"),
                InlineKeyboardButton("📋 查看提示词", callback_data=f"mcp_prompt_{tool_id}")
            ],
            [
                InlineKeyboardButton("🔙 返回工具列表", callback_data=f"mcp_category_{self.get_tool_info(tool_id)['category']}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)

# 全局MCP菜单实例
_mcp_menu: Optional[MCPToolsMenu] = None

def get_mcp_menu() -> MCPToolsMenu:
    """获取全局MCP菜单实例"""
    global _mcp_menu
    if _mcp_menu is None:
        _mcp_menu = MCPToolsMenu()
    return _mcp_menu

def initialize_mcp_menu() -> bool:
    """初始化MCP菜单"""
    global _mcp_menu
    try:
        _mcp_menu = MCPToolsMenu()
        return True
    except Exception as e:
        print(f"初始化MCP菜单失败: {e}")
        return False

if __name__ == "__main__":
    # 测试MCP菜单
    if initialize_mcp_menu():
        menu = get_mcp_menu()
        print("=== MCP菜单测试 ===")
        
        # 测试统计信息
        stats = menu.get_stats_message()
        print(stats)
        
        # 测试工具信息
        tool = menu.get_tool_info("penetration_testing")
        if tool:
            print(f"\n=== 工具信息 ===")
            print(f"名称: {tool['name']}")
            print(f"描述: {tool['description']}")
            print(f"分类: {tool['category_name']}")
            print(f"作者: {tool['author']}")
    else:
        print("MCP菜单初始化失败")