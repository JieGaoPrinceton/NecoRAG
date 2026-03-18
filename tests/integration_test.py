"""
集成测试模块
提供系统级集成测试功能
"""

import time
from typing import List, Dict, Any, Optional
import logging

from .test_suite import IntegrationTestCase, TestStatus
from src.interface import knowledge_service


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def test_full_query_pipeline(self, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试完整查询流水线
        Args:
            test_data: 测试数据列表
        Returns:
            Dict: 测试结果
        """
        self.logger.info("Starting full query pipeline integration test")
        
        results = {
            "total_tests": len(test_data),
            "passed": 0,
            "failed": 0,
            "errors": [],
            "timing_stats": {}
        }
        
        timing_data = []
        
        for i, test_case in enumerate(test_data):
            try:
                start_time = time.time()
                
                # 执行完整查询流程
                response = knowledge_service.query_knowledge(test_case["request"])
                
                end_time = time.time()
                execution_time = end_time - start_time
                timing_data.append(execution_time)
                
                # 验证结果
                if self._validate_query_response(response, test_case["expected"]):
                    results["passed"] += 1
                    self.logger.debug(f"Test case {i+1} passed in {execution_time:.3f}s")
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "test_case": i+1,
                        "error": "Response validation failed",
                        "execution_time": execution_time
                    })
                    self.logger.warning(f"Test case {i+1} failed")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "test_case": i+1,
                    "error": str(e),
                    "execution_time": 0
                })
                self.logger.error(f"Test case {i+1} error: {str(e)}")
        
        # 计算时间统计
        if timing_data:
            results["timing_stats"] = {
                "min_time": min(timing_data),
                "max_time": max(timing_data),
                "avg_time": sum(timing_data) / len(timing_data),
                "total_time": sum(timing_data)
            }
        
        success_rate = results["passed"] / results["total_tests"] if results["total_tests"] > 0 else 0
        results["success_rate"] = success_rate
        
        self.logger.info(f"Pipeline test completed: {results['passed']}/{results['total_tests']} passed ({success_rate:.1%})")
        return results
    
    def test_data_lifecycle(self, test_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        测试数据生命周期（插入->查询->更新->删除）
        Args:
            test_entries: 测试数据条目
        Returns:
            Dict: 测试结果
        """
        self.logger.info("Starting data lifecycle integration test")
        
        results = {
            "phases": {},
            "overall_success": True
        }
        
        try:
            # 1. 插入测试
            self.logger.info("Testing data insertion...")
            insert_start = time.time()
            insert_result = knowledge_service.insert_knowledge({
                "entries": test_entries
            })
            insert_time = time.time() - insert_start
            
            results["phases"]["insertion"] = {
                "success": insert_result.get("success", False),
                "time": insert_time,
                "inserted_count": insert_result.get("inserted_count", 0)
            }
            
            if not insert_result.get("success"):
                results["overall_success"] = False
                return results
            
            # 2. 查询测试
            self.logger.info("Testing data query...")
            query_start = time.time()
            query_result = knowledge_service.query_knowledge({
                "query": test_entries[0].get("title", ""),
                "top_k": 5
            })
            query_time = time.time() - query_start
            
            results["phases"]["query"] = {
                "success": len(query_result.get("results", [])) > 0,
                "time": query_time,
                "result_count": len(query_result.get("results", []))
            }
            
            if not results["phases"]["query"]["success"]:
                results["overall_success"] = False
            
            # 3. 更新测试
            if insert_result.get("inserted_ids"):
                entry_id = insert_result["inserted_ids"][0]
                self.logger.info("Testing data update...")
                update_start = time.time()
                update_result = knowledge_service.update_knowledge({
                    "entry_id": entry_id,
                    "updates": {"content": "Updated content for testing"}
                })
                update_time = time.time() - update_start
                
                results["phases"]["update"] = {
                    "success": update_result.get("success", False),
                    "time": update_time
                }
                
                if not update_result.get("success"):
                    results["overall_success"] = False
            
            # 4. 删除测试
            if insert_result.get("inserted_ids"):
                self.logger.info("Testing data deletion...")
                delete_start = time.time()
                delete_result = knowledge_service.delete_knowledge({
                    "entry_ids": insert_result["inserted_ids"]
                })
                delete_time = time.time() - delete_start
                
                results["phases"]["deletion"] = {
                    "success": delete_result.get("success", False),
                    "time": delete_time,
                    "deleted_count": delete_result.get("deleted_count", 0)
                }
                
                if not delete_result.get("success"):
                    results["overall_success"] = False
            
        except Exception as e:
            results["overall_success"] = False
            results["error"] = str(e)
            self.logger.error(f"Data lifecycle test error: {str(e)}")
        
        self.logger.info(f"Data lifecycle test completed: {'SUCCESS' if results['overall_success'] else 'FAILED'}")
        return results
    
    def test_concurrent_access(self, concurrent_users: int = 10, duration: int = 30) -> Dict[str, Any]:
        """
        测试并发访问
        Args:
            concurrent_users: 并发用户数
            duration: 测试持续时间
        Returns:
            Dict: 测试结果
        """
        self.logger.info(f"Starting concurrent access test: {concurrent_users} users for {duration}s")
        
        import threading
        import random
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "timing_data": [],
            "errors": []
        }
        
        stop_event = threading.Event()
        threads = []
        
        def worker():
            local_requests = 0
            local_success = 0
            local_failures = 0
            local_timing = []
            local_errors = []
            
            test_queries = [
                "人工智能",
                "机器学习",
                "深度学习",
                "自然语言处理",
                "计算机视觉"
            ]
            
            while not stop_event.is_set():
                try:
                    query = random.choice(test_queries)
                    start_time = time.time()
                    
                    response = knowledge_service.query_knowledge({
                        "query": query,
                        "top_k": 3
                    })
                    
                    end_time = time.time()
                    local_timing.append(end_time - start_time)
                    local_requests += 1
                    
                    if response and len(response.get("results", [])) > 0:
                        local_success += 1
                    else:
                        local_failures += 1
                        
                except Exception as e:
                    local_failures += 1
                    local_errors.append(str(e))
            
            # 更新全局结果
            results["total_requests"] += local_requests
            results["successful_requests"] += local_success
            results["failed_requests"] += local_failures
            results["timing_data"].extend(local_timing)
            results["errors"].extend(local_errors)
        
        # 启动并发线程
        for _ in range(concurrent_users):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 运行测试
        time.sleep(duration)
        stop_event.set()
        
        # 等待所有线程结束
        for thread in threads:
            thread.join()
        
        # 计算统计信息
        if results["timing_data"]:
            results["timing_stats"] = {
                "avg_response_time": sum(results["timing_data"]) / len(results["timing_data"]),
                "min_response_time": min(results["timing_data"]),
                "max_response_time": max(results["timing_data"])
            }
        
        success_rate = results["successful_requests"] / results["total_requests"] if results["total_requests"] > 0 else 0
        results["success_rate"] = success_rate
        
        self.logger.info(f"Concurrent test completed: {results['successful_requests']}/{results['total_requests']} successful ({success_rate:.1%})")
        return results
    
    def _validate_query_response(self, response: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """验证查询响应"""
        try:
            # 检查基本结构
            if not isinstance(response, dict):
                return False
            
            # 检查必需字段
            required_fields = ["query_id", "results", "execution_time"]
            for field in required_fields:
                if field not in response:
                    return False
            
            # 检查结果数量
            if "min_results" in expected:
                if len(response["results"]) < expected["min_results"]:
                    return False
            
            # 检查执行时间
            if "max_execution_time" in expected:
                if response["execution_time"] > expected["max_execution_time"]:
                    return False
            
            # 检查结果内容（如果指定了期望内容）
            if "expected_content" in expected and response["results"]:
                content_found = any(
                    expected["expected_content"] in str(result.get("content", ""))
                    for result in response["results"]
                )
                if not content_found:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Response validation error: {str(e)}")
            return False


# 集成测试用例
class FullSystemIntegrationTest(IntegrationTestCase):
    """完整系统集成测试"""
    
    def __init__(self):
        super().__init__("full_system_integration", "Complete system integration test")
    
    def run_test(self) -> bool:
        """执行完整系统集成测试"""
        tester = IntegrationTester()
        
        # 准备测试数据
        test_entries = [
            {
                "content": "人工智能是计算机科学的一个重要分支，致力于创造能够模拟人类智能的系统。",
                "title": "人工智能定义",
                "tags": ["AI", "计算机科学"],
                "domain": "technology"
            },
            {
                "content": "机器学习是人工智能的核心技术之一，通过算法让计算机从数据中学习规律。",
                "title": "机器学习概念",
                "tags": ["ML", "AI"],
                "domain": "technology"
            }
        ]
        
        test_queries = [
            {
                "request": {"query": "什么是人工智能？", "top_k": 3},
                "expected": {"min_results": 1, "max_execution_time": 2.0}
            },
            {
                "request": {"query": "机器学习的基本原理", "top_k": 3},
                "expected": {"min_results": 1, "max_execution_time": 2.0}
            }
        ]
        
        try:
            # 测试数据生命周期
            lifecycle_result = tester.test_data_lifecycle(test_entries)
            self.assertTrue(lifecycle_result["overall_success"], "Data lifecycle test failed")
            
            # 测试查询流水线
            pipeline_result = tester.test_full_query_pipeline(test_queries)
            self.assertTrue(pipeline_result["success_rate"] >= 0.8, "Query pipeline test failed")
            
            # 测试并发访问
            concurrent_result = tester.test_concurrent_access(concurrent_users=5, duration=10)
            self.assertTrue(concurrent_result["success_rate"] >= 0.9, "Concurrent access test failed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Integration test failed: {str(e)}")
            return False