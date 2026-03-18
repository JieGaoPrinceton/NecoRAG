"""
NecoRAG 测试套件模块
提供完整的单元测试、集成测试和性能测试框架
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Testing Team"

from .test_runner import TestRunner
from .test_suite import TestSuite, TestCase
from .performance_test import PerformanceTester
from .integration_test import IntegrationTester

__all__ = [
    "TestRunner",
    "TestSuite",
    "TestCase",
    "PerformanceTester",
    "IntegrationTester"
]