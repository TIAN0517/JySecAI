#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南Google Dorks查询生成器
Vietnam Google Dorks Query Generator

专门生成针对越南物流快递电商系统的Google Hacking查询
包含越南语关键字和技术指纹

支持的目标类型:
- 越南物流快递系统
- 越南电商平台
- 越南支付系统
- 越南订单管理系统
- 越南API端点
- 越南管理后台
"""

import json
import random
from datetime import datetime
from typing import List, Dict, Any

class VietnamGoogleDorksGenerator:
    """越南Google Dorks生成器"""

    def __init__(self):
        # 越南域名
        self.vn_domains = [
            "site:.vn",
            "site:.com.vn",
            "site:.edu.vn",
            "site:.gov.vn",
            "site:.net.vn",
            "site:.org.vn"
        ]

        # 越南语关键字
        self.vn_keywords = {
            # 物流快递
            "logistics": [
                "vận chuyển", "chuyển phát", "giao hàng", "logistics",
                "shipping", "delivery", "vận tải", "vận chuyển hàng hóa",
                "chuyển phát nhanh", "giao hàng nhanh", "dịch vụ vận chuyển",
                "logistic service", "freight", "cargo", "courier"
            ],

            # 电商购物
            "ecommerce": [
                "thương mại điện tử", "mua sắm online", "cửa hàng online",
                "sản phẩm", "giỏ hàng", "đặt hàng", "mua hàng",
                "shopping online", "e-commerce", "online store",
                "cửa hàng", "sản phẩm", "hàng hóa", "bán hàng"
            ],

            # 订单管理
            "orders": [
                "đơn hàng", "order", "đặt hàng", "quản lý đơn hàng",
                "chi tiết đơn hàng", "xử lý đơn hàng", "tracking đơn hàng",
                "order management", "order processing", "order tracking",
                "lịch sử đơn hàng", "trạng thái đơn hàng"
            ],

            # 支付系统
            "payment": [
                "thanh toán", "payment", "thanh toán online", "ví điện tử",
                "chuyển khoản", "thanh toán an toàn", "cổng thanh toán",
                "payment gateway", "e-wallet", "momo", "zalopay", "vnpay",
                "thanh toán VNPay", "ví MoMo", "ZaloPay ví điện tử"
            ],

            # 管理后台
            "admin": [
                "admin", "dashboard", "quản trị", "quản lý",
                "control panel", "backend", "admin panel", "trang quản trị",
                "hệ thống quản lý", "quản trị viên", "admin login"
            ],

            # API端点
            "api": [
                "api", "endpoint", "restful", "web service",
                "application programming interface", "json api"
            ],

            # 跟踪系统
            "tracking": [
                "tracking", "theo dõi", "kiểm tra", "trạng thái",
                "tracking system", "shipment tracking", "delivery tracking",
                "theo dõi đơn hàng", "kiểm tra vận chuyển"
            ]
        }

        # 技术指纹
        self.tech_fingerprints = {
            "platforms": [
                "magento", "prestashop", "woocommerce", "shopify",
                "opencart", "zen cart", "virtuemart", "cs-cart",
                "bigcommerce", "volusion", "3dcart"
            ],

            "frameworks": [
                "wordpress", "joomla", "drupal", "magento",
                "laravel", "codeigniter", "symfony", "yii",
                "django", "flask", "rails", "spring"
            ],

            "servers": [
                "apache", "nginx", "iis", "litespeed",
                "node.js", "tomcat", "jetty", "glassfish"
            ],

            "databases": [
                "mysql", "postgresql", "mongodb", "redis",
                "sql server", "oracle", "sqlite", "cassandra"
            ]
        }

        # 漏洞指示器
        self.vulnerability_indicators = [
            "error establishing database connection",
            "warning: mysql",
            "fatal error",
            "notice: undefined",
            "parse error",
            "syntax error",
            "internal server error",
            "500 internal server error",
            "database error",
            "sql error",
            "connection failed",
            "timeout error"
        ]

        # 敏感文件
        self.sensitive_files = [
            "config.php", "wp-config.php", "database.php",
            ".env", "environment", "settings.php",
            "backup.sql", "dump.sql", "database.sql",
            "admin.php", "login.php", "config.json",
            "phpinfo.php", "test.php", "info.php"
        ]

        # Google Hacking操作符
        self.operators = [
            "site:", "inurl:", "intitle:", "intext:", "filetype:",
            "inurl:", "ext:", "link:", "related:", "cache:",
            "intitle:", "inurl:", "inanchor:", "inurl:"
        ]

    def generate_logistics_dorks(self) -> List[str]:
        """生成物流快递Google Dorks"""
        dorks = []

        # 基础物流系统搜索
        for domain in self.vn_domains[:3]:  # 限制域名数量
            for keyword in self.vn_keywords["logistics"][:5]:
                dorks.append(f"{domain} \"{keyword}\"")

        # 物流管理系统
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:admin {random.choice(self.vn_keywords['logistics'])}",
                f"{domain} inurl:tracking {random.choice(self.vn_keywords['tracking'])}",
                f"{domain} inurl:shipment {random.choice(self.vn_keywords['logistics'])}",
                f"{domain} intitle:\"{random.choice(self.vn_keywords['logistics'])}\""
            ])

        # 物流API端点
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:api {random.choice(self.vn_keywords['tracking'])}",
                f"{domain} inurl:api/v1 tracking",
                f"{domain} filetype:json api {random.choice(self.vn_keywords['logistics'])}"
            ])

        # 物流配置文件
        for domain in self.vn_domains[:1]:
            for file in self.sensitive_files[:3]:
                dorks.append(f"{domain} filetype:php {file} {random.choice(self.vn_keywords['logistics'])}")

        return dorks

    def generate_ecommerce_dorks(self) -> List[str]:
        """生成电商系统Google Dorks"""
        dorks = []

        # 越南电商平台
        for domain in self.vn_domains[:3]:
            for keyword in self.vn_keywords["ecommerce"][:4]:
                dorks.append(f"{domain} \"{keyword}\"")

        # 知名越南电商
        vietnam_brands = ["Shopee", "Lazada", "Tiki", "Sendo", "Nguyen Kim", "FPT Shop"]
        for brand in vietnam_brands:
            dorks.extend([
                f"site:.vn \"{brand}\"",
                f"site:.vn {brand.lower()} inurl:admin",
                f"site:.vn {brand.lower()} inurl:api"
            ])

        # 电商管理后台
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:admin {random.choice(self.vn_keywords['ecommerce'])}",
                f"{domain} inurl:dashboard {random.choice(self.vn_keywords['orders'])}",
                f"{domain} intitle:\"admin\" {random.choice(self.vn_keywords['ecommerce'])}"
            ])

        # 电商API端点
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:api {random.choice(self.vn_keywords['ecommerce'])}",
                f"{domain} inurl:api/v1 {random.choice(self.vn_keywords['orders'])}",
                f"{domain} filetype:json {random.choice(self.vn_keywords['payment'])}"
            ])

        # 购物车和订单
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:cart {random.choice(self.vn_keywords['ecommerce'])}",
                f"{domain} inurl:order {random.choice(self.vn_keywords['orders'])}",
                f"{domain} inurl:checkout {random.choice(self.vn_keywords['payment'])}"
            ])

        return dorks

    def generate_payment_dorks(self) -> List[str]:
        """生成支付系统Google Dorks"""
        dorks = []

        # 越南支付系统
        for domain in self.vn_domains[:3]:
            for keyword in self.vn_keywords["payment"][:4]:
                dorks.append(f"{domain} \"{keyword}\"")

        # 知名支付平台
        payment_brands = ["MoMo", "ZaloPay", "VNPay", "Viettel Pay", "OnePay"]
        for brand in payment_brands:
            dorks.extend([
                f"site:.vn \"{brand}\"",
                f"site:.vn {brand.lower()} inurl:api",
                f"site:.vn {brand.lower()} inurl:payment"
            ])

        # 支付网关
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:payment {random.choice(self.vn_keywords['payment'])}",
                f"{domain} inurl:gateway {random.choice(self.vn_keywords['payment'])}",
                f"{domain} intitle:\"payment\" {random.choice(self.vn_keywords['payment'])}"
            ])

        # 支付API
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:api payment",
                f"{domain} inurl:api/v1 transaction",
                f"{domain} filetype:json payment gateway"
            ])

        return dorks

    def generate_admin_dorks(self) -> List[str]:
        """生成管理后台Google Dorks"""
        dorks = []

        # 越南管理后台
        for domain in self.vn_domains[:3]:
            for keyword in self.vn_keywords["admin"][:4]:
                dorks.append(f"{domain} inurl:admin \"{keyword}\"")

        # 通用管理面板
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:admin",
                f"{domain} inurl:dashboard",
                f"{domain} inurl:login admin",
                f"{domain} intitle:\"admin panel\"",
                f"{domain} intitle:\"dashboard\"",
                f"{domain} intitle:\"login\""
            ])

        # WordPress后台
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:wp-admin",
                f"{domain} inurl:wp-login",
                f"{domain} \"Powered by WordPress\""
            ])

        # Magento后台
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} inurl:magento admin",
                f"{domain} \"Powered by Magento\"",
                f"{domain} inurl:index.php/admin"
            ])

        return dorks

    def generate_api_dorks(self) -> List[str]:
        """生成API端点Google Dorks"""
        dorks = []

        # API端点搜索
        for domain in self.vn_domains[:3]:
            dorks.extend([
                f"{domain} inurl:api",
                f"{domain} inurl:api/v1",
                f"{domain} inurl:api/v2",
                f"{domain} inurl:rest",
                f"{domain} inurl:webhook"
            ])

        # JSON API
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} filetype:json inurl:api",
                f"{domain} filetype:json inurl:v1",
                f"{domain} filetype:json {random.choice(self.vn_keywords['orders'])}"
            ])

        # 特定API类型
        api_types = [
            "products", "orders", "users", "payments", "shipping",
            "tracking", "customers", "categories", "cart", "checkout"
        ]

        for domain in self.vn_domains[:2]:
            for api_type in api_types[:5]:
                dorks.append(f"{domain} inurl:api/{api_type}")

        return dorks

    def generate_vulnerability_dorks(self) -> List[str]:
        """生成漏洞指示器Google Dorks"""
        dorks = []

        # 错误信息
        for domain in self.vn_domains[:2]:
            for indicator in self.vulnerability_indicators[:5]:
                dorks.append(f"{domain} \"{indicator}\"")

        # 敏感文件
        for domain in self.vn_domains[:2]:
            for file in self.sensitive_files[:5]:
                dorks.append(f"{domain} filetype:php {file}")

        # 数据库错误
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} \"mysql error\"",
                f"{domain} \"database error\"",
                f"{domain} \"sql syntax\"",
                f"{domain} \"warning mysql\""
            ])

        # 目录列表
        for domain in self.vn_domains[:2]:
            dorks.extend([
                f"{domain} intitle:\"index of\"",
                f"{domain} intitle:\"directory listing\"",
                f"{domain} inurl:backup"
            ])

        return dorks

    def generate_tech_fingerprint_dorks(self) -> List[str]:
        """生成技术指纹Google Dorks"""
        dorks = []

        # 平台指纹
        for domain in self.vn_domains[:2]:
            for platform in self.tech_fingerprints["platforms"][:5]:
                dorks.append(f"{domain} \"Powered by {platform}\"")
                dorks.append(f"{domain} inurl:{platform}")

        # 框架指纹
        for domain in self.vn_domains[:2]:
            for framework in self.tech_fingerprints["frameworks"][:5]:
                dorks.append(f"{domain} \"Powered by {framework}\"")
                dorks.append(f"{domain} {framework} inurl:admin")

        return dorks

    def generate_comprehensive_dorks(self) -> Dict[str, List[str]]:
        """生成全面的Google Dorks"""
        return {
            "logistics": self.generate_logistics_dorks(),
            "ecommerce": self.generate_ecommerce_dorks(),
            "payment": self.generate_payment_dorks(),
            "admin": self.generate_admin_dorks(),
            "api": self.generate_api_dorks(),
            "vulnerabilities": self.generate_vulnerability_dorks(),
            "tech_fingerprints": self.generate_tech_fingerprint_dorks()
        }

    def generate_custom_dorks(self, keywords: List[str], domain: str = "site:.vn") -> List[str]:
        """生成自定义Google Dorks"""
        dorks = []

        for keyword in keywords:
            dorks.extend([
                f"{domain} \"{keyword}\"",
                f"{domain} inurl:{keyword}",
                f"{domain} intitle:\"{keyword}\"",
                f"{domain} inurl:admin \"{keyword}\"",
                f"{domain} inurl:api \"{keyword}\""
            ])

        return dorks

    def export_dorks(self, dorks: Dict[str, List[str]], filename: str = None) -> str:
        """导出Google Dorks"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vietnam_google_dorks_{timestamp}.json"

        # 统计信息
        total_dorks = sum(len(dork_list) for dork_list in dorks.values())

        export_data = {
            "generated_at": datetime.now().isoformat(),
            "total_dorks": total_dorks,
            "categories": {
                category: len(dork_list)
                for category, dork_list in dorks.items()
            },
            "dorks": dorks
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        # 同时导出文本格式
        text_filename = filename.replace('.json', '.txt')
        with open(text_filename, 'w', encoding='utf-8') as f:
            f.write(f"越南Google Dorks查询集合\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总计查询: {total_dorks}\n")
            f.write("="*60 + "\n\n")

            for category, dork_list in dorks.items():
                f.write(f"【{category.upper()}】({len(dork_list)}个查询)\n")
                f.write("-" * 40 + "\n")
                for dork in dork_list:
                    f.write(f"{dork}\n")
                f.write("\n")

        return filename

    def get_random_dorks(self, count: int = 10) -> List[str]:
        """获取随机Google Dorks"""
        all_dorks = self.generate_comprehensive_dorks()
        flat_dorks = [dork for dork_list in all_dorks.values() for dork in dork_list]
        return random.sample(flat_dorks, min(count, len(flat_dorks)))

def main():
    """主程序"""
    print("越南Google Dorks查询生成器")
    print("专门生成越南物流快递电商系统查询")
    print("="*50)

    generator = VietnamGoogleDorksGenerator()

    print("\n选择生成类型:")
    print("1. 物流快递系统查询")
    print("2. 电商平台查询")
    print("3. 支付系统查询")
    print("4. 管理后台查询")
    print("5. API端点查询")
    print("6. 漏洞指示器查询")
    print("7. 技术指纹查询")
    print("8. 全面查询集合")
    print("9. 自定义查询")
    print("10. 随机查询")

    choice = input("\n请选择 (1-10): ").strip()

    if choice == '1':
        dorks = {"logistics": generator.generate_logistics_dorks()}
    elif choice == '2':
        dorks = {"ecommerce": generator.generate_ecommerce_dorks()}
    elif choice == '3':
        dorks = {"payment": generator.generate_payment_dorks()}
    elif choice == '4':
        dorks = {"admin": generator.generate_admin_dorks()}
    elif choice == '5':
        dorks = {"api": generator.generate_api_dorks()}
    elif choice == '6':
        dorks = {"vulnerabilities": generator.generate_vulnerability_dorks()}
    elif choice == '7':
        dorks = {"tech_fingerprints": generator.generate_tech_fingerprint_dorks()}
    elif choice == '8':
        dorks = generator.generate_comprehensive_dorks()
    elif choice == '9':
        print("\n请输入关键字 (用逗号分隔):")
        keywords = input().strip().split(',')
        keywords = [k.strip() for k in keywords if k.strip()]
        if keywords:
            dorks = {"custom": generator.generate_custom_dorks(keywords)}
        else:
            print("❌ 未输入有效关键字")
            return
    elif choice == '10':
        count = input("随机查询数量 (默认10): ").strip()
        count = int(count) if count.isdigit() else 10
        random_dorks = generator.get_random_dorks(count)
        dorks = {"random": random_dorks}
    else:
        print("❌ 无效选择")
        return

    # 显示统计
    total_dorks = sum(len(dork_list) for dork_list in dorks.values())
    print(f"\n生成统计:")
    print(f"   总查询数: {total_dorks}")
    for category, dork_list in dorks.items():
        print(f"   {category}: {len(dork_list)}")

    # 显示部分示例
    print(f"\n查询示例 (前5个):")
    all_dorks = [dork for dork_list in dorks.values() for dork in dork_list]
    for i, dork in enumerate(all_dorks[:5], 1):
        print(f"   {i}. {dork}")

    # 导出文件
    filename = generator.export_dorks(dorks)
    print(f"\n查询已导出到:")
    print(f"   JSON格式: {filename}")
    print(f"   文本格式: {filename.replace('.json', '.txt')}")

    print(f"\n生成完成! 可以使用这些查询在Google或其他搜索引擎中搜索越南目标系统")

if __name__ == "__main__":
    main()