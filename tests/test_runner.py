"""
测试运行器
提供测试执行、结果收集和报告生成功能
"""

import time
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .test_suite import TestSuite, TestResult, TestStatus


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.test_suites: List[TestSuite] = []
        self.all_results: List[TestResult] = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.logger = logging.getLogger(__name__)
    
    def add_test_suite(self, test_suite: TestSuite) -> None:
        """添加测试套件"""
        self.test_suites.append(test_suite)
        self.logger.debug(f"Added test suite: {test_suite.name}")
    
    def add_test_suites(self, test_suites: List[TestSuite]) -> None:
        """批量添加测试套件"""
        for suite in test_suites:
            self.add_test_suite(suite)
    
    def run_all_tests(self, stop_on_failure: bool = False) -> Dict[str, Any]:
        """
        运行所有测试
        Args:
            stop_on_failure: 遇到失败是否停止
        Returns:
            Dict: 测试执行结果统计
        """
        self.start_time = time.time()
        self.logger.info("Starting test execution...")
        
        self.all_results = []
        
        for suite in self.test_suites:
            suite_results = suite.run(stop_on_failure)
            self.all_results.extend(suite_results)
            
            if stop_on_failure:
                failed_results = [r for r in suite_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
                if failed_results:
                    self.logger.warning(f"Stopping due to failures in suite: {suite.name}")
                    break
        
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        
        # 生成统计报告
        report = self._generate_report(execution_time)
        self.logger.info(f"Test execution completed in {execution_time:.3f}s")
        
        return report
    
    def run_selected_suites(self, suite_names: List[str], stop_on_failure: bool = False) -> Dict[str, Any]:
        """
        运行选定的测试套件
        Args:
            suite_names: 要运行的套件名称列表
            stop_on_failure: 遇到失败是否停止
        Returns:
            Dict: 测试执行结果统计
        """
        selected_suites = [suite for suite in self.test_suites if suite.name in suite_names]
        
        if not selected_suites:
            self.logger.warning("No matching test suites found")
            return self._empty_report()
        
        # 临时替换测试套件列表
        original_suites = self.test_suites
        self.test_suites = selected_suites
        
        try:
            return self.run_all_tests(stop_on_failure)
        finally:
            # 恢复原始套件列表
            self.test_suites = original_suites
    
    def get_results_by_status(self, status: TestStatus) -> List[TestResult]:
        """按状态筛选所有测试结果"""
        return [result for result in self.all_results if result.status == status]
    
    def generate_text_report(self) -> str:
        """生成文本格式的测试报告"""
        if not self.all_results:
            return "No test results available"
        
        lines = []
        lines.append("=" * 60)
        lines.append("NecoRAG Test Report")
        lines.append("=" * 60)
        lines.append(f"Execution Time: {self.start_time:.3f} - {self.end_time:.3f}")
        lines.append(f"Duration: {self.end_time - self.start_time:.3f}s")
        lines.append("")
        
        # 总体统计
        total = len(self.all_results)
        passed = len(self.get_results_by_status(TestStatus.PASSED))
        failed = len(self.get_results_by_status(TestStatus.FAILED))
        errors = len(self.get_results_by_status(TestStatus.ERROR))
        skipped = len(self.get_results_by_status(TestStatus.SKIPPED))
        
        lines.append("Summary:")
        lines.append(f"  Total Tests: {total}")
        lines.append(f"  Passed: {passed}")
        lines.append(f"  Failed: {failed}")
        lines.append(f"  Errors: {errors}")
        lines.append(f"  Skipped: {skipped}")
        lines.append(f"  Success Rate: {passed/total*100:.1f}%" if total > 0 else "  Success Rate: 0%")
        lines.append("")
        
        # 按套件分组显示
        suite_results = {}
        for result in self.all_results:
            # 从测试名称推断套件名（假设格式为 "suite_name.test_name"）
            if '.' in result.test_name:
                suite_name = result.test_name.split('.')[0]
            else:
                suite_name = "Unknown"
            
            if suite_name not in suite_results:
                suite_results[suite_name] = []
            suite_results[suite_name].append(result)
        
        lines.append("Detailed Results:")
        lines.append("-" * 40)
        
        for suite_name, results in suite_results.items():
            lines.append(f"\nSuite: {suite_name}")
            suite_passed = len([r for r in results if r.status == TestStatus.PASSED])
            suite_total = len(results)
            lines.append(f"  Tests: {suite_total}, Passed: {suite_passed}, Failed: {suite_total - suite_passed}")
            
            for result in results:
                status_icon = {
                    TestStatus.PASSED: "✓",
                    TestStatus.FAILED: "✗",
                    TestStatus.ERROR: "⚡",
                    TestStatus.SKIPPED: "○"
                }.get(result.status, "?")
                
                lines.append(f"    {status_icon} {result.test_name} ({result.duration:.3f}s)")
                if result.status in [TestStatus.FAILED, TestStatus.ERROR] and result.message:
                    lines.append(f"      Error: {result.message}")
        
        return "\n".join(lines)
    
    def generate_json_report(self, filename: str = None) -> Dict[str, Any]:
        """生成JSON格式的测试报告"""
        report = self._generate_detailed_report()
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"JSON report saved to: {filename}")
        
        return report
    
    def generate_xml_report(self, filename: str = None) -> str:
        """生成JUnit XML格式的测试报告"""
        root = ET.Element("testsuites")
        
        # 总体统计
        total = len(self.all_results)
        failures = len(self.get_results_by_status(TestStatus.FAILED))
        errors = len(self.get_results_by_status(TestStatus.ERROR))
        
        root.set("tests", str(total))
        root.set("failures", str(failures))
        root.set("errors", str(errors))
        root.set("time", f"{self.end_time - self.start_time:.3f}")
        
        # 按套件组织
        suite_dict = {}
        for result in self.all_results:
            if '.' in result.test_name:
                suite_name, test_name = result.test_name.split('.', 1)
            else:
                suite_name, test_name = "default", result.test_name
            
            if suite_name not in suite_dict:
                suite_dict[suite_name] = []
            suite_dict[suite_name].append((test_name, result))
        
        # 创建测试套件元素
        for suite_name, test_results in suite_dict.items():
            suite_elem = ET.SubElement(root, "testsuite")
            suite_elem.set("name", suite_name)
            suite_elem.set("tests", str(len(test_results)))
            
            failures_count = sum(1 for _, result in test_results if result.status == TestStatus.FAILED)
            errors_count = sum(1 for _, result in test_results if result.status == TestStatus.ERROR)
            
            suite_elem.set("failures", str(failures_count))
            suite_elem.set("errors", str(errors_count))
            suite_elem.set("time", str(sum(result.duration for _, result in test_results)))
            
            # 添加测试用例
            for test_name, result in test_results:
                case_elem = ET.SubElement(suite_elem, "testcase")
                case_elem.set("name", test_name)
                case_elem.set("time", f"{result.duration:.3f}")
                
                if result.status == TestStatus.FAILED:
                    failure_elem = ET.SubElement(case_elem, "failure")
                    failure_elem.set("message", result.message or "Test failed")
                elif result.status == TestStatus.ERROR:
                    error_elem = ET.SubElement(case_elem, "error")
                    error_elem.set("message", result.message or "Test error")
                    if result.error:
                        error_elem.text = str(result.error)
        
        xml_str = ET.tostring(root, encoding='unicode')
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_str)
            self.logger.info(f"XML report saved to: {filename}")
        
        return xml_str
    
    def _generate_report(self, execution_time: float) -> Dict[str, Any]:
        """生成测试报告"""
        total = len(self.all_results)
        passed = len(self.get_results_by_status(TestStatus.PASSED))
        failed = len(self.get_results_by_status(TestStatus.FAILED))
        errors = len(self.get_results_by_status(TestStatus.ERROR))
        skipped = len(self.get_results_by_status(TestStatus.SKIPPED))
        
        return {
            "summary": {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "skipped": skipped,
                "success_rate": passed / total if total > 0 else 0,
                "execution_time": execution_time,
                "start_time": self.start_time,
                "end_time": self.end_time
            },
            "details": [self._result_to_dict(result) for result in self.all_results]
        }
    
    def _generate_detailed_report(self) -> Dict[str, Any]:
        """生成详细测试报告"""
        report = self._generate_report(self.end_time - self.start_time)
        
        # 按套件分组
        suite_groups = {}
        for result in self.all_results:
            suite_name = result.test_name.split('.')[0] if '.' in result.test_name else "default"
            if suite_name not in suite_groups:
                suite_groups[suite_name] = []
            suite_groups[suite_name].append(self._result_to_dict(result))
        
        report["suite_groups"] = suite_groups
        return report
    
    def _empty_report(self) -> Dict[str, Any]:
        """生成空报告"""
        return {
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "skipped": 0,
                "success_rate": 0,
                "execution_time": 0,
                "start_time": 0,
                "end_time": 0
            },
            "details": []
        }
    
    def _result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        """将测试结果转换为字典"""
        return {
            "test_name": result.test_name,
            "status": result.status.value,
            "duration": result.duration,
            "message": result.message,
            "error": str(result.error) if result.error else None,
            "metadata": result.metadata or {}
        }
    
    @property
    def total_tests(self) -> int:
        """总测试数"""
        return len(self.all_results)
    
    @property
    def passed_tests(self) -> int:
        """通过的测试数"""
        return len(self.get_results_by_status(TestStatus.PASSED))
    
    @property
    def failed_tests(self) -> int:
        """失败的测试数"""
        return len(self.get_results_by_status(TestStatus.FAILED))
    
    @property
    def error_tests(self) -> int:
        """错误的测试数"""
        return len(self.get_results_by_status(TestStatus.ERROR))
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests