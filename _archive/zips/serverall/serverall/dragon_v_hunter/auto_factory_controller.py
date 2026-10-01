"""
Dragon-V 自动化工厂控制器
整合所有模块实现端到端自动化渗透测试
"""

import asyncio
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import subprocess
import sys

# 导入现有模块
from standalone_vietnam_pipeline import StandaloneVietnamPipeline
from core.vietnamese_fingerprinter import VietnameseFingerprinter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AutoFactoryConfig:
    """自动化工厂配置"""
    target_domains: List[str]
    max_workers: int = 3
    timeout: int = 30
    output_dir: str = "auto_factory_output"
    enable_database: bool = True
    enable_ai_analysis: bool = False
    scan_modes: List[str] = None

    def __post_init__(self):
        if self.scan_modes is None:
            self.scan_modes = ["fingerprint", "recon", "exploit"]

class AutoFactoryController:
    """自动化工厂主控制器"""

    def __init__(self, config: AutoFactoryConfig):
        self.config = config
        self.results = []
        self.session = None

        # 创建输出目录
        os.makedirs(self.config.output_dir, exist_ok=True)

        # 初始化各个模块
        self.pipeline = StandaloneVietnamPipeline()
        self.fingerprinter = VietnameseFingerprinter()
        # 简化版本，暂时禁用数据库功能

    async def run_full_auto_factory(self) -> Dict[str, Any]:
        """运行完整的自动化工厂"""
        logger.info("🚀 启动 Dragon-V 自动化工厂...")
        start_time = datetime.now()

        # 阶段1: 信息收集自动化
        logger.info("📡 阶段1: 自动信息收集")
        recon_results = await self.auto_recon_phase()

        # 阶段2: AI辅助漏洞分析
        logger.info("🧠 阶段2: AI辅助漏洞分析")
        analysis_results = await self.ai_analysis_phase(recon_results)

        # 阶段3: 自动化漏洞利用
        logger.info("⚡ 阶段3: 自动化漏洞利用")
        exploit_results = await self.auto_exploit_phase(analysis_results)

        # 阶段4: 数据入库和报告生成
        logger.info("💾 阶段4: 数据入库和报告生成")
        report_results = await self.data_processing_phase(exploit_results)

        # 生成最终报告
        final_report = await self.generate_final_report(
            recon_results, analysis_results, exploit_results, report_results, start_time
        )

        return final_report

    async def auto_recon_phase(self) -> Dict[str, Any]:
        """自动信息收集阶段"""
        logger.info("🔍 开始自动信息收集...")
        recon_results = {}

        for domain in self.config.target_domains:
            logger.info(f"🎯 收集目标: {domain}")

            target_recon = {
                "domain": domain,
                "subdomains": [],
                "endpoints": [],
                "js_files": [],
                "technologies": [],
                "vulnerabilities_found": []
            }

            # 调用现有的指纹识别器
            try:
                fingerprint_data = await self.fingerprinter.fingerprint_target(domain)
                target_recon.update(fingerprint_data)
            except Exception as e:
                logger.error(f"指纹识别失败 {domain}: {e}")

            # 调用扫描器（如果有配置文件）
            if os.path.exists("config/targets.json"):
                try:
                    cmd = [
                        "python", "batch_scanner.py",
                        "--targets", "config/targets.json",
                        "--workers", str(self.config.max_workers),
                        "--mode", "fingerprint-only",
                        "--verify"
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.config.timeout)
                    if result.returncode == 0:
                        target_recon["scanner_output"] = result.stdout
                except Exception as e:
                    logger.error(f"扫描器执行失败 {domain}: {e}")

            recon_results[domain] = target_recon

        return recon_results

    async def ai_analysis_phase(self, recon_results: Dict[str, Any]) -> Dict[str, Any]:
        """AI辅助漏洞分析阶段"""
        logger.info("🤖 开始AI辅助分析...")
        analysis_results = {}

        for domain, recon_data in recon_results.items():
            logger.info(f"🧠 分析目标: {domain}")

            # 基于发现的端点和技术生成潜在的攻击面
            attack_surface = self.generate_attack_surface(recon_data)

            # 智能分析漏洞类型
            vulnerability_analysis = self.analyze_vulnerabilities(recon_data)

            analysis_results[domain] = {
                "attack_surface": attack_surface,
                "vulnerability_analysis": vulnerability_analysis,
                "prioritized_targets": self.prioritize_targets(attack_surface, vulnerability_analysis)
            }

        return analysis_results

    def generate_attack_surface(self, recon_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成攻击面"""
        attack_surface = []

        # 基于发现的端点生成攻击面
        endpoints = recon_data.get("endpoints", [])
        js_files = recon_data.get("js_files", [])

        # API端点攻击面
        for endpoint in endpoints:
            if any(api in endpoint.lower() for api in ["api", "rest", "graphql"]):
                attack_surface.append({
                    "type": "api",
                    "endpoint": endpoint,
                    "potential_attacks": ["sql_injection", "idor", "auth_bypass"],
                    "priority": "high"
                })

        # JavaScript文件攻击面
        for js_file in js_files:
            if any(secret in js_file.lower() for secret in ["config", "env", "secret", "key"]):
                attack_surface.append({
                    "type": "js_analysis",
                    "file": js_file,
                    "potential_attacks": ["api_keys", "endpoints", "config_leak"],
                    "priority": "medium"
                })

        return attack_surface

    def analyze_vulnerabilities(self, recon_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析潜在漏洞"""
        analysis = {
            "technologies": recon_data.get("technologies", []),
            "risk_level": "low",
            "potential_vulnerabilities": []
        }

        # 基于技术栈评估风险
        if any(tech.lower() in ["wordpress", "drupal", "joomla"] for tech in analysis["technologies"]):
            analysis["risk_level"] = "medium"
            analysis["potential_vulnerabilities"].append("cms_vulnerabilities")

        if any("old" in tech.lower() or "legacy" in tech.lower() for tech in analysis["technologies"]):
            analysis["risk_level"] = "high"
            analysis["potential_vulnerabilities"].append("outdated_software")

        return analysis

    def prioritize_targets(self, attack_surface: List[Dict], vulnerability_analysis: Dict) -> List[Dict]:
        """优先级排序攻击目标"""
        prioritized = []

        for target in attack_surface:
            priority_score = 0

            # 基于类型打分
            if target["type"] == "api":
                priority_score += 10
            elif target["type"] == "js_analysis":
                priority_score += 5

            # 基于潜在攻击打分
            if "sql_injection" in target["potential_attacks"]:
                priority_score += 15
            if "auth_bypass" in target["potential_attacks"]:
                priority_score += 12

            # 基于风险等级打分
            if vulnerability_analysis["risk_level"] == "high":
                priority_score += 8
            elif vulnerability_analysis["risk_level"] == "medium":
                priority_score += 4

            target["priority_score"] = priority_score
            prioritized.append(target)

        return sorted(prioritized, key=lambda x: x["priority_score"], reverse=True)

    async def auto_exploit_phase(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """自动化漏洞利用阶段"""
        logger.info("⚡ 开始自动化漏洞利用...")
        exploit_results = {}

        for domain, analysis in analysis_results.items():
            logger.info(f"🎯 利用目标: {domain}")

            # 获取高优先级目标
            high_priority_targets = [
                target for target in analysis["prioritized_targets"]
                if target["priority_score"] >= 10
            ]

            domain_results = {
                "domain": domain,
                "targets_tested": [],
                "successful_exploits": [],
                "failed_exploits": []
            }

            # 使用现有的Vietnam Pipeline进行利用测试
            try:
                async with self.pipeline as pipeline:
                    # 测试越南目标的通用漏洞
                    pipeline_results = await pipeline.run_full_pipeline()

                    for result in pipeline_results:
                        if result.success:
                            domain_results["successful_exploits"].append(result)
                        else:
                            domain_results["failed_exploits"].append(result)

                domain_results["targets_tested"] = len(pipeline_results)

            except Exception as e:
                logger.error(f"漏洞利用失败 {domain}: {e}")
                domain_results["error"] = str(e)

            exploit_results[domain] = domain_results

        return exploit_results

    async def data_processing_phase(self, exploit_results: Dict[str, Any]) -> Dict[str, Any]:
        """数据入库和处理阶段（简化版本）"""
        logger.info("💾 开始数据处理...")
        processing_results = {}

        if not self.config.enable_database:
            logger.warning("⚠️ 数据库功能已禁用，跳过数据入库")
            return {"skipped": True, "reason": "Database disabled"}

        # 简化版本：直接保存到JSON文件
        for domain, exploit_data in exploit_results.items():
            logger.info(f"💾 处理目标数据: {domain}")

            try:
                successful_exploits = exploit_data.get("successful_exploits", [])
                processing_results[domain] = {
                    "status": "success",
                    "records_stored": len(successful_exploits),
                    "data_saved": True
                }

                # 保存成功利用的数据
                if successful_exploits:
                    filename = f"exploited_data_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    filepath = os.path.join(self.config.output_dir, filename)

                    data_to_save = {
                        "domain": domain,
                        "exploits": [
                            {
                                "type": exploit.vulnerability_type,
                                "data_extracted": exploit.data_extracted,
                                "financial_impact": exploit.financial_impact,
                                "raw_content": exploit.raw_content[:1000]  # 只保存前1000字符
                            }
                            for exploit in successful_exploits
                        ],
                        "timestamp": datetime.now().isoformat()
                    }

                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data_to_save, f, ensure_ascii=False, indent=2, default=str)

                    logger.info(f"✅ 数据已保存: {filepath}")

            except Exception as e:
                logger.error(f"数据处理失败 {domain}: {e}")
                processing_results[domain] = {"status": "failed", "error": str(e)}

        return processing_results

    async def generate_final_report(self, recon_results, analysis_results, exploit_results, processing_results, start_time) -> Dict[str, Any]:
        """生成最终自动化工厂报告"""
        logger.info("📊 生成最终自动化工厂报告...")

        end_time = datetime.now()
        duration = end_time - start_time

        # 统计数据
        total_domains = len(self.config.target_domains)
        successful_domains = len([r for r in exploit_results.values() if r.get("successful_exploits")])
        total_exploits = sum(len(r.get("successful_exploits", [])) for r in exploit_results.values())
        total_failed = sum(len(r.get("failed_exploits", [])) for r in exploit_results.values())

        report = {
            "factory_info": {
                "name": "Dragon-V 自动化工厂",
                "version": "1.0",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "target_domains": self.config.target_domains,
                "configuration": {
                    "max_workers": self.config.max_workers,
                    "timeout": self.config.timeout,
                    "enable_database": self.config.enable_database,
                    "scan_modes": self.config.scan_modes
                }
            },
            "statistics": {
                "total_domains": total_domains,
                "successful_domains": successful_domains,
                "total_exploits": total_exploits,
                "total_failed": total_failed,
                "success_rate": (successful_domains / total_domains * 100) if total_domains > 0 else 0
            },
            "recon_results": recon_results,
            "analysis_results": analysis_results,
            "exploit_results": exploit_results,
            "processing_results": processing_results,
            "recommendations": self.generate_recommendations(exploit_results)
        }

        # 保存报告
        report_filename = f"auto_factory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(self.config.output_dir, report_filename)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"📄 自动化工厂报告已保存: {report_path}")

        # 生成简化报告
        await self.generate_simple_report(report, report_path.replace('.json', '_summary.txt'))

        return report

    def generate_recommendations(self, exploit_results: Dict[str, Any]) -> List[str]:
        """生成安全建议"""
        recommendations = []

        successful_exploits = sum(len(r.get("successful_exploits", [])) for r in exploit_results.values())

        if successful_exploits > 0:
            recommendations.append("🚨 Critical: 发现多个可利用漏洞，建议立即修复")
            recommendations.append("🔒 High: 实施输入验证和参数化查询")
            recommendations.append("🛡️ High: 部署Web应用防火墙")
        else:
            recommendations.append("✅ Low: 未发现明显漏洞，建议保持定期安全评估")
            recommendations.append("📊 Medium: 建议定期进行安全扫描")

        recommendations.append("🔧 Technical: 建议实施自动化安全监控")
        recommendations.append("📚 Training: 对开发团队进行安全意识培训")

        return recommendations

    async def generate_simple_report(self, report: Dict[str, Any], output_path: str):
        """生成简化文本报告"""
        simple_report = []
        simple_report.append("=" * 60)
        simple_report.append("🏭 Dragon-V 自动化工厂报告")
        simple_report.append("=" * 60)
        simple_report.append("")

        # 工厂信息
        factory_info = report["factory_info"]
        simple_report.append("【工厂信息】")
        simple_report.append(f"运行时间: {factory_info['start_time']} 至 {factory_info['end_time']}")
        simple_report.append(f"持续时间: {factory_info['duration_seconds']:.1f} 秒")
        simple_report.append(f"目标数量: {report['statistics']['total_domains']}")
        simple_report.append("")

        # 统计信息
        stats = report["statistics"]
        simple_report.append("【测试统计】")
        simple_report.append(f"成功域名: {stats['successful_domains']}")
        simple_report.append(f"总漏洞利用: {stats['total_exploits']}")
        simple_report.append(f"失败利用: {stats['total_failed']}")
        simple_report.append(f"成功率: {stats['success_rate']:.1f}%")
        simple_report.append("")

        # 成功案例
        simple_report.append("【成功利用案例】")
        for domain, exploit_data in report["exploit_results"].items():
            successful = exploit_data.get("successful_exploits", [])
            if successful:
                simple_report.append(f"🎯 {domain}:")
                for exploit in successful[:3]:  # 只显示前3个
                    simple_report.append(f"   - {exploit.vulnerability_type}: {len(exploit.data_extracted)} 条数据")
        simple_report.append("")

        # 建议
        simple_report.append("【安全建议】")
        for rec in report["recommendations"]:
            simple_report.append(rec)

        simple_report.append("")
        simple_report.append(f"详细报告: {output_path.replace('_summary.txt', '.json')}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(simple_report))

        logger.info(f"📄 简化报告已保存: {output_path}")

async def main():
    """主函数"""
    # 示例配置
    config = AutoFactoryConfig(
        target_domains=["viettelpost.com.vn", "vnpost.vn"],
        max_workers=3,
        timeout=30,
        enable_database=False,  # 先禁用数据库避免连接问题
        enable_ai_analysis=False  # 先禁用AI功能避免依赖
    )

    controller = AutoFactoryController(config)

    try:
        result = await controller.run_full_auto_factory()

        print("\n" + "=" * 60)
        print("🏭 Dragon-V 自动化工厂运行完成!")
        print("=" * 60)
        print(f"测试域名: {len(config.target_domains)} 个")
        print(f"成功率: {result['statistics']['success_rate']:.1f}%")
        print(f"总漏洞利用: {result['statistics']['total_exploits']}")
        print(f"输出目录: {config.output_dir}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"自动化工厂运行失败: {e}")
        print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())