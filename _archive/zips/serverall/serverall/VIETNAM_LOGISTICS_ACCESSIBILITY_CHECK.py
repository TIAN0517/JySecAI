#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南快递站点可访问性检查工具
Vietnam Logistics Sites Accessibility Checker for Dragon-V Triple Bot v3.2.0

检查越南快递物流网站的可访问性，筛选出可以进行安全扫描的目标
"""

import requests
import concurrent.futures
import socket
import ssl
import time
import yaml
from urllib.parse import urlparse
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_accessibility_check.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VietnamLogisticsAccessibilityChecker:
    """越南物流站点可访问性检查器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 越南主要快递公司列表
        self.logistics_targets = [
            {
                "name": "GHN (Giao Hàng Nhanh)",
                "url": "https://ghn.vn",
                "backup_urls": ["https://giaohangnhanh.vn"],
                "type": "major_express",
                "priority": 1
            },
            {
                "name": "GHTK (Giao Hàng Tiết Kiệm)",
                "url": "https://ghtk.vn",
                "backup_urls": ["https://giaohangtietkiem.vn"],
                "type": "major_express",
                "priority": 2
            },
            {
                "name": "Viettel Post",
                "url": "https://viettelpost.vn",
                "backup_urls": ["https://vtp.vn"],
                "type": "state_owned",
                "priority": 3
            },
            {
                "name": "VNPost (Vietnam Post)",
                "url": "https://vnpost.vn",
                "backup_urls": ["https://buudien.vn"],
                "type": "state_owned",
                "priority": 4
            },
            {
                "name": "J&T Express Vietnam",
                "url": "https://jntexpress.vn",
                "backup_urls": ["https://jandtexpress.vn"],
                "type": "international",
                "priority": 5
            },
            {
                "name": "Ninja Van Vietnam",
                "url": "https://ninjavan.co",
                "backup_urls": ["https://ninjavan.vn"],
                "type": "regional",
                "priority": 6
            },
            {
                "name": "Shopee Express Vietnam",
                "url": "https://express.shopee.vn",
                "backup_urls": [],
                "type": "ecommerce",
                "priority": 7
            },
            {
                "name": "Giaohangtietkiem",
                "url": "https://giaohangtietkiem.vn",
                "backup_urls": [],
                "type": "economy",
                "priority": 8
            },
            {
                "name": "Ahamove",
                "url": "https://ahamove.com",
                "backup_urls": ["https://ahamove.vn"],
                "type": "bike_delivery",
                "priority": 9
            },
            {
                "name": "Beelivery",
                "url": "https://beelivery.vn",
                "backup_urls": [],
                "type": "bike_delivery",
                "priority": 10
            }
        ]

    def check_url_accessibility(self, url: str) -> dict:
        """检查单个URL的可访问性"""
        result = {
            "url": url,
            "accessible": False,
            "status_code": None,
            "response_time": None,
            "error": None,
            "server_info": {},
            "ssl_info": {},
            "content_type": None,
            "content_length": 0,
            "redirect_chain": []
        }

        try:
            start_time = time.time()

            # 尝试HTTP连接
            response = self.session.get(url, allow_redirects=True, verify=False)
            end_time = time.time()

            result.update({
                "accessible": True,
                "status_code": response.status_code,
                "response_time": round((end_time - start_time) * 1000, 2),  # 毫秒
                "content_type": response.headers.get('content-type', ''),
                "content_length": len(response.content),
                "redirect_chain": [r.url for r in response.history] + [response.url]
            })

            # 获取服务器信息
            result["server_info"] = {
                "server": response.headers.get('server', ''),
                "x_powered_by": response.headers.get('x-powered-by', ''),
                "cache_control": response.headers.get('cache-control', ''),
                "content_encoding": response.headers.get('content-encoding', '')
            }

            # 获取SSL信息（如果是HTTPS）
            if url.startswith('https://'):
                try:
                    parsed_url = urlparse(url)
                    context = ssl.create_default_context()
                    with socket.create_connection((parsed_url.hostname, parsed_url.port or 443), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=parsed_url.hostname) as ssock:
                            cert = ssock.getpeercert()
                            result["ssl_info"] = {
                                "version": ssock.version(),
                                "cipher": ssock.cipher(),
                                "cert_subject": dict(x[0] for x in cert.get('subject', [])),
                                "cert_issuer": dict(x[0] for x in cert.get('issuer', [])),
                                "cert_not_before": cert.get('notBefore', ''),
                                "cert_not_after": cert.get('notAfter', '')
                            }
                except Exception as ssl_error:
                    result["ssl_info"]["error"] = str(ssl_error)

        except requests.exceptions.RequestException as e:
            result["error"] = str(e)
            result["response_time"] = None
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def check_target_accessibility(self, target: dict) -> dict:
        """检查目标及其备份URL的可访问性"""
        logger.info(f"检查目标: {target['name']} - {target['url']}")

        results = {
            "target": target,
            "primary_check": self.check_url_accessibility(target["url"]),
            "backup_checks": [],
            "overall_accessible": False,
            "best_url": None,
            "check_time": datetime.now().isoformat()
        }

        # 检查主URL
        if results["primary_check"]["accessible"]:
            results["overall_accessible"] = True
            results["best_url"] = target["url"]
            logger.info(f"✅ 主URL可访问: {target['url']}")
        else:
            logger.warning(f"❌ 主URL不可访问: {target['url']} - {results['primary_check'].get('error', 'Unknown error')}")

        # 检查备份URL
        for backup_url in target.get("backup_urls", []):
            backup_result = self.check_url_accessibility(backup_url)
            results["backup_checks"].append(backup_result)

            if backup_result["accessible"]:
                results["overall_accessible"] = True
                if not results["best_url"]:
                    results["best_url"] = backup_url
                logger.info(f"✅ 备份URL可访问: {backup_url}")
            else:
                logger.warning(f"❌ 备份URL不可访问: {backup_url} - {backup_result.get('error', 'Unknown error')}")

        return results

    def check_all_targets(self, max_workers: int = 5) -> dict:
        """检查所有目标的可访问性"""
        logger.info(f"开始检查 {len(self.logistics_targets)} 个越南快递物流站点的可访问性")

        results = {
            "check_time": datetime.now().isoformat(),
            "total_targets": len(self.logistics_targets),
            "accessible_targets": [],
            "inaccessible_targets": [],
            "summary": {},
            "detailed_results": []
        }

        # 并发检查
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_target = {executor.submit(self.check_target_accessibility, target): target for target in self.logistics_targets}

            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results["detailed_results"].append(result)

                    if result["overall_accessible"]:
                        results["accessible_targets"].append(result)
                        logger.info(f"✅ 目标可访问: {target['name']}")
                    else:
                        results["inaccessible_targets"].append(result)
                        logger.warning(f"❌ 目标不可访问: {target['name']}")

                except Exception as e:
                    logger.error(f"检查目标时出错 {target['name']}: {e}")
                    results["inaccessible_targets"].append({
                        "target": target,
                        "error": str(e),
                        "overall_accessible": False
                    })

        # 生成统计摘要
        results["summary"] = {
            "total_targets": len(self.logistics_targets),
            "accessible_count": len(results["accessible_targets"]),
            "inaccessible_count": len(results["inaccessible_targets"]),
            "accessibility_rate": round(len(results["accessible_targets"]) / len(self.logistics_targets) * 100, 2),
            "average_response_time": self._calculate_average_response_time(results["accessible_targets"])
        }

        return results

    def _calculate_average_response_time(self, accessible_targets: list) -> float:
        """计算平均响应时间"""
        if not accessible_targets:
            return 0.0

        total_time = 0
        count = 0

        for target in accessible_targets:
            if target["primary_check"]["accessible"]:
                total_time += target["primary_check"]["response_time"]
                count += 1

            for backup in target["backup_checks"]:
                if backup["accessible"]:
                    total_time += backup["response_time"]
                    count += 1

        return round(total_time / count, 2) if count > 0 else 0.0

    def generate_accessibility_report(self, results: dict) -> str:
        """生成可访问性检查报告"""
        report = f"""
# 越南快递物流站点可访问性检查报告
**检查时间**: {results['check_time']}
**检查工具**: Dragon-V Triple Bot v3.2.0 可访问性检查器

---

## 📊 检查摘要

- **总目标数量**: {results['summary']['total_targets']}
- **可访问目标**: {results['summary']['accessible_count']}
- **不可访问目标**: {results['summary']['inaccessible_count']}
- **可访问率**: {results['summary']['accessibility_rate']}%
- **平均响应时间**: {results['summary']['average_response_time']}ms

---

## ✅ 可访问的目标

以下目标可以进行安全扫描:

"""

        for target in results["accessible_targets"]:
            primary = target["primary_check"]
            if primary["accessible"]:
                best_url = target["target"]["url"]
                response_time = primary["response_time"]
                status_code = primary["status_code"]
            else:
                # 查找可访问的备份URL
                for backup in target["backup_checks"]:
                    if backup["accessible"]:
                        best_url = backup["url"]
                        response_time = backup["response_time"]
                        status_code = backup["status_code"]
                        break

            report += f"""
### {target['target']['name']}

- **最佳URL**: {best_url}
- **状态码**: {status_code}
- **响应时间**: {response_time}ms
- **类型**: {target['target']['type']}
- **优先级**: {target['target']['priority']}

"""

        report += f"""
## ❌ 不可访问的目标

以下目标当前无法访问:

"""

        for target in results["inaccessible_targets"]:
            error = target.get("error", "Unknown error")
            report += f"""
### {target['target']['name']}

- **URL**: {target['target']['url']}
- **错误**: {error}
- **类型**: {target['target']['type']}
- **优先级**: {target['target']['priority']}

"""

        report += f"""
## 🎯 扫描建议

### 推荐扫描目标 (按优先级排序)

1. **高优先级** (响应快, 稳定):
"""

        # 按优先级和响应时间排序可访问目标
        sorted_targets = sorted(
            [t for t in results["accessible_targets"] if t["primary_check"]["accessible"]],
            key=lambda x: (x["target"]["priority"], x["primary_check"]["response_time"])
        )

        for i, target in enumerate(sorted_targets[:5], 1):
            report += f"""
   {i}. {target['target']['name']} - {target['target']['url']} ({target['primary_check']['response_time']}ms)
"""

        report += f"""

### 扫描执行建议

1. **首选目标**: 选择响应时间 < 3000ms 的目标
2. **避开高峰**: 避开越南时间 9:00-17:00 业务高峰
3. **分批执行**: 一次扫描1-2个目标，避免集中访问
4. **监控影响**: 实时监控扫描对目标系统的影响

### 下一步行动

1. **联系授权**: 向可访问目标发送扫描授权申请
2. **准备扫描**: 配置扫描参数和时间窗口
3. **执行扫描**: 按优先级顺序执行安全扫描
4. **分析结果**: 生成详细的安全评估报告

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**生成工具**: Dragon-V Triple Bot v3.2.0
**建议更新**: 每周重新检查可访问性

> 💡 **提醒**: 网站可访问性可能随时变化，建议在执行扫描前重新验证目标可访问性。
        """

        return report.strip()

def main():
    """主函数 - 执行越南物流站点可访问性检查"""
    print("=== 越南快递物流站点可访问性检查 ===")
    print("检查工具: Dragon-V Triple Bot v3.2.0")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    checker = VietnamLogisticsAccessibilityChecker()

    print(f"\n开始检查 {len(checker.logistics_targets)} 个目标...")
    results = checker.check_all_targets(max_workers=3)

    print(f"\n=== 检查完成 ===")
    print(f"总目标数: {results['summary']['total_targets']}")
    print(f"可访问: {results['summary']['accessible_count']} 个 ({results['summary']['accessibility_rate']}%)")
    print(f"不可访问: {results['summary']['inaccessible_count']} 个")
    print(f"平均响应时间: {results['summary']['average_response_time']}ms")

    # 显示可访问的目标
    print(f"\n=== 可访问的目标 (推荐扫描) ===")
    for i, target in enumerate(results["accessible_targets"], 1):
        target_info = target["target"]
        if target["primary_check"]["accessible"]:
            url = target["primary_check"]["url"]
            response_time = target["primary_check"]["response_time"]
        else:
            # 找到第一个可访问的备份URL
            url = None
            response_time = None
            for backup in target["backup_checks"]:
                if backup["accessible"]:
                    url = backup["url"]
                    response_time = backup["response_time"]
                    break

        if url:
            print(f"{i:2d}. {target_info['name']}")
            print(f"    URL: {url}")
            print(f"    响应时间: {response_time}ms")
            print(f"    类型: {target_info['type']}")
            print()

    # 生成报告
    report = checker.generate_accessibility_report(results)
    report_file = f"vietnam_logistics_accessibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"=== 详细报告已保存 ===")
    print(f"报告文件: {report_file}")
    print(f"共发现 {len(results['accessible_targets'])} 个可扫描的目标")

    # 给出建议
    if results["accessible_targets"]:
        print(f"\n=== 扫描建议 ===")
        print("✅ 推荐开始联系以下目标申请扫描授权:")
        top_targets = sorted(
            [t for t in results["accessible_targets"] if t["primary_check"]["accessible"]],
            key=lambda x: x["target"]["priority"]
        )[:3]

        for i, target in enumerate(top_targets, 1):
            print(f"  {i}. {target['target']['name']} - {target['target']['url']}")
    else:
        print(f"\n⚠️  当前没有可访问的目标，建议:")
        print("  1. 稍后重新检查")
        print("  2. 检查网络连接")
        print("  3. 考虑其他目标")

if __name__ == "__main__":
    main()