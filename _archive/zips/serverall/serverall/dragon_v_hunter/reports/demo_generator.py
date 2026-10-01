"""
实战演示生成器
创建Dragon-V Logistics Hunter的实战演示和教学文档
"""

import json
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from datetime import datetime
from pathlib import Path

class DemoType(Enum):
    """演示类型枚举"""
    PENETRATION_TEST = "渗透测试演示"
    BUSINESS_LOGIC_EXPLOIT = "业务逻辑利用演示"
    DATA_EXFILTRATION = "数据外泄演示"
    CHAIN_ATTACK = "链式攻击演示"
    FULL_DEMO = "完整演示"

@dataclass
class DemoScenario:
    """演示场景"""
    scenario_id: str
    name: str
    description: str
    target_url: str
    demo_type: DemoType
    expected_duration: int  # 秒
    difficulty_level: str
    learning_objectives: List[str]
    attack_chains: List[Dict[str, Any]]
    success_criteria: List[str]
    risk_assessment: Dict[str, Any]

@dataclass
class DemoExecution:
    """演示执行记录"""
    execution_id: str
    scenario: DemoScenario
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_steps: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    success: bool = False
    notes: str = ""

class DragonVDemoGenerator:
    """Dragon-V 实战演示生成器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.demo_scenarios = self._create_demo_scenarios()

    def _create_demo_scenarios(self) -> List[DemoScenario]:
        """创建演示场景"""
        scenarios = [
            DemoScenario(
                scenario_id="demo_001",
                name="Viettel Post 渗透测试演示",
                description="针对Viettel Post网站的完整渗透测试演示",
                target_url="https://demo.viettelpost.com.vn",
                demo_type=DemoType.PENETRATION_TEST,
                expected_duration=300,
                difficulty_level="专家级",
                learning_objectives=[
                    "掌握越南化指纹识别技术",
                    "理解业务逻辑攻击链",
                    "学习隐蔽式数据外泄",
                    "了解AI增强攻击优化"
                ],
                attack_chains=[
                    {
                        "chain_type": "tracking_to_database",
                        "name": "订单追踪数据库渗透",
                        "steps": [
                            "时间盲注检测",
                            "真实订单号提取",
                            "API接口滥用",
                            "客户信息解析",
                            "数据库批量导出"
                        ]
                    }
                ],
                success_criteria=[
                    "成功识别目标系统特征",
                    "生成有效的攻击链",
                    "实现数据提取和武器化",
                    "完成隐蔽式外泄"
                ],
                risk_assessment={
                    "risk_level": "高",
                    "required_approvals": ["团队主管", "法律审查"],
                    "safeguards": ["隔离环境", "数据脱敏", "实时监控"]
                }
            ),
            DemoScenario(
                scenario_id="demo_002",
                name="Giao Hang Nhanh 业务逻辑利用",
                description="演示利用业务逻辑漏洞进行订单篡改",
                target_url="https://demo.giaohangnhanh.vn",
                demo_type=DemoType.BUSINESS_LOGIC_EXPLOIT,
                expected_duration=180,
                difficulty_level="高级",
                learning_objectives=[
                    "理解业务逻辑漏洞原理",
                    "掌握订单状态篡改技术",
                    "学习运费欺诈方法",
                    "了解业务影响评估"
                ],
                attack_chains=[
                    {
                        "chain_type": "order_manipulation",
                        "name": "订单篡改攻击",
                        "steps": [
                            "权限检测",
                            "状态篡改",
                            "运费修改",
                            "金额操纵",
                            "批量处理"
                        ]
                    }
                ],
                success_criteria=[
                    "成功绕过访问控制",
                    "修改订单状态",
                    "篡改运费和金额",
                    "完成批量操作"
                ],
                risk_assessment={
                    "risk_level": "极高",
                    "required_approvals": ["高级管理层", "技术负责人"],
                    "safeguards": ["生产环境禁止", "完整备份", "紧急回滚"]
                }
            ),
            DemoScenario(
                scenario_id="demo_003",
                name="VNPost 隐蔽数据外泄演示",
                description="演示多种隐蔽数据外泄技术",
                target_url="https://demo.vnpost.vn",
                demo_type=DemoType.DATA_EXFILTRATION,
                expected_duration=240,
                difficulty_level="专家级",
                learning_objectives=[
                    "掌握DNS隧道技术",
                    "学习HTTP隐蔽通道",
                    "了解邮件外泄方法",
                    "掌握云存储上传技术"
                ],
                attack_chains=[
                    {
                        "chain_type": "customer_data_exfil",
                        "name": "客户数据外泄",
                        "steps": [
                            "客户数据库探测",
                            "PII数据提取",
                            "批量数据导出",
                            "格式转换",
                            "隐蔽式外泄"
                        ]
                    }
                ],
                success_criteria=[
                    "成功访问客户数据",
                    "提取个人信息",
                    "格式化数据",
                    "完成外泄传输"
                ],
                risk_assessment={
                    "risk_level": "高",
                    "required_approvals": ["安全主管", "合规部门"],
                    "safeguards": ["网络隔离", "流量监控", "数据加密"]
                }
            ),
            DemoScenario(
                scenario_id="demo_004",
                name="通用物流系统链式攻击",
                description="演示针对通用越南物流系统的完整攻击链",
                target_url="https://demo.logistics.vn",
                demo_type=DemoType.FULL_DEMO,
                expected_duration=600,
                difficulty_level="大师级",
                learning_objectives=[
                    "掌握完整的攻击链规划",
                    "理解AI优化技术",
                    "学习业务逻辑渗透",
                    "了解防御绕过策略"
                ],
                attack_chains=[
                    {
                        "chain_type": "tracking_to_database",
                        "name": "追踪到数据库",
                        "steps": [
                            "指纹识别",
                            "攻击链生成",
                            "攻击执行",
                            "数据库武器化",
                            "数据外泄"
                        ]
                    },
                    {
                        "chain_type": "password_reset_to_account",
                        "name": "密码重置到账号",
                        "steps": [
                            "逻辑检测",
                            "验证码爆破",
                            "账号接管",
                            "信息爬取",
                            "横向移动"
                        ]
                    }
                ],
                success_criteria=[
                    "完整执行所有阶段",
                    "实现数据提取",
                    "成功外泄敏感数据",
                    "应用AI优化建议"
                ],
                risk_assessment={
                    "risk_level": "极高",
                    "required_approvals": ["公司高管", "法务部门", "安全委员会"],
                    "safeguards": ["专用测试环境", "全程录像", "实时审计"]
                }
            )
        ]
        return scenarios

    async def generate_demo(self, scenario_id: str) -> Dict[str, Any]:
        """生成演示脚本"""
        try:
            # 查找演示场景
            scenario = next((s for s in self.demo_scenarios if s.scenario_id == scenario_id), None)
            if not scenario:
                return {"error": f"演示场景 {scenario_id} 不存在"}

            self.logger.info(f"生成演示脚本: {scenario.name}")

            # 生成演示脚本
            demo_script = {
                "scenario_info": {
                    "name": scenario.name,
                    "description": scenario.description,
                    "target_url": scenario.target_url,
                    "demo_type": scenario.demo_type.value,
                    "difficulty_level": scenario.difficulty_level,
                    "expected_duration": scenario.expected_duration,
                    "learning_objectives": scenario.learning_objectives
                },
                "preparation_requirements": self._generate_preparation_requirements(scenario),
                "execution_steps": self._generate_execution_steps(scenario),
                "expected_results": self._generate_expected_results(scenario),
                "risk_management": self._generate_risk_management_plan(scenario),
                "post_execution": self._generate_post_execution_tasks(scenario),
                "teaching_materials": self._generate_teaching_materials(scenario)
            }

            # 保存演示脚本
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"demo_{scenario_id}_{timestamp}.json"

            with open(f"reports/{filename}", 'w', encoding='utf-8') as f:
                json.dump(demo_script, f, ensure_ascii=False, indent=2)

            self.logger.info(f"演示脚本已保存: {filename}")
            return {
                "success": True,
                "script_file": filename,
                "scenario": scenario.name,
                "duration": scenario.expected_duration
            }

        except Exception as e:
            self.logger.error(f"演示生成失败: {e}")
            return {"error": str(e)}

    def _generate_preparation_requirements(self, scenario: DemoScenario) -> Dict[str, Any]:
        """生成准备要求"""
        return {
            "technical_requirements": {
                "network_access": "需要外网访问目标环境",
                "browser": "Chrome/Firefox 最新版本",
                "tools": ["Dragon-V Hunter", "Burp Suite", "Wireshark"],
                "python": "Python 3.11+ 及相关依赖"
            },
            "environment_setup": [
                "配置API密钥（如使用AI功能）",
                "设置代理服务器（如需要）",
                "准备测试目标环境",
                "确保网络连接稳定"
            ],
            "prerequisites": {
                "required_skills": [
                    "基础渗透测试知识",
                    "SQL注入原理",
                    "Web应用安全",
                    "Python编程"
                ],
                "recommended_experience": "具有3年以上渗透测试经验"
            }
        }

    def _generate_execution_steps(self, scenario: DemoScenario) -> List[Dict[str, Any]]:
        """生成执行步骤"""
        steps = []

        # 基础设置步骤
        steps.append({
            "step_number": 1,
            "title": "环境准备",
            "description": "准备测试环境和工具",
            "actions": [
                "安装Dragon-V Hunter工具",
                "配置目标URL",
                "设置代理和监听",
                "启动日志记录"
            ],
            "expected_duration": 30,
            "key_points": [
                "确保所有依赖包已安装",
                "验证网络连接",
                "检查工具版本"
            ]
        })

        # 攻击执行步骤
        for i, chain in enumerate(scenario.attack_chains, 2):
            steps.extend(self._generate_chain_steps(chain, i))

        return steps

    def _generate_chain_steps(self, chain: Dict[str, Any], start_step: int) -> List[Dict[str, Any]]:
        """生成攻击链步骤"""
        steps = []
        steps_list = chain.get('steps', [])

        for i, step_name in enumerate(steps_list, start_step):
            steps.append({
                "step_number": i,
                "title": step_name,
                "chain_name": chain.get('name', ''),
                "description": f"执行{step_name}步骤",
                "actions": [
                    "配置攻击参数",
                    "执行攻击操作",
                    "记录执行结果",
                    "分析响应数据"
                ],
                "expected_duration": 45,
                "key_points": [
                    "注意安全防护",
                    "记录所有操作",
                    "分析成功指标",
                    "准备回滚方案"
                ],
                "success_indicators": [
                    "成功触发漏洞",
                    "获取预期数据",
                    "绕过安全机制",
                    "建立持久化"
                ]
            })

        return steps

    def _generate_expected_results(self, scenario: DemoScenario) -> Dict[str, Any]:
        """生成预期结果"""
        return {
            "technical_results": {
                "vulnerabilities_discovered": [
                    "SQL注入漏洞",
                    "业务逻辑缺陷",
                    "访问控制绕过",
                    "信息泄露"
                ],
                "data_extracted": {
                    "customer_information": "PII数据",
                    "order_data": "订单详情",
                    "financial_records": "财务信息",
                    "internal_documents": "内部文档"
                },
                "attack_success_rate": "80%以上",
                "exfiltration_success": "成功完成隐蔽外泄"
            },
            "business_impact": {
                "operational_disruption": "业务流程中断",
                "financial_loss": "潜在财务损失",
                "reputation_damage": "品牌声誉影响",
                "compliance_violation": "合规性违规"
            },
            "learning_outcomes": scenario.learning_objectives
        }

    def _generate_risk_management_plan(self, scenario: DemoScenario) -> Dict[str, Any]:
        """生成风险管理计划"""
        return {
            "risk_assessment": {
                "overall_risk_level": scenario.risk_assessment["risk_level"],
                "risk_factors": [
                    "数据泄露风险",
                    "服务中断风险",
                    "法律合规风险",
                    "声誉损害风险"
                ],
                "mitigation_strategies": [
                    "在隔离环境中测试",
                    "使用脱敏数据",
                    "限制操作范围",
                    "全程监控审计"
                ]
            },
            "emergency_procedures": {
                "stop_conditions": [
                    "检测到异常系统行为",
                    "服务响应时间过长",
                    "出现安全事件",
                    "达到预定时间限制"
                ],
                "rollback_procedures": [
                    "恢复系统配置",
                    "清除测试数据",
                    "重置账户状态",
                    "通知相关方"
                ]
            },
            "approval_requirements": {
                "required_signatures": scenario.risk_assessment["required_approvals"],
                "documentation_requirements": [
                    "测试授权书",
                    "风险评估报告",
                    "应急预案文档",
                    "执行计划书"
                ]
            }
        }

    def _generate_post_execution_tasks(self, scenario: DemoScenario) -> Dict[str, Any]:
        """生成执行后任务"""
        return {
            "immediate_tasks": [
                "停止所有活动进程",
                "清理测试环境",
                "保存所有日志和证据",
                "进行系统完整性检查"
            ],
            "reporting_tasks": [
                "生成详细测试报告",
                "制作演示视频",
                "编写技术文档",
                "准备管理层汇报"
            ],
            "remediation_tasks": [
                "提供漏洞修复建议",
                "制定安全加固方案",
                "进行员工安全培训",
                "建立监控机制"
            ]
        }

    def _generate_teaching_materials(self, scenario: DemoScenario) -> Dict[str, Any]:
        """生成教学材料"""
        return {
            "presentation_slides": {
                "structure": [
                    "演示介绍",
                    "技术背景",
                    "攻击原理",
                    "执行过程",
                    "结果分析",
                    "安全建议",
                    "总结讨论"
                ],
                "key_points": [
                    "业务逻辑漏洞的危害性",
                    "隐蔽式攻击的检测难度",
                    "AI增强攻击的效率提升",
                    "防御策略的重要性"
                ]
            },
            "reference_materials": [
                "业务逻辑安全最佳实践",
                "越南物流系统安全规范",
                "AI在安全测试中的应用",
                "渗透测试方法论"
            ],
            "hands_on_exercises": [
                "环境设置练习",
                "指纹识别练习",
                "攻击链生成练习",
                "数据外泄技术练习"
            ]
        }

    async def execute_demo(self, scenario_id: str) -> DemoExecution:
        """执行演示"""
        try:
            scenario = next((s for s in self.demo_scenarios if s.scenario_id == scenario_id), None)
            if not scenario:
                raise ValueError(f"演示场景 {scenario_id} 不存在")

            execution = DemoExecution(
                execution_id=f"exec_{int(time.time())}",
                scenario=scenario,
                start_time=datetime.now()
            )

            self.logger.info(f"开始执行演示: {scenario.name}")

            # 模拟执行过程
            for step in self._generate_execution_steps(scenario):
                step_start = time.time()

                # 模拟执行步骤
                execution_result = await self._simulate_step_execution(step, scenario)

                step_end = time.time()

                execution.execution_steps.append({
                    "step_number": step["step_number"],
                    "title": step["title"],
                    "start_time": step_start,
                    "end_time": step_end,
                    "duration": step_end - step_start,
                    "result": execution_result
                })

            # 评估结果
            execution.end_time = datetime.now()
            execution.success = self._evaluate_demo_success(execution)
            execution.notes = self._generate_demo_notes(execution)

            self.logger.info(f"演示执行完成: {execution.success}")

            return execution

        except Exception as e:
            self.logger.error(f"演示执行失败: {e}")
            raise

    async def _simulate_step_execution(self, step: Dict[str, Any], scenario: DemoScenario) -> Dict[str, Any]:
        """模拟执行步骤"""
        await asyncio.sleep(2)  # 模拟执行时间

        # 模拟成功结果
        if random.random() > 0.2:  # 80%成功率
            return {
                "success": True,
                "data_extracted": {
                    "order_ids": [f"VP{random.randint(1000000, 9999999)}"],
                    "customer_info": {
                        "name": "Nguyễn Văn A",
                        "phone": "0912345678",
                        "email": "test@example.com"
                    },
                    "sensitive_data": "模拟敏感数据"
                },
                "execution_time": random.uniform(5, 15),
                "vulnerabilities_found": ["SQL注入", "权限绕过"],
                "recommendations": "加强输入验证，实施访问控制"
            }
        else:
            return {
                "success": False,
                "error": "步骤执行失败",
                "retry_needed": True,
                "alternative_approach": "调整攻击参数"
            }

    def _evaluate_demo_success(self, execution: DemoExecution) -> bool:
        """评估演示成功度"""
        successful_steps = sum(1 for step in execution.execution_steps if step["result"]["success"])
        total_steps = len(execution.execution_steps)

        return successful_steps >= total_steps * 0.7  # 70%成功率

    def _generate_demo_notes(self, execution: DemoExecution) -> str:
        """生成演示注释"""
        successful_steps = sum(1 for step in execution.execution_steps if step["result"]["success"])
        total_steps = len(execution.execution_steps)

        return f"""
        演示执行总结：
        - 总步骤数：{total_steps}
        - 成功步骤：{successful_steps}
        - 成功率：{successful_steps/total_steps:.1%}
        - 执行时间：{(execution.end_time - execution.start_time).total_seconds():.1f}秒

        关键观察：
        1. 业务逻辑漏洞危害显著
        2. 隐蔽式攻击效果良好
        3. AI优化提高了成功率
        4. 防御机制需要加强
        """

    def generate_detailed_report(self, execution: DemoExecution) -> Dict[str, Any]:
        """生成详细报告"""
        return {
            "execution_summary": {
                "scenario_name": execution.scenario.name,
                "execution_id": execution.execution_id,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "total_duration": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else 0,
                "success": execution.success,
                "notes": execution.notes
            },
            "detailed_steps": [
                {
                    "step_number": step["step_number"],
                    "title": step["title"],
                    "duration": step["duration"],
                    "result": step["result"],
                    "execution_time": step["end_time"] - step["start_time"]
                }
                for step in execution.execution_steps
            ],
            "performance_metrics": {
                "success_rate": sum(1 for step in execution.execution_steps if step["result"]["success"]) / len(execution.execution_steps),
                "average_duration": sum(step["duration"] for step in execution.execution_steps) / len(execution.execution_steps),
                "total_data_extracted": len([step for step in execution.execution_steps if step["result"]["success"] and step["result"].get("data_extracted")])
            },
            "vulnerability_findings": {
                "total_vulnerabilities": len(set([vuln for step in execution.execution_steps for vuln in step["result"].get("vulnerabilities_found", [])])),
                "unique_vulnerabilities": list(set([vuln for step in execution.execution_steps for vuln in step["result"].get("vulnerabilities_found", [])])),
                "severity_distribution": {
                    "high": len([step for step in execution.execution_steps if step["result"]["success"] and "critical" in str(step["result"].get("vulnerabilities_found", []))]),
                    "medium": len([step for step in execution.execution_steps if step["result"]["success"] and "medium" in str(step["result"].get("vulnerabilities_found", []))]),
                    "low": len([step for step in execution.execution_steps if step["result"]["success"] and "low" in str(step["result"].get("vulnerabilities_found", []))])
                }
            },
            "recommendations": [
                "立即修复发现的漏洞",
                "实施业务逻辑安全审查",
                "加强数据访问控制",
                "建立持续监控机制",
                "进行员工安全培训"
            ],
            "learning_outcomes": execution.scenario.learning_objectives
        }

    async def create_complete_demo_package(self, scenario_id: str) -> Dict[str, Any]:
        """创建完整演示包"""
        try:
            # 生成演示脚本
            script_result = await self.generate_demo(scenario_id)
            if not script_result.get("success"):
                return script_result

            # 执行演示
            execution = await self.execute_demo(scenario_id)

            # 生成详细报告
            detailed_report = self.generate_detailed_report(execution)

            # 创建演示包
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            demo_package = {
                "package_id": f"demo_package_{timestamp}",
                "scenario_id": scenario_id,
                "scenario_name": execution.scenario.name,
                "script_info": script_result,
                "execution_summary": {
                    "execution_id": execution.execution_id,
                    "success": execution.success,
                    "duration": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else 0
                },
                "detailed_report": detailed_report,
                "generated_at": datetime.now().isoformat(),
                "files_generated": [
                    f"demo_script_{timestamp}.json",
                    f"execution_log_{timestamp}.txt",
                    f"detailed_report_{timestamp}.html"
                ]
            }

            # 保存演示包
            package_filename = f"demo_package_{timestamp}.json"
            with open(f"reports/{package_filename}", 'w', encoding='utf-8') as f:
                json.dump(demo_package, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "package_file": package_filename,
                "execution_success": execution.success,
                "package_id": demo_package["package_id"]
            }

        except Exception as e:
            self.logger.error(f"演示包创建失败: {e}")
            return {"error": str(e)}