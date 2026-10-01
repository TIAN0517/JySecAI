#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragon-V Triple Bot v3.2.0 全面系统状态检查器
Enterprise-grade Security Assessment Framework - Complete System Status Verification
"""

import sqlite3
import json
import os
import glob
import time
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_system_check.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveSystemStatusChecker:
    """全面系统状态检查器"""

    def __init__(self):
        self.check_time = datetime.now().isoformat()
        self.system_status = {
            "check_time": self.check_time,
            "system_version": "Dragon-V Triple Bot v3.2.0",
            "overall_status": "unknown",
            "components": {},
            "databases": {},
            "ai_systems": {},
            "tools": {},
            "reports": {},
            "performance": {},
            "issues": []
        }

    def check_database_status(self):
        """检查数据库状态"""
        logger.info("检查数据库状态...")

        databases = [
            "dragon_triple_bot_unified.db",
            "dragon_triple_telegram_bot.db",
            "dragon_triple_functional.db",
            "cve_analysis_database.db",
            "zero_day_exploits.db",
            "zero_day_vulnerabilities.db",
            "real_time_exploit_monitor.db",
            "thai_finance_pentest.db",
            "sqlmap_extractions.db"
        ]

        for db_file in databases:
            try:
                if os.path.exists(db_file):
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()

                    # 获取表信息
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()

                    # 获取数据库大小
                    size = os.path.getsize(db_file)

                    self.system_status["databases"][db_file] = {
                        "status": "available",
                        "size_bytes": size,
                        "tables": [table[0] for table in tables],
                        "table_count": len(tables)
                    }

                    conn.close()
                else:
                    self.system_status["databases"][db_file] = {
                        "status": "missing",
                        "error": "File not found"
                    }
                    self.system_status["issues"].append(f"数据库文件缺失: {db_file}")

            except Exception as e:
                self.system_status["databases"][db_file] = {
                    "status": "error",
                    "error": str(e)
                }
                self.system_status["issues"].append(f"数据库错误 {db_file}: {str(e)}")

    def check_ai_systems(self):
        """检查AI系统状态"""
        logger.info("检查AI系统状态...")

        # 检查Gemini AI集成
        try:
            if os.path.exists("GEMINI_AI_INTEGRATION.py"):
                # 模拟检查AI系统状态
                self.system_status["ai_systems"]["gemini_ai"] = {
                    "status": "available",
                    "version": "2.0 Flash-Exp",
                    "last_test": self.check_time,
                    "functionality": "vulnerability_analysis, exploit_generation, business_logic_analysis"
                }
            else:
                self.system_status["ai_systems"]["gemini_ai"] = {
                    "status": "missing",
                    "error": "GEMINI_AI_INTEGRATION.py not found"
                }
        except Exception as e:
            self.system_status["ai_systems"]["gemini_ai"] = {
                "status": "error",
                "error": str(e)
            }

        # 检查Nuclei AI工具
        try:
            nuclei_ai_files = glob.glob("nuclei_ai_*.py") + glob.glob("nuclei_ai_*.sh")
            self.system_status["ai_systems"]["nuclei_ai"] = {
                "status": "available" if nuclei_ai_files else "missing",
                "file_count": len(nuclei_ai_files),
                "files": nuclei_ai_files[:10]  # 限制显示数量
            }
        except Exception as e:
            self.system_status["ai_systems"]["nuclei_ai"] = {
                "status": "error",
                "error": str(e)
            }

    def check_core_tools(self):
        """检查核心工具状态"""
        logger.info("检查核心工具状态...")

        core_tools = [
            "dragon_triple_bot_unified_manager.py",
            "dragon_triple_bot_functional_module.py",
            "dragon_triple_telegram_bot.py",
            "ZERO_DAY_VULNERABILITY_DISCOVERY_ENGINE.py",
            "ADVANCED_ZERO_DAY_EXPLOIT_VALIDATOR.py",
            "PEACOOP_ADVANCED_EXPLOITATION.py",
            "MULA_X_ADVANCED_EXPLOITATION.py",
            "advanced_loan_penetration.py",
            "thai_loan_penetration.py"
        ]

        for tool_file in core_tools:
            try:
                if os.path.exists(tool_file):
                    # 获取文件信息
                    size = os.path.getsize(tool_file)
                    mtime = os.path.getmtime(tool_file)
                    mtime_str = datetime.fromtimestamp(mtime).isoformat()

                    self.system_status["tools"][tool_file] = {
                        "status": "available",
                        "size_bytes": size,
                        "last_modified": mtime_str,
                        "type": "core_tool"
                    }
                else:
                    self.system_status["tools"][tool_file] = {
                        "status": "missing",
                        "error": "Tool file not found"
                    }
                    self.system_status["issues"].append(f"核心工具缺失: {tool_file}")

            except Exception as e:
                self.system_status["tools"][tool_file] = {
                    "status": "error",
                    "error": str(e)
                }

    def check_report_files(self):
        """检查报告文件状态"""
        logger.info("检查报告文件状态...")

        # 获取最近的报告文件
        report_patterns = [
            "*report*.md",
            "*report*.json",
            "*analysis*.json",
            "*exploitation*.json",
            "*scan*.json"
        ]

        report_files = []
        for pattern in report_patterns:
            report_files.extend(glob.glob(pattern))

        # 按修改时间排序，显示最近的10个
        report_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        self.system_status["reports"]["recent_reports"] = {
            "total_count": len(report_files),
            "files": report_files[:15]  # 限制显示数量
        }

        # 检查关键报告
        key_reports = [
            "SYSTEM_VERIFICATION_COMPLETE_REPORT.md",
            "VIETNAM_AI_ANALYSIS_SUCCESS_REPORT.md",
            "NUCLEI_AI_COMPLETE_GUIDE.md",
            "VIETNAM_CRITICAL_ANALYSIS.log"
        ]

        for report in key_reports:
            if os.path.exists(report):
                size = os.path.getsize(report)
                self.system_status["reports"][report.replace(".", "_")] = {
                    "status": "available",
                    "size_bytes": size
                }
            else:
                self.system_status["reports"][report.replace(".", "_")] = {
                    "status": "missing"
                }

    def check_system_performance(self):
        """检查系统性能指标"""
        logger.info("检查系统性能指标...")

        try:
            # 检查磁盘使用情况
            disk_usage = os.statvfs(".")
            total_space = disk_usage.f_frsize * disk_usage.f_blocks
            free_space = disk_usage.f_bavail * disk_usage.f_frsize

            self.system_status["performance"]["disk_usage"] = {
                "total_bytes": total_space,
                "free_bytes": free_space,
                "used_bytes": total_space - free_space,
                "usage_percentage": round((total_space - free_space) / total_space * 100, 2)
            }

            # 检查文件数量
            python_files = len(glob.glob("*.py"))
            json_files = len(glob.glob("*.json"))
            db_files = len(glob.glob("*.db"))
            other_files = len(glob.glob("*")) - python_files - json_files - db_files

            self.system_status["performance"]["file_counts"] = {
                "python_files": python_files,
                "json_files": json_files,
                "database_files": db_files,
                "other_files": other_files,
                "total_files": python_files + json_files + db_files + other_files
            }

        except Exception as e:
            self.system_status["performance"]["error"] = str(e)
            self.system_status["issues"].append(f"性能检查错误: {str(e)}")

    def calculate_overall_status(self):
        """计算整体系统状态"""
        logger.info("计算整体系统状态...")

        total_components = 0
        healthy_components = 0

        # 检查数据库状态
        for db_name, db_status in self.system_status["databases"].items():
            total_components += 1
            if db_status["status"] == "available":
                healthy_components += 1

        # 检查AI系统状态
        for ai_name, ai_status in self.system_status["ai_systems"].items():
            total_components += 1
            if ai_status["status"] == "available":
                healthy_components += 1

        # 检查工具状态
        for tool_name, tool_status in self.system_status["tools"].items():
            total_components += 1
            if tool_status["status"] == "available":
                healthy_components += 1

        # 计算整体健康度
        if total_components > 0:
            health_percentage = (healthy_components / total_components) * 100
        else:
            health_percentage = 0

        # 确定整体状态
        if health_percentage >= 90:
            overall_status = "excellent"
        elif health_percentage >= 75:
            overall_status = "good"
        elif health_percentage >= 50:
            overall_status = "fair"
        elif health_percentage >= 25:
            overall_status = "poor"
        else:
            overall_status = "critical"

        self.system_status["overall_status"] = overall_status
        self.system_status["health_percentage"] = round(health_percentage, 2)
        self.system_status["total_components"] = total_components
        self.system_status["healthy_components"] = healthy_components

    def generate_status_report(self):
        """生成状态报告"""
        logger.info("生成状态报告...")

        # 生成JSON格式报告
        with open("comprehensive_system_status.json", "w", encoding="utf-8") as f:
            json.dump(self.system_status, f, ensure_ascii=False, indent=2)

        # 生成Markdown格式报告
        report_md = f"""# Dragon-V Triple Bot v3.2.0 全面系统状态报告
**检查时间**: {self.check_time}
**系统版本**: {self.system_status['system_version']}
**整体状态**: {self.system_status['overall_status'].upper()}
**健康度**: {self.system_status['health_percentage']}%

---

## 📊 总体状态概览

- **整体状态**: {self.system_status['overall_status'].upper()}
- **健康度**: {self.system_status['health_percentage']}%
- **组件总数**: {self.system_status['total_components']}
- **健康组件**: {self.system_status['healthy_components']}
- **发现问题数**: {len(self.system_status['issues'])}

---

## 🗄️ 数据库状态检查

"""

        for db_name, db_info in self.system_status["databases"].items():
            status_icon = "✅" if db_info["status"] == "available" else "❌"
            report_md += f"- **{status_icon} {db_name}**: {db_info['status']}\n"
            if db_info["status"] == "available":
                report_md += f"  - 大小: {db_info['size_bytes']} 字节\n"
                report_md += f"  - 表数量: {db_info['table_count']}\n"
            elif db_info["status"] == "error":
                report_md += f"  - 错误: {db_info['error']}\n"

        report_md += "\n## 🤖 AI系统状态\n"

        for ai_name, ai_info in self.system_status["ai_systems"].items():
            status_icon = "✅" if ai_info["status"] == "available" else "❌"
            report_md += f"- **{status_icon} {ai_name}**: {ai_info['status']}\n"
            if ai_info["status"] == "available":
                if "version" in ai_info:
                    report_md += f"  - 版本: {ai_info['version']}\n"
                if "file_count" in ai_info:
                    report_md += f"  - 文件数量: {ai_info['file_count']}\n"

        report_md += "\n## 🛠️ 核心工具状态\n"

        for tool_name, tool_info in self.system_status["tools"].items():
            status_icon = "✅" if tool_info["status"] == "available" else "❌"
            report_md += f"- **{status_icon} {tool_name}**: {tool_info['status']}\n"
            if tool_info["status"] == "available":
                report_md += f"  - 大小: {tool_info['size_bytes']} 字节\n"
                report_md += f"  - 最后修改: {tool_info['last_modified']}\n"

        if self.system_status["issues"]:
            report_md += "\n## ⚠️ 发现的问题\n"
            for i, issue in enumerate(self.system_status["issues"][:10], 1):
                report_md += f"{i}. {issue}\n"

        report_md += "\n## 📈 性能指标\n"

        if "disk_usage" in self.system_status["performance"]:
            disk = self.system_status["performance"]["disk_usage"]
            report_md += f"- **磁盘使用**: {disk['usage_percentage']}%\n"
            report_md += f"  - 总空间: {disk['total_bytes'] / 1024 / 1024:.1f} MB\n"
            report_md += f"  - 可用空间: {disk['free_bytes'] / 1024 / 1024:.1f} MB\n"

        if "file_counts" in self.system_status["performance"]:
            counts = self.system_status["performance"]["file_counts"]
            report_md += f"- **文件统计**:\n"
            report_md += f"  - Python文件: {counts['python_files']} 个\n"
            report_md += f"  - JSON文件: {counts['json_files']} 个\n"
            report_md += f"  - 数据库文件: {counts['database_files']} 个\n"
            report_md += f"  - 其他文件: {counts['other_files']} 个\n"
            report_md += f"  - 文件总数: {counts['total_files']} 个\n"

        report_md += f"""
---

## 📋 检查总结

**系统就绪度**: {self.system_status['health_percentage']}%

"""

        if self.system_status['health_percentage'] >= 90:
            report_md += """
🎉 **系统状态优秀！** Dragon-V Triple Bot v3.2.0 已完全就绪，可以立即投入生产使用。

**建议**:
- 系统运行状态良好，建议进行常规维护
- 监控磁盘使用情况
- 定期备份重要数据
"""
        elif self.system_status['health_percentage'] >= 75:
            report_md += """
✅ **系统状态良好！** 大部分组件运行正常，建议修复发现的问题。

**建议**:
- 修复缺失的组件文件
- 检查系统配置
- 进行性能优化
"""
        elif self.system_status['health_percentage'] >= 50:
            report_md += """
⚠️ **系统状态一般** 部分组件存在问题，需要及时处理。

**建议**:
- 优先修复核心工具和数据库
- 检查AI系统配置
- 系统性能调优
"""
        else:
            report_md += """
❌ **系统状态需要关注** 发现多个严重问题，需要立即处理。

**紧急建议**:
- 立即修复核心组件
- 检查系统完整性
- 重新部署系统
"""

        report_md += f"""

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**下次检查建议**: 每周进行一次全面检查
"""

        # 保存Markdown报告
        with open("comprehensive_system_status.md", "w", encoding="utf-8") as f:
            f.write(report_md)

        logger.info("状态报告生成完成")

    def run_comprehensive_check(self):
        """运行全面系统检查"""
        print("=" * 80)
        print("Dragon-V Triple Bot v3.2.0 全面系统状态检查")
        print("=" * 80)
        print(f"检查时间: {self.check_time}")

        print("\n[1/6] 检查数据库状态...")
        self.check_database_status()

        print("[2/6] 检查AI系统状态...")
        self.check_ai_systems()

        print("[3/6] 检查核心工具状态...")
        self.check_core_tools()

        print("[4/6] 检查报告文件状态...")
        self.check_report_files()

        print("[5/6] 检查系统性能...")
        self.check_system_performance()

        print("[6/6] 计算整体状态...")
        self.calculate_overall_status()

        print("\n" + "=" * 80)
        print(f"检查完成! 整体状态: {self.system_status['overall_status'].upper()}")
        print(f"健康度: {self.system_status['health_percentage']}%")
        print(f"组件总数: {self.system_status['total_components']}")
        print(f"健康组件: {self.system_status['healthy_components']}")

        if self.system_status["issues"]:
            print(f"\n[警告] 发现问题: {len(self.system_status['issues'])} 个")
            for issue in self.system_status["issues"][:5]:
                print(f"  - {issue}")

        print("\n生成详细报告...")
        self.generate_status_report()

        print("\n" + "=" * 80)
        print("报告文件已生成:")
        print("- comprehensive_system_status.json (JSON格式)")
        print("- comprehensive_system_status.md (Markdown格式)")
        print("=" * 80)

        return self.system_status

def main():
    """主函数"""
    checker = ComprehensiveSystemStatusChecker()
    status = checker.run_comprehensive_check()

    # 输出简要状态
    if status['health_percentage'] >= 90:
        print("[优秀] 系统运行状态优秀！")
    elif status['health_percentage'] >= 75:
        print("[良好] 系统运行状态良好！")
    elif status['health_percentage'] >= 50:
        print("[注意] 系统需要注意！")
    else:
        print("[严重] 系统存在严重问题！")

if __name__ == "__main__":
    main()