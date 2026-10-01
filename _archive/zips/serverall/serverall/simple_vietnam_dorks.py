#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版越南Google Dorks生成器
Simple Vietnam Google Dorks Generator

快速生成针对越南系统的Google Hacking查询
"""

import json
from datetime import datetime

def generate_vietnam_dorks():
    """生成越南Google Dorks"""

    # 越南域名
    vn_domains = ["site:.vn", "site:.com.vn"]

    # 越南语关键字
    vn_keywords = {
        "logistics": ["van chuyen", "giao hang", "chuyen phat", "shipping", "delivery"],
        "ecommerce": ["thuong mai dien tu", "mua sam online", "san pham", "gio hang"],
        "payment": ["thanh toan", "payment", "vi dien tu", "chuyen khoan"],
        "admin": ["admin", "dashboard", "quan tri", "quan ly"],
        "tracking": ["tracking", "theo doi", "trang thai", "kiem tra"]
    }

    # Google Hacking模板
    templates = [
        "{} inurl:{}",
        "{} intitle:{}",
        "{} \"{}\"",
        "{} inurl:admin {}",
        "{} inurl:api {}",
        "{} filetype:json {}",
        "{} inurl:login {}",
        "{} intitle:\"admin panel\" {}"
    ]

    dorks = []

    # 生成物流快递查询
    for domain in vn_domains:
        for keyword in vn_keywords["logistics"]:
            for template in templates[:3]:
                dorks.append(template.format(domain, keyword))

    # 生成电商查询
    for domain in vn_domains:
        for keyword in vn_keywords["ecommerce"]:
            for template in templates[:3]:
                dorks.append(template.format(domain, keyword))

    # 生成支付查询
    for domain in vn_domains:
        for keyword in vn_keywords["payment"]:
            for template in templates[:2]:
                dorks.append(template.format(domain, keyword))

    # 生成管理后台查询
    for domain in vn_domains:
        for keyword in vn_keywords["admin"]:
            dorks.append(f"{domain} inurl:admin")
            dorks.append(f"{domain} intitle:admin panel")

    # 生成API查询
    for domain in vn_domains:
        dorks.append(f"{domain} inurl:api")
        dorks.append(f"{domain} inurl:api/v1")
        dorks.append(f"{domain} filetype:json api")

    # 生成跟踪查询
    for domain in vn_domains:
        for keyword in vn_keywords["tracking"]:
            dorks.append(f"{domain} {keyword}")

    # 添加越南特定品牌
    vietnam_brands = ["Shopee", "Lazada", "Tiki", "Sendo", "VNPost", "Viettel Post", "Giao Hang Nhanh", "MoMo", "ZaloPay", "VNPay"]

    for brand in vietnam_brands:
        dorks.append(f"site:.vn \"{brand}\"")
        dorks.append(f"site:.vn {brand.lower()} inurl:admin")

    # 添加漏洞指示器
    vulnerabilities = [
        "error establishing database connection",
        "warning mysql",
        "fatal error",
        "internal server error",
        "database error"
    ]

    for domain in vn_domains[:1]:
        for vuln in vulnerabilities:
            dorks.append(f"{domain} \"{vuln}\"")

    return list(set(dorks))  # 去重

def main():
    print("Vietnam Google Dorks Generator")
    print("Generating queries for Vietnam systems...")
    print("="*50)

    dorks = generate_vietnam_dorks()

    print(f"Generated {len(dorks)} unique queries")
    print("\nSample queries:")
    for i, dork in enumerate(dorks[:10], 1):
        print(f"{i:2d}. {dork}")

    if len(dorks) > 10:
        print(f"... and {len(dorks) - 10} more queries")

    # 导出到文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vietnam_dorks_{timestamp}.txt"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("Vietnam Google Dorks for Logistics, E-commerce & Payment Systems\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total queries: {len(dorks)}\n")
        f.write("="*60 + "\n\n")

        for dork in dorks:
            f.write(f"{dork}\n")

    print(f"\nQueries exported to: {filename}")

    # 分类统计
    categories = {
        "Logistics": sum(1 for d in dorks if any(k in d.lower() for k in ["van chuyen", "giao hang", "shipping", "delivery"])),
        "E-commerce": sum(1 for d in dorks if any(k in d.lower() for k in ["thuong mai", "mua sam", "san pham"])),
        "Payment": sum(1 for d in dorks if any(k in d.lower() for k in ["thanh toan", "payment", "vi dien tu"])),
        "Admin": sum(1 for d in dorks if any(k in d.lower() for k in ["admin", "dashboard", "quan tri"])),
        "API": sum(1 for d in dorks if any(k in d.lower() for k in ["api", "json"])),
        "Vietnam Brands": sum(1 for d in dorks if any(k in d for k in ["shopee", "lazada", "tiki", "sendo", "vnpay"])),
        "Vulnerabilities": sum(1 for d in dorks if any(k in d.lower() for k in ["error", "warning", "fatal"]))
    }

    print("\nQuery Categories:")
    for category, count in categories.items():
        if count > 0:
            print(f"  {category}: {count}")

    print("\nUsage:")
    print("1. Copy queries to Google search")
    print("2. Use with security tools like Nuclei, Nmap")
    print("3. Validate discovered targets")
    print("4. Test with penetration testing tools")

if __name__ == "__main__":
    main()