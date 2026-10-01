#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南系统指纹识别器
Vietnam System Fingerprint Recognizer

专门用于识别越南快递、物流、商城、订单系统的指纹识别工具
支持识别:
- 越南快递公司 (VNPost, Viettel Post, Giao Hang Nhanh, J&T Express Vietnam)
- 越南电商平台 (Shopee VN, Lazada VN, Tiki, Sendo, Nguyen Kim)
- 越南物流系统 (Viettel Post Logistics, GHTK, Ahamove)
- 越南支付系统 (MoMo, ZaloPay, VNPay)
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from bs4 import BeautifulSoup
import hashlib

class SystemCategory(Enum):
    """系统分类"""
    EXPRESS_DELIVERY = "express_delivery"
    ECOMMERCE = "ecommerce"
    LOGISTICS = "logistics"
    PAYMENT = "payment"
    GOVERNMENT = "government"

@dataclass
class VietnamSystemFingerprint:
    """越南系统指纹"""
    system_name: str
    category: SystemCategory
    confidence: float
    url_patterns: List[str]
    html_signatures: List[str]
    js_signatures: List[str]
    api_signatures: List[str]
    vietnam_specific: bool
    description: str
    common_vulnerabilities: List[str]

class VietnamFingerprintRecognizer:
    """越南系统指纹识别器"""

    def __init__(self):
        self.fingerprints = self._load_vietnam_fingerprints()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _load_vietnam_fingerprints(self) -> Dict[str, VietnamSystemFingerprint]:
        """加载越南系统指纹库"""
        return {
            # 越南快递公司
            "vnpost": VietnamSystemFingerprint(
                system_name="VNPost - Vietnam Post",
                category=SystemCategory.EXPRESS_DELIVERY,
                confidence=0.95,
                url_patterns=[
                    r"vnpost\.vn",
                    r"buudien\.vn",
                    r"vietnam-post\.vn",
                    r"post\.vn"
                ],
                html_signatures=[
                    r"Bưu điện Việt Nam",
                    r"VNPost",
                    r"Vietnam Post",
                    r"Công ty TNHH MTV Bưu điện"
                ],
                js_signatures=[
                    r"vnpost\.js",
                    r"buudien",
                    r"vietnamPost"
                ],
                api_signatures=[
                    r"/api/v2/tracking",
                    r"/api/shipment",
                    r"/tracking/.*"
                ],
                vietnam_specific=True,
                description="越南国家邮政公司，最大的快递服务提供商",
                common_vulnerabilities=[
                    "SQL注入 - 跟踪系统",
                    "XSS - 客户信息页面",
                    "认证绕过 - 管理后台",
                    "订单信息泄露"
                ]
            ),

            "viettel_post": VietnamSystemFingerprint(
                system_name="Viettel Post",
                category=SystemCategory.EXPRESS_DELIVERY,
                confidence=0.93,
                url_patterns=[
                    r"viettelpost\.vn",
                    r"vtp\.vn",
                    r"viettel-post\.vn"
                ],
                html_signatures=[
                    r"Viettel Post",
                    r"VTP",
                    r"Tập đoàn Công nghiệp - Viễn thông Quân đội"
                ],
                js_signatures=[
                    r"viettelpost",
                    r"vtp\.js",
                    r"trackingVTP"
                ],
                api_signatures=[
                    r"/api/tracking",
                    r"/v2/tracking",
                    r"/order/tracking"
                ],
                vietnam_specific=True,
                description="越南电信集团旗下快递服务",
                common_vulnerabilities=[
                    "API未授权访问",
                    "跟踪信息篡改",
                    "用户数据泄露",
                    "支付绕过"
                ]
            ),

            "giaohangnhanh": VietnamSystemFingerprint(
                system_name="Giao Hàng Nhanh",
                category=SystemCategory.EXPRESS_DELIVERY,
                confidence=0.91,
                url_patterns=[
                    r"giaohangnhanh\.vn",
                    r"ghn\.vn",
                    r"giaohangnhanh\.com"
                ],
                html_signatures=[
                    r"Giao Hàng Nhanh",
                    r"GHN",
                    r"Giao Hàng Nhanh JSC"
                ],
                js_signatures=[
                    r"ghn",
                    r"giaohangnhanh",
                    r"tracking-ghn"
                ],
                api_signatures=[
                    r"/api/v1/tracking",
                    r"/api/shipment",
                    r"/public/tracking"
                ],
                vietnam_specific=True,
                description="越南快速配送服务，专注于电商配送",
                common_vulnerabilities=[
                    "订单状态篡改",
                    "Shop后台漏洞",
                    "API速率限制绕过",
                    "配送信息泄露"
                ]
            ),

            "ghtk": VietnamSystemFingerprint(
                system_name="Giao Hàng Tiết Kiệm",
                category=SystemCategory.EXPRESS_DELIVERY,
                confidence=0.89,
                url_patterns=[
                    r"ghtk\.vn",
                    r"giaohangtietkiem\.vn",
                    r"donhang\.ghtk\.vn"
                ],
                html_signatures=[
                    r"Giao Hàng Tiết Kiệm",
                    r"GHTK",
                    r"Tiết Kiệm"
                ],
                js_signatures=[
                    r"ghtk",
                    r"giao-hang-tiet-kiem"
                ],
                api_signatures=[
                    r"/api/portal",
                    r"/services/shipment",
                    r"/tracking"
                ],
                vietnam_specific=True,
                description="越南经济型配送服务",
                common_vulnerabilities=[
                    "Portal注入",
                    "商户数据泄露",
                    "运费计算漏洞",
                    "批量订单操作"
                ]
            ),

            # 越南电商平台
            "shopee_vn": VietnamSystemFingerprint(
                system_name="Shopee Vietnam",
                category=SystemCategory.ECOMMERCE,
                confidence=0.96,
                url_patterns=[
                    r"shopee\.vn",
                    r"shopee.*\.vn"
                ],
                html_signatures=[
                    r"Shopee Việt Nam",
                    r"Shopee VN",
                    r"Mua sắm và bán hàng online"
                ],
                js_signatures=[
                    r"shopee",
                    r"__NEXT_DATA__",
                    r"shoppee"
                ],
                api_signatures=[
                    r"/api/v4",
                    r"/api/v2",
                    r"/cart",
                    r"/checkout"
                ],
                vietnam_specific=True,
                description="东南亚电商巨头Shopee的越南分支",
                common_vulnerabilities=[
                    "API Rate Limit绕过",
                    "价格操纵",
                    "优惠券滥用",
                    "账户接管"
                ]
            ),

            "lazada_vn": VietnamSystemFingerprint(
                system_name="Lazada Vietnam",
                category=SystemCategory.ECOMMERCE,
                confidence=0.94,
                url_patterns=[
                    r"lazada\.vn",
                    r"lazada.*\.vn"
                ],
                html_signatures=[
                    r"Lazada Việt Nam",
                    r"Lazada VN",
                    r"Mua sắm online giá tốt"
                ],
                js_signatures=[
                    r"lazada",
                    r"lzd-global",
                    r"main-lazada"
                ],
                api_signatures=[
                    r"/api",
                    r"/product",
                    r"/cart"
                ],
                vietnam_specific=True,
                description="阿里巴巴旗下电商平台的越南分支",
                common_vulnerabilities=[
                    "Magento漏洞",
                    "支付网关绕过",
                    "产品数据泄露",
                    "用户会话劫持"
                ]
            ),

            "tiki": VietnamSystemFingerprint(
                system_name="Tiki",
                category=SystemCategory.ECOMMERCE,
                confidence=0.92,
                url_patterns=[
                    r"tiki\.vn",
                    r"tiki.*\.vn"
                ],
                html_signatures=[
                    r"Tiki",
                    r"Mua sắm online tại Tiki",
                    r"Tiki Trading"
                ],
                js_signatures=[
                    r"tiki",
                    r"tiki-",
                    r"tiki.vn"
                ],
                api_signatures=[
                    r"/api/v2",
                    r"/api/personal",
                    r"/graphql"
                ],
                vietnam_specific=True,
                description="越南本土电商平台，以快速配送著称",
                common_vulnerabilities=[
                    "GraphQL注入",
                    "TikiNow特权绕过",
                    "订单信息泄露",
                    "支付验证绕过"
                ]
            ),

            "sendo": VietnamSystemFingerprint(
                system_name="Sendo",
                category=SystemCategory.ECOMMERCE,
                confidence=0.88,
                url_patterns=[
                    r"sendo\.vn",
                    r"sendo.*\.vn"
                ],
                html_signatures=[
                    r"Sendo",
                    r"Mua sắm online Sendo",
                    r"Sendome"
                ],
                js_signatures=[
                    r"sendo",
                    r"sd-",
                    r"sendo.vn"
                ],
                api_signatures=[
                    r"/api",
                    r"/web-api",
                    r"/product"
                ],
                vietnam_specific=True,
                description="越南本土电商平台",
                common_vulnerabilities=[
                    "商品库存操纵",
                    "商户后台漏洞",
                    "优惠券堆叠",
                    "支付状态篡改"
                ]
            ),

            # 越南支付系统
            "momo": VietnamSystemFingerprint(
                system_name="MoMo Wallet",
                category=SystemCategory.PAYMENT,
                confidence=0.95,
                url_patterns=[
                    r"momo\.vn",
                    r"m-.*\.vn"
                ],
                html_signatures=[
                    r"Ví MoMo",
                    r"MoMo",
                    r"Thanh toán MoMo"
                ],
                js_signatures=[
                    r"momo",
                    r"web-sdk",
                    r"momo-"
                ],
                api_signatures=[
                    r"/api/",
                    r"/payment/",
                    r"/app/"
                ],
                vietnam_specific=True,
                description="越南最大的电子钱包",
                common_vulnerabilities=[
                    "支付绕过",
                    "余额篡改",
                    "交易记录泄露",
                    "API未授权访问"
                ]
            ),

            "zalopay": VietnamSystemFingerprint(
                system_name="ZaloPay",
                category=SystemCategory.PAYMENT,
                confidence=0.91,
                url_patterns=[
                    r"zalopay\.vn",
                    r"zalo.*\.vn"
                ],
                html_signatures=[
                    r"ZaloPay",
                    r"Thanh toán ZaloPay",
                    r"Ví điện tử ZaloPay"
                ],
                js_signatures=[
                    r"zalopay",
                    r"zlp-",
                    r"zalo-pay"
                ],
                api_signatures=[
                    r"/api/",
                    r"/payment/",
                    r"/qr/"
                ],
                vietnam_specific=True,
                description="Zalo旗下支付平台",
                common_vulnerabilities=[
                    "QR码伪造",
                    "支付验证绕过",
                    "用户数据泄露",
                    "交易重放攻击"
                ]
            ),

            "vnpay": VietnamSystemFingerprint(
                system_name="VNPay",
                category=SystemCategory.PAYMENT,
                confidence=0.90,
                url_patterns=[
                    r"vnpay\.vn",
                    r"vnpay.*\.vn"
                ],
                html_signatures=[
                    r"VNPay",
                    r"Cổng thanh toán VNPay",
                    r"VNPAY"
                ],
                js_signatures=[
                    r"vnpay",
                    r"vnp",
                    r"vnpay-"
                ],
                api_signatures=[
                    r"/api/",
                    r"/paymentv2",
                    r"/querydr"
                ],
                vietnam_specific=True,
                description="越南主流支付网关",
                common_vulnerabilities=[
                    "支付签名绕过",
                    "订单状态篡改",
                    "返款漏洞",
                    "商户信息泄露"
                ]
            )
        }

    def identify_system(self, url: str) -> Optional[VietnamSystemFingerprint]:
        """识别越南系统"""
        try:
            response = self.session.get(url, timeout=10)
            content = response.text
            soup = BeautifulSoup(content, 'html.parser')

            # 提取页面内容
            title = soup.title.string if soup.title else ""
            meta_description = ""
            if soup.find("meta", attrs={"name": "description"}):
                meta_description = soup.find("meta", attrs={"name": "description"}).get("content", "")

            page_content = f"{url} {title} {meta_description} {content}".lower()

            # 匹配指纹
            best_match = None
            highest_confidence = 0

            for system_name, fingerprint in self.fingerprints.items():
                confidence = self._calculate_confidence(page_content, fingerprint, url)
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = fingerprint

            if best_match and highest_confidence > 0.7:
                best_match.confidence = highest_confidence
                return best_match

        except Exception as e:
            print(f"识别失败 {url}: {e}")

        return None

    def _calculate_confidence(self, content: str, fingerprint: VietnamSystemFingerprint, url: str) -> float:
        """计算匹配置信度"""
        confidence = 0

        # URL匹配
        for pattern in fingerprint.url_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                confidence += 0.4
                break

        # HTML签名匹配
        html_matches = sum(1 for pattern in fingerprint.html_signatures
                          if re.search(pattern, content, re.IGNORECASE))
        if html_matches > 0:
            confidence += 0.3 * (html_matches / len(fingerprint.html_signatures))

        # JavaScript签名匹配
        js_matches = sum(1 for pattern in fingerprint.js_signatures
                        if re.search(pattern, content, re.IGNORECASE))
        if js_matches > 0:
            confidence += 0.2 * (js_matches / len(fingerprint.js_signatures))

        # API签名匹配
        api_matches = sum(1 for pattern in fingerprint.api_signatures
                         if re.search(pattern, content, re.IGNORECASE))
        if api_matches > 0:
            confidence += 0.1 * (api_matches / len(fingerprint.api_signatures))

        return min(confidence, 1.0)

    def get_vulnerability_recommendations(self, fingerprint: VietnamSystemFingerprint) -> List[str]:
        """获取漏洞利用建议"""
        recommendations = []

        for vuln in fingerprint.common_vulnerabilities:
            if "SQL注入" in vuln:
                recommendations.append(f"🔍 {vuln}: 测试跟踪系统、搜索功能的SQL注入点")
            elif "XSS" in vuln:
                recommendations.append(f"🔍 {vuln}: 检查用户输入、评论、反馈表单")
            elif "认证绕过" in vuln:
                recommendations.append(f"🔍 {vuln}: 尝试默认密码、弱口令、会话劫持")
            elif "API未授权" in vuln:
                recommendations.append(f"🔍 {vuln}: 枚举API端点，测试访问控制")
            elif "支付绕过" in vuln:
                recommendations.append(f"🔍 {vuln}: 检查支付流程、金额篡改、状态修改")
            elif "数据泄露" in vuln:
                recommendations.append(f"🔍 {vuln}: 寻找未保护的端点、目录遍历")
            else:
                recommendations.append(f"🔍 {vuln}: 专门针对{fingerprint.system_name}的测试")

        return recommendations

    def generate_fingerprint_report(self, url: str) -> str:
        """生成指纹识别报告"""
        fingerprint = self.identify_system(url)

        if not fingerprint:
            report = {
                "status": "未识别到越南系统",
                "url": url,
                "suggestion": "请确认目标是否为越南快递、物流、电商或支付系统",
                "alternatives": [
                    "检查URL是否正确",
                    "确认网站是否为越南系统",
                    "尝试不同的页面路径"
                ]
            }
        else:
            recommendations = self.get_vulnerability_recommendations(fingerprint)

            report = {
                "status": "识别成功",
                "url": url,
                "system_info": {
                    "name": fingerprint.system_name,
                    "category": fingerprint.category.value,
                    "confidence": f"{fingerprint.confidence:.2%}",
                    "vietnam_specific": fingerprint.vietnam_specific,
                    "description": fingerprint.description
                },
                "vulnerability_recommendations": recommendations,
                "testing_priority": "高" if fingerprint.confidence > 0.9 else "中" if fingerprint.confidence > 0.8 else "低",
                "next_steps": [
                    "进行详细的漏洞扫描",
                    "测试业务逻辑漏洞",
                    "验证安全控制措施",
                    "生成渗透测试报告"
                ]
            }

        return json.dumps(report, ensure_ascii=False, indent=2)

# 主程序入口
if __name__ == "__main__":
    def main():
        print("🇻🇳 越南系统指纹识别器")
        print("🎯 专门识别越南快递、物流、电商、支付系统")
        print("=" * 50)

        recognizer = VietnamFingerprintRecognizer()

        # 测试URL列表
        test_urls = [
            "https://shopee.vn",
            "https://vnpost.vn",
            "https://lazada.vn",
            "https://momo.vn",
            "https://tiki.vn"
        ]

        for url in test_urls:
            print(f"\n🔍 识别: {url}")
            fingerprint = recognizer.identify_system(url)

            if fingerprint:
                print(f"✅ 识别成功: {fingerprint.system_name}")
                print(f"📊 类别: {fingerprint.category.value}")
                print(f"🎯 置信度: {fingerprint.confidence:.2%}")
                print(f"🇻🇳 越南特色: {'是' if fingerprint.vietnam_specific else '否'}")
                print(f"📝 描述: {fingerprint.description}")

                recommendations = recognizer.get_vulnerability_recommendations(fingerprint)
                print("🔍 建议测试:")
                for rec in recommendations[:3]:  # 显示前3个建议
                    print(f"   • {rec}")
            else:
                print("❌ 未识别到越南系统")

            # 生成详细报告
            report = recognizer.generate_fingerprint_report(url)
            print(f"📋 详细报告已生成")

    main()