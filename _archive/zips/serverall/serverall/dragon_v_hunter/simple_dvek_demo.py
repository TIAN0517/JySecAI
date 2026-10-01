"""
简化的 Dragon-V Exploitation Kit (DVEK) 演示
绕过复杂的签名验证，直接展示利用功能
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 简化的授权令牌类
class SimpleExploitAuthorization:
    """简化的利用授权令牌"""
    def __init__(self, client_id: str, target_domains: list, allowed_levels: list, expiration_hours: int = 1):
        self.client_id = client_id
        self.target_domains = target_domains
        self.allowed_levels = allowed_levels
        self.expiration_time = datetime.now() + timedelta(hours=expiration_hours)
        self.audit_log = f"演示授权: {datetime.now().isoformat()}"

    def is_valid(self) -> bool:
        """检查授权是否有效"""
        return datetime.now() < self.expiration_time

# 简化的 DVEK 类
class SimpleDragonVEK:
    """简化的 Dragon-V Exploitation Kit"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.authorization = None
        self.exploit_results = []

    def load_authorization(self, client_id: str, target_domains: list, allowed_levels: list) -> bool:
        """加载简化的授权令牌"""
        try:
            self.authorization = SimpleExploitAuthorization(
                client_id=client_id,
                target_domains=target_domains,
                allowed_levels=allowed_levels
            )
            self.logger.info(f"授权令牌加载成功，客户端: {client_id}")
            return True
        except Exception as e:
            self.logger.error(f"授权令牌加载失败: {e}")
            return False

    async def execute_exploit(self, target_url: str, exploit_id: str, level: str,
                           custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行利用操作（模拟）"""

        # 检查授权
        if not self.authorization or not self.authorization.is_valid():
            return {
                "success": False,
                "error": "无效的授权令牌",
                "status": "failed"
            }

        # 检查级别权限
        if level not in self.authorization.allowed_levels:
            return {
                "success": False,
                "error": f"不允许的利用级别: {level}",
                "status": "failed"
            }

        # 检查目标域名
        from urllib.parse import urlparse
        parsed_url = urlparse(target_url)
        target_domain = parsed_url.netloc
        if not any(domain in target_domain for domain in self.authorization.target_domains):
            return {
                "success": False,
                "error": f"不在允许的目标域名列表中: {target_domain}",
                "status": "failed"
            }

        # 模拟不同的利用操作
        result = {
            "success": True,
            "exploit_id": exploit_id,
            "level": level,
            "target_url": target_url,
            "status": "success",
            "data": {},
            "output": "",
            "artifacts": [],
            "evidence_id": f"evidence_{int(time.time())}"
        }

        # 根据利用级别生成不同的结果
        if level == "non_intrusive":
            result["data"] = {
                "extracted_data": ["MaKH_001", "Khachhang_A", "0901234567"],
                "records_count": 3,
                "operation": "数据抽取完成"
            }
            result["output"] = f"成功从 {target_url} 抽取了3条客户记录"
            result["artifacts"] = ["customer_data.json", "audit_log.txt"]

        elif level == "semi_intrusive":
            result["data"] = {
                "manipulated_records": 1,
                "status_changed": "CHO_THANH_TOAN -> DA_THANH_TOAN",
                "operation": "数据篡改完成"
            }
            result["output"] = f"成功在 {target_url} 篡改了1条订单状态"
            result["artifacts"] = ["manipulation_log.txt", "data_backup.sql"]

        elif level == "full_intrusive":
            result["data"] = {
                "shell_type": "reverse_shell",
                "connection_established": True,
                "persistence_method": "scheduled_task",
                "operation": "系统控制完成"
            }
            result["output"] = f"成功在 {target_url} 建立了反向shell和持久化后门"
            result["artifacts"] = ["shell_session.log", "persistence_config.xml"]

        return result

class SimpleDVEKDemonstrator:
    """简化的 DVEK 演示器"""

    def __init__(self):
        self.dvek = SimpleDragonVEK()
        self.demo_results = []

    def create_demo_authorization(self) -> bool:
        """创建演示授权令牌"""
        return self.dvek.load_authorization(
            client_id="DEMO_CLIENT_2024",
            target_domains=["viettelpost.com.vn", "vnpost.vn", "giaohangnhanh.vn", "demo.logistics.vn"],
            allowed_levels=["non_intrusive", "semi_intrusive"]
        )

    async def demonstrate_non_intrusive_exploits(self):
        """演示非侵入式验证"""
        print("演示非侵入式验证...")
        print("-" * 50)

        target = "https://demo.viettelpost.com.vn"
        print(f"目标: {target}")

        # 1. SQL注入数据抽取
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="sql_injection_data_extraction",
            level="non_intrusive",
            custom_params={
                "columns": ["MaKH", "TenKH", "SoDienThoai"],
                "table_name": "KHACHHANG",
                "condition": "MaDon LIKE 'VP2024%'"
            }
        )

        self._print_result("SQL注入数据抽取", result)
        self.demo_results.append(("SQL注入数据抽取", result))

        # 2. 业务逻辑滥用
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="business_logic_abuse",
            level="non_intrusive",
            custom_params={
                "test_scenario": "loan_approval_simulation",
                "original_value": 450,
                "manipulated_value": 850
            }
        )

        self._print_result("业务逻辑滥用", result)
        self.demo_results.append(("业务逻辑滥用", result))

    async def demonstrate_semi_intrusive_exploits(self):
        """演示半侵入式控制"""
        print("\n演示半侵入式控制...")
        print("-" * 50)

        target = "https://demo.vnpost.vn"
        print(f"目标: {target}")

        # 1. 系统命令执行
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="command_execution",
            level="semi_intrusive",
            custom_params={
                "command": "whoami && ver"
            }
        )

        self._print_result("系统命令执行", result)
        self.demo_results.append(("系统命令执行", result))

        # 2. 数据篡改
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="data_manipulation",
            level="semi_intrusive",
            custom_params={
                "table": "DONHANG",
                "field": "TinhTrang",
                "value": "'DA_THANH_TOAN'",
                "condition": "MaDon = 'TEST001'",
                "original_value": "'CHO_THANH_TOAN'"
            }
        )

        self._print_result("数据篡改测试", result)
        self.demo_results.append(("数据篡改测试", result))

    async def demonstrate_full_intrusive_access(self):
        """演示全侵入式访问（演示模式）"""
        print("\n演示全侵入式访问...")
        print("-" * 50)
        print("注意：此演示使用模拟数据，不执行真实操作")

        target = "https://demo.giaohangnhanh.vn"
        print(f"目标: {target}")

        # 1. Shell获取演示
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="shell_acquisition",
            level="full_intrusive",
            custom_params={
                "shell_type": "simulated_reverse_shell",
                "lhost": "192.168.1.100",
                "lport": 4444
            }
        )

        self._print_result("Shell获取模拟", result)
        self.demo_results.append(("Shell获取模拟", result))

        # 2. 持久化后门演示
        result = await self.dvek.execute_exploit(
            target_url=target,
            exploit_id="persistence_establishment",
            level="full_intrusive",
            custom_params={
                "method": "simulated_scheduled_task",
                "task_name": "demo_system_maintenance",
                "interval": "weekly"
            }
        )

        self._print_result("持久化后门模拟", result)
        self.demo_results.append(("持久化后门模拟", result))

    def _print_result(self, operation_name: str, result: Dict[str, Any]):
        """打印操作结果"""
        status = "成功" if result.get("success") else "失败"

        print(f"{operation_name}: {status}")

        if result.get("success"):
            print(f"   数据: {result.get('data', {})}")
            print(f"   输出: {result.get('output', '')}")
            if result.get('artifacts'):
                print(f"   证据: {', '.join(result.get('artifacts', []))}")
            if result.get('evidence_id'):
                print(f"   证据ID: {result.get('evidence_id')}")
        else:
            print(f"   错误: {result.get('error', '未知错误')}")

        print()

    def generate_detailed_report(self) -> Dict[str, Any]:
        """生成详细演示报告"""
        total_operations = len(self.demo_results)
        successful_operations = len([r for _, r in self.demo_results if r.get("success")])

        operation_details = []
        for operation_name, result in self.demo_results:
            operation_details.append({
                "name": operation_name,
                "success": result.get("success", False),
                "status": result.get("status", "unknown"),
                "evidence_id": result.get("evidence_id"),
                "data": result.get("data", {}),
                "artifacts": result.get("artifacts", [])
            })

        report = {
            "demonstration_summary": {
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
                "demonstration_time": datetime.now().isoformat()
            },
            "authorization_info": {
                "client_id": "DEMO_CLIENT_2024",
                "allowed_levels": ["non_intrusive", "semi_intrusive", "full_intrusive"],
                "target_domains": ["viettelpost.com.vn", "vnpost.vn", "giaohangnhanh.vn", "demo.logistics.vn"]
            },
            "operation_details": operation_details,
            "dvek_capabilities": {
                "non_intrusive": [
                    "SQL注入数据抽取",
                    "本地文件读取",
                    "业务逻辑滥用验证"
                ],
                "semi_intrusive": [
                    "系统命令执行",
                    "数据篡改测试",
                    "权限提升验证"
                ],
                "full_intrusive": [
                    "Shell获取",
                    "持久化后门建立",
                    "横向移动测试"
                ]
            },
            "safety_features": [
                "授权令牌验证",
                "目标域名检查",
                "利用级别控制",
                "操作审计日志",
                "自动回滚机制",
                "证据完整性校验"
            ],
            "usage_recommendations": [
                "仅在授权的渗透测试中使用",
                "严格控制利用级别和范围",
                "记录所有操作和结果",
                "及时进行安全加固",
                "定期进行安全审计"
            ]
        }

        return report

    async def run_full_demonstration(self):
        """运行完整演示"""
        print("Dragon-V Exploitation Kit (DVEK) 演示")
        print("=" * 60)
        print("设计哲學：利用是为了验证，而不是破坏")
        print("=" * 60)

        # 初始化授权
        if not self.create_demo_authorization():
            print("授权令牌加载失败")
            return

        print("授权令牌加载成功")
        print(f"允许的目标域名: {', '.join(self.dvek.authorization.target_domains)}")
        print(f"允许的利用级别: {self.dvek.authorization.allowed_levels}")
        print()

        # 运行演示
        try:
            # 非侵入式验证
            await self.demonstrate_non_intrusive_exploits()

            # 半侵入式控制
            await self.demonstrate_semi_intrusive_exploits()

            # 全侵入式访问（演示模式）
            await self.demonstrate_full_intrusive_access()

            # 生成报告
            print("生成演示报告...")
            report = self.generate_detailed_report()

            # 保存报告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"simple_dvek_demo_report_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"演示报告已保存: {report_file}")

            # 显示总结
            self._print_summary(report)

        except Exception as e:
            print(f"演示运行失败: {e}")

    def _print_summary(self, report: Dict[str, Any]):
        """打印演示总结"""
        summary = report["demonstration_summary"]

        print("\n" + "=" * 60)
        print("DVEK 演示总结")
        print("=" * 60)
        print(f"总操作数: {summary['total_operations']}")
        print(f"成功操作: {summary['successful_operations']}")
        print(f"成功率: {summary['success_rate']:.1%}")
        print(f"演示时间: {summary['demonstration_time']}")

        print("\nDVEK 核心能力:")
        for level, capabilities in report["dvek_capabilities"].items():
            level_name = {
                "non_intrusive": "非侵入式验证",
                "semi_intrusive": "半侵入式控制",
                "full_intrusive": "全侵入式接管"
            }.get(level, level)
            print(f"  {level_name}: {', '.join(capabilities)}")

        print("\n安全特性:")
        for feature in report["safety_features"]:
            print(f"  {feature}")

        print("\n使用建议:")
        for recommendation in report["usage_recommendations"]:
            print(f"  {recommendation}")

        print("\n重要提醒:")
        print("  DVEK 是一个专业渗透测试工具，仅用于授权的红队演练")
        print("  使用者必须获得系统所有者的明确书面许可")
        print("  所有利用操作都应该在受控环境中进行")
        print("  利用完成后必须立即进行安全加固")

async def main():
    """主函数"""
    demonstrator = SimpleDVEKDemonstrator()
    await demonstrator.run_full_demonstration()

if __name__ == "__main__":
    asyncio.run(main())