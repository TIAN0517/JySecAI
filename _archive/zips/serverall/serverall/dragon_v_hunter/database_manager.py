"""
数据库管理和查询工具
用于管理和分析越南目标收集的数据
"""

import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, List, Any, Optional
from data_to_postgres import DataToPostgres

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.db_processor = DataToPostgres()

    def connect(self):
        """建立数据库连接"""
        return self.db_processor.connect()

    def disconnect(self):
        """关闭数据库连接"""
        self.db_processor.disconnect()

    def get_all_data_summary(self) -> Dict[str, Any]:
        """获取所有数据的汇总信息"""
        if not self.connect():
            return {}

        try:
            summary = {}

            # 客户数据汇总
            self.db_processor.cursor.execute("""
                SELECT
                    COUNT(*) as total_customers,
                    COUNT(DISTINCT source_company) as companies,
                    COUNT(CASE WHEN trang_thai = 'ACTIVE' THEN 1 END) as active_customers,
                    COUNT(CASE WHEN gioi_tinh = 'Nam' THEN 1 END) as male_customers,
                    COUNT(CASE WHEN gioi_tinh = 'Nu' THEN 1 END) as female_customers
                FROM vietnam_customers
            """)
            customer_summary = self.db_processor.cursor.fetchone()
            summary['customers'] = {
                'total': customer_summary[0],
                'companies': customer_summary[1],
                'active': customer_summary[2],
                'male': customer_summary[3],
                'female': customer_summary[4]
            }

            # 订单数据汇总
            self.db_processor.cursor.execute("""
                SELECT
                    COUNT(*) as total_orders,
                    SUM(gia_tri) as total_value,
                    COUNT(DISTINCT tinh_trang) as status_types,
                    AVG(gia_tri) as avg_value
                FROM vietnam_orders
            """)
            order_summary = self.db_processor.cursor.fetchone()
            summary['orders'] = {
                'total': order_summary[0],
                'total_value': float(order_summary[1]) if order_summary[1] else 0,
                'status_types': order_summary[2],
                'avg_value': float(order_summary[3]) if order_summary[3] else 0
            }

            # 支付数据汇总
            self.db_processor.cursor.execute("""
                SELECT
                    COUNT(*) as total_payments,
                    SUM(so_tien) as total_amount,
                    COUNT(DISTINCT trang_thai) as status_types
                FROM vietnam_payments
            """)
            payment_summary = self.db_processor.cursor.fetchone()
            summary['payments'] = {
                'total': payment_summary[0],
                'total_amount': float(payment_summary[1]) if payment_summary[1] else 0,
                'status_types': payment_summary[2]
            }

            # 利用日志汇总
            self.db_processor.cursor.execute("""
                SELECT
                    COUNT(*) as total_exploits,
                    COUNT(CASE WHEN success = TRUE THEN 1 END) as successful_exploits,
                    COUNT(DISTINCT target_company) as companies,
                    COUNT(DISTINCT vulnerability_type) as vulnerability_types
                FROM exploitation_logs
            """)
            exploit_summary = self.db_processor.cursor.fetchone()
            summary['exploits'] = {
                'total': exploit_summary[0],
                'successful': exploit_summary[1],
                'success_rate': (exploit_summary[1] / exploit_summary[0] * 100) if exploit_summary[0] > 0 else 0,
                'companies': exploit_summary[2],
                'vulnerability_types': exploit_summary[3]
            }

            # 财务影响汇总
            self.db_processor.cursor.execute("""
                SELECT
                    target_company,
                    vulnerability_type,
                    SUM(impact_vnd) as total_impact,
                    COUNT(*) as exploit_count
                FROM exploitation_logs
                WHERE success = TRUE
                GROUP BY target_company, vulnerability_type
                ORDER BY total_impact DESC
            """)
            financial_summary = self.db_processor.cursor.fetchall()
            summary['financial_impact'] = financial_summary

            self.db_processor.conn.commit()
            return summary

        except Exception as e:
            logger.error(f"获取数据汇总失败: {e}")
            self.db_processor.conn.rollback()
            return {}
        finally:
            self.disconnect()

    def get_company_detailed_data(self, company_name: str) -> Dict[str, Any]:
        """获取特定公司的详细数据"""
        if not self.connect():
            return {}

        try:
            detailed_data = {}

            # 客户数据
            self.db_processor.cursor.execute("""
                SELECT ma_kh, ten_kh, so_dien_thoai, dia_chi, email, ngay_sinh, gioi_tinh, trang_thai
                FROM vietnam_customers
                WHERE source_company = %s
                ORDER BY ngay_sinh DESC
            """, (company_name,))
            customers = self.db_processor.cursor.fetchall()
            detailed_data['customers'] = customers

            # 订单数据
            self.db_processor.cursor.execute("""
                SELECT ma_don, ma_kh, tinh_trang, gia_tri, ngay_dat, ngay_giao
                FROM vietnam_orders
                WHERE source_company = %s
                ORDER BY ngay_dat DESC
            """, (company_name,))
            orders = self.db_processor.cursor.fetchall()
            detailed_data['orders'] = orders

            # 支付数据
            self.db_processor.cursor.execute("""
                SELECT ma_thanh_toan, ma_don, so_tien, trang_thai, ngay_thanh_toan
                FROM vietnam_payments
                WHERE source_company = %s
                ORDER BY ngay_thanh_toan DESC
            """, (company_name,))
            payments = self.db_processor.cursor.fetchall()
            detailed_data['payments'] = payments

            # 利用日志
            self.db_processor.cursor.execute("""
                SELECT vulnerability_type, endpoint, payload, impact_vnd, extraction_date
                FROM exploitation_logs
                WHERE target_company = %s AND success = TRUE
                ORDER BY extraction_date DESC
            """, (company_name,))
            exploits = self.db_processor.cursor.fetchall()
            detailed_data['exploits'] = exploits

            self.db_processor.conn.commit()
            return detailed_data

        except Exception as e:
            logger.error(f"获取公司详细数据失败: {e}")
            self.db_processor.conn.rollback()
            return {}
        finally:
            self.disconnect()

    def export_to_csv(self, output_dir: str = "exports"):
        """导出数据到CSV文件"""
        import os

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if not self.connect():
            return False

        try:
            # 导出客户数据
            self.db_processor.cursor.execute("""
                SELECT * FROM vietnam_customers ORDER BY extraction_date DESC
            """)
            customers = self.db_processor.cursor.fetchall()
            columns = [desc[0] for desc in self.db_processor.cursor.description]

            df_customers = pd.DataFrame(customers, columns=columns)
            df_customers.to_csv(f"{output_dir}/vietnam_customers.csv", index=False, encoding='utf-8')

            # 导出订单数据
            self.db_processor.cursor.execute("""
                SELECT * FROM vietnam_orders ORDER BY extraction_date DESC
            """)
            orders = self.db_processor.cursor.fetchall()
            columns = [desc[0] for desc in self.db_processor.cursor.description]

            df_orders = pd.DataFrame(orders, columns=columns)
            df_orders.to_csv(f"{output_dir}/vietnam_orders.csv", index=False, encoding='utf-8')

            # 导出支付数据
            self.db_processor.cursor.execute("""
                SELECT * FROM vietnam_payments ORDER BY extraction_date DESC
            """)
            payments = self.db_processor.cursor.fetchall()
            columns = [desc[0] for desc in self.db_processor.cursor.description]

            df_payments = pd.DataFrame(payments, columns=columns)
            df_payments.to_csv(f"{output_dir}/vietnam_payments.csv", index=False, encoding='utf-8')

            # 导出利用日志
            self.db_processor.cursor.execute("""
                SELECT * FROM exploitation_logs ORDER BY extraction_date DESC
            """)
            exploits = self.db_processor.cursor.fetchall()
            columns = [desc[0] for desc in self.db_processor.cursor.description]

            df_exploits = pd.DataFrame(exploits, columns=columns)
            df_exploits.to_csv(f"{output_dir}/exploitation_logs.csv", index=False, encoding='utf-8')

            self.db_processor.conn.commit()
            logger.info(f"✅ 数据已导出到 {output_dir} 目录")
            return True

        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            self.db_processor.conn.rollback()
            return False
        finally:
            self.disconnect()

    def generate_analysis_report(self) -> str:
        """生成分析报告"""
        summary = self.get_all_data_summary()

        if not summary:
            return "无法获取数据汇总"

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("📊 越南目标数据库分析报告")
        report_lines.append("=" * 60)
        report_lines.append("")

        # 整体统计
        report_lines.append("【整体统计】")
        report_lines.append(f"总客户数量: {summary['customers']['total']}")
        report_lines.append(f"涉及公司: {summary['customers']['companies']} 家")
        report_lines.append(f"活跃客户: {summary['customers']['active']}")
        report_lines.append(f"男性客户: {summary['customers']['male']}")
        report_lines.append(f"女性客户: {summary['customers']['female']}")
        report_lines.append("")

        report_lines.append(f"总订单数量: {summary['orders']['total']}")
        report_lines.append(f"订单总价值: {summary['orders']['total_value']:,.0f} VND")
        report_lines.append(f"平均订单价值: {summary['orders']['avg_value']:,.0f} VND")
        report_lines.append(f"订单状态类型: {summary['orders']['status_types']} 种")
        report_lines.append("")

        report_lines.append(f"总支付数量: {summary['payments']['total']}")
        report_lines.append(f"支付总金额: {summary['payments']['total_amount']:,.0f} VND")
        report_lines.append(f"支付状态类型: {summary['payments']['status_types']} 种")
        report_lines.append("")

        # 利用统计
        report_lines.append("【渗透测试统计】")
        report_lines.append(f"总测试次数: {summary['exploits']['total']}")
        report_lines.append(f"成功利用: {summary['exploits']['successful']}")
        report_lines.append(f"成功率: {summary['exploits']['success_rate']:.1f}%")
        report_lines.append(f"目标公司: {summary['exploits']['companies']} 家")
        report_lines.append(f"漏洞类型: {summary['exploits']['vulnerability_types']} 种")
        report_lines.append("")

        # 财务影响分析
        report_lines.append("【财务影响分析】")
        if 'financial_impact' in summary and summary['financial_impact']:
            for item in summary['financial_impact']:
                company, vuln_type, impact, count = item
                report_lines.append(f"{company} - {vuln_type}:")
                report_lines.append(f"  损失: {impact:,.0f} VND")
                report_lines.append(f"  利用次数: {count}")
                report_lines.append("")

        # 建议和措施
        report_lines.append("【建议措施】")
        report_lines.append("基于数据分析的改进建议:")
        report_lines.append("1. 立即修复高影响漏洞")
        report_lines.append("2. 加强客户数据保护")
        report_lines.append("3. 实施支付安全监控")
        report_lines.append("4. 建立定期安全评估机制")

        report_content = "\n".join(report_lines)

        # 保存报告
        with open("database_analysis_report.txt", "w", encoding="utf-8") as f:
            f.write(report_content)

        return report_content

    def cleanup_old_data(self, days_old: int = 30):
        """清理旧数据"""
        if not self.connect():
            return False

        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            # 删除旧的利用日志
            self.db_processor.cursor.execute("""
                DELETE FROM exploitation_logs
                WHERE extraction_date < %s
                RETURNING COUNT(*)
            """, (cutoff_date,))
            deleted_logs = self.db_processor.cursor.fetchone()[0]

            # 删除旧的财务影响记录
            self.db_processor.cursor.execute("""
                DELETE FROM financial_impact
                WHERE reported_date < %s
                RETURNING COUNT(*)
            """, (cutoff_date,))
            deleted_impact = self.db_processor.cursor.fetchone()[0]

            self.db_processor.conn.commit()
            logger.info(f"✅ 清理完成: 删除 {deleted_logs} 条利用日志, {deleted_impact} 条财务记录")
            return True

        except Exception as e:
            logger.error(f"清理数据失败: {e}")
            self.db_processor.conn.rollback()
            return False
        finally:
            self.disconnect()

    def backup_database(self, backup_file: str = "database_backup.json"):
        """备份数据库到JSON文件"""
        if not self.connect():
            return False

        try:
            backup_data = {}

            # 备份所有表的数据
            tables = ['vietnam_customers', 'vietnam_orders', 'vietnam_payments', 'exploitation_logs', 'financial_impact']

            for table in tables:
                self.db_processor.cursor.execute(f"SELECT * FROM {table}")
                data = self.db_processor.cursor.fetchall()
                columns = [desc[0] for desc in self.db_processor.cursor.description]

                backup_data[table] = []
                for row in data:
                    backup_data[table].append(dict(zip(columns, row)))

            # 保存备份
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

            self.db_processor.conn.commit()
            logger.info(f"✅ 数据库备份完成: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            self.db_processor.conn.rollback()
            return False
        finally:
            self.disconnect()

def main():
    """主函数"""
    db_manager = DatabaseManager()

    print("🔧 数据库管理工具")
    print("=" * 40)

    while True:
        print("\n请选择操作:")
        print("1. 生成分析报告")
        print("2. 导出数据到CSV")
        print("3. 备份数据库")
        print("4. 清理旧数据")
        print("5. 查看特定公司数据")
        print("6. 退出")

        choice = input("\n请输入选项 (1-6): ").strip()

        if choice == '1':
            print("\n生成分析报告...")
            report = db_manager.generate_analysis_report()
            print(report)
        elif choice == '2':
            print("\n导出数据到CSV...")
            if db_manager.export_to_csv():
                print("✅ 数据导出成功")
            else:
                print("❌ 数据导出失败")
        elif choice == '3':
            print("\n备份数据库...")
            if db_manager.backup_database():
                print("✅ 数据库备份成功")
            else:
                print("❌ 数据库备份失败")
        elif choice == '4':
            days = input("输入要保留的天数 (默认30): ").strip()
            days = int(days) if days else 30
            print(f"\n清理 {days} 天前的数据...")
            if db_manager.cleanup_old_data(days):
                print("✅ 数据清理成功")
            else:
                print("❌ 数据清理失败")
        elif choice == '5':
            company = input("输入公司名称: ").strip()
            if company:
                print(f"\n获取 {company} 的详细数据...")
                data = db_manager.get_company_detailed_data(company)
                if data:
                    print(f"找到数据: 客户{len(data.get('customers', []))}, 订单{len(data.get('orders', []))}, 支付{len(data.get('payments', []))}")
                else:
                    print("未找到数据")
            else:
                print("公司名称不能为空")
        elif choice == '6':
            print("👋 退出程序")
            break
        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    main()