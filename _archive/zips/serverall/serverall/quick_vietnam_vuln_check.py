#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速越南漏洞检查工具
Quick Vietnam Vulnerability Checker

快速检查越南高价值目标的常见漏洞
"""

import requests
import json
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_vulnerabilities():
    """检查漏洞"""

    # 高价值目标
    targets = [
        {"name": "Shopee Vietnam", "url": "https://shopee.vn", "type": "ecommerce"},
        {"name": "MoMo Wallet", "url": "https://momo.vn", "type": "payment"},
        {"name": "Tiki", "url": "https://tiki.vn", "type": "ecommerce"},
        {"name": "Viettel Post", "url": "https://viettelpost.vn", "type": "logistics"},
        {"name": "ZaloPay", "url": "https://zalopay.vn", "type": "payment"},
        {"name": "Lazada Vietnam", "url": "https://lazada.vn", "type": "ecommerce"},
        {"name": "VNPost", "url": "https://vnpost.vn", "type": "logistics"},
        {"name": "VNPay", "url": "https://vnpay.vn", "type": "payment"}
    ]

    results = []
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    print("快速越南漏洞检查工具")
    print("=" * 40)
    print(f"检查 {len(targets)} 个高价值目标")
    print()

    for target in targets:
        print(f"[检查] {target['name']} ({target['url']})")

        result = {
            "target": target,
            "accessible": False,
            "vulnerabilities": []
        }

        try:
            # 基础访问测试
            response = session.get(target['url'], timeout=10)
            if response.status_code == 200:
                result["accessible"] = True
                print(f"  [OK] 可访问")

                # 检查管理后台
                admin_paths = ["/admin", "/wp-admin", "/login", "/dashboard", "/backend"]
                for path in admin_paths:
                    try:
                        admin_url = target['url'] + path
                        admin_resp = session.get(admin_url, timeout=5)
                        if admin_resp.status_code in [200, 401, 403]:
                            result["vulnerabilities"].append({
                                "type": "admin_panel",
                                "url": admin_url,
                                "status": admin_resp.status_code,
                                "severity": "High" if admin_resp.status_code == 200 else "Medium"
                            })
                            print(f"  [ADMIN] 发现管理后台: {path} ({admin_resp.status_code})")
                    except:
                        continue

                # 检查API端点
                api_paths = ["/api", "/api/v1", "/rest", "/webapi"]
                for path in api_paths:
                    try:
                        api_url = target['url'] + path
                        api_resp = session.get(api_url, timeout=5)
                        if api_resp.status_code == 200:
                            content = api_resp.text.lower()
                            if any(word in content for word in ["password", "token", "key", "secret"]):
                                result["vulnerabilities"].append({
                                    "type": "api_info_leak",
                                    "url": api_url,
                                    "severity": "High"
                                })
                                print(f"  [API] 信息泄露: {path}")
                    except:
                        continue

                # 检查常见漏洞文件
                vuln_files = ["/phpinfo.php", "/info.php", "/test.php", "/.env"]
                for file in vuln_files:
                    try:
                        file_url = target['url'] + file
                        file_resp = session.get(file_url, timeout=5)
                        if file_resp.status_code == 200:
                            result["vulnerabilities"].append({
                                "type": "sensitive_file",
                                "url": file_url,
                                "severity": "Medium"
                            })
                            print(f"  [FILE] 敏感文件: {file}")
                    except:
                        continue

            else:
                print(f"  [FAIL] 不可访问 ({response.status_code})")

        except Exception as e:
            print(f"  [ERROR] {str(e)[:30]}")

        results.append(result)
        time.sleep(1)  # 避免过于频繁

    # 生成报告
    print("\n" + "=" * 40)
    print("扫描结果汇总")
    print("=" * 40)

    total = len(results)
    accessible = len([r for r in results if r["accessible"]])
    total_vulns = sum(len(r["vulnerabilities"]) for r in results)

    print(f"总目标数: {total}")
    print(f"可访问: {accessible}")
    print(f"发现漏洞: {total_vulns}")

    # 显示有漏洞的目标
    vuln_targets = [r for r in results if r["vulnerabilities"]]

    if vuln_targets:
        print(f"\n存在漏洞的目标 ({len(vuln_targets)} 个):")
        for result in vuln_targets:
            target = result["target"]
            vulns = result["vulnerabilities"]
            print(f"\n• {target['name']} ({target['type']})")
            print(f"  URL: {target['url']}")

            # 按严重程度分组
            critical = [v for v in vulns if v.get("severity") == "Critical"]
            high = [v for v in vulns if v.get("severity") == "High"]
            medium = [v for v in vulns if v.get("severity") == "Medium"]

            if critical:
                print(f"  严重: {len(critical)} 个")
                for v in critical:
                    print(f"    - {v['type']}: {v['url']}")

            if high:
                print(f"  高危: {len(high)} 个")
                for v in high:
                    print(f"    - {v['type']}: {v['url']}")

            if medium:
                print(f"  中危: {len(medium)} 个")
                for v in medium:
                    print(f"    - {v['type']}: {v['url']}")

    # 保存详细结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"vietnam_vuln_check_{timestamp}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "scan_time": datetime.now().isoformat(),
            "summary": {
                "total_targets": total,
                "accessible": accessible,
                "total_vulnerabilities": total_vulns
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存到: {report_file}")

    # 重点关注
    critical_targets = [r for r in results if any(v.get("severity") == "Critical" for v in r["vulnerabilities"])]
    high_targets = [r for r in results if any(v.get("severity") == "High" for v in r["vulnerabilities"])]

    print(f"\n重点关注:")
    if critical_targets:
        print(f"  严重漏洞: {len(critical_targets)} 个目标")
        for target in critical_targets:
            print(f"    • {target['target']['name']}")

    if high_targets:
        print(f"  高危漏洞: {len(high_targets)} 个目标")
        for target in high_targets:
            print(f"    • {target['target']['name']}")

if __name__ == "__main__":
    try:
        check_vulnerabilities()
    except KeyboardInterrupt:
        print("\n检查被中断")
    except Exception as e:
        print(f"\n检查出错: {e}")