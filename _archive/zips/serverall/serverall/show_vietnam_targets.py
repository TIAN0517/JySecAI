#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示越南目标扫描结果
Show Vietnam Target Scan Results
"""

def show_targets():
    """显示扫描到的越南目标"""

    # 从扫描结果中提取的可访问目标
    accessible_targets = [
        {"url": "https://viettelpost.vn", "category": "logistics"},
        {"url": "https://tiki.vn", "category": "ecommerce"},
        {"url": "https://giaohangnhanh.vn", "category": "logistics"},
        {"url": "https://ghtk.vn", "category": "logistics"},
        {"url": "https://ahamove.com", "category": "logistics"},
        {"url": "https://hasaki.vn", "category": "ecommerce"},
        {"url": "https://chotot.vn", "category": "ecommerce"},
        {"url": "https://shopee.vn", "category": "ecommerce"},
        {"url": "https://onepay.vn", "category": "payment"},
        {"url": "https://vnpay.vn", "category": "payment"},
        {"url": "https://zalopay.vn", "category": "payment"},
        {"url": "https://payoo.vn", "category": "payment"},
        {"url": "https://momo.vn", "category": "payment"},
        {"url": "https://vatgia.com", "category": "ecommerce"},
        {"url": "https://lazada.vn", "category": "ecommerce"},
        {"url": "https://vnpost.vn", "category": "logistics"},
        {"url": "https://shipchung.vn", "category": "logistics"},
        {"url": "https://sendo.vn", "category": "ecommerce"},
        {"url": "https://nganluong.vn", "category": "payment"},
        {"url": "https://epay.vn", "category": "payment"},
        {"url": "https://tiki.vn", "category": "ecommerce"},
        {"url": "https://watsons.vn", "category": "ecommerce"},
        {"url": "https://adayroi.com", "category": "ecommerce"}
    ]

    print("越南目标扫描结果 - 可访问目标列表")
    print("="*60)
    print(f"总计发现: {len(accessible_targets)} 个可访问目标")
    print()

    # 按类别分组
    categories = {}
    for target in accessible_targets:
        cat = target["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(target)

    for category, targets in categories.items():
        print(f"{category.upper()} 系统 ({len(targets)} 个)")
        print("-" * 40)

        for i, target in enumerate(targets, 1):
            print(f"{i:2d}. {target['url']}")

        print()

    # 高价值目标推荐
    high_value = [
        "https://shopee.vn",      # 最大电商平台
        "https://lazada.vn",      # 阿里电商
        "https://tiki.vn",        # 本土电商
        "https://momo.vn",        # 最大电子钱包
        "https://zalopay.vn",     # Zalo支付
        "https://vnpay.vn",       # 支付网关
        "https://vnpost.vn",      # 国家邮政
        "https://viettelpost.vn", # 军队电信
        "https://giaohangnhanh.vn", # 快速配送
        "https://ghtk.vn"         # 经济配送
    ]

    print("高价值目标推荐 (TOP 10)")
    print("-" * 40)
    for i, url in enumerate(high_value, 1):
        category = next((t['category'] for t in accessible_targets if t['url'] == url), "unknown")
        print(f"{i:2d}. {url} ({category})")

    print()
    print("扫描统计:")
    print(f"- 总扫描目标: 37")
    print(f"- 可访问目标: 24")
    print(f"- 成功率: 64.9%")
    print(f"- 物流系统: 7 个")
    print(f"- 电商平台: 10 个")
    print(f"- 支付系统: 7 个")

if __name__ == "__main__":
    show_targets()