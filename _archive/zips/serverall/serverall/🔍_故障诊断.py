#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 DRAGON-V 启动故障诊断工具
帮助排查和解决启动问题
"""

import os
import sys
import traceback

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_section(title):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def check_bot_file(filename):
    """检查 Bot 文件是否可导入"""
    print_section(f"检查 Bot 文件: {filename}")
    
    if not os.path.exists(filename):
        print(f"{Colors.RED}✗ 文件不存在: {filename}{Colors.END}")
        return False
    
    try:
        print(f"[*] 尝试导入 {filename}...")
        
        # 尝试编译文件
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        compile(code, filename, 'exec')
        print(f"{Colors.GREEN}✓ 语法检查通过{Colors.END}")
        return True
        
    except SyntaxError as e:
        print(f"{Colors.RED}✗ 语法错误:{Colors.END}")
        print(f"  行号: {e.lineno}")
        print(f"  错误: {e.msg}")
        print(f"  {e.text}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ 错误: {str(e)}{Colors.END}")
        return False

def check_token_validity():
    """检查 Bot Token 格式"""
    print_section("检查 Bot Token")
    
    tokens = {
        "Bot #1": "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
        "Bot #3": "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA"
    }
    
    for name, token in tokens.items():
        print(f"[*] {name}: {token[:20]}...")
        
        if ':' in token and len(token.split(':')) == 2:
            parts = token.split(':')
            bot_id, token_part = parts
            
            if bot_id.isdigit() and len(token_part) > 20:
                print(f"{Colors.GREEN}✓ Token 格式有效{Colors.END}\n")
            else:
                print(f"{Colors.RED}✗ Token 格式错误{Colors.END}\n")
        else:
            print(f"{Colors.RED}✗ Token 格式错误{Colors.END}\n")

def check_telegram_import():
    """检查 Telegram 库是否可用"""
    print_section("检查 Telegram 库")
    
    try:
        print("[*] 尝试导入 telegram...")
        import telegram
        print(f"{Colors.GREEN}✓ Telegram 库已安装{Colors.END}")
        print(f"    版本: {telegram.__version__}")
        
        print("[*] 尝试导入 telegram.ext...")
        from telegram import ext
        print(f"{Colors.GREEN}✓ Telegram.ext 已安装{Colors.END}\n")
        return True
        
    except ImportError as e:
        print(f"{Colors.RED}✗ 导入失败: {str(e)}{Colors.END}\n")
        print(f"解决方案:")
        print(f"  pip install python-telegram-bot\n")
        return False

def check_requests_import():
    """检查 Requests 库"""
    print_section("检查 Requests 库")
    
    try:
        print("[*] 尝试导入 requests...")
        import requests
        print(f"{Colors.GREEN}✓ Requests 库已安装{Colors.END}")
        print(f"    版本: {requests.__version__}\n")
        return True
        
    except ImportError:
        print(f"{Colors.RED}✗ Requests 库未安装{Colors.END}\n")
        print(f"解决方案:")
        print(f"  pip install requests\n")
        return False

def test_telegram_connection():
    """测试 Telegram API 连接"""
    print_section("测试 Telegram 连接")
    
    try:
        import requests
        print("[*] 测试与 Telegram API 连接...")
        
        response = requests.get("https://api.telegram.org", timeout=5)
        print(f"{Colors.GREEN}✓ 可以连接到 Telegram 服务器{Colors.END}\n")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}✗ 无法连接到 Telegram 服务器{Colors.END}\n")
        print(f"可能的原因:")
        print(f"  • 网络连接问题")
        print(f"  • 防火墙阻止")
        print(f"  • 代理问题\n")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ 连接测试失败: {str(e)}{Colors.END}\n")
        return False

def check_bot_token_validity():
    """测试 Bot Token 是否有效"""
    print_section("验证 Bot Token")
    
    try:
        import requests
        
        tokens = {
            "Bot #1": "8314772330:AAHOEYCPAY5WL99orpwwETrbykwFwBG6Jkw",
            "Bot #3": "8344575992:AAGIszxFk2AgqmkkHIri6QhtkDe_71nKgvA"
        }
        
        for name, token in tokens.items():
            print(f"[*] 测试 {name}...")
            
            try:
                url = f"https://api.telegram.org/bot{token}/getMe"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('ok'):
                        bot_info = data.get('result', {})
                        print(f"{Colors.GREEN}✓ Token 有效{Colors.END}")
                        print(f"    Bot 名称: {bot_info.get('first_name')}")
                        print(f"    Bot 用户名: @{bot_info.get('username')}\n")
                    else:
                        print(f"{Colors.RED}✗ Token 无效{Colors.END}\n")
                else:
                    print(f"{Colors.RED}✗ 请求失败 (状态码: {response.status_code}){Colors.END}\n")
                    
            except Exception as e:
                print(f"{Colors.RED}✗ 测试失败: {str(e)}{Colors.END}\n")
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}✗ 错误: {str(e)}{Colors.END}\n")
        return False

def run_full_diagnostic():
    """运行完整诊断"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}🔍 DRAGON-V 启动故障诊断{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    results = []
    
    # 1. 检查 Bot 文件
    results.append(("Bot 文件 #1", check_bot_file("bot_ultimate_with_waf_bypass.py")))
    results.append(("Bot 文件 #3", check_bot_file("bot_3_ultimate_with_waf_bypass.py")))
    
    # 2. 检查 Token
    check_token_validity()
    
    # 3. 检查库
    results.append(("Telegram 库", check_telegram_import()))
    results.append(("Requests 库", check_requests_import()))
    
    # 4. 测试连接
    results.append(("Telegram 连接", test_telegram_connection()))
    
    # 5. 验证 Token
    results.append(("Token 验证", check_bot_token_validity()))
    
    # 打印总结
    print_section("诊断总结")
    
    all_ok = True
    for name, result in results:
        status = f"{Colors.GREEN}✓{Colors.END}" if result else f"{Colors.RED}✗{Colors.END}"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    print()
    if all_ok:
        print(f"{Colors.GREEN}✅ 所有诊断通过！系统应该可以正常启动{Colors.END}\n")
        print(f"如果仍然无法启动，请尝试:")
        print(f"  1. 重新启动系统")
        print(f"  2. 重新安装依赖: pip install --upgrade python-telegram-bot requests")
        print(f"  3. 以管理员身份运行\n")
    else:
        print(f"{Colors.RED}❌ 诊断发现问题，请按上述提示解决{Colors.END}\n")
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

if __name__ == "__main__":
    try:
        run_full_diagnostic()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.CYAN}诊断已中断{Colors.END}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}诊断出错: {str(e)}{Colors.END}\n")
        traceback.print_exc()
        sys.exit(1)
