# NecoRAG 测试套件

## 概述

NecoRAG测试套件提供完整的测试框架，包括单元测试、集成测试、性能测试和系统测试，确保系统质量和稳定性。

## 功能特性

### 🧪 测试类型
- **单元测试**：测试单个组件和函数
- **集成测试**：测试组件间交互和数据流
- **性能测试**：基准测试、压力测试、并发测试
- **系统测试**：端到端完整系统测试

### 📊 测试报告
- 文本格式报告
- JSON格式报告
- JUnit XML格式报告
- 详细的性能统计

### ⚡ 性能测试
- 单操作基准测试
- 并发性能测试
- 压力测试
- 内存使用监控

## 快速开始

### 1. 运行Demo测试

```bash
# 运行所有测试
python tests/demo_test_runner.py

# 运行特定测试类型
python -m pytest tests/test_core/ -v
```

### 2. 编写测试用例

```python
from tests.test_suite import UnitTestCase

class MyTest(UnitTestCase):
    def __init__(self):
        super().__init__("my_test", "My test description")
    
    def run_test(self) -> bool:
        # 测试逻辑
        self.assertEqual(1 + 1, 2)
        return True
```

### 3. 使用装饰器

```python
from tests.test_suite import test_case

@test_case("simple_test", "Simple test example")
def test_simple_math():
    assert 2 + 2 == 4
    return True
```

## 测试框架结构

```
tests/
├── __init__.py              # 测试模块入口
├── test_suite.py           # 测试套件和用例基类
├── test_runner.py          # 测试运行器
├── performance_test.py     # 性能测试模块
├── integration_test.py     # 集成测试模块
├── demo_test_runner.py     # Demo程序和示例
├── test_core/             # 核心模块测试
├── test_integration/      # 集成测试
├── test_plugins/          # 插件测试
└── test_interface/        # 接口测试
```

## API参考

### TestRunner
```python
runner = TestRunner()
runner.add_test_suite(suite)
report = runner.run_all_tests()
```

### TestSuite
```python
suite = TestSuite("My Suite")
suite.add_test_case(test_case)
results = suite.run()
```

### PerformanceTester
```python
tester = PerformanceTester()
metrics = tester.benchmark_single_operation(my_function, iterations=1000)
```

## 测试最佳实践

### 1. 测试命名
- 使用描述性的测试名称
- 遵循 `test_功能_场景_预期结果` 的命名约定

### 2. 测试组织
- 按功能模块组织测试文件
- 使用测试套件分组相关测试

### 3. 断言使用
```python
# 基本断言
self.assertEqual(actual, expected)
self.assertTrue(condition)
self.assertIn(member, container)

# 带消息的断言
self.assertEqual(actual, expected, "Values should be equal")
```

### 4. 测试数据
- 使用独立的测试数据
- 避免测试间的数据依赖
- 清理测试产生的数据

## 性能测试指南

### 基准测试
```python
def my_operation():
    # 要测试的操作
    pass

tester = PerformanceTester()
metrics = tester.benchmark_single_operation(my_operation, iterations=1000)
```

### 并发测试
```python
metrics = tester.benchmark_concurrent_operations(
    my_operation, 
    concurrent_users=10, 
    duration_seconds=30
)
```

### 压力测试
```python
stress_result = tester.stress_test(
    my_operation,
    max_duration=300,
    failure_threshold=0.05
)
```

## 集成测试示例

```python
from tests.integration_test import IntegrationTester

tester = IntegrationTester()

# 测试完整查询流水线
test_data = [
    {
        "request": {"query": "测试查询", "top_k": 5},
        "expected": {"min_results": 1, "max_execution_time": 2.0}
    }
]
result = tester.test_full_query_pipeline(test_data)
```

## 测试报告示例

### 文本报告
```
============================================================
NecoRAG Test Report
============================================================
Execution Time: 123.456 - 125.789
Duration: 2.333s

Summary:
  Total Tests: 15
  Passed: 13
  Failed: 2
  Errors: 0
  Success Rate: 86.7%
```

### JSON报告
```json
{
  "summary": {
    "total_tests": 15,
    "passed": 13,
    "failed": 2,
    "success_rate": 0.867,
    "execution_time": 2.333
  },
  "details": [...]
}
```

## 持续集成

### GitHub Actions配置
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          python tests/demo_test_runner.py
```

## 故障排除

### 常见问题

1. **测试超时**
   - 增加测试超时设置
   - 优化被测试代码性能

2. **内存不足**
   - 减少并发用户数
   - 分批执行大型测试

3. **测试不稳定**
   - 检查测试数据依赖
   - 确保测试环境一致性

## 贡献指南

欢迎贡献新的测试用例和改进测试框架！

### 测试贡献要求
1. 遵循现有的测试结构
2. 提供清晰的测试描述
3. 包含适当的断言
4. 通过所有现有测试

## 许可证

MIT License