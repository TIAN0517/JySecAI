#!/usr/bin/env python3
"""
越南订单数据提取工具 - 简化CLI版本
支持自定义日期范围和平台选择
"""

import argparse
import json
import csv
from datetime import datetime, timedelta
import sys
import os

def generate_sample_data(start_date, end_date, platform='all', orders_per_day=5):
    """生成越南订单模拟数据"""

    # 越南客户数据
    vietnamese_customers = [
        {
            'name': 'Nguyen Van Anh',
            'phone': '+84912345678',
            'email': 'nguyenvananh@email.com',
            'address': 'Ha Noi, Vietnam'
        },
        {
            'name': 'Tran Thi Binh',
            'phone': '+84987654321',
            'email': 'tranthibinh@email.com',
            'address': 'Ho Chi Minh City, Vietnam'
        },
        {
            'name': 'Le Van Cuong',
            'phone': '+84555555555',
            'email': 'levancuong@email.com',
            'address': 'Da Nang, Vietnam'
        },
        {
            'name': 'Pham Thi Dung',
            'phone': '+84333333333',
            'email': 'phamthidung@email.com',
            'address': 'Can Tho, Vietnam'
        },
        {
            'name': 'Nguyen Van Minh',
            'phone': '+84111111111',
            'email': 'nguyenvanminh@email.com',
            'address': 'Binh Duong, Vietnam'
        }
    ]

    # 产品数据
    products = [
        'iPhone 15 Pro 256GB',
        'Samsung Galaxy S24 Ultra',
        'MacBook Pro 14寸',
        'iPad Air 5',
        'Sony WH-1000XM5',
        'Apple Watch Series 9',
        'Xiaomi 14 Pro',
        'Dell XPS 15',
        'HP Spectre x360',
        'AirPods Pro 2'
    ]

    # 平台数据
    platforms = {
        'shopee': 'Shopee Vietnam',
        'lazada': 'Lazada Vietnam',
        'tiki': 'Tiki Marketplace',
        'ghtk': 'GHTK'
    }

    # 状态和支付方式
    statuses = ['processing', 'shipped', 'delivered', 'completed']
    payment_methods = ['信用卡', '银行转账', '支付宝', '现金']

    # 验证日期
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("错误: 日期格式不正确，请使用YYYY-MM-DD格式")
        return None

    if start_dt > end_dt:
        print("错误: 开始日期不能晚于结束日期")
        return None

    # 验证平台
    if platform != 'all' and platform not in platforms:
        print(f"错误: 不支持的平台 {platform}")
        return None

    # 计算天数
    total_days = (end_dt - start_dt).days + 1
    total_orders = total_days * orders_per_day

    print(f"生成数据: {start_date} 到 {end_date}")
    print(f"日期范围: {total_days} 天")
    print(f"预计订单: {total_orders} 条")

    all_orders = []
    order_id = 1

    current_date = start_dt

    for day in range(total_days):
        for i in range(orders_per_day):
            customer = vietnamese_customers[i % len(vietnamese_customers)]
            product = products[i % len(products)]

            # 选择平台
            if platform == 'all':
                platform_key = list(platforms.keys())[i % len(platforms)]
            else:
                platform_key = platform

            platform_name = platforms[platform_key]

            # 生成价格
            base_price = 10000000  # 1000万越南盾起
            price_variation = (i % 10) * 10000000  # 每个产品增加1000万
            price = base_price + price_variation

            # 随机状态
            status = statuses[i % len(statuses)]

            # 随机支付方式
            payment_method = payment_methods[i % len(payment_methods)]

            # 生成订单号
            order_prefix = platform_key.upper()
            order_number = f"{order_prefix}{current_date.strftime('%Y%m%d')}{order_id:03d}"

            order = {
                'order_id': order_number,
                'customer_name': customer['name'],
                'phone': customer['phone'],
                'email': customer['email'],
                'address': customer['address'],
                'product': product,
                'price': price,
                'status': status,
                'order_time': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'payment_method': payment_method,
                'tracking_number': f"SGN{order_id:09d}VN",
                'platform': platform_name,
                'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            all_orders.append(order)
            order_id += 1

        current_date += timedelta(days=1)

    print(f"成功生成 {len(all_orders)} 条订单数据")
    return all_orders

def save_json(orders, filename):
    """保存为JSON格式"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"JSON数据已保存到: {filename}")

def save_csv(orders, filename):
    """保存为CSV格式"""
    if not orders:
        print("警告: 没有订单数据可保存")
        return

    fields = orders[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(orders)
    print(f"CSV数据已保存到: {filename}")

def main():
    parser = argparse.ArgumentParser(
        description='越南订单数据提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  python simple_order_cli.py --start 2025-10-24 --end 2025-10-25
  python simple_order_cli.py --start 2025-10-01 --end 2025-10-30 --platform shopee
  python simple_order_cli.py --start 2025-10-24 --end 2025-10-25 --platform all --format csv
  python simple_order_cli.py --start 2025-10-24 --end 2025-10-25 --platform lazada --orders 10
        '''
    )

    parser.add_argument('--start', '-s',
                      required=True,
                      help='开始日期 (YYYY-MM-DD)')

    parser.add_argument('--end', '-e',
                      required=True,
                      help='结束日期 (YYYY-MM-DD)')

    parser.add_argument('--platform', '-p',
                      choices=['all', 'shopee', 'lazada', 'tiki', 'ghtk'],
                      default='all',
                      help='选择平台 (默认: all)')

    parser.add_argument('--format', '-f',
                      choices=['json', 'csv', 'both'],
                      default='both',
                      help='输出格式 (默认: both)')

    parser.add_argument('--orders-per-day', '-n',
                      type=int,
                      default=5,
                      help='每天生成订单数 (默认: 5)')

    parser.add_argument('--quiet', '-q',
                      action='store_true',
                      help='静默模式')

    args = parser.parse_args()

    if not args.quiet:
        print("=== 越南订单数据提取工具 ===")
        print(f"开始日期: {args.start}")
        print(f"结束日期: {args.end}")
        print(f"平台: {args.platform}")
        print(f"输出格式: {args.format}")
        print(f"每天订单数: {args.orders_per_day}")
        print("-" * 40)

    # 生成订单数据
    orders = generate_sample_data(
        args.start,
        args.end,
        args.platform,
        args.orders_per_day
    )

    if orders is None:
        sys.exit(1)

    # 保存数据
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = f"vietnam_orders_{args.start}_to_{args.end}_{args.platform}_{timestamp}"

    if args.format in ['json', 'both']:
        json_filename = f"{base_filename}.json"
        save_json(orders, json_filename)

    if args.format in ['csv', 'both']:
        csv_filename = f"{base_filename}.csv"
        save_csv(orders, csv_filename)

    # 显示统计信息
    print("\n=== 提取统计 ===")
    print(f"总订单数: {len(orders)}")
    print(f"日期范围: {args.start} 到 {args.end}")
    print(f"平台: {args.platform}")
    print(f"输出格式: {args.format}")

    if args.platform == 'all':
        # 显示各平台统计
        platform_stats = {}
        for order in orders:
            platform = order['platform']
            platform_stats[platform] = platform_stats.get(platform, 0) + 1

        print("\n各平台订单统计:")
        for platform, count in platform_stats.items():
            print(f"  {platform}: {count} 条")

    print("\n数据提取完成!")

if __name__ == "__main__":
    main()