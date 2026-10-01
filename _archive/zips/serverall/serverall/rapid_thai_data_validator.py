#!/usr/bin/env python3
"""
快速泰国贷款数据验证和清洗系统
23小时内完成所有验证和清洗
"""

import json
import re
import time
import requests
import sqlite3
from datetime import datetime, timedelta
import os
import glob
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class RapidThaiDataValidator:
    def __init__(self):
        self.start_time = datetime.now()
        self.deadline = self.start_time + timedelta(hours=23)
        self.validated_data = []
        self.cleaned_datasets = []

        # 泰国数据验证规则
        self.validation_rules = {
            'thai_id': {
                'pattern': r'^\d{13}$',
                'description': '13位泰国身份证'
            },
            'thai_phone': {
                'pattern': r'^0[689]\d{8}$',
                'description': '泰国手机号码'
            },
            'bank_account': {
                'pattern': r'^\d{10,15}$',
                'description': '银行账户号码'
            },
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'description': '邮箱地址'
            },
            'loan_amount': {
                'pattern': r'^\d{4,8}(?:,\d{3})*(?:\.\d{2})?$',
                'description': '贷款金额'
            },
            'thai_name': {
                'pattern': r'^[\u0E00-\u0E7F\s]+$',
                'description': '泰语姓名'
            }
        }

    def load_all_reports(self):
        """加载所有生成的报告"""
        reports = []

        # 加载JSON报告
        json_files = glob.glob("*report*20251029*.json")
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reports.append({'file': file, 'data': data, 'type': 'json'})
            except Exception as e:
                print(f"[-] Error loading {file}: {e}")

        # 加载TXT报告
        txt_files = glob.glob("*report*20251029*.txt")
        for file in txt_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    reports.append({'file': file, 'data': content, 'type': 'txt'})
            except Exception as e:
                print(f"[-] Error loading {file}: {e}")

        print(f"[+] Loaded {len(reports)} reports")
        return reports

    def extract_potential_data(self, reports):
        """从报告中提取潜在数据"""
        extracted_data = []

        for report in reports:
            if report['type'] == 'json':
                extracted = self.extract_from_json(report['data'], report['file'])
            else:
                extracted = self.extract_from_text(report['data'], report['file'])

            extracted_data.extend(extracted)

        print(f"[+] Extracted {len(extracted_data)} potential data items")
        return extracted_data

    def extract_from_json(self, data, source_file):
        """从JSON数据提取"""
        items = []

        def recursive_search(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    items.extend(recursive_search(value, new_path))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    items.extend(recursive_search(item, f"{path}[{i}]"))
            elif isinstance(obj, str):
                # 检查是否匹配敏感数据模式
                for data_type, rule in self.validation_rules.items():
                    if re.match(rule['pattern'], obj.strip()):
                        items.append({
                            'type': data_type,
                            'value': obj.strip(),
                            'source': source_file,
                            'path': path,
                            'confidence': 'high'
                        })

        recursive_search(data)
        return items

    def extract_from_text(self, text, source_file):
        """从文本数据提取"""
        items = []

        # 匹配各种敏感数据
        patterns = {
            'thai_id': r'\b\d{13}\b',
            'thai_phone': r'\b0[689]\d{8}\b',
            'bank_account': r'\b\d{10,15}\b',
            'email': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            'loan_amount': r'\b\d{4,8}(?:,\d{3})*(?:\.\d{2})?\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'url': r'https?://[^\s<>"{}|\\^`[\]]+'
        }

        for data_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            for match in matches:
                items.append({
                    'type': data_type,
                    'value': match.strip(),
                    'source': source_file,
                    'path': 'text_content',
                    'confidence': 'medium'
                })

        return items

    def validate_data(self, data_items):
        """验证数据有效性"""
        validated = []

        for item in data_items:
            validation_result = self.validate_single_item(item)
            if validation_result['is_valid']:
                validated.append(validation_result)

        print(f"[+] Validated {len(validated)} items from {len(data_items)} potential items")
        return validated

    def validate_single_item(self, item):
        """验证单个数据项"""
        data_type = item['type']
        value = item['value']

        if data_type not in self.validation_rules:
            return {
                **item,
                'is_valid': False,
                'reason': 'Unknown data type'
            }

        rule = self.validation_rules[data_type]

        # 基本格式验证
        is_valid = bool(re.match(rule['pattern'], value))
        reason = 'Format valid' if is_valid else 'Invalid format'

        # 额外验证逻辑
        if is_valid:
            if data_type == 'thai_id':
                # 泰国身份证校验位验证
                if len(value) == 13:
                    is_valid = self.validate_thai_id_checksum(value)
                    reason = 'ID checksum valid' if is_valid else 'Invalid ID checksum'

            elif data_type == 'thai_phone':
                # 排除无效手机号前缀
                invalid_prefixes = ['000', '111', '222', '333', '444', '555', '666', '777', '888', '999']
                if any(value.startswith(prefix) for prefix in invalid_prefixes):
                    is_valid = False
                    reason = 'Invalid phone prefix'

            elif data_type == 'email':
                # 排除常见垃圾邮箱域名
                spam_domains = ['tempmail.com', '10minutemail.com', 'guerrillamail.com']
                if any(domain in value.lower() for domain in spam_domains):
                    is_valid = False
                    reason = 'Spam email domain'

        return {
            **item,
            'is_valid': is_valid,
            'reason': reason,
            'validation_timestamp': datetime.now().isoformat()
        }

    def validate_thai_id_checksum(self, thai_id):
        """验证泰国身份证校验位"""
        if len(thai_id) != 13 or not thai_id.isdigit():
            return False

        try:
            # 泰国身份证校验算法
            digits = [int(d) for d in thai_id[:12]]
            weights = list(range(13, 1, -1))

            total = sum(d * w for d, w in zip(digits, weights))
            remainder = total % 11
            checksum = (11 - remainder) % 10

            return checksum == int(thai_id[-1])
        except:
            return False

    def clean_data(self, validated_data):
        """清洗和标准化数据"""
        cleaned = []

        for item in validated_data:
            cleaned_item = self.clean_single_item(item)
            if cleaned_item:
                cleaned.append(cleaned_item)

        # 去重
        unique_data = self.deduplicate_data(cleaned)

        print(f"[+] Cleaned and deduplicated to {len(unique_data)} unique items")
        return unique_data

    def clean_single_item(self, item):
        """清洗单个数据项"""
        value = item['value']
        data_type = item['type']

        # 基本清洗
        cleaned_value = value.strip().replace(' ', '')

        if data_type == 'thai_phone':
            # 标准化手机号格式
            cleaned_value = cleaned_value.replace('-', '').replace(' ', '')

        elif data_type == 'loan_amount':
            # 移除货币符号和逗号
            cleaned_value = cleaned_value.replace(',', '').replace('฿', '').replace('$', '')

        # 检查清洗后是否仍然有效
        if not cleaned_value:
            return None

        # 重新验证
        original_value = item['value']
        item['value'] = cleaned_value
        item['original_value'] = original_value

        validation = self.validate_single_item(item)
        if not validation['is_valid']:
            return None

        return {
            **validation,
            'data_quality': self.assess_data_quality(validation),
            'risk_level': self.assess_risk_level(validation)
        }

    def assess_data_quality(self, item):
        """评估数据质量"""
        score = 0
        factors = []

        # 来源质量
        if 'report' in item.get('source', '').lower():
            score += 30
            factors.append('From official report')

        # 置信度
        if item.get('confidence') == 'high':
            score += 40
            factors.append('High confidence extraction')
        elif item.get('confidence') == 'medium':
            score += 20
            factors.append('Medium confidence extraction')

        # 数据完整性
        if len(item.get('value', '')) > 0:
            score += 30
            factors.append('Complete data')

        if score >= 80:
            return 'excellent'
        elif score >= 60:
            return 'good'
        elif score >= 40:
            return 'fair'
        else:
            return 'poor'

    def assess_risk_level(self, item):
        """评估风险等级"""
        data_type = item['type']

        if data_type in ['thai_id', 'bank_account']:
            return 'high'
        elif data_type in ['thai_phone', 'email']:
            return 'medium'
        else:
            return 'low'

    def deduplicate_data(self, data):
        """去重"""
        seen = set()
        unique = []

        for item in data:
            key = (item['type'], item['value'])
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    def generate_summary_report(self, cleaned_data):
        """生成摘要报告"""
        summary = {
            'validation_summary': {
                'total_processed': len(cleaned_data),
                'by_type': {},
                'by_quality': {},
                'by_risk': {},
                'by_source': {}
            },
            'high_value_targets': [],
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }

        # 统计分析
        for item in cleaned_data:
            # 按类型统计
            data_type = item['type']
            summary['validation_summary']['by_type'][data_type] = summary['validation_summary']['by_type'].get(data_type, 0) + 1

            # 按质量统计
            quality = item['data_quality']
            summary['validation_summary']['by_quality'][quality] = summary['validation_summary']['by_quality'].get(quality, 0) + 1

            # 按风险统计
            risk = item['risk_level']
            summary['validation_summary']['by_risk'][risk] = summary['validation_summary']['by_risk'].get(risk, 0) + 1

            # 按来源统计
            source = os.path.basename(item['source'])
            summary['validation_summary']['by_source'][source] = summary['validation_summary']['by_source'].get(source, 0) + 1

            # 高价值目标
            if item['risk_level'] == 'high' and item['data_quality'] in ['excellent', 'good']:
                summary['high_value_targets'].append(item)

        # 生成建议
        if summary['validation_summary']['total_processed'] > 100:
            summary['recommendations'].append("大量敏感数据发现，建议立即采取防护措施")

        if len(summary['high_value_targets']) > 10:
            summary['recommendations'].append("发现多个高价值目标，建议深入调查")

        thai_ids = summary['validation_summary']['by_type'].get('thai_id', 0)
        if thai_ids > 50:
            summary['recommendations'].append(f"发现{thai_ids}个泰国身份证，存在严重隐私泄露风险")

        return summary

    def save_results(self, cleaned_data, summary):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存清洗后的数据
        data_file = f"validated_thai_data_{timestamp}.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

        # 保存摘要报告
        summary_file = f"thai_data_validation_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # 生成Excel格式报告
        self.generate_excel_report(cleaned_data, summary, timestamp)

        print(f"[+] Results saved:")
        print(f"    - Data: {data_file}")
        print(f"    - Summary: {summary_file}")
        print(f"    - Excel: thai_data_report_{timestamp}.xlsx")

        return data_file, summary_file

    def generate_excel_report(self, data, summary, timestamp):
        """生成Excel报告"""
        try:
            import pandas as pd

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 保存为Excel
            excel_file = f"thai_data_report_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)

            # 创建摘要表
            summary_data = []
            for data_type, count in summary['validation_summary']['by_type'].items():
                summary_data.append({
                    'Data Type': data_type,
                    'Count': count,
                    'Description': self.validation_rules.get(data_type, {}).get('description', 'Unknown')
                })

            summary_df = pd.DataFrame(summary_data)
            with pd.ExcelWriter(excel_file, mode='a') as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

        except ImportError:
            print("[-] pandas not available, skipping Excel report")

    def run_rapid_validation(self):
        """运行快速验证"""
        print("RAPID THAI DATA VALIDATION AND CLEANING")
        print("=" * 50)
        print(f"Deadline: {self.deadline}")
        print(f"Time remaining: {self.deadline - datetime.now()}")
        print("=" * 50)

        start_time = time.time()

        # 1. 加载所有报告
        print("[1/5] Loading all reports...")
        reports = self.load_all_reports()

        # 2. 提取潜在数据
        print("[2/5] Extracting potential data...")
        potential_data = self.extract_potential_data(reports)

        # 3. 验证数据
        print("[3/5] Validating data...")
        validated_data = self.validate_data(potential_data)

        # 4. 清洗数据
        print("[4/5] Cleaning and deduplicating data...")
        cleaned_data = self.clean_data(validated_data)

        # 5. 生成报告
        print("[5/5] Generating summary report...")
        summary = self.generate_summary_report(cleaned_data)

        # 6. 保存结果
        print("\n[+] Saving results...")
        data_file, summary_file = self.save_results(cleaned_data, summary)

        # 7. 打印最终摘要
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print("VALIDATION COMPLETED")
        print(f"{'='*60}")
        print(f"Processing time: {elapsed:.2f} seconds")
        print(f"Total valid items: {len(cleaned_data)}")
        print(f"High-value targets: {len(summary['high_value_targets'])}")
        print(f"Thai IDs found: {summary['validation_summary']['by_type'].get('thai_id', 0)}")
        print(f"Phone numbers found: {summary['validation_summary']['by_type'].get('thai_phone', 0)}")
        print(f"Email addresses found: {summary['validation_summary']['by_type'].get('email', 0)}")
        print(f"Bank accounts found: {summary['validation_summary']['by_type'].get('bank_account', 0)}")
        print(f"\nTime remaining until deadline: {self.deadline - datetime.now()}")
        print(f"{'='*60}")

        return cleaned_data, summary

def main():
    validator = RapidThaiDataValidator()
    data, summary = validator.run_rapid_validation()

    print(f"\n[+] Rapid validation completed successfully!")
    print(f"[+] Ready for next phase with {len(data)} validated items")

if __name__ == "__main__":
    main()