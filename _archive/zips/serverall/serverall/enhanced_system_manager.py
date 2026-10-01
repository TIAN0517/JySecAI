#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强系统管理器 - 提供系统稳定性和错误处理
Enhanced System Manager - Provides system stability and error handling
"""

import asyncio
import logging
import sys
import traceback
import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

class SystemManager:
    """系统管理器 - 提供监控、错误处理和资源管理"""
    
    def __init__(self, bot_name: str = "Dragon-V Bot"):
        self.bot_name = bot_name
        self.start_time = datetime.now()
        self.error_count = 0
        self.success_count = 0
        self.system_stats = {}
        
        # 配置日志
        self._setup_logging()
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        
    def _setup_logging(self):
        """配置日志系统"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'{self.bot_name}_system.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(self.bot_name)
        
    async def safe_execute(self, func, *args, **kwargs):
        """安全执行函数，包含错误处理"""
        try:
            result = await func(*args, **kwargs)
            self.success_count += 1
            return result
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"执行函数 {func.__name__} 时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # 记录详细错误信息
            error_info = {
                'function': func.__name__,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'args': str(args),
                'kwargs': str(kwargs)
            }
            
            # 保存错误日志
            self._save_error_log(error_info)
            
            # 根据错误类型决定是否重试
            if self._should_retry(e):
                self.logger.info("正在重试操作...")
                await asyncio.sleep(2)  # 等待2秒后重试
                return await self.safe_execute(func, *args, **kwargs)
            
            return None
    
    def _should_retry(self, error: Exception) -> bool:
        """判断是否应该重试"""
        retry_errors = [
            'ConnectionError', 'TimeoutError', 'ConnectionResetError',
            'requests.exceptions.ConnectionError', 'requests.exceptions.Timeout'
        ]
        
        error_str = str(error)
        for retry_error in retry_errors:
            if retry_error in error_str:
                return True
        return False
    
    def _save_error_log(self, error_info: Dict[str, Any]):
        """保存错误日志"""
        try:
            log_file = f"{self.bot_name}_errors.json"
            
            # 读取现有日志
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # 添加新日志
            logs.append(error_info)
            
            # 限制日志数量
            if len(logs) > 100:
                logs = logs[-100:]
            
            # 保存日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"保存错误日志失败: {str(e)}")
    
    async def monitor_system_health(self):
        """监控系统健康状态"""
        while True:
            try:
                # 获取系统状态
                system_status = await self.performance_monitor.get_system_status()
                
                # 检查资源使用情况
                if system_status['cpu_percent'] > 80:
                    self.logger.warning(f"CPU使用率过高: {system_status['cpu_percent']}%")
                
                if system_status['memory_percent'] > 80:
                    self.logger.warning(f"内存使用率过高: {system_status['memory_percent']}%")
                
                if system_status['disk_percent'] > 90:
                    self.logger.warning(f"磁盘使用率过高: {system_status['disk_percent']}%")
                
                # 更新系统统计
                self.system_stats = system_status
                
                # 每30秒检查一次
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"系统监控错误: {str(e)}")
                await asyncio.sleep(60)  # 出错后等待更长时间
    
    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统摘要"""
        uptime = datetime.now() - self.start_time
        
        return {
            'bot_name': self.bot_name,
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': uptime.total_seconds(),
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0,
            'system_stats': self.system_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def graceful_shutdown(self):
        """优雅关闭系统"""
        self.logger.info("开始优雅关闭...")
        
        # 保存最终状态
        summary = self.get_system_summary()
        with open(f'{self.bot_name}_shutdown_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info("系统已安全关闭")


class PerformanceMonitor:
    """性能监控器"""
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 网络连接
            network = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            process_cpu = process.cpu_percent()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_memory_mb': round(process_memory, 2),
                'process_cpu_percent': process_cpu,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"获取系统状态失败: {str(e)}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'network_bytes_sent': 0,
                'network_bytes_recv': 0,
                'process_memory_mb': 0,
                'process_cpu_percent': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def monitor_performance(self, interval: int = 60):
        """持续监控性能"""
        performance_data = []
        
        while True:
            status = await self.get_system_status()
            performance_data.append(status)
            
            # 限制数据量
            if len(performance_data) > 100:
                performance_data = performance_data[-100:]
            
            # 保存性能数据
            with open('performance_monitor.json', 'w', encoding='utf-8') as f:
                json.dump(performance_data, f, indent=2)
            
            await asyncio.sleep(interval)


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        self.active_connections = {}
        self.connection_stats = {
            'total_connections': 0,
            'failed_connections': 0,
            'successful_connections': 0
        }
    
    async def create_connection(self, target: str, timeout: int = 10):
        """创建连接"""
        connection_id = f"conn_{len(self.active_connections) + 1}"
        
        try:
            # 这里可以添加实际的连接逻辑
            # 例如: requests.Session() 或数据库连接等
            
            connection_info = {
                'id': connection_id,
                'target': target,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            self.active_connections[connection_id] = connection_info
            self.connection_stats['successful_connections'] += 1
            self.connection_stats['total_connections'] += 1
            
            return connection_id
            
        except Exception as e:
            self.connection_stats['failed_connections'] += 1
            self.connection_stats['total_connections'] += 1
            raise e
    
    async def close_connection(self, connection_id: str):
        """关闭连接"""
        if connection_id in self.active_connections:
            self.active_connections[connection_id]['status'] = 'closed'
            self.active_connections[connection_id]['closed_at'] = datetime.now().isoformat()
    
    def get_connection_stats(self):
        """获取连接统计"""
        active_count = sum(1 for conn in self.active_connections.values() if conn['status'] == 'active')
        
        return {
            **self.connection_stats,
            'active_connections': active_count,
            'closed_connections': self.connection_stats['total_connections'] - active_count
        }


# 使用示例
async def main():
    """主函数示例"""
    system_manager = SystemManager("Dragon-V Security Bot")
    
    # 启动系统监控
    asyncio.create_task(system_manager.monitor_system_health())
    
    # 示例：安全执行一个函数
    async def example_function():
        await asyncio.sleep(1)
        return "Function executed successfully"
    
    result = await system_manager.safe_execute(example_function)
    print(f"Result: {result}")
    
    # 获取系统状态
    summary = system_manager.get_system_summary()
    print(f"System Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())