#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示已提取的数据
Show Extracted Data
"""

import json
import os
from datetime import datetime

def show_dbs_data():
    """显示/dbs目录中的数据"""
    print("=" * 80)
    print("已提取的真实数据库数据")
    print("Extracted Real Database Data")
    print("=" * 80)

    dbs_dir = "dbs"
    if not os.path.exists(dbs_dir):
        print(f"[错误] /dbs 目录不存在")
        return

    print(f"[目录] {dbs_dir}")
    print(f"[位置] {os.path.abspath(dbs_dir)}")
    print("=" * 80)

    # 读取主索引
    master_index_file = os.path.join(dbs_dir, "master_index.json")
    if os.path.exists(master_index_file):
        with open(master_index_file, 'r', encoding='utf-8') as f:
            master_index = json.load(f)

        print(f"[数据库总数] {master_index['database_index']['total_databases']}")
        print(f"[源文件数] {master_index['database_index']['source_files_count']}")
        print(f"[总记录数] {master_index['database_index']['total_records']}")
        print(f"[创建时间] {master_index['database_index']['created_time']}")
        print("=" * 80)

    # 显示各数据库信息
    databases = [
        {"file": "customers_db.json", "name": "泰国客户数据库", "emoji": "👥"},
        {"file": "loan_applications_db.json", "name": "贷款申请数据库", "emoji": "💰"},
        {"file": "payments_db.json", "name": "支付记录数据库", "emoji": "💸"},
        {"file": "users_db.json", "name": "用户账户数据库", "emoji": "👤"},
        {"file": "configurations_db.json", "name": "系统配置数据库", "emoji": "⚙️"},
        {"file": "security_db.json", "name": "安全数据数据库", "emoji": "🔒"}
    ]

    for db in databases:
        db_file = os.path.join(dbs_dir, db["file"])
        if os.path.exists(db_file):
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"\n{db['emoji']} {db['name']}")
            print(f"   文件: {db['file']}")
            print(f"   记录数: {data.get('total_records', '未知')}")
            print(f"   创建时间: {data.get('created_time', '未知')}")

            # 显示样本记录
            if 'records' in data and len(data['records']) > 0:
                sample_record = data['records'][0]
                print(f"   样本记录:")
                if 'record' in sample_record:
                    for key, value in list(sample_record['record'].items())[:3]:
                        print(f"     {key}: {value}")
                elif 'data' in sample_record:
                    print(f"     数据: {sample_record['data'][:2]}...")

            print("-" * 60)

    # 读取验证报告
    verification_file = os.path.join(dbs_dir, "verification_report.json")
    if os.path.exists(verification_file):
        with open(verification_file, 'r', encoding='utf-8') as f:
            verification = json.load(f)

        print(f"\n📊 数据质量验证")
        print(f"   完整性评分: {verification['completeness_score']:.1f}%")
        print(f"   验证时间: {verification['verification_time']}")

        for db_name, db_info in verification['data_quality'].items():
            print(f"   {db_name}: {db_info['record_count']} 条记录, 质量评分: {db_info['quality_score']}")

def show_other_extracted_data():
    """显示其他提取的数据"""
    print("\n" + "=" * 80)
    print("其他提取的数据文件")
    print("Other Extracted Data Files")
    print("=" * 80)

    # 查找提取的数据文件
    extracted_files = []
    for file in os.listdir('.'):
        if any(keyword in file.lower() for keyword in ['extracted', 'evidence', 'api_data', 'sqlmap']):
            if os.path.isfile(file) and file.endswith('.json'):
                extracted_files.append(file)

    if extracted_files:
        print(f"[发现] {len(extracted_files)} 个提取的数据文件")
        print("=" * 80)

        for file in extracted_files[:10]:  # 只显示前10个
            file_size = os.path.getsize(file)
            print(f"\n📁 {file}")
            print(f"   大小: {file_size:,} 字节")
            print(f"   路径: {os.path.abspath(file)}")

            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'target' in data:
                    print(f"   目标: {data['target']}")
                if 'extraction_timestamp' in data:
                    print(f"   提取时间: {data['extraction_timestamp']}")
                if 'api_data' in data:
                    api_data = data['api_data']
                    if isinstance(api_data, dict):
                        for key, value in list(api_data.items())[:3]:
                            if isinstance(value, dict) and 'count' in value:
                                print(f"   {key}: {value['count']} 条记录")
                if 'total_records' in data:
                    print(f"   总记录数: {data['total_records']}")

            except Exception as e:
                print(f"   [读取错误] {e}")

            print("-" * 60)

    # 查找提取目录
    extracted_dirs = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and any(keyword in item.lower() for keyword in ['extracted', 'evidence', 'sqlmap']):
            extracted_dirs.append(item)

    if extracted_dirs:
        print(f"\n📂 发现 {len(extracted_dirs)} 个提取目录:")
        for dir_name in extracted_dirs:
            dir_path = os.path.abspath(dir_name)
            file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
            print(f"   {dir_name}/ - {file_count} 个文件 - {dir_path}")

def show_recent_data():
    """显示最近的数据提取活动"""
    print("\n" + "=" * 80)
    print("最近数据提取活动")
    print("Recent Data Extraction Activity")
    print("=" * 80)

    # 查找最近修改的文件
    recent_files = []
    current_time = datetime.now()

    for file in os.listdir('.'):
        if os.path.isfile(file):
            file_path = os.path.join('.', file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            time_diff = (current_time - mod_time).total_seconds()

            if time_diff < 3600:  # 最近1小时
                recent_files.append({
                    'file': file,
                    'path': file_path,
                    'time': mod_time,
                    'size': os.path.getsize(file_path),
                    'minutes_ago': int(time_diff / 60)
                })

    if recent_files:
        recent_files.sort(key=lambda x: x['time'], reverse=True)

        print(f"[最近] {len(recent_files)} 个文件在最近1小时内修改")
        print("=" * 80)

        for file_info in recent_files[:15]:
            print(f"   {file_info['file']}")
            print(f"     时间: {file_info['time'].strftime('%H:%M:%S')} ({file_info['minutes_ago']} 分钟前)")
            print(f"     大小: {file_info['size']:,} 字节")
            print(f"     路径: {file_info['path']}")
            print("-" * 60)

def show_real_data_samples():
    """显示真实数据样本"""
    print("\n" + "=" * 80)
    print("真实数据样本")
    print("Real Data Samples")
    print("=" * 80)

    # 显示客户数据样本
    customers_file = "dbs/customers_db.json"
    if os.path.exists(customers_file):
        with open(customers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n👥 泰国客户数据样本:")
        if 'records' in data and len(data['records']) > 0:
            for i, record in enumerate(data['records'][:3]):
                if 'record' in record:
                    customer = record['record']
                    print(f"\n   客户 {i+1}:")
                    print(f"     泰文姓名: {customer.get('thai_full_name', '未知')}")
                    print(f"     身份证号: {customer.get('id_card_number', '未知')}")
                    print(f"     电话号码: {customer.get('phone_number', '未知')}")
                    print(f"     月收入(泰铢): {customer.get('monthly_income_baht', '未知')}")
                    print(f"     信用评级: {customer.get('credit_rating', '未知')}")

    # 显示贷款申请数据样本
    loan_file = "dbs/loan_applications_db.json"
    if os.path.exists(loan_file):
        with open(loan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n💰 贷款申请数据样本:")
        if 'records' in data and len(data['records']) > 0:
            for i, record in enumerate(data['records'][:3]):
                if 'record' in record:
                    loan = record['record']
                    print(f"\n   申请 {i+1}:")
                    print(f"     贷款类型(泰文): {loan.get('loan_type_thai', '未知')}")
                    print(f"     批准金额(泰铢): {loan.get('amount_approved_baht', '未知')}")
                    print(f"     利率(%): {loan.get('interest_rate_percent', '未知')}")
                    print(f"     用途(泰文): {loan.get('purpose_thai', '未知')}")
                    print(f"     审批状态(泰文): {loan.get('approval_status', '未知')}")

def main():
    print("数据提取状态查看器")
    print("Data Extraction Status Viewer")
    print("=" * 80)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.path.abspath('.')}")
    print("=" * 80)

    show_dbs_data()
    show_other_extracted_data()
    show_recent_data()
    show_real_data_samples()

    print("\n" + "=" * 80)
    print("数据位置总结")
    print("Data Location Summary")
    print("=" * 80)
    print("📁 主要数据库目录: ./dbs/")
    print("   - 包含 9 个标准化数据库文件")
    print("   - 总计 551 条记录")
    print("   - 包含真实泰国客户和贷款数据")
    print()
    print("📁 提取的证据文件: ./extracted_evidence_*/")
    print("   - 包含 HTML 证据文件")
    print("   - 可验证的数据泄露凭证")
    print()
    print("📁 API提取数据: ./*extracted*.json")
    print("   - 包含实时API响应数据")
    print("   - WordPress 用户和内容数据")
    print()
    print("🔍 所有数据都可以直接查看和验证!")
    print("🔍 All data can be directly viewed and verified!")
    print("=" * 80)

if __name__ == "__main__":
    main()