#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南关键漏洞深度分析模块
Vietnam Critical Vulnerabilities Deep Analysis Module for Dragon-V Triple Bot v3.2.0

基于提供的发现数据，对越南主要Web应用的关键漏洞进行深度AI分析
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from GEMINI_AI_INTEGRATION import GeminiAIIntegration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_critical_analysis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VietnamCriticalVulnerabilitiesAnalyzer:
    """越南关键漏洞深度分析器"""

    def __init__(self):
        self.ai_analyzer = GeminiAIIntegration()

        # 发现的关键漏洞数据
        self.discovered_vulnerabilities = {
            "shopee_vn": {
                "url": "https://shopee.vn",
                "name": "Shopee Vietnam",
                "type": "电商平台",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 18},
                    {"component": "admin_panel", "severity": "High", "count": 18},
                    {"component": "admin_panel", "severity": "High", "count": 18}
                ]
            },
            "momo_vn": {
                "url": "https://momo.vn",
                "name": "MoMo Wallet",
                "type": "金融服务",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 1}
                ]
            },
            "tiki_vn": {
                "url": "https://tiki.vn",
                "name": "Tiki",
                "type": "电商平台",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 9},
                    {"component": "admin_panel", "severity": "High", "count": 9},
                    {"component": "admin_panel", "severity": "High", "count": 9}
                ]
            },
            "lazada_vn": {
                "url": "https://lazada.vn",
                "name": "Lazada Vietnam",
                "type": "电商平台",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 41},
                    {"component": "admin_panel", "severity": "High", "count": 41},
                    {"component": "admin_panel", "severity": "High", "count": 41}
                ]
            },
            "viettelpost_vn": {
                "url": "https://viettelpost.vn",
                "name": "Viettel Post",
                "type": "国营物流",
                "vulnerabilities": [
                    {"component": "unauthorized_api", "severity": "Critical", "count": 20},
                    {"component": "unauthorized_api", "severity": "Critical", "count": 20},
                    {"component": "unauthorized_api", "severity": "Critical", "count": 20}
                ]
            },
            "vnpost_vn": {
                "url": "https://vnpost.vn",
                "name": "VNPost",
                "type": "国营邮政",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 2},
                    {"component": "admin_panel", "severity": "High", "count": 2}
                ]
            },
            "giaohangnhanh_vn": {
                "url": "https://giaohangnhanh.vn",
                "name": "Giao Hang Nhanh",
                "type": "快递服务",
                "vulnerabilities": [
                    {"component": "path_traversal", "severity": "Critical", "count": 153},
                    {"component": "path_traversal", "severity": "Critical", "count": 153},
                    {"component": "path_traversal", "severity": "Critical", "count": 153}
                ]
            },
            "vnpay_vn": {
                "url": "https://vnpay.vn",
                "name": "VNPay",
                "type": "支付服务",
                "vulnerabilities": [
                    {"component": "admin_panel", "severity": "High", "count": 3},
                    {"component": "admin_panel", "severity": "High", "count": 3},
                    {"component": "admin_panel", "severity": "High", "count": 3}
                ]
            }
        }

    def analyze_single_target(self, target_key: str, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个目标的漏洞"""
        logger.info(f"开始分析目标: {target_data['name']}")

        # 计算漏洞统计
        total_vulns = len(target_data['vulnerabilities'])
        critical_vulns = len([v for v in target_data['vulnerabilities'] if v['severity'] == 'Critical'])
        high_vulns = len([v for v in target_data['vulnerabilities'] if v['severity'] == 'High'])

        # 按组件分组
        vuln_by_component = {}
        for vuln in target_data['vulnerabilities']:
            component = vuln['component']
            if component not in vuln_by_component:
                vuln_by_component[component] = {
                    'severity': vuln['severity'],
                    'count': 0,
                    'affected_components': []
                }
            vuln_by_component[component]['count'] += 1

        # 生成分析提示词
        analysis_prompt = f"""
作为高级网络安全专家，请对以下越南网站的漏洞发现进行深度分析：

网站信息：
- 网站名称: {target_data['name']}
- 网站URL: {target_data['url']}
- 业务类型: {target_data['type']}
- 总漏洞数: {total_vulns}
- 严重漏洞: {critical_vulns}个
- 高危漏洞: {high_vulns}个

漏洞详情:
{json.dumps(target_data['vulnerabilities'], ensure_ascii=False, indent=2)}

请进行以下分析：
1. 漏洞类型和危害评估
2. 潜在攻击场景和攻击面分析
3. 业务影响和风险评估
4. 可能的数据泄露风险
5. 修复优先级和紧急程度
6. 对越南互联网安全的影响
7. 修复建议和安全最佳实践

请特别关注：
- 管理面板漏洞的通用模式
- 未授权API的访问控制问题
- 路径遍历漏洞的严重性
- 电商和支付系统的特殊风险

请用中文进行详细分析，提供专业的安全建议。
"""

        try:
            # 使用AI进行分析
            ai_result = self.ai_analyzer.analyze_vulnerability({
                "target_info": target_data,
                "vulnerability_stats": {
                    "total": total_vulns,
                    "critical": critical_vulns,
                    "high": high_vulns
                },
                "component_analysis": vuln_by_component
            })

            if 'analysis_result' in ai_result:
                return {
                    "target_info": target_data,
                    "vulnerability_stats": {
                        "total": total_vulns,
                        "critical": critical_vulns,
                        "high": high_vulns,
                        "medium": total_vulns - critical_vulns - high_vulns,
                        "by_component": vuln_by_component
                    },
                    "ai_analysis": ai_result,
                    "analysis_time": datetime.now().isoformat(),
                    "risk_level": self._calculate_risk_level(critical_vulns, high_vulns, target_data['type']),
                    "urgency": self._calculate_urgency(critical_vulns, target_data['type'])
                }
            else:
                return {
                    "target_info": target_data,
                    "vulnerability_stats": {
                        "total": total_vulns,
                        "critical": critical_vulns,
                        "high": high_vulns
                    },
                    "error": "AI分析失败",
                    "analysis_time": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"分析目标 {target_key} 时出错: {e}")
            return {
                "target_info": target_data,
                "vulnerability_stats": {
                    "total": total_vulns,
                    "critical": critical_vulns,
                    "high": high_vulns
                },
                "error": str(e),
                "analysis_time": datetime.now().isoformat()
            }

    def _calculate_risk_level(self, critical_vulns: int, high_vulns: int, target_type: str) -> str:
        """计算风险等级"""
        total = critical_vulns + high_vulns

        if total >= 50:
            return "CRITICAL"
        elif total >= 20:
            return "HIGH"
        elif total >= 10:
            return "MEDIUM"
        elif total >= 5:
            return "LOW"
        else:
            return "MINIMAL"

    def _calculate_urgency(self, critical_vulns: int, target_type: str) -> str:
        """计算紧急程度"""
        if critical_vulns > 0:
            if target_type in ["金融服务", "支付服务"]:
                return "IMMEDIATE"
            elif target_type in ["电商平台", "国营物流"]:
                return "URGENT"
            else:
                return "HIGH"
        else:
            return "MEDIUM"

    def analyze_all_targets(self) -> Dict[str, Any]:
        """分析所有发现的目标"""
        logger.info("开始分析所有越南关键漏洞目标")

        analysis_results = {
            "analysis_time": datetime.now().isoformat(),
            "total_targets": len(self.discovered_vulnerabilities),
            "target_analyses": {},
            "summary_statistics": {},
            "risk_matrix": {},
            "recommendations": []
        }

        high_risk_targets = []
        critical_vulns_total = 0

        # 分析每个目标
        for target_key, target_data in self.discovered_vulnerabilities.items():
            result = self.analyze_single_target(target_key, target_data)
            analysis_results["target_analyses"][target_key] = result

            if result.get("risk_level") in ["CRITICAL", "HIGH"]:
                high_risk_targets.append(target_key)

            if "vulnerability_stats" in result:
                critical_vulns_total += result["vulnerability_stats"]["critical"]

        # 生成统计摘要
        analysis_results["summary_statistics"] = self._generate_summary_statistics(analysis_results["target_analyses"])

        # 生成风险矩阵
        analysis_results["risk_matrix"] = self._generate_risk_matrix(analysis_results["target_analyses"])

        # 生成总体建议
        analysis_results["recommendations"] = self._generate_recommendations(analysis_results["target_analyses"])

        logger.info(f"分析完成，共分析 {len(self.discovered_vulnerabilities)} 个目标")
        return analysis_results

    def _generate_summary_statistics(self, target_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """生成统计摘要"""
        stats = {
            "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "by_type": {},
            "by_component": {},
            "total_vulnerabilities": 0,
            "risk_distribution": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }

        for target_key, analysis in target_analyses.items():
            if "vulnerability_stats" in analysis:
                vuln_stats = analysis["vulnerability_stats"]
                target_info = analysis["target_info"]

                # 按严重程度统计
                if analysis.get("risk_level") == "CRITICAL":
                    stats["by_severity"]["Critical"] += vuln_stats["critical"]
                elif analysis.get("risk_level") == "HIGH":
                    stats["by_severity"]["High"] += vuln_stats["high"]
                elif analysis.get("risk_level") == "MEDIUM":
                    stats["by_severity"]["Medium"] += vuln_stats.get("medium", 0)
                else:
                    stats["by_severity"]["Low"] += vuln_stats.get("low", 0)

                # 按业务类型统计
                target_type = target_info["type"]
                if target_type not in stats["by_type"]:
                    stats["by_type"][target_type] = {"total": 0, "critical": 0, "high": 0}
                stats["by_type"][target_type]["total"] += vuln_stats["total"]
                stats["by_type"][target_type]["critical"] += vuln_stats["critical"]
                stats["by_type"][target_type]["high"] += vuln_stats["high"]

                # 按组件类型统计
                if "vulnerability_stats" in analysis and "by_component" in analysis["vulnerability_stats"]:
                    for component in analysis["vulnerability_stats"]["by_component"]:
                        if component not in stats["by_component"]:
                            stats["by_component"][component] = 0
                        stats["by_component"][component] += analysis["vulnerability_stats"]["by_component"][component]["count"]

                stats["total_vulnerabilities"] += vuln_stats["total"]

        return stats

    def _generate_risk_matrix(self, target_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险矩阵"""
        risk_matrix = {
            "critical_targets": [],
            "high_risk_targets": [],
            "medium_risk_targets": [],
            "low_risk_targets": [],
            "by_urgency": {"IMMEDIATE": [], "URGENT": [], "HIGH": [], "MEDIUM": []}
        }

        for target_key, analysis in target_analyses.items():
            risk_level = analysis.get("risk_level", "UNKNOWN")
            urgency = analysis.get("urgency", "UNKNOWN")
            target_info = analysis["target_info"]

            target_summary = {
                "name": target_info["name"],
                "url": target_info["url"],
                "type": target_info["type"],
                "risk_level": risk_level,
                "urgency": urgency,
                "total_vulns": analysis.get("vulnerability_stats", {}).get("total", 0),
                "critical_vulns": analysis.get("vulnerability_stats", {}).get("critical", 0),
                "ai_analysis_available": "ai_analysis" in analysis
            }

            if risk_level == "CRITICAL":
                risk_matrix["critical_targets"].append(target_summary)
            elif risk_level == "HIGH":
                risk_matrix["high_risk_targets"].append(target_summary)
            elif risk_level == "MEDIUM":
                risk_matrix["medium_risk_targets"].append(target_summary)
            else:
                risk_matrix["low_risk_targets"].append(target_summary)

            if urgency in risk_matrix["by_urgency"]:
                risk_matrix["by_urgency"][urgency].append(target_summary)

        return risk_matrix

    def _generate_recommendations(self, target_analyses: Dict[str, Any]) -> List[str]:
        """生成总体建议"""
        recommendations = []

        # 统计最严重的漏洞
        all_critical_vulns = []
        all_high_vulns = []

        for analysis in target_analyses.values():
            if "vulnerability_stats" in analysis:
                all_critical_vulns.extend(analysis["vulnerability_stats"].get("critical_vulns", []))
                all_high_vulns.extend(analysis["vulnerability_stats"].get("high_vulns", []))

        # 基于统计数据生成建议
        if len(all_critical_vulns) > 50:
            recommendations.append("[紧急] 立即行动：发现大量严重漏洞，建议立即进行全面安全评估和紧急修复")

        if len(all_critical_vulns) > 20:
            recommendations.append("[警告] 高风险警告：严重漏洞数量较多，需要优先处理")

        # 按类型生成建议
        critical_types = []
        for analysis in target_analyses.values():
            if analysis.get("risk_level") in ["CRITICAL", "HIGH"]:
                critical_types.append(analysis["target_info"]["type"])

        if "金融服务" in critical_types:
            recommendations.append("🏦 金融系统安全：支付服务发现关键漏洞，需要立即修复并加强安全监控")

        if "国营物流" in critical_types:
            recommendations.append("📦 基础设施安全：国营物流系统漏洞可能影响公共服务，需要优先处理")

        if "电商平台" in critical_types:
            recommendations.append("🛒 电商安全：电商平台漏洞可能影响大量用户，需要加强安全防护")

        # 具体修复建议
        recommendations.append("🔧 修复建议：")
        recommendations.append("   1. 修复所有管理面板的未授权访问漏洞")
        recommendations.append("   2. 加强API访问控制和身份验证")
        - recommendations.append("   3. 修复路径遍历漏洞，加强文件访问控制")
        recommendations.append("   4. 实施定期的安全扫描和漏洞评估")
        recommendations.append("   5. 建立完善的安全监控和应急响应机制")

        return recommendations

    def generate_comprehensive_report(self, analysis_results: Dict[str, Any]) -> str:
        """生成综合分析报告"""

        # 使用AI生成报告
        report_prompt = f"""
作为越南网络安全专家，请根据以下深度分析结果生成一份专业的越南关键漏洞综合评估报告：

分析概要：
- 分析时间: {analysis_results['analysis_time']}
- 分析目标数: {analysis_results['total_targets']}
- 发现的漏洞总数: {analysis_results['summary_statistics']['total_vulnerabilities']}
- 严重漏洞总数: {analysis_results['summary_statistics']['by_severity']['Critical']}
- 高危漏洞总数: {analysis_results['summary_statistics']['by_severity']['High']}

详细分析结果：
{json.dumps(analysis_results['target_analyses'], ensure_ascii=False, indent=2)}

风险矩阵信息：
{json.dumps(analysis_results['risk_matrix'], ensure_ascii=False, indent=2)}

统计摘要：
{json.dumps(analysis_results['summary_statistics'], ensure_ascii=False, indent=2)}

请生成包含以下内容的报告：
1. 执行摘要
2. 严重性评估
3. 详细分析
4. 风险矩阵
5. 影响评估
6. 修复建议
7. 长期规划
8. 合规建议

报告要求：
- 使用专业的网络安全术语
- 提供具体的数据支持
- 重点关注越南互联网安全
- 给出可操作的建议
- 适合管理层和技术人员阅读
- 格式清晰易读

请用中文生成详细的分析报告。
"""

        try:
            ai_report = self.ai_analyzer.generate_security_report(
                analysis_results['summary_statistics'],
                {"name": "越南关键漏洞综合评估", "type": "多目标分析"}
            )

            if 'ai_report' in ai_report:
                return ai_report['ai_report']
            else:
                return "AI报告生成失败，请检查API配置"

        except Exception as e:
            logger.error(f"生成AI报告时出错: {e}")
            return f"报告生成失败: {str(e)}"

    def save_analysis_results(self, analysis_results: Dict[str, Any], filename: str = None) -> str:
        """保存分析结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vietnam_critical_vulnerabilities_analysis_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"分析结果已保存到: {filename}")
            return filename

        except Exception as e:
            logger.error(f"保存分析结果时出错: {e}")
            return None

def main():
    """主函数 - 执行越南关键漏洞分析"""
    print("=== 越南关键漏洞深度分析 ===")
    print("分析系统: Dragon-V Triple Bot v3.2.0 + Gemini AI 2.0 Flash-Exp")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 创建分析器
    analyzer = VietnamCriticalVulnerabilitiesAnalyzer()

    print("[分析] 发现的关键目标:")
    for key, data in analyzer.discovered_vulnerabilities.items():
        vuln_count = len(data['vulnerabilities'])
        critical_count = len([v for v in data['vulnerabilities'] if v['severity'] == 'Critical'])
        high_count = len([v for v in data['vulnerabilities'] if v['severity'] == 'High'])

        print(f"- {data['name']} ({data['url']})")
        print(f"  类型: {data['type']}")
        print(f"  漏洞: {vuln_count} 个 (严重: {critical_count}, 高危: {high_count})")
        print()

    print("[AI] 开始AI深度分析...")
    analysis_results = analyzer.analyze_all_targets()

    print(f"\n[摘要] 分析摘要:")
    print(f"- 分析目标数: {analysis_results['total_targets']}")
    print(f"- 总漏洞数: {analysis_results['summary_statistics']['total_vulnerabilities']}")
    print(f"- 严重漏洞: {analysis_results['summary_statistics']['by_severity']['Critical']} 个")
    print(f"- 高危漏洞: {analysis_results['summary_statistics']['by_severity']['High']} 个")
    print(f"- 中危漏洞: {analysis_results['summary_statistics']['by_severity']['Medium']} 个")
    print(f"- 低危漏洞: {analysis_results['summary_statistics']['by_severity']['Low']} 个")

    print(f"\n[风险] 风险分布:")
    risk_matrix = analysis_results['risk_matrix']
    print(f"- 极高风险: {len(risk_matrix['critical_targets'])} 个")
    print(f"- 高风险: {len(risk_matrix['high_risk_targets'])} 个")
    print(f"- 中风险: {len(risk_matrix['medium_risk_targets'])} 个")
    print(f"- 低风险: {len(risk_matrix['low_risk_targets'])} 个")

    print(f"\n[紧急] 紧急程度分布:")
    urgency = risk_matrix['by_urgency']
    print(f"- 立即处理: {len(urgency.get('IMMEDIATE', []))} 个")
    print(f"- 紧急处理: {len(urgency.get('URGENT', []))} 个")
    print(f"- 高优先级: {len(urgency.get('HIGH', []))} 个")
    print(f"- 中优先级: {len(urgency.get('MEDIUM', []))} 个")

    print(f"\n[建议] 总体建议:")
    for i, rec in enumerate(analysis_results['recommendations'], 1):
        print(f"{i}. {rec}")

    # 生成综合报告
    print(f"\n📄 生成综合AI分析报告...")
    report = analyzer.generate_comprehensive_report(analysis_results)

    # 保存分析结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = f"vietnam_critical_analysis_{timestamp}.json"
    json_file_path = analyzer.save_analysis_results(analysis_results, json_file)

    # 保存AI报告
    report_file = f"vietnam_critical_analysis_report_{timestamp}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[完成] 分析完成")
    print(f"[报告] 详细报告: {report_file}")
    print(f"[数据] 数据文件: {json_file_path}")
    print(f"[发现] 发现了{analysis_results['summary_statistics']['total_vulnerabilities']}个关键漏洞，需要立即关注！")

if __name__ == "__main__":
    main()