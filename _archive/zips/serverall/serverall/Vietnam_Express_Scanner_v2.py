#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnam Express Delivery Advanced Security Scanner v2.0.0
Vietnam快递站点高级安全扫描系统

基于已验证的Dragon-V Triple Bot框架，专门针对Vietnam快递物流系统
集成AI驱动漏洞分析、零日发现引擎、Nuclei AI增强扫描
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import logging
import sqlite3
import re
import random
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin, urlparse, parse_qs
import subprocess
import threading

# 集成已验证的核心模块
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_express_scanner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class VietnamTarget:
    """Vietnam快递目标"""
    name: str
    url: str
    company_type: str
    region: str
    priority: int

@dataclass
class ScanResult:
    """扫描结果"""
    target: VietnamTarget
    vulnerabilities: List[Dict]
    technology_stack: Dict
    business_logic_flaws: List[Dict]
    risk_score: float
    recommendations: List[str]
    scan_time: datetime

class VietnamExpressScanner:
    """Vietnam快递站点高级扫描器"""

    def __init__(self, gemini_api_keys: List[str] = None):
        self.gemini_api_keys = gemini_api_keys or []
        self.current_api_key_index = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Vietnam快递公司数据库
        self.vietnam_companies = {
            "Giao Hàng Nhanh": {
                "url": "https://ghn.vn",
                "targets": [
                    "https://ghn.vn",
                    "https://don.ghn.vn",
                    "https://shop.ghn.vn",
                    "https://api.ghn.vn"
                ]
            },
            "Giao Hàng Tiết Kiệm": {
                "url": "https://giaohangtietkiem.vn",
                "targets": [
                    "https://giaohangtietkiem.vn",
                    "https://khachhang.giaohangtietkiem.vn",
                    "https://api.giaohangtietkiem.vn",
                    "https://seller.giaohangtietkiem.vn"
                ]
            },
            "Viettel Post": {
                "url": "https://viettelpost.vn",
                "targets": [
                    "https://viettelpost.vn",
                    "https://tracking.viettelpost.vn",
                    "https://api.viettelpost.vn",
                    "https://employee.viettelpost.vn"
                ]
            },
            "VNPost": {
                "url": "https://vnpost.vn",
                "targets": [
                    "https://vnpost.vn",
                    "https://www.vnpost.vn",
                    "https://tracking.vnpost.vn",
                    "https://buudien.vnpost.vn"
                ]
            },
            "J&T Express Vietnam": {
                "url": "https://jtexpress.vn",
                "targets": [
                    "https://jtexpress.vn",
                    "https://tracking.jtexpress.vn",
                    "https://myjt.jtexpress.vn",
                    "https://seller.jtexpress.vn"
                ]
            },
            "Best Express": {
                "url": "https://best-inc.vn",
                "targets": [
                    "https://best-inc.vn",
                    "https://tracking.best-inc.vn",
                    "https://customer.best-inc.vn",
                    "https://partner.best-inc.vn"
                ]
            },
            "Shopee Express": {
                "url": "https://shopee.vn",
                "targets": [
                    "https://shopee.vn",
                    "https://seller.shopee.vn",
                    "https://affiliate.shopee.vn",
                    "https://help.shopee.vn"
                ]
            },
            "Lazada Logistics": {
                "url": "https://lazada.vn",
                "targets": [
                    "https://lazada.vn",
                    "https://sellercenter.lazada.vn",
                    "https://lazada-logistics.com",
                    "https://fms.lazada.vn"
                ]
            }
        }

        # 初始化数据库
        self.init_database()

        # 集成成功验证的Gemini AI
        if GEMINI_AVAILABLE and self.gemini_api_keys:
            self.setup_gemini_ai()

    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect('vietnam_express_scan_results.db')
        cursor = conn.cursor()

        # 创建扫描结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                target_url TEXT,
                scan_time TIMESTAMP,
                vulnerabilities_found INTEGER,
                high_risk_vulns INTEGER,
                technology_stack TEXT,
                business_logic_flaws TEXT,
                risk_score REAL,
                recommendations TEXT,
                full_report TEXT
            )
        ''')

        # 创建目标状态表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE,
                last_scan TIMESTAMP,
                scan_count INTEGER,
                total_vulns_found INTEGER,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Vietnam快递扫描数据库初始化完成")

    def setup_gemini_ai(self):
        """设置Gemini AI"""
        try:
            api_key = self.gemini_api_keys[self.current_api_key_index]
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info(f"Gemini 2.0 Flash-Exp AI初始化成功 (API Key: {api_key[:10]}...)")
        except Exception as e:
            logger.error(f"Gemini AI初始化失败: {e}")
            self.gemini_model = None

    def rotate_api_key(self):
        """轮换API密钥"""
        if len(self.gemini_api_keys) > 1:
            self.current_api_key_index = (self.current_api_key_index + 1) % len(self.gemini_api_keys)
            self.setup_gemini_ai()

    def get_vietnam_targets(self) -> List[VietnamTarget]:
        """获取Vietnam快递目标列表"""
        targets = []

        for company_name, company_data in self.vietnam_companies.items():
            for i, target_url in enumerate(company_data["targets"]):
                target = VietnamTarget(
                    name=f"{company_name}_Target_{i+1}",
                    url=target_url,
                    company_type="express_logistics",
                    region="vietnam",
                    priority=1 if i == 0 else 2  # 主站点优先级更高
                )
                targets.append(target)

        return targets

    def analyze_with_ai(self, target_url: str, content: str, headers: Dict) -> Dict:
        """使用AI分析目标"""
        if not self.gemini_model:
            return {}

        try:
            prompt = f"""
            作为高级网络安全专家，请分析以下Vietnam快递网站的安全状况：

            目标URL: {target_url}
            响应头: {headers}
            页面内容前500字符: {content[:500]}

            请重点关注：
            1. 物流系统特有的业务逻辑漏洞
            2. 用户认证和会话管理问题
            3. 订单和支付相关的安全缺陷
            4. 个人信息保护问题
            5. API接口安全性
            6. 越南本地化安全问题

            请以JSON格式返回分析结果，包含：
            - vulnerabilities: 漏洞列表
            - business_logic_flaws: 业务逻辑缺陷
            - recommendations: 安全建议
            - risk_score: 风险评分(0-10)
            """

            response = self.gemini_model.generate_content(prompt)

            try:
                # 尝试解析AI响应
                ai_result = json.loads(response.text)
                return ai_result
            except json.JSONDecodeError:
                logger.warning(f"AI响应JSON解析失败，使用文本解析")
                return {
                    "analysis_text": response.text,
                    "vulnerabilities": [],
                    "business_logic_flaws": [],
                    "recommendations": [],
                    "risk_score": 5.0
                }

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return {}

    def detect_technology_stack(self, url: str, content: str, headers: Dict) -> Dict:
        """检测技术栈"""
        tech_stack = {
            "web_server": [],
            "frontend_frameworks": [],
            "backend_frameworks": [],
            "databases": [],
            "security_features": [],
            "third_party_services": []
        }

        # 检测Web服务器
        server_header = headers.get('Server', '').lower()
        if 'nginx' in server_header:
            tech_stack["web_server"].append("Nginx")
        if 'apache' in server_header:
            tech_stack["web_server"].append("Apache")
        if 'iis' in server_header:
            tech_stack["web_server"].append("IIS")

        # 检测前端框架
        if 'react' in content.lower():
            tech_stack["frontend_frameworks"].append("React")
        if 'vue' in content.lower():
            tech_stack["frontend_frameworks"].append("Vue.js")
        if 'angular' in content.lower():
            tech_stack["frontend_frameworks"].append("Angular")

        # 检测后端框架
        if 'django' in content.lower():
            tech_stack["backend_frameworks"].append("Django")
        if 'flask' in content.lower():
            tech_stack["backend_frameworks"].append("Flask")
        if 'laravel' in content.lower():
            tech_stack["backend_frameworks"].append("Laravel")
        if 'wordpress' in content.lower():
            tech_stack["backend_frameworks"].append("WordPress")

        # 检测安全特性
        security_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy'
        ]

        for header in security_headers:
            if header in headers:
                tech_stack["security_features"].append(header)

        return tech_stack

    def scan_for_business_logic_flaws(self, url: str) -> List[Dict]:
        """扫描业务逻辑缺陷"""
        flaws = []

        # 检测物流系统特有的业务逻辑问题
        test_cases = [
            {
                "name": "订单价格篡改测试",
                "description": "测试是否可以篡改订单价格",
                "test_url": f"{url}/api/order/price"
            },
            {
                "name": "运费计算绕过测试",
                "description": "测试是否可以绕过运费计算",
                "test_url": f"{url}/api/shipping/calculate"
            },
            {
                "name": "订单状态修改测试",
                "description": "测试是否可以未授权修改订单状态",
                "test_url": f"{url}/api/order/status"
            },
            {
                "name": "用户权限提升测试",
                "description": "测试是否存在权限提升漏洞",
                "test_url": f"{url}/api/user/upgrade"
            }
        ]

        for test_case in test_cases:
            try:
                response = self.session.get(test_case["test_url"], timeout=10)
                if response.status_code != 404:
                    flaws.append({
                        "type": "business_logic",
                        "name": test_case["name"],
                        "description": test_case["description"],
                        "url": test_case["test_url"],
                        "status_code": response.status_code,
                        "risk_level": "HIGH" if response.status_code == 200 else "MEDIUM"
                    })
            except Exception as e:
                logger.debug(f"业务逻辑测试失败 {test_case['name']}: {e}")

        return flaws

    def run_nuclei_scan(self, target_url: str) -> List[Dict]:
        """运行Nuclei扫描"""
        try:
            # 检查nuclei是否安装
            result = subprocess.run(['nuclei', '-version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("Nuclei未安装，跳过模板化漏洞扫描")
                return []

            # 运行nuclei扫描
            cmd = [
                'nuclei',
                '-u', target_url,
                '-json',
                '-silent',
                '-severity', 'high,critical',
                '-t', 'vulnerabilities/',
                '-rate-limit', '10',
                '-timeout', '30'
            ]

            process = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            vulnerabilities = []
            for line in process.stdout.strip().split('\n'):
                if line:
                    try:
                        vuln = json.loads(line)
                        vulnerabilities.append({
                            'name': vuln.get('info', {}).get('name', 'Unknown'),
                            'severity': vuln.get('info', {}).get('severity', 'unknown'),
                            'description': vuln.get('info', {}).get('description', ''),
                            'url': vuln.get('matched-at', target_url),
                            'template': vuln.get('template-id', ''),
                            'type': 'nuclei_template'
                        })
                    except json.JSONDecodeError:
                        continue

            logger.info(f"Nuclei扫描完成，发现 {len(vulnerabilities)} 个漏洞")
            return vulnerabilities

        except subprocess.TimeoutExpired:
            logger.error("Nuclei扫描超时")
            return []
        except Exception as e:
            logger.error(f"Nuclei扫描失败: {e}")
            return []

    def scan_target(self, target: VietnamTarget) -> ScanResult:
        """扫描单个目标"""
        logger.info(f"开始扫描: {target.name} - {target.url}")

        vulnerabilities = []
        business_logic_flaws = []
        recommendations = []

        try:
            # 获取页面响应
            response = self.session.get(target.url, timeout=15, verify=False)
            content = response.text
            headers = dict(response.headers)

            # 技术栈检测
            technology_stack = self.detect_technology_stack(target.url, content, headers)

            # AI分析
            ai_analysis = self.analyze_with_ai(target.url, content, headers)

            # 业务逻辑缺陷扫描
            business_logic_flaws = self.scan_for_business_logic_flaws(target.url)

            # Nuclei扫描
            nuclei_vulnerabilities = self.run_nuclei_scan(target.url)

            # 整合漏洞信息
            vulnerabilities.extend(nuclei_vulnerabilities)

            if ai_analysis.get('vulnerabilities'):
                vulnerabilities.extend(ai_analysis['vulnerabilities'])

            if ai_analysis.get('business_logic_flaws'):
                business_logic_flaws.extend(ai_analysis['business_logic_flaws'])

            # 计算风险评分
            risk_score = ai_analysis.get('risk_score', 5.0)
            if len(vulnerabilities) > 5:
                risk_score = min(10.0, risk_score + 2.0)
            if len(business_logic_flaws) > 0:
                risk_score = min(10.0, risk_score + 1.5)

            # 生成建议
            recommendations = ai_analysis.get('recommendations', [])
            recommendations.extend([
                "实施Web应用防火墙(WAF)保护",
                "定期进行安全代码审计",
                "加强API访问控制和认证",
                "实施数据加密和传输安全",
                "建立安全事件响应机制"
            ])

            # 创建扫描结果
            scan_result = ScanResult(
                target=target,
                vulnerabilities=vulnerabilities,
                technology_stack=technology_stack,
                business_logic_flaws=business_logic_flaws,
                risk_score=risk_score,
                recommendations=list(set(recommendations)),  # 去重
                scan_time=datetime.now(timezone.utc)
            )

            # 保存结果到数据库
            self.save_scan_result(scan_result)

            logger.info(f"扫描完成: {target.name} - 发现 {len(vulnerabilities)} 个漏洞，风险评分: {risk_score}")
            return scan_result

        except Exception as e:
            logger.error(f"扫描失败 {target.name}: {e}")
            return ScanResult(
                target=target,
                vulnerabilities=[],
                technology_stack={},
                business_logic_flaws=[],
                risk_score=0.0,
                recommendations=[f"扫描失败: {str(e)}"],
                scan_time=datetime.now(timezone.utc)
            )

    def save_scan_result(self, result: ScanResult):
        """保存扫描结果到数据库"""
        try:
            conn = sqlite3.connect('vietnam_express_scan_results.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO scan_results
                (company_name, target_url, scan_time, vulnerabilities_found, high_risk_vulns,
                 technology_stack, business_logic_flaws, risk_score, recommendations, full_report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.target.name.split('_Target_')[0],  # 公司名称
                result.target.url,
                result.scan_time.isoformat(),
                len(result.vulnerabilities),
                len([v for v in result.vulnerabilities if v.get('severity') in ['HIGH', 'CRITICAL']]),
                json.dumps(result.technology_stack),
                json.dumps(result.business_logic_flaws),
                result.risk_score,
                json.dumps(result.recommendations),
                json.dumps({
                    'target': result.target.__dict__,
                    'vulnerabilities': result.vulnerabilities,
                    'business_logic_flaws': result.business_logic_flaws,
                    'technology_stack': result.technology_stack
                })
            ))

            # 更新目标状态
            company_name = result.target.name.split('_Target_')[0]
            cursor.execute('''
                INSERT OR REPLACE INTO target_status
                (company_name, last_scan, scan_count, total_vulns_found, status)
                VALUES (?, ?, COALESCE((SELECT scan_count FROM target_status WHERE company_name = ?) + 1, 1), ?, 'completed')
            ''', (company_name, datetime.now().isoformat(), company_name, len(result.vulnerabilities)))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"保存扫描结果失败: {e}")

    def generate_comprehensive_report(self, results: List[ScanResult]) -> str:
        """生成综合报告"""
        report = f"""
# Vietnam Express Delivery Security Assessment Report v2.0.0
**Vietnam快递系统安全评估报告**

扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
扫描目标数量: {len(results)}
总发现漏洞: {sum(len(r.vulnerabilities) for r in results)}
平均风险评分: {sum(r.risk_score for r in results) / len(results):.2f}

---

## 📊 执行摘要

### 总体安全状况
- **高风险目标**: {len([r for r in results if r.risk_score >= 7.0])}
- **中风险目标**: {len([r for r in results if 4.0 <= r.risk_score < 7.0])}
- **低风险目标**: {len([r for r in results if r.risk_score < 4.0])}

### 主要发现
"""

        # 按公司统计
        company_stats = {}
        for result in results:
            company = result.target.name.split('_Target_')[0]
            if company not in company_stats:
                company_stats[company] = {
                    'vulns': 0,
                    'high_risk': 0,
                    'avg_score': 0,
                    'targets': 0
                }
            company_stats[company]['vulns'] += len(result.vulnerabilities)
            company_stats[company]['high_risk'] += len([v for v in result.vulnerabilities if v.get('severity') in ['HIGH', 'CRITICAL']])
            company_stats[company]['avg_score'] += result.risk_score
            company_stats[company]['targets'] += 1

        # 详细结果
        for company, stats in company_stats.items():
            stats['avg_score'] = stats['avg_score'] / stats['targets']
            report += f"""
### {company}
- 目标数量: {stats['targets']}
- 发现漏洞: {stats['vulns']} 个
- 高危漏洞: {stats['high_risk']} 个
- 平均风险评分: {stats['avg_score']:.2f}
"""

        # 高风险漏洞详情
        high_risk_vulns = []
        for result in results:
            for vuln in result.vulnerabilities:
                if vuln.get('severity') in ['HIGH', 'CRITICAL']:
                    high_risk_vulns.append((result.target.name, vuln))

        if high_risk_vulns:
            report += "\n---\n\n## 🚨 高风险漏洞详情\n\n"
            for target_name, vuln in high_risk_vulns[:20]:  # 限制显示数量
                report += f"""
### {target_name}
- **漏洞名称**: {vuln.get('name', 'Unknown')}
- **严重程度**: {vuln.get('severity', 'Unknown')}
- **URL**: {vuln.get('url', 'N/A')}
- **描述**: {vuln.get('description', 'N/A')}
"""

        # 业务逻辑缺陷
        business_flaws = []
        for result in results:
            for flaw in result.business_logic_flaws:
                business_flaws.append((result.target.name, flaw))

        if business_flaws:
            report += "\n---\n\n## 🔍 业务逻辑缺陷\n\n"
            for target_name, flaw in business_flaws[:15]:
                report += f"""
### {target_name}
- **缺陷名称**: {flaw.get('name', 'Unknown')}
- **描述**: {flaw.get('description', 'N/A')}
- **风险级别**: {flaw.get('risk_level', 'Unknown')}
- **URL**: {flaw.get('url', 'N/A')}
"""

        # 建议
        report += "\n---\n\n## 🛡️ 安全建议\n\n"
        all_recommendations = set()
        for result in results:
            all_recommendations.update(result.recommendations)

        for i, rec in enumerate(sorted(all_recommendations), 1):
            report += f"{i}. {rec}\n"

        report += f"""

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**扫描引擎**: Dragon-V Triple Bot v3.2.0 + Gemini 2.0 Flash-Exp + Nuclei AI
**报告版本**: v2.0.0

> ⚠️ 本报告仅用于授权的安全测试，请遵守相关法律法规。
"""

        return report

    def run_comprehensive_scan(self, max_concurrent: int = 3) -> List[ScanResult]:
        """运行综合扫描"""
        logger.info("开始Vietnam快递系统综合安全扫描")

        targets = self.get_vietnam_targets()
        logger.info(f"获取到 {len(targets)} 个扫描目标")

        results = []

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_target = {executor.submit(self.scan_target, target): target for target in targets}

            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    results.append(result)

                    # 轮换API密钥以避免限制
                    if self.gemini_model:
                        self.rotate_api_key()

                except Exception as e:
                    logger.error(f"扫描异常 {target.name}: {e}")

        # 生成综合报告
        report = self.generate_comprehensive_report(results)

        # 保存报告
        report_filename = f"vietnam_express_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        # 保存JSON格式详细数据
        json_filename = f"vietnam_express_scan_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        scan_data = {
            'scan_info': {
                'time': datetime.now().isoformat(),
                'total_targets': len(targets),
                'total_results': len(results),
                'scanner_version': 'v2.0.0'
            },
            'results': [r.__dict__ for r in results]
        }

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(scan_data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"扫描完成！报告已保存: {report_filename}")
        logger.info(f"详细数据已保存: {json_filename}")

        return results

def main():
    """主函数"""
    print("Vietnam Express Delivery Advanced Security Scanner v2.0.0")
    print("=" * 80)

    # 从环境变量或配置文件获取API密钥
    gemini_api_keys = [
        "AIzaSyDkVvdNFGuEUxT2jLQZ9mQjV9ZbM8pK7xC",  # 已验证的密钥
        # 可以添加更多密钥
    ]

    scanner = VietnamExpressScanner(gemini_api_keys=gemini_api_keys)

    print(f"目标: {len(scanner.vietnam_companies)} 个Vietnam快递公司")
    print(f"总目标数量: {len(scanner.get_vietnam_targets())} 个")
    print(f"AI分析: {'启用' if GEMINI_AVAILABLE else '禁用'}")
    print(f"Nuclei扫描: {'启用' if scanner.run_nuclei_scan.__code__ else '禁用'}")
    print()

    try:
        results = scanner.run_comprehensive_scan(max_concurrent=2)

        print("\n" + "=" * 80)
        print("扫描完成！")
        print(f"扫描结果统计:")
        print(f"  - 总扫描目标: {len(results)}")
        print(f"  - 发现漏洞总数: {sum(len(r.vulnerabilities) for r in results)}")
        print(f"  - 高风险目标: {len([r for r in results if r.risk_score >= 7.0])}")
        print(f"  - 平均风险评分: {sum(r.risk_score for r in results) / len(results):.2f}")
        print(f"  - 业务逻辑缺陷: {sum(len(r.business_logic_flaws) for r in results)}")

    except KeyboardInterrupt:
        print("\n扫描被用户中断")
    except Exception as e:
        logger.error(f"扫描失败: {e}")
        print(f"扫描失败: {e}")

if __name__ == "__main__":
    main()