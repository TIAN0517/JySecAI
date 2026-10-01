#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus配置管理器 - 企业级漏洞扫描配置
Nessus Configuration Manager - Enterprise Vulnerability Scanning Configuration

功能特性:
- Nessus服务器配置管理
- 扫描策略配置
- 扫描模板定义
- 自动发现配置
- 报告格式设置
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class NessusConfig:
    """Nessus配置管理器"""
    
    def __init__(self, config_file: str = "nessus_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "nessus_servers": {
                "primary": {
                    "host": "localhost",
                    "port": 8834,
                    "access_key": "30621a6d39e501a21bc31adb1aa40f633127e0deef08cd094ff20f80d5565f8c",
                    "secret_key": "5716d0ca6fb04b6a0c235d1f57756e08c0847b869fd50c5313e8f34e34e45856",
                    "enabled": True,
                    "description": "主Nessus服务器"
                },
                "secondary": {
                    "host": "localhost",
                    "port": 8834,
                    "access_key": "30621a6d39e501a21bc31adb1aa40f633127e0deef08cd094ff20f80d5565f8c",
                    "secret_key": "5716d0ca6fb04b6a0c235d1f57756e08c0847b869fd50c5313e8f34e34e45856",
                    "enabled": True,
                    "description": "备用Nessus服务器"
                }
            },
            "scan_policies": {
                "web_application": {
                    "name": "Web应用安全扫描",
                    "description": "针对Web应用程序的全面安全扫描",
                    "template": "webapp",
                    "settings": {
                        "portscan_range": "default",
                        "thorough_tests": True,
                        "report_verbosity": "Normal",
                        "safe_checks": True
                    }
                },
                "network_infrastructure": {
                    "name": "网络基础设施扫描",
                    "description": "网络设备和服务器的安全评估",
                    "template": "advanced",
                    "settings": {
                        "portscan_range": "1-65535",
                        "syn_scanner": True,
                        "udp_scanner": False,
                        "report_verbosity": "Detailed"
                    }
                },
                "critical_vulnerabilities": {
                    "name": "关键漏洞扫描",
                    "description": "专注于高危和严重漏洞检测",
                    "template": "discovery",
                    "settings": {
                        "portscan_range": "1-10000",
                        "only_critical": True,
                        "safe_checks": True
                    }
                }
            },
            "scan_templates": {
                "basic": {
                    "name": "基础扫描",
                    "description": "快速基础安全扫描",
                    "uuid": "731a8e52-3ea6-11e7-8d6e-ebd96b2fc7ab"
                },
                "discovery": {
                    "name": "发现扫描",
                    "description": "网络发现和主机枚举",
                    "uuid": "bbd4f0c6-1796-11e6-a68d-ebd96b2fc7ab"
                },
                "webapp": {
                    "name": "Web应用扫描",
                    "description": "Web应用程序漏洞扫描",
                    "uuid": "5e0f5c1e-8c2a-4c7e-8e4f-8b0e2b0f8b1e"
                },
                "advanced": {
                    "name": "高级扫描",
                    "description": "全面深入的安全评估",
                    "uuid": "c5e7a9b8-3ea6-11e7-9d6d-ebd96b2fc7ab"
                }
            },
            "report_config": {
                "formats": ["nessus", "html", "pdf", "csv"],
                "default_format": "html",
                "include_remediation": True,
                "include_technical_details": True,
                "risk_levels": ["critical", "high", "medium", "low", "info"],
                "custom_templates": {
                    "executive_summary": {
                        "include_executive_summary": True,
                        "include_risk_matrix": True,
                        "include_recommendations": True
                    },
                    "technical_report": {
                        "include_vulnerability_details": True,
                        "include_remediation_steps": True,
                        "include_references": True
                    }
                }
            },
            "scan_schedules": {
                "daily": {
                    "enabled": False,
                    "frequency": "daily",
                    "start_time": "02:00",
                    "targets": []
                },
                "weekly": {
                    "enabled": False,
                    "frequency": "weekly",
                    "day_of_week": "sunday",
                    "start_time": "03:00",
                    "targets": []
                },
                "monthly": {
                    "enabled": False,
                    "frequency": "monthly",
                    "day_of_month": 1,
                    "start_time": "04:00",
                    "targets": []
                }
            },
            "notification_settings": {
                "email_notifications": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": [],
                    "scan_complete": True,
                    "critical_findings": True
                },
                "telegram_notifications": {
                    "enabled": True,
                    "bot_token": "",
                    "chat_id": "",
                    "scan_complete": True,
                    "critical_findings": True
                }
            },
            "integration_settings": {
                "dragon_v_integration": {
                    "enabled": True,
                    "auto_import": True,
                    "risk_threshold": "medium",
                    "generate_reports": True
                },
                "webhook_integration": {
                    "enabled": False,
                    "webhook_url": "",
                    "events": ["scan_complete", "critical_finding"]
                }
            }
        }
        
        # 如果配置文件存在则加载，否则使用默认配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] 加载配置文件失败: {e}，使用默认配置")
                return default_config
        else:
            # 保存默认配置
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """保存配置到文件"""
        try:
            if config is None:
                config = self.config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            print(f"[+] 配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            print(f"[-] 保存配置失败: {e}")
            return False
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的配置"""
        return self.config.get('nessus_servers', {}).get(server_name)
    
    def update_server_config(self, server_name: str, config: Dict[str, Any]) -> bool:
        """更新服务器配置"""
        try:
            if 'nessus_servers' not in self.config:
                self.config['nessus_servers'] = {}
            
            self.config['nessus_servers'][server_name] = config
            return self.save_config()
        except Exception as e:
            print(f"[-] 更新服务器配置失败: {e}")
            return False
    
    def get_scan_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """获取扫描策略"""
        return self.config.get('scan_policies', {}).get(policy_name)
    
    def update_scan_policy(self, policy_name: str, policy: Dict[str, Any]) -> bool:
        """更新扫描策略"""
        try:
            if 'scan_policies' not in self.config:
                self.config['scan_policies'] = {}
            
            self.config['scan_policies'][policy_name] = policy
            return self.save_config()
        except Exception as e:
            print(f"[-] 更新扫描策略失败: {e}")
            return False
    
    def add_scan_schedule(self, schedule_name: str, schedule: Dict[str, Any]) -> bool:
        """添加扫描计划"""
        try:
            if 'scan_schedules' not in self.config:
                self.config['scan_schedules'] = {}
            
            self.config['scan_schedules'][schedule_name] = schedule
            return self.save_config()
        except Exception as e:
            print(f"[-] 添加扫描计划失败: {e}")
            return False
    
    def enable_notifications(self, notification_type: str, enabled: bool = True) -> bool:
        """启用/禁用通知"""
        try:
            notification_config = self.config.get('notification_settings', {})
            
            if notification_type in notification_config:
                notification_config[notification_type]['enabled'] = enabled
                return self.save_config()
            else:
                print(f"[-] 未知的通知类型: {notification_type}")
                return False
        except Exception as e:
            print(f"[-] 更新通知设置失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 验证服务器配置
        servers = self.config.get('nessus_servers', {})
        if not servers:
            validation_result['valid'] = False
            validation_result['errors'].append("未配置Nessus服务器")
        
        for server_name, server_config in servers.items():
            if not server_config.get('host'):
                validation_result['errors'].append(f"服务器 {server_name} 缺少主机地址")
            
            if not server_config.get('access_key') or not server_config.get('secret_key'):
                validation_result['errors'].append(f"服务器 {server_name} 缺少API密钥")
        
        # 验证扫描策略
        policies = self.config.get('scan_policies', {})
        if not policies:
            validation_result['warnings'].append("未配置扫描策略")
        
        # 验证通知设置
        notifications = self.config.get('notification_settings', {})
        telegram_notifications = notifications.get('telegram_notifications', {})
        if telegram_notifications.get('enabled'):
            if not telegram_notifications.get('bot_token'):
                validation_result['warnings'].append("Telegram通知已启用但未配置Bot Token")
            if not telegram_notifications.get('chat_id'):
                validation_result['warnings'].append("Telegram通知已启用但未配置Chat ID")
        
        return validation_result
    
    def export_config(self, export_file: str = None) -> str:
        """导出配置"""
        if export_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = f"nessus_config_export_{timestamp}.json"
        
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            print(f"[+] 配置已导出到: {export_file}")
            return export_file
        except Exception as e:
            print(f"[-] 导出配置失败: {e}")
            return ""
    
    def import_config(self, import_file: str) -> bool:
        """导入配置"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # 验证导入的配置
            self.config = imported_config
            validation = self.validate_config()
            
            if validation['valid'] or validation['warnings']:
                # 如果有警告但仍然有效，可以继续
                self.save_config()
                print(f"[+] 配置已从 {import_file} 导入")
                return True
            else:
                print(f"[-] 导入的配置无效: {validation['errors']}")
                return False
        except Exception as e:
            print(f"[-] 导入配置失败: {e}")
            return False

# 全局配置实例
nessus_config = NessusConfig()

def get_nessus_config():
    """获取全局Nessus配置"""
    return nessus_config

def update_nessus_server(server_name: str, host: str, port: int, access_key: str, secret_key: str, enabled: bool = True) -> bool:
    """更新Nessus服务器配置"""
    config = {
        "host": host,
        "port": port,
        "access_key": access_key,
        "secret_key": secret_key,
        "enabled": enabled,
        "description": f"{server_name} Nessus服务器"
    }
    return nessus_config.update_server_config(server_name, config)

def main():
    """配置管理主函数"""
    print("🔧 Nessus配置管理器")
    print("=" * 50)
    
    # 验证配置
    validation = nessus_config.validate_config()
    print(f"配置验证结果: {'✅ 有效' if validation['valid'] else '❌ 无效'}")
    
    if validation['errors']:
        print("错误信息:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("警告信息:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    # 显示服务器配置
    print("\n服务器配置:")
    servers = nessus_config.config.get('nessus_servers', {})
    for name, config in servers.items():
        print(f"  {name}: {config.get('host')}:{config.get('port')} {'✅ 启用' if config.get('enabled') else '❌ 禁用'}")
    
    # 显示扫描策略
    print("\n扫描策略:")
    policies = nessus_config.config.get('scan_policies', {})
    for name, policy in policies.items():
        print(f"  {name}: {policy.get('name')}")

if __name__ == "__main__":
    main()