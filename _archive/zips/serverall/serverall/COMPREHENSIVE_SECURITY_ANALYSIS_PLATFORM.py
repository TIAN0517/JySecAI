#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合安全分析平台
Comprehensive Security Analysis Platform for Dragon-V Triple Bot v3.2.0

集成CVE数据库、智能查询、漏洞匹配、风险评估等功能的一体化平台
"""

import os
import sys
import yaml
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
import logging

# 导入我们开发的组件
try:
    from INTELLIGENT_CVE_ANALYSIS_SYSTEM import IntelligentCVEAnalysisSystem
    from AUTOMATED_VULNERABILITY_MATCHING_ENGINE import AutomatedVulnerabilityMatchingEngine
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保相关模块文件存在")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_analysis_platform.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveSecurityAnalysisPlatform:
    """综合安全分析平台"""

    def __init__(self):
        """初始化平台"""
        logger.info("初始化综合安全分析平台...")

        # 初始化核心组件
        self.cve_analyzer = IntelligentCVEAnalysisSystem()
        self.vulnerability_matcher = AutomatedVulnerabilityMatchingEngine()

        # 平台状态
        self.platform_status = {
            'initialized': True,
            'cve_database_loaded': len(self.cve_analyzer.cve_database) > 0,
            'fingerprint_database_loaded': len(self.vulnerability_matcher.fingerprint_database) > 0,
            'last_analysis': None,
            'total_analyses': 0
        }

        # 分析历史
        self.analysis_history = []

        logger.info("综合安全分析平台初始化完成")

    def get_platform_status(self) -> Dict[str, Any]:
        """获取平台状态"""
        return {
            'platform_info': {
                'name': 'Dragon-V Triple Bot 综合安全分析平台',
                'version': '3.2.0',
                'status': 'operational' if self.platform_status['initialized'] else 'offline'
            },
            'database_status': {
                'cve_entries': len(self.cve_analyzer.cve_database),
                'fingerprints': len(self.vulnerability_matcher.fingerprint_database),
                'last_updated': datetime.now().isoformat()
            },
            'analysis_statistics': {
                'total_analyses': self.platform_status['total_analyses'],
                'last_analysis': self.platform_status['last_analysis']
            },
            'capabilities': [
                'CVE智能查询',
                '全文搜索',
                '统计分析',
                '漏洞匹配',
                '风险评估',
                '报告生成',
                '批量扫描',
                '趋势分析'
            ]
        }

    def comprehensive_target_analysis(self, target_url: str, analysis_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """对目标进行全面安全分析"""
        logger.info(f"开始对目标进行全面分析: {target_url}")

        analysis_options = analysis_options or {
            'include_cve_analysis': True,
            'include_vulnerability_matching': True,
            'include_risk_assessment': True,
            'include_trend_analysis': False,
            'scan_depth': 'standard'
        }

        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(target_url) % 10000}"

        comprehensive_result = {
            'analysis_id': analysis_id,
            'target_url': target_url,
            'analysis_time': datetime.now().isoformat(),
            'analysis_options': analysis_options,
            'results': {},
            'summary': {}
        }

        try:
            # 第一阶段：漏洞匹配扫描
            if analysis_options.get('include_vulnerability_matching', True):
                logger.info("执行漏洞匹配扫描...")
                scan_result = self.vulnerability_matcher.scan_target(target_url)
                comprehensive_result['results']['vulnerability_scan'] = scan_result

            # 第二阶段：CVE相关性分析
            if analysis_options.get('include_cve_analysis', True):
                logger.info("执行CVE相关性分析...")
                cve_analysis = self._perform_cve_analysis(comprehensive_result['results'].get('vulnerability_scan', {}))
                comprehensive_result['results']['cve_analysis'] = cve_analysis

            # 第三阶段：风险评估
            if analysis_options.get('include_risk_assessment', True):
                logger.info("执行风险评估...")
                risk_assessment = self._perform_risk_assessment(comprehensive_result['results'])
                comprehensive_result['results']['risk_assessment'] = risk_assessment

            # 第四阶段：生成综合摘要
            comprehensive_result['summary'] = self._generate_analysis_summary(comprehensive_result['results'])

            # 更新平台状态
            self.platform_status['last_analysis'] = datetime.now().isoformat()
            self.platform_status['total_analyses'] += 1

            # 保存分析历史
            self.analysis_history.append(comprehensive_result)

            logger.info(f"全面分析完成: {analysis_id}")

        except Exception as e:
            logger.error(f"全面分析失败: {e}")
            comprehensive_result['error'] = str(e)

        return comprehensive_result

    def _perform_cve_analysis(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行CVE相关性分析"""
        cve_analysis = {
            'related_cves': [],
            'severity_distribution': {},
            'top_vulnerabilities': [],
            'recommendation_priorities': []
        }

        try:
            # 获取匹配的漏洞
            matched_vulns = scan_result.get('matched_vulnerabilities', [])
            detected_components = scan_result.get('detected_components', [])

            # 分析相关的CVE
            for vuln in matched_vulns:
                cve_id = vuln.get('cve_id')
                if cve_id:
                    # 查找相关的CVE
                    related_cves = self.cve_analyzer.find_related_cves(cve_id, similarity_threshold=0.3)
                    cve_analysis['related_cves'].extend(related_cves[:5])  # 限制数量

            # 统计严重程度分布
            severity_counts = Counter(vuln.get('severity', 'unknown') for vuln in matched_vulns)
            cve_analysis['severity_distribution'] = dict(severity_counts)

            # 获取推荐修复优先级
            priorities = self.cve_analyzer.recommend_priorities(10)
            cve_analysis['recommendation_priorities'] = priorities[:5]

        except Exception as e:
            logger.warning(f"CVE分析出错: {e}")

        return cve_analysis

    def _perform_risk_assessment(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行风险评估"""
        risk_assessment = {
            'overall_risk': 'low',
            'risk_score': 0.0,
            'risk_factors': [],
            'mitigation_strategies': [],
            'compliance_status': 'unknown'
        }

        try:
            # 基于漏洞扫描结果的风险评估
            vulnerability_scan = analysis_results.get('vulnerability_scan', {})
            scan_risk = vulnerability_scan.get('risk_assessment', {})

            # 基于CVE分析的风险评估
            cve_analysis = analysis_results.get('cve_analysis', {})
            cve_risk_factors = []

            # 计算综合风险分数
            risk_score = scan_risk.get('risk_score', 0)

            # 添加风险因素
            if scan_risk.get('critical_count', 0) > 0:
                cve_risk_factors.append(f"发现 {scan_risk.get('critical_count')} 个严重漏洞")

            if scan_risk.get('high_count', 0) > 2:
                cve_risk_factors.append(f"发现 {scan_risk.get('high_count')} 个高危漏洞")

            if vulnerability_scan.get('detected_components'):
                cve_risk_factors.append("检测到多个应用组件")

            # 确定风险等级
            if risk_score >= 70:
                overall_risk = 'critical'
            elif risk_score >= 50:
                overall_risk = 'high'
            elif risk_score >= 30:
                overall_risk = 'medium'
            else:
                overall_risk = 'low'

            # 生成缓解策略
            mitigation_strategies = [
                "立即修复严重和高危漏洞",
                "定期进行安全扫描",
                "加强安全配置管理",
                "建立安全监控机制"
            ]

            if scan_risk.get('critical_count', 0) > 0:
                mitigation_strategies.insert(0, "紧急处理严重漏洞")

            risk_assessment = {
                'overall_risk': overall_risk,
                'risk_score': min(risk_score, 100),
                'risk_factors': cve_risk_factors,
                'mitigation_strategies': mitigation_strategies,
                'compliance_status': self._assess_compliance(analysis_results)
            }

        except Exception as e:
            logger.warning(f"风险评估出错: {e}")

        return risk_assessment

    def _assess_compliance(self, analysis_results: Dict[str, Any]) -> str:
        """评估合规性状态"""
        try:
            vulnerability_scan = analysis_results.get('vulnerability_scan', {})
            risk_assessment = vulnerability_scan.get('risk_assessment', {})

            critical_count = risk_assessment.get('critical_count', 0)
            high_count = risk_assessment.get('high_count', 0)

            if critical_count == 0 and high_count <= 1:
                return 'compliant'
            elif critical_count == 0 and high_count <= 3:
                return 'partial_compliant'
            else:
                return 'non_compliant'

        except Exception:
            return 'unknown'

    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            'key_findings': [],
            'risk_level': 'low',
            'action_items': [],
            'metrics': {}
        }

        try:
            vulnerability_scan = analysis_results.get('vulnerability_scan', {})
            cve_analysis = analysis_results.get('cve_analysis', {})
            risk_assessment = analysis_results.get('risk_assessment', {})

            # 关键发现
            key_findings = []

            detected_components = len(vulnerability_scan.get('detected_components', []))
            if detected_components > 0:
                key_findings.append(f"检测到 {detected_components} 个应用组件")

            matched_vulns = len(vulnerability_scan.get('matched_vulnerabilities', []))
            if matched_vulns > 0:
                key_findings.append(f"发现 {matched_vulns} 个匹配的漏洞")

            if risk_assessment.get('risk_factors'):
                key_findings.extend(risk_assessment['risk_factors'])

            # 行动项目
            action_items = []

            if matched_vulns > 0:
                action_items.append("立即修复已发现的漏洞")
                action_items.append("制定漏洞修复计划")

            if detected_components > 5:
                action_items.append("简化应用架构以减少攻击面")

            action_items.extend(risk_assessment.get('mitigation_strategies', [])[:3])

            # 指标
            metrics = {
                'components_detected': detected_components,
                'vulnerabilities_found': matched_vulns,
                'risk_score': risk_assessment.get('risk_score', 0),
                'compliance_status': risk_assessment.get('compliance_status', 'unknown')
            }

            summary = {
                'key_findings': key_findings,
                'risk_level': risk_assessment.get('overall_risk', 'low'),
                'action_items': action_items,
                'metrics': metrics
            }

        except Exception as e:
            logger.warning(f"生成摘要出错: {e}")

        return summary

    def batch_comprehensive_analysis(self, targets: List[str], analysis_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """批量进行全面分析"""
        logger.info(f"开始批量全面分析 {len(targets)} 个目标")

        batch_results = {
            'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'total_targets': len(targets),
            'analysis_options': analysis_options,
            'results': [],
            'summary': {}
        }

        for i, target in enumerate(targets, 1):
            try:
                logger.info(f"分析目标 {i}/{len(targets)}: {target}")
                result = self.comprehensive_target_analysis(target, analysis_options)
                batch_results['results'].append(result)
            except Exception as e:
                logger.error(f"批量分析目标 {target} 失败: {e}")
                batch_results['results'].append({
                    'target_url': target,
                    'error': str(e),
                    'analysis_time': datetime.now().isoformat()
                })

        # 生成批量分析摘要
        batch_results['summary'] = self._generate_batch_summary(batch_results['results'])
        batch_results['end_time'] = datetime.now().isoformat()

        logger.info("批量全面分析完成")
        return batch_results

    def _generate_batch_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成批量分析摘要"""
        summary = {
            'total_analyzed': len(results),
            'successful_analyses': 0,
            'failed_analyses': 0,
            'risk_distribution': {},
            'overall_metrics': {},
            'top_risks': []
        }

        risk_counts = Counter()
        total_risk_score = 0
        total_components = 0
        total_vulnerabilities = 0

        for result in results:
            if 'error' in result:
                summary['failed_analyses'] += 1
            else:
                summary['successful_analyses'] += 1

                summary_data = result.get('summary', {})
                metrics = summary_data.get('metrics', {})

                risk_level = summary_data.get('risk_level', 'low')
                risk_counts[risk_level] += 1

                total_risk_score += metrics.get('risk_score', 0)
                total_components += metrics.get('components_detected', 0)
                total_vulnerabilities += metrics.get('vulnerabilities_found', 0)

        summary['risk_distribution'] = dict(risk_counts)
        summary['overall_metrics'] = {
            'avg_risk_score': total_risk_score / max(summary['successful_analyses'], 1),
            'total_components_detected': total_components,
            'total_vulnerabilities_found': total_vulnerabilities,
            'success_rate': (summary['successful_analyses'] / len(results)) * 100
        }

        return summary

    def generate_comprehensive_report(self, analysis_data: Dict[str, Any], report_format: str = 'markdown') -> str:
        """生成综合安全分析报告"""
        if report_format == 'markdown':
            return self._generate_markdown_report(analysis_data)
        elif report_format == 'json':
            return json.dumps(analysis_data, ensure_ascii=False, indent=2)
        elif report_format == 'html':
            return self._generate_html_report(analysis_data)
        else:
            return str(analysis_data)

    def _generate_markdown_report(self, analysis_data: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        report = f"""# 综合安全分析报告
**分析时间**: {analysis_data.get('analysis_time', 'Unknown')}
**目标URL**: {analysis_data.get('target_url', 'Unknown')}
**分析ID**: {analysis_data.get('analysis_id', 'Unknown')}

---

## 执行摘要

"""

        summary = analysis_data.get('summary', {})

        # 关键发现
        if summary.get('key_findings'):
            report += "### 关键发现\n\n"
            for finding in summary['key_findings']:
                report += f"- {finding}\n"
            report += "\n"

        # 风险评估
        report += f"""### 风险评估

- **风险等级**: {summary.get('risk_level', 'Unknown').upper()}
- **风险分数**: {summary.get('metrics', {}).get('risk_score', 0)}

"""

        # 详细分析结果
        results = analysis_data.get('results', {})

        # 漏洞扫描结果
        if 'vulnerability_scan' in results:
            vuln_scan = results['vulnerability_scan']
            report += f"""## 漏洞扫描结果

- **检测到的组件**: {len(vuln_scan.get('detected_components', []))}
- **匹配的漏洞**: {len(vuln_scan.get('matched_vulnerabilities', []))}
- **风险等级**: {vuln_scan.get('risk_assessment', {}).get('overall_risk', 'unknown')}

"""

            if vuln_scan.get('matched_vulnerabilities'):
                report += "### 发现的漏洞\n\n"
                for vuln in vuln_scan['matched_vulnerabilities'][:5]:
                    report += f"- **{vuln.get('cve_id', 'Unknown')}** ({vuln.get('severity', 'unknown')})\n"
                    report += f"  - 匹配分数: {vuln.get('match_score', 0):.2f}\n"
                report += "\n"

        # CVE分析结果
        if 'cve_analysis' in results:
            cve_analysis = results['cve_analysis']
            report += f"""## CVE相关性分析

- **相关CVE数量**: {len(cve_analysis.get('related_cves', []))}
- **推荐优先级**: {len(cve_analysis.get('recommendation_priorities', []))}

"""

        # 风险评估结果
        if 'risk_assessment' in results:
            risk_assessment = results['risk_assessment']
            report += f"""## 详细风险评估

- **总体风险**: {risk_assessment.get('overall_risk', 'unknown')}
- **风险分数**: {risk_assessment.get('risk_score', 0)}
- **合规状态**: {risk_assessment.get('compliance_status', 'unknown')}

### 风险因素

"""
            for factor in risk_assessment.get('risk_factors', []):
                report += f"- {factor}\n"

            report += "\n### 缓解策略\n\n"
            for strategy in risk_assessment.get('mitigation_strategies', []):
                report += f"- {strategy}\n"

            report += "\n"

        # 行动项目
        if summary.get('action_items'):
            report += "## 建议行动项目\n\n"
            for i, action in enumerate(summary['action_items'], 1):
                report += f"{i}. {action}\n"
            report += "\n"

        report += f"""---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**生成工具**: Dragon-V Triple Bot 综合安全分析平台 v3.2.0
**数据来源**: 统一CVE数据库和应用指纹库
"""

        return report

    def _generate_html_report(self, analysis_data: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>综合安全分析报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .risk-critical {{ color: #dc3545; font-weight: bold; }}
        .risk-high {{ color: #fd7e14; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>综合安全分析报告</h1>
        <p><strong>目标URL:</strong> {target_url}</p>
        <p><strong>分析时间:</strong> {analysis_time}</p>
    </div>

    <div class="section">
        <h2>执行摘要</h2>
        <div class="metric">
            <strong>风险等级:</strong>
            <span class="risk-{risk_level}">{risk_level_upper}</span>
        </div>
        <div class="metric">
            <strong>风险分数:</strong> {risk_score}
        </div>
        <div class="metric">
            <strong>检测组件:</strong> {components_detected}
        </div>
        <div class="metric">
            <strong>发现漏洞:</strong> {vulnerabilities_found}
        </div>
    </div>

    <div class="section">
        <h2>建议行动项目</h2>
        <ul>
        {action_items}
        </ul>
    </div>

    <div class="footer">
        <p><em>报告生成时间: {generation_time}</em></p>
        <p><em>生成工具: Dragon-V Triple Bot 综合安全分析平台 v3.2.0</em></p>
    </div>
</body>
</html>
        """

        # 简化的HTML报告生成
        try:
            summary = analysis_data.get('summary', {})
            metrics = summary.get('metrics', {})

            html_content = html_template.format(
                target_url=analysis_data.get('target_url', 'Unknown'),
                analysis_time=analysis_data.get('analysis_time', 'Unknown'),
                risk_level=summary.get('risk_level', 'low'),
                risk_level_upper=summary.get('risk_level', 'low').upper(),
                risk_score=metrics.get('risk_score', 0),
                components_detected=metrics.get('components_detected', 0),
                vulnerabilities_found=metrics.get('vulnerabilities_found', 0),
                action_items='\n'.join(f'<li>{item}</li>' for item in summary.get('action_items', [])),
                generation_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

            return html_content

        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            return "<html><body><h1>报告生成失败</h1></body></html>"

    def export_analysis_data(self, format: str = 'json') -> str:
        """导出分析数据"""
        if format == 'json':
            return json.dumps(self.analysis_history, ensure_ascii=False, indent=2)
        elif format == 'csv':
            return self._export_to_csv()
        else:
            return str(self.analysis_history)

    def _export_to_csv(self) -> str:
        """导出为CSV格式"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # CSV头部
        writer.writerow([
            'Analysis_ID', 'Target_URL', 'Analysis_Time', 'Risk_Level',
            'Risk_Score', 'Components_Detected', 'Vulnerabilities_Found'
        ])

        # 数据行
        for analysis in self.analysis_history:
            summary = analysis.get('summary', {})
            metrics = summary.get('metrics', {})

            writer.writerow([
                analysis.get('analysis_id', ''),
                analysis.get('target_url', ''),
                analysis.get('analysis_time', ''),
                summary.get('risk_level', ''),
                metrics.get('risk_score', 0),
                metrics.get('components_detected', 0),
                metrics.get('vulnerabilities_found', 0)
            ])

        return output.getvalue()

def main():
    """主函数 - 演示综合安全分析平台"""
    platform = ComprehensiveSecurityAnalysisPlatform()

    print("=" * 80)
    print("Dragon-V Triple Bot 综合安全分析平台")
    print("=" * 80)

    # 显示平台状态
    status = platform.get_platform_status()
    print("\n平台状态:")
    print(f"- 平台名称: {status['platform_info']['name']}")
    print(f"- 版本: {status['platform_info']['version']}")
    print(f"- 状态: {status['platform_info']['status']}")
    print(f"- CVE条目: {status['database_status']['cve_entries']}")
    print(f"- 应用指纹: {status['database_status']['fingerprints']}")

    print("\n核心功能:")
    for capability in status['capabilities']:
        print(f"- {capability}")

    # 演示全面分析
    print("\n正在进行全面安全分析演示...")

    # 使用测试目标
    test_target = "https://httpbin.org"
    analysis_result = platform.comprehensive_target_analysis(test_target)

    print(f"\n分析结果:")
    summary = analysis_result.get('summary', {})
    print(f"- 风险等级: {summary.get('risk_level', 'unknown')}")
    print(f"- 风险分数: {summary.get('metrics', {}).get('risk_score', 0)}")
    print(f"- 检测组件: {summary.get('metrics', {}).get('components_detected', 0)}")
    print(f"- 发现漏洞: {summary.get('metrics', {}).get('vulnerabilities_found', 0)}")

    # 显示关键发现
    if summary.get('key_findings'):
        print(f"\n关键发现:")
        for finding in summary['key_findings'][:3]:
            print(f"- {finding}")

    # 显示建议行动
    if summary.get('action_items'):
        print(f"\n建议行动:")
        for action in summary['action_items'][:3]:
            print(f"- {action}")

    # 生成报告
    report_file = f"comprehensive_security_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_content = platform.generate_comprehensive_report(analysis_result, 'markdown')

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n综合分析报告已生成: {report_file}")

    print("\n综合安全分析平台演示完成！")
    print("功能特性:")
    print("- 统一的CVE数据库查询")
    print("- 智能漏洞匹配")
    print("- 全面风险评估")
    print("- 多格式报告生成")
    print("- 批量分析支持")
    print("- 历史数据管理")

if __name__ == "__main__":
    main()