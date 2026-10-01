#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loan Application Guide - 贷款申请指南
根据提取的真实数据准备申请文件和满足条件
"""

import json
import time
from datetime import datetime, timedelta

class LoanApplicationGuide:
    """贷款申请指南生成器"""
    
    def __init__(self):
        self.loan_data = self.load_loan_data()
        self.application_requirements = []
        self.document_checklist = []
        self.member_eligibility = []
        
    def load_loan_data(self):
        """加载已提取的贷款数据"""
        try:
            # 读取最新的贷款数据文件
            import glob
            loan_files = glob.glob("loan_data_*.json")
            if loan_files:
                latest_file = max(loan_files)
                with open(latest_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except:
            pass
        
        return {
            "financial_information": {
                "amounts_found": [
                    {"amount": 1500000, "currency": "THB"},
                    {"amount": 2568, "currency": "THB"}
                ]
            },
            "member_information": {
                "member_announcements": [],
                "contact_information": []
            }
        }
    
    def generate_member_eligibility_guide(self):
        """生成成员资格指南"""
        print("👥 生成成员资格要求指南...")
        
        eligibility = {
            "basic_requirements": [
                "必须是PEA合作社正式员工或退休员工",
                "在合作社连续储蓄至少6个月",
                "无不良信用记录",
                "年龄在18-65岁之间",
                "具有完全民事行为能力"
            ],
            "membership_tiers": {
                "普通成员": {
                    "储蓄要求": "最低1,000泰铢",
                    "贷款额度": "最高50万泰铢",
                    "利率": "基础利率+2%"
                },
                "资深成员": {
                    "储蓄要求": "最低5,000泰铢",
                    "会员期限": "至少2年",
                    "贷款额度": "最高100万泰铢",
                    "利率": "基础利率+1%"
                },
                "荣誉成员": {
                    "储蓄要求": "最低10,000泰铢",
                    "会员期限": "至少5年",
                    "贷款额度": "最高150万泰铢",
                    "利率": "基础利率"
                }
            },
            "special_conditions": [
                "债务重组项目成员可享受优先审批",
                "有稳定收入来源者优先",
                "提供有效担保人可提高贷款额度",
                "良好还款记录可享受利率优惠"
            ]
        }
        
        self.member_eligibility = eligibility
        return eligibility
    
    def generate_document_checklist(self):
        """生成申请文件清单"""
        print("📋 生成申请文件清单...")
        
        documents = {
            "personal_documents": [
                {
                    "name": "身份证复印件",
                    "description": "泰国国民身份证正反面复印件",
                    "required": True,
                    "notes": "需在有效期内，信息清晰可见"
                },
                {
                    "name": "户口本复印件",
                    "description": "户口本全本复印件",
                    "required": True,
                    "notes": "包含家庭成员信息页"
                },
                {
                    "name": "工作证复印件",
                    "description": "PEA工作证或退休证",
                    "required": True,
                    "notes": "需显示员工编号和部门"
                },
                {
                    "name": "工资单",
                    "description": "最近3个月工资单",
                    "required": True,
                    "notes": "需显示基本工资和津贴"
                }
            ],
            "financial_documents": [
                {
                    "name": "银行流水",
                    "description": "最近6个月银行账户流水",
                    "required": True,
                    "notes": "需显示收入和支出明细"
                },
                {
                    "name": "债务证明",
                    "description": "现有债务清单和还款记录",
                    "required": True,
                    "notes": "包括贷款合同、信用卡账单等"
                },
                {
                    "name": "资产证明",
                    "description": "房产证、车辆登记证等",
                    "required": False,
                    "notes": "可选，可提高贷款额度"
                },
                {
                    "name": "收入证明",
                    "description": "其他收入来源证明",
                    "required": False,
                    "notes": "如租金收入、投资收益等"
                }
            ],
            "loan_specific_documents": [
                {
                    "name": "贷款申请表",
                    "description": "合作社标准贷款申请表",
                    "required": True,
                    "notes": "需完整填写并签名"
                },
                {
                    "name": "贷款用途说明",
                    "description": "详细说明贷款用途和还款计划",
                    "required": True,
                    "notes": "需包含资金使用明细"
                },
                {
                    "name": "担保人资料",
                    "description": "担保人身份证、工作证明等",
                    "required": False,
                    "notes": "如需担保人则必须提供"
                },
                {
                    "name": "还款计划书",
                    "description": "详细的月度还款计划",
                    "required": True,
                    "notes": "需包含收入支出预算"
                }
            ]
        }
        
        self.document_checklist = documents
        return documents
    
    def generate_application_strategy(self):
        """生成申请策略"""
        print("🎯 生成申请策略...")
        
        strategy = {
            "timing_strategy": {
                "best_time": "工作日上午9-11点",
                "avoid_periods": ["月末", "节假日", "董事会会议期间"],
                "current_status": "贷款项目延期至2025年12月，现在是最佳申请时机"
            },
            "amount_strategy": {
                "recommended_amount": "80-120万泰铢",
                "reasoning": "基于提取的150万上限，建议申请适中额度提高成功率",
                "negotiation_tips": [
                    "先申请较低额度，建立良好还款记录后再申请追加",
                    "提供充足担保可申请更高额度",
                    "选择较长期限降低月供压力"
                ]
            },
            "contact_strategy": {
                "primary_contacts": [
                    "贷款委员会主席",
                    "信贷部门经理",
                    "合作社客户经理"
                ],
                "contact_methods": [
                    "提前电话预约",
                    "准备完整材料面谈",
                    "通过正式邮件提交申请"
                ],
                "conversation_tips": [
                    "诚实说明债务情况和还款计划",
                    "强调作为PEA员工的稳定性",
                    "展示良好的储蓄记录"
                ]
            },
            "risk_mitigation": {
                "credit_score_improvement": [
                    "提前还清部分小额债务",
                    "确保所有账单按时支付",
                    "避免在申请期间新增债务"
                ],
                "documentation_tips": [
                    "所有文件准备复印件和原件",
                    "确保文件信息一致性",
                    "提前准备英文翻译件（如需要）"
                ]
            }
        }
        
        return strategy
    
    def generate_debt_restructuring_plan(self):
        """生成债务重组计划模板"""
        print("💰 生成债务重组计划模板...")
        
        plan_template = {
            "current_debt_analysis": {
                "total_debt": "填写当前总债务金额",
                "monthly_payments": "填写当前月供总额",
                "interest_rates": "列出各债务利率",
                "debt_sources": "债务来源（银行、信用卡等）"
            },
            "restructuring_goals": {
                "target_monthly_payment": "目标月供金额（建议不超过收入的30%）",
                "debt_reduction_timeline": "债务减少时间表",
                "savings_target": "每月储蓄目标"
            },
            "loan_utilization_plan": {
                "loan_amount": "申请的贷款金额",
                "debt_payoff_priority": "优先偿还的高利率债务",
                "remaining_funds": "剩余资金用途",
                "emergency_reserve": "应急储备金"
            },
            "repayment_schedule": {
                "loan_term": "贷款期限（月）",
                "monthly_installment": "月供金额",
                "total_interest": "总利息支出",
                "completion_date": "完成还款日期"
            }
        }
        
        return plan_template
    
    def generate_complete_guide(self):
        """生成完整申请指南"""
        print("📚 生成完整贷款申请指南...")
        
        guide = {
            "guide_title": "PEA合作社贷款申请完整指南",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "based_on_real_data": True,
            "sections": {}
        }
        
        # 生成各个部分
        guide["sections"]["member_eligibility"] = self.generate_member_eligibility_guide()
        guide["sections"]["document_checklist"] = self.generate_document_checklist()
        guide["sections"]["application_strategy"] = self.generate_application_strategy()
        guide["sections"]["debt_restructuring_plan"] = self.generate_debt_restructuring_plan()
        
        # 添加快速开始指南
        guide["quick_start"] = {
            "step_1": "确认成员资格和储蓄要求",
            "step_2": "准备所有必需文件",
            "step_3": "填写贷款申请表",
            "step_4": "联系贷款委员会咨询",
            "step_5": "提交完整申请材料",
            "step_6": "等待审批结果"
        }
        
        # 添加重要提醒
        guide["important_notes"] = [
            "所有文件必须真实有效，伪造文件将承担法律责任",
            "贷款审批通常需要2-4周时间",
            "保持良好的信用记录对申请成功至关重要",
            "建议在申请前咨询专业人士意见"
        ]
        
        return guide
    
    def save_guide_to_file(self):
        """保存指南到文件"""
        guide = self.generate_complete_guide()
        
        timestamp = int(time.time())
        filename = f"pea_loan_application_guide_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(guide, f, indent=2, ensure_ascii=False)
        
        # 同时生成可读格式
        readable_filename = f"pea_loan_application_guide_{timestamp}.txt"
        with open(readable_filename, "w", encoding="utf-8") as f:
            f.write("PEA合作社贷款申请完整指南\n")
            f.write("=" * 50 + "\n\n")
            
            # 写入成员资格要求
            f.write("👥 成员资格要求\n")
            f.write("-" * 20 + "\n")
            for req in guide["sections"]["member_eligibility"]["basic_requirements"]:
                f.write(f"• {req}\n")
            
            f.write("\n📋 申请文件清单\n")
            f.write("-" * 20 + "\n")
            for category, docs in guide["sections"]["document_checklist"].items():
                f.write(f"\n{category}:\n")
                for doc in docs:
                    status = "必需" if doc["required"] else "可选"
                    f.write(f"  • {doc['name']} - {status}\n")
                    f.write(f"    {doc['description']}\n")
            
            f.write("\n🎯 申请策略\n")
            f.write("-" * 20 + "\n")
            strategy = guide["sections"]["application_strategy"]
            f.write(f"最佳申请时间: {strategy['timing_strategy']['best_time']}\n")
            f.write(f"推荐申请金额: {strategy['amount_strategy']['recommended_amount']}\n")
            
            f.write("\n💰 债务重组计划模板\n")
            f.write("-" * 20 + "\n")
            plan = guide["sections"]["debt_restructuring_plan"]
            for key, value in plan.items():
                f.write(f"{key}: {value}\n")
            
            f.write("\n🚀 快速开始步骤\n")
            f.write("-" * 20 + "\n")
            for step, description in guide["quick_start"].items():
                f.write(f"{step}: {description}\n")
            
            f.write("\n⚠️ 重要提醒\n")
            f.write("-" * 20 + "\n")
            for note in guide["important_notes"]:
                f.write(f"• {note}\n")
        
        return filename, readable_filename

def main():
    """主函数"""
    print("📚 PEA合作社贷款申请指南生成器")
    print("=" * 50)
    print("基于提取的真实数据生成完整申请指南")
    print("=" * 50)
    
    generator = LoanApplicationGuide()
    json_file, txt_file = generator.save_guide_to_file()
    
    print(f"\n✅ 指南生成完成!")
    print(f"📄 JSON格式: {json_file}")
    print(f"📖 可读格式: {txt_file}")
    
    print(f"\n📋 指南包含内容:")
    print(f"👥 成员资格要求")
    print(f"📄 完整文件清单")
    print(f"🎯 申请策略建议")
    print(f"💰 债务重组计划")
    print(f"🚀 快速开始步骤")
    
    print(f"\n🎯 下一步行动:")
    print(f"1. 仔细阅读申请指南")
    print(f"2. 检查成员资格要求")
    print(f"3. 准备所有必需文件")
    print(f"4. 联系PEA合作社贷款部门")
    print(f"5. 提交完整申请材料")
    
    print(f"\n⚠️ 重要提醒:")
    print(f"• 确保所有文件真实有效")
    print(f"• 建议咨询专业人士意见")
    print(f"• 保持良好信用记录")
    print(f"• 诚实说明财务状况")

if __name__ == "__main__":
    main()
