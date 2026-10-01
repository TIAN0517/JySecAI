#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI辅助决策系统 - 自动化漏洞分析
基于历史数据和机器学习模型自动分析漏洞模式并提供决策支持
"""

import json
import pickle
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import logging
import re
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import random
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HistoricalDataPoint:
    """历史数据点"""
    target_name: str
    target_url: str
    country: str
    sector: str
    vulnerability_type: str
    success_probability: float
    actual_success: bool
    execution_time: float
    method_used: str
    impact_score: int
    timestamp: datetime
    environment: str  # production, staging, test
    mitigation_level: str  # low, medium, high

@dataclass
class DecisionResult:
    """决策结果"""
    target_name: str
    recommended_action: str  # immediate, scheduled, monitoring, skip
    priority_score: float
    confidence_level: float
    reasoning: List[str]
    expected_success_rate: float
    estimated_impact: str
    recommended_methods: List[str]
    estimated_risk: str
    next_steps: List[str]

class AIAssistedDecisionSystem:
    """AI辅助决策系统"""

    def __init__(self):
        self.historical_data = []
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.trained = False

        # 读取之前生成的历史数据
        self.load_historical_data()

        # 风险权重配置
        self.risk_weights = {
            "Banking": {"SQL Injection": 0.9, "Authentication Bypass": 0.8, "API Security": 0.7},
            "Government": {"Authentication Bypass": 0.9, "Privilege Escalation": 0.8, "Data Breach": 0.95},
            "Logistics": {"SQL Injection": 0.6, "Business Logic": 0.7, "API Testing": 0.5},
            "Finance": {"API Security": 0.8, "Data Extraction": 0.7, "Payment Bypass": 0.9},
            "E-commerce": {"XSS": 0.5, "CSRF": 0.4, "Session Hijacking": 0.6}
        }

        # 国家优先级配置
        self.country_priority = {
            "Vietnam": 1.2,
            "Thailand": 1.1,
            "Hong Kong": 1.0,
            "USA": 0.9,
            "International": 0.8
        }

        # 行业价值配置
        self.sector_values = {
            "Banking": 100,
            "Government": 95,
            "Finance": 85,
            "Logistics": 70,
            "E-commerce": 60,
            "Education": 40,
            "Media": 35,
            "Energy": 45,
            "Construction": 30,
            "Fishery": 25,
            "Taxation": 50,
            "Monitoring": 20
        }

        # 成功率因素
        self.success_factors = {
            "SQL Injection": {"基础": 0.6, "高权限": 0.8, "目标环境": 0.7},
            "Authentication Bypass": {"简单": 0.8, "复杂": 0.5, "保护弱": 0.9},
            "API Security": {"REST": 0.7, "GraphQL": 0.8, "SOAP": 0.6},
            "Business Logic": {"标准": 0.6, "自定义": 0.4, "开源": 0.7}
        }

    def load_historical_data(self):
        """加载历史数据"""
        try:
            # 从现有文件中提取历史数据
            if os.path.exists("comprehensive_verification_report_*.txt"):
                # 读取之前的报告数据
                report_files = [f for f in os.listdir() if f.startswith("comprehensive_verification_report_")]
                if report_files:
                    self.generate_synthetic_historical_data()
        except Exception as e:
            logger.warning(f"加载历史数据失败: {e}")
            self.generate_synthetic_historical_data()

    def generate_synthetic_historical_data(self):
        """生成合成历史数据用于演示"""
        # 基于之前测试结果生成历史数据
        historical_data = [
            HistoricalDataPoint(
                target_name="TBAC",
                target_url="https://tbac.or.th",
                country="Thailand",
                sector="Banking",
                vulnerability_type="SQL Injection",
                success_probability=0.75,
                actual_success=True,
                execution_time=45.2,
                method_used="union_based",
                impact_score=85,
                timestamp=datetime.now() - timedelta(days=1),
                environment="production",
                mitigation_level="low"
            ),
            HistoricalDataPoint(
                target_name="CMCoop",
                target_url="https://cmcoop.or.th",
                country="Thailand",
                sector="Finance",
                vulnerability_type="Business Logic",
                success_probability=0.70,
                actual_success=True,
                execution_time=32.8,
                method_used="business_logic",
                impact_score=75,
                timestamp=datetime.now() - timedelta(days=2),
                environment="production",
                mitigation_level="medium"
            ),
            HistoricalDataPoint(
                target_name="MunSaving",
                target_url="https://munsaving.com",
                country="Thailand",
                sector="Banking",
                vulnerability_type="Authentication Bypass",
                success_probability=0.80,
                actual_success=True,
                execution_time=28.5,
                method_used="auth_bypass",
                impact_score=90,
                timestamp=datetime.now() - timedelta(days=3),
                environment="production",
                mitigation_level="low"
            ),
            HistoricalDataPoint(
                target_name="ThaiVivat",
                target_url="https://thaivivat.co.th",
                country="Thailand",
                sector="Banking",
                vulnerability_type="API Security",
                success_probability=0.65,
                actual_success=False,
                execution_time=55.3,
                method_used="api_testing",
                impact_score=70,
                timestamp=datetime.now() - timedelta(days=4),
                environment="production",
                mitigation_level="medium"
            ),
            HistoricalDataPoint(
                target_name="VNPost",
                target_url="https://vnpost.vn",
                country="Vietnam",
                sector="Logistics",
                vulnerability_type="SQL Injection",
                success_probability=0.60,
                actual_success=True,
                execution_time=48.7,
                method_used="union_based",
                impact_score=65,
                timestamp=datetime.now() - timedelta(days=5),
                environment="production",
                mitigation_level="high"
            ),
            HistoricalDataPoint(
                target_name="NetPost Vietnam",
                target_url="https://netpost.vn",
                country="Vietnam",
                sector="Logistics",
                vulnerability_type="Data Extraction",
                success_probability=0.67,
                actual_success=True,
                execution_time=42.1,
                method_used="sql_injection",
                impact_score=60,
                timestamp=datetime.now() - timedelta(days=6),
                environment="production",
                mitigation_level="medium"
            ),
            HistoricalDataPoint(
                target_name="Viettel Post Portal",
                target_url="https://viettelpost.com.vn",
                country="Vietnam",
                sector="Logistics",
                vulnerability_type="Order Manipulation",
                success_probability=0.55,
                actual_success=True,
                execution_time=38.9,
                method_used="sql_injection",
                impact_score=70,
                timestamp=datetime.now() - timedelta(days=7),
                environment="production",
                mitigation_level="medium"
            )
        ]

        self.historical_data = historical_data
        self.train_model()

    def train_model(self):
        """训练机器学习模型"""
        if len(self.historical_data) < 10:
            logger.warning("历史数据不足，使用默认决策逻辑")
            return

        try:
            # 准备训练数据
            X = []
            y = []

            for data in self.historical_data:
                features = self.extract_features(data)
                target = 1 if data.actual_success else 0

                X.append(features)
                y.append(target)

            X = np.array(X)
            y = np.array(y)

            # 训练模型
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            self.trained = True

            logger.info(f"模型训练完成，准确率: {self.model.score(X_scaled, y):.2f}")

        except Exception as e:
            logger.error(f"模型训练失败: {e}")
            self.trained = False

    def extract_features(self, data: HistoricalDataPoint) -> List[float]:
        """提取特征"""
        features = [
            data.success_probability,
            data.impact_score,
            self.sector_values[data.sector],
            self.country_priority.get(data.country, 1.0),
            1.0 if data.environment == "production" else 0.5,
            1.0 if data.mitigation_level == "low" else 0.5,
            data.execution_time / 100.0,  # 归一化执行时间
            len(data.vulnerability_type) / 20.0  # 漏洞复杂度
        ]
        return features

    def predict_success_probability(self, target_data: Dict[str, Any]) -> float:
        """预测成功率"""
        if not self.trained:
            # 使用基于规则的概率计算
            return self.calculate_rule_based_probability(target_data)

        try:
            # 创建模拟数据点
            data_point = HistoricalDataPoint(
                target_name=target_data["name"],
                target_url=target_data["url"],
                country=target_data["country"],
                sector=target_data["sector"],
                vulnerability_type=target_data.get("vulnerability_type", "Unknown"),
                success_probability=0.5,
                actual_success=False,
                execution_time=30.0,
                method_used="unknown",
                impact_score=50,
                timestamp=datetime.now(),
                environment=target_data.get("environment", "production"),
                mitigation_level=target_data.get("mitigation_level", "medium")
            )

            features = self.extract_features(data_point)
            features_scaled = self.scaler.transform([features])
            probability = self.model.predict_proba(features_scaled)[0][1]

            return probability

        except Exception as e:
            logger.error(f"预测失败: {e}")
            return self.calculate_rule_based_probability(target_data)

    def calculate_rule_based_probability(self, target_data: Dict[str, Any]) -> float:
        """基于规则计算成功率"""
        base_prob = 0.3

        # 基于行业调整
        sector = target_data["sector"]
        if sector in ["Banking", "Government"]:
            base_prob += 0.4
        elif sector in ["Finance", "Logistics"]:
            base_prob += 0.3
        else:
            base_prob += 0.2

        # 基于国家调整
        country = target_data["country"]
        if country == "Vietnam":
            base_prob += 0.2
        elif country == "Thailand":
            base_prob += 0.15
        elif country == "Hong Kong":
            base_prob += 0.1

        # 基于漏洞类型调整
        vuln_type = target_data.get("vulnerability_type", "Unknown")
        if vuln_type in ["SQL Injection", "Authentication Bypass"]:
            base_prob += 0.2
        elif vuln_type in ["API Security", "Business Logic"]:
            base_prob += 0.15

        # 基于历史成功率调整
        historical_success_rate = self.calculate_historical_success_rate(
            target_data["sector"], vuln_type
        )
        base_prob = (base_prob + historical_success_rate) / 2

        return min(base_prob, 1.0)

    def calculate_historical_success_rate(self, sector: str, vuln_type: str) -> float:
        """计算历史成功率"""
        relevant_data = [
            data for data in self.historical_data
            if data.sector == sector and data.vulnerability_type == vuln_type
        ]

        if not relevant_data:
            return 0.5

        success_count = sum(1 for data in relevant_data if data.actual_success)
        return success_count / len(relevant_data)

    def generate_ai_decision(self, target_data: Dict[str, Any]) -> DecisionResult:
        """生成AI决策"""
        # 预测成功率
        success_probability = self.predict_success_probability(target_data)

        # 计算优先级分数
        priority_score = self.calculate_priority_score(target_data, success_probability)

        # 确定推荐行动
        recommended_action = self.determine_action(target_data, priority_score, success_probability)

        # 计算置信度
        confidence_level = self.calculate_confidence(target_data, success_probability)

        # 生成推理过程
        reasoning = self.generate_reasoning(target_data, success_probability, priority_score)

        # 估计影响
        estimated_impact = self.estimate_impact(target_data, success_probability)

        # 推荐方法
        recommended_methods = self.recommend_methods(target_data)

        # 估计风险
        estimated_risk = self.estimate_risk(target_data, success_probability)

        # 下一步建议
        next_steps = self.generate_next_steps(target_data, recommended_action)

        return DecisionResult(
            target_name=target_data["name"],
            recommended_action=recommended_action,
            priority_score=priority_score,
            confidence_level=confidence_level,
            reasoning=reasoning,
            expected_success_rate=success_probability,
            estimated_impact=estimated_impact,
            recommended_methods=recommended_methods,
            estimated_risk=estimated_risk,
            next_steps=next_steps
        )

    def calculate_priority_score(self, target_data: Dict[str, Any], success_probability: float) -> float:
        """计算优先级分数"""
        # 基础分数
        base_score = success_probability * 100

        # 行业价值权重
        sector_value = self.sector_values.get(target_data["sector"], 50)

        # 国家优先级
        country_priority = self.country_priority.get(target_data["country"], 1.0)

        # 漏洞类型权重
        vuln_type = target_data.get("vulnerability_type", "Unknown")
        vuln_weight = self.risk_weights.get(target_data["sector"], {}).get(vuln_type, 1.0)

        # 综合计算
        priority_score = base_score * sector_value / 100.0 * country_priority * vuln_weight

        return min(priority_score, 100.0)

    def determine_action(self, target_data: Dict[str, Any], priority_score: float, success_probability: float) -> str:
        """确定推荐行动"""
        if priority_score >= 80 and success_probability >= 0.7:
            return "immediate"  # 立即执行
        elif priority_score >= 60 and success_probability >= 0.5:
            return "scheduled"  # 计划执行
        elif priority_score >= 40 and success_probability >= 0.3:
            return "monitoring"  # 监控观察
        else:
            return "skip"  # 跳过

    def calculate_confidence(self, target_data: Dict[str, Any], success_probability: float) -> float:
        """计算置信度"""
        # 基于数据量和历史记录
        relevant_data = [
            data for data in self.historical_data
            if data.sector == target_data["sector"]
        ]

        data_confidence = min(len(relevant_data) / 10.0, 1.0)  # 最多10个数据点

        # 基于预测一致性
        prediction_confidence = success_probability

        # 综合置信度
        confidence = (data_confidence + prediction_confidence) / 2.0

        return min(confidence, 1.0)

    def generate_reasoning(self, target_data: Dict[str, Any], success_probability: float, priority_score: float) -> List[str]:
        """生成推理过程"""
        reasoning = []

        # 行业分析
        sector = target_data["sector"]
        reasoning.append(f"目标属于{sector}行业，该行业通常具有较高价值")

        # 国家分析
        country = target_data["country"]
        reasoning.append(f"位于{country}，属于优先级目标地区")

        # 成功率分析
        if success_probability >= 0.7:
            reasoning.append(f"预期成功率较高（{success_probability:.1%}）")
        elif success_probability >= 0.5:
            reasoning.append(f"预期成功率中等（{success_probability:.1%}）")
        else:
            reasoning.append(f"预期成功率较低（{success_probability:.1%}）")

        # 风险分析
        vuln_type = target_data.get("vulnerability_type", "Unknown")
        reasoning.append(f"发现{vuln_type}漏洞类型，具有较高利用价值")

        # 历史模式分析
        if self.trained:
            reasoning.append("基于机器学习模型分析，历史数据支持此决策")

        return reasoning

    def estimate_impact(self, target_data: Dict[str, Any], success_probability: float) -> str:
        """估计影响"""
        sector = target_data["sector"]
        vuln_type = target_data.get("vulnerability_type", "Unknown")

        # 基于行业和漏洞类型估算影响
        impact_map = {
            "Banking": {
                "SQL Injection": "财务损失 50-100亿泰铢",
                "Authentication Bypass": "系统控制权损失",
                "API Security": "数据泄露风险"
            },
            "Government": {
                "Authentication Bypass": "国家安全风险",
                "Privilege Escalation": "政策数据篡改",
                "Data Breach": "公民信息泄露"
            },
            "Logistics": {
                "SQL Injection": "物流数据泄露",
                "Order Manipulation": "商业欺诈风险",
                "API Testing": "系统服务中断"
            },
            "Finance": {
                "API Security": "金融交易风险",
                "Data Extraction": "客户信息泄露",
                "Payment Bypass": "经济损失"
            }
        }

        impact = impact_map.get(sector, {}).get(vuln_type, "中等影响")

        if success_probability >= 0.7:
            impact += "（高概率实现）"
        elif success_probability < 0.3:
            impact += "（低概率实现）"

        return impact

    def recommend_methods(self, target_data: Dict[str, Any]) -> List[str]:
        """推荐利用方法"""
        sector = target_data["sector"]
        vuln_type = target_data.get("vulnerability_type", "Unknown")

        method_map = {
            "SQL Injection": [
                "UNION查询注入",
                "时间盲注",
                "错误信息注入",
                "布尔盲注"
            ],
            "Authentication Bypass": [
                "SQL注入绕过",
                "会话劫持",
                "权限提升",
                "默认凭证利用"
            ],
            "API Security": [
                "参数注入攻击",
                "认证绕过",
                "速率限制突破",
                "端点发现"
            ],
            "Business Logic": [
                "业务规则绕过",
                "支付流程篡改",
                "订单状态修改",
                "权限提升"
            ]
        }

        methods = method_map.get(vuln_type, ["通用测试方法"])

        # 基于历史成功率调整
        historical_methods = self.get_successful_methods(sector, vuln_type)
        if historical_methods:
            methods = historical_methods + methods[:2]  # 优先推荐历史成功方法

        return methods[:3]  # 返回前3个推荐方法

    def get_successful_methods(self, sector: str, vuln_type: str) -> List[str]:
        """获取历史成功的方法"""
        successful_data = [
            data for data in self.historical_data
            if data.sector == sector and data.vulnerability_type == vuln_type and data.actual_success
        ]

        if not successful_data:
            return []

        method_counter = Counter([data.method_used for data in successful_data])
        most_common = method_counter.most_common(2)

        return [method for method, count in most_common]

    def estimate_risk(self, target_data: Dict[str, Any], success_probability: float) -> str:
        """估计风险"""
        sector = target_data["sector"]
        country = target_data["country"]

        # 基础风险评估
        if sector in ["Banking", "Government"]:
            base_risk = "极高"
        elif sector in ["Finance"]:
            base_risk = "高"
        else:
            base_risk = "中等"

        # 基于成功率调整
        if success_probability >= 0.7:
            risk_modifier = "（成功概率高，风险加剧）"
        elif success_probability < 0.3:
            risk_modifier = "（成功概率低，风险相对可控）"
        else:
            risk_modifier = "（成功概率中等）"

        return base_risk + risk_modifier

    def generate_next_steps(self, target_data: Dict[str, Any], recommended_action: str) -> List[str]:
        """生成下一步建议"""
        next_steps = []

        if recommended_action == "immediate":
            next_steps = [
                "立即进行授权验证",
                "准备测试环境",
                "执行深度漏洞利用",
                "收集证据并评估影响",
                "制定缓解方案"
            ]
        elif recommended_action == "scheduled":
            next_steps = [
                "安排授权时间窗口",
                "准备测试工具和环境",
                "进行初步风险评估",
                "安排专人监控",
                "准备应急方案"
            ]
        elif recommended_action == "monitoring":
            next_steps = [
                "持续监控目标活动",
                "收集更多情报信息",
                "等待更好的测试时机",
                "准备详细测试计划",
                "评估授权可能性"
            ]
        else:
            next_steps = [
                "记录目标信息以备后续参考",
                "继续收集相关情报",
                "寻找其他高优先级目标",
                "更新威胁情报数据库"
            ]

        return next_steps

    def batch_analyze_targets(self, targets: List[Dict[str, Any]]) -> List[DecisionResult]:
        """批量分析目标"""
        results = []

        logger.info(f"开始批量分析 {len(targets)} 个目标...")

        for i, target in enumerate(targets, 1):
            logger.info(f"分析目标 {i}/{len(targets)}: {target['name']}")

            try:
                decision = self.generate_ai_decision(target)
                results.append(decision)

                # 保存结果
                with open(f"ai_decision_{target['name'].replace(' ', '_')}.json", 'w', encoding='utf-8') as f:
                    json.dump(asdict(decision), f, ensure_ascii=False, indent=2, default=str)

            except Exception as e:
                logger.error(f"分析目标 {target['name']} 失败: {e}")

        # 生成综合报告
        self.generate_batch_report(results)

        return results

    def generate_batch_report(self, results: List[DecisionResult]):
        """生成批量分析报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ai_decision_report_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80)
            f.write("\nAI辅助决策系统分析报告")
            f.write("\n" + "=" * 80)
            f.write(f"\n分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            f.write(f"\n分析目标数量: {len(results)}")
            f.write("\n")

            # 统计信息
            immediate_count = len([r for r in results if r.recommended_action == "immediate"])
            scheduled_count = len([r for r in results if r.recommended_action == "scheduled"])
            monitoring_count = len([r for r in results if r.recommended_action == "monitoring"])
            skip_count = len([r for r in results if r.recommended_action == "skip"])

            f.write("\n【决策分布统计】")
            f.write(f"\n立即执行: {immediate_count} 个")
            f.write(f"\n计划执行: {scheduled_count} 个")
            f.write(f"\n监控观察: {monitoring_count} 个")
            f.write(f"\n跳过目标: {skip_count} 个")
            f.write("\n")

            # 按优先级排序
            sorted_results = sorted(results, key=lambda x: x.priority_score, reverse=True)

            f.write("\n【高优先级目标详细分析】")
            f.write("\n" + "-" * 60)

            for result in sorted_results[:10]:
                f.write(f"\n\n目标: {result.target_name}")
                f.write(f"\n推荐行动: {result.recommended_action}")
                f.write(f"\n优先级分数: {result.priority_score:.1f}")
                f.write(f"\n预期成功率: {result.expected_success_rate:.1%}")
                f.write(f"\n置信度: {result.confidence_level:.1%}")
                f.write(f"\n估计影响: {result.estimated_impact}")
                f.write(f"\n估计风险: {result.estimated_risk}")

                f.write(f"\n推理过程:")
                for reason in result.reasoning:
                    f.write(f"\n  - {reason}")

                f.write(f"\n推荐方法:")
                for method in result.recommended_methods:
                    f.write(f"\n  - {method}")

                f.write(f"\n下一步建议:")
                for step in result.next_steps[:3]:
                    f.write(f"\n  - {step}")

            # 建议总结
            f.write("\n\n【建议总结】")
            f.write("\n1. 优先处理'立即执行'类目标，具有高成功率和影响")
            f.write("\n2. '计划执行'类目标需要提前准备和授权")
            f.write("\n3. '监控观察'类目标需要持续收集情报")
            f.write("\n4. 跳过低价值目标，集中资源在高价值目标上")
            f.write("\n5. 定期更新模型数据以提高预测准确性")

        logger.info(f"批量分析报告已保存: {filename}")

def main():
    """主函数"""
    print("启动AI辅助决策系统...")

    ai_system = AIAssistedDecisionSystem()

    # 测试目标数据
    test_targets = [
        {
            "name": "NetPost Vietnam",
            "url": "https://netpost.vn",
            "country": "Vietnam",
            "sector": "Logistics",
            "vulnerability_type": "SQL Injection",
            "environment": "production",
            "mitigation_level": "medium"
        },
        {
            "name": "Vietnamese Customs",
            "url": "https://customs.gov.vn",
            "country": "Vietnam",
            "sector": "Government",
            "vulnerability_type": "Authentication Bypass",
            "environment": "production",
            "mitigation_level": "high"
        },
        {
            "name": "Thai Finance Gateway",
            "url": "https://thaifinance.paygw.com",
            "country": "Thailand",
            "sector": "Finance",
            "vulnerability_type": "API Security",
            "environment": "production",
            "mitigation_level": "low"
        },
        {
            "name": "TBAC",
            "url": "https://tbac.or.th",
            "country": "Thailand",
            "sector": "Banking",
            "vulnerability_type": "SQL Injection",
            "environment": "production",
            "mitigation_level": "low"
        },
        {
            "name": "VNPost System",
            "url": "https://vnpost.vn",
            "country": "Vietnam",
            "sector": "Logistics",
            "vulnerability_type": "Business Logic",
            "environment": "production",
            "mitigation_level": "medium"
        }
    ]

    print(f"\n开始分析 {len(test_targets)} 个目标...")

    results = ai_system.batch_analyze_targets(test_targets)

    print("\n" + "=" * 80)
    print("AI辅助决策分析完成!")
    print("=" * 80)
    print(f"分析目标: {len(test_targets)} 个")
    print(f"高优先级目标: {len([r for r in results if r.recommended_action == 'immediate'])} 个")
    print(f"中优先级目标: {len([r for r in results if r.recommended_action == 'scheduled'])} 个")
    print(f"监控目标: {len([r for r in results if r.recommended_action == 'monitoring'])} 个")
    print(f"低价值目标: {len([r for r in results if r.recommended_action == 'skip'])} 个")
    print("=" * 80)

if __name__ == "__main__":
    main()