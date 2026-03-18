"""
性能测试模块
提供性能基准测试和压力测试功能
"""

import time
import threading
import multiprocessing
import statistics
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
import logging

from .test_suite import PerformanceTestCase, TestStatus


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    std_deviation: float
    percentiles: Dict[int, float]  # 50%, 90%, 95%, 99%
    throughput: float  # 每秒执行次数
    total_executions: int
    total_time: float


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def benchmark_single_operation(self, 
                                 operation: Callable, 
                                 iterations: int = 1000,
                                 warmup_iterations: int = 100) -> PerformanceMetrics:
        """
        单操作性能基准测试
        Args:
            operation: 要测试的操作函数
            iterations: 测试迭代次数
            warmup_iterations: 预热迭代次数
        Returns:
            PerformanceMetrics: 性能指标
        """
        self.logger.info(f"Starting benchmark: {iterations} iterations")
        
        # 预热
        if warmup_iterations > 0:
            self.logger.debug(f"Warming up with {warmup_iterations} iterations")
            for _ in range(warmup_iterations):
                operation()
        
        # 执行测试
        execution_times = []
        start_time = time.time()
        
        for i in range(iterations):
            iter_start = time.time()
            try:
                operation()
            except Exception as e:
                self.logger.warning(f"Benchmark iteration {i} failed: {str(e)}")
                continue
            iter_end = time.time()
            execution_times.append(iter_end - iter_start)
        
        total_time = time.time() - start_time
        
        if not execution_times:
            raise RuntimeError("All benchmark iterations failed")
        
        # 计算指标
        metrics = self._calculate_metrics(execution_times, total_time, iterations)
        self.logger.info(f"Benchmark completed: avg={metrics.avg_time:.6f}s, throughput={metrics.throughput:.2f} ops/s")
        
        return metrics
    
    def benchmark_concurrent_operations(self,
                                      operation: Callable,
                                      concurrent_users: int = 10,
                                      duration_seconds: int = 30) -> PerformanceMetrics:
        """
        并发性能测试
        Args:
            operation: 要测试的操作函数
            concurrent_users: 并发用户数
            duration_seconds: 测试持续时间
        Returns:
            PerformanceMetrics: 性能指标
        """
        self.logger.info(f"Starting concurrent benchmark: {concurrent_users} users for {duration_seconds}s")
        
        results = []
        threads = []
        stop_event = threading.Event()
        
        def worker():
            thread_results = []
            while not stop_event.is_set():
                start_time = time.time()
                try:
                    operation()
                    end_time = time.time()
                    thread_results.append(end_time - start_time)
                except Exception as e:
                    self.logger.warning(f"Concurrent operation failed: {str(e)}")
            results.extend(thread_results)
        
        # 启动并发线程
        for _ in range(concurrent_users):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 运行指定时间
        time.sleep(duration_seconds)
        stop_event.set()
        
        # 等待所有线程结束
        for thread in threads:
            thread.join()
        
        if not results:
            raise RuntimeError("All concurrent operations failed")
        
        total_time = concurrent_users * duration_seconds
        metrics = self._calculate_metrics(results, total_time, len(results))
        self.logger.info(f"Concurrent benchmark completed: {len(results)} operations, throughput={metrics.throughput:.2f} ops/s")
        
        return metrics
    
    def stress_test(self,
                   operation: Callable,
                   max_duration: int = 300,
                   failure_threshold: float = 0.05) -> Dict[str, Any]:
        """
        压力测试
        Args:
            operation: 要测试的操作函数
            max_duration: 最大测试时间
            failure_threshold: 失败率阈值
        Returns:
            Dict: 压力测试结果
        """
        self.logger.info(f"Starting stress test: max {max_duration}s, failure threshold {failure_threshold:.1%}")
        
        start_time = time.time()
        successful_ops = 0
        failed_ops = 0
        execution_times = []
        
        while (time.time() - start_time) < max_duration:
            iter_start = time.time()
            try:
                operation()
                successful_ops += 1
                execution_times.append(time.time() - iter_start)
            except Exception as e:
                failed_ops += 1
                self.logger.debug(f"Stress test operation failed: {str(e)}")
            
            # 检查失败率
            total_ops = successful_ops + failed_ops
            if total_ops > 100:  # 至少执行100次后再检查
                failure_rate = failed_ops / total_ops
                if failure_rate > failure_threshold:
                    self.logger.warning(f"Failure rate {failure_rate:.1%} exceeded threshold {failure_threshold:.1%}")
                    break
        
        total_time = time.time() - start_time
        failure_rate = failed_ops / (successful_ops + failed_ops) if (successful_ops + failed_ops) > 0 else 0
        
        result = {
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "failure_rate": failure_rate,
            "total_time": total_time,
            "operations_per_second": (successful_ops + failed_ops) / total_time if total_time > 0 else 0
        }
        
        if execution_times:
            result["performance_metrics"] = self._calculate_metrics(
                execution_times, total_time, successful_ops
            )
        
        self.logger.info(f"Stress test completed: {successful_ops} successful, {failed_ops} failed, rate={failure_rate:.1%}")
        return result
    
    def memory_usage_test(self, operation: Callable, iterations: int = 100) -> Dict[str, Any]:
        """
        内存使用测试
        Args:
            operation: 要测试的操作函数
            iterations: 迭代次数
        Returns:
            Dict: 内存使用统计
        """
        try:
            import psutil
            import os
        except ImportError:
            self.logger.warning("psutil not available, skipping memory test")
            return {"error": "psutil not installed"}
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        memory_samples = []
        for i in range(iterations):
            operation()
            current_memory = process.memory_info().rss
            memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss
        
        return {
            "initial_memory_mb": initial_memory / 1024 / 1024,
            "final_memory_mb": final_memory / 1024 / 1024,
            "memory_increase_mb": (final_memory - initial_memory) / 1024 / 1024,
            "peak_memory_mb": max(memory_samples) / 1024 / 1024,
            "average_memory_mb": statistics.mean(memory_samples) / 1024 / 1024,
            "memory_samples": len(memory_samples)
        }
    
    def _calculate_metrics(self, 
                          execution_times: List[float], 
                          total_time: float, 
                          total_executions: int) -> PerformanceMetrics:
        """计算性能指标"""
        if not execution_times:
            raise ValueError("No execution times provided")
        
        sorted_times = sorted(execution_times)
        
        # 基本统计
        min_time = min(execution_times)
        max_time = max(execution_times)
        avg_time = statistics.mean(execution_times)
        
        # 中位数
        n = len(sorted_times)
        if n % 2 == 0:
            median_time = (sorted_times[n//2 - 1] + sorted_times[n//2]) / 2
        else:
            median_time = sorted_times[n//2]
        
        # 标准差
        std_deviation = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        
        # 百分位数
        percentiles = {
            50: self._percentile(sorted_times, 50),
            90: self._percentile(sorted_times, 90),
            95: self._percentile(sorted_times, 95),
            99: self._percentile(sorted_times, 99)
        }
        
        # 吞吐量
        throughput = total_executions / total_time if total_time > 0 else 0
        
        return PerformanceMetrics(
            min_time=min_time,
            max_time=max_time,
            avg_time=avg_time,
            median_time=median_time,
            std_deviation=std_deviation,
            percentiles=percentiles,
            throughput=throughput,
            total_executions=total_executions,
            total_time=total_time
        )
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not sorted_data:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight


# 性能测试用例示例
class ApiPerformanceTest(PerformanceTestCase):
    """API性能测试用例"""
    
    def __init__(self, api_client, endpoint: str, timeout: float = 30.0):
        super().__init__(f"api_performance_{endpoint}", f"Performance test for {endpoint}", timeout)
        self.api_client = api_client
        self.endpoint = endpoint
    
    def run_test(self) -> bool:
        """执行API性能测试"""
        tester = PerformanceTester()
        
        def api_call():
            response = self.api_client.get(self.endpoint)
            if response.status_code != 200:
                raise Exception(f"API call failed with status {response.status_code}")
        
        try:
            metrics = tester.benchmark_single_operation(api_call, iterations=100)
            
            # 性能断言
            self.assertTrue(metrics.avg_time < 1.0, f"Average response time too slow: {metrics.avg_time:.3f}s")
            self.assertTrue(metrics.throughput > 10, f"Throughput too low: {metrics.throughput:.2f} req/s")
            self.assertTrue(metrics.percentiles[95] < 2.0, f"95th percentile too high: {metrics.percentiles[95]:.3f}s")
            
            return True
        except Exception as e:
            self.logger.error(f"Performance test failed: {str(e)}")
            return False