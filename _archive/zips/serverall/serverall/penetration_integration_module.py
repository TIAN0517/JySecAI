#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渗透测试集成模块
将MCP、CVE POC和Metasploit功能集成到Dragon-V系统中
提供统一的渗透测试接口和命令处理
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# 导入渗透测试相关模块
try:
    from exploitation_module import ExploitationEngine
    from mcp_exploit_database import MCPExploitDatabase
    from cve_poc_enhanced import CVEPOCDatabase
    from metasploit_integration import msf_integration
    from advanced_waf_bypass_real import AdvancedWAFBypass
    from config_enhanced import ConfigManager
    from enhanced_system_manager import SystemManager
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"[!] 导入模块失败: {e}")
    print("[!] 将使用简化模式运行")
    IMPORT_SUCCESS = False


class PenetrationIntegration:
    """渗透测试集成管理器"""
    
    def __init__(self):
        self.exploitation_engine = None
        self.mcp_database = None
        self.cve_database = None
        self.waf_bypass = None
        self.config_manager = None
        self.system_manager = None
        
        self.initialized = False
        self.mode = "enhanced"  # enhanced, basic, minimal
    
    async def initialize(self) -> bool:
        """初始化渗透测试集成"""
        try:
            if not IMPORT_SUCCESS:
                print("[!] 使用简化模式初始化")
                self.mode = "minimal"
                self.initialized = True
                return True
            
            # 初始化配置管理器
            self.config_manager = ConfigManager()
            
            # 初始化系统管理器
            self.system_manager = SystemManager()
            
            # 初始化漏洞利用引擎（延迟初始化，需要目标URL）
            self.exploitation_engine = None  # 将在使用时初始化
            
            # 初始化MCP数据库
            self.mcp_database = MCPExploitDatabase()
            
            # 初始化CVE POC数据库
            self.cve_database = CVEPOCDatabase()
            
            # 初始化WAF绕过工具（延迟初始化，需要目标URL）
            self.waf_bypass = None  # 将在使用时初始化
            
            # 尝试初始化Metasploit集成，但不让失败影响整体初始化
            try:
                await msf_integration.initialize()
                print("[+] Metasploit集成初始化成功")
            except Exception as msf_error:
                print(f"[!] Metasploit集成初始化失败（不影响其他功能）: {msf_error}")
            
            print("[+] 渗透测试集成初始化完成")
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"[!] 渗透测试集成初始化失败: {e}")
            self.mode = "basic"
            self.initialized = True
            return False
    
    async def perform_penetration_test(self, target_url: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行完整的渗透测试
        
        Args:
            target_url: 目标URL
            options: 测试选项
            
        Returns:
            测试结果
        """
        if not self.initialized:
            await self.initialize()
        
        options = options or {}
        results = {
            "target": target_url,
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "scanning": {},
            "exploitation": {},
            "waf_bypass": {},
            "metasploit": {},
            "summary": {}
        }
        
        try:
            # 1. 执行漏洞扫描
            scanning_results = await self._perform_scanning(target_url, options)
            results["scanning"] = scanning_results
            
            # 2. 执行WAF绕过测试
            if options.get("waf_bypass", True):
                waf_results = await self._perform_waf_bypass(target_url, options)
                results["waf_bypass"] = waf_results
            
            # 3. 执行漏洞利用
            if options.get("exploitation", True):
                exploit_results = await self._perform_exploitation(target_url, scanning_results, options)
                results["exploitation"] = exploit_results
            
            # 4. 执行Metasploit攻击（如果适用）
            if options.get("metasploit", False):
                msf_results = await self._perform_metasploit_attacks(target_url, scanning_results, options)
                results["metasploit"] = msf_results
            
            # 5. 生成总结报告
            results["summary"] = self._generate_summary(results)
            
            return results
            
        except Exception as e:
            print(f"[!] 渗透测试执行失败: {e}")
            results["error"] = str(e)
            return results
    
    async def _perform_scanning(self, target_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行漏洞扫描"""
        if self.mode == "minimal":
            return {"status": "skipped", "reason": "minimal mode"}
        
        try:
            # 延迟初始化exploitation_engine
            if self.exploitation_engine is None:
                self.exploitation_engine = ExploitationEngine(target_url)
            
            # 使用漏洞利用引擎进行扫描
            scan_results = await self.exploitation_engine.run_all_exploits()
            
            # 补充MCP数据库扫描
            mcp_results = self.mcp_database.get_exploits_by_target(target_url)
            
            # 补充CVE数据库扫描
            cve_results = self.cve_database.search_vulnerabilities(target_url)
            
            return {
                "status": "completed",
                "exploitation_engine": scan_results,
                "mcp_exploits": mcp_results,
                "cve_vulnerabilities": cve_results
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _perform_waf_bypass(self, target_url: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行WAF绕过测试"""
        if self.mode == "minimal":
            return {"status": "skipped", "reason": "minimal mode"}
        
        try:
            # 延迟初始化waf_bypass
            if self.waf_bypass is None:
                self.waf_bypass = AdvancedWAFBypass(target_url)
            
            # 执行WAF检测
            waf_detection = self.waf_bypass.detect_waf(target_url)
            
            # 执行WAF绕过测试
            bypass_results = self.waf_bypass.test_bypass_techniques(target_url)
            
            return {
                "status": "completed",
                "waf_detected": waf_detection,
                "bypass_results": bypass_results
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _perform_exploitation(self, target_url: str, scan_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """执行漏洞利用"""
        if self.mode == "minimal":
            return {"status": "skipped", "reason": "minimal mode"}
        
        try:
            # 延迟初始化exploitation_engine
            if self.exploitation_engine is None:
                self.exploitation_engine = ExploitationEngine(target_url)
            
            exploitation_results = {}
            
            # 基于扫描结果执行漏洞利用
            vulnerabilities = scan_results.get("exploitation_engine", {}).get("vulnerabilities", [])
            
            for vuln in vulnerabilities:
                try:
                    exploit_result = await self.exploitation_engine.exploit_vulnerability(
                        target_url, vuln["type"], vuln["payload"]
                    )
                    exploitation_results[vuln["type"]] = exploit_result
                except Exception as e:
                    exploitation_results[vuln["type"]] = {"status": "failed", "error": str(e)}
            
            return {
                "status": "completed",
                "exploitation_results": exploitation_results
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    async def _perform_metasploit_attacks(self, target_url: str, scan_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """执行Metasploit攻击"""
        try:
            # 构建目标信息
            target_info = {
                "url": target_url,
                "services": scan_results.get("services", []),
                "technologies": scan_results.get("technologies", [])
            }
            
            # 搜索相关漏洞
            exploits = await msf_integration.search_vulnerabilities(target_info)
            
            # 执行Metasploit攻击
            attack_results = {}
            for exploit in exploits[:3]:  # 限制为前3个漏洞
                exploit_config = {
                    "exploit_path": exploit["name"],
                    "target_ip": target_url.replace("http://", "").replace("https://", "").split("/")[0],
                    "options": {
                        "rport": "80" if "http" in target_url else "443",
                        "lhost": "192.168.1.100",
                        "lport": "4444"
                    }
                }
                
                result = await msf_integration.execute_metasploit_attack(exploit_config)
                attack_results[exploit["name"]] = result
            
            return {
                "status": "completed",
                "exploits_found": len(exploits),
                "attack_results": attack_results
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试总结"""
        summary = {
            "total_vulnerabilities": 0,
            "critical_vulnerabilities": 0,
            "exploited_vulnerabilities": 0,
            "waf_bypassed": False,
            "risk_level": "Low",
            "recommendations": []
        }
        
        # 计算漏洞数量
        scanning = results.get("scanning", {})
        if scanning.get("status") == "completed":
            exploitation_engine = scanning.get("exploitation_engine", {})
            vulnerabilities = exploitation_engine.get("vulnerabilities", [])
            summary["total_vulnerabilities"] = len(vulnerabilities)
            
            # 统计严重漏洞
            for vuln in vulnerabilities:
                if vuln.get("severity") in ["critical", "high"]:
                    summary["critical_vulnerabilities"] += 1
        
        # 检查WAF绕过
        waf_bypass = results.get("waf_bypass", {})
        if waf_bypass.get("status") == "completed":
            summary["waf_bypassed"] = waf_bypass.get("waf_detected", False)
        
        # 检查漏洞利用结果
        exploitation = results.get("exploitation", {})
        if exploitation.get("status") == "completed":
            exploitation_results = exploitation.get("exploitation_results", {})
            summary["exploited_vulnerabilities"] = len([
                r for r in exploitation_results.values() 
                if r.get("success") == True
            ])
        
        # 评估风险等级
        if summary["critical_vulnerabilities"] > 0:
            summary["risk_level"] = "Critical"
        elif summary["total_vulnerabilities"] > 5:
            summary["risk_level"] = "High"
        elif summary["total_vulnerabilities"] > 2:
            summary["risk_level"] = "Medium"
        else:
            summary["risk_level"] = "Low"
        
        # 生成建议
        if summary["critical_vulnerabilities"] > 0:
            summary["recommendations"].append("立即修复关键漏洞")
        
        if summary["waf_bypassed"]:
            summary["recommendations"].append("加强WAF配置规则")
        
        if summary["exploited_vulnerabilities"] > 0:
            summary["recommendations"].append("已成功利用的漏洞需要立即修复")
        
        return summary
    
    async def get_available_commands(self) -> Dict[str, Any]:
        """获取可用的渗透测试命令"""
        commands = {
            "scan": {
                "description": "执行漏洞扫描",
                "usage": "/scan <target_url> [options]",
                "options": {
                    "quick": "快速扫描模式",
                    "deep": "深度扫描模式",
                    "waf_bypass": "启用WAF绕过"
                }
            },
            "exploit": {
                "description": "执行漏洞利用",
                "usage": "/exploit <target_url> <vulnerability_type>",
                "options": {
                    "payload": "自定义载荷",
                    "technique": "利用技术"
                }
            },
            "waf_bypass": {
                "description": "WAF绕过测试",
                "usage": "/waf_bypass <target_url>",
                "options": {
                    "technique": "指定绕过技术",
                    "intensity": "测试强度"
                }
            },
            "metasploit": {
                "description": "Metasploit攻击",
                "usage": "/metasploit <target_url> [module]",
                "options": {
                    "search": "搜索漏洞模块",
                    "exploit": "执行漏洞利用"
                }
            },
            "report": {
                "description": "生成渗透测试报告",
                "usage": "/report <target_url>",
                "options": {
                    "format": "报告格式 (html/json)",
                    "detailed": "详细报告"
                }
            }
        }
        
        # 根据模式调整可用命令
        if self.mode == "minimal":
            commands = {
                "scan": commands["scan"],
                "report": commands["report"]
            }
        
        return commands

    async def generate_report(self, target_url: str, results: Dict[str, Any] = None, format: str = "text") -> str:
        """
        生成详细的渗透测试报告
        
        Args:
            target_url: 目标URL
            results: 渗透测试结果（如果为None则重新测试）
            format: 报告格式 (text/html/json)
            
        Returns:
            格式化报告
        """
        try:
            # 如果没有提供结果，则执行测试
            if results is None:
                results = await self.perform_penetration_test(target_url)
            
            summary = results.get("summary", {})
            scanning = results.get("scanning", {})
            exploitation = results.get("exploitation", {})
            waf_bypass = results.get("waf_bypass", {})
            metasploit = results.get("metasploit", {})
            
            if format == "html":
                return self._generate_html_report(target_url, results, summary)
            elif format == "json":
                return self._generate_json_report(results)
            else:
                return self._generate_text_report(target_url, results, summary, scanning, exploitation, waf_bypass, metasploit)
                
        except Exception as e:
            error_msg = f"❌ 生成报告失败: {str(e)}"
            if format == "html":
                return f"<html><body><h1>报告生成失败</h1><p>{error_msg}</p></body></html>"
            elif format == "json":
                return json.dumps({"error": error_msg})
            else:
                return error_msg

    def _generate_text_report(self, target_url: str, results: Dict[str, Any], summary: Dict[str, Any], 
                             scanning: Dict[str, Any], exploitation: Dict[str, Any], 
                             waf_bypass: Dict[str, Any], metasploit: Dict[str, Any]) -> str:
        """生成文本格式报告"""
        report = f"""
🐉 Dragon-V 渗透测试报告
{'='*50}

📊 基本信息
{'='*50}
目标URL: {target_url}
测试时间: {results.get('timestamp', 'N/A')}
测试模式: {results.get('mode', 'Unknown')}
风险等级: {summary.get('risk_level', 'Unknown')}

📈 测试摘要
{'='*50}
总漏洞数: {summary.get('total_vulnerabilities', 0)}
严重漏洞: {summary.get('critical_vulnerabilities', 0)}
已利用漏洞: {summary.get('exploited_vulnerabilities', 0)}
WAF检测: {'发现' if waf_bypass.get('waf_detected') else '未发现'}
WAF绕过: {'成功' if summary.get('waf_bypassed') else '失败'}

🔍 漏洞扫描结果
{'='*50}
扫描状态: {scanning.get('status', 'Unknown')}
"""
        
        # 扫描详情
        if scanning.get("status") == "completed":
            exploitation_engine = scanning.get("exploitation_engine", {})
            vulnerabilities = exploitation_engine.get("vulnerabilities", [])
            
            if vulnerabilities:
                report += f"发现漏洞: {len(vulnerabilities)} 个\n"
                for i, vuln in enumerate(vulnerabilities[:10], 1):  # 显示前10个漏洞
                    report += f"{i}. {vuln.get('type', 'Unknown')} - {vuln.get('severity', 'Unknown')}\n"
            else:
                report += "未发现漏洞\n"
        
        # WAF绕过结果
        if waf_bypass.get("status") == "completed":
            report += f"\n🛡️ WAF绕过测试\n{'='*50}\n"
            bypass_results = waf_bypass.get("bypass_results", {})
            if bypass_results:
                for technique, result in bypass_results.items():
                    report += f"{technique}: {'成功' if result.get('success') else '失败'}\n"
        
        # 漏洞利用结果
        if exploitation.get("status") == "completed":
            report += f"\n💥 漏洞利用结果\n{'='*50}\n"
            exploit_results = exploitation.get("exploitation_results", {})
            if exploit_results:
                for vuln_type, result in exploit_results.items():
                    status = "成功" if result.get("success") else "失败"
                    report += f"{vuln_type}: {status}\n"
        
        # Metasploit结果
        if metasploit.get("status") == "completed":
            report += f"\n🔧 Metasploit攻击\n{'='*50}\n"
            exploits_found = metasploit.get("exploits_found", 0)
            attack_results = metasploit.get("attack_results", {})
            report += f"发现漏洞模块: {exploits_found} 个\n"
            if attack_results:
                for exploit_name, result in attack_results.items():
                    status = "成功" if result.get("success") else "失败"
                    report += f"{exploit_name}: {status}\n"
        
        # 安全建议
        recommendations = summary.get("recommendations", [])
        if recommendations:
            report += f"\n💡 安全建议\n{'='*50}\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        
        report += f"\n{'='*50}\n"
        report += "🔒 报告生成完成 | Dragon-V 安全团队\n"
        
        return report

    def _generate_html_report(self, target_url: str, results: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """生成HTML格式报告"""
        html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dragon-V 渗透测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .critical {{ background-color: #ffebee; border-color: #f44336; }}
        .high {{ background-color: #fff3e0; border-color: #ff9800; }}
        .medium {{ background-color: #fffde7; border-color: #ffc107; }}
        .low {{ background-color: #e8f5e8; border-color: #4caf50; }}
        .recommendation {{ background-color: #e3f2fd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🐉 Dragon-V 渗透测试报告</h1>
    
    <div class="section">
        <h2>📊 基本信息</h2>
        <p><strong>目标URL:</strong> {target_url}</p>
        <p><strong>测试时间:</strong> {results.get('timestamp', 'N/A')}</p>
        <p><strong>测试模式:</strong> {results.get('mode', 'Unknown')}</p>
        <p><strong>风险等级:</strong> <span class="{summary.get('risk_level', 'low').lower()}">{summary.get('risk_level', 'Unknown')}</span></p>
    </div>
    
    <div class="section">
        <h2>📈 测试摘要</h2>
        <p><strong>总漏洞数:</strong> {summary.get('total_vulnerabilities', 0)}</p>
        <p><strong>严重漏洞:</strong> {summary.get('critical_vulnerabilities', 0)}</p>
        <p><strong>已利用漏洞:</strong> {summary.get('exploited_vulnerabilities', 0)}</p>
        <p><strong>WAF检测:</strong> {'发现' if results.get('waf_bypass', {}).get('waf_detected') else '未发现'}</p>
        <p><strong>WAF绕过:</strong> {'成功' if summary.get('waf_bypassed') else '失败'}</p>
    </div>
    
    <div class="section">
        <h2>💡 安全建议</h2>
        """
        
        recommendations = summary.get("recommendations", [])
        for rec in recommendations:
            html_report += f'<div class="recommendation">• {rec}</div>'
        
        html_report += """
    </div>
    
    <div class="section">
        <h2>🔒 报告信息</h2>
        <p>此报告由 Dragon-V 安全渗透测试系统生成</p>
        <p>生成时间: """ + results.get('timestamp', 'N/A') + """</p>
    </div>
</body>
</html>
"""
        return html_report

    def _generate_json_report(self, results: Dict[str, Any]) -> str:
        """生成JSON格式报告"""
        try:
            return json.dumps(results, indent=2, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"生成JSON报告失败: {str(e)}"})


# Bot命令处理器
class PenetrationCommandHandler:
    """渗透测试命令处理器"""
    
    def __init__(self, penetration_integration: PenetrationIntegration):
        self.penetration = penetration_integration
        
    async def handle_command(self, command: str, args: List[str]) -> str:
        """处理渗透测试命令"""
        if not self.penetration.initialized:
            await self.penetration.initialize()
        
        if command == "scan":
            return await self._handle_scan_command(args)
        elif command == "exploit":
            return await self._handle_exploit_command(args)
        elif command == "waf_bypass":
            return await self._handle_waf_bypass_command(args)
        elif command == "metasploit":
            return await self._handle_metasploit_command(args)
        elif command == "report":
            return await self._handle_report_command(args)
        elif command == "help":
            return await self._handle_help_command()
        else:
            return f"未知命令: {command}\n使用 /help 查看可用命令"
    
    async def _handle_scan_command(self, args: List[str]) -> str:
        """处理扫描命令"""
        if len(args) < 1:
            return "用法: /scan <目标URL> [选项]\n选项: --quick, --deep, --waf_bypass"
        
        target_url = args[0]
        options = {
            "quick": "--quick" in args,
            "deep": "--deep" in args,
            "waf_bypass": "--waf_bypass" in args
        }
        
        result = await self.penetration.perform_penetration_test(target_url, options)
        
        # 格式化结果
        summary = result.get("summary", {})
        response = f"""
✅ 扫描完成

目标: {target_url}
风险等级: {summary.get('risk_level', 'Unknown')}
总漏洞数: {summary.get('total_vulnerabilities', 0)}
严重漏洞: {summary.get('critical_vulnerabilities', 0)}
已利用漏洞: {summary.get('exploited_vulnerabilities', 0)}
WAF绕过: {'是' if summary.get('waf_bypassed') else '否'}

建议:
"""
        
        for rec in summary.get("recommendations", []):
            response += f"• {rec}\n"
        
        return response
    
    async def _handle_exploit_command(self, args: List[str]) -> str:
        """处理漏洞利用命令"""
        if len(args) < 2:
            return "用法: /exploit <目标URL> <漏洞类型> [选项]\n漏洞类型: sql, xss, rce, lfi, etc."
        
        target_url = args[0]
        vuln_type = args[1]
        
        try:
            if self.penetration.mode == "minimal":
                return "漏洞利用功能在简化模式下不可用"
            
            result = await self.penetration.exploitation_engine.exploit_vulnerability(
                target_url, vuln_type
            )
            
            if result.get("success"):
                return f"✅ 漏洞利用成功!\n结果: {result.get('result', 'N/A')}"
            else:
                return f"❌ 漏洞利用失败: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ 漏洞利用错误: {str(e)}"
    
    async def _handle_waf_bypass_command(self, args: List[str]) -> str:
        """处理WAF绕过命令"""
        if len(args) < 1:
            return "用法: /waf_bypass <目标URL> [选项]"
        
        target_url = args[0]
        
        try:
            if self.penetration.mode == "minimal":
                return "WAF绕过功能在简化模式下不可用"
            
            result = await self.penetration.perform_penetration_test(target_url, {"waf_bypass": True})
            waf_result = result.get("waf_bypass", {})
            
            if waf_result.get("status") == "completed":
                waf_detected = waf_result.get("waf_detected", False)
                bypass_results = waf_result.get("bypass_results", {})
                
                response = f"WAF检测: {'发现' if waf_detected else '未发现'}\n"
                response += f"绕过结果: {bypass_results}"
                return response
            else:
                return f"WAF绕过测试失败: {waf_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ WAF绕过错误: {str(e)}"
    
    async def _handle_metasploit_command(self, args: List[str]) -> str:
        """处理Metasploit命令"""
        if len(args) < 1:
            return "用法: /metasploit <目标URL> [模块]\n选项: --search, --exploit"
        
        target_url = args[0]
        
        if "--search" in args:
            # 搜索漏洞模块
            target_info = {"url": target_url}
            exploits = await msf_integration.search_vulnerabilities(target_info)
            
            response = f"找到 {len(exploits)} 个漏洞模块:\n"
            for exploit in exploits[:5]:  # 显示前5个
                response += f"• {exploit.get('name', 'N/A')} - {exploit.get('description', '')}\n"
            return response
        
        else:
            return "Metasploit功能需要指定操作类型\n使用 --search 搜索漏洞模块"
    
    async def _handle_report_command(self, args: List[str]) -> str:
        """处理报告命令"""
        if len(args) < 1:
            return "用法: /report <目标URL> [选项]\n选项: --format=html/json, --detailed"
        
        target_url = args[0]
        
        result = await self.penetration.perform_penetration_test(target_url)
        
        # 生成简化报告
        summary = result.get("summary", {})
        report = f"""
📊 渗透测试报告

目标: {target_url}
时间: {result.get('timestamp', 'N/A')}
模式: {result.get('mode', 'Unknown')}

📈 测试结果:
• 总漏洞数: {summary.get('total_vulnerabilities', 0)}
• 严重漏洞: {summary.get('critical_vulnerabilities', 0)}
• 已利用漏洞: {summary.get('exploited_vulnerabilities', 0)}
• WAF绕过: {'是' if summary.get('waf_bypassed') else '否'}
• 风险等级: {summary.get('risk_level', 'Unknown')}

💡 建议:
"""
        
        for rec in summary.get("recommendations", []):
            report += f"• {rec}\n"
        
        return report
    
    async def _handle_help_command(self) -> str:
        """处理帮助命令"""
        commands = await self.penetration.get_available_commands()
        
        response = "🔍 渗透测试命令:\n\n"
        for cmd, info in commands.items():
            response += f"/{cmd}: {info['description']}\n"
            response += f"  用法: {info['usage']}\n"
            if info.get('options'):
                for opt, desc in info['options'].items():
                    response += f"  选项: {opt} - {desc}\n"
            response += "\n"
        
        return response


# 全局实例
penetration_integration = PenetrationIntegration()
command_handler = PenetrationCommandHandler(penetration_integration)


async def test_integration():
    """测试集成功能"""
    print("测试渗透测试集成...")
    
    await penetration_integration.initialize()
    
    # 测试命令处理
    commands = [
        "help",
        "scan http://example.com --quick",
        "report http://example.com"
    ]
    
    for cmd in commands:
        parts = cmd.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        result = await command_handler.handle_command(command, args)
        print(f"命令: {cmd}")
        print(f"结果: {result}\n")


if __name__ == "__main__":
    asyncio.run(test_integration())