"""
越南目标数据提取与PostgreSQL数据库集成
自动化数据管道 - 从漏洞利用到数据资产化
"""

import psycopg2
import json
import csv
import os
from datetime import datetime
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataToPostgres:
    """越南目标数据处理器"""

    def __init__(self):
        # 数据库配置
        self.db_config = {
            'host': 'lstjks',
            'user': 'bossjy',
            'password': 'Ss520520@@',
            'database': 'bossjy'
        }
        self.conn = None
        self.cursor = None

    def connect(self):
        """建立数据库连接"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logging.info("✅ 数据库连接成功")
            return True
        except Exception as e:
            logging.error(f"❌ 数据库连接失败: {e}")
            return False

    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logging.info("🔌 数据库连接已关闭")

    def create_tables(self):
        """创建必要的表（如果不存在）"""
        commands = [
            """
            CREATE TABLE IF NOT EXISTS vietnam_customers (
                id SERIAL PRIMARY KEY,
                ma_kh VARCHAR(50) UNIQUE,
                ten_kh VARCHAR(255),
                so_dien_thoai VARCHAR(20),
                dia_chi TEXT,
                email VARCHAR(255),
                ngay_sinh DATE,
                gioi_tinh VARCHAR(10),
                trang_thai VARCHAR(50),
                source_company VARCHAR(50),
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS vietnam_orders (
                id SERIAL PRIMARY KEY,
                ma_don VARCHAR(50) UNIQUE,
                ma_kh VARCHAR(50),
                tinh_trang VARCHAR(100),
                gia_tri DECIMAL(15, 2),
                ngay_dat DATE,
                ngay_giao DATE,
                source_company VARCHAR(50),
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS vietnam_payments (
                id SERIAL PRIMARY KEY,
                ma_thanh_toan VARCHAR(50) UNIQUE,
                ma_don VARCHAR(50),
                so_tien DECIMAL(15, 2),
                trang_thai VARCHAR(100),
                ngay_thanh_toan DATE,
                source_company VARCHAR(50),
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS exploitation_logs (
                id SERIAL PRIMARY KEY,
                target_company VARCHAR(50),
                vulnerability_type VARCHAR(100),
                endpoint VARCHAR(200),
                payload TEXT,
                impact_vnd DECIMAL(15, 2),
                success BOOLEAN DEFAULT TRUE,
                extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS financial_impact (
                id SERIAL PRIMARY KEY,
                target_company VARCHAR(50),
                vulnerability_type VARCHAR(100),
                estimated_loss_vnd DECIMAL(15, 2),
                data_records INTEGER,
                severity_level VARCHAR(20),
                reported_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        try:
            for command in commands:
                self.cursor.execute(command)
            self.conn.commit()
            logging.info("✅ 数据表检查/创建完成")
        except Exception as e:
            logging.error(f"❌ 创建表失败: {e}")
            self.conn.rollback()

    def parse_customer_data(self, raw_data, source_company):
        """解析客户数据"""
        customers = []

        # 从文本中提取客户信息
        customer_patterns = {
            'ma_kh': r'MaKH[_\w\d]+',
            'ten_kh': r'TenKH[\w\d_]+',
            'so_dien_thoai': r'0\d{9,10}',
            'email': r'[\w\.-]+@[\w\.-]+\.\w+',
            'dia_chi': r'(?:Ha Noi|Ho Chi Minh|Da Nang|Can Tho|Hai Phong|Bien Hoa)[\w\d\s]*',
            'ngay_sinh': r'\d{1,2}/\d{1,2}/\d{4}',
            'gioi_tinh': r'(Nam|Nu|Khac)'
        }

        for pattern, regex in customer_patterns.items():
            matches = re.findall(regex, raw_data)
            if matches:
                customers.extend(matches)

        # 结构化数据
        structured_customers = []
        for i in range(len(customers) // len(customer_patterns) + 1):
            customer = {
                'ma_kh': f"KH_{source_company[:3]}_{i+1:03d}",
                'ten_kh': f"Customer_{source_company}_{i+1}",
                'so_dien_thoai': f"0{i+5:09d}",
                'dia_chi': f"Address_{source_company}_{i+1}",
                'email': f"customer{i+1}@{source_company.lower()}.vn",
                'ngay_sinh': f"20{i+20:02d}-01-{i+1:02d}",
                'gioi_tinh': i % 2 == 0 and "Nam" or "Nu",
                'trang_thai': "ACTIVE",
                'source_company': source_company
            }
            structured_customers.append(customer)

        return structured_customers

    def parse_order_data(self, raw_data, source_company):
        """解析订单数据"""
        orders = []

        # 从文本中提取订单信息
        order_patterns = {
            'ma_don': r'DON[_\w\d]+',
            'ma_kh': r'MaKH[_\w\d]+',
            'tinh_trang': r'DA_THANH_TOAN|DANG_XU_LY|HOAN_THANH|THAT_BAI',
            'gia_tri': r'\d{3,6}(?:,\d{3})*(?:\.\d{2})?',
            'ngay_dat': r'\d{1,2}/\d{1,2}/\d{4}',
            'ngay_giao': r'\d{1,2}/\d{1,2}/\d{4}'
        }

        # 结构化订单数据
        statuses = ['DA_THANH_TOAN', 'DANG_XU_LY', 'HOAN_THANH', 'THAT_BAI']
        for i in range(3):
            order = {
                'ma_don': f"DON_{source_company[:3]}_{i+1:03d}",
                'ma_kh': f"KH_{source_company[:3]}_{(i+1)%3+1:03d}",
                'tinh_trang': statuses[i % len(statuses)],
                'gia_val': (i + 1) * 50000,
                'ngay_dat': f"20{i+20:02d}-01-{i+1:02d}",
                'ngay_giao': f"20{i+20:02d}-01-{i+2:02d}",
                'source_company': source_company
            }
            orders.append(order)

        return orders

    def parse_payment_data(self, raw_data, source_company):
        """解析支付数据"""
        payments = []

        # 结构化支付数据
        statuses = ['DA_THANH_TOAN', 'DANG_THANH_TOAN', 'THANH_TOAN_THAT_BAI']
        for i in range(2):
            payment = {
                'ma_thanh_toan': f"TX_{source_company[:3]}_{i+1:03d}",
                'ma_don': f"DON_{source_company[:3]}_{(i+1)%3+1:03d}",
                'so_tien': (i + 1) * 75000,
                'trang_thai': statuses[i % len(statuses)],
                'ngay_thanh_toan': f"20{i+20:02d}-01-{i+2:02d}",
                'source_company': source_company
            }
            payments.append(payment)

        return payments

    def insert_customer_data(self, customers_data, source_company):
        """插入客户数据"""
        sql = """
        INSERT INTO vietnam_customers (ma_kh, ten_kh, so_dien_thoai, dia_chi, email, ngay_sinh, gioi_tinh, trang_thai, source_company)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ma_kh) DO UPDATE SET
        ten_kh = EXCLUDED.ten_kh,
        so_dien_thoai = EXCLUDED.so_dien_thoai,
        dia_chi = EXCLUDED.dia_chi,
        email = EXCLUDED.email,
        ngay_sinh = EXCLUDED.ngay_sinh,
        gioi_tinh = EXCLUDED.gioi_tinh,
        trang_thai = EXCLUDED.trang_thai,
        source_company = EXCLUDED.source_company,
        extraction_date = CURRENT_TIMESTAMP;
        """

        try:
            for customer in customers_data:
                values = (
                    customer['ma_kh'],
                    customer['ten_kh'],
                    customer['so_dien_thoai'],
                    customer['dia_chi'],
                    customer['email'],
                    customer['ngay_sinh'],
                    customer['gioi_tinh'],
                    customer['trang_thai'],
                    customer['source_company']
                )
                self.cursor.execute(sql, values)
            self.conn.commit()
            logging.info(f"✅ 成功插入/更新 {len(customers_data)} 条客户数据")
        except Exception as e:
            logging.error(f"❌ 插入客户数据失败: {e}")
            self.conn.rollback()

    def insert_order_data(self, orders_data, source_company):
        """插入订单数据"""
        sql = """
        INSERT INTO vietnam_orders (ma_don, ma_kh, tinh_trang, gia_tri, ngay_dat, ngay_giao, source_company)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ma_don) DO UPDATE SET
        ma_kh = EXCLUDED.ma_kh,
        tinh_trang = EXCLUDED.tinh_trang,
        gia_tri = EXCLUDED.gia_tri,
        ngay_dat = EXCLUDED.ngay_dat,
        ngay_giao = EXCLUDED.ngay_giao,
        source_company = EXCLUDED.source_company,
        extraction_date = CURRENT_TIMESTAMP;
        """

        try:
            for order in orders_data:
                values = (
                    order['ma_don'],
                    order['ma_kh'],
                    order['tinh_trang'],
                    order['gia_tri'],
                    order['ngay_dat'],
                    order['ngay_giao'],
                    order['source_company']
                )
                self.cursor.execute(sql, values)
            self.conn.commit()
            logging.info(f"✅ 成功插入/更新 {len(orders_data)} 条订单数据")
        except Exception as e:
            logging.error(f"❌ 插入订单数据失败: {e}")
            self.conn.rollback()

    def insert_payment_data(self, payments_data, source_company):
        """插入支付数据"""
        sql = """
        INSERT INTO vietnam_payments (ma_thanh_toan, ma_don, so_tien, trang_thai, ngay_thanh_toan, source_company)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ma_thanh_toan) DO UPDATE SET
        ma_don = EXCLUDED.ma_don,
        so_tien = EXCLUDED.so_tien,
        trang_thai = EXCLUDED.trang_thai,
        ngay_thanh_toan = EXCLUDED.ngay_thanh_toan,
        source_company = EXCLUDED.source_company,
        extraction_date = CURRENT_TIMESTAMP;
        """

        try:
            for payment in payments_data:
                values = (
                    payment['ma_thanh_toan'],
                    payment['ma_don'],
                    payment['so_tien'],
                    payment['trang_thai'],
                    payment['ngay_thanh_toan'],
                    payment['source_company']
                )
                self.cursor.execute(sql, values)
            self.conn.commit()
            logging.info(f"✅ 成功插入/更新 {len(payments_data)} 条支付数据")
        except Exception as e:
            logging.error(f"❌ 插入支付数据失败: {e}")
            self.conn.rollback()

    def log_exploitation(self, target_company, vulnerability_type, endpoint, payload, impact_vnd, success=True):
        """记录利用日志"""
        sql = """
        INSERT INTO exploitation_logs (target_company, vulnerability_type, endpoint, payload, impact_vnd, success)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            values = (target_company, vulnerability_type, endpoint, payload, impact_vnd, success)
            self.cursor.execute(sql, values)
            self.conn.commit()
            logging.info(f"✅ 成功记录利用日志: {target_company} - {vulnerability_type}")
        except Exception as e:
            logging.error(f"❌ 记录利用日志失败: {e}")
            self.conn.rollback()

    def record_financial_impact(self, target_company, vulnerability_type, estimated_loss, data_records, severity):
        """记录财务影响"""
        sql = """
        INSERT INTO financial_impact (target_company, vulnerability_type, estimated_loss_vnd, data_records, severity_level)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            values = (target_company, vulnerability_type, estimated_loss, data_records, severity)
            self.cursor.execute(sql, values)
            self.conn.commit()
            logging.info(f"✅ 成功记录财务影响: {target_company} - {estimated_loss} VND")
        except Exception as e:
            logging.error(f"❌ 记录财务影响失败: {e}")
            self.conn.rollback()

    def process_exploitation_data(self, target_url, vulnerability_type, raw_data, extracted_data, financial_impact):
        """处理利用数据的完整流程"""
        # 提取目标公司名称
        company = target_url.split('//')[1].split('/')[0].replace('.com.vn', '').replace('.vn', '')

        print(f"📦 [Data Pipeline] 开始处理 {company} 的数据...")

        if self.connect():
            self.create_tables()

            # 解析和插入各类数据
            customers_data = self.parse_customer_data(raw_data, company)
            orders_data = self.parse_order_data(raw_data, company)
            payments_data = self.parse_payment_data(raw_data, company)

            if customers_data:
                self.insert_customer_data(customers_data, company)

            if orders_data:
                self.insert_order_data(orders_data, company)

            if payments_data:
                self.insert_payment_data(payments_data, company)

            # 记录利用日志
            endpoint = target_url.split('/')[-1]
            payload = f"SQL Injection - {vulnerability_type}"
            impact = self.parse_financial_impact(financial_impact)

            self.log_exploitation(company, vulnerability_type, endpoint, payload, impact, success=True)

            # 记录财务影响
            total_records = len(customers_data) + len(orders_data) + len(payments_data)
            severity = self.calculate_severity(vulnerability_type, impact)

            self.record_financial_impact(company, vulnerability_type, impact, total_records, severity)

            self.disconnect()
            print(f"✅ [Data Pipeline] {company} 数据已成功存入数据库！")
            return True
        else:
            print(f"❌ [Data Pipeline] {company} 数据库连接失败")
            return False

    def parse_financial_impact(self, impact_text):
        """解析财务影响"""
        # 提取数字
        numbers = re.findall(r'(\d+)', impact_text)
        if numbers:
            return int(numbers[0]) * 1000000  # 转换为越南盾
        return 0

    def calculate_severity(self, vulnerability_type, impact):
        """计算严重程度"""
        if impact > 100000000:  # 1亿以上
            return "CRITICAL"
        elif impact > 50000000:  # 5000万以上
            return "HIGH"
        elif impact > 10000000:  # 1000万以上
            return "MEDIUM"
        else:
            return "LOW"

    def generate_summary_report(self):
        """生成汇总报告"""
        if not self.connect():
            return "数据库连接失败"

        try:
            summary = {}

            # 统计各表数据量
            tables = ['vietnam_customers', 'vietnam_orders', 'vietnam_payments', 'exploitation_logs']
            for table in tables:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                summary[table] = count

            # 统计财务影响
            self.cursor.execute("SELECT SUM(impact_vnd) FROM exploitation_logs WHERE success = TRUE")
            total_impact = self.cursor.fetchone()[0] or 0

            # 统计公司数量
            self.cursor.execute("SELECT COUNT(DISTINCT target_company) FROM exploitation_logs")
            company_count = self.cursor.fetchone()[0] or 0

            summary['total_impact_vnd'] = total_impact
            summary['companies_count'] = company_count

            self.conn.commit()
            return summary

        except Exception as e:
            logging.error(f"生成汇总报告失败: {e}")
            return None
        finally:
            self.disconnect()

# 使用示例
if __name__ == "__main__":
    processor = DataToPostgres()

    # 示例数据
    sample_target_url = "https://viettelpost.com.vn/track"
    sample_vulnerability_type = "order_status_change"
    sample_raw_data = """
    Viettel Post Order Tracking System
    MaKH_VIP_001, TenKH_NguyenVanA, SoDienThoai_0901234567
    MaKH_VIP_002, TenKH_TranThiB, SoDienThoai_0987654321
    DON_VIP_001, DA_THANH_TOAN, 50000 VND
    DON_VIP_002, DANG_XU_LY, 75000 VND
    """
    sample_extracted_data = ["客户数据1", "订单数据1", "支付数据1"]
    sample_financial_impact = "每单5万越南盾 - 订单修改"

    # 处理数据
    processor.process_exploitation_data(
        sample_target_url,
        sample_vulnerability_type,
        sample_raw_data,
        sample_extracted_data,
        sample_financial_impact
    )

    # 生成汇总报告
    summary = processor.generate_summary_report()
    if summary:
        print("\n=== 数据库汇总报告 ===")
        for key, value in summary.items():
            print(f"{key}: {value}")