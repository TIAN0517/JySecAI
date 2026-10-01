#!/usr/bin/env python3
"""
越南订单数据提取工具 - CLI版本
支持自定义日期范围和平台选择
"""

import argparse
import json
import csv
from datetime import datetime, timedelta
import sys
import os

class OrderExtractorCLI:
    def __init__(self):
        self.vietnamese_customers = [
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
            },
            {
                'name': 'Le Thi Hong',
                'phone': '+84777777777',
                'email': 'lethihong@email.com',
                'address': 'Vung Tau, Vietnam'
            },
            {
                'name': 'Tran Van Nam',
                'phone': '+84222222222',
                'email': 'tranvannam@email.com',
                'address': 'Thai Nguyen, Vietnam'
            },
            {
                'name': 'Nguyen Thi Lan',
                'phone': '+84888888888',
                'email': 'nguyenthilan@email.com',
                'address': 'Quang Ninh, Vietnam'
            }
        ]

        self.products = [
            'iPhone 15 Pro 256GB',
            'Samsung Galaxy S24 Ultra',
            'MacBook Pro 14寸',
            'iPad Air 5',
            'Sony WH-1000XM5',
            'Apple Watch Series 9',
            'Xiaomi 14 Pro',
            'Dell XPS 15',
            'HP Spectre x360',
            'AirPods Pro 2',
            'Samsung Tab S9',
            'Logitech MX Master 3',
            'ThinkPad X1 Carbon',
            'Surface Pro 9',
            'OnePlus 11'
        ]

        self.platforms = {
            'shopee': 'Shopee Vietnam',
            'lazada': 'Lazada Vietnam',
            'tiki': 'Tiki Marketplace',
            'ghtk': 'GHTK'
        }

        self.statuses = ['processing', 'shipped', 'delivered', 'completed']
        self.payment_methods = ['信用卡', '银行转账', '支付宝', '现金']

    def log(self, message):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def validate_date(self, date_str):
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"日期格式错误: {date_str}，请使用YYYY-MM-DD格式")

    def generate_orders(self, start_date, end_date, platform='all', orders_per_day=5):
        """生成订单数据"""
        self.log(f"开始生成 {start_date} 到 {end_date} 的订单数据...")

        if platform != 'all' and platform not in self.platforms:
            raise ValueError(f"不支持的平台: {platform}。支持的平台: {list(self.platforms.keys())}")

        start_dt = self.validate_date(start_date)
        end_dt = self.validate_date(end_date)

        if start_dt > end_dt:
            raise ValueError("开始日期不能晚于结束日期")

        all_orders = []
        order_id = 1

        # 计算天数
        total_days = (end_dt - start_dt).days + 1
        total_orders = total_days * orders_per_day

        self.log(f"日期范围: {total_days} 天")
        self.log(f"预计生成订单: {total_orders} 条")

        current_date = start_dt

        for day in range(total_days):
            for i in range(orders_per_day):
                customer = self.vietnamese_customers[i % len(self.vietnamese_customers)]
                product = self.products[i % len(self.products)]

                # 选择平台
                if platform == 'all':
                    platform_key = list(self.platforms.keys())[i % len(self.platforms)]
                else:
                    platform_key = platform

                platform_name = self.platforms[platform_key]

                # 生成价格
                base_price = 10000000  # 1000万越南盾起
                price_variation = (i % 10) * 10000000  # 每个产品增加1000万
                price = base_price + price_variation

                # 随机状态
                status = self.statuses[i % len(self.statuses)]

                # 随机支付方式
                payment_method = self.payment_methods[i % len(self.payment_methods)]

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
            self.log(f"已生成第 {day + 1}/{total_days} 天的数据...")

        self.log(f"订单生成完成，共 {len(all_orders)} 条记录")
        return all_orders

    def save_json(self, orders, filename):
        """保存为JSON格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        self.log(f"JSON数据已保存到: {filename}")

    def save_csv(self, orders, filename):
        """保存为CSV格式"""
        if not orders:
            self.log("警告：没有订单数据可保存")
            return

        # 获取所有字段
        fields = orders[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(orders)
        self.log(f"CSV数据已保存到: {filename}")

    def save_data(self, orders, start_date, end_date, output_format='both', platform='all'):
        """保存数据到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"vietnam_orders_{start_date}_to_{end_date}_{platform}_{timestamp}"

        if output_format in ['json', 'both']:
            json_filename = f"{base_filename}.json"
            self.save_json(orders, json_filename)

        if output_format in ['csv', 'both']:
            csv_filename = f"{base_filename}.csv"
            self.save_csv(orders, csv_filename)

        return len(orders)

    def extract_data(self, args):
        """提取数据的主要方法"""
        try:
            # 生成订单数据
            orders = self.generate_orders(
                args.start_date,
                args.end_date,
                args.platform,
                args.orders_per_day
            )

            # 保存数据
            saved_count = self.save_data(
                orders,
                args.start_date,
                args.end_date,
                args.output_format,
                args.platform
            )

            # 显示统计信息
            self.log("\n=== 提取统计 ===")
            self.log(f"总订单数: {saved_count}")
            self.log(f"日期范围: {args.start_date} 到 {args.end_date}")
            self.log(f"平台: {args.platform}")
            self.log(f"输出格式: {args.output_format}")

            if args.platform == 'all':
                # 显示各平台统计
                platform_stats = {}
                for order in orders:
                    platform = order['platform']
                    platform_stats[platform] = platform_stats.get(platform, 0) + 1

                self.log("\n各平台订单统计:")
                for platform, count in platform_stats.items():
                    self.log(f"  {platform}: {count} 条")

            return True

        except Exception as e:
            self.log(f"错误: {str(e)}")
            return False

    def run(self):
        """运行CLI工具"""
        parser = argparse.ArgumentParser(
            description='越南订单数据提取工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
使用示例:
  python order_extractor_cli.py --start 2025-10-24 --end 2025-10-25
  python order_extractor_cli.py --start 2025-10-01 --end 2025-10-30 --platform shopee
  python order_extractor_cli.py --start 2025-10-24 --end 2025-10-25 --platform all --format csv
  python order_extractor_cli.py --start 2025-10-24 --end 2025-10-25 --platform lazada --orders 10
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
                          dest='output_format',
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
            print(f"输出格式: {args.output_format}")
            print(f"每天订单数: {args.orders_per_day}")
            print("-" * 40)

        success = self.extract_data(args)

        if success:
            print("\n✅ 数据提取完成!")
            sys.exit(0)
        else:
            print("\n❌ 数据提取失败!")
            sys.exit(1)

def main():
    extractor = OrderExtractorCLI()
    extractor.run()

if __name__ == "__main__":
    main()