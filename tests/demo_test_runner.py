"""
测试套件使用示例和Demo程序
展示如何使用测试框架进行各种测试
"""

import sys
import os
import time
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 避免循环导入问题，直接导入所需模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_suite import UnitTestCase, IntegrationTestCase, test_case, TestSuite
from tests.test_runner import TestRunner
from tests.performance_test import PerformanceTester
from tests.integration_test import IntegrationTester


# 示例：单元测试用例
class MathUnitTest(UnitTestCase):
    """数学运算单元测试"""
    
    def __init__(self):
        super().__init__("math_operations", "Basic math operations test")
    
    def run_test(self) -> bool:
        """测试基本数学运算"""
        # 测试加法
        self.assertEqual(2 + 2, 4, "Basic addition failed")
        
        # 测试乘法
        self.assertEqual(3 * 4, 12, "Basic multiplication failed")
        
        # 测试除法
        self.assertEqual(10 / 2, 5.0, "Basic division failed")
        
        # 测试条件判断
        self.assertTrue(5 > 3, "Comparison failed")
        self.assertFalse(1 > 2, "Negative comparison failed")
        
        return True


class StringProcessingTest(UnitTestCase):
    """字符串处理单元测试"""
    
    def __init__(self):
        super().__init__("string_processing", "String processing operations test")
    
    def run_test(self) -> bool:
        """测试字符串处理功能"""
        test_string = "Hello World"
        
        # 测试字符串方法
        self.assertEqual(test_string.upper(), "HELLO WORLD", "String upper failed")
        self.assertEqual(test_string.lower(), "hello world", "String lower failed")
        self.assertIn("World", test_string, "String contains check failed")
        self.assertEqual(len(test_string), 11, "String length check failed")
        
        # 测试字符串分割
        parts = test_string.split()
        self.assertEqual(len(parts), 2, "String split failed")
        self.assertEqual(parts[0], "Hello", "String split result failed")
        
        return True


# 使用装饰器的测试用例
@test_case("list_operations", "List manipulation tests")
def test_list_operations():
    """测试列表操作"""
    test_list = [1, 2, 3, 4, 5]
    
    # 长度检查
    assert len(test_list) == 5
    
    # 元素检查
    assert 3 in test_list
    assert 6 not in test_list
    
    # 切片操作
    assert test_list[1:3] == [2, 3]
    
    return True


@test_case("dict_operations", "Dictionary manipulation tests")
def test_dict_operations():
    """测试字典操作"""
    test_dict = {"name": "Alice", "age": 30, "city": "Beijing"}
    
    # 键值检查
    assert test_dict["name"] == "Alice"
    assert "age" in test_dict
    assert len(test_dict) == 3
    
    # 更新操作
    test_dict["age"] = 31
    assert test_dict["age"] == 31
    
    return True


def run_unit_tests():
    """运行单元测试"""
    print("🧪 运行单元测试...")
    
    # 创建测试套件
    unit_suite = TestSuite("Unit Tests", "Basic functionality tests")
    
    # 添加测试用例
    unit_suite.add_test_case(MathUnitTest())
    unit_suite.add_test_case(StringProcessingTest())
    unit_suite.add_test_case(test_list_operations)
    unit_suite.add_test_case(test_dict_operations)
    
    # 运行测试
    results = unit_suite.run()
    
    # 显示结果
    print(f"\n📊 单元测试结果:")
    print(f"   总计: {unit_suite.get_total_count()}")
    print(f"   通过: {unit_suite.get_passed_count()}")
    print(f"   失败: {unit_suite.get_failed_count()}")
    print(f"   通过率: {unit_suite.get_pass_rate():.1%}")
    print(f"   平均耗时: {unit_suite.get_average_duration():.3f}s")
    
    return results


def run_performance_tests():
    """运行性能测试"""
    print("\n⚡ 运行性能测试...")
    
    tester = PerformanceTester()
    
    # 测试简单操作性能
    def simple_operation():
        result = sum(range(1000))
        return result
    
    try:
        metrics = tester.benchmark_single_operation(simple_operation, iterations=1000)
        
        print(f"\n📈 性能测试结果:")
        print(f"   平均执行时间: {metrics.avg_time:.6f}s")
        print(f"   吞吐量: {metrics.throughput:.2f} ops/s")
        print(f"   95%分位数: {metrics.percentiles[95]:.6f}s")
        print(f"   标准差: {metrics.std_deviation:.6f}s")
        
        # 性能断言
        assert metrics.avg_time < 0.01, "Average time too slow"
        assert metrics.throughput > 100, "Throughput too low"
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {str(e)}")
        return False


def run_integration_tests():
    """运行集成测试"""
    print("\n🔄 运行集成测试...")
    
    try:
        tester = IntegrationTester()
        
        # 测试数据生命周期
        test_entries = [
            {
                "content": "这是一个测试条目，用于验证数据生命周期功能。",
                "title": "测试条目1",
                "tags": ["test"],
                "domain": "example"
            }
        ]
        
        lifecycle_result = tester.test_data_lifecycle(test_entries)
        
        print(f"\n📋 数据生命周期测试结果:")
        print(f"   整体成功: {lifecycle_result['overall_success']}")
        for phase, result in lifecycle_result['phases'].items():
            status = "✅" if result['success'] else "❌"
            print(f"   {phase}: {status} ({result['time']:.3f}s)")
        
        return lifecycle_result['overall_success']
        
    except Exception as e:
        print(f"❌ 集成测试失败: {str(e)}")
        return False


def run_system_integration_test():
    """运行系统集成测试"""
    print("\n🌐 运行系统集成测试...")
    
    try:
        # 简化版本的系统测试
        tester = IntegrationTester()
        
        # 模拟测试数据
        test_data = [
            {
                "content": "测试数据用于系统集成测试",
                "title": "系统测试条目",
                "tags": ["test", "system"],
                "domain": "testing"
            }
        ]
        
        # 执行简化测试
        result = tester.test_data_lifecycle(test_data)
        
        print(f"\n🎯 系统集成测试结果:")
        print(f"   整体成功: {result['overall_success']}")
        if 'error' in result:
            print(f"   错误信息: {result['error']}")
        
        return result['overall_success']
        
    except Exception as e:
        print(f"❌ 系统集成测试失败: {str(e)}")
        return False


def main():
    """主函数 - 运行所有测试"""
    print("=" * 60)
    print("🚀 NecoRAG 测试套件 Demo")
    print("=" * 60)
    
    start_time = time.time()
    
    # 运行各类测试
    test_results = []
    
    # 1. 单元测试
    unit_results = run_unit_tests()
    test_results.append(("单元测试", unit_results))
    
    # 2. 性能测试
    perf_success = run_performance_tests()
    test_results.append(("性能测试", perf_success))
    
    # 3. 集成测试
    integration_success = run_integration_tests()
    test_results.append(("集成测试", integration_success))
    
    # 4. 系统集成测试
    system_success = run_system_integration_test()
    test_results.append(("系统集成测试", system_success))
    
    # 总结
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📋 测试总结报告")
    print("=" * 60)
    
    passed_count = sum(1 for _, result in test_results if result)
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 总体统计:")
    print(f"   总测试项: {total_count}")
    print(f"   通过项: {passed_count}")
    print(f"   失败项: {total_count - passed_count}")
    print(f"   通过率: {passed_count/total_count*100:.1f}%")
    print(f"   总耗时: {total_time:.3f}s")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)