#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus管理器 - 与Dragon-V系统深度集成
Nessus Manager - Deep Integration with Dragon-V System

功能特性:
- 与现有Telegram Bot系统集成
- 自动扫描任务调度
- 实时状态监控
- 智能报告生成
- 漏洞数据同步
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from nessus_integration import NessusIntegration, nessus_servers_config
from nessus_config import nessus_config
import sqlite3
import os

class NessusManager:
    """Nessus管理器 - 深度集成Dragon-V系统"""
    
    def __init__(self, db_path: str = "dragon_triple_telegram_bot.db"):
        self.db_path = db_path
        self.active_scans = {}
        self.scan_history = []
        
        # 初始化数据库
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建Nessus扫描记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nessus_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT UNIQUE,
                    target TEXT NOT NULL,
                    scan_name TEXT,
                    policy_name TEXT,
                    status TEXT DEFAULT 'pending',
                    start_time DATETIME,
                    end_time DATETIME,
                    vulnerabilities_critical INTEGER DEFAULT 0,
                    vulnerabilities_high INTEGER DEFAULT 0,
                    vulnerabilities_medium INTEGER DEFAULT 0,
                    vulnerabilities_low INTEGER DEFAULT 0,
                    risk_score INTEGER DEFAULT 0,
                    report_file TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建漏洞详情表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nessus_vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT,
                    plugin_id INTEGER,
                    plugin_name TEXT,
                    severity INTEGER,
                    description TEXT,
                    risk_factor TEXT,
                    solution TEXT,
                    cvss_score REAL,
                    port TEXT,
                    protocol TEXT,
                    FOREIGN KEY (scan_id) REFERENCES nessus_scans (scan_id)
                )
            ''')
            
            # 创建扫描策略表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nessus_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    template_uuid TEXT,
                    settings TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("[+] Nessus数据库表初始化完成")
        except Exception as e:
            print(f"[-] 数据库初始化失败: {e}")
    
    async def get_active_nessus_server(self) -> Optional[NessusIntegration]:
        """获取可用的Nessus服务器"""
        for server_name, server_config in nessus_servers_config.items():
            try:
                # 创建Nessus实例
                server = NessusIntegration(
                    server_config['nessus_url'],
                    server_config['access_key'],
                    server_config['secret_key']
                )
                # 测试连接
                connection_result = await server.test_connection()
                if connection_result.get('status') == 'success':
                    print(f"[+] 使用Nessus服务器: {server_name}")
                    return server
            except Exception as e:
                print(f"[-] Nessus服务器 {server_name} 连接失败: {e}")
        
        print("[-] 没有可用的Nessus服务器")
        return None
    
    async def schedule_scan(self, target: str, policy_name: str = "web_application", 
                           scan_name: str = None, telegram_chat_id: str = None) -> Dict[str, Any]:
        """调度Nessus扫描任务"""
        try:
            nessus = await self.get_active_nessus_server()
            if not nessus:
                return {"error": "没有可用的Nessus服务器"}
            
            # 获取扫描策略
            policy = nessus_config.get_scan_policy(policy_name)
            if not policy:
                return {"error": f"未知的扫描策略: {policy_name}"}
            
            if not scan_name:
                scan_name = f"Dragon-V Nessus扫描 - {target} - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 创建扫描记录
            scan_id = await self.create_scan_record(target, scan_name, policy_name)
            
            # 发送开始通知
            if telegram_chat_id:
                await self.send_telegram_notification(
                    telegram_chat_id, 
                    f"🔍 Nessus扫描开始\n目标: {target}\n策略: {policy['name']}\n扫描ID: {scan_id}"
                )
            
            # 执行扫描
            result = await self.execute_scan(nessus, target, policy_name, scan_name, scan_id)
            
            # 发送完成通知
            if telegram_chat_id and result.get('success'):
                analysis = result.get('vulnerability_analysis', {})
                message = f"✅ Nessus扫描完成\n目标: {target}\n"
                message += f"严重漏洞: {analysis.get('critical_count', 0)}个\n"
                message += f"高危漏洞: {analysis.get('high_count', 0)}个\n"
                message += f"风险评分: {analysis.get('risk_score', 0)}"
                
                await self.send_telegram_notification(telegram_chat_id, message)
            
            return result
            
        except Exception as e:
            error_msg = f"调度扫描失败: {e}"
            print(f"[-] {error_msg}")
            return {"error": error_msg}
    
    async def create_scan_record(self, target: str, scan_name: str, policy_name: str) -> str:
        """创建扫描记录"""
        try:
            scan_id = f"nessus_{int(time.time())}_{hash(target) % 10000}"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO nessus_scans (scan_id, target, scan_name, policy_name, status, start_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (scan_id, target, scan_name, policy_name, 'running', datetime.now()))
            
            conn.commit()
            conn.close()
            
            print(f"[+] 创建扫描记录: {scan_id}")
            return scan_id
            
        except Exception as e:
            print(f"[-] 创建扫描记录失败: {e}")
            return f"error_{int(time.time())}"
    
    async def execute_scan(self, nessus: NessusIntegration, target: str, policy_name: str, 
                          scan_name: str, scan_id: str) -> Dict[str, Any]:
        """执行Nessus扫描"""
        try:
            # 创建扫描
            actual_scan_id = await nessus.create_scan(target, policy_name, scan_name)
            if not actual_scan_id:
                return {"error": "创建Nessus扫描失败"}
            
            # 启动扫描
            if not await nessus.launch_scan(actual_scan_id):
                return {"error": "启动Nessus扫描失败"}
            
            # 等待完成
            if not await nessus.wait_for_scan_completion(actual_scan_id):
                return {"error": "Nessus扫描未完成或超时"}
            
            # 获取结果
            results = await nessus.get_scan_results(actual_scan_id)
            if not results:
                return {"error": "获取扫描结果失败"}
            
            # 分析漏洞
            analysis = await nessus.analyze_vulnerabilities(results)
            
            # 导出报告
            report_file = await nessus.export_scan_report(actual_scan_id)
            
            # 更新扫描记录
            await self.update_scan_record(scan_id, actual_scan_id, analysis, report_file)
            
            # 保存漏洞详情
            await self.save_vulnerability_details(scan_id, results)
            
            return {
                "success": True,
                "scan_id": scan_id,
                "actual_scan_id": actual_scan_id,
                "vulnerability_analysis": analysis,
                "report_file": report_file,
                "raw_results": results
            }
            
        except Exception as e:
            error_msg = f"执行扫描失败: {e}"
            print(f"[-] {error_msg}")
            
            # 更新扫描记录为失败
            await self.update_scan_record(scan_id, "", {}, "", "failed")
            
            return {"error": error_msg}
    
    async def update_scan_record(self, scan_id: str, actual_scan_id: str, analysis: Dict[str, Any], 
                                report_file: str, status: str = "completed"):
        """更新扫描记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE nessus_scans 
                SET status = ?, end_time = ?, 
                    vulnerabilities_critical = ?, vulnerabilities_high = ?,
                    vulnerabilities_medium = ?, vulnerabilities_low = ?,
                    risk_score = ?, report_file = ?
                WHERE scan_id = ?
            ''', (
                status, datetime.now(),
                analysis.get('critical_count', 0), analysis.get('high_count', 0),
                analysis.get('medium_count', 0), analysis.get('low_count', 0),
                analysis.get('risk_score', 0), report_file, scan_id
            ))
            
            conn.commit()
            conn.close()
            
            print(f"[+] 更新扫描记录: {scan_id}")
            
        except Exception as e:
            print(f"[-] 更新扫描记录失败: {e}")
    
    async def save_vulnerability_details(self, scan_id: str, results: Dict[str, Any]):
        """保存漏洞详情"""
        try:
            vulnerabilities = results.get('vulnerabilities', [])
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for vuln in vulnerabilities:
                cursor.execute('''
                    INSERT INTO nessus_vulnerabilities 
                    (scan_id, plugin_id, plugin_name, severity, description, risk_factor, solution, cvss_score, port, protocol)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    scan_id,
                    vuln.get('plugin_id'),
                    vuln.get('plugin_name', ''),
                    vuln.get('severity', 0),
                    vuln.get('description', ''),
                    vuln.get('risk_factor', ''),
                    vuln.get('solution', ''),
                    vuln.get('cvss_base_score', 0.0),
                    vuln.get('port', ''),
                    vuln.get('protocol', '')
                ))
            
            conn.commit()
            conn.close()
            
            print(f"[+] 保存漏洞详情: {len(vulnerabilities)} 个漏洞")
            
        except Exception as e:
            print(f"[-] 保存漏洞详情失败: {e}")
    
    async def send_telegram_notification(self, chat_id: str, message: str) -> bool:
        """发送Telegram通知"""
        try:
            # 这里需要集成现有的Telegram Bot系统
            # 暂时使用简单的打印
            print(f"📢 Telegram通知 ({chat_id}): {message}")
            return True
        except Exception as e:
            print(f"[-] 发送Telegram通知失败: {e}")
            return False
    
    def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取扫描历史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM nessus_scans 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            scans = []
            for row in cursor.fetchall():
                scan = {
                    'id': row[0],
                    'scan_id': row[1],
                    'target': row[2],
                    'scan_name': row[3],
                    'policy_name': row[4],
                    'status': row[5],
                    'start_time': row[6],
                    'end_time': row[7],
                    'vulnerabilities_critical': row[8],
                    'vulnerabilities_high': row[9],
                    'vulnerabilities_medium': row[10],
                    'vulnerabilities_low': row[11],
                    'risk_score': row[12],
                    'report_file': row[13],
                    'created_at': row[14]
                }
                scans.append(scan)
            
            conn.close()
            return scans
            
        except Exception as e:
            print(f"[-] 获取扫描历史失败: {e}")
            return []
    
    def get_vulnerability_details(self, scan_id: str) -> List[Dict[str, Any]]:
        """获取漏洞详情"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM nessus_vulnerabilities 
                WHERE scan_id = ? 
                ORDER BY severity DESC
            ''', (scan_id,))
            
            vulnerabilities = []
            for row in cursor.fetchall():
                vuln = {
                    'id': row[0],
                    'scan_id': row[1],
                    'plugin_id': row[2],
                    'plugin_name': row[3],
                    'severity': row[4],
                    'description': row[5],
                    'risk_factor': row[6],
                    'solution': row[7],
                    'cvss_score': row[8],
                    'port': row[9],
                    'protocol': row[10]
                }
                vulnerabilities.append(vuln)
            
            conn.close()
            return vulnerabilities
            
        except Exception as e:
            print(f"[-] 获取漏洞详情失败: {e}")
            return []
    
    def generate_scan_report(self, scan_id: str, format: str = "html") -> str:
        """生成扫描报告"""
        try:
            # 获取扫描信息
            scans = self.get_scan_history(100)  # 获取足够多的记录
            scan_info = None
            for scan in scans:
                if scan['scan_id'] == scan_id:
                    scan_info = scan
                    break
            
            if not scan_info:
                return ""
            
            # 获取漏洞详情
            vulnerabilities = self.get_vulnerability_details(scan_id)
            
            if format == "html":
                return self.generate_html_report(scan_info, vulnerabilities)
            elif format == "text":
                return self.generate_text_report(scan_info, vulnerabilities)
            else:
                return self.generate_text_report(scan_info, vulnerabilities)
                
        except Exception as e:
            print(f"[-] 生成报告失败: {e}")
            return ""
    
    def generate_html_report(self, scan_info: Dict[str, Any], vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成HTML报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Nessus扫描报告 - {scan_info['target']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .vulnerability {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .critical {{ border-left: 5px solid #d9534f; background: #f2dede; }}
                .high {{ border-left: 5px solid #f0ad4e; background: #fcf8e3; }}
                .medium {{ border-left: 5px solid #5bc0de; background: #d9edf7; }}
                .low {{ border-left: 5px solid #5cb85c; background: #dff0d8; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Nessus扫描报告</h1>
                <p><strong>目标:</strong> {scan_info['target']}</p>
                <p><strong>扫描名称:</strong> {scan_info['scan_name']}</p>
                <p><strong>扫描时间:</strong> {scan_info['start_time']} 至 {scan_info['end_time']}</p>
                <p><strong>风险评分:</strong> {scan_info['risk_score']}</p>
                <p><strong>漏洞统计:</strong> 
                    严重: {scan_info['vulnerabilities_critical']} | 
                    高危: {scan_info['vulnerabilities_high']} | 
                    中危: {scan_info['vulnerabilities_medium']} | 
                    低危: {scan_info['vulnerabilities_low']}
                </p>
            </div>
            
            <h2>漏洞详情</h2>
        """
        
        for vuln in vulnerabilities:
            severity_class = ""
            if vuln['severity'] >= 4:
                severity_class = "critical"
            elif vuln['severity'] == 3:
                severity_class = "high"
            elif vuln['severity'] == 2:
                severity_class = "medium"
            else:
                severity_class = "low"
            
            html += f"""
            <div class="vulnerability {severity_class}">
                <h3>{vuln['plugin_name']} (严重性: {vuln['severity']})</h3>
                <p><strong>风险因素:</strong> {vuln['risk_factor']}</p>
                <p><strong>CVSS评分:</strong> {vuln['cvss_score']}</p>
                <p><strong>端口/协议:</strong> {vuln['port']}/{vuln['protocol']}</p>
                <p><strong>描述:</strong> {vuln['description'][:500]}...</p>
                <p><strong>解决方案:</strong> {vuln['solution'][:500]}...</p>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        # 保存HTML文件
        filename = f"nessus_report_{scan_info['scan_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filename
    
    def generate_text_report(self, scan_info: Dict[str, Any], vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成文本报告"""
        report = f"""
        Nessus扫描报告
        ===============
        
        目标: {scan_info['target']}
        扫描名称: {scan_info['scan_name']}
        扫描时间: {scan_info['start_time']} 至 {scan_info['end_time']}
        风险评分: {scan_info['risk_score']}
        
        漏洞统计:
        - 严重: {scan_info['vulnerabilities_critical']}
        - 高危: {scan_info['vulnerabilities_high']}
        - 中危: {scan_info['vulnerabilities_medium']}
        - 低危: {scan_info['vulnerabilities_low']}
        
        漏洞详情:
        =========
        """
        
        for i, vuln in enumerate(vulnerabilities, 1):
            report += f"""
        {i}. {vuln['plugin_name']} (严重性: {vuln['severity']})
           风险因素: {vuln['risk_factor']}
           CVSS评分: {vuln['cvss_score']}
           端口/协议: {vuln['port']}/{vuln['protocol']}
           描述: {vuln['description'][:300]}...
           解决方案: {vuln['solution'][:300]}...
            
            """
        
        # 保存文本文件
        filename = f"nessus_report_{scan_info['scan_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename

# 全局管理器实例
nessus_manager = NessusManager()

async def test_nessus_integration():
    """测试Nessus集成"""
    print("🧪 测试Nessus集成...")
    
    # 测试目标
    target = "example.com"
    
    result = await nessus_manager.schedule_scan(target, "web_application")
    
    if result.get("success"):
        print("✅ Nessus集成测试成功")
        print(f"扫描ID: {result.get('scan_id')}")
        print(f"漏洞分析: {result.get('vulnerability_analysis')}")
        print(f"报告文件: {result.get('report_file')}")
    else:
        print(f"❌ Nessus集成测试失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_nessus_integration())