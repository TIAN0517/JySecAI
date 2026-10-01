#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强配置管理器 - 企业级配置管理
Enhanced Configuration Manager - Enterprise Configuration Management
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器 - 支持多种配置格式和环境变量"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = self._get_default_config()
        
        # 尝试从文件加载配置
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.json'):
                        file_config = json.load(f)
                    elif self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        file_config = yaml.safe_load(f)
                    else:
                        file_config = {}
                
                # 合并配置（文件配置覆盖默认配置）
                return {**default_config, **file_config}
                
            except Exception as e:
                print(f"警告: 配置文件加载失败，使用默认配置: {e}")
                return default_config
        else:
            # 创建默认配置文件
            self._create_default_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "telegram": {
                "bot_tokens": {
                    "bot_1": os.getenv("BOT_1_TOKEN", "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw"),
                    "bot_3": os.getenv("BOT_3_TOKEN", "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA")
                },
                "admin_ids": [123456789],  # 管理员用户ID
                "max_workers": 5,  # 最大工作线程数
                "rate_limit": 30  # 消息频率限制（消息/分钟）
            },
            "security": {
                "allowed_domains": [
                    "example.com",
                    "test.com"
                ],
                "blocked_domains": [
                    "google.com",
                    "facebook.com"
                ],
                "max_scan_time": 300,  # 最大扫描时间（秒）
                "request_timeout": 30,  # 请求超时时间（秒）
                "max_requests_per_minute": 60  # 每分钟最大请求数
            },
            "scanning": {
                "sql_injection": True,
                "xss": True,
                "idor": True,
                "file_upload": True,
                "api_leaks": True,
                "sensitive_data": True,
                "waf_bypass": True,
                "deep_scan": False,  # 深度扫描模式
                "aggressive_mode": False  # 激进模式
            },
            "reporting": {
                "generate_html": True,
                "generate_json": True,
                "save_to_file": True,
                "send_to_telegram": True,
                "report_format": "detailed"  # detailed/summary/minimal
            },
            "performance": {
                "max_concurrent_scans": 3,
                "request_delay": 1.0,  # 请求延迟（秒）
                "retry_attempts": 3,
                "timeout_multiplier": 2.0
            },
            "logging": {
                "level": "INFO",  # DEBUG/INFO/WARNING/ERROR
                "file_enabled": True,
                "console_enabled": True,
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5
            },
            "database": {
                "path": "dragon_v_scanner.db",
                "backup_enabled": True,
                "backup_interval": 3600  # 备份间隔（秒）
            },
            "waf_bypass": {
                "enabled": True,
                "techniques": ["encoding", "obfuscation", "timing"],
                "max_payloads_per_technique": 50,
                "random_delay": True
            },
            "exploitation": {
                "max_extraction_records": 100,
                "data_sampling": True,
                "safe_mode": True  # 安全模式，避免破坏性操作
            }
        }
    
    def _create_default_config(self, config: Dict[str, Any]):
        """创建默认配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.json'):
                    json.dump(config, f, indent=2, ensure_ascii=False)
                elif self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"默认配置文件已创建: {self.config_file}")
            print("请根据您的需求修改配置文件。")
            
        except Exception as e:
            print(f"创建配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.json'):
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                elif self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def validate(self) -> bool:
        """验证配置"""
        errors = []
        
        # 检查必要配置
        required_configs = [
            "telegram.bot_tokens.bot_1",
            "telegram.bot_tokens.bot_3",
            "security.max_scan_time",
            "performance.max_concurrent_scans"
        ]
        
        for config_key in required_configs:
            if self.get(config_key) is None:
                errors.append(f"缺少必要配置: {config_key}")
        
        # 检查配置值范围
        max_workers = self.get("telegram.max_workers")
        if max_workers and (max_workers < 1 or max_workers > 20):
            errors.append("max_workers 必须在 1-20 之间")
        
        max_scan_time = self.get("security.max_scan_time")
        if max_scan_time and (max_scan_time < 10 or max_scan_time > 3600):
            errors.append("max_scan_time 必须在 10-3600 秒之间")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """获取Telegram配置"""
        return self.get("telegram", {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get("security", {})
    
    def get_scanning_config(self) -> Dict[str, Any]:
        """获取扫描配置"""
        return self.get("scanning", {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.get("performance", {})


class EnvironmentConfig:
    """环境变量配置"""
    
    @staticmethod
    def get_bot_token(bot_name: str) -> Optional[str]:
        """获取Bot Token"""
        env_var = f"{bot_name.upper()}_TOKEN"
        return os.getenv(env_var)
    
    @staticmethod
    def get_admin_ids() -> list:
        """获取管理员ID"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            return [int(id.strip()) for id in admin_ids_str.split(",")]
        return []
    
    @staticmethod
    def get_database_path() -> str:
        """获取数据库路径"""
        return os.getenv("DATABASE_PATH", "dragon_v_scanner.db")
    
    @staticmethod
    def get_log_level() -> str:
        """获取日志级别"""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @staticmethod
    def is_debug_mode() -> bool:
        """是否调试模式"""
        return os.getenv("DEBUG", "false").lower() == "true"


# 全局配置实例
config_manager = ConfigManager()

# 使用示例
if __name__ == "__main__":
    # 验证配置
    if config_manager.validate():
        print("配置验证通过")
        
        # 获取配置值
        bot_token = config_manager.get("telegram.bot_tokens.bot_1")
        max_scan_time = config_manager.get("security.max_scan_time")
        
        print(f"Bot Token: {bot_token[:10]}...")
        print(f"最大扫描时间: {max_scan_time}秒")
        
        # 修改配置
        config_manager.set("performance.max_concurrent_scans", 5)
        config_manager.save()
        print("配置已保存")
    else:
        print("配置验证失败，请检查配置文件")