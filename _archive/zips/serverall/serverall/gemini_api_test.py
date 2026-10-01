#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini API密钥测试脚本
测试Gemini 2.5 Flash-Lite和Gemini 2.0 Flash-Lite模型的可用性
"""

import requests
import json
import time
from datetime import datetime

# 您提供的API密钥列表
GEMINI_API_KEYS = [
    "AIzaSyCjMszGNOpYodeIVGzjErmX-T0aIpnIcHk",
    "AIzaSyB3xQ-u2cDdpmh15eZPghujFijr7HaUiqA",
    "AIzaSyDbuxSNqLYPyGOmR46lW0qJ4rdHhmXAE0",
    "AIzaSyCaxwg8pSTK5yAbbxCFIQU03LCSFDXK_YU",
    "AIzaSyAZLQjWFi57qPu-7y8Vyd7oEm9pCbBV3Z4",
    "AIzaSyAQjL9lJebTyHF_zr_5ecV2OmB5D1aKiuU",
    "AIzaSyAvk38IBPodmvBRkCsyhk45QO2Evd6c6B4",
    "AIzaSyAYZkUIkSAZnzWzaS5dwfj5M6HrA19tSdU",
    "AIzaSyAIuyh8um5rMOfFV6hWX3LjppaCLgHlIw8",
    "AIzaSyAO2x7bSI-sN_ou_6cL95LMLxOmyea6B90",
    "AIzaSyBsdfDFzK658-QbLaWpnhDImR_ZmyamBCM",
    "AIzaSyCZOxGMnBZVEcWGDnmNEPN3pYdlocT5DOE",
    "AIzaSyD-l2YKi3IqGqFDnhcZFxzlmEQ2SYjdeRA",
    "AIzaSyDS5cBxLD5n1hFLAplxnmxzqZ1BJIal6p8",
    "AIzaSyAF_JXS-mtTk91JH5Byx1bG-b84_FXMRZc",
    "AIzaSyCr870CgVdLoo3lLt-Sn590_Q_j7dyug1A",
    "AIzaSyCGB8435_AQL14RuO2psNwbHnPAYFPR7AY",
    "AIzaSyCsKWK35uqWgFm2TKIOlBcDR1hi2OkTYLg",
    "AIzaSyA5Rub55-yTFlM1V7XaNSv3cPdj7Hb63Ig",
    "AIzaSyB4HGcMwEw9A-hmFScscIODVKtPMapHKRY",
    "AIzaSyB4HGcMwEw9A-hmFScscIODVKtPMapHKRY"  # 重复的密钥，保留一个
]

# 测试模型列表
TEST_MODELS = [
    "gemini-2.5-flash-lite",      # Gemini 2.5 Flash-Lite
    "gemini-2.0-flash-exp",       # Gemini 2.0 Flash-Lite (实验版本)
    "gemini-1.5-flash"            # 备用模型
]

class GeminiAPITester:
    def __init__(self):
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.test_results = []

    def test_api_key(self, api_key, model):
        """测试单个API密钥和模型组合"""
        headers = {
            "Content-Type": "application/json"
        }

        # 简单的测试请求
        test_data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "你好，请简单回复确认这个API密钥是否工作正常，模型是否可用。"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 50,
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

        url = f"{self.base_url}/models/{model}:generateContent?key={api_key}"

        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=test_data, timeout=30)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    response_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return {
                        "status": "success",
                        "response_time": f"{end_time - start_time:.2f}s",
                        "response_text": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                        "model": model,
                        "api_key": api_key[:20] + "..."
                    }
                else:
                    return {
                        "status": "no_response",
                        "error": "API返回成功但没有内容",
                        "model": model,
                        "api_key": api_key[:20] + "..."
                    }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text[:100]}",
                    "model": model,
                    "api_key": api_key[:20] + "..."
                }

        except requests.exceptions.Timeout:
            return {
                "status": "timeout",
                "error": "请求超时",
                "model": model,
                "api_key": api_key[:20] + "..."
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "connection_error",
                "error": f"连接错误: {str(e)[:100]}",
                "model": model,
                "api_key": api_key[:20] + "..."
            }
        except Exception as e:
            return {
                "status": "unknown_error",
                "error": f"未知错误: {str(e)[:100]}",
                "model": model,
                "api_key": api_key[:20] + "..."
            }

    def run_tests(self):
        """运行所有API密钥测试"""
        print("Gemini API密钥测试开始")
        print("=" * 60)

        # 去重重复的密钥
        unique_keys = list(set(GEMINI_API_KEYS))
        print(f"总API密钥数量: {len(GEMINI_API_KEYS)}")
        print(f"去重后API密钥数量: {len(unique_keys)}")
        print(f"测试模型数量: {len(TEST_MODELS)}")
        print(f"总测试次数: {len(unique_keys) * len(TEST_MODELS)}")
        print("=" * 60)

        success_count = 0
        total_tests = 0

        for i, api_key in enumerate(unique_keys[:5], 1):  # 只测试前5个密钥以节省配额
            print(f"\n测试API密钥 {i}/5: {api_key[:20]}...")

            for model in TEST_MODELS:
                total_tests += 1
                print(f"  测试模型: {model}")

                result = self.test_api_key(api_key, model)
                self.test_results.append(result)

                if result["status"] == "success":
                    success_count += 1
                    print(f"    成功 - 响应时间: {result['response_time']}")
                    print(f"    回复: {result['response_text']}")
                else:
                    print(f"    失败 - {result['error']}")

                # 添加延迟避免频率限制
                time.sleep(1)

            print(f"  API密钥 {i} 测试完成")

        return success_count, total_tests

    def generate_report(self, success_count, total_tests):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("Gemini API测试报告")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"成功率: {success_count}/{total_tests} ({(success_count/total_tests)*100:.1f}%)")

        # 按模型统计成功情况
        model_stats = {}
        for result in self.test_results:
            model = result["model"]
            if model not in model_stats:
                model_stats[model] = {"success": 0, "total": 0}
            model_stats[model]["total"] += 1
            if result["status"] == "success":
                model_stats[model]["success"] += 1

        print("\n按模型统计:")
        for model, stats in model_stats.items():
            rate = (stats["success"]/stats["total"])*100 if stats["total"] > 0 else 0
            print(f"  {model}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

        # 找出最佳组合
        best_combinations = []
        for result in self.test_results:
            if result["status"] == "success":
                best_combinations.append(result)

        if best_combinations:
            print("\n推荐的API密钥和模型组合:")
            for i, result in enumerate(best_combinations[:3], 1):
                print(f"  {i}. 密钥: {result['api_key']} + 模型: {result['model']}")
                print(f"     响应时间: {result['response_time']}")

        # 保存详细结果
        try:
            with open("gemini_api_test_results.json", "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "total_tests": total_tests,
                        "success_count": success_count,
                        "success_rate": (success_count/total_tests)*100
                    },
                    "model_stats": model_stats,
                    "detailed_results": self.test_results
                }, f, ensure_ascii=False, indent=2)
            print(f"\n详细结果已保存到: gemini_api_test_results.json")
        except Exception as e:
            print(f"\n保存结果文件失败: {e}")

        return success_count > 0

def main():
    """主函数"""
    tester = GeminiAPITester()
    success_count, total_tests = tester.run_tests()
    has_working_keys = tester.generate_report(success_count, total_tests)

    print(f"\n测试结论: {'有可用的API密钥' if has_working_keys else '没有可用的API密钥'}")

    if has_working_keys:
        print("您可以开始使用Gemini API进行开发！")
        print("建议使用测试成功的密钥和模型组合")
    else:
        print("建议检查API密钥是否正确或网络连接")
        print("确认API密钥是否有效且未过期")

if __name__ == "__main__":
    main()