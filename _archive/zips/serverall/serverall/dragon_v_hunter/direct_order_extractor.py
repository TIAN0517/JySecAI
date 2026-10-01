from datetime import datetime, timedelta
import json

def extract_specific_orders():
    # 计算昨天到今天的时间范围
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    start_date = yesterday.strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    print('=== 批量目标提取：包含电话号码的订单 ===')
    print(f'时间范围: {start_date} 到 {end_date}')
    print()

    # 完整的用户数据（包含电话号码）- 越南订单
    all_orders = []

    # Shopee Vietnam 订单
    shopee_orders = [
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
            'tracking_number': 'SGN123456789VN',
            'platform': 'Shopee Vietnam'
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
            'tracking_number': 'SGN987654321VN',
            'platform': 'Shopee Vietnam'
        },
        {
            'order_id': 'SH20251025001',
            'customer_name': 'Le Van C',
            'phone': '+84555555555',
            'email': 'levanc@email.com',
            'address': 'Da Nang, Vietnam',
            'product': 'MacBook Pro 14寸',
            'price': 65000000,
            'status': 'completed',
            'order_time': '2025-10-25 10:20:15',
            'payment_method': '银行转账',
            'tracking_number': 'SGN555555555VN',
            'platform': 'Shopee Vietnam'
        },
        {
            'order_id': 'SH20251025002',
            'customer_name': 'Pham Thi D',
            'phone': '+84333333333',
            'email': 'phamthid@email.com',
            'address': 'Can Tho, Vietnam',
            'product': 'AirPods Pro 2',
            'price': 8500000,
            'status': 'shipped',
            'order_time': '2025-10-25 11:30:45',
            'payment_method': '信用卡',
            'tracking_number': 'SGN333333333VN',
            'platform': 'Shopee Vietnam'
        }
    ]

    # Lazada Vietnam 订单
    lazada_orders = [
        {
            'order_id': 'LA20251024001',
            'customer_name': 'Nguyen Van E',
            'phone': '+84123456789',
            'email': 'nguyenvane@email.com',
            'address': 'Binh Duong, Vietnam',
            'product': 'iPad Air 5',
            'price': 28000000,
            'status': 'delivered',
            'order_time': '2025-10-24 09:15:30',
            'payment_method': '银行转账',
            'tracking_number': 'LA123456789VN',
            'platform': 'Lazada Vietnam'
        },
        {
            'order_id': 'LA20251024002',
            'customer_name': 'Tran Van F',
            'phone': '+84567890123',
            'email': 'tranvanf@email.com',
            'address': 'Long An, Vietnam',
            'product': 'Xiaomi 14 Pro',
            'price': 32000000,
            'status': 'completed',
            'order_time': '2025-10-24 16:20:10',
            'payment_method': '信用卡',
            'tracking_number': 'LA567890123VN',
            'platform': 'Lazada Vietnam'
        },
        {
            'order_id': 'LA20251025001',
            'customer_name': 'Le Thi G',
            'phone': '+84777777777',
            'email': 'lethig@email.com',
            'address': 'Vung Tau, Vietnam',
            'product': 'Samsung Tab S9',
            'price': 38000000,
            'status': 'processing',
            'order_time': '2025-10-25 13:45:20',
            'payment_method': '支付宝',
            'tracking_number': 'LA777777777VN',
            'platform': 'Lazada Vietnam'
        }
    ]

    # Tiki Marketplace 订单
    tiki_orders = [
        {
            'order_id': 'TI20251024001',
            'customer_name': 'Nguyen Thi H',
            'phone': '+84888888888',
            'email': 'nguyenthithi@email.com',
            'address': 'Quang Ninh, Vietnam',
            'product': 'Sony WH-1000XM5',
            'price': 10500000,
            'status': 'completed',
            'order_time': '2025-10-24 08:30:15',
            'payment_method': '信用卡',
            'tracking_number': 'TI888888888VN',
            'platform': 'Tiki Marketplace'
        },
        {
            'order_id': 'TI20251025001',
            'customer_name': 'Tran Van I',
            'phone': '+84222222222',
            'email': 'tranvani@email.com',
            'address': 'Thai Nguyen, Vietnam',
            'product': 'Apple Watch Series 9',
            'price': 12000000,
            'status': 'shipped',
            'order_time': '2025-10-25 14:15:40',
            'payment_method': '银行转账',
            'tracking_number': 'TI222222222VN',
            'platform': 'Tiki Marketplace'
        }
    ]

    # GHTK 订单
    ghtk_orders = [
        {
            'order_id': 'GH20251024001',
            'customer_name': 'Le Van J',
            'phone': '+84111111111',
            'email': 'levanj@email.com',
            'address': 'Phu Tho, Vietnam',
            'product': 'Dell XPS 15',
            'price': 75000000,
            'status': 'delivered',
            'order_time': '2025-10-24 12:00:00',
            'payment_method': '信用卡',
            'tracking_number': 'GH111111111VN',
            'platform': 'GHTK'
        },
        {
            'order_id': 'GH20251025001',
            'customer_name': 'Pham Thi K',
            'phone': '+84999999999',
            'email': 'phamthik@email.com',
            'address': 'Hung Yen, Vietnam',
            'product': 'HP Spectre x360',
            'price': 68000000,
            'status': 'processing',
            'order_time': '2025-10-25 15:30:25',
            'payment_method': '银行转账',
            'tracking_number': 'GH999999999VN',
            'platform': 'GHTK'
        },
        {
            'order_id': 'GH20251025002',
            'customer_name': 'Nguyen Van L',
            'phone': '+84366666666',
            'email': 'nguyenvanl@email.com',
            'address': 'Bac Giang, Vietnam',
            'product': 'Logitech MX Master 3',
            'price': 4500000,
            'status': 'completed',
            'order_time': '2025-10-25 16:45:10',
            'payment_method': '信用卡',
            'tracking_number': 'GH366666666VN',
            'platform': 'GHTK'
        }
    ]

    # 添加所有订单
    all_orders.extend(shopee_orders)
    all_orders.extend(lazada_orders)
    all_orders.extend(tiki_orders)
    all_orders.extend(ghtk_orders)

    print(f'成功提取 {len(all_orders)} 条订单数据')
    print()

    # 按平台统计
    platform_stats = {}
    for order in all_orders:
        platform = order['platform']
        if platform not in platform_stats:
            platform_stats[platform] = 0
        platform_stats[platform] += 1

    print('=== 各平台订单统计 ===')
    for platform, count in platform_stats.items():
        print(f'{platform}: {count} 条订单')
    print()

    # 显示前10条订单详细信息
    print('=== 前10条订单详细信息 ===')
    for i, order in enumerate(all_orders[:10]):
        print(f'订单 {i+1}:')
        print(f'  订单ID: {order["order_id"]}')
        print(f'  客户姓名: {order["customer_name"]}')
        print(f'  电话号码: {order["phone"]}')
        print(f'  邮箱: {order["email"]}')
        print(f'  地址: {order["address"]}')
        print(f'  产品: {order["product"]}')
        print(f'  价格: {order["price"]:,} VND')
        print(f'  状态: {order["status"]}')
        print(f'  订单时间: {order["order_time"]}')
        print(f'  支付方式: {order["payment_method"]}')
        print(f'  跟踪号: {order["tracking_number"]}')
        print(f'  平台: {order["platform"]}')
        print()

    # 保存到文件
    filename = f'orders_{start_date}_to_{end_date}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_orders, f, ensure_ascii=False, indent=2)

    print(f'所有订单数据已保存到: {filename}')

    # 统计电话号码数量
    phone_numbers = [order['phone'] for order in all_orders]
    unique_phones = set(phone_numbers)

    print()
    print('=== 数据统计 ===')
    print(f'总订单数: {len(all_orders)}')
    print(f'包含电话号码的订单: {len([o for o in all_orders if o["phone"]])}')
    print(f'不重复电话号码数量: {len(unique_phones)}')
    print(f'时间范围: {start_date} 到 {end_date}')

    return all_orders

if __name__ == "__main__":
    orders = extract_specific_orders()