#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
显示最终报告摘要
"""

import json

def show_report_summary():
    """显示报告摘要"""
    with open('FINAL_PENETRATION_REPORT.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print("🎯 最终渗透测试报告摘要")
    print("="*60)
    print(f"任务状态: {report['mission_status']}")
    print()
    
    print("目标利用结果:")
    for target in report['targets_exploited']:
        print(f"  🎯 {target['target']}")
        print(f"     漏洞类型: {target['vulnerability']}")
        print(f"     状态: {target['status']}")
        print(f"     风险等级: {target['risk_level']}")
        print()
    
    summary = report['extracted_data_summary']
    print("数据提取统计:")
    print(f"  端点数量: {summary['total_endpoints_exploited']}")
    print(f"  数据总量: {summary['total_data_size_bytes']} 字节")
    print(f"  高风险发现: {summary['high_risk_findings']}")
    print(f"  SQL注入成功: {summary['sql_injection_success']}")
    print(f"  WAF绕过成功: {summary['waf_bypass_success']}")
    print()
    
    print("业务影响:")
    for key, value in report['business_impact'].items():
        print(f"  {key}: {value}")
    print()
    
    print("技术细节:")
    for key, value in report['technical_details'].items():
        if isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
        else:
            print(f"  {key}: {value}")
    print()
    
    print("证据文件数量:", len(report['evidence_files']))
    print("完整报告: FINAL_PENETRATION_REPORT.json")

if __name__ == "__main__":
    show_report_summary()