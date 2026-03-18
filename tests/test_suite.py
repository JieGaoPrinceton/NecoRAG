"""
测试用例基类和测试套件管理
"""

import unittest
import time
import logging
from typing import Dict, Any, List, Callable, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    status: TestStatus
    duration: float
    message: str = ""
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = None


class TestCase(ABC):
    """测试用例基类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.status = TestStatus.PENDING
        self.duration = 0.0
        self.start_time = 0.0
        self.result: Optional[TestResult] = None
        self.logger = logging.getLogger(f"test.{name}")
    
    def setUp(self) -> None:
        """测试前置准备"""
        pass
    
    def tearDown(self) -> None:
        """测试后置清理"""
        pass
    
    @abstractmethod
    def run_test(self) -> bool:
        """执行测试逻辑，返回测试是否通过"""
        pass
    
    def assertEqual(self, actual, expected, message: str = ""):
        """断言相等"""
        if actual != expected:
            raise AssertionError(f"Expected {expected}, but got {actual}. {message}")
    
    def assertNotEqual(self, actual, expected, message: str = ""):
        """断言不相等"""
        if actual == expected:
            raise AssertionError(f"Expected not equal to {expected}, but got {actual}. {message}")
    
    def assertTrue(self, condition, message: str = ""):
        """断言为真"""
        if not condition:
            raise AssertionError(f"Expected True, but got {condition}. {message}")
    
    def assertFalse(self, condition, message: str = ""):
        """断言为假"""
        if condition:
            raise AssertionError(f"Expected False, but got {condition}. {message}")
    
    def assertIn(self, member, container, message: str = ""):
        """断言包含"""
        if member not in container:
            raise AssertionError(f"Expected {member} to be in {container}. {message}")
    
    def assertNotIn(self, member, container, message: str = ""):
        """断言不包含"""
        if member in container:
            raise AssertionError(f"Expected {member} not to be in {container}. {message}")
    
    def assertIsNone(self, value, message: str = ""):
        """断言为None"""
        if value is not None:
            raise AssertionError(f"Expected None, but got {value}. {message}")
    
    def assertIsNotNone(self, value, message: str = ""):
        """断言不为None"""
        if value is None:
            raise AssertionError(f"Expected not None. {message}")
    
    def execute(self) -> TestResult:
        """执行测试用例"""
        self.start_time = time.time()
        self.status = TestStatus.RUNNING
        
        try:
            self.setUp()
            passed = self.run_test()
            self.tearDown()
            
            self.duration = time.time() - self.start_time
            
            if passed:
                self.status = TestStatus.PASSED
                result = TestResult(
                    test_name=self.name,
                    status=TestStatus.PASSED,
                    duration=self.duration,
                    message="Test passed"
                )
            else:
                self.status = TestStatus.FAILED
                result = TestResult(
                    test_name=self.name,
                    status=TestStatus.FAILED,
                    duration=self.duration,
                    message="Test failed"
                )
                
        except Exception as e:
            self.duration = time.time() - self.start_time
            self.status = TestStatus.ERROR
            result = TestResult(
                test_name=self.name,
                status=TestStatus.ERROR,
                duration=self.duration,
                message=str(e),
                error=e
            )
            self.logger.error(f"Test error: {str(e)}")
        
        self.result = result
        return result


class TestSuite:
    """测试套件类"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self.logger = logging.getLogger(f"suite.{name}")
    
    def add_test_case(self, test_case: TestCase) -> None:
        """添加测试用例"""
        self.test_cases.append(test_case)
        self.logger.debug(f"Added test case: {test_case.name}")
    
    def add_test_cases(self, test_cases: List[TestCase]) -> None:
        """批量添加测试用例"""
        for test_case in test_cases:
            self.add_test_case(test_case)
    
    def run(self, stop_on_failure: bool = False) -> List[TestResult]:
        """
        运行测试套件
        Args:
            stop_on_failure: 遇到失败是否停止
        Returns:
            List[TestResult]: 测试结果列表
        """
        self.logger.info(f"Running test suite: {self.name}")
        self.results = []
        
        for test_case in self.test_cases:
            try:
                result = test_case.execute()
                self.results.append(result)
                
                if result.status in [TestStatus.FAILED, TestStatus.ERROR] and stop_on_failure:
                    self.logger.warning(f"Stopping on failure: {test_case.name}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error running test case {test_case.name}: {str(e)}")
                result = TestResult(
                    test_name=test_case.name,
                    status=TestStatus.ERROR,
                    duration=0.0,
                    message=str(e),
                    error=e
                )
                self.results.append(result)
        
        # 统计结果
        self._log_summary()
        return self.results
    
    def get_results_by_status(self, status: TestStatus) -> List[TestResult]:
        """按状态筛选测试结果"""
        return [result for result in self.results if result.status == status]
    
    def get_passed_count(self) -> int:
        """获取通过的测试数量"""
        return len(self.get_results_by_status(TestStatus.PASSED))
    
    def get_failed_count(self) -> int:
        """获取失败的测试数量"""
        return len(self.get_results_by_status(TestStatus.FAILED))
    
    def get_error_count(self) -> int:
        """获取错误的测试数量"""
        return len(self.get_results_by_status(TestStatus.ERROR))
    
    def get_total_count(self) -> int:
        """获取总测试数量"""
        return len(self.results)
    
    def get_pass_rate(self) -> float:
        """获取通过率"""
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return self.get_passed_count() / total
    
    def get_average_duration(self) -> float:
        """获取平均执行时间"""
        if not self.results:
            return 0.0
        return sum(result.duration for result in self.results) / len(self.results)
    
    def _log_summary(self) -> None:
        """记录测试汇总信息"""
        total = self.get_total_count()
        passed = self.get_passed_count()
        failed = self.get_failed_count()
        errors = self.get_error_count()
        pass_rate = self.get_pass_rate()
        
        self.logger.info(f"Test suite '{self.name}' completed:")
        self.logger.info(f"  Total: {total}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
        self.logger.info(f"  Pass rate: {pass_rate:.2%}")
        self.logger.info(f"  Average duration: {self.get_average_duration():.3f}s")


# 便捷的测试装饰器
def test_case(name: str, description: str = ""):
    """测试用例装饰器"""
    def decorator(func: Callable) -> Callable:
        class DecoratedTestCase(TestCase):
            def __init__(self):
                super().__init__(name, description)
            
            def run_test(self) -> bool:
                try:
                    result = func()
                    return result if isinstance(result, bool) else True
                except Exception:
                    return False
        
        return DecoratedTestCase()
    return decorator


# 预定义的测试用例类型
class UnitTestCase(TestCase):
    """单元测试用例基类"""
    pass


class IntegrationTestCase(TestCase):
    """集成测试用例基类"""
    pass


class PerformanceTestCase(TestCase):
    """性能测试用例基类"""
    
    def __init__(self, name: str, description: str = "", timeout: float = 30.0):
        super().__init__(name, description)
        self.timeout = timeout
    
    def run_test(self) -> bool:
        """执行性能测试"""
        # 子类需要实现具体的性能测试逻辑
        raise NotImplementedError("Performance test logic must be implemented")