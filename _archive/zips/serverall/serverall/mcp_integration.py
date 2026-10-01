#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP工具集成模块
集成所有MCP配置文件，提供统一的MCP工具管理

支持的MCP工具:
- 渗透测试专用MCP
- SQLMap优化器
- 漏洞利用助手
- CVE PoC专家
- 认证绕过技术
- 命令注入攻击
- 高级越狱技术
- 间接提示注入
- 工具投毒检测
- 拉地毯攻击检测
- 凭证窃取技术
- 漏洞审查
- MCP信息收集
- 代码信息收集
- 硬编码API密钥检测
- 名称混淆攻击
- 工具影子攻击
- HTC POST SQL注入
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MCPToolInfo:
    """MCP工具信息"""
    id: str
    name: str
    description: str
    author: str
    category: str
    prompt_template: str
    file_path: str
    is_active: bool = True

class MCPIntegration:
    """MCP工具集成管理器"""
    
    def __init__(self, mcp_dir: str = "mcp"):
        """
        初始化MCP集成管理器
        
        Args:
            mcp_dir: MCP配置文件目录路径
        """
        self.mcp_dir = Path(mcp_dir)
        self.tools: Dict[str, MCPToolInfo] = {}
        self.load_mcp_tools()
    
    def load_mcp_tools(self) -> bool:
        """
        加载所有MCP工具配置
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if not self.mcp_dir.exists():
                logger.error(f"MCP目录不存在: {self.mcp_dir}")
                return False
            
            # 遍历MCP目录下的所有YAML文件
            yaml_files = list(self.mcp_dir.glob("*.yaml"))
            logger.info(f"找到 {len(yaml_files)} 个MCP配置文件")
            
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    # 验证配置文件结构
                    if not self._validate_mcp_config(config):
                        logger.warning(f"配置文件格式无效: {yaml_file.name}")
                        continue
                    
                    # 创建工具信息
                    tool_info = MCPToolInfo(
                        id=config['info']['id'],
                        name=config['info']['name'],
                        description=config['info']['description'],
                        author=config['info']['author'],
                        category=config['info'].get('category', 'general'),
                        prompt_template=config['prompt_template'],
                        file_path=str(yaml_file)
                    )
                    
                    self.tools[tool_info.id] = tool_info
                    logger.info(f"加载MCP工具: {tool_info.name} ({tool_info.id})")
                    
                except Exception as e:
                    logger.error(f"加载MCP配置文件失败 {yaml_file.name}: {e}")
                    continue
            
            logger.info(f"成功加载 {len(self.tools)} 个MCP工具")
            return True
            
        except Exception as e:
            logger.error(f"加载MCP工具失败: {e}")
            return False
    
    def _validate_mcp_config(self, config: Dict) -> bool:
        """
        验证MCP配置文件结构
        
        Args:
            config: 配置文件内容
            
        Returns:
            bool: 是否有效
        """
        required_fields = ['info', 'prompt_template']
        info_required = ['id', 'name', 'description', 'author']
        
        # 检查必需字段
        for field in required_fields:
            if field not in config:
                return False
        
        # 检查info字段
        for field in info_required:
            if field not in config['info']:
                return False
        
        return True
    
    def get_tool_by_id(self, tool_id: str) -> Optional[MCPToolInfo]:
        """
        根据ID获取MCP工具
        
        Args:
            tool_id: 工具ID
            
        Returns:
            Optional[MCPToolInfo]: 工具信息，如果不存在返回None
        """
        return self.tools.get(tool_id)
    
    def get_tools_by_category(self, category: str) -> List[MCPToolInfo]:
        """
        根据分类获取MCP工具
        
        Args:
            category: 工具分类
            
        Returns:
            List[MCPToolInfo]: 工具列表
        """
        return [tool for tool in self.tools.values() if tool.category == category]
    
    def get_all_tools(self) -> List[MCPToolInfo]:
        """
        获取所有MCP工具
        
        Returns:
            List[MCPToolInfo]: 所有工具列表
        """
        return list(self.tools.values())
    
    def get_tool_categories(self) -> List[str]:
        """
        获取所有工具分类
        
        Returns:
            List[str]: 分类列表
        """
        categories = set()
        for tool in self.tools.values():
            # 处理category可能是列表的情况
            if isinstance(tool.category, list):
                for cat in tool.category:
                    categories.add(cat)
            else:
                categories.add(tool.category)
        return list(categories)
    
    def generate_prompt(self, tool_id: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        生成MCP工具的提示词
        
        Args:
            tool_id: 工具ID
            context: 上下文参数
            
        Returns:
            Optional[str]: 生成的提示词，如果工具不存在返回None
        """
        tool = self.get_tool_by_id(tool_id)
        if not tool:
            return None
        
        prompt = tool.prompt_template
        
        # 替换上下文变量
        if context:
            for key, value in context.items():
                placeholder = f"{{{{ .{key} }}}}"
                prompt = prompt.replace(placeholder, str(value))
        
        return prompt
    
    def get_tool_summary(self) -> Dict[str, Any]:
        """
        获取工具摘要信息
        
        Returns:
            Dict[str, Any]: 工具摘要
        """
        return {
            "total_tools": len(self.tools),
            "categories": self.get_tool_categories(),
            "tools_by_category": {
                category: len(self.get_tools_by_category(category))
                for category in self.get_tool_categories()
            },
            "active_tools": [tool.id for tool in self.tools.values() if tool.is_active]
        }
    
    def reload_tools(self) -> bool:
        """
        重新加载MCP工具
        
        Returns:
            bool: 是否成功
        """
        self.tools.clear()
        return self.load_mcp_tools()

# 全局MCP集成实例
_mcp_integration: Optional[MCPIntegration] = None

def get_mcp_integration() -> MCPIntegration:
    """
    获取全局MCP集成实例
    
    Returns:
        MCPIntegration: MCP集成实例
    """
    global _mcp_integration
    if _mcp_integration is None:
        _mcp_integration = MCPIntegration()
    return _mcp_integration

def initialize_mcp_integration() -> bool:
    """
    初始化MCP集成
    
    Returns:
        bool: 是否成功
    """
    global _mcp_integration
    try:
        _mcp_integration = MCPIntegration()
        return True
    except Exception as e:
        logger.error(f"初始化MCP集成失败: {e}")
        return False

# 便捷函数
def get_mcp_tool(tool_id: str) -> Optional[MCPToolInfo]:
    """获取指定MCP工具"""
    return get_mcp_integration().get_tool_by_id(tool_id)

def get_all_mcp_tools() -> List[MCPToolInfo]:
    """获取所有MCP工具"""
    return get_mcp_integration().get_all_tools()

def get_mcp_tools_by_category(category: str) -> List[MCPToolInfo]:
    """根据分类获取MCP工具"""
    return get_mcp_integration().get_tools_by_category(category)

def generate_mcp_prompt(tool_id: str, context: Dict[str, Any] = None) -> Optional[str]:
    """生成MCP提示词"""
    return get_mcp_integration().generate_prompt(tool_id, context)

def get_mcp_summary() -> Dict[str, Any]:
    """获取MCP工具摘要"""
    return get_mcp_integration().get_tool_summary()

if __name__ == "__main__":
    # 测试MCP集成
    if initialize_mcp_integration():
        summary = get_mcp_summary()
        print("=== MCP工具集成测试 ===")
        print(f"总工具数: {summary['total_tools']}")
        print(f"分类: {summary['categories']}")
        print(f"按分类统计: {summary['tools_by_category']}")
        
        # 测试生成提示词
        penetration_tool = get_mcp_tool("penetration_testing")
        if penetration_tool:
            context = {
                "TargetURL": "http://example.com",
                "TestType": "SQL注入",
                "Vulnerabilities": "SQL注入漏洞"
            }
            prompt = generate_mcp_prompt("penetration_testing", context)
            print(f"\n=== 渗透测试提示词示例 ===")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    else:
        print("MCP集成初始化失败")