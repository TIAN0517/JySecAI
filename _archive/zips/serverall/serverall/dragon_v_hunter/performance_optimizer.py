#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化器 - 提高自动化成功率
通过智能调度、重试机制、缓存优化和错误恢复来提升系统性能
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from functools import wraps, lru_cache
import concurrent.futures
import statistics
from collections import deque, defaultdict
import hashlib
import pickle
import os
import gc
import psutil
import signal
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float
    success_rate: float
    error_rate: float
    retries_count: int
    memory_usage: float
    cpu_usage: float
    network_latency: float
    cache_hit_rate: float

@dataclass
class OptimizationResult:
    """优化结果"""
    original_metrics: PerformanceMetrics
    optimized_metrics: PerformanceMetrics
    improvement_percentage: float
    optimizations_applied: List[str]
    execution_summary: str

class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.performance_history = []
        self.optimization_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "timeout": 30,
            "max_concurrent_requests": 10,
            "cache_size": 1000,
            "batch_size": 50,
            "memory_limit": "1GB",
            "cpu_limit": 80
        }

        # 智能重试配置
        self.retry_strategies = {
            "exponential_backoff": lambda attempt: min(2 ** attempt, 32),
            "linear_backoff": lambda attempt: attempt * 1.0,
            "fixed_backoff": lambda attempt: 1.0
        }

        # 缓存配置
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}

        # 错误统计
        self.error_statistics = defaultdict(int)
        self.successful_operations = []

        # 性能监控
        self.performance_monitor = PerformanceMonitor()

        # 智能调度器
        self.scheduler = IntelligentScheduler()

    def optimized_function(self, func: Callable) -> Callable:
        """性能优化装饰器"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                # 性能监控开始
                self.performance_monitor.start_monitoring(func.__name__)

                # 智能调度
                optimized_result = await self.scheduler.schedule_operation(func, args, kwargs)

                # 执行函数
                result = await optimized_result

                # 性能监控结束
                metrics = self.performance_monitor.end_monitoring()

                # 记录成功操作
                self.successful_operations.append({
                    "function": func.__name__,
                    "timestamp": datetime.now(),
                    "execution_time": metrics.execution_time,
                    "success": True
                })

                return result

            except Exception as e:
                # 错误处理和重试
                result = await self.handle_error_with_retry(func, args, kwargs, e)

                # 记录错误
                self.error_statistics[type(e).__name__] += 1

                return result

            finally:
                # 清理资源
                self.cleanup_resources()

        return wrapper

    async def handle_error_with_retry(self, func: Callable, args: Tuple, kwargs: Dict, error: Exception) -> Any:
        """智能错误处理和重试"""
        last_error = error

        for attempt in range(self.optimization_config["max_retries"]):
            try:
                # 指数退避
                delay = self.retry_strategies["exponential_backoff"](attempt)
                await asyncio.sleep(delay)

                # 清理缓存和连接
                await self.cleanup_for_retry()

                # 重试执行
                result = await func(*args, **kwargs)

                logger.info(f"函数 {func.__name__} 在第 {attempt + 1} 次重试后成功")
                return result

            except Exception as retry_error:
                last_error = retry_error
                logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次重试失败: {retry_error}")

                # 如果是特定错误类型，立即重试
                if self.should_immediate_retry(retry_error):
                    continue
                elif attempt < self.optimization_config["max_retries"] - 1:
                    await asyncio.sleep(delay)
                else:
                    break

        logger.error(f"函数 {func.__name__} 所有重试均失败: {last_error}")
        raise last_error

    def should_immediate_retry(self, error: Exception) -> bool:
        """判断是否应该立即重试"""
        # 网络相关错误立即重试
        immediate_retry_errors = [
            "ConnectionError",
            "TimeoutError",
            "aiohttp.ClientError",
            "asyncio.TimeoutError"
        ]

        return type(error).__name__ in immediate_retry_errors

    async def cleanup_for_retry(self):
        """重试前清理资源"""
        try:
            # 清理事件循环
            if asyncio.get_event_loop().is_running():
                await asyncio.sleep(0.1)

            # 强制垃圾回收
            gc.collect()

            # 清理HTTP会话
            for session in self.get_active_sessions():
                await session.close()

        except Exception as e:
            logger.warning(f"清理资源失败: {e}")

    def get_active_sessions(self) -> List[aiohttp.ClientSession]:
        """获取活跃的HTTP会话"""
        # 简化实现，实际应该跟踪所有活跃会话
        return []

    async def cleanup_resources(self):
        """清理资源"""
        try:
            # 强制垃圾回收
            gc.collect()

            # 检查内存使用
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 90:
                logger.warning(f"内存使用率过高: {memory_usage}%")
                await self.force_cleanup()

        except Exception as e:
            logger.error(f"资源清理失败: {e}")

    async def force_cleanup(self):
        """强制清理资源"""
        try:
            # 清理缓存
            self.cache.clear()

            # 清理历史记录
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-500:]

            # 清理成功操作记录
            if len(self.successful_operations) > 1000:
                cutoff_time = datetime.now() - timedelta(days=7)
                self.successful_operations = [
                    op for op in self.successful_operations
                    if op["timestamp"] > cutoff_time
                ]

        except Exception as e:
            logger.error(f"强制清理失败: {e}")

    @lru_cache(maxsize=1000)
    def cached_request(self, url: str, method: str = "GET", **kwargs) -> str:
        """带缓存的请求"""
        cache_key = hashlib.md5(f"{url}_{method}_{json.dumps(kwargs)}".encode()).hexdigest()

        if cache_key in self.cache:
            self.cache_stats["hits"] += 1
            return self.cache[cache_key]

        self.cache_stats["misses"] += 1
        return None

    async def batch_process(self, items: List[Any], process_func: Callable, batch_size: int = None) -> List[Any]:
        """批量处理优化"""
        if not batch_size:
            batch_size = self.optimization_config["batch_size"]

        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            logger.info(f"处理批次 {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")

            # 并行处理批次
            batch_results = await asyncio.gather(
                *[process_func(item) for item in batch],
                return_exceptions=True
            )

            # 处理结果
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"批量处理失败: {result}")
                else:
                    results.append(result)

            # 批次间延迟
            await asyncio.sleep(0.5)

        return results

    def optimize_concurrent_requests(self, tasks: List[Callable]) -> List[Any]:
        """优化并发请求"""
        max_concurrent = self.optimization_config["max_concurrent_requests"]

        results = []
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_task(task):
            async with semaphore:
                return await task()

        # 创建受限任务列表
        limited_tasks = [limited_task(task) for task in tasks]

        # 分批执行
        for i in range(0, len(limited_tasks), max_concurrent):
            batch = limited_tasks[i:i + max_concurrent]
            batch_results = asyncio.run(asyncio.gather(*batch, return_exceptions=True))
            results.extend(batch_results)

        return results

    def calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return self.cache_stats["hits"] / total_requests

    def analyze_performance_patterns(self) -> Dict[str, Any]:
        """分析性能模式"""
        if not self.successful_operations:
            return {}

        # 按函数分组分析
        function_stats = defaultdict(list)

        for op in self.successful_operations:
            function_stats[op["function"]].append(op["execution_time"])

        analysis = {}

        for func_name, times in function_stats.items():
            analysis[func_name] = {
                "avg_execution_time": statistics.mean(times),
                "median_execution_time": statistics.median(times),
                "min_execution_time": min(times),
                "max_execution_time": max(times),
                "std_deviation": statistics.stdev(times) if len(times) > 1 else 0,
                "total_calls": len(times),
                "success_rate": len(times) / max(1, len([op for op in self.successful_operations if op["function"] == func_name]))
            }

        return analysis

    def generate_optimization_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 分析错误统计
        if self.error_statistics:
            most_common_error = max(self.error_statistics.items(), key=lambda x: x[1])
            if most_common_error[1] > 5:
                recommendations.append(f"频繁出现错误: {most_common_error[0]}，建议添加特殊处理逻辑")

        # 分析缓存命中率
        cache_hit_rate = self.calculate_cache_hit_rate()
        if cache_hit_rate < 0.3:
            recommendations.append("缓存命中率较低，建议增加缓存策略")

        # 分析性能模式
        performance_analysis = self.analyze_performance_patterns()
        for func_name, stats in performance_analysis.items():
            if stats["std_deviation"] > stats["avg_execution_time"] * 0.5:
                recommendations.append(f"函数 {func_name} 执行时间波动较大，建议优化算法")

            if stats["avg_execution_time"] > 10:
                recommendations.append(f"函数 {func_name} 执行时间较长，考虑异步处理")

        # 检查配置参数
        if self.optimization_config["max_concurrent_requests"] > 20:
            recommendations.append("并发请求数量过高，可能导致性能下降，建议降低并发数")

        if self.optimization_config["batch_size"] > 100:
            recommendations.append("批次大小过大，建议减小批次大小以提高响应速度")

        return recommendations

    def update_config_based_on_performance(self):
        """根据性能数据更新配置"""
        try:
            performance_analysis = self.analyze_performance_patterns()

            # 基于性能数据动态调整配置
            for func_name, stats in performance_analysis.items():
                if stats["avg_execution_time"] > 5:
                    # 执行时间长的函数，减少并发数
                    self.optimization_config["max_concurrent_requests"] = max(5, self.optimization_config["max_concurrent_requests"] - 1)

                if stats["std_deviation"] > 2:
                    # 波动大的函数，增加重试次数
                    self.optimization_config["max_retries"] = min(5, self.optimization_config["max_retries"] + 1)

        except Exception as e:
            logger.error(f"动态更新配置失败: {e}")

    def save_performance_data(self, filename: str = None):
        """保存性能数据"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_data_{timestamp}.json"

        try:
            data = {
                "config": self.optimization_config,
                "cache_stats": self.cache_stats,
                "error_statistics": dict(self.error_statistics),
                "performance_history": [asdict(h) for h in self.performance_history[-100:]],
                "success_operations_count": len(self.successful_operations),
                "timestamp": datetime.now().isoformat()
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"性能数据已保存: {filename}")

        except Exception as e:
            logger.error(f"保存性能数据失败: {e}")

    def load_performance_data(self, filename: str):
        """加载性能数据"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.optimization_config.update(data.get("config", {}))
            self.cache_stats.update(data.get("cache_stats", {}))
            self.error_statistics.update(data.get("error_statistics", {}))

            logger.info(f"性能数据已加载: {filename}")

        except Exception as e:
            logger.error(f"加载性能数据失败: {e}")

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.memory_start = 0
        self.cpu_start = 0
        self.network_latencies = []

    def start_monitoring(self, operation_name: str):
        """开始监控"""
        self.start_time = time.time()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.cpu_start = psutil.cpu_percent()
        logger.info(f"开始监控操作: {operation_name}")

    def end_monitoring(self) -> PerformanceMetrics:
        """结束监控并返回指标"""
        self.end_time = time.time()

        execution_time = self.end_time - self.start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_usage = memory_end - self.memory_start
        cpu_usage = psutil.cpu_percent() - self.cpu_start

        # 计算网络延迟（模拟）
        network_latency = statistics.mean(self.network_latencies) if self.network_latencies else 0

        metrics = PerformanceMetrics(
            execution_time=execution_time,
            success_rate=1.0,  # 简化实现
            error_rate=0.0,    # 简化实现
            retries_count=0,   # 简化实现
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            network_latency=network_latency,
            cache_hit_rate=0.0  # 简化实现
        )

        return metrics

class IntelligentScheduler:
    """智能调度器"""

    def __init__(self):
        self.task_queue = []
        self.active_tasks = {}
        self.system_load_history = deque(maxlen=100)
        self.optimal_batch_size = 50

    def schedule_operation(self, func: Callable, args: Tuple, kwargs: Dict) -> Any:
        """智能调度操作"""
        # 评估系统负载
        current_load = self.evaluate_system_load()

        # 决定调度策略
        if current_load < 0.3:
            # 低负载，立即执行
            return func(*args, **kwargs)
        elif current_load < 0.7:
            # 中等负载，批量处理
            return self.batch_schedule(func, args, kwargs)
        else:
            # 高负载，延迟执行
            return self.delayed_schedule(func, args, kwargs)

    def evaluate_system_load(self) -> float:
        """评估系统负载"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            load_average = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_percent / 100

            # 综合负载评估
            system_load = (cpu_percent + memory_percent + load_average * 100) / 300

            self.system_load_history.append(system_load)
            return system_load

        except Exception:
            return 0.5  # 默认中等负载

    async def batch_schedule(self, func: Callable, args: Tuple, kwargs: Dict) -> Any:
        """批量调度"""
        # 添加到队列
        task_id = id(func)
        self.task_queue.append({
            "task_id": task_id,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "timestamp": time.time()
        })

        # 批量处理
        if len(self.task_queue) >= self.optimal_batch_size:
            await self.process_batch()

        return None  # 简化实现

    async def delayed_schedule(self, func: Callable, args: Tuple, kwargs: Dict) -> Any:
        """延迟调度"""
        # 延迟执行
        await asyncio.sleep(1)

        # 重新评估负载
        if self.evaluate_system_load() < 0.5:
            return func(*args, **kwargs)
        else:
            # 继续延迟
            await asyncio.sleep(2)
            return func(*args, **kwargs)

    async def process_batch(self):
        """处理批量任务"""
        if not self.task_queue:
            return

        batch = self.task_queue[:self.optimal_batch_size]
        self.task_queue = self.task_queue[self.optimal_batch_size:]

        logger.info(f"处理批量任务: {len(batch)} 个")

        # 并行执行批量任务
        tasks = [item["func"](*item["args"], **item["kwargs"]) for item in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 记录结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批量任务失败: {result}")

def create_optimized_target_analyzer():
    """创建优化的目标分析器"""
    optimizer = PerformanceOptimizer()

    # 装饰优化关键函数
    async def analyze_targets_optimized(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化的目标分析函数"""

        @optimizer.optimized_function
        async def analyze_single_target(target: Dict[str, Any]) -> Dict[str, Any]:
            """分析单个目标"""
            # 模拟分析过程
            await asyncio.sleep(0.1)

            result = {
                "name": target["name"],
                "url": target["url"],
                "risk_level": "HIGH" if target.get("sector") == "Banking" else "MEDIUM",
                "success_probability": 0.7,
                "timestamp": datetime.now().isoformat()
            }

            # 缓存请求结果
            cache_key = f"target_{target['name']}"
            cached_result = optimizer.cached_request(cache_key)
            if cached_result:
                return cached_result

            # 模拟网络延迟
            latency = random.uniform(0.05, 0.2)
            optimizer.performance_monitor.network_latencies.append(latency)

            return result

        # 批量处理
        results = await optimizer.batch_process(targets, analyze_single_target)

        return results

    return analyze_targets_optimized

def main():
    """主函数"""
    print("启动性能优化器...")

    # 创建性能优化器
    optimizer = PerformanceOptimizer()

    # 测试优化功能
    async def test_optimization():
        print("\n测试优化功能...")

        # 创建测试目标
        test_targets = [
            {"name": f"Target_{i}", "url": f"https://target{i}.example.com", "sector": "Banking"}
            for i in range(20)
        ]

        # 创建优化的分析器
        analyze_targets = create_optimized_target_analyzer()

        # 执行分析
        start_time = time.time()
        results = await analyze_targets(test_targets)
        end_time = time.time()

        print(f"分析完成: {len(results)} 个目标")
        print(f"执行时间: {end_time - start_time:.2f} 秒")

        # 生成优化建议
        recommendations = optimizer.generate_optimization_recommendations()
        print(f"\n优化建议:")
        for rec in recommendations:
            print(f"  - {rec}")

        # 保存性能数据
        optimizer.save_performance_data()

        # 计算缓存命中率
        cache_hit_rate = optimizer.calculate_cache_hit_rate()
        print(f"缓存命中率: {cache_hit_rate:.2%}")

        return results

    # 运行测试
    asyncio.run(test_optimization())

    print("\n" + "=" * 80)
    print("性能优化器测试完成!")
    print("=" * 80)
    print("主要优化功能:")
    print("1. 智能重试机制 - 基于错误类型的重试策略")
    print("2. 缓存优化 - LRU缓存减少重复请求")
    print("3. 批量处理 - 提高并发效率")
    print("4. 资源清理 - 自动内存和连接管理")
    print("5. 性能监控 - 实时指标收集和分析")
    print("6. 智能调度 - 根据系统负载动态调整")
    print("7. 配置优化 - 基于性能数据的自动调优")
    print("=" * 80)

if __name__ == "__main__":
    main()