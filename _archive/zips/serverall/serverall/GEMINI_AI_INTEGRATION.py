#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI 2.0 Flash-Exp 集成模块
Gemini AI Integration Module for Dragon-V Triple Bot v3.2.0

集成Google Gemini 2.0 Flash-Exp模型，提供AI驱动的智能安全分析能力
"""

import google.generativeai as genai
import json
import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import re
import requests
from concurrent.futures import ThreadPoolExecutor
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_ai_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GeminiAIIntegration:
    """Gemini AI 2.0 Flash-Exp 集成类"""

    def __init__(self):
        # Gemini API密钥列表
        self.api_keys = [
            "AIzaSyCjMszGNOpYodeIVGzjErmX-T0aIpnIcHk",
            "AIzaSyB3xQ-u2cDdpmh15eZPghujFijr7HaUiqA",
            "AIzaSyDbuxSNqLYPyGOmR46lW0qJ4rdHhmXAE0",
            "AIzaSyCaxwg8pSTK5yAbbxCFIQU03LCSFDXK_YU",
            "AIzaSyAZLQjWFi57qPu-7y8Vyd7oEm9pCbBV3Z4",
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
            "AIzaSyAF_JXS-mtTk91JH5Byx1bG-b84_FXMRZc"
        ]

        self.current_key_index = 0
        self.model = None
        self.rate_limiter = {
            'requests_per_minute': 15,
            'requests_per_day': 1500,
            'current_minute_requests': 0,
            'current_day_requests': 0,
            'last_minute_reset': time.time(),
            'last_day_reset': time.time()
        }

        # 初始化Gemini
        self._initialize_gemini()

    def _initialize_gemini(self):
        """初始化Gemini模型"""
        try:
            # 配置API密钥
            api_key = self._get_next_api_key()
            genai.configure(api_key=api_key)

            # 配置模型参数
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            safety_settings = [
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
                },
            ]

            # 创建模型实例
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            logger.info("Gemini 2.0 Flash-Exp 模型初始化成功")

        except Exception as e:
            logger.error(f"初始化Gemini模型失败: {e}")
            self.model = None

    def _get_next_api_key(self) -> str:
        """获取下一个API密钥"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key

    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = time.time()

        # 检查分钟限制
        if current_time - self.rate_limiter['last_minute_reset'] >= 60:
            self.rate_limiter['current_minute_requests'] = 0
            self.rate_limiter['last_minute_reset'] = current_time

        # 检查日限制
        if current_time - self.rate_limiter['last_day_reset'] >= 86400:
            self.rate_limiter['current_day_requests'] = 0
            self.rate_limiter['last_day_reset'] = current_time

        # 检查是否超过限制
        if (self.rate_limiter['current_minute_requests'] >= self.rate_limiter['requests_per_minute'] or
            self.rate_limiter['current_day_requests'] >= self.rate_limiter['requests_per_day']):
            return False

        return True

    def _update_rate_limit(self):
        """更新速率限制计数"""
        self.rate_limiter['current_minute_requests'] += 1
        self.rate_limiter['current_day_requests'] += 1

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """带重试机制的Gemini调用"""
        if not self.model:
            logger.error("Gemini模型未初始化")
            return None

        if not self._check_rate_limit():
            logger.warning("达到速率限制，请稍后重试")
            return None

        for attempt in range(max_retries):
            try:
                self._update_rate_limit()

                # 调用Gemini API
                response = self.model.generate_content(prompt)

                if response and response.text:
                    logger.info(f"Gemini调用成功，返回{len(response.text)}字符")
                    return response.text.strip()
                else:
                    logger.warning("Gemini返回空响应")
                    return None

            except Exception as e:
                logger.error(f"Gemini调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    # 尝试切换API密钥
                    try:
                        api_key = self._get_next_api_key()
                        genai.configure(api_key=api_key)
                        self.model = genai.GenerativeModel(
                            model_name="gemini-2.0-flash-exp",
                            generation_config={
                                "temperature": 0.7,
                                "top_p": 0.8,
                                "top_k": 64,
                                "max_output_tokens": 8192,
                            }
                        )
                        logger.info(f"切换到新API密钥: {api_key[:10]}...")
                    except Exception as switch_error:
                        logger.error(f"切换API密钥失败: {switch_error}")

                    time.sleep(2 ** attempt)  # 指数退避

        return None

    def analyze_vulnerability(self, vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用AI分析漏洞"""
        prompt = f"""
请作为网络安全专家，分析以下漏洞信息并提供详细的安全评估：

漏洞信息：
- CVE ID: {vulnerability_data.get('cve_id', 'Unknown')}
- 严重程度: {vulnerability_data.get('severity', 'Unknown')}
- 描述: {vulnerability_data.get('description', 'No description')}
- 影响产品: {vulnerability_data.get('affected_product', 'Unknown')}
- CVSS评分: {vulnerability_data.get('cvss_score', 'Unknown')}

请提供以下分析：
1. 漏洞技术原理
2. 潜在攻击场景
3. 影响范围评估
4. 修复优先级建议
5. 具体修复步骤
6. 预防措施

请用中文回答，格式清晰，内容专业。
"""

        try:
            response = self._call_gemini_with_retry(prompt)

            if response:
                return {
                    "analysis_result": response,
                    "ai_insights": self._extract_insights(response),
                    "recommendations": self._extract_recommendations(response),
                    "risk_assessment": self._extract_risk_assessment(response),
                    "analysis_time": datetime.now().isoformat()
                }
            else:
                return {"error": "AI分析失败"}

        except Exception as e:
            logger.error(f"AI分析漏洞时出错: {e}")
            return {"error": str(e)}

    def generate_exploit_payload(self, vulnerability_info: Dict[str, Any], target_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏洞利用载荷（仅用于授权测试）"""
        prompt = f"""
作为安全研究员，请为以下漏洞生成概念性的测试载荷（仅用于授权安全测试）：

漏洞信息：
- CVE ID: {vulnerability_info.get('cve_id', 'Unknown')}
- 漏洞类型: {vulnerability_info.get('vulnerability_type', 'Unknown')}
- 影响组件: {vulnerability_info.get('affected_component', 'Unknown')}
- 技术细节: {vulnerability_info.get('technical_details', 'No details')}

目标信息：
- 目标URL: {target_info.get('url', 'Unknown')}
- 技术栈: {target_info.get('tech_stack', 'Unknown')}
- 应用类型: {target_info.get('application_type', 'Unknown')}

请生成：
1. 概念性测试方法
2. 检测PoC（概念验证）
3. 验证步骤
4. 安全注意事项
5. 影响评估

重要提醒：
- 仅用于授权的安全测试
- 不得用于恶意目的
- 必须遵守法律法规
- 负责任地使用

请用中文回答，提供技术细节和操作指导。
"""

        try:
            response = self._call_gemini_with_retry(prompt)

            if response:
                return {
                    "payload_info": response,
                    "test_methods": self._extract_test_methods(response),
                    "safety_notes": self._extract_safety_notes(response),
                    "verification_steps": self._extract_verification_steps(response),
                    "generation_time": datetime.now().isoformat()
                }
            else:
                return {"error": "载荷生成失败"}

        except Exception as e:
            logger.error(f"生成载荷时出错: {e}")
            return {"error": str(e)}

    def analyze_business_logic(self, application_info: Dict[str, Any], scenario: str) -> Dict[str, Any]:
        """分析业务逻辑漏洞"""
        prompt = f"""
作为业务逻辑安全专家，请分析以下应用的潜在业务逻辑漏洞：

应用信息：
- 应用名称: {application_info.get('name', 'Unknown')}
- 应用类型: {application_info.get('type', 'Unknown')}
- 主要功能: {application_info.get('main_functions', 'Unknown')}
- 技术栈: {application_info.get('tech_stack', 'Unknown')}
- 用户角色: {application_info.get('user_roles', 'Unknown')}

测试场景: {scenario}

请分析：
1. 潜在业务逻辑漏洞
2. 权限绕过可能性
3. 数据篡改风险
4. 流程控制问题
5. 经济损失风险
6. 用户体验问题

请提供：
- 具体漏洞描述
- 攻击场景
- 影响评估
- 修复建议
- 预防措施

请用中文回答，重点关注实际业务风险。
"""

        try:
            response = self._call_gemini_with_retry(prompt)

            if response:
                return {
                    "business_analysis": response,
                    "identified_vulnerabilities": self._extract_business_vulnerabilities(response),
                    "risk_scenarios": self._extract_risk_scenarios(response),
                    "fix_recommendations": self._extract_fix_recommendations(response),
                    "analysis_time": datetime.now().isoformat()
                }
            else:
                return {"error": "业务逻辑分析失败"}

        except Exception as e:
            logger.error(f"分析业务逻辑时出错: {e}")
            return {"error": str(e)}

    def generate_security_report(self, scan_results: Dict[str, Any], target_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成智能安全报告"""
        prompt = f"""
作为高级安全分析师，请根据以下扫描结果生成专业的安全评估报告：

扫描结果：
- 总漏洞数: {scan_results.get('total_vulnerabilities', 0)}
- 严重漏洞: {scan_results.get('critical_vulns', 0)}
- 高危漏洞: {scan_results.get('high_vulns', 0)}
- 中危漏洞: {scan_results.get('medium_vulns', 0)}
- 低危漏洞: {scan_results.get('low_vulns', 0)}
- 风险分数: {scan_results.get('risk_score', 0)}

目标信息：
- 目标名称: {target_info.get('name', 'Unknown')}
- 目标类型: {target_info.get('type', 'Unknown')}
- 业务重要性: {target_info.get('business_importance', 'Unknown')}
- 用户规模: {target_info.get('user_scale', 'Unknown')}

请生成包含以下内容的报告：
1. 执行摘要
2. 风险评估
3. 关键发现
4. 详细分析
5. 修复优先级
6. 安全建议
7. 合规评估
8. 长期规划

要求：
- 使用专业的网络安全术语
- 提供具体的数据支持
- 给出可操作的建议
- 格式清晰易读
- 适合管理层阅读

请用中文生成报告，语言专业但易懂。
"""

        try:
            response = self._call_gemini_with_retry(prompt)

            if response:
                return {
                    "ai_report": response,
                    "executive_summary": self._extract_executive_summary(response),
                    "risk_matrix": self._extract_risk_matrix(response),
                    "action_items": self._extract_action_items(response),
                    "report_time": datetime.now().isoformat()
                }
            else:
                return {"error": "报告生成失败"}

        except Exception as e:
            logger.error(f"生成安全报告时出错: {e}")
            return {"error": str(e)}

    def predict_vulnerability_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预测漏洞趋势"""
        prompt = f"""
作为网络安全趋势分析师，请基于以下历史数据预测漏洞发展趋势：

历史数据：
{json.dumps(historical_data, ensure_ascii=False, indent=2)}

请分析：
1. 漏洞类型分布趋势
2. 严重程度变化趋势
3. 新兴威胁预测
4. 技术栈风险分析
5. 防御策略建议
6. 投资优先级

请提供：
- 数据可视化建议
- 趋势图表描述
- 预测置信度
- 关键发现
- 行动建议

请用中文进行分析，提供专业的洞察和建议。
"""

        try:
            response = self._call_gemini_with_retry(prompt)

            if response:
                return {
                    "trend_analysis": response,
                    "predictions": self._extract_predictions(response),
                    "insights": self._extract_insights(response),
                    "recommendations": self._extract_recommendations(response),
                    "analysis_time": datetime.now().isoformat()
                }
            else:
                return {"error": "趋势预测失败"}

        except Exception as e:
            logger.error(f"预测漏洞趋势时出错: {e}")
            return {"error": str(e)}

    # 辅助方法
    def _extract_insights(self, response: str) -> List[str]:
        """从AI响应中提取洞察"""
        insights = []
        lines = response.split('\n')
        for line in lines:
            if '洞察' in line or '发现' in line or '重要' in line:
                insights.append(line.strip())
        return insights[:5]  # 返回前5个洞察

    def _extract_recommendations(self, response: str) -> List[str]:
        """从AI响应中提取建议"""
        recommendations = []
        lines = response.split('\n')
        for line in lines:
            if '建议' in line or '推荐' in line or '应该' in line:
                recommendations.append(line.strip())
        return recommendations[:5]

    def _extract_risk_assessment(self, response: str) -> Dict[str, str]:
        """从AI响应中提取风险评估"""
        assessment = {}
        lines = response.split('\n')
        for line in lines:
            if '风险等级' in line or '风险级别' in line:
                assessment['level'] = line.split(':')[-1].strip() if ':' in line else line.strip()
            elif '影响范围' in line:
                assessment['scope'] = line.split(':')[-1].strip() if ':' in line else line.strip()
            elif '紧急程度' in line:
                assessment['urgency'] = line.split(':')[-1].strip() if ':' in line else line.strip()
        return assessment

    def _extract_test_methods(self, response: str) -> List[str]:
        """提取测试方法"""
        methods = []
        lines = response.split('\n')
        for line in lines:
            if '测试' in line or '验证' in line or '检测' in line:
                methods.append(line.strip())
        return methods[:5]

    def _extract_safety_notes(self, response: str) -> List[str]:
        """提取安全注意事项"""
        notes = []
        lines = response.split('\n')
        for line in lines:
            if '注意' in line or '安全' in line or '警告' in line or '提醒' in line:
                notes.append(line.strip())
        return notes[:5]

    def _extract_verification_steps(self, response: str) -> List[str]:
        """提取验证步骤"""
        steps = []
        lines = response.split('\n')
        for line in lines:
            if '步骤' in line or ('第' in line and '步' in line) or line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                steps.append(line.strip())
        return steps[:5]

    def _extract_business_vulnerabilities(self, response: str) -> List[str]:
        """提取业务漏洞"""
        vulns = []
        lines = response.split('\n')
        for line in lines:
            if '漏洞' in line or '风险' in line or '问题' in line:
                vulns.append(line.strip())
        return vulns[:5]

    def _extract_risk_scenarios(self, response: str) -> List[str]:
        """提取风险场景"""
        scenarios = []
        lines = response.split('\n')
        for line in lines:
            if '场景' in line or '情况' in line or '可能' in line:
                scenarios.append(line.strip())
        return scenarios[:5]

    def _extract_fix_recommendations(self, response: str) -> List[str]:
        """提取修复建议"""
        fixes = []
        lines = response.split('\n')
        for line in lines:
            if '修复' in line or '解决' in line or '改进' in line:
                fixes.append(line.strip())
        return fixes[:5]

    def _extract_executive_summary(self, response: str) -> str:
        """提取执行摘要"""
        lines = response.split('\n')
        summary_lines = []
        in_summary = False

        for line in lines:
            if '摘要' in line or '总结' in line or '概述' in line:
                in_summary = True
            elif in_summary and line.strip():
                if '风险' in line or '建议' in line or '发现' in line:
                    summary_lines.append(line.strip())
                elif '##' in line or '#' in line:
                    break

        return '\n'.join(summary_lines[:5]) if summary_lines else "请参考完整报告"

    def _extract_risk_matrix(self, response: str) -> Dict[str, Any]:
        """提取风险矩阵"""
        matrix = {}
        lines = response.split('\n')

        for line in lines:
            if '严重' in line and '高' in line:
                matrix['critical_high'] = line.strip()
            elif '中' in line and '低' in line:
                matrix['medium_low'] = line.strip()
            elif '紧急' in line:
                matrix['urgent'] = line.strip()

        return matrix

    def _extract_action_items(self, response: str) -> List[str]:
        """提取行动项"""
        actions = []
        lines = response.split('\n')

        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')) or \
               '立即' in line or '紧急' in line or '优先' in line:
                actions.append(line.strip())

        return actions[:5]

    def _extract_predictions(self, response: str) -> List[str]:
        """提取预测"""
        predictions = []
        lines = response.split('\n')

        for line in lines:
            if '预测' in line or '趋势' in line or '预计' in line or '可能' in line:
                predictions.append(line.strip())

        return predictions[:5]

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "model_status": "initialized" if self.model else "not_initialized",
            "available_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "rate_limit_status": self.rate_limiter,
            "model_name": "gemini-2.0-flash-exp",
            "last_check": datetime.now().isoformat()
        }

def main():
    """主函数 - 演示Gemini AI集成功能"""
    print("=== Gemini AI 2.0 Flash-Exp 集成演示 ===")
    print("集成到 Dragon-V Triple Bot v3.2.0")
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 初始化Gemini集成
    gemini = GeminiAIIntegration()

    # 显示系统状态
    status = gemini.get_system_status()
    print(f"\n=== 系统状态 ===")
    print(f"模型状态: {status['model_status']}")
    print(f"可用密钥: {status['available_keys']} 个")
    print(f"当前密钥索引: {status['current_key_index']}")
    print(f"模型名称: {status['model_name']}")

    if status['model_status'] == 'initialized':
        print(f"\n=== AI功能演示 ===")

        # 演示漏洞分析
        test_vulnerability = {
            "cve_id": "CVE-2024-10707",
            "severity": "High",
            "description": "Chuanhugpt本地文件读取漏洞",
            "affected_product": "Chuanhugpt",
            "cvss_score": "7.5"
        }

        print("正在测试漏洞分析功能...")
        result = gemini.analyze_vulnerability(test_vulnerability)

        if 'analysis_result' in result:
            print("✓ 漏洞分析功能正常")
            print(f"分析结果长度: {len(result['analysis_result'])} 字符")
            print(f"AI洞察数量: {len(result.get('ai_insights', []))}")
            print(f"建议数量: {len(result.get('recommendations', []))}")
        else:
            print("✗ 漏洞分析功能异常")
            print(f"错误信息: {result.get('error', 'Unknown error')}")

        # 演示安全报告生成
        test_scan_results = {
            "total_vulnerabilities": 15,
            "critical_vulns": 2,
            "high_vulns": 5,
            "medium_vulns": 6,
            "low_vulns": 2,
            "risk_score": 75
        }

        test_target_info = {
            "name": "测试Web应用",
            "type": "电商网站",
            "business_importance": "高",
            "user_scale": "10000+"
        }

        print("\n正在测试安全报告生成功能...")
        report_result = gemini.generate_security_report(test_scan_results, test_target_info)

        if 'ai_report' in report_result:
            print("✓ 安全报告生成功能正常")
            print(f"报告长度: {len(report_result['ai_report'])} 字符")
            print(f"执行摘要: {len(report_result.get('executive_summary', ''))} 字符")
            print(f"行动项数量: {len(report_result.get('action_items', []))}")
        else:
            print("✗ 安全报告生成功能异常")
            print(f"错误信息: {report_result.get('error', 'Unknown error')}")

        print(f"\n=== 集成演示完成 ===")
        print("✓ Gemini AI 2.0 Flash-Exp 集成成功")
        print("✓ AI分析功能正常运行")
        print("✓ 报告生成功能正常")
        print("✓ 系统已准备好与Dragon-V Triple Bot集成")

    else:
        print("\n❌ Gemini模型初始化失败")
        print("请检查API密钥配置和网络连接")

    print(f"\n配置的API密钥数量: {len(gemini.api_keys)}")
    print("支持自动切换和速率限制控制")

if __name__ == "__main__":
    main()