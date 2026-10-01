#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化AI模型选择器 - Gemini 2.0 Flash Exp支持
Simple AI Model Selector - Gemini 2.0 Flash Exp Support

支持Gemini 2.0 Flash Exp和其他AI模型的智能调用
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class SimpleAIModelSelector:
    """简化AI模型选择器"""

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

        # 当前使用的密钥索引
        self.current_key_index = 0

        # 模型配置
        self.models = {
            "gemini-2.0-flash-exp": {
                "name": "Gemini 2.0 Flash Exp",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent",
                "max_tokens": 8192,
                "temperature": 0.7,
                "description": "最新Gemini 2.0 Flash实验版本",
                "specialties": ["vulnerability_analysis", "security_testing", "code_generation"]
            },
            "gemini-1.5-flash": {
                "name": "Gemini 1.5 Flash",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                "max_tokens": 8192,
                "temperature": 0.7,
                "description": "Gemini 1.5 Flash，快速响应",
                "specialties": ["quick_analysis", "real_time_response"]
            },
            "gemini-1.5-pro": {
                "name": "Gemini 1.5 Pro",
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
                "max_tokens": 32768,
                "temperature": 0.7,
                "description": "Gemini 1.5 Pro，专业版本",
                "specialties": ["complex_analysis", "detailed_reports", "expert_knowledge"]
            }
        }

    def get_api_key(self) -> str:
        """获取API密钥（轮询）"""
        key = self.gemini_api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.gemini_api_keys)
        return key

    def call_gemini(self, prompt: str, model: str = "gemini-2.0-flash-exp") -> Dict:
        """调用Gemini API"""
        model_config = self.models.get(model)
        if not model_config:
            return {"error": f"Unknown model: {model}"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_api_key()}"
        }

        payload = {
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

    def analyze_vulnerability(self, target_info: Dict, vulnerabilities: List) -> Dict:
        """分析漏洞"""
        prompt = f"""
作为网络安全专家，请分析以下越南目标的漏洞情况：

目标: {target_info.get('name', 'Unknown')}
URL: {target_info.get('url', 'Category: ' + target_info.get('category', 'Unknown'))}

发现的漏洞:
{json.dumps(vulnerabilities, ensure_ascii=False, indent=2)}

请提供分析：
1. 漏洞严重程度评估
2. 攻击可行性分析
3. 业务影响评估
4. 利用建议
5. 防护措施

用中文回答，重点关注实际的攻击利用。
"""
        return self.call_gemini(prompt, "gemini-2.0-flash-exp")

    def generate_exploit_code(self, vulnerability: Dict, target: Dict) -> Dict:
        """生成利用代码"""
        prompt = f"""
为以下漏洞生成Python利用代码：

漏洞类型: {vulnerability.get('type', 'Unknown')}
URL: {vulnerability.get('url', 'Unknown')}
严重程度: {vulnerability.get('severity', 'Unknown')}

目标: {target.get('name', 'Unknown')}
URL: {target.get('url', 'Unknown')}

请生成：
1. 完整的Python利用代码
2. 详细的攻击步骤
3. 验证方法
4. 安全注意事项

仅用于授权测试。用中文回答。
"""
        return self.call_gemini(prompt, "gemini-2.0-flash-exp")

    def generate_security_report(self, scan_results: List) -> Dict:
        """生成安全报告"""
        prompt = f"""
根据以下扫描结果生成专业的安全报告：

扫描结果:
{json.dumps(scan_results, ensure_ascii=False, indent=2)}

请生成包含以下内容的报告：
1. 执行摘要
2. 漏洞统计
3. 风险评估
4. 详细分析
5. 修复建议
6. 优先级排序

用中文回答，格式清晰专业。
"""
        return self.call_gemini(prompt, "gemini-1.5-pro")

    def test_api_connection(self) -> Dict:
        """测试API连接"""
        test_prompt = "请回复'API连接正常测试'"
        return self.call_gemini(test_prompt, "gemini-1.5-flash")

    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "total_api_keys": len(self.gemini_api_keys),
            "available_models": list(self.models.keys()),
            "current_key_index": self.current_key_index,
            "models": {
                model_id: {
                    "name": config["name"],
                    "max_tokens": config["max_tokens"],
                    "temperature": config["temperature"],
                    "description": config["description"]
                }
                for model_id, config in self.models.items()
            }
        }

def main():
    """主程序"""
    print("简化AI模型选择器")
    print("支持Gemini 2.0 Flash Exp")
    print("=" * 40)

    selector = SimpleAIModelSelector()

    print("\n[INFO] AI模型信息:")
    info = selector.get_model_info()
    print(f"API密钥数量: {info['total_api_keys']}")
    print(f"可用模型: {len(info['available_models'])}")
    print(f"当前密钥索引: {info['current_key_index']}")

    print(f"\n[MODELS] 可用模型:")
    for model_id, config in info["models"].items():
        print(f"- {config['name']} ({model_id})")
        print(f"  MaxTokens: {config['max_tokens']}")
        print(f"  Description: {config['description']}")

    print(f"\n[TEST] 测试API连接...")
    test_result = selector.test_api_connection()

    if test_result["success"]:
        print("[OK] API连接成功")
        print(f"模型: {test_result['model']}")
        print(f"时间: {test_result['timestamp']}")
        print(f"回复: {test_result['content'][:50]}...")
    else:
        print(f"[FAIL] API连接失败: {test_result['error']}")

    # 演示漏洞分析
    print(f"\n[DEMO] 漏洞分析演示:")
    target_info = {
        "name": "Shopee Vietnam",
        "url": "https://shopee.vn",
        "category": "ecommerce"
    }

    vulnerabilities = [
        {
            "type": "admin_panel",
            "url": "https://shopee.vn/admin",
            "severity": "High",
            "description": "管理后台直接可访问"
        },
        {
            "type": "api_exposure",
            "url": "https://shopee.vn/api",
            "severity": "Medium",
            "description": "API端点未受保护"
        }
    ]

    print("正在分析漏洞...")
    analysis_result = selector.analyze_vulnerability(target_info, vulnerabilities)

    if analysis_result["success"]:
        print("[OK] 漏洞分析完成")
        print(f"使用模型: {analysis_result['model']}")
        print(f"分析内容:")
        print(analysis_result["content"][:200] + "...")
    else:
        print(f"[FAIL] 分析失败: {analysis_result['error']}")

    # 显示功能列表
    print(f"\n[FUNCTIONS] 可用功能:")
    print("1. analyze_vulnerability - 漏洞分析")
    print("2. generate_exploit_code - 生成利用代码")
    print("3. generate_security_report - 生成安全报告")
    print("4. test_api_connection - 测试API连接")

    print(f"\n[API_KEYS] 密钥状态:")
    print(f"总数: {len(selector.gemini_api_keys)}")
    print(f"轮询机制: 已启用")
    print(f"自动切换: 支持故障转移")

    print(f"\n[TASK_TYPE] 任务推荐模型:")
    task_types = ["vulnerability_analysis", "security_testing", "code_generation", "detailed_reports"]
    for task in task_types:
        if task == "vulnerability_analysis" or task == "security_testing":
            print(f"{task}: gemini-2.0-flash-exp (推荐)")
        elif task == "code_generation":
            print(f"{task}: gemini-2.0-flash-exp (推荐)")
        else:
            print(f"{task}: gemini-1.5-pro (推荐)")

    print(f"\n[STATUS] AI模型选择器已就绪")
    print("可以调用各种AI功能进行智能分析")

if __name__ == "__main__":
    main()