#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南化扫描系统增强模块
Vietnam Localization Enhancement for Dragon-V Triple Bot v3.2.0

专门针对越南快递物流站点的扫描能力增强
"""

import re
import requests
import yaml
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vietnam_localization.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VietnamLocalizationEnhancement:
    """越南化扫描增强系统"""

    def __init__(self):
        self.vietnam_keywords = self._load_vietnam_keywords()
        self.logistics_patterns = self._load_logistics_patterns()
        self.vietnam_fingerprints = self._load_vietnam_fingerprints()
        self.payment_systems = self._load_payment_systems()

    def _load_vietnam_keywords(self) -> Dict[str, List[str]]:
        """加载越南语关键词"""
        return {
            "物流相关": [
                "giao hàng", "vận chuyển", "phát nhanh", "vận đơn", "theo dõi",
                "đơn hàng", "chuyển phát", "logistics", "giao nhận", "phân phối",
                "kho hàng", "xuất kho", "nhập kho", "tồn kho", "đơn vị vận chuyển"
            ],

            "快递服务": [
                "thời gian giao hàng", "phí vận chuyển", "giao hàng nhanh", "giao hàng tiết kiệm",
                "giao hàng hỏa tốc", "giao hàng trong ngày", "giao hàng liên tỉnh",
                "giao hàng nội thành", "giao hàng quốc tế", "dịch vụ giao hàng"
            ],

            "订单管理": [
                "quản lý đơn hàng", "trạng thái đơn hàng", "lịch sử đơn hàng",
                "chi tiết đơn hàng", "thanh toán đơn hàng", "hủy đơn hàng",
                "đổi trả hàng", "hoàn tiền", "khách hàng", "người nhận"
            ],

            "支付相关": [
                "thanh toán", "thanh toán online", "thanh toán khi nhận hàng",
                "thanh toán qua ví", "chuyển khoản", "thẻ tín dụng",
                "MoMo", "ZaloPay", "ViettelPay", "VNPay", "tiền mặt"
            ],

            "技术术语": [
                "API", "web", "hệ thống", "ứng dụng", "di động", "platform",
                "tracking", "mã vận đơn", "mã bưu chính", "barcode", "QR code"
            ]
        }

    def _load_logistics_patterns(self) -> Dict[str, str]:
        """加载物流网站模式识别"""
        return {
            "url_patterns": [
                r".*\.vn$",
                r".*ghn.*",
                r".*ghtk.*",
                r".*viettelpost.*",
                r".*vnpost.*",
                r".*jntexpress.*",
                r".*giaohang.*",
                r".*vanchuyen.*",
                r".*phatnhanh.*"
            ],

            "title_patterns": [
                r".*[Gg]iao *[Hh]àng.*",
                r".*[Vv]ận *[Cc]uyển.*",
                r".*[Đđ]ơn *[Hh]àng.*",
                r".*[Tt]heo *[Đd]õi.*",
                r".*[Ll]ogistics.*",
                r".*[Cc]huyển *[Pp]hát.*"
            ],

            "content_patterns": [
                r"Mã vận đơn",
                r"Mã đơn hàng",
                r"Trạng thái đơn hàng",
                r"Theo dõi đơn hàng",
                r"Giao hàng thành công",
                r"Đang giao hàng",
                r"Chờ giao hàng"
            ]
        }

    def _load_vietnam_fingerprints(self) -> Dict[str, Any]:
        """加载越南应用指纹"""
        return {
            "支付系统": {
                "MoMo": {
                    "patterns": [r"momo", r"MoMo", r"MOMO"],
                    "indicators": ["payment.momo.vn", "app.momo.vn"]
                },
                "ZaloPay": {
                    "patterns": [r"zalopay", r"ZaloPay", r"ZALOPAY"],
                    "indicators": ["zalopay.vn", "api.zalopay.vn"]
                },
                "ViettelPay": {
                    "patterns": [r"viettelpay", r"ViettelPay", r"VIETTEL PAY"],
                    "indicators": ["viettelpay.vn", "pay.viettel.vn"]
                },
                "VNPay": {
                    "patterns": [r"vnpay", r"VNPay", r"VNPAY"],
                    "indicators": ["vnpay.vn", "api.vnpay.vn"]
                }
            },

            "地图服务": {
                "Google Maps Vietnam": {
                    "patterns": [r"googleapis\.com/maps", r"maps\.googleapis\.com"],
                    "indicators": ["Google Maps", "Vietnam"]
                },
                "Vietmap": {
                    "patterns": [r"vietmap", r"Vietmap", r"VIETMAP"],
                    "indicators": ["vietmap.vn", "api.vietmap.vn"]
                }
            },

            "云服务": {
                "Viettel Cloud": {
                    "patterns": [r"viettelcloud", r"Viettel Cloud"],
                    "indicators": ["viettelcloud.vn", "cloud.viettel.vn"]
                },
                "FPT Cloud": {
                    "patterns": [r"fptcloud", r"FPT Cloud"],
                    "indicators": ["fptcloud.com", "cloud.fpt.com.vn"]
                }
            }
        }

    def _load_payment_systems(self) -> List[str]:
        """加载越南支付系统"""
        return [
            "MoMo", "ZaloPay", "ViettelPay", "VNPay",
            "Ngân Lượng VR", "Bảo Kim", "OnePay",
            "2Checkout", "Payoo", "Zion"
        ]

    def detect_vietnam_logistics_site(self, url: str, content: str = None) -> Dict[str, Any]:
        """检测是否为越南物流网站"""
        result = {
            "is_vietnam_logistics": False,
            "confidence": 0.0,
            "detected_indicators": [],
            "site_type": "unknown",
            "payment_systems": [],
            "logistics_features": []
        }

        try:
            # URL模式检测
            for pattern in self.logistics_patterns["url_patterns"]:
                if re.search(pattern, url, re.IGNORECASE):
                    result["detected_indicators"].append(f"URL匹配: {pattern}")
                    result["confidence"] += 0.3

            # 如果有内容，进行内容分析
            if content:
                content_lower = content.lower()

                # 关键词检测
                for category, keywords in self.vietnam_keywords.items():
                    found_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in content_lower:
                            found_keywords.append(keyword)

                    if found_keywords:
                        result["detected_indicators"].append(f"{category}: {', '.join(found_keywords)}")
                        result["confidence"] += 0.2
                        result["logistics_features"].extend(found_keywords)

                # 支付系统检测
                for payment in self.payment_systems:
                    if payment.lower() in content_lower:
                        result["payment_systems"].append(payment)
                        result["confidence"] += 0.1

            # 判断是否为越南物流网站
            if result["confidence"] >= 0.5:
                result["is_vietnam_logistics"] = True

                # 判断网站类型
                if "giao hàng" in " ".join(result["logistics_features"]) or "vận chuyển" in " ".join(result["logistics_features"]):
                    result["site_type"] = "logistics_platform"
                elif "đơn hàng" in " ".join(result["logistics_features"]):
                    result["site_type"] = "ecommerce_logistics"
                elif "theo dõi" in " ".join(result["logistics_features"]):
                    result["site_type"] = "tracking_system"
                else:
                    result["site_type"] = "general_logistics"

            # 限制置信度范围
            result["confidence"] = min(result["confidence"], 1.0)

        except Exception as e:
            logger.error(f"检测越南物流网站时出错: {e}")

        return result

    def analyze_vietnam_technology_stack(self, response_headers: Dict, content: str) -> Dict[str, Any]:
        """分析越南网站技术栈"""
        tech_stack = {
            "local_technologies": [],
            "payment_integrations": [],
            "local_services": [],
            "vietnam_specific_features": []
        }

        try:
            content_lower = content.lower()

            # 检测越南特定技术
            for category, systems in self.vietnam_fingerprints.items():
                for system_name, system_info in systems.items():
                    for pattern in system_info["patterns"]:
                        if re.search(pattern, content_lower, re.IGNORECASE):
                            tech_stack[category.replace("_", " ").title()].append(system_name)

                            # 检测指示器
                            for indicator in system_info.get("indicators", []):
                                if indicator.lower() in content_lower:
                                    tech_stack["local_services"].append(indicator)

            # 检测越南语内容
            vietnamese_chars = re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', content)
            if len(vietnamese_chars) > 10:  # 如果有足够多的越南语字符
                tech_stack["vietnam_specific_features"].append("Vietnamese_Language_Content")

            # 检测越南特定的业务功能
            business_patterns = {
                "Vietnamese_Address_Format": r"(số|nhà)\s+[\d\w\s]+,(phường|xã)\s+[\w\s]+,(quận|huyện)\s+[\w\s]+,(tỉnh|thành phố)\s+[\w\s]+",
                "Vietnamese_Phone_Format": r"(0|\+84)[\d]{9,10}",
                "Vietnamese_Identification": r"[0-9]{9}|[0-9]{12}",
                "Vietnam_Postal_Code": r"[0-9]{5,6}"
            }

            for feature_name, pattern in business_patterns.items():
                if re.search(pattern, content):
                    tech_stack["vietnam_specific_features"].append(feature_name)

        except Exception as e:
            logger.error(f"分析越南技术栈时出错: {e}")

        return tech_stack

    def generate_vulnerability_test_cases(self, site_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成针对越南网站的漏洞测试用例"""
        test_cases = []

        try:
            # 基础Web应用测试
            test_cases.extend([
                {
                    "name": "SQL注入测试 - 越南语输入",
                    "description": "测试越南语字符的SQL注入防护",
                    "payloads": [
                        "đơn hàng' OR '1'='1",
                        "vận chuyển\"; DROP TABLE orders;--",
                        "theo dõi' UNION SELECT * FROM users--"
                    ],
                    "severity": "High",
                    "category": "Injection"
                },
                {
                    "name": "XSS测试 - 越南语脚本",
                    "description": "测试越南语内容的XSS防护",
                    "payloads": [
                        "<script>alert('giao hàng thành công')</script>",
                        "đơn hàng<img src=x onerror=alert('vận chuyển')>",
                        "theo dõi<svg onload=alert('phát nhanh')>"
                    ],
                    "severity": "Medium",
                    "category": "XSS"
                }
            ])

            # 物流业务逻辑测试
            if site_info.get("site_type") in ["logistics_platform", "tracking_system"]:
                test_cases.extend([
                    {
                        "name": "运费操纵测试",
                        "description": "测试运费计算的业务逻辑漏洞",
                        "payloads": [
                            {"weight": "-1", "distance": "1000"},
                            {"weight": "999999", "distance": "0"},
                            {"promotion_code": "TEST123", "discount": "100"}
                        ],
                        "severity": "High",
                        "category": "Business Logic"
                    },
                    {
                        "name": "订单状态篡改测试",
                        "description": "测试订单状态修改权限",
                        "payloads": [
                            {"order_id": "123456", "status": "delivered"},
                            {"tracking_code": "VN123456789", "status": "paid"}
                        ],
                        "severity": "Critical",
                        "category": "Authorization"
                    }
                ])

            # 支付系统测试
            if site_info.get("payment_systems"):
                test_cases.extend([
                    {
                        "name": "支付绕过测试",
                        "description": "测试越南支付系统的安全防护",
                        "payloads": [
                            {"amount": "0", "currency": "VND"},
                            {"payment_method": "momo", "transaction_id": "fake123"},
                            {"callback_url": "http://evil.com/callback"}
                        ],
                        "severity": "Critical",
                        "category": "Payment Security"
                    }
                ])

        except Exception as e:
            logger.error(f"生成测试用例时出错: {e}")

        return test_cases

    def create_vietnam_scan_report(self, scan_results: Dict[str, Any]) -> str:
        """创建越南语扫描报告"""
        report = f"""
# Báo Cáo Đánh Giá Bảo Mật Hệ Thống Giao Hàng Việt Nam
**Thời gian扫描**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Đối tượng扫描**: {scan_results.get('target_url', 'Unknown')}
**Hệ thống**: Dragon-V Triple Bot v3.2.0

---

## Tổng Quan

Loại hình网站: {scan_results.get('site_type', 'Unknown')}
Mức độ tin cậy: {scan_results.get('confidence', 0):.2f}
Hệ thống thanh toán: {', '.join(scan_results.get('payment_systems', []))}
Tính năng logistics: {', '.join(scan_results.get('logistics_features', []))}

---

## Kết Quả Quét Mã Lỗi

Tổng số lỗ_hổng tìm thấy: {scan_results.get('total_vulnerabilities', 0)}
Lỗ hổng nghiêm trọng: {scan_results.get('critical_vulns', 0)}
Lỗ hổng cao: {scan_results.get('high_vulns', 0)}
Lỗ hổng trung bình: {scan_results.get('medium_vulns', 0)}
Lỗ hổng thấp: {scan_results.get('low_vulns', 0)}

---

## Đề Xuất Sửa Chữa

1. **Ưu tiên cao**: Sửa các lỗ hổng nghiêm trọng và cao ngay lập tức
2. **Bảo mật thanh toán**: Kiểm tra và bảo mật các hệ thống thanh toán
3. **Bảo vệ dữ liệu**: Mã hóa thông tin khách hàng và đơn hàng
4. **Kiểm soát truy cập**: Thực hiện kiểm soát quyền truy cập chặt chẽ

---

## Liên Hệ

Dragon-V Triple Bot Security Team
Email: security@dragon-v-bot.com

*Báo cáo này được tạo ra tự động bởi hệ thống扫描 chuyên dụng*
        """

        return report.strip()

def main():
    """主函数 - 演示越南化增强功能"""
    print("=== 越南化扫描系统增强演示 ===")

    enhancer = VietnamLocalizationEnhancement()

    # 演示URL检测
    test_urls = [
        "https://ghn.vn",
        "https://ghtk.vn",
        "https://viettelpost.vn",
        "https://shop.example.com"
    ]

    print("\n=== 越南物流网站检测演示 ===")
    for url in test_urls:
        result = enhancer.detect_vietnam_logistics_site(url)
        print(f"\nURL: {url}")
        print(f"是否为越南物流网站: {result['is_vietnam_logistics']}")
        print(f"置信度: {result['confidence']:.2f}")
        print(f"网站类型: {result['site_type']}")
        print(f"检测指标: {len(result['detected_indicators'])} 个")

    # 演示测试用例生成
    print("\n=== 越南化测试用例生成演示 ===")
    site_info = {
        "site_type": "logistics_platform",
        "payment_systems": ["MoMo", "VNPay"]
    }

    test_cases = enhancer.generate_vulnerability_test_cases(site_info)
    print(f"生成测试用例数量: {len(test_cases)}")

    for i, test_case in enumerate(test_cases[:3], 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   描述: {test_case['description']}")
        print(f"   严重性: {test_case['severity']}")

    print("\n=== 越南化增强系统演示完成 ===")

if __name__ == "__main__":
    main()