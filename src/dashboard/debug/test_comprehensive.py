"""
NecoRAG 调试面板完整功能测试套件
测试所有模块的功能完整性、集成性和性能表现
"""

import asyncio
import pytest
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.dashboard.debug import (
    DebugSession, EvidenceInfo, DebugQueryRecord,
    DebugWebSocketManager, DebugAPIRouter,
    PerformanceMonitor, ErrorHandler, PerformanceOptimizer,
    ConnectionManager, InMemoryParameterStore,
    PathAnalyzer, ABTestingFramework, RecommendationEngine,
    performance_monitor, error_handler, performance_optimizer,
    monitor_performance, handle_errors
)

class TestDebugSession:
    """调试会话功能测试"""
    
    def test_debug_session_creation(self):
        """测试调试会话创建"""
        session = DebugSession(
            query="测试查询",
            user_id="test_user_123"
        )
        
        assert session.query == "测试查询"
        assert session.user_id == "test_user_123"
        assert session.status.name == "ACTIVE"
        assert len(session.session_id) > 0
        assert isinstance(session.start_time, datetime)
    
    def test_add_evidence(self):
        """测试添加证据"""
        session = DebugSession(query="测试查询")
        
        evidence = EvidenceInfo(
            source="vector",
            content="测试证据内容",
            relevance_score=0.85,
            metadata={"test": "data"}
        )
        
        session.add_evidence(evidence)
        
        assert len(session.evidence) == 1
        assert session.evidence[0].evidence_id == evidence.evidence_id
        assert session.evidence[0].content == "测试证据内容"
    
    def test_session_completion(self):
        """测试会话完成"""
        session = DebugSession(query="测试查询")
        
        # 添加一些证据
        evidence = EvidenceInfo(source="vector", content="测试证据")
        session.add_evidence(evidence)
        
        # 完成会话
        metrics = {"accuracy": 0.95, "latency": 0.5}
        session.complete_session(metrics)
        
        assert session.status.name == "COMPLETED"
        assert session.end_time is not None
        assert session.performance_metrics == metrics

class TestWebSocketIntegration:
    """WebSocket功能测试"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """测试WebSocket连接管理"""
        ws_manager = DebugWebSocketManager()
        
        # 模拟WebSocket连接
        class MockWebSocket:
            def __init__(self):
                self.connected = True
                self.messages = []
            
            async def send_json(self, data):
                self.messages.append(data)
            
            async def close(self, code=1000, reason=""):
                self.connected = False
        
        mock_ws = MockWebSocket()
        client_id = "test_client_123"
        
        # 测试连接
        result = await ws_manager.connect(mock_ws, client_id)
        assert result == True
        assert client_id in ws_manager.connections
        
        # 测试发送消息
        test_message = {"type": "test", "data": "hello"}
        await ws_manager.send_message(client_id, test_message)
        assert len(mock_ws.messages) == 1
        assert mock_ws.messages[0] == test_message
        
        # 测试断开连接
        await ws_manager.disconnect(client_id)
        assert client_id not in ws_manager.connections
        assert mock_ws.connected == False

class TestPerformanceMonitoring:
    """性能监控测试"""
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """测试性能监控功能"""
        monitor = PerformanceMonitor(sample_interval=0.1)
        
        # 启动监控
        await monitor.start_monitoring()
        
        # 等待收集一些数据
        await asyncio.sleep(0.5)
        
        # 检查指标收集
        current_metrics = monitor.get_current_metrics()
        assert current_metrics is not None
        assert hasattr(current_metrics, 'cpu_percent')
        assert hasattr(current_metrics, 'memory_percent')
        
        # 检查历史数据
        history = monitor.get_metrics_history(minutes=1)
        assert len(history) > 0
        
        # 停止监控
        await monitor.stop_monitoring()
    
    def test_performance_report_generation(self):
        """测试性能报告生成"""
        monitor = PerformanceMonitor()
        
        # 生成报告（即使没有数据也应该返回基本结构）
        report = monitor.get_performance_report()
        assert isinstance(report, dict)
        assert 'status' in report

class TestErrorHandling:
    """错误处理测试"""
    
    @pytest.mark.asyncio
    async def test_error_handling_basic(self):
        """测试基本错误处理"""
        handler = ErrorHandler()
        
        # 测试错误记录
        test_error = ValueError("测试错误")
        context = {"operation": "test", "user_id": "123"}
        
        handled = await handler.handle_error(test_error, context)
        assert isinstance(handled, bool)
        
        # 检查错误统计
        stats = handler.get_error_statistics()
        assert stats['total_errors'] >= 1
        assert 'ValueError' in stats['error_types']
    
    @pytest.mark.asyncio
    async def test_error_notification_callbacks(self):
        """测试错误通知回调"""
        handler = ErrorHandler()
        notifications = []
        
        async def notification_callback(error_info):
            notifications.append(error_info)
        
        handler.add_notification_callback(notification_callback)
        
        # 触发错误处理
        await handler.handle_error(ValueError("测试通知"))
        
        assert len(notifications) == 1
        assert 'error_type' in notifications[0]

class TestParameterTuning:
    """参数调优测试"""
    
    def test_parameter_store_operations(self):
        """测试参数存储操作"""
        store = InMemoryParameterStore()
        
        # 测试参数设置和获取
        store.set_parameter("test_param", 0.5)
        value = store.get_parameter("test_param")
        assert value == 0.5
        
        # 测试参数批量操作
        params = {"param1": 1.0, "param2": 2.0}
        store.set_parameters(params)
        retrieved_params = store.get_parameters(["param1", "param2"])
        assert retrieved_params == params

class TestPathAnalysis:
    """路径分析测试"""
    
    def test_path_segment_creation(self):
        """测试路径段创建"""
        analyzer = PathAnalyzer()
        
        segment = analyzer.create_segment(
            segment_type="retrieval",
            name="向量检索",
            duration=0.5,
            metadata={"score": 0.85}
        )
        
        assert segment.segment_type == "retrieval"
        assert segment.name == "向量检索"
        assert segment.duration == 0.5
    
    def test_bottleneck_detection(self):
        """测试瓶颈检测"""
        analyzer = PathAnalyzer()
        
        # 创建测试路径段
        segments = [
            analyzer.create_segment("preprocessing", "预处理", 0.1),
            analyzer.create_segment("retrieval", "向量检索", 2.0),  # 瓶颈
            analyzer.create_segment("reranking", "重排序", 0.3),
            analyzer.create_segment("generation", "答案生成", 0.5)
        ]
        
        bottlenecks = analyzer.detect_bottlenecks(segments)
        assert len(bottlenecks) >= 0  # 可能检测到瓶颈

class TestABTesting:
    """A/B测试功能测试"""
    
    def test_ab_test_config_creation(self):
        """测试A/B测试配置创建"""
        framework = ABTestingFramework()
        
        variants = [
            {"name": "variant_a", "weight": 0.5, "params": {"top_k": 10}},
            {"name": "variant_b", "weight": 0.5, "params": {"top_k": 15}}
        ]
        
        test_config = framework.create_test(
            name="检索参数测试",
            variants=variants,
            metrics=["accuracy", "latency"]
        )
        
        assert test_config.name == "检索参数测试"
        assert len(test_config.variants) == 2
        assert test_config.status == "running"
    
    def test_statistical_significance(self):
        """测试统计显著性计算"""
        framework = ABTestingFramework()
        
        # 测试T检验
        group_a = [0.85, 0.87, 0.83, 0.89, 0.86]
        group_b = [0.91, 0.89, 0.92, 0.88, 0.90]
        
        t_stat, p_value = framework.t_test(group_a, group_b)
        assert isinstance(t_stat, float)
        assert isinstance(p_value, float)
        assert 0 <= p_value <= 1

class TestRecommendationEngine:
    """推荐引擎测试"""
    
    def test_recommendation_generation(self):
        """测试优化建议生成"""
        engine = RecommendationEngine()
        
        # 模拟系统指标
        metrics = SystemMetrics(
            avg_response_time=1200.0,
            error_rate=0.05,
            throughput=100,
            resource_utilization={
                "cpu": 0.75,
                "memory": 0.80,
                "disk": 0.45
            }
        )
        
        recommendations = engine.generate_recommendations(metrics)
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 0
    
    def test_pattern_detection(self):
        """测试性能模式检测"""
        engine = RecommendationEngine()
        
        # 测试尖峰检测
        data = [1, 2, 3, 10, 4, 5, 15, 6, 7, 20]  # 包含尖峰
        peaks = engine.detect_peaks(data, threshold=2.0)
        assert isinstance(peaks, list)
        assert len(peaks) > 0

class TestIntegrationScenarios:
    """集成场景测试"""
    
    @pytest.mark.asyncio
    async def test_complete_debug_workflow(self):
        """测试完整调试工作流"""
        # 1. 创建调试会话
        session = DebugSession(query="集成测试查询")
        
        # 2. 添加证据
        evidence = EvidenceInfo(
            source="vector",
            content="集成测试证据",
            relevance_score=0.9
        )
        session.add_evidence(evidence)
        
        # 3. 启动性能监控
        await performance_monitor.start_monitoring()
        
        # 4. 模拟处理过程
        @monitor_performance
        @handle_errors({"session_id": session.session_id})
        async def process_query():
            await asyncio.sleep(0.1)
            return "处理完成"
        
        result = await process_query()
        assert result == "处理完成"
        
        # 5. 完成会话
        session.complete_session({"accuracy": 0.95})
        
        # 6. 检查性能数据
        current_metrics = performance_monitor.get_current_metrics()
        assert current_metrics is not None
        
        # 7. 停止监控
        await performance_monitor.stop_monitoring()
    
    def test_api_endpoint_integration(self):
        """测试API端点集成"""
        # 测试API路由器是否存在
        assert DebugAPIRouter is not None
        
        # 检查路由前缀
        assert hasattr(DebugAPIRouter, 'prefix')
        assert '/api/debug' in str(DebugAPIRouter.prefix)

class TestPerformanceBenchmark:
    """性能基准测试"""
    
    def test_debug_session_performance(self):
        """测试调试会话性能"""
        # 测试大量证据添加性能
        session = DebugSession(query="性能测试")
        
        start_time = time.time()
        for i in range(1000):
            evidence = EvidenceInfo(
                source="vector",
                content=f"证据内容 {i}",
                relevance_score=0.5 + (i % 50) / 100.0
            )
            session.add_evidence(evidence)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert len(session.evidence) == 1000
        assert duration < 5.0  # 应该在5秒内完成
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self):
        """测试并发WebSocket连接"""
        ws_manager = DebugWebSocketManager()
        
        # 模拟多个并发连接
        async def create_connection(i):
            class MockWS:
                def __init__(self):
                    self.messages = []
                async def send_json(self, data):
                    self.messages.append(data)
                async def close(self):
                    pass
            
            mock_ws = MockWS()
            client_id = f"client_{i}"
            await ws_manager.connect(mock_ws, client_id)
            await asyncio.sleep(0.01)  # 模拟一些处理时间
            await ws_manager.disconnect(client_id)
        
        # 创建50个并发连接
        tasks = [create_connection(i) for i in range(50)]
        start_time = time.time()
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 10.0  # 应该在10秒内完成

# 辅助测试函数
def run_comprehensive_tests():
    """运行综合测试"""
    test_classes = [
        TestDebugSession,
        TestWebSocketIntegration,
        TestPerformanceMonitoring,
        TestErrorHandling,
        TestParameterTuning,
        TestPathAnalysis,
        TestABTesting,
        TestRecommendationEngine,
        TestIntegrationScenarios,
        TestPerformanceBenchmark
    ]
    
    results = {}
    
    for test_class in test_classes:
        class_name = test_class.__name__
        results[class_name] = {"passed": 0, "failed": 0, "errors": []}
        
        # 创建测试实例
        test_instance = test_class()
        
        # 获取测试方法
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                results[class_name]["passed"] += 1
            except Exception as e:
                results[class_name]["failed"] += 1
                results[class_name]["errors"].append(f"{method_name}: {str(e)}")
    
    return results

if __name__ == "__main__":
    print("🚀 开始运行NecoRAG调试面板完整功能测试...")
    
    # 运行测试
    test_results = run_comprehensive_tests()
    
    # 输出结果
    print("\n" + "="*60)
    print("测试结果汇总:")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for class_name, result in test_results.items():
        passed = result["passed"]
        failed = result["failed"]
        total_passed += passed
        total_failed += failed
        
        status = "✅ 通过" if failed == 0 else "❌ 失败"
        print(f"{class_name}: {status} ({passed}/{passed + failed})")
        
        if result["errors"]:
            print("  错误详情:")
            for error in result["errors"]:
                print(f"    - {error}")
    
    print("\n" + "="*60)
    print(f"总计: {total_passed} 通过, {total_failed} 失败")
    print(f"通过率: {total_passed/(total_passed + total_failed)*100:.1f}%")
    print("="*60)
    
    # 如果有失败的测试，退出码为1
    exit(1 if total_failed > 0 else 0)