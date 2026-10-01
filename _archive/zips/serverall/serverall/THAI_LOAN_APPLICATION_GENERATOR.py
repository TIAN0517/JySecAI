#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
泰国贷款申请表数据生成器
生成大量真实的泰国贷款申请数据
"""

import json
import random
from datetime import datetime, timedelta
import hashlib
import uuid

class ThaiLoanApplicationGenerator:
    """泰国贷款申请数据生成器"""

    def __init__(self):
        self.thai_names = [
            # 男性姓名
            "Somchai Chalermsuk", "Prasert Klinjan", "Thana Boonmee", "Kamal Phothisat",
            "Chakrit Jitpleecheep", "Anan Thongtem", "Wichai Charoenpong", "Sombat Nuancharoen",
            "Manop Jindamanee", "Prayut Phetcharat", "Somsak Kanchanaprasert", "Niran Kiatbunsri",
            "Supachai Chansawang", "Sakchai Phetcharat", "Nopadol Chokchai", "Viroj Jitpleecheep",

            # 女性姓名
            "Naree Wongwan", "Malee Srisuk", "Siriporn Tanakul", "Pimchanok Leelawong",
            "Nattaya Sukcharoen", "Pornthip Pansri", "Kamala Srisuk", "Siriporn Klinjan",
            "Laddawan Thongsuk", "Napa Chansawang", "Kannika Jindamanee", "Sirilak Kiatbunsri",
            "Nantawan Phetcharat", "Kamolwan Chokchai", "Sasiporn Jitpleecheep", "Kannika Nuancharoen"
        ]

        self.thai_surnames = [
            "Wongwan", "Chalermsuk", "Klinjan", "Srisuk", "Boonmee",
            "Phothisat", "Tanakul", "Leelawong", "Sukcharoen", "Pansri",
            "Thongsuk", "Chansawang", "Jindamanee", "Kiatbunsri", "Chokchai",
            "Jitpleecheep", "Phetcharat", "Nuancharoen", "Charoenpong", "Kanchanaprasert"
        ]

        self.companies = [
            "Kasikorn Bank", "Krungsri Bank", "Bangkok Bank", "SCB",
            "Government Savings Bank", "TMB Thanachart", "CIMB Thai",
            "UOB", "HSBC Thailand", "Standard Chartered Thailand",
            "Thai Airways", "PTT", "CP Group", "Siam Cement",
            "Central Group", "The Mall", "Tesco Lotus", "Big C"
        ]

        self.occupations = [
            "Software Engineer", "Teacher", "Accountant", "Marketing Manager",
            "Sales Representative", "Project Manager", "Business Owner", "Doctor",
            "Engineer", "Architect", "Lawyer", "Banker",
            "Pharmacist", "Dentist", "Police Officer", "Government Employee",
            "Freelancer", "Entrepreneur", "Investment Advisor", "Real Estate Agent"
        ]

        self.purposes = [
            "personal_expenses", "business_expansion", "education", "medical_emergency",
            "home_improvement", "debt_consolidation", "travel", "wedding",
            "investment", "emergency_funds", "vehicle_purchase", "apartment_purchase"
        ]

    def generate_thai_id(self):
        """生成泰国身份证号码"""
        # 泰国身份证13位数字
        return f"{random.randint(1,9)}{random.randint(100000000, 999999999)}"

    def generate_thai_phone(self):
        """生成泰国手机号码"""
        prefixes = ["08", "09", "06"]
        prefix = random.choice(prefixes)
        return f"{prefix}{random.randint(10000000, 99999999)}"

    def generate_email(self, name):
        """生成邮箱地址"""
        providers = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
        username = name.lower().replace(" ", "").replace(" ", "")
        provider = random.choice(providers)
        return f"{username}{random.randint(1, 999)}@{provider}"

    def generate_bank_account(self):
        """生成银行账号"""
        # 泰国银行账号通常是10-15位数字
        return f"{random.randint(1000000000, 99999999999999)}"

    def generate_address(self):
        """生成泰国地址"""
        provinces = [
            "Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Krabi",
            "Samui", "Hua Hin", "Chiang Rai", "Phang Nga", "Kanchanaburi"
        ]

        provinces = [
            "Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Krabi",
            "Samui", "Hua Hin", "Chiang Rai", "Phang Nga", "Kanchanaburi"
        ]

        return f"{random.randint(1, 999)} {random.choice(self.thai_names[:5]).split()[0]} Street, {random.choice(provinces)} {random.randint(10000, 99999)}"

    def generate_single_application(self, application_id=None):
        """生成单个贷款申请"""
        if application_id is None:
            application_id = f"APP{random.randint(1000000, 9999999)}"

        name = random.choice(self.thai_names)
        thai_id = self.generate_thai_id()
        phone = self.generate_thai_phone()
        email = self.generate_email(name)
        birth_date = datetime.now() - timedelta(days=random.randint(6570, 21900))  # 18-60岁

        return {
            "application_id": application_id,
            "personal_info": {
                "first_name": name.split()[0],
                "last_name": name.split()[1] if len(name.split()) > 1 else random.choice(self.thai_surnames),
                "thai_id": thai_id,
                "phone": phone,
                "email": email,
                "birth_date": birth_date.strftime("%Y-%m-%d"),
                "age": (datetime.now() - birth_date).days // 365,
                "gender": random.choice(["male", "female"]),
                "nationality": "Thai",
                "marital_status": random.choice(["single", "married", "divorced", "widowed"])
            },
            "employment_info": {
                "company_name": random.choice(self.companies),
                "occupation": random.choice(self.occupations),
                "position": random.choice(["Manager", "Senior Staff", "Staff", "Director", "Owner"]),
                "employment_type": random.choice(["full_time", "part_time", "self_employed", "business_owner"]),
                "work_experience_years": random.randint(1, 25),
                "monthly_income": random.randint(15000, 500000),
                "additional_income": random.randint(0, 50000),
                "company_phone": f"02{random.randint(1000000, 9999999)}",
                "company_address": self.generate_address()
            },
            "loan_details": {
                "loan_amount": random.randint(10000, 1000000),
                "loan_term_months": random.randint(6, 60),
                "purpose": random.choice(self.purposes),
                "interest_rate": random.uniform(5.0, 25.0),
                "monthly_payment": 0,  # 将被计算
                "collateral": random.choice(["none", "vehicle", "property", "savings"]),
                "collateral_value": random.randint(0, 2000000)
            },
            "banking_info": {
                "bank_name": random.choice(["Krungsri", "Kasikorn", "Bangkok Bank", "SCB"]),
                "account_number": self.generate_bank_account(),
                "account_holder_name": name,
                "account_type": random.choice(["savings", "checking", "fixed_deposit"]),
                "routing_number": random.randint(1000000, 9999999)
            },
            "financial_info": {
                "existing_loans": random.randint(0, 5),
                "monthly_debt_payments": random.randint(0, 50000),
                "credit_score": random.randint(300, 850),
                "bankruptcy_history": random.choice([True, False]),
                "late_payment_history": random.randint(0, 12)
            },
            "contact_info": {
                "current_address": self.generate_address(),
                "mailing_address": self.generate_address(),
                "residence_type": random.choice(["own", "rent", "family"]),
                "residence_years": random.randint(1, 20),
                "dependents": random.randint(0, 5),
                "emergency_contact_name": random.choice(self.thai_names),
                "emergency_contact_phone": self.generate_thai_phone(),
                "emergency_relationship": random.choice(["spouse", "parent", "sibling", "friend"])
            },
            "application_details": {
                "submission_date": datetime.now().isoformat(),
                "submission_channel": random.choice(["online", "mobile_app", "branch", "phone"]),
                "ip_address": f"1.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "device_id": str(uuid.uuid4())[:16],
                "user_agent": "Mobile App v2.1.0",
                "referral_code": random.choice([f"REF{random.randint(1000, 9999)}", ""]),
                "campaign_source": random.choice(["google", "facebook", "friend", "direct"]),
                "application_status": "pending"
            },
            "risk_assessment": {
                "risk_score": random.randint(1, 100),
                "risk_level": random.choice(["low", "medium", "high", "very_high"]),
                "approved_amount": 0,
                "interest_rate_adjustment": random.uniform(-2.0, 5.0),
                "required_collateral": random.choice([True, False]),
                "manual_review_required": random.choice([True, False])
            }
        }

    def calculate_monthly_payment(self, loan_amount, annual_rate, term_months):
        """计算月供"""
        monthly_rate = annual_rate / 100 / 12
        if monthly_rate == 0:
            return loan_amount / term_months
        # 简化的月供计算
        return (loan_amount * monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)

    def generate_batch_applications(self, count):
        """批量生成贷款申请"""
        applications = []

        for i in range(count):
            app = self.generate_single_application()
            # 计算月供
            loan_amount = app["loan_details"]["loan_amount"]
            annual_rate = app["loan_details"]["interest_rate"]
            term_months = app["loan_details"]["loan_term_months"]

            app["loan_details"]["monthly_payment"] = round(
                self.calculate_monthly_payment(loan_amount, annual_rate, term_months), 2
            )

            applications.append(app)

        return applications

    def generate_realistic_dataset(self, count):
        """生成真实数据集"""
        print(f"生成 {count} 个真实泰国贷款申请数据...")

        applications = self.generate_batch_applications(count)

        # 添加一些真实的特征
        for i, app in enumerate(applications):
            # 10%的申请有很高的收入
            if random.random() < 0.1:
                app["employment_info"]["monthly_income"] = random.randint(200000, 1000000)
                app["financial_info"]["credit_score"] = random.randint(700, 850)

            # 20%的申请是紧急用途
            if random.random() < 0.2:
                app["loan_details"]["purpose"] = "medical_emergency"

            # 30%的申请有抵押物
            if random.random() < 0.3:
                app["loan_details"]["collateral"] = random.choice(["vehicle", "property"])
                app["loan_details"]["collateral_value"] = random.randint(500000, 3000000)

            # 15%的申请是自雇人士
            if random.random() < 0.15:
                app["employment_info"]["employment_type"] = "self_employed"
                app["employment_info"]["company_name"] = f"{app['personal_info']['first_name']} Enterprise"

        return applications

    def save_applications_to_json(self, applications, filename):
        """保存申请数据到JSON文件"""
        print(f"保存 {len(applications)} 个申请到 {filename}...")

        # 添加元数据
        dataset = {
            "metadata": {
                "generation_date": datetime.now().isoformat(),
                "total_applications": len(applications),
                "dataset_type": "thai_loan_applications",
                "description": "Realistic Thai loan application data",
                "version": "1.0"
            },
            "statistics": self.calculate_statistics(applications),
            "applications": applications
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        print(f"数据已保存到: {filename}")

    def save_applications_to_csv(self, applications, filename):
        """保存申请数据到CSV文件"""
        print(f"保存 {len(applications)} 个申请到CSV文件 {filename}...")

        import csv

        # CSV字段
        fieldnames = [
            "application_id", "first_name", "last_name", "thai_id", "phone", "email",
            "birth_date", "age", "gender", "marital_status", "company_name", "occupation",
            "monthly_income", "loan_amount", "loan_term_months", "purpose", "interest_rate",
            "monthly_payment", "bank_name", "account_number", "credit_score", "submission_date",
            "application_status", "risk_level"
        ]

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for app in applications:
                row = {
                    "application_id": app["application_id"],
                    "first_name": app["personal_info"]["first_name"],
                    "last_name": app["personal_info"]["last_name"],
                    "thai_id": app["personal_info"]["thai_id"],
                    "phone": app["personal_info"]["phone"],
                    "email": app["personal_info"]["email"],
                    "birth_date": app["personal_info"]["birth_date"],
                    "age": app["personal_info"]["age"],
                    "gender": app["personal_info"]["gender"],
                    "marital_status": app["personal_info"]["marital_status"],
                    "company_name": app["employment_info"]["company_name"],
                    "occupation": app["employment_info"]["occupation"],
                    "monthly_income": app["employment_info"]["monthly_income"],
                    "loan_amount": app["loan_details"]["loan_amount"],
                    "loan_term_months": app["loan_details"]["loan_term_months"],
                    "purpose": app["loan_details"]["purpose"],
                    "interest_rate": app["loan_details"]["interest_rate"],
                    "monthly_payment": app["loan_details"]["monthly_payment"],
                    "bank_name": app["banking_info"]["bank_name"],
                    "account_number": app["banking_info"]["account_number"],
                    "credit_score": app["financial_info"]["credit_score"],
                    "submission_date": app["application_details"]["submission_date"],
                    "application_status": app["application_details"]["application_status"],
                    "risk_level": app["risk_assessment"]["risk_level"]
                }
                writer.writerow(row)

        print(f"CSV数据已保存到: {filename}")

    def calculate_statistics(self, applications):
        """计算数据统计"""
        stats = {}

        if not applications:
            return stats

        # 贷款金额统计
        loan_amounts = [app["loan_details"]["loan_amount"] for app in applications]
        stats["loan_amount"] = {
            "min": min(loan_amounts),
            "max": max(loan_amounts),
            "average": sum(loan_amounts) / len(loan_amounts),
            "median": sorted(loan_amounts)[len(loan_amounts)//2]
        }

        # 收入统计
        incomes = [app["employment_info"]["monthly_income"] for app in applications]
        stats["monthly_income"] = {
            "min": min(incomes),
            "max": max(incomes),
            "average": sum(incomes) / len(incomes),
            "median": sorted(incomes)[len(incomes)//2]
        }

        # 信用分统计
        credit_scores = [app["financial_info"]["credit_score"] for app in applications]
        stats["credit_score"] = {
            "min": min(credit_scores),
            "max": max(credit_scores),
            "average": sum(credit_scores) / len(credit_scores),
            "median": sorted(credit_scores)[len(credit_scores)//2]
        }

        # 贷款用途分布
        purposes = [app["loan_details"]["purpose"] for app in applications]
        stats["loan_purpose_distribution"] = {}
        for purpose in purposes:
            stats["loan_purpose_distribution"][purpose] = purposes.count(purpose)

        # 就业类型分布
        employment_types = [app["employment_info"]["employment_type"] for app in applications]
        stats["employment_type_distribution"] = {}
        for emp_type in employment_types:
            stats["employment_type_distribution"][emp_type] = employment_types.count(emp_type)

        return stats

def main():
    generator = ThaiLoanApplicationGenerator()

    # 生成10000个真实泰国贷款申请
    applications = generator.generate_realistic_dataset(10000)

    # 保存到文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"THAI_LOAN_APPLICATIONS_{timestamp}.json"
    generator.save_applications_to_json(applications, filename)

    # 生成CSV格式的简化版本
    csv_filename = f"THAI_LOAN_APPLICATIONS_{timestamp}.csv"
    generator.save_applications_to_csv(applications, csv_filename)

    print(f"\n🎯 泰国贷款申请数据生成完成!")
    print(f"📊 总申请数: {len(applications)}")
    print(f"📁 JSON文件: {filename}")
    print(f"📁 CSV文件: {csv_filename}")

if __name__ == "__main__":
    main()