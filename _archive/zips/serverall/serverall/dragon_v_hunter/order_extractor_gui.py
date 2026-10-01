import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime, timedelta
import threading
import os

class OrderExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("越南订单数据提取工具")
        self.root.geometry("800x600")

        # 样式
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.setup_ui()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="越南订单数据提取工具",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # 日期选择框架
        date_frame = ttk.LabelFrame(main_frame, text="日期设置", padding="10")
        date_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        # 开始日期
        ttk.Label(date_frame, text="开始日期:").grid(row=0, column=0, sticky=tk.W)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=0, column=1, padx=5)
        self.start_date_entry.insert(0, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))

        # 结束日期
        ttk.Label(date_frame, text="结束日期:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=15)
        self.end_date_entry.grid(row=0, column=3, padx=5)
        self.end_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))

        # 快速选择按钮
        quick_frame = ttk.Frame(date_frame)
        quick_frame.grid(row=1, column=0, columnspan=4, pady=5)

        ttk.Button(quick_frame, text="今天", command=self.set_today).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="昨天", command=self.set_yesterday).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="最近7天", command=self.set_last_7_days).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="最近30天", command=self.set_last_30_days).pack(side=tk.LEFT, padx=2)

        # 平台选择框架
        platform_frame = ttk.LabelFrame(main_frame, text="平台选择", padding="10")
        platform_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.platform_vars = {}
        platforms = [
            ("Shopee Vietnam", "shopee"),
            ("Lazada Vietnam", "lazada"),
            ("Tiki Marketplace", "tiki"),
            ("GHTK", "ghtk"),
            ("All Platforms", "all")
        ]

        for i, (text, value) in enumerate(platforms):
            var = tk.BooleanVar(value=True if value == "all" else False)
            self.platform_vars[value] = var
            cb = ttk.Checkbutton(platform_frame, text=text, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=10, pady=2)

        # 输出格式选择
        output_frame = ttk.LabelFrame(main_frame, text="输出格式", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.output_format = tk.StringVar(value="both")
        ttk.Radiobutton(output_frame, text="JSON", variable=self.output_format,
                       value="json").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(output_frame, text="CSV", variable=self.output_format,
                       value="csv").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(output_frame, text="Both", variable=self.output_format,
                       value="both").pack(side=tk.LEFT, padx=5)

        # 提取按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)

        self.extract_btn = ttk.Button(button_frame, text="开始提取",
                                     command=self.start_extraction)
        self.extract_btn.pack(side=tk.LEFT, padx=5)

        self.cli_btn = ttk.Button(button_frame, text="CLI模式",
                                 command=self.cli_mode)
        self.cli_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=5, column=0, columnspan=3, pady=10)

        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="提取日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # 日志文本框
        self.log_text = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def set_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        self.start_date_var.set(today)
        self.end_date_var.set(today)

    def set_yesterday(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.start_date_var.set(yesterday)
        self.end_date_var.set(yesterday)

    def set_last_7_days(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        self.start_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(end_date.strftime('%Y-%m-%d'))

    def set_last_30_days(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        self.start_date_var.set(start_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(end_date.strftime('%Y-%m-%d'))

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def generate_sample_data(self, start_date, end_date):
        """生成模拟数据 - 仅用于演示"""
        self.log("生成模拟数据...")

        # 越南客户数据
        vietnamese_customers = [
            {
                'name': 'Nguyen Van Anh',
                'phone': '+84912345678',
                'email': 'nguyenvananh@email.com',
                'address': 'Ha Noi, Vietnam'
            },
            {
                'name': 'Tran Thi Binh',
                'phone': '+84987654321',
                'email': 'tranthibinh@email.com',
                'address': 'Ho Chi Minh City, Vietnam'
            },
            {
                'name': 'Le Van Cuong',
                'phone': '+84555555555',
                'email': 'levancuong@email.com',
                'address': 'Da Nang, Vietnam'
            },
            {
                'name': 'Pham Thi Dung',
                'phone': '+84333333333',
                'email': 'phamthidung@email.com',
                'address': 'Can Tho, Vietnam'
            },
            {
                'name': 'Nguyen Van Minh',
                'phone': '+84111111111',
                'email': 'nguyenvanminh@email.com',
                'address': 'Binh Duong, Vietnam'
            }
        ]

        # 产品数据
        products = [
            'iPhone 15 Pro 256GB',
            'Samsung Galaxy S24 Ultra',
            'MacBook Pro 14寸',
            'iPad Air 5',
            'Sony WH-1000XM5',
            'Apple Watch Series 9',
            'Xiaomi 14 Pro',
            'Dell XPS 15',
            'HP Spectre x360',
            'AirPods Pro 2'
        ]

        # 平台数据
        all_platforms = ['shopee', 'lazada', 'tiki', 'ghtk']
        selected_platforms = [p for p, var in self.platform_vars.items()
                           if var.get() and p != 'all']
        if not selected_platforms:
            selected_platforms = all_platforms
        elif 'all' in self.platform_vars and self.platform_vars['all'].get():
            selected_platforms = all_platforms

        all_orders = []
        order_id = 1

        # 计算需要生成的订单数量
        total_days = (datetime.strptime(end_date, '%Y-%m-%d') -
                     datetime.strptime(start_date, '%Y-%m-%d')).days + 1
        orders_per_day = 5
        total_orders = total_days * orders_per_day

        self.log(f"预计生成 {total_orders} 条订单数据...")

        # 生成订单数据
        current_date = datetime.strptime(start_date, '%Y-%m-%d')

        for day in range(total_days):
            for i in range(orders_per_day):
                customer = vietnamese_customers[i % len(vietnamese_customers)]
                product = products[i % len(products)]
                platform = selected_platforms[i % len(selected_platforms)]

                # 随机价格（越南盾）
                base_price = 10000000  # 1000万越南盾起
                price_variation = (i % 10) * 10000000  # 每个产品增加1000万
                price = base_price + price_variation

                # 随机状态
                statuses = ['processing', 'shipped', 'delivered', 'completed']
                status = statuses[i % len(statuses)]

                # 随机支付方式
                payment_methods = ['信用卡', '银行转账', '支付宝', '现金']
                payment_method = payment_methods[i % len(payment_methods)]

                # 生成订单号
                order_prefix = platform.upper()
                order_number = f"{order_prefix}{current_date.strftime('%Y%m%d')}{order_id:03d}"

                order = {
                    'order_id': order_number,
                    'customer_name': customer['name'],
                    'phone': customer['phone'],
                    'email': customer['email'],
                    'address': customer['address'],
                    'product': product,
                    'price': price,
                    'status': status,
                    'order_time': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'payment_method': payment_method,
                    'tracking_number': f"SGN{order_id:09d}VN",
                    'platform': self.get_platform_name(platform),
                    'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                all_orders.append(order)
                order_id += 1

            current_date += timedelta(days=1)

        return all_orders

    def get_platform_name(self, platform):
        platform_names = {
            'shopee': 'Shopee Vietnam',
            'lazada': 'Lazada Vietnam',
            'tiki': 'Tiki Marketplace',
            'ghtk': 'GHTK'
        }
        return platform_names.get(platform, platform)

    def save_data(self, orders, start_date, end_date):
        """保存数据到文件"""
        output_format = self.output_format.get()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format in ['json', 'both']:
            json_filename = f"vietnam_orders_{start_date}_to_{end_date}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(orders, f, ensure_ascii=False, indent=2)
            self.log(f"JSON数据已保存到: {json_filename}")

        if output_format in ['csv', 'both']:
            csv_filename = f"vietnam_orders_{start_date}_to_{end_date}_{timestamp}.csv"
            if orders:
                # 获取所有字段
                fields = orders[0].keys()
                with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(orders)
            self.log(f"CSV数据已保存到: {csv_filename}")

        return len(orders)

    def start_extraction(self):
        """开始提取数据"""
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()

        if not start_date or not end_date:
            messagebox.showerror("错误", "请选择日期范围")
            return

        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "日期格式不正确，请使用YYYY-MM-DD格式")
            return

        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return

        # 在新线程中执行提取
        thread = threading.Thread(target=self.extract_data, args=(start_date, end_date))
        thread.daemon = True
        thread.start()

    def extract_data(self, start_date, end_date):
        """执行数据提取"""
        self.extract_btn.config(state='disabled')
        self.progress['value'] = 0

        try:
            self.log("开始提取越南订单数据...")

            # 更新进度
            self.progress['value'] = 20
            self.root.update()

            # 生成数据
            orders = self.generate_sample_data(start_date, end_date)

            self.progress['value'] = 60
            self.root.update()
            self.log(f"成功生成 {len(orders)} 条订单数据")

            # 保存数据
            saved_count = self.save_data(orders, start_date, end_date)

            self.progress['value'] = 100
            self.root.update()

            self.log("数据提取完成!")
            messagebox.showinfo("成功", f"成功提取并保存了 {saved_count} 条订单数据")

        except Exception as e:
            self.log(f"提取过程中发生错误: {str(e)}")
            messagebox.showerror("错误", f"提取失败: {str(e)}")
        finally:
            self.extract_btn.config(state='normal')
            self.progress['value'] = 0

    def cli_mode(self):
        """CLI模式"""
        # 创建CLI窗口
        cli_window = tk.Toplevel(self.root)
        cli_window.title("CLI模式")
        cli_window.geometry("600x400")

        # CLI界面
        cli_frame = ttk.Frame(cli_window, padding="10")
        cli_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输入框架
        input_frame = ttk.LabelFrame(cli_frame, text="CLI参数", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(input_frame, text="开始日期 (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W)
        cli_start = ttk.Entry(input_frame, width=20)
        cli_start.grid(row=0, column=1, padx=5)
        cli_start.insert(0, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))

        ttk.Label(input_frame, text="结束日期 (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W)
        cli_end = ttk.Entry(input_frame, width=20)
        cli_end.grid(row=1, column=1, padx=5)
        cli_end.insert(0, datetime.now().strftime('%Y-%m-%d'))

        ttk.Label(input_frame, text="平台 (shopee/lazada/tiki/ghtk/all):").grid(row=2, column=0, sticky=tk.W)
        cli_platform = ttk.Entry(input_frame, width=20)
        cli_platform.grid(row=2, column=1, padx=5)
        cli_platform.insert(0, "all")

        ttk.Label(input_frame, text="输出格式 (json/csv/both):").grid(row=3, column=0, sticky=tk.W)
        cli_format = ttk.Entry(input_frame, width=20)
        cli_format.grid(row=3, column=1, padx=5)
        cli_format.insert(0, "both")

        # 执行按钮
        def run_cli():
            start_date = cli_start.get()
            end_date = cli_end.get()
            platform = cli_platform.get()
            output_format = cli_format.get()

            # 这里调用CLI逻辑
            self.cli_extract(start_date, end_date, platform, output_format)

        ttk.Button(input_frame, text="执行CLI提取", command=run_cli).grid(row=4, column=0, columnspan=2, pady=10)

        # 结果显示
        result_frame = ttk.LabelFrame(cli_frame, text="CLI输出", padding="10")
        result_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        cli_output = tk.Text(result_frame, height=15, width=70, wrap=tk.WORD)
        cli_output.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        cli_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=cli_output.yview)
        cli_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        cli_output.config(yscrollcommand=cli_scrollbar.set)

        # 重定向日志到CLI输出
        original_log = self.log
        def cli_log(message):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cli_output.insert(tk.END, f"[{timestamp}] {message}\n")
            cli_output.see(tk.END)
            cli_window.update()

        self.log = cli_log

        # 恢复原始日志函数
        def restore_log():
            self.log = original_log

        cli_window.protocol("WM_DELETE_WINDOW", lambda: [restore_log(), cli_window.destroy()])

    def cli_extract(self, start_date, end_date, platform, output_format):
        """CLI模式提取"""
        try:
            self.log(f"CLI模式开始提取...")
            self.log(f"开始日期: {start_date}")
            self.log(f"结束日期: {end_date}")
            self.log(f"平台: {platform}")
            self.log(f"输出格式: {output_format}")

            # 验证日期
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')

            # 生成数据
            self.log("生成模拟数据...")
            orders = self.generate_sample_data(start_date, end_date)

            # 过滤平台
            if platform != 'all':
                platform_name = self.get_platform_name(platform)
                orders = [o for o in orders if o['platform'] == platform_name]
                self.log(f"过滤到 {platform_name} 平台数据")

            # 保存数据
            self.log(f"保存数据，格式: {output_format}")
            saved_count = self.save_data(orders, start_date, end_date)

            self.log(f"CLI模式完成！共提取 {saved_count} 条订单")

        except Exception as e:
            self.log(f"CLI模式错误: {str(e)}")

def main():
    root = tk.Tk()
    app = OrderExtractorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()