#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSL密码管理器 - 用于MCP Kali系统
"""

import os
import json
import subprocess
from pathlib import Path

class WSLPasswordManager:
    def __init__(self):
        self.password = "520520"
        self.config_file = Path.home() / ".cursor" / "wsl_config.json"
        self.ensure_config_dir()

    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def save_password(self):
        """保存密码到配置文件"""
        config = {
            "wsl_password": self.password,
            "wsl_user": "bossjy",
            "timestamp": "2025-10-27"
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

        print(f"WSL password config saved to: {self.config_file}")

    def test_sudo_access(self):
        """测试sudo权限"""
        try:
            # 创建一个带有密码的sudo命令
            cmd = f'echo "{self.password}" | sudo -S whoami'
            result = subprocess.run(
                ['wsl', 'bash', '-c', cmd],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print("✅ WSL sudo权限测试成功")
                return True
            else:
                print(f"❌ WSL sudo权限测试失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("⚠️ WSL sudo权限测试超时")
            return False
        except Exception as e:
            print(f"❌ WSL sudo权限测试出错: {e}")
            return False

    def create_sudoers_config(self):
        """创建sudoers配置以减少密码输入"""
        try:
            # 创建临时sudoers配置
            sudoers_config = f"""
# MCP Kali WSL Configuration
bossjy ALL=(ALL) NOPASSWD: /usr/bin/nmap
bossjy ALL=(ALL) NOPASSWD: /usr/bin/sqlmap
bossjy ALL=(ALL) NOPASSWD: /usr/bin/hydra
bossjy ALL=(ALL) NOPASSWD: /usr/bin/nikto
bossjy ALL=(ALL) NOPASSWD: /usr/bin/gobuster
bossjy ALL=(ALL) NOPASSWD: /usr/bin/dirb
bossjy ALL=(ALL) NOPASSWD: /usr/bin/wpscan
bossjy ALL=(ALL) NOPASSWD: /usr/bin/enum4linux
bossjy ALL=(ALL) NOPASSWD: /usr/bin/john
"""

            # 写入临时文件
            temp_file = "/tmp/mcp_sudoers"
            with open(temp_file, 'w') as f:
                f.write(sudoers_config)

            print(f"📝 Sudoers配置文件已创建: {temp_file}")
            print("💡 请手动执行以下命令来应用配置:")
            print(f"   sudo cp {temp_file} /etc/sudoers.d/mcp_kali")
            print(f"   sudo chmod 440 /etc/sudoers.d/mcp_kali")

        except Exception as e:
            print(f"❌ 创建sudoers配置失败: {e}")

def main():
    """主函数"""
    print("WSL Password Manager")
    print("=" * 50)

    manager = WSLPasswordManager()

    # 保存密码配置
    manager.save_password()

    # 测试sudo权限
    print("\n🔐 测试WSL sudo权限...")
    if manager.test_sudo_access():
        print("✅ WSL权限配置正常")
    else:
        print("⚠️ WSL权限需要手动配置")

    # 创建sudoers配置
    print("\n📋 创建sudoers配置...")
    manager.create_sudoers_config()

    print("\n🎉 WSL密码管理器配置完成！")
    print("\n📋 下一步操作:")
    print("1. 重启Cursor以加载MCP配置")
    print("2. 在Cursor中使用Kali工具")
    print("3. 如需完整权限，请手动应用sudoers配置")

if __name__ == "__main__":
    main()