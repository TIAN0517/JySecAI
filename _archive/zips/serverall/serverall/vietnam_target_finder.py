#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南目标发现器 - 可访问目标验证
Vietnam Target Finder - Accessible Target Verification

直接运行，只返回能够访问的越南物流电商目标
"""

import requests
import json
import time
import csv
from datetime import datetime
from urllib.parse import urljoin, urlparse
import concurrent.futures
import threading

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class VietnamTargetFinder:
    """越南目标发现器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.session.verify = False
        self.accessible_targets = []
        self.lock = threading.Lock()

    def get_test_urls(self):
        """获取测试URL列表"""
        # 越南物流快递系统
        logistics_urls = [
            "https://vnpost.vn",
            "https://viettelpost.vn",
            "https://giaohangnhanh.vn",
            "https://ghtk.vn",
            "https://j&texpress.vn",
            "https://ahamove.com",
            "https://ghtk.vn",
            "https://vietnam-post.vn",
            "https://shipchung.vn",
            "https://boxme.vn",
            "https://logistics.viettel.vn",
            "https://vtp.vn",
            "https://donhang.ghn.vn",
            "https://seller.ghn.vn"
        ]

        # 越南电商平台
        ecommerce_urls = [
            "https://shopee.vn",
            "https://lazada.vn",
            "https://tiki.vn",
            "https://sendo.vn",
            "https://nguyenkim.vn",
            "https://fptshop.com.vn",
            "https://thegioididong.com",
            "https://dienmayxanh.com",
            "https://vatgia.com",
            "https://chotot.vn",
            "https://adayroi.com",
            "https://tiki.vn",
            "https://hasaki.vn",
            "https://guardian.vn",
            "https://watsons.vn"
        ]

        # 越南支付系统
        payment_urls = [
            "https://momo.vn",
            "https://zalopay.vn",
            "https://vnpay.vn",
            "https://onepay.vn",
            "https://nganluong.vn",
            "https://payoo.vn",
            "https://123pay.vn",
            "https://epay.vn"
        ]

        return {
            "logistics": logistics_urls,
            "ecommerce": ecommerce_urls,
            "payment": payment_urls
        }

    def check_accessibility(self, url, category):
        """检查URL可访问性"""
        try:
            # 测试主页面
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text

                # 识别系统类型
                system_info = self.identify_system(url, content)

                # 检测管理后台
                admin_urls = self.find_admin_urls(url)

                # 检测API端点
                api_urls = self.find_api_urls(url)

                target_info = {
                    "url": url,
                    "category": category,
                    "status_code": response.status_code,
                    "title": self.extract_title(content),
                    "system_type": system_info["type"],
                    "platform": system_info["platform"],
                    "vietnam_content": system_info["vietnam_content"],
                    "admin_urls": admin_urls,
                    "api_urls": api_urls,
                    "response_time": response.elapsed.total_seconds(),
                    "accessible": True,
                    "checked_at": datetime.now().isoformat()
                }

                with self.lock:
                    self.accessible_targets.append(target_info)

                print(f"[OK] {url} ({category}) - {system_info['type']}")
                return True

        except requests.exceptions.RequestException as e:
            print(f"[FAIL] {url} - {str(e)[:50]}")
            return False

    def identify_system(self, url, content):
        """识别系统信息"""
        content_lower = content.lower()
        url_lower = url.lower()

        # 检测平台
        platform = "unknown"
        if "magento" in content_lower:
            platform = "magento"
        elif "woocommerce" in content_lower:
            platform = "woocommerce"
        elif "shopify" in content_lower:
            platform = "shopify"
        elif "wordpress" in content_lower:
            platform = "wordpress"
        elif "laravel" in content_lower:
            platform = "laravel"
        elif "django" in content_lower:
            platform = "django"
        elif "node.js" in content_lower or "nodejs" in content_lower:
            platform = "nodejs"
        elif "react" in content_lower:
            platform = "react"
        elif "vue" in content_lower:
            platform = "vue"

        # 检测系统类型
        system_type = "unknown"

        # 物流快递关键词
        logistics_keywords = [
            "vận chuyển", "giao hàng", "chuyển phát", "tracking",
            "shipment", "delivery", "shipping", "logistics",
            "theo dõi", "đơn hàng", "kiểm tra"
        ]

        # 电商关键词
        ecommerce_keywords = [
            "sản phẩm", "giỏ hàng", "mua sắm", "thanh toán",
            "product", "cart", "shopping", "payment", "order"
        ]

        # 支付关键词
        payment_keywords = [
            "thanh toán", "payment", "chuyển khoản", "ví điện tử",
            "e-wallet", "transaction", "payment gateway"
        ]

        # 计算匹配分数
        logistics_score = sum(1 for kw in logistics_keywords if kw in content_lower or kw in url_lower)
        ecommerce_score = sum(1 for kw in ecommerce_keywords if kw in content_lower or kw in url_lower)
        payment_score = sum(1 for kw in payment_keywords if kw in content_lower or kw in url_lower)

        if logistics_score > ecommerce_score and logistics_score > payment_score:
            system_type = "logistics"
        elif ecommerce_score > payment_score:
            system_type = "ecommerce"
        elif payment_score > 0:
            system_type = "payment"

        # 检测越南内容
        vietnamese_chars = len([
            c for c in content if ord(c) >= 0x0900 and ord(c) <= 0x097F or
            c in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ"
        ])

        vietnam_content = vietnamese_chars > 50

        return {
            "type": system_type,
            "platform": platform,
            "vietnam_content": vietnam_content,
            "content_length": len(content)
        }

    def extract_title(self, content):
        """提取页面标题"""
        import re
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            return title[:100]  # 限制长度
        return "No Title"

    def find_admin_urls(self, base_url):
        """查找管理后台URL"""
        admin_paths = [
            "/admin",
            "/admin/login",
            "/administrator",
            "/wp-admin",
            "/wp-login.php",
            "/login",
            "/dashboard",
            "/backend",
            "/control",
            "/manage",
            "/panel",
            "/cms",
            "/quan-tri",
            "/quan-ly"
        ]

        found_admins = []

        for path in admin_paths:
            try:
                admin_url = urljoin(base_url, path)
                response = self.session.get(admin_url, timeout=5)
                if response.status_code in [200, 401, 403]:  # 存在但需要认证
                    found_admins.append({
                        "url": admin_url,
                        "status": response.status_code,
                        "title": self.extract_title(response.text)
                    })
            except:
                pass

        return found_admins

    def find_api_urls(self, base_url):
        """查找API端点URL"""
        api_paths = [
            "/api",
            "/api/v1",
            "/api/v2",
            "/rest",
            "/rest/v1",
            "/webapi",
            "/service",
            "/services",
            "/json",
            "/ajax"
        ]

        found_apis = []

        for path in api_paths:
            try:
                api_url = urljoin(base_url, path)
                response = self.session.get(api_url, timeout=5)
                if response.status_code == 200:
                    found_apis.append({
                        "url": api_url,
                        "status": response.status_code,
                        "content_type": response.headers.get('content-type', '')
                    })
            except:
                pass

        return found_apis

    def scan_all_targets(self, max_workers=10):
        """扫描所有目标"""
        print("越南目标发现器启动")
        print("专门扫描物流、电商、支付系统")
        print("=" * 50)

        urls_by_category = self.get_test_urls()
        all_urls = []

        for category, urls in urls_by_category.items():
            print(f"\n{category.upper()} 系统 ({len(urls)} 个目标)")
            for url in urls:
                all_urls.append((url, category))

        print(f"\n开始扫描 {len(all_urls)} 个目标...")
        print(f"使用 {max_workers} 个并发线程")
        print("-" * 50)

        # 并发扫描
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for url, category in all_urls:
                future = executor.submit(self.check_accessibility, url, category)
                futures.append(future)

            # 等待所有任务完成
            concurrent.futures.wait(futures)

        print(f"\n扫描完成!")
        print(f"统计结果:")
        print(f"   总目标数: {len(all_urls)}")
        print(f"   可访问: {len(self.accessible_targets)}")

        # 分类统计
        categories = {}
        for target in self.accessible_targets:
            cat = target['category']
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in categories.items():
            print(f"   {cat}: {count} 个")

        return self.accessible_targets

    def export_results(self, filename=None):
        """导出结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vietnam_accessible_targets_{timestamp}.csv"

        print(f"\n导出结果到: {filename}")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'url', 'category', 'status_code', 'title', 'system_type',
                'platform', 'vietnam_content', 'response_time', 'admin_count',
                'api_count', 'checked_at'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for target in self.accessible_targets:
                writer.writerow({
                    'url': target['url'],
                    'category': target['category'],
                    'status_code': target['status_code'],
                    'title': target['title'],
                    'system_type': target['system_type'],
                    'platform': target['platform'],
                    'vietnam_content': target['vietnam_content'],
                    'response_time': f"{target['response_time']:.3f}s",
                    'admin_count': len(target['admin_urls']),
                    'api_count': len(target['api_urls']),
                    'checked_at': target['checked_at']
                })

        # 同时导出详细信息JSON
        json_filename = filename.replace('.csv', '.json')
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.accessible_targets, jsonfile, ensure_ascii=False, indent=2)

        return filename

    def show_detailed_results(self):
        """显示详细结果"""
        print("\n详细结果:")
        print("=" * 80)

        # 按类别分组显示
        by_category = {}
        for target in self.accessible_targets:
            cat = target['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(target)

        for category, targets in by_category.items():
            print(f"\n{category.upper()} 系统 ({len(targets)} 个)")
            print("-" * 60)

            for i, target in enumerate(targets, 1):
                print(f"{i:2d}. {target['url']}")
                print(f"    标题: {target['title']}")
                print(f"    系统: {target['system_type']} ({target['platform']})")
                print(f"    越南内容: {'是' if target['vietnam_content'] else '否'}")
                print(f"    响应时间: {target['response_time']:.3f}s")

                if target['admin_urls']:
                    print(f"    管理后台 ({len(target['admin_urls'])} 个):")
                    for admin in target['admin_urls'][:2]:  # 显示前2个
                        print(f"      • {admin['url']} ({admin['status']})")

                if target['api_urls']:
                    print(f"    API端点 ({len(target['api_urls'])} 个):")
                    for api in target['api_urls'][:2]:  # 显示前2个
                        print(f"      • {api['url']} ({api['content_type']})")

                print()

def main():
    """主程序"""
    finder = VietnamTargetFinder()

    # 扫描所有目标
    targets = finder.scan_all_targets(max_workers=15)

    if targets:
        # 显示详细结果
        finder.show_detailed_results()

        # 导出结果
        filename = finder.export_results()

        # 显示高价值目标
        print("\n高价值目标 (有管理后台或API端点):")
        print("=" * 60)

        high_value = [t for t in targets if t['admin_urls'] or t['api_urls']]
        for target in high_value[:10]:  # 显示前10个
            print(f"• {target['url']} ({target['category']})")
            print(f"  系统: {target['system_type']}")
            if target['admin_urls']:
                print(f"  管理后台: {len(target['admin_urls'])} 个")
            if target['api_urls']:
                print(f"  API端点: {len(target['api_urls'])} 个")
            print()

        if len(high_value) > 10:
            print(f"... 还有 {len(high_value) - 10} 个高价值目标")

        print(f"\n总结:")
        print(f"   可访问目标: {len(targets)}")
        print(f"   高价值目标: {len(high_value)}")
        print(f"   结果文件: {filename}")

    else:
        print("\n未发现可访问的目标")

if __name__ == "__main__":
    print("越南目标发现器 - 实时扫描")
    print("只返回能够访问的物流、电商、支付目标")
    print("=" * 60)

    try:
        main()
    except KeyboardInterrupt:
        print("\n扫描被用户中断")
    except Exception as e:
        print(f"\n扫描出错: {e}")