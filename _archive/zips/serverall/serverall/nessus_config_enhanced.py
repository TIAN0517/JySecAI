#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强Nessus扫描配置文件
Enhanced Nessus Scan Configuration

提供高级扫描配置选项，支持企业级安全扫描需求
"""

from typing import Dict, List, Any
from enum import Enum

class ScanPolicy(Enum):
    """扫描策略枚举"""
    WEB_APPLICATION = "web_application"
    NETWORK = "network"
    MALWARE = "malware"
    MOBILE = "mobile"
    DATABASE = "database"
    CLOUD = "cloud"
    CUSTOM = "custom"

class ScanIntensity(Enum):
    """扫描强度枚举"""
    LIGHT = "light"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"

class ScanConfiguration:
    """扫描配置类"""
    
    def __init__(self):
        self.configs = {
            # Web应用扫描配置
            "web_application": {
                "name": "Web应用安全扫描",
                "description": "针对Web应用程序的全面安全扫描",
                "settings": {
                    "policy": "webapp",
                    "portscan_range": "tcp:80,443,8080,8443,8000,3000,5000",
                    "thorough_tests": True,
                    "safe_checks": False,
                    "report_verbosity": "Normal",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "web", "webapp", "xss", "sql", "rfi", "lfi", 
                            "csrf", "xxe", "ssrf", "cors", "jwt", "api"
                        ]
                    }
                }
            },
            
            # 网络扫描配置
            "network": {
                "name": "网络基础设施扫描",
                "description": "针对网络设备和服务的全面扫描",
                "settings": {
                    "policy": "network",
                    "portscan_range": "default",
                    "thorough_tests": True,
                    "safe_checks": True,
                    "report_verbosity": "Detailed",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "general", "service_detection", "vulnerability",
                            "backdoor", "malware", "dos"
                        ]
                    }
                }
            },
            
            # 恶意软件扫描配置
            "malware": {
                "name": "恶意软件检测扫描",
                "description": "专门检测恶意软件和可疑活动的扫描",
                "settings": {
                    "policy": "malware",
                    "portscan_range": "tcp:21,22,23,25,53,80,110,143,443,993,995,1433,3306,3389,5432,5900",
                    "thorough_tests": True,
                    "safe_checks": True,
                    "report_verbosity": "Detailed",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "malware", "backdoor", "trojan", "virus", 
                            "ransomware", "crypto_miner"
                        ]
                    }
                }
            },
            
            # 移动应用扫描配置
            "mobile": {
                "name": "移动应用安全扫描",
                "description": "针对移动应用和API的安全测试",
                "settings": {
                    "policy": "mobile",
                    "portscan_range": "tcp:80,443,8080,8443",
                    "thorough_tests": True,
                    "safe_checks": False,
                    "report_verbosity": "Normal",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "mobile", "api", "oauth", "jwt", "ssl", 
                            "insecure_storage", "code_injection"
                        ]
                    }
                }
            },
            
            # 数据库扫描配置
            "database": {
                "name": "数据库安全扫描",
                "description": "针对数据库系统的安全评估",
                "settings": {
                    "policy": "database",
                    "portscan_range": "tcp:1433,1521,3306,5432,27017,6379",
                    "thorough_tests": True,
                    "safe_checks": True,
                    "report_verbosity": "Detailed",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "database", "sql", "nosql", "misconfiguration",
                            "weak_auth", "injection"
                        ]
                    }
                }
            },
            
            # 云环境扫描配置
            "cloud": {
                "name": "云环境安全扫描",
                "description": "针对云服务和基础设施的安全评估",
                "settings": {
                    "policy": "cloud",
                    "portscan_range": "default",
                    "thorough_tests": True,
                    "safe_checks": True,
                    "report_verbosity": "Detailed",
                    "performance": "Normal",
                    "plugin_selection": {
                        "enabled": True,
                        "include": [
                            "cloud", "aws", "azure", "gcp", "misconfiguration",
                            "iam", "storage", "api"
                        ]
                    }
                }
            }
        }
        
        # 强度配置映射
        self.intensity_settings = {
            "light": {
                "thorough_tests": False,
                "performance": "Fast",
                "plugin_selection": {"enabled": True, "include": ["basic", "critical"]}
            },
            "normal": {
                "thorough_tests": True,
                "performance": "Normal",
                "plugin_selection": {"enabled": True, "include": ["standard"]}
            },
            "aggressive": {
                "thorough_tests": True,
                "performance": "Normal",
                "safe_checks": False,
                "plugin_selection": {"enabled": True, "include": ["comprehensive"]}
            },
            "extreme": {
                "thorough_tests": True,
                "performance": "Aggressive",
                "safe_checks": False,
                "report_verbosity": "Detailed",
                "plugin_selection": {"enabled": False}  # 启用所有插件
            }
        }
    
    def get_scan_config(self, policy: str, intensity: str = "normal", custom_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """获取扫描配置"""
        if policy not in self.configs:
            policy = "web_application"  # 默认配置
        
        config = self.configs[policy].copy()
        
        # 应用强度设置
        if intensity in self.intensity_settings:
            intensity_config = self.intensity_settings[intensity]
            config["settings"].update(intensity_config)
        
        # 应用自定义设置
        if custom_settings:
            config["settings"].update(custom_settings)
        
        return config
    
    def get_policy_list(self) -> List[Dict[str, str]]:
        """获取策略列表"""
        policies = []
        for key, config in self.configs.items():
            policies.append({
                "id": key,
                "name": config["name"],
                "description": config["description"]
            })
        return policies
    
    def get_custom_policy(self, target_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """生成自定义策略"""
        base_policy = self.get_scan_config("web_application", "normal")
        
        # 根据目标类型调整
        if target_type == "api":
            base_policy["settings"]["portscan_range"] = "tcp:80,443,8080,8443,3000,5000"
            base_policy["settings"]["plugin_selection"]["include"].extend(["api", "rest", "graphql"])
        
        elif target_type == "critical_infrastructure":
            base_policy["settings"]["portscan_range"] = "default"
            base_policy["settings"]["safe_checks"] = True
            base_policy["settings"]["thorough_tests"] = True
            base_policy["settings"]["plugin_selection"]["include"].extend(["ics", "scada", "industrial"])
        
        # 应用需求
        if "ports" in requirements:
            base_policy["settings"]["portscan_range"] = requirements["ports"]
        
        if "plugins" in requirements:
            base_policy["settings"]["plugin_selection"]["include"].extend(requirements["plugins"])
        
        return base_policy

# 全局配置实例
scan_config_manager = ScanConfiguration()

def create_advanced_scan_preset(name: str, description: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """创建高级扫描预设"""
    return {
        "name": name,
        "description": description,
        "settings": settings
    }

# 预设扫描配置
PRESET_CONFIGS = {
    "enterprise_web": create_advanced_scan_preset(
        "企业Web应用扫描",
        "针对企业级Web应用的全面安全评估",
        {
            "policy": "webapp",
            "portscan_range": "tcp:80,443,8080,8443,8000,3000,5000,9000",
            "thorough_tests": True,
            "safe_checks": False,
            "report_verbosity": "Detailed",
            "performance": "Normal",
            "plugin_selection": {
                "enabled": True,
                "include": ["web", "webapp", "api", "ssl", "authentication", "authorization"]
            }
        }
    ),
    
    "critical_infrastructure": create_advanced_scan_preset(
        "关键基础设施扫描",
        "针对关键系统和基础设施的安全评估",
        {
            "policy": "network",
            "portscan_range": "default",
            "thorough_tests": True,
            "safe_checks": True,
            "report_verbosity": "Detailed",
            "performance": "Normal",
            "plugin_selection": {
                "enabled": True,
                "include": ["critical", "vulnerability", "service", "protocol"]
            }
        }
    ),
    
    "api_security": create_advanced_scan_preset(
        "API安全扫描",
        "针对RESTful API和微服务的安全测试",
        {
            "policy": "webapp",
            "portscan_range": "tcp:80,443,8080,8443,3000,5000,8000",
            "thorough_tests": True,
            "safe_checks": False,
            "report_verbosity": "Normal",
            "performance": "Normal",
            "plugin_selection": {
                "enabled": True,
                "include": ["api", "rest", "graphql", "authentication", "authorization", "injection"]
            }
        }
    )
}

if __name__ == "__main__":
    # 测试配置管理器
    config_mgr = ScanConfiguration()
    
    print("可用扫描策略:")
    for policy in config_mgr.get_policy_list():
        print(f"- {policy['name']}: {policy['description']}")
    
    print("\nWeb应用扫描配置示例:")
    web_config = config_mgr.get_scan_config("web_application", "aggressive")
    print(web_config)
