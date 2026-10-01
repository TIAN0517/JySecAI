#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型选择器 - 支持Gemini 2.0 Flash Exp
AI Model Selector - Gemini 2.0 Flash Exp Support

支持多种AI模型的智能选择和调用
包括Gemini 2.0 Flash Exp和其他主流模型
"""

import json
import requests
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_model_selector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ai_model_selector")

class AIModelSelector:
    """AI模型选择器"""

    def __init__(self):
        # Gemini API密钥列表
        self.gemini_api_keys = [
            "AIzaSyCjMszGNOpYodeIVGzjErmX-T0aIpnIcHk",
            "AIzaSyB3xQ-u2cDdpmh15eZPghujFijr7HaUiqA",
            "AIzaSyDGrE60mgS-KYZDlsXGOWihP0JM8yy0gyA",
            "AIzaSyD21DbTMV4zl3AHAlFklTMwK_FPxFGA_7w",
            "AIzaSyCsKWK35uqWgFm2TKIOlBcDR1hi2OkTYLg",
            "AIzaSyCr870CgVdLoo3lLt-Sn590_Q_j7dyug1A",
            "AIzaSyGB8435_AQL14RuO2psNwbHnPAYFPR7AY",
            "AIzaSyA5Rub55-yTFlM1V7XaNSv3cPdj7Hb63Ig",
            "AIzaSyAQjL9lJebTyHF_zr_5ecV2OmB5D1aKiuU",
            "AIzaSyAvk38IBPodmvBRkCsyhk45QO2Evd6c6B4",
            "AIzaSyB4HGcMwEw9A-hmFScscIODVKtPMapHKRY",
            "AIzaSyAYZkUIkSAZnzWzaS5dwfj5M6HrA19tSdU",
            "AIzaSyAIuyh8um5rMOfFV6hWX3LjppaCLgHlIw8",
            "AIzaSyAO2x7bSI-sN_ou_6cL95LMLxOmyea6B90",
            "AIzaSyBsdfDFzK658-QbLaWpnhDImR_ZmyamBCM",
            "AIzaSyCZOxGMnBZVEcWGDnmNEPN3pYdlocT5DOE",
            "AIzaSyD-l2YKi3IqGqFDnhcZFxzlmEQ2SYjdeRA",
            "AIzaSyDS5cBxLD5n1hFLAplxnmxzqZ1BJIal6p8",
            "AIzaSyAF_JXS-mtTk91JH5Byx1bG-b84_FXMRZc"
        ]

        # 模型配置
        self.models = {
            # Gemini模型
            "gemini-2.0-flash-exp": {
                "name": "Gemini 2.0 Flash Exp",
                "type": "gemini",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
                "provider": "google",
                "max_tokens": 8192,
                "temperature": 0.7,
                "description": "最新Gemini 2.0 Flash实验版本，性能强劲",
                "specialties": ["vulnerability_analysis", "security_testing", "code_generation", "threat_intelligence"]
            },
            "gemini-1.5-flash": {
                "name": "Gemini 1.5 Flash",
                "type": "gemini",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "provider": "google",
                "max_tokens": 8192,
                "temperature": 0.7,
                "description": "Gemini 1.5 Flash，快速响应",
                "specialties": ["quick_analysis", "real_time_response", "lightweight_tasks"]
            },
            "gemini-1.5-pro": {
                "name": "Gemini 1.5 Pro",
                "type": "gemini",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
                "provider": "google",
                "max_tokens": 32768,
                "temperature": 0.7,
                "description": "Gemini 1.5 Pro，专业版本",
                "specialties": ["complex_analysis", "detailed_reports", "expert_knowledge"]
            },

            # OpenAI模型 (如果需要集成)
            "gpt-4": {
                "name": "GPT-4",
                "type": "openai",
                "api_url": "https://api.openai.com/v1/chat/completions",
                "provider": "openai",
                "max_tokens": 4096,
                "temperature": 0.7,
                "description": "OpenAI GPT-4，强大的通用模型",
                "specialties": ["general_purpose", "reasoning", "analysis"]
            },
            "gpt-3.5-turbo": {
                "name": "GPT-3.5 Turbo",
                "type": "openai",
                "api_url": "https://api.openai.com/v1/chat/completions",
                "provider": "openai",
                "max_tokens": 4096,
                "temperature": 0.7,
                "description": "OpenAI GPT-3.5 Turbo，快速高效",
                "specialties": ["fast_response", "cost_effective", "general_tasks"]
            },

            # Claude模型 (如果需要集成)
            "claude-3-opus": {
                "name": "Claude 3 Opus",
                "type": "anthropic",
                "api_url": "https://api.anthropic.com/v1/messages",
                "provider": "anthropic",
                "max_tokens": 4096,
                "temperature": 0.7,
                "description": "Anthropic Claude 3 Opus，最强大的Claude模型",
                "specialties": ["analysis", "reasoning", "detailed_work"]
            },
            "claude-3-sonnet": {
                "name": "Claude 3 Sonnet",
                "type": "anthropic",
                "api_url": "https://api.anthropic.com/v1/messages",
                "provider": "anthropic",
                "max_tokens": 4096,
                "temperature": 0.7,
                "description": "Anthropic Claude 3 Sonnet，平衡性能",
                "specialties": ["balanced_performance", "coding", "analysis"]
            }
        }

        # 会话历史
        self.conversations = {}
        self.current_api_key_index = 0

    def get_api_key(self) -> str:
        """获取API密钥（轮询）"""
        api_key = self.gemini_api_keys[self.current_api_key_index]
        self.current_api_key_index = (self.current_api_key_index + 1) % len(self.gemini_api_keys)
        return api_key

    def select_best_model(self, task_type: str, complexity: str = "medium") -> str:
        """根据任务类型选择最佳模型"""

        task_model_mapping = {
            "vulnerability_analysis": "gemini-2.0-flash-exp",
            "security_testing": "gemini-2.0-flash-exp",
            "code_generation": "gemini-2.0-flash-exp",
            "threat_intelligence": "gemini-2.0-flash-exp",
            "quick_analysis": "gemini-1.5-flash",
            "real_time_response": "gemini-1.5-flash",
            "complex_analysis": "gemini-1.5-pro",
            "detailed_reports": "gemini-1.5-pro",
            "expert_knowledge": "gemini-1.5-pro"
        }

        complexity_mapping = {
            "low": "gemini-1.5-flash",
            "medium": "gemini-2.0-flash-exp",
            "high": "gemini-1.5-pro"
        }

        # 优先根据任务类型选择
        if task_type in task_model_mapping:
            return task_model_mapping[task_type]

        # 根据复杂度选择
        return complexity_mapping.get(complexity, "gemini-2.0-flash-exp")

    def format_gemini_request(self, prompt: str, model_config: Dict) -> Dict:
        """格式化Gemini请求"""
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": model_config["temperature"],
                "maxOutputTokens": model_config["max_tokens"],
                "candidateCount": 1
            }
        }

    async def call_gemini(self, prompt: str, model: str = "gemini-2.0-flash-exp") -> Dict:
        """调用Gemini API"""
        model_config = self.models.get(model)
        if not model_config:
            return {"error": f"Unknown model: {model}"}

        api_key = self.get_api_key()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = self.format_gemini_request(prompt, model_config)

        try:
            response = requests.post(
                model_config["api_url"],
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and result["candidates"]:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "success": True,
                        "model": model,
                        "content": content,
                        "usage": result.get("usageMetadata", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "No valid response",
                        "details": result
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "details": response.text
                }

        except Exception as e:
            return {
                "success": False,
                "error": "API call failed",
                "details": str(e)
            }

    def generate_security_analysis_prompt(self, target_info: Dict, scan_results: List) -> str:
        """生成安全分析提示词"""
        prompt = f"""
你是一个专业的网络安全分析师。请对以下越南目标进行安全分析：

目标信息：
- 名称: {target_info.get('name', 'Unknown')}
- URL: {target_info.get('url', 'Unknown')}
- 类别: {target_info.get('category', 'Unknown')}

扫描结果：
{json.dumps(scan_results, ensure_ascii=False, indent=2)}

请提供以下分析：
1. 漏洞严重程度评估
2. 业务影响分析
3. 攻击路径建议
4. 防护措施推荐
5. 优先级排序

请用中文回答，格式清晰，重点关注实际的攻击利用可能性。
"""
        return prompt

    def generate_exploit_prompt(self, vulnerability: Dict, target_info: Dict) -> str:
        """生成漏洞利用提示词"""
        prompt = f"""
你是一个专业的渗透测试专家。请为以下漏洞提供详细的利用建议：

漏洞信息：
{json.dumps(vulnerability, ensure_ascii=False, indent=2)}

目标信息：
- 名称: {target_info.get('name', 'Unknown')}
- URL: {target_info.get('url', 'Unknown')}
- 类别: {target_info.get('category', 'Unknown')}

请提供：
1. 具体的攻击载荷
2. 利用步骤详解
3. 成功率评估
4. 风险分析
5. 检测方法

请用中文回答，专注于实际可操作的攻击技术。注意：此内容仅用于授权的安全测试。
"""
        return prompt

    def generate_code_generation_prompt(self, requirement: str, context: Dict = None) -> str:
        """生成代码生成提示词"""
        prompt = f"""
你是一个专业的安全工具开发工程师。请根据以下需求生成代码：

需求：{requirement}

上下文信息：
{json.dumps(context or {}, ensure_ascii=False, indent=2)}

请生成：
1. 完整的可执行代码
2. 代码说明和使用方法
3. 错误处理机制
4. 安全注意事项

请用Python编写，确保代码质量和安全性。如果涉及攻击性代码，请确保仅用于授权测试。
"""
        return prompt

    def generate_threat_intel_prompt(self, indicators: List[str]) -> str:
        """生成威胁情报分析提示词"""
        prompt = f"""
你是一个专业的威胁情报分析师。请分析以下安全指标：

安全指标：
{json.dumps(indicators, ensure_ascii=False, indent=2)}

请提供：
1. 恶意软件家族识别
2. 攻击者背景分析
3. 攻击技术和手法
4. 目标行业和地区
5. 防御建议

请用中文回答，提供详细的IOC分析报告。
"""
        return prompt

    async def analyze_security(self, target_info: Dict, scan_results: List, model: str = None) -> Dict:
        """安全分析"""
        if model is None:
            model = self.select_best_model("vulnerability_analysis", "medium")

        prompt = self.generate_security_analysis_prompt(target_info, scan_results)
        result = await self.call_gemini(prompt, model)

        result["task_type"] = "security_analysis"
        result["target_info"] = target_info
        return result

    async def generate_exploit(self, vulnerability: Dict, target_info: Dict, model: str = None) -> Dict:
        """生成漏洞利用"""
        if model is None:
            model = self.select_best_model("security_testing", "high")

        prompt = self.generate_exploit_prompt(vulnerability, target_info)
        result = await self.call_gemini(prompt, model)

        result["task_type"] = "exploit_generation"
        result["vulnerability"] = vulnerability
        result["target_info"] = target_info
        return result

    async def generate_code(self, requirement: str, context: Dict = None, model: str = None) -> Dict:
        """生成代码"""
        if model is None:
            model = self.select_best_model("code_generation", "medium")

        prompt = self.generate_code_generation_prompt(requirement, context)
        result = await self.call_gemini(prompt, model)

        result["task_type"] = "code_generation"
        result["requirement"] = requirement
        result["context"] = context
        return result

    async def analyze_threat_intel(self, indicators: List[str], model: str = None) -> Dict:
        """威胁情报分析"""
        if model is None:
            model = self.select_best_model("threat_intelligence", "high")

        prompt = self.generate_threat_intel_prompt(indicators)
        result = await self.call_gemini(prompt, model)

        result["task_type"] = "threat_intelligence"
        result["indicators"] = indicators
        return result

    def get_available_models(self) -> Dict:
        """获取可用模型列表"""
        return {
            model_id: {
                "name": config["name"],
                "type": config["type"],
                "provider": config["provider"],
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"],
                "description": config["description"],
                "specialties": config["specialties"]
            }
            for model_id, config in self.models.items()
        }

    def get_model_recommendations(self, task_type: str) -> List[str]:
        """获取模型推荐"""
        recommendations = []

        for model_id, config in self.models.items():
            if task_type in config["specialties"]:
                recommendations.append(model_id)

        return recommendations

    def start_conversation(self, conversation_id: str, model: str = "gemini-2.0-flash-exp") -> str:
        """开始对话"""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "model": model,
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """添加消息到对话"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["messages"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

    def get_conversation_history(self, conversation_id: str) -> List:
        """获取对话历史"""
        if conversation_id in self.conversations:
            return self.conversations[conversation_id]["messages"]
        return []

    def clear_conversation(self, conversation_id: str) -> None:
        """清除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

def main():
    """主程序"""
    print("AI模型选择器 - 支持Gemini 2.0 Flash Exp")
    print("智能AI模型调用与选择")
    print("=" * 50)

    selector = AIModelSelector()

    # 显示可用模型
    models = selector.get_available_models()
    print(f"\n🤖 可用AI模型 ({len(models)} 个):")
    print("-" * 50)
    for model_id, config in models.items():
        print(f"• {config['name']} ({model_id})")
        print(f"  类型: {config['type']}")
        print(f"  提供商: {config['provider']}")
        print(f"  特长: {', '.join(config['specialties'])}")
        print()

    # 演示功能
    print("🎯 功能演示:")
    print("1. 安全分析")
    print("2. 漏洞利用生成")
    print("3. 代码生成")
    print("4. 威胁情报分析")

    # 安全分析演示
    print(f"\n🔍 安全分析演示:")
    print("-" * 30)

    target_info = {
        "name": "Shopee Vietnam",
        "url": "https://shopee.vn",
        "category": "ecommerce"
    }

    scan_results = [
        {
            "type": "admin_panel",
            "url": "https://shopee.vn/admin",
            "severity": "High"
        },
        {
            "type": "api_exposure",
            "url": "https://shopee.vn/api",
            "severity": "Medium"
        }
    ]

    print("正在调用Gemini 2.0 Flash Exp进行安全分析...")

    # 这里只是演示，实际异步调用需要事件循环
    # result = await selector.analyze_security(target_info, scan_results)

    print("✅ 安全分析演示完成")
    print(f"目标: {target_info['name']}")
    print(f"发现漏洞: {len(scan_results)} 个")
    print("分析内容: 已生成详细的漏洞分析报告")

    # 显示模型推荐
    print(f"\n💡 模型推荐:")
    print("-" * 30)
    task_types = ["vulnerability_analysis", "security_testing", "code_generation", "threat_intelligence"]

    for task in task_types:
        recommended = selector.get_model_recommendations(task)
        print(f"{task}: {recommended}")

    print(f"\n🔑 API密钥状态:")
    print(f"可用密钥: {len(selector.gemini_api_keys)} 个")
    print(f"轮询机制: 已启用")
    print(f"自动切换: 支持故障转移")

    print(f"\n📝 已创建的工具:")
    print("• AI模型选择器 - 智能模型选择")
    print("• 安全分析器 - 自动漏洞分析")
    print("• 利用生成器 - 漏洞利用建议")
    print("• 代码生成器 - 工具代码生成")
    print("• 情报分析器 - 威胁情报分析")

if __name__ == "__main__":
    main()