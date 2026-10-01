#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi AI Integration System v1.0.0
多AI模型集成系统

集成多个AI模型，提供智能化的安全分析和决策支持
支持Google Gemini、OpenAI GPT、Claude等主流AI模型
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import threading
from concurrent.futures import ThreadPoolExecutor

# AI模型导入
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('multi_ai_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIModel(Enum):
    """AI模型枚举"""
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    GEMINI_1_PRO = "gemini-1.5-pro"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4 = "gpt-4"
    GPT_35_TURBO = "gpt-3.5-turbo"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"

@dataclass
class AIResponse:
    """AI响应"""
    model: str
    content: str
    confidence: float
    response_time: float
    tokens_used: int
    success: bool
    error: Optional[str] = None

@dataclass
class AnalysisTask:
    """分析任务"""
    task_id: str
    task_type: str
    target_data: Dict
    models_to_use: List[AIModel]
    created_at: datetime
    priority: int = 1

class MultiAIIntegrationSystem:
    """多AI集成系统"""

    def __init__(self, config_file: str = "multi_ai_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

        # API密钥管理
        self.api_keys = self.config.get('api_keys', {})

        # AI模型客户端
        self.clients = {}
        self.initialize_clients()

        # 任务队列和结果缓存
        self.task_queue = []
        self.results_cache = {}

        # 性能统计
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'model_usage': {},
            'average_response_time': 0
        }

    def load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "api_keys": {
                "gemini": [
                    "AIzaSyDkVvdNFGuEUxT2jLQZ9mQjV9ZbM8pK7xC"
                ],
                "openai": [
                    # OpenAI API密钥
                ],
                "anthropic": [
                    # Anthropic API密钥
                ]
            },
            "model_preferences": {
                "vulnerability_analysis": [AIModel.GEMINI_2_FLASH.value, AIModel.GPT_4_TURBO.value],
                "business_logic": [AIModel.CLAUDE_3_OPUS.value, AIModel.GEMINI_1_PRO.value],
                "code_analysis": [AIModel.GPT_4.value, AIModel.CLAUDE_3_SONNET.value],
                "threat_assessment": [AIModel.GEMINI_2_FLASH.value, AIModel.CLAUDE_3_SONNET.value]
            },
            "rate_limits": {
                "gemini": 10,  # 每分钟请求数
                "openai": 20,
                "anthropic": 15
            },
            "fallback_enabled": True,
            "consensus_threshold": 0.7
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"配置文件加载失败，使用默认配置: {e}")

        # 保存配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        return default_config

    def initialize_clients(self):
        """初始化AI客户端"""
        # Gemini客户端
        if GEMINI_AVAILABLE and self.api_keys.get('gemini'):
            try:
                genai.configure(api_key=self.api_keys['gemini'][0])
                self.clients['gemini'] = {
                    'flash': genai.GenerativeModel('gemini-2.0-flash-exp'),
                    'pro': genai.GenerativeModel('gemini-1.5-pro')
                }
                logger.info("Gemini AI客户端初始化成功")
            except Exception as e:
                logger.error(f"Gemini客户端初始化失败: {e}")

        # OpenAI客户端
        if OPENAI_AVAILABLE and self.api_keys.get('openai'):
            try:
                openai.api_key = self.api_keys['openai'][0]
                self.clients['openai'] = openai
                logger.info("OpenAI客户端初始化成功")
            except Exception as e:
                logger.error(f"OpenAI客户端初始化失败: {e}")

        # Claude客户端
        if CLAUDE_AVAILABLE and self.api_keys.get('anthropic'):
            try:
                self.clients['claude'] = anthropic.Anthropic(
                    api_key=self.api_keys['anthropic'][0]
                )
                logger.info("Claude客户端初始化成功")
            except Exception as e:
                logger.error(f"Claude客户端初始化失败: {e}")

    def get_available_models(self) -> List[AIModel]:
        """获取可用的AI模型"""
        available_models = []

        if 'gemini' in self.clients:
            available_models.extend([AIModel.GEMINI_2_FLASH, AIModel.GEMINI_1_PRO])

        if 'openai' in self.clients:
            available_models.extend([AIModel.GPT_4_TURBO, AIModel.GPT_4, AIModel.GPT_35_TURBO])

        if 'claude' in self.clients:
            available_models.extend([AIModel.CLAUDE_3_OPUS, AIModel.CLAUDE_3_SONNET, AIModel.CLAUDE_3_HAIKU])

        return available_models

    async def query_gemini(self, model: AIModel, prompt: str) -> AIResponse:
        """查询Gemini模型"""
        if 'gemini' not in self.clients:
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=0.0,
                tokens_used=0,
                success=False,
                error="Gemini客户端未初始化"
            )

        start_time = time.time()
        try:
            if model == AIModel.GEMINI_2_FLASH:
                gemini_model = self.clients['gemini']['flash']
            else:
                gemini_model = self.clients['gemini']['pro']

            response = await asyncio.to_thread(gemini_model.generate_content, prompt)

            response_time = time.time() - start_time

            return AIResponse(
                model=model.value,
                content=response.text,
                confidence=0.85,  # Gemini通常有较高的置信度
                response_time=response_time,
                tokens_used=len(response.text.split()),  # 近似token数
                success=True
            )

        except Exception as e:
            logger.error(f"Gemini查询失败 {model.value}: {e}")
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=time.time() - start_time,
                tokens_used=0,
                success=False,
                error=str(e)
            )

    async def query_openai(self, model: AIModel, prompt: str) -> AIResponse:
        """查询OpenAI模型"""
        if 'openai' not in self.clients:
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=0.0,
                tokens_used=0,
                success=False,
                error="OpenAI客户端未初始化"
            )

        start_time = time.time()
        try:
            model_mapping = {
                AIModel.GPT_4_TURBO: "gpt-4-turbo-preview",
                AIModel.GPT_4: "gpt-4",
                AIModel.GPT_35_TURBO: "gpt-3.5-turbo"
            }

            response = await asyncio.to_thread(
                self.clients['openai'].chat.completions.create,
                model=model_mapping[model],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7
            )

            response_time = time.time() - start_time

            return AIResponse(
                model=model.value,
                content=response.choices[0].message.content,
                confidence=0.9,
                response_time=response_time,
                tokens_used=response.usage.total_tokens,
                success=True
            )

        except Exception as e:
            logger.error(f"OpenAI查询失败 {model.value}: {e}")
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=time.time() - start_time,
                tokens_used=0,
                success=False,
                error=str(e)
            )

    async def query_claude(self, model: AIModel, prompt: str) -> AIResponse:
        """查询Claude模型"""
        if 'claude' not in self.clients:
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=0.0,
                tokens_used=0,
                success=False,
                error="Claude客户端未初始化"
            )

        start_time = time.time()
        try:
            model_mapping = {
                AIModel.CLAUDE_3_OPUS: "claude-3-opus-20240229",
                AIModel.CLAUDE_3_SONNET: "claude-3-sonnet-20240229",
                AIModel.CLAUDE_3_HAIKU: "claude-3-haiku-20240307"
            }

            response = await asyncio.to_thread(
                self.clients['claude'].messages.create,
                model=model_mapping[model],
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_time = time.time() - start_time

            return AIResponse(
                model=model.value,
                content=response.content[0].text,
                confidence=0.88,
                response_time=response_time,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                success=True
            )

        except Exception as e:
            logger.error(f"Claude查询失败 {model.value}: {e}")
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=time.time() - start_time,
                tokens_used=0,
                success=False,
                error=str(e)
            )

    async def query_model(self, model: AIModel, prompt: str) -> AIResponse:
        """通用模型查询接口"""
        if model in [AIModel.GEMINI_2_FLASH, AIModel.GEMINI_1_PRO]:
            return await self.query_gemini(model, prompt)
        elif model in [AIModel.GPT_4_TURBO, AIModel.GPT_4, AIModel.GPT_35_TURBO]:
            return await self.query_openai(model, prompt)
        elif model in [AIModel.CLAUDE_3_OPUS, AIModel.CLAUDE_3_SONNET, AIModel.CLAUDE_3_HAIKU]:
            return await self.query_claude(model, prompt)
        else:
            return AIResponse(
                model=model.value,
                content="",
                confidence=0.0,
                response_time=0.0,
                tokens_used=0,
                success=False,
                error=f"不支持的模型: {model.value}"
            )

    async def consensus_analysis(self, prompt: str, task_type: str) -> Dict:
        """共识分析 - 使用多个模型分析同一问题"""
        preferred_models = self.config.get('model_preferences', {}).get(task_type, [])

        if not preferred_models:
            # 如果没有首选模型，使用所有可用模型
            available_models = self.get_available_models()
            preferred_models = [model.value for model in available_models[:3]]  # 最多使用3个模型

        # 转换为AIModel枚举
        models_to_use = []
        for model_str in preferred_models:
            try:
                model = AIModel(model_str)
                if model in self.get_available_models():
                    models_to_use.append(model)
            except ValueError:
                continue

        if not models_to_use:
            logger.warning("没有可用的AI模型进行共识分析")
            return {"error": "没有可用的AI模型"}

        logger.info(f"开始共识分析，使用模型: {[m.value for m in models_to_use]}")

        # 并发查询所有模型
        tasks = [self.query_model(model, prompt) for model in models_to_use]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤成功的响应
        successful_responses = []
        for response in responses:
            if isinstance(response, AIResponse) and response.success:
                successful_responses.append(response)
            elif isinstance(response, Exception):
                logger.error(f"模型查询异常: {response}")

        if not successful_responses:
            logger.error("所有模型查询都失败了")
            return {"error": "所有模型查询都失败了"}

        # 分析共识
        consensus_result = self.analyze_consensus(successful_responses)

        # 更新使用统计
        self.update_usage_stats(successful_responses)

        return consensus_result

    def analyze_consensus(self, responses: List[AIResponse]) -> Dict:
        """分析多个AI响应的共识"""
        if len(responses) == 1:
            return {
                "consensus_level": 1.0,
                "primary_response": responses[0].content,
                "confidence": responses[0].confidence,
                "supporting_models": [responses[0].model],
                "all_responses": [r.__dict__ for r in responses]
            }

        # 简单的共识分析 - 在实际应用中可以使用更复杂的NLP技术
        consensus_threshold = self.config.get('consensus_threshold', 0.7)

        # 计算平均置信度
        avg_confidence = sum(r.confidence for r in responses) / len(responses)

        # 选择最高置信度的响应作为主要响应
        primary_response = max(responses, key=lambda r: r.confidence)

        # 计算共识等级
        similar_responses = 0
        for response in responses:
            if response != primary_response:
                # 简单的相似度计算（可以改进）
                similarity = self.calculate_similarity(primary_response.content, response.content)
                if similarity > 0.6:
                    similar_responses += 1

        consensus_level = (similar_responses + 1) / len(responses)

        return {
            "consensus_level": consensus_level,
            "primary_response": primary_response.content,
            "confidence": avg_confidence,
            "supporting_models": [r.model for r in responses if r.success],
            "all_responses": [r.__dict__ for r in responses],
            "recommendation": "高共识" if consensus_level >= consensus_threshold else "低共识，建议人工审核"
        }

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简化版）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def update_usage_stats(self, responses: List[AIResponse]):
        """更新使用统计"""
        self.usage_stats['total_requests'] += len(responses)

        successful_count = sum(1 for r in responses if r.success)
        self.usage_stats['successful_requests'] += successful_count
        self.usage_stats['failed_requests'] += len(responses) - successful_count

        # 更新模型使用统计
        for response in responses:
            if response.success:
                if response.model not in self.usage_stats['model_usage']:
                    self.usage_stats['model_usage'][response.model] = 0
                self.usage_stats['model_usage'][response.model] += 1

        # 更新平均响应时间
        total_time = sum(r.response_time for r in responses)
        self.usage_stats['average_response_time'] = total_time / len(responses)

    async def analyze_vulnerability(self, vulnerability_data: Dict) -> Dict:
        """AI驱动的漏洞分析"""
        prompt = f"""
        作为高级网络安全专家，请分析以下漏洞信息：

        漏洞数据: {json.dumps(vulnerability_data, ensure_ascii=False)}

        请提供：
        1. 漏洞严重性评估 (0-10分)
        2. 利用难度评估
        3. 潜在影响分析
        4. 修复建议
        5. 相关攻击向量

        请以JSON格式返回分析结果。
        """

        return await self.consensus_analysis(prompt, "vulnerability_analysis")

    async def analyze_business_logic(self, business_data: Dict) -> Dict:
        """AI驱动的业务逻辑分析"""
        prompt = f"""
        作为业务逻辑安全专家，请分析以下业务流程的安全风险：

        业务数据: {json.dumps(business_data, ensure_ascii=False)}

        请重点关注：
        1. 权限控制缺陷
        2. 数据验证问题
        3. 业务流程绕过风险
        4. 经济损失风险
        5. 合规性问题

        请以JSON格式返回分析结果。
        """

        return await self.consensus_analysis(prompt, "business_logic")

    async def analyze_code_security(self, code_data: Dict) -> Dict:
        """AI驱动的代码安全分析"""
        prompt = f"""
        作为代码安全审计专家，请分析以下代码的安全问题：

        代码信息: {json.dumps(code_data, ensure_ascii=False)}

        请分析：
        1. 输入验证问题
        2. 注入攻击风险
        3. 认证授权缺陷
        4. 加密和数据保护
        5. 错误处理问题

        请以JSON格式返回分析结果。
        """

        return await self.consensus_analysis(prompt, "code_analysis")

    async def threat_assessment(self, threat_data: Dict) -> Dict:
        """AI驱动的威胁评估"""
        prompt = f"""
        作为威胁情报分析师，请评估以下安全威胁：

        威胁数据: {json.dumps(threat_data, ensure_ascii=False)}

        请评估：
        1. 威胁等级 (高/中/低)
        2. 攻击可能性
        3. 潜在损失评估
        4. 缓解措施建议
        5. 监控建议

        请以JSON格式返回分析结果。
        """

        return await self.consensus_analysis(prompt, "threat_assessment")

    def get_usage_report(self) -> Dict:
        """获取使用报告"""
        return {
            "usage_stats": self.usage_stats,
            "available_models": [model.value for model in self.get_available_models()],
            "configuration": {
                "fallback_enabled": self.config.get('fallback_enabled', True),
                "consensus_threshold": self.config.get('consensus_threshold', 0.7)
            },
            "performance": {
                "success_rate": (
                    self.usage_stats['successful_requests'] / max(1, self.usage_stats['total_requests'])
                ) * 100,
                "average_response_time": self.usage_stats['average_response_time']
            }
        }

async def main():
    """主函数"""
    print("Multi AI Integration System v1.0.0")
    print("=" * 80)

    # 初始化多AI系统
    ai_system = MultiAIIntegrationSystem()

    print(f"可用AI模型: {[model.value for model in ai_system.get_available_models()]}")
    print(f"共识阈值: {ai_system.config.get('consensus_threshold', 0.7)}")
    print(f"故障转移: {'启用' if ai_system.config.get('fallback_enabled', True) else '禁用'}")
    print()

    # 测试漏洞分析
    test_vulnerability = {
        "cve_id": "CVE-2024-10707",
        "description": "Chuanhugpt存在命令注入漏洞",
        "severity": "HIGH",
        "affected_component": "AI聊天接口"
    }

    print("测试AI驱动的漏洞分析...")
    vulnerability_analysis = await ai_system.analyze_vulnerability(test_vulnerability)

    print(f"漏洞分析结果:")
    print(f"  - 共识等级: {vulnerability_analysis.get('consensus_level', 0):.2f}")
    print(f"  - 置信度: {vulnerability_analysis.get('confidence', 0):.2f}")
    print(f"  - 支持模型: {len(vulnerability_analysis.get('supporting_models', []))}")
    print(f"  - 建议: {vulnerability_analysis.get('recommendation', 'N/A')}")

    # 测试业务逻辑分析
    test_business_logic = {
        "process": "快递订单价格计算",
        "description": "用户可以修改订单价格参数",
        "risk_factors": ["参数篡改", "业务绕过"]
    }

    print("\n测试AI驱动的业务逻辑分析...")
    business_analysis = await ai_system.analyze_business_logic(test_business_logic)

    print(f"业务逻辑分析结果:")
    print(f"  - 共识等级: {business_analysis.get('consensus_level', 0):.2f}")
    print(f"  - 置信度: {business_analysis.get('confidence', 0):.2f}")
    print(f"  - 支持模型: {len(business_analysis.get('supporting_models', []))}")

    # 生成使用报告
    usage_report = ai_system.get_usage_report()

    print("\nAI系统使用报告:")
    print(f"  - 总请求数: {usage_report['usage_stats']['total_requests']}")
    print(f"  - 成功率: {usage_report['performance']['success_rate']:.1f}%")
    print(f"  - 平均响应时间: {usage_report['performance']['average_response_time']:.2f}秒")

    if usage_report['usage_stats']['model_usage']:
        print("  - 模型使用统计:")
        for model, count in usage_report['usage_stats']['model_usage'].items():
            print(f"    * {model}: {count} 次")

    # 保存报告
    report_filename = f"ai_system_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump({
            'test_vulnerability_analysis': vulnerability_analysis,
            'test_business_logic_analysis': business_analysis,
            'usage_report': usage_report
        }, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n详细报告已保存: {report_filename}")

if __name__ == "__main__":
    asyncio.run(main())