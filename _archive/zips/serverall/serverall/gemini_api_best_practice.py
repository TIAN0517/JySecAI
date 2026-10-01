#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API 最佳实践示例
使用测试成功的最佳API密钥和模型组合
"""

import requests
import json
from datetime import datetime

# 最佳API配置 (基于测试结果)
BEST_API_KEY = "AIzaSyDS5cBxLD5n1hFL..."
BEST_MODEL = "gemini-2.0-flash-exp"  # 100%成功率
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

class GeminiAPIBestPractice:
    def __init__(self):
        self.api_key = BEST_API_KEY
        self.model = BEST_MODEL
        self.base_url = BASE_URL

    def make_request(self, prompt, temperature=0.7, max_tokens=1000):
        """发送请求到Gemini API"""
        headers = {
            "Content-Type": "application/json"
        }

        data = {
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
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.8,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return {
                        "success": True,
                        "response": result["candidates"][0]["content"]["parts"][0]["text"],
                        "model": self.model,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": "API返回成功但没有内容",
                        "model": self.model
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "model": self.model
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"请求失败: {str(e)}",
                "model": self.model
            }

    def code_generation(self, language, requirements):
        """代码生成功能"""
        prompt = f"""请为{language}编写代码，满足以下要求：

需求：
{requirements}

请提供完整、可运行的代码，并包含必要的注释。"""

        return self.make_request(prompt)

    def data_analysis(self, data_description, analysis_type):
        """数据分析功能"""
        prompt = f"""请对以下数据进行{analysis_type}分析：

数据描述：
{data_description}

请提供详细的分析结果和建议。"""

        return self.make_request(prompt)

    def security_analysis(self, code_or_config):
        """安全分析功能"""
        prompt = f"""请对以下代码或配置进行安全分析：

{code_or_config}

请识别潜在的安全漏洞，并提供修复建议。"""

        return self.make_request(prompt)

    def creative_writing(self, topic, style="专业"):
        """创意写作功能"""
        prompt = f"""请以{style}风格写一篇关于{topic}的文章。

要求：
1. 内容丰富有价值
2. 结构清晰
3. 语言流畅
4. 适合目标读者"""

        return self.make_request(prompt)

    def problem_solving(self, problem_description):
        """问题解决功能"""
        prompt = f"""请帮助解决以下问题：

问题描述：
{problem_description}

请提供：
1. 问题分析
2. 多种解决方案
3. 推荐方案
4. 实施步骤"""

        return self.make_request(prompt)

def main():
    """主函数 - 演示各种功能"""
    client = GeminiAPIBestPractice()

    print("=" * 60)
    print("🚀 Gemini API 最佳实践示例")
    print("=" * 60)
    print(f"使用模型: {client.model}")
    print(f"API密钥: {client.api_key[:20]}...")
    print()

    # 1. 代码生成示例
    print("📝 示例1: Python代码生成")
    code_result = client.code_generation(
        "Python",
        "创建一个简单的REST API服务器，使用Flask框架，包含GET和POST端点"
    )

    if code_result["success"]:
        print("✅ 代码生成成功:")
        print(code_result["response"][:200] + "..." if len(code_result["response"]) > 200 else code_result["response"])
    else:
        print(f"❌ 代码生成失败: {code_result['error']}")

    print("\n" + "-" * 40 + "\n")

    # 2. 数据分析示例
    print("📊 示例2: 数据分析")
    analysis_result = client.data_analysis(
        "用户行为数据，包含访问时间、页面停留时间、点击次数等",
        "用户行为模式分析"
    )

    if analysis_result["success"]:
        print("✅ 数据分析成功:")
        print(analysis_result["response"][:200] + "..." if len(analysis_result["response"]) > 200 else analysis_result["response"])
    else:
        print(f"❌ 数据分析失败: {analysis_result['error']}")

    print("\n" + "-" * 40 + "\n")

    # 3. 安全分析示例
    print("🔒 示例3: 安全分析")
    security_result = client.security_analysis(
        """
import sqlite3
import hashlib

def login(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # 简单的密码验证
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)

    return cursor.fetchone()
        """
    )

    if security_result["success"]:
        print("✅ 安全分析成功:")
        print(security_result["response"][:300] + "..." if len(security_result["response"]) > 300 else security_result["response"])
    else:
        print(f"❌ 安全分析失败: {security_result['error']}")

    print("\n" + "=" * 60)
    print("📋 示例完成！您可以根据需要调整提示词。")
    print("=" * 60)

if __name__ == "__main__":
    main()