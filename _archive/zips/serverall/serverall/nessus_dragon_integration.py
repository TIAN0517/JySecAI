#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus与Dragon-V系统集成模块
Nessus and Dragon-V System Integration Module

将Nessus企业级漏洞扫描与Dragon-V渗透测试系统无缝集成
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入现有模块
from nessus_integration import nessus_manager
from nessus_config_enhanced import scan_config_manager, PRESET_CONFIGS
from exploitation_module import ExploitationEngine
from report_generator import HTMLReportGenerator

class DragonNessusIntegration:
    """Dragon-V与Nessus集成管理器"""
    
    def __init__(self):
        self.nessus_manager = nessus_manager
        # 初始化时不需要target_url，将在实际使用时传入
        self.exploitation_engine = None
        self.scan_config_manager = scan_config_manager
        
    async def comprehensive_security_assessment(self, target: str, scan_policy: str = "web_application", 
                                               intensity: str = "normal") -> Dict[str, Any]:
        """综合安全评估 - 结合Nessus和Dragon-V能力"""
        
        results = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "scan_policy": scan_policy,
            "intensity": intensity,
            "phases": {}
        }
        
        print(f"🔍 开始综合安全评估: {target}")
        
        # 阶段1: Nessus漏洞扫描
        print("[*] 阶段1: Nessus漏洞扫描...")
        nessus_results = await self._run_nessus_scan(target, scan_policy, intensity)
        results["phases"]["nessus_scan"] = nessus_results
        
        # 阶段2: Dragon-V渗透测试
        print("[*] 阶段2: Dragon-V渗透测试...")
        dragon_results = await self._run_dragon_v_tests(target)
        results["phases"]["dragon_v_tests"] = dragon_results
        
        # 阶段3: 智能关联分析
        print("[*] 阶段3: 智能关联分析...")
        correlation_results = await self._correlate_findings(nessus_results, dragon_results)
        results["phases"]["correlation_analysis"] = correlation_results
        
        # 阶段4: 生成综合报告
        print("[*] 阶段4: 生成综合报告...")
        final_report = await self._generate_comprehensive_report(results)
        results["final_report"] = final_report
        
        print(f"✅ 综合安全评估完成: {target}")
        return results
    
    async def _run_nessus_scan(self, target: str, policy: str, intensity: str) -> Dict[str, Any]:
        """运行Nessus扫描"""
        try:
            # 获取扫描配置
            scan_config = self.scan_config_manager.get_scan_config(policy, intensity)
            
            # 获取最佳服务器
            best_server = await self.nessus_manager.get_best_server()
            if not best_server:
                return {"error": "没有可用的Nessus服务器"}
            
            # 执行扫描
            scan_results = await best_server.full_scan_workflow(
                target, 
                f"Dragon-V {policy}扫描 - {target}"
            )
            
            return {
                "status": "completed",
                "scan_config": scan_config,
                "results": scan_results
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _run_dragon_v_tests(self, target: str) -> Dict[str, Any]:
        """运行Dragon-V渗透测试"""
        try:
            # 初始化渗透引擎
            exploitation_engine = ExploitationEngine(target)
            
            # 执行SQL注入测试
            sql_results = await exploitation_engine.sql_injection_exploit()
            
            # 执行文件上传测试
            file_upload_results = await exploitation_engine.file_upload_exploit()
            
            # 执行API数据提取
            api_results = await exploitation_engine.data_extraction_api()
            
            # 执行IDOR测试
            idor_results = await exploitation_engine.idor_exploit()
            
            # 执行敏感数据提取
            sensitive_data_results = await exploitation_engine.sensitive_data_extraction()
            
            return {
                "status": "completed",
                "sql_injection": sql_results,
                "file_upload": file_upload_results,
                "api_extraction": api_results,
                "idor": idor_results,
                "sensitive_data": sensitive_data_results
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _correlate_findings(self, nessus_results: Dict[str, Any], dragon_results: Dict[str, Any]) -> Dict[str, Any]:
        """智能关联分析"""
        correlation = {
            "high_risk_vulnerabilities": [],
            "exploitable_findings": [],
            "risk_assessment": {},
            "recommendations": []
        }
        
        # 提取Nessus高危漏洞
        if nessus_results.get("status") == "completed":
            nessus_data = nessus_results.get("results", {})
            if nessus_data.get("status") == "success":
                scan_results = nessus_data.get("scan_results", {})
                
                # 分析严重漏洞
                vulnerabilities = scan_results.get("vulnerabilities", [])
                for vuln in vulnerabilities:
                    severity = vuln.get("severity", 0)
                    if severity >= 3:  # 高危及以上
                        correlation["high_risk_vulnerabilities"].append({
                            "source": "nessus",
                            "severity": severity,
                            "name": vuln.get("plugin_name", "未知"),
                            "description": vuln.get("description", "无描述")
                        })
        
        # 提取Dragon-V可利用发现
        if dragon_results.get("status") == "completed":
            if dragon_results.get("sql_injection", {}).get("exploited"):
                correlation["exploitable_findings"].append({
                    "type": "sql_injection",
                    "source": "dragon_v",
                    "severity": 4,
                    "description": "发现SQL注入漏洞"
                })
            
            if dragon_results.get("file_upload", {}).get("exploited"):
                correlation["exploitable_findings"].append({
                    "type": "file_upload",
                    "source": "dragon_v",
                    "severity": 4,
                    "description": "发现文件上传漏洞"
                })
            
            if dragon_results.get("idor", {}).get("exploited"):
                correlation["exploitable_findings"].append({
                    "type": "idor",
                    "source": "dragon_v",
                    "severity": 3,
                    "description": "发现IDOR漏洞"
                })
        
        # 风险评估
        total_high_risk = len(correlation["high_risk_vulnerabilities"])
        total_exploitable = len(correlation["exploitable_findings"])
        
        risk_level = "低"
        if total_high_risk > 5 or total_exploitable > 2:
            risk_level = "极高"
        elif total_high_risk > 2 or total_exploitable > 0:
            risk_level = "高"
        elif total_high_risk > 0:
            risk_level = "中"
        
        correlation["risk_assessment"] = {
            "level": risk_level,
            "high_risk_count": total_high_risk,
            "exploitable_count": total_exploitable,
            "total_findings": total_high_risk + total_exploitable
        }
        
        # 生成建议
        if total_high_risk > 0:
            correlation["recommendations"].append("立即修复高危漏洞")
        if total_exploitable > 0:
            correlation["recommendations"].append("优先处理可利用漏洞")
        if risk_level == "极高":
            correlation["recommendations"].append("系统存在严重安全风险，建议立即采取措施")
        
        return correlation
    
    async def _generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """生成综合报告"""
        target = results["target"]
        timestamp = results["timestamp"]
        
        # 创建HTML报告
        html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>综合安全评估报告 - Dragon-V + Nessus</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; font-weight: bold; }}
        .risk-low {{ color: #27ae60; font-weight: bold; }}
        .vulnerability {{ border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; background: #fdf2f2; }}
        .exploit {{ border-left: 4px solid #f39c12; padding: 10px; margin: 10px 0; background: #fef9e7; }}
        .recommendation {{ background: #e8f4fd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 综合安全评估报告</h1>
        <p><strong>目标:</strong> {target}</p>
        <p><strong>扫描时间:</strong> {timestamp}</p>
        <p><strong>扫描策略:</strong> {results['scan_policy']} | <strong>强度:</strong> {results['intensity']}</p>
    </div>
    
    <div class="section">
        <h2>📊 风险评估摘要</h2>
        <div class="stats">
            <div class="stat-card">
                <h3>风险等级</h3>
                <p class="risk-{results['phases']['correlation_analysis']['risk_assessment']['level']}">
                    {results['phases']['correlation_analysis']['risk_assessment']['level']}
                </p>
            </div>
            <div class="stat-card">
                <h3>高危漏洞</h3>
                <p>{results['phases']['correlation_analysis']['risk_assessment']['high_risk_count']}</p>
            </div>
            <div class="stat-card">
                <h3>可利用漏洞</h3>
                <p>{results['phases']['correlation_analysis']['risk_assessment']['exploitable_count']}</p>
            </div>
            <div class="stat-card">
                <h3>总发现</h3>
                <p>{results['phases']['correlation_analysis']['risk_assessment']['total_findings']}</p>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>⚠️ 高危漏洞</h2>
        """
        
        # 高危漏洞列表
        for vuln in results['phases']['correlation_analysis']['high_risk_vulnerabilities']:
            html_report += f"""
        <div class="vulnerability">
            <h4>{vuln['name']} [{vuln['source']}]</h4>
            <p><strong>严重性:</strong> {vuln['severity']}/4</p>
            <p>{vuln['description'][:200]}...</p>
        </div>
            """
        
        html_report += """
    </div>
    
    <div class="section">
        <h2>🎯 可利用发现</h2>
        """
        
        # 可利用漏洞列表
        for exploit in results['phases']['correlation_analysis']['exploitable_findings']:
            html_report += f"""
        <div class="exploit">
            <h4>{exploit['type']} [{exploit['source']}]</h4>
            <p><strong>严重性:</strong> {exploit['severity']}/4</p>
            <p>{exploit['description']}</p>
        </div>
            """
        
        html_report += """
    </div>
    
    <div class="section">
        <h2>💡 安全建议</h2>
        """
        
        # 建议列表
        for rec in results['phases']['correlation_analysis']['recommendations']:
            html_report += f"""
        <div class="recommendation">
            <p>✅ {rec}</p>
        </div>
            """
        
        html_report += """
    </div>
    
    <div class="section">
        <h2>📋 详细信息</h2>
        <p><strong>Nessus扫描状态:</strong> {nessus_status}</p>
        <p><strong>Dragon-V测试状态:</strong> {dragon_status}</p>
        <p><strong>报告生成时间:</strong> {report_time}</p>
    </div>
</body>
</html>
        """.format(
            nessus_status=results['phases']['nessus_scan'].get('status', 'unknown'),
            dragon_status=results['phases']['dragon_v_tests'].get('status', 'unknown'),
            report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # 保存报告
        filename = f"comprehensive_security_assessment_{target.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        return filename

async def test_integration():
    """测试集成功能"""
    print("🧪 测试Dragon-V + Nessus集成...")
    
    integration = DragonNessusIntegration()
    
    # 测试目标
    target = "example.com"
    
    # 执行综合评估
    results = await integration.comprehensive_security_assessment(
        target=target,
        scan_policy="web_application",
        intensity="normal"
    )
    
    print(f"综合评估结果: {results}")
    
    if "final_report" in results:
        print(f"✅ 报告已生成: {results['final_report']}")
    else:
        print("❌ 报告生成失败")

if __name__ == "__main__":
    asyncio.run(test_integration())