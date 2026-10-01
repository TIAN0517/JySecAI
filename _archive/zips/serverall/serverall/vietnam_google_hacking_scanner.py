#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南Google Hacking批量扫描器
Vietnam Google Hacking Bulk Scanner

专门使用Google Hacking语法搜索越南物流快递电商系统
并自动验证发现的系统

支持的越南语关键字:
- 物流: logistics, vận chuyển, giao hàng
- 快递: express, nhanh, chuyển phát nhanh
- 电商: thương mại điện tử, mua sắm online
- 订单: đơn hàng, order, đặt hàng

Google Hacking语法:
- site:vn - 限制越南域名
- inurl:admin - 查找管理后台
- intitle:"dashboard" - 查找仪表板
- filetype:json - 查找JSON文件
- inurl:api - 查找API端点
"""

import requests
import json
import time
import re
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import csv
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_google_hacking.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vietnam_google_hacking")

@dataclass
class VietnamTarget:
    """越南目标信息"""
    url: str
    title: str
    system_type: str
    keywords: List[str]
    vulnerability_indicators: List[str]
    confidence: float
    discovered_at: str

class VietnamGoogleHackingScanner:
    """越南Google Hacking扫描器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 越南语关键字库
        self.vietnam_keywords = {
            # 物流快递
            "logistics": [
                "vận chuyển", "logistics", "giao hàng", "chuyển phát",
                "vận tải", "logistic", "shipping", "delivery",
                "giao hàng nhanh", "chuyển phát nhanh", "vận chuyển hàng hóa"
            ],

            # 电商平台
            "ecommerce": [
                "thương mại điện tử", "mua sắm online", "cửa hàng online",
                "sàn thương mại", "đặt hàng online", "mua bán online",
                "shopping online", "e-commerce", "cửa hàng", "sản phẩm"
            ],

            # 订单系统
            "orders": [
                "đơn hàng", "order", "đặt hàng", "quản lý đơn hàng",
                "chi tiết đơn hàng", "tracking đơn hàng", "xử lý đơn hàng",
                "order management", "order processing", "order tracking"
            ],

            # 支付系统
            "payment": [
                "thanh toán", "payment", "thanh toán online", "ví điện tử",
                "chuyển khoản", "thanh toán an toàn", "cổng thanh toán",
                "payment gateway", "e-wallet", "momo", "zalopay", "vnpay"
            ],

            # 管理后台
            "admin": [
                "admin", "dashboard", "quản trị", "quản lý",
                "control panel", "backend", "admin panel",
                "hệ thống quản lý", "trang quản trị"
            ]
        }

        # Google Hacking查询模板
        self.google_dorks = [
            # 越南域名 + 管理后台
            "site:.vn inurl:admin",
            "site:.vn inurl:dashboard",
            "site:.vn intitle:\"admin panel\"",
            "site:.vn intitle:\"dashboard\"",

            # 越南物流系统
            "site:.vn inurl:vận chuyển",
            "site:.vn inurl:giao hàng",
            "site:.vn inurl:tracking",
            "site:.vn inurl:shipment",
            "site:.vn intitle:\"vận chuyển\"",
            "site:.vn intitle:\"giao hàng\"",

            # 越南电商系统
            "site:.vn inurl:sản phẩm",
            "site:.vn inurl:đơn hàng",
            "site:.vn inurl:giỏ hàng",
            "site:.vn inurl:thanh toán",
            "site:.vn intitle:\"thương mại điện tử\"",
            "site:.vn intitle:\"mua sắm online\"",

            # API端点
            "site:.vn inurl:api",
            "site:.vn inurl:api/v1",
            "site:.vn inurl:api/v2",
            "site:.vn filetype:json inurl:api",

            # 配置文件
            "site:.vn filetype:json",
            "site:.vn filetype:config",
            "site:.vn filetype:env",
            "site:.vn filetype:sql",
            "site:.vn filetype:xml",

            # 技术栈标识
            "site:.vn \"Powered by\"",
            "site:.vn \"Developed by\"",
            "site:.vn inurl:wp-admin",
            "site:.vn inurl:wp-content",
            "site:.vn inurl:magento",
            "site:.vn inurl:prestashop",

            # 越南特定系统
            "site:.vn \"Shopee\"",
            "site:.vn \"Lazada\"",
            "site:.vn \"Tiki\"",
            "site:.vn \"Sendo\"",
            "site:.vn \"VNPost\"",
            "site:.vn \"Viettel Post\"",
            "site:.vn \"Giao Hàng Nhanh\"",
            "site:.vn \"MoMo\"",
            "site:.vn \"ZaloPay\"",

            # 漏洞指示器
            "site:.vn \"Error establishing database connection\"",
            "site:.vn \"Warning: mysql\"",
            "site:.vn \"Fatal error\"",
            "site:.vn inurl:phpinfo.php",
            "site:.vn intitle:\"Index of\"",
            "site:.vn intitle:\"phpMyAdmin\""
        ]

    def search_google_dorks(self, query: str, max_results: int = 10) -> List[str]:
        """
        使用Google Hacking搜索 (模拟实现)
        注意: 实际使用需要Google API或其他搜索引擎API
        """
        logger.info(f"🔍 搜索查询: {query}")

        # 模拟搜索结果 (实际应用中需要调用真实搜索API)
        mock_results = []

        # 根据查询类型生成模拟结果
        if "admin" in query.lower():
            mock_results.extend([
                "https://example-vn1.vn/admin",
                "https://logistics-vn.vn/dashboard",
                "https://shop-vn.vn/admin/login"
            ])
        elif "vận chuyển" in query or "giao hàng" in query:
            mock_results.extend([
                "https://vanchuyen-vn.vn",
                "https://giaohang-vn.vn/tracking",
                "https://logistics-vn.vn/shipment"
            ])
        elif "api" in query.lower():
            mock_results.extend([
                "https://api-vn.vn/v1/products",
                "https://shop-vn.vn/api/orders",
                "https://payment-vn.vn/api/transaction"
            ])
        else:
            # 通用越南网站
            mock_results.extend([
                "https://website1.vn",
                "https://store2.vn",
                "https://service3.vn"
            ])

        # 限制结果数量
        return mock_results[:max_results]

    def identify_system_type(self, url: str, content: str = "") -> str:
        """识别系统类型"""
        url_lower = url.lower()
        content_lower = content.lower()

        # 检查物流快递指标
        logistics_indicators = [
            "vận chuyển", "giao hàng", "chuyển phát", "shipping",
            "delivery", "logistics", "tracking", "shipment"
        ]

        # 检查电商指标
        ecommerce_indicators = [
            "sản phẩm", "giỏ hàng", "đơn hàng", "thanh toán",
            "product", "cart", "order", "payment", "shopping"
        ]

        # 检查支付指标
        payment_indicators = [
            "thanh toán", "payment", "chuyển khoản", "e-wallet",
            "momo", "zalopay", "vnpay", "payment gateway"
        ]

        # 检查管理后台指标
        admin_indicators = [
            "admin", "dashboard", "quản trị", "quản lý",
            "control panel", "backend", "admin panel"
        ]

        # 计算匹配分数
        logistics_score = sum(1 for indicator in logistics_indicators
                            if indicator in url_lower or indicator in content_lower)
        ecommerce_score = sum(1 for indicator in ecommerce_indicators
                            if indicator in url_lower or indicator in content_lower)
        payment_score = sum(1 for indicator in payment_indicators
                          if indicator in url_lower or indicator in content_lower)
        admin_score = sum(1 for indicator in admin_indicators
                       if indicator in url_lower or indicator in content_lower)

        # 确定主要类型
        scores = {
            "logistics": logistics_score,
            "ecommerce": ecommerce_score,
            "payment": payment_score,
            "admin": admin_score
        }

        max_score = max(scores.values())
        if max_score == 0:
            return "unknown"

        return max(scores, key=scores.get)

    def detect_vulnerability_indicators(self, url: str, content: str) -> List[str]:
        """检测漏洞指示器"""
        indicators = []
        content_lower = content.lower()

        # 错误信息指示器
        error_patterns = [
            (r"mysql.*error", "MySQL数据库错误"),
            (r"warning.*mysql", "MySQL警告信息"),
            (r"fatal error", "致命PHP错误"),
            (r"notice.*undefined", "PHP未定义变量"),
            (r"error establishing database connection", "数据库连接错误"),
            (r"sql syntax.*error", "SQL语法错误")
        ]

        # 技术栈指示器
        tech_patterns = [
            (r"wp-content", "WordPress"),
            (r"magento", "Magento"),
            (r"prestashop", "PrestaShop"),
            (r"joomla", "Joomla"),
            (r"drupal", "Drupal"),
            (r"phpinfo\(\)", "phpinfo信息泄露"),
            (r"apache/[0-9.]+", "Apache服务器"),
            (r"nginx/[0-9.]+", "Nginx服务器")
        ]

        # 敏感文件指示器
        file_patterns = [
            (r"index of", "目录列表"),
            (r"phpmyadmin", "phpMyAdmin"),
            (r"\.env$", "环境配置文件"),
            (r"\.sql$", "SQL文件"),
            (r"\.backup$", "备份文件"),
            (r"config\.php", "PHP配置文件")
        ]

        # 检查所有模式
        all_patterns = error_patterns + tech_patterns + file_patterns
        for pattern, description in all_patterns:
            if re.search(pattern, content_lower):
                indicators.append(description)

        return indicators

    def verify_target(self, url: str) -> Optional[VietnamTarget]:
        """验证目标"""
        try:
            logger.info(f"🔍 验证目标: {url}")

            # 发送请求
            response = self.session.get(url, timeout=10, verify=False)
            if response.status_code != 200:
                return None

            content = response.text

            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else ""

            # 识别系统类型
            system_type = self.identify_system_type(url, content)

            # 检测漏洞指示器
            vuln_indicators = self.detect_vulnerability_indicators(url, content)

            # 计算置信度
            confidence = self.calculate_confidence(url, content, system_type, vuln_indicators)

            # 提取关键字
            keywords = self.extract_keywords(url, content)

            return VietnamTarget(
                url=url,
                title=title,
                system_type=system_type,
                keywords=keywords,
                vulnerability_indicators=vuln_indicators,
                confidence=confidence,
                discovered_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"验证目标失败 {url}: {e}")
            return None

    def calculate_confidence(self, url: str, content: str, system_type: str, indicators: List[str]) -> float:
        """计算置信度"""
        confidence = 0.0

        # URL匹配 (30%)
        if ".vn" in url:
            confidence += 0.3

        # 系统类型识别 (20%)
        if system_type != "unknown":
            confidence += 0.2

        # 越南语内容 (25%)
        vietnamese_chars = len(re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', content))
        if vietnamese_chars > 10:
            confidence += 0.25

        # 漏洞指示器 (25%)
        if indicators:
            confidence += min(0.25, len(indicators) * 0.05)

        return min(confidence, 1.0)

    def extract_keywords(self, url: str, content: str) -> List[str]:
        """提取关键字"""
        keywords = []
        content_lower = content.lower()
        url_lower = url.lower()

        for category, words in self.vietnam_keywords.items():
            for word in words:
                if word in url_lower or word in content_lower:
                    keywords.append(word)

        return list(set(keywords))  # 去重

    async def bulk_scan(self, max_queries: int = 20, max_results_per_query: int = 5) -> List[VietnamTarget]:
        """批量扫描"""
        logger.info(f"🚀 开始批量Google Hacking扫描...")
        logger.info(f"   查询数量: {max_queries}")
        logger.info(f"   每查询结果: {max_results_per_query}")

        all_targets = []
        processed_urls = set()

        # 限制查询数量
        queries_to_use = self.google_dorks[:max_queries]

        for i, query in enumerate(queries_to_use, 1):
            logger.info(f"📡 执行查询 {i}/{len(queries_to_use)}: {query}")

            # 搜索URL
            urls = self.search_google_dorks(query, max_results_per_query)

            # 验证每个URL
            for url in urls:
                if url not in processed_urls:
                    target = self.verify_target(url)
                    if target and target.confidence > 0.3:
                        all_targets.append(target)
                        processed_urls.add(url)
                        logger.info(f"   ✅ 发现目标: {url} ({target.system_type}, {target.confidence:.2f})")

            # 添加延迟避免请求过于频繁
            if i < len(queries_to_use):
                await asyncio.sleep(1)

        logger.info(f"🎉 扫描完成! 总共发现 {len(all_targets)} 个有效目标")
        return all_targets

    def export_results(self, targets: List[VietnamTarget], filename: str = None) -> str:
        """导出结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vietnam_google_hacking_results_{timestamp}.csv"

        logger.info(f"📄 导出结果到: {filename}")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'url', 'title', 'system_type', 'keywords',
                'vulnerability_indicators', 'confidence', 'discovered_at'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for target in targets:
                writer.writerow({
                    'url': target.url,
                    'title': target.title,
                    'system_type': target.system_type,
                    'keywords': ', '.join(target.keywords),
                    'vulnerability_indicators': ', '.join(target.vulnerability_indicators),
                    'confidence': f"{target.confidence:.2f}",
                    'discovered_at': target.discovered_at
                })

        # 同时导出JSON格式
        json_filename = filename.replace('.csv', '.json')
        results_data = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'total_targets': len(targets),
                'queries_used': len(self.google_dorks)
            },
            'targets': [
                {
                    'url': t.url,
                    'title': t.title,
                    'system_type': t.system_type,
                    'keywords': t.keywords,
                    'vulnerability_indicators': t.vulnerability_indicators,
                    'confidence': t.confidence,
                    'discovered_at': t.discovered_at
                }
                for t in targets
            ]
        }

        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(results_data, jsonfile, ensure_ascii=False, indent=2)

        logger.info(f"📊 同时导出JSON到: {json_filename}")
        return filename

    def generate_summary_report(self, targets: List[VietnamTarget]) -> str:
        """生成总结报告"""
        if not targets:
            return "未发现任何目标"

        # 统计信息
        total_targets = len(targets)
        system_types = {}
        vulnerability_count = 0
        high_confidence_count = 0

        for target in targets:
            # 系统类型统计
            system_types[target.system_type] = system_types.get(target.system_type, 0) + 1

            # 漏洞指示器统计
            if target.vulnerability_indicators:
                vulnerability_count += 1

            # 高置信度统计
            if target.confidence > 0.7:
                high_confidence_count += 1

        report = f"""
越南Google Hacking扫描报告
=====================================

扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总目标数: {total_targets}
高置信度目标: {high_confidence_count}
存在漏洞指示器: {vulnerability_count}

系统类型分布:
"""

        for system_type, count in system_types.items():
            percentage = (count / total_targets) * 100
            report += f"  {system_type}: {count} ({percentage:.1f}%)\n"

        report += "\n高价值目标 (置信度 > 0.8):\n"
        high_value_targets = [t for t in targets if t.confidence > 0.8]

        for target in high_value_targets[:10]:  # 显示前10个
            report += f"  • {target.url}\n"
            report += f"    类型: {target.system_type}\n"
            report += f"    置信度: {target.confidence:.2f}\n"
            if target.vulnerability_indicators:
                report += f"    漏洞指示: {', '.join(target.vulnerability_indicators[:3])}\n"
            report += "\n"

        if len(high_value_targets) > 10:
            report += f"  ... 还有 {len(high_value_targets) - 10} 个高价值目标\n"

        return report

async def main():
    """主程序"""
    print("🔍 越南Google Hacking批量扫描器")
    print("🎯 专门搜索越南物流快递电商系统")
    print("="*50)

    scanner = VietnamGoogleHackingScanner()

    # 用户选择
    print("\n📋 扫描选项:")
    print("1. 快速扫描 (10个查询)")
    print("2. 标准扫描 (20个查询)")
    print("3. 深度扫描 (50个查询)")
    print("4. 自定义扫描")

    choice = input("\n请选择扫描模式 (1-4): ").strip()

    max_queries = 20
    max_results = 5

    if choice == '1':
        max_queries = 10
    elif choice == '2':
        max_queries = 20
    elif choice == '3':
        max_queries = 50
    elif choice == '4':
        try:
            max_queries = int(input("查询数量 (建议10-50): "))
            max_results = int(input("每查询结果数 (建议5-10): "))
        except ValueError:
            print("输入无效，使用默认值")

    print(f"\n🚀 开始扫描 (查询: {max_queries}, 结果/查询: {max_results})")

    # 执行扫描
    targets = await scanner.bulk_scan(max_queries, max_results)

    if targets:
        # 生成报告
        report = scanner.generate_summary_report(targets)
        print("\n" + report)

        # 导出结果
        filename = scanner.export_results(targets)
        print(f"\n📄 结果已导出到: {filename}")

        # 显示统计
        print(f"\n📊 扫描统计:")
        print(f"   总目标: {len(targets)}")
        print(f"   高置信度: {len([t for t in targets if t.confidence > 0.7])}")
        print(f"   有漏洞指示: {len([t for t in targets if t.vulnerability_indicators])}")

    else:
        print("\n❌ 未发现任何目标")

if __name__ == "__main__":
    asyncio.run(main())