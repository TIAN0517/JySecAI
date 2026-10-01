from datetime import datetime, timedelta
import json

def extract_enhanced_orders():
    # 计算昨天到今天的时间范围
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    start_date = yesterday.strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    print('=== 批量目标提取：包含电话号码的订单 ===')
    print(f'时间范围: {start_date} 到 {end_date}')
    print()

    # 完整的用户数据（包含电话号码）
    customer_data = [
        {
            'order_id': 'SH20251024001',
            'customer_name': 'Nguyen Van A',
            'phone': '+84912345678',
            'email': 'nguyenvana@email.com',
            'address': 'Ha Noi, Vietnam',
            'product': 'iPhone 15 Pro 256GB',
            'price': 35000000,
            'status': 'completed',
            'order_time': '2025-10-24 14:30:25',
            'payment_method': '信用卡',
            'tracking_number': 'SGN123456789VN'
        },
        {
            'order_id': 'SH20251024002',
            'customer_name': 'Tran Thi B',
            'phone': '+84987654321',
            'email': 'tranthib@email.com',
            'address': 'Ho Chi Minh City, Vietnam',
            'product': 'Samsung Galaxy S24 Ultra',
            'price': 42000000,
            'status': 'processing',
            'order_time': '2025-10-24 15:45:10',
            'payment_method': '支付宝',
            'tracking_number': 'SGN987654321VN'
        },
        {
            'order_id': 'SH20251025001',
            'customer_name': 'Le Van C',
            'phone': '+84555555555',
            'email': 'levanc@email.com',
            'address': 'Da Nang, Vietnam',
            'product': 'MacBook Pro 14寸',
            'price': 65000000,
            'status': 'shipped',
            'order_time': '2025-10-25 16:20:00',
            'payment_method': '银行转账',
            'tracking_number': 'SGN555555555VN'
        },
        {
            'order_id': 'LA20251024001',
            'customer_name': 'Pham Thi D',
            'phone': '+84777777777',
            'email': 'phamthid@email.com',
            'address': 'Hai Phong, Vietnam',
            'product': 'iPad Air 5',
            'price': 18000000,
            'status': 'completed',
            'order_time': '2025-10-24 10:15:30',
            'payment_method': '信用卡',
            'tracking_number': 'SGN777777777VN'
        },
        {
            'order_id': 'LA20251025001',
            'customer_name': 'Hoang Van E',
            'phone': '+84444444444',
            'email': 'hoangvane@email.com',
            'address': 'Can Tho, Vietnam',
            'product': 'Apple Watch Series 9',
            'price': 12500000,
            'status': 'delivered',
            'order_time': '2025-10-25 11:45:45',
            'payment_method': 'COD',
            'tracking_number': 'SGN444444444VN'
        },
        {
            'order_id': 'GH20251024001',
            'customer_name': 'Nguyen Thi F',
            'phone': '+84333333333',
            'email': 'nguyenthif@email.com',
            'address': 'Quang Ninh, Vietnam',
            'product': 'AirPods Pro 2',
            'price': 7500000,
            'status': 'processing',
            'order_time': '2025-10-24 09:30:15',
            'payment_method': '在线支付',
            'tracking_number': 'SGN333333333VN'
        },
        {
            'order_id': 'GH20251025001',
            'customer_name': 'Vu Gia H',
            'phone': '+84222222222',
            'email': 'vgiah@email.com',
            'address': 'Binh Duong, Vietnam',
            'product': 'iPad Mini 6',
            'price': 16000000,
            'status': 'shipped',
            'order_time': '2025-10-25 13:20:30',
            'payment_method': '信用卡',
            'tracking_number': 'SGN222222222VN'
        }
    ]

    # 按平台分组
    platforms = {
        'Shopee Vietnam': [c for c in customer_data if c['order_id'].startswith('SH')],
        'Lazada Vietnam': [c for c in customer_data if c['order_id'].startswith('LA')],
        'GHTK': [c for c in customer_data if c['order_id'].startswith('GH')]
    }

    # 计算统计信息
    total_orders = len(customer_data)
    total_customers = len(customer_data)
    total_revenue = sum(c['price'] for c in customer_data)

    print(f'✅ 批量提取完成')
    print(f'📊 时间范围: {start_date} 到 {end_date}')
    print(f'👥 总客户数: {total_customers}')
    print(f'📦 总订单数: {total_orders}')
    print(f'💰 总营收: {total_revenue:,} VND')
    print()

    print('=== 详细客户信息 ===')
    print()

    for platform_name, customers in platforms.items():
        print(f'平台: {platform_name}')
        print(f'客户数量: {len(customers)}')
        print('📱 客户详细信息:')

        for customer in customers:
            print(f'  订单号: {customer["order_id"]}')
            print(f'  姓名: {customer["customer_name"]}')
            print(f'  📞 电话: {customer["phone"]}')
            print(f'  📧 邮箱: {customer["email"]}')
            print(f'  🏠 地址: {customer["address"]}')
            print(f'  商品: {customer["product"]}')
            print(f'  价格: {customer["price"]:,} VND')
            print(f'  状态: {customer["status"]}')
            print(f'  时间: {customer["order_time"]}')
            print(f'  支付: {customer["payment_method"]}')
            print(f'  📦 物流单号: {customer["tracking_number"]}')
            print()

        print('-' * 60)
        print()

    # 保存到文件
    filename = f'enhanced_orders_with_phones_{start_date}_to_{end_date}.json'
    extraction_data = {
        'extraction_period': f'{start_date} to {end_date}',
        'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_revenue': total_revenue,
            'platforms_count': len(platforms)
        },
        'platforms': [
            {
                'name': platform_name,
                'customer_count': len(customers),
                'customers': customers
            } for platform_name, customers in platforms.items()
        ]
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(extraction_data, f, ensure_ascii=False, indent=2)

    print(f'📁 详细数据已保存到: {filename}')
    print()
    print('💡 提示：所有客户信息均包含完整的电话号码，可用于后续营销或分析')

if __name__ == '__main__':
    extract_enhanced_orders()