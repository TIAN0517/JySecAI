#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nessus扫描管理界面
Nessus Scan Management UI

提供图形化界面来管理Nessus扫描任务和查看结果
"""

import asyncio
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入Nessus模块
from nessus_integration import nessus_manager
from nessus_config_enhanced import scan_config_manager, PRESET_CONFIGS
from nessus_dragon_integration import DragonNessusIntegration

class NessusManagementUI:
    """Nessus管理界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Dragon-V Nessus管理器 v2.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # 初始化管理器
        self.nessus_manager = nessus_manager
        self.dragon_integration = DragonNessusIntegration()
        
        # 当前扫描状态
        self.current_scans = {}
        self.scan_results = {}
        
        # 创建界面
        self.create_ui()
        
        # 启动时检查服务器状态
        self.root.after(1000, self.check_servers_async)
    
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔒 Dragon-V Nessus管理器", 
                               font=('Arial', 16, 'bold'), foreground='#3498db')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 服务器状态区域
        self.create_server_status_area(main_frame)
        
        # 扫描配置区域
        self.create_scan_config_area(main_frame)
        
        # 扫描控制区域
        self.create_scan_control_area(main_frame)
        
        # 结果展示区域
        self.create_results_area(main_frame)
        
        # 日志区域
        self.create_log_area(main_frame)
    
    def create_server_status_area(self, parent):
        """创建服务器状态区域"""
        status_frame = ttk.LabelFrame(parent, text="🖥️ 服务器状态", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        self.server_status_labels = {}
        
        for i, server_name in enumerate(self.nessus_manager.servers):
            # 服务器名称
            name_label = ttk.Label(status_frame, text=f"服务器 {i+1}:")
            name_label.grid(row=i, column=0, sticky=tk.W, padx=(0, 10))
            
            # 状态标签
            status_label = ttk.Label(status_frame, text="检查中...", foreground='gray')
            status_label.grid(row=i, column=1, sticky=tk.W)
            self.server_status_labels[server_name] = status_label
            
            # 刷新按钮
            refresh_btn = ttk.Button(status_frame, text="刷新", 
                                   command=lambda s=server_name: self.check_server_async(s))
            refresh_btn.grid(row=i, column=2, padx=(10, 0))
    
    def create_scan_config_area(self, parent):
        """创建扫描配置区域"""
        config_frame = ttk.LabelFrame(parent, text="⚙️ 扫描配置", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # 目标输入
        ttk.Label(config_frame, text="目标:").grid(row=0, column=0, sticky=tk.W)
        self.target_entry = ttk.Entry(config_frame, width=50)
        self.target_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        self.target_entry.insert(0, "example.com")
        
        # 扫描策略
        ttk.Label(config_frame, text="扫描策略:").grid(row=1, column=0, sticky=tk.W)
        self.policy_var = tk.StringVar(value="web_application")
        policy_combo = ttk.Combobox(config_frame, textvariable=self.policy_var, 
                                   values=["web_application", "network", "malware", "mobile", "database", "cloud"])
        policy_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        
        # 扫描强度
        ttk.Label(config_frame, text="扫描强度:").grid(row=2, column=0, sticky=tk.W)
        self.intensity_var = tk.StringVar(value="normal")
        intensity_combo = ttk.Combobox(config_frame, textvariable=self.intensity_var,
                                      values=["light", "normal", "aggressive", "extreme"])
        intensity_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        
        # 预设配置
        ttk.Label(config_frame, text="预设配置:").grid(row=3, column=0, sticky=tk.W)
        self.preset_var = tk.StringVar(value="enterprise_web")
        preset_combo = ttk.Combobox(config_frame, textvariable=self.preset_var,
                                   values=list(PRESET_CONFIGS.keys()))
        preset_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        preset_combo.bind('<<ComboboxSelected>>', self.on_preset_selected)
    
    def create_scan_control_area(self, parent):
        """创建扫描控制区域"""
        control_frame = ttk.LabelFrame(parent, text="🎯 扫描控制", padding="10")
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 快速扫描按钮
        quick_scan_btn = ttk.Button(control_frame, text="🚀 快速扫描", 
                                   command=self.quick_scan_async)
        quick_scan_btn.grid(row=0, column=0, padx=(0, 10))
        
        # 综合评估按钮
        comprehensive_btn = ttk.Button(control_frame, text="🔍 综合安全评估", 
                                      command=self.comprehensive_assessment_async)
        comprehensive_btn.grid(row=0, column=1, padx=(0, 10))
        
        # 自定义扫描按钮
        custom_scan_btn = ttk.Button(control_frame, text="⚡ 自定义扫描", 
                                    command=self.custom_scan_async)
        custom_scan_btn.grid(row=0, column=2, padx=(0, 10))
        
        # 停止扫描按钮
        stop_scan_btn = ttk.Button(control_frame, text="⏹️ 停止扫描", 
                                  command=self.stop_scans)
        stop_scan_btn.grid(row=0, column=3)
    
    def create_results_area(self, parent):
        """创建结果展示区域"""
        results_frame = ttk.LabelFrame(parent, text="📊 扫描结果", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # 创建笔记本控件
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 漏洞列表标签页
        vuln_frame = ttk.Frame(self.notebook)
        self.notebook.add(vuln_frame, text="漏洞列表")
        
        # 漏洞表格
        columns = ('severity', 'name', 'source', 'description')
        self.vuln_tree = ttk.Treeview(vuln_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        self.vuln_tree.heading('severity', text='严重性')
        self.vuln_tree.heading('name', text='漏洞名称')
        self.vuln_tree.heading('source', text='来源')
        self.vuln_tree.heading('description', text='描述')
        
        # 设置列宽
        self.vuln_tree.column('severity', width=80)
        self.vuln_tree.column('name', width=200)
        self.vuln_tree.column('source', width=100)
        self.vuln_tree.column('description', width=400)
        
        # 滚动条
        vuln_scroll = ttk.Scrollbar(vuln_frame, orient=tk.VERTICAL, command=self.vuln_tree.yview)
        self.vuln_tree.configure(yscrollcommand=vuln_scroll.set)
        
        self.vuln_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vuln_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        vuln_frame.columnconfigure(0, weight=1)
        vuln_frame.rowconfigure(0, weight=1)
        
        # 统计信息标签页
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="统计信息")
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, width=80, height=15)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
    
    def create_log_area(self, parent):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(parent, text="📋 操作日志", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=8)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 清空日志按钮
        clear_log_btn = ttk.Button(log_frame, text="清空日志", command=self.clear_log)
        clear_log_btn.grid(row=1, column=0, pady=(5, 0))
    
    def log_message(self, message: str):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    async def check_server_health_async(self, server_name: str):
        """异步检查服务器健康状态"""
        try:
            health = await self.nessus_manager.check_server_health(server_name)
            status_info = self.nessus_manager.server_status[server_name]
            
            # 更新UI
            self.root.after(0, self.update_server_status, server_name, health, status_info)
            
        except Exception as e:
            self.root.after(0, self.log_message, f"检查服务器 {server_name} 失败: {e}")
    
    def check_server_async(self, server_name: str):
        """异步检查服务器"""
        self.log_message(f"检查服务器 {server_name} 状态...")
        asyncio.create_task(self.check_server_health_async(server_name))
    
    def check_servers_async(self):
        """异步检查所有服务器"""
        self.log_message("检查所有服务器状态...")
        for server_name in self.nessus_manager.servers:
            asyncio.create_task(self.check_server_health_async(server_name))
    
    def update_server_status(self, server_name: str, health: bool, status_info: Dict[str, Any]):
        """更新服务器状态显示"""
        label = self.server_status_labels[server_name]
        
        if health:
            label.config(text="✅ 在线", foreground='green')
            self.log_message(f"服务器 {server_name} 状态: 在线")
        else:
            label.config(text="❌ 离线", foreground='red')
            error_msg = status_info.get('error', '未知错误')
            self.log_message(f"服务器 {server_name} 状态: 离线 - {error_msg}")
    
    def on_preset_selected(self, event):
        """预设配置选择事件"""
        preset = self.preset_var.get()
        if preset in PRESET_CONFIGS:
            config = PRESET_CONFIGS[preset]
            self.log_message(f"选择预设配置: {config['name']}")
    
    async def quick_scan_async(self):
        """异步快速扫描"""
        target = self.target_entry.get().strip()
        if not target:
            self.root.after(0, lambda: messagebox.showerror("错误", "请输入目标地址"))
            return
        
        self.log_message(f"开始快速扫描: {target}")
        
        try:
            best_server = await self.nessus_manager.get_best_server()
            if not best_server:
                self.root.after(0, lambda: messagebox.showerror("错误", "没有可用的Nessus服务器"))
                return
            
            # 执行扫描
            results = await best_server.full_scan_workflow(target, f"快速扫描 - {target}")
            
            # 更新结果
            self.root.after(0, self.update_scan_results, results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"扫描失败: {e}"))
    
    async def comprehensive_assessment_async(self):
        """异步综合安全评估"""
        target = self.target_entry.get().strip()
        if not target:
            self.root.after(0, lambda: messagebox.showerror("错误", "请输入目标地址"))
            return
        
        self.log_message(f"开始综合安全评估: {target}")
        
        try:
            results = await self.dragon_integration.comprehensive_security_assessment(
                target=target,
                scan_policy=self.policy_var.get(),
                intensity=self.intensity_var.get()
            )
            
            # 更新结果
            self.root.after(0, self.update_comprehensive_results, results)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"综合评估失败: {e}"))
    
    async def custom_scan_async(self):
        """异步自定义扫描"""
        # 实现自定义扫描逻辑
        self.log_message("自定义扫描功能开发中...")
    
    def stop_scans(self):
        """停止所有扫描"""
        self.log_message("停止所有扫描任务...")
        # 实现停止扫描逻辑
    
    def update_scan_results(self, results: Dict[str, Any]):
        """更新扫描结果"""
        if results.get('status') == 'success':
            self.log_message("扫描完成!")
            
            # 更新漏洞列表
            self.update_vulnerability_list(results)
            
            # 更新统计信息
            self.update_statistics(results)
            
        else:
            self.log_message(f"扫描失败: {results.get('message', '未知错误')}")
    
    def update_comprehensive_results(self, results: Dict[str, Any]):
        """更新综合评估结果"""
        self.log_message("综合安全评估完成!")
        
        # 显示报告路径
        if 'final_report' in results:
            self.log_message(f"报告已生成: {results['final_report']}")
    
    def update_vulnerability_list(self, results: Dict[str, Any]):
        """更新漏洞列表"""
        # 清空现有数据
        for item in self.vuln_tree.get_children():
            self.vuln_tree.delete(item)
        
        # 添加新数据
        scan_results = results.get('scan_results', {})
        vulnerabilities = scan_results.get('vulnerabilities', [])
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 0)
            severity_text = {4: '严重', 3: '高危', 2: '中危', 1: '低危', 0: '信息'}.get(severity, '未知')
            
            self.vuln_tree.insert('', tk.END, values=(
                severity_text,
                vuln.get('plugin_name', '未知'),
                'Nessus',
                vuln.get('description', '无描述')[:100] + '...'
            ))
    
    def update_statistics(self, results: Dict[str, Any]):
        """更新统计信息"""
        scan_results = results.get('scan_results', {})
        severity = scan_results.get('severity_summary', {})
        
        stats_text = f"""扫描统计信息:

目标: {results.get('target', '未知')}
扫描ID: {results.get('scan_id', '未知')}
扫描时间: {results.get('timestamp', '未知')}

漏洞统计:
- 总计: {scan_results.get('total_vulnerabilities', 0)} 个漏洞
- 严重: {severity.get('critical', 0)} 个
- 高危: {severity.get('high', 0)} 个  
- 中危: {severity.get('medium', 0)} 个
- 低危: {severity.get('low', 0)} 个
- 信息: {severity.get('info', 0)} 个

风险评估:
- 风险等级: {self.calculate_risk_level(severity)}
- 建议措施: {self.get_recommendations(severity)}
"""
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def calculate_risk_level(self, severity: Dict[str, int]) -> str:
        """计算风险等级"""
        critical = severity.get('critical', 0)
        high = severity.get('high', 0)
        
        if critical > 0:
            return "极高风险"
        elif high > 2:
            return "高风险"
        elif high > 0:
            return "中风险"
        else:
            return "低风险"
    
    def get_recommendations(self, severity: Dict[str, int]) -> str:
        """获取建议措施"""
        critical = severity.get('critical', 0)
        high = severity.get('high', 0)
        
        if critical > 0:
            return "立即修复严重漏洞"
        elif high > 2:
            return "优先处理高危漏洞"
        elif high > 0:
            return "安排漏洞修复计划"
        else:
            return "保持安全监控"
    
    def quick_scan_async(self):
        """包装快速扫描为异步"""
        asyncio.create_task(self.quick_scan_async())
    
    def comprehensive_assessment_async(self):
        """包装综合评估为异步"""
        asyncio.create_task(self.comprehensive_assessment_async())
    
    def custom_scan_async(self):
        """包装自定义扫描为异步"""
        asyncio.create_task(self.custom_scan_async())

def main():
    """主函数"""
    root = tk.Tk()
    app = NessusManagementUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()