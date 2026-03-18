"""
测试 NecoRAG 检索器模块

测试内容：
- 检索器初始化
- 基本检索流程
- 早停控制器
- 检索路径追踪
"""

import pytest
import numpy as np

from src.retrieval.retriever import EarlyTerminationController, AdaptiveRetriever
from src.retrieval.models import RetrievalResult, QueryAnalysis
from src.memory.manager import MemoryManager


class TestEarlyTerminationController:
    """早停控制器测试"""
    
    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        controller = EarlyTerminationController()
        
        assert controller.threshold == 0.85
        assert controller.min_gain == 0.05
        assert controller.last_confidence == 0.0
    
    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        controller = EarlyTerminationController(threshold=0.9, min_gain=0.1)
        
        assert controller.threshold == 0.9
        assert controller.min_gain == 0.1
    
    def test_evaluate_confidence_empty_results(self):
        """测试空结果的置信度评估"""
        controller = EarlyTerminationController()
        
        confidence = controller.evaluate_confidence([])
        
        assert confidence == 0.0
    
    def test_evaluate_confidence_single_result(self):
        """测试单个结果的置信度评估"""
        controller = EarlyTerminationController()
        results = [
            RetrievalResult(memory_id="1", content="test", score=0.9, source="vector")
        ]
        
        confidence = controller.evaluate_confidence(results)
        
        # 少量结果置信度较低
        assert confidence == 0.9 * 0.8  # 0.72
    
    def test_evaluate_confidence_multiple_results(self):
        """测试多个结果的置信度评估"""
        controller = EarlyTerminationController()
        results = [
            RetrievalResult(memory_id="1", content="test1", score=0.95, source="vector"),
            RetrievalResult(memory_id="2", content="test2", score=0.7, source="vector"),
            RetrievalResult(memory_id="3", content="test3", score=0.5, source="vector"),
        ]
        
        confidence = controller.evaluate_confidence(results)
        
        # 应该根据 top-1 分数和分数差距计算
        assert confidence > 0.9
        assert confidence <= 1.0
    
    def test_should_terminate_high_confidence(self):
        """测试高置信度应该终止"""
        controller = EarlyTerminationController(threshold=0.85)
        
        should_stop = controller.should_terminate(0.9)
        
        assert should_stop is True
    
    def test_should_terminate_low_confidence(self):
        """测试低置信度不应终止"""
        controller = EarlyTerminationController(threshold=0.85)
        
        should_stop = controller.should_terminate(0.5)
        
        assert should_stop is False
    
    def test_should_terminate_marginal_gain(self):
        """测试边际收益递减终止"""
        controller = EarlyTerminationController(threshold=0.95, min_gain=0.05)
        
        # 第一次评估
        controller.should_terminate(0.6)
        # 第二次评估，边际收益小于阈值
        should_stop = controller.should_terminate(0.62)  # 增益只有 0.02
        
        assert should_stop is True
    
    def test_calculate_adaptive_threshold_short_query(self):
        """测试短查询的自适应阈值"""
        controller = EarlyTerminationController(threshold=0.85)
        
        threshold = controller.calculate_adaptive_threshold("短查询")
        
        # 短查询阈值降低
        assert threshold < 0.85
        assert threshold == 0.85 * 0.9
    
    def test_calculate_adaptive_threshold_long_query(self):
        """测试长查询的自适应阈值"""
        controller = EarlyTerminationController(threshold=0.85)
        
        threshold = controller.calculate_adaptive_threshold("这是一个比较长的查询，包含很多信息和细节")
        
        # 长查询保持原阈值
        assert threshold == 0.85


class TestAdaptiveRetrieverInit:
    """AdaptiveRetriever 初始化测试"""
    
    def test_init_basic(self):
        """测试基本初始化"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        assert retriever.memory == memory
        assert retriever.hyde is not None  # 默认启用 HyDE
        assert retriever.reranker is not None
        assert retriever.termination_controller is not None
    
    def test_init_without_hyde(self):
        """测试不启用 HyDE 的初始化"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        assert retriever.hyde is None
    
    def test_init_custom_threshold(self):
        """测试自定义置信度阈值"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, confidence_threshold=0.9)
        
        assert retriever.termination_controller.threshold == 0.9


class TestAdaptiveRetrieverRetrieve:
    """AdaptiveRetriever 检索测试"""
    
    def test_retrieve_basic(self):
        """测试基本检索"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve("测试查询")
        
        # 应该返回结果列表
        assert isinstance(results, list)
    
    def test_retrieve_with_top_k(self):
        """测试指定 top_k 的检索"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve("测试查询", top_k=5)
        
        # 结果数量不应超过 top_k
        assert len(results) <= 5
    
    def test_retrieve_with_min_score(self):
        """测试最低分数过滤"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve("测试查询", min_score=0.5)
        
        # 所有结果分数应该 >= min_score
        for result in results:
            assert result.score >= 0.5 or result.score == 0  # 空结果允许
    
    def test_retrieve_with_query_vector(self):
        """测试带查询向量的检索"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        query_vector = np.random.rand(768)
        results = retriever.retrieve("测试查询", query_vector=query_vector)
        
        assert isinstance(results, list)
    
    def test_retrieval_trace(self):
        """测试检索路径追踪"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        retriever.retrieve("测试查询")
        trace = retriever.get_retrieval_trace()
        
        assert isinstance(trace, list)
        assert len(trace) > 0


class TestAdaptiveRetrieverMethods:
    """AdaptiveRetriever 方法测试"""
    
    def test_analyze_query(self):
        """测试查询分析"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        analysis = retriever._analyze_query("这是一个测试查询？")
        
        assert isinstance(analysis, QueryAnalysis)
        assert analysis.original_query == "这是一个测试查询？"
        assert analysis.query_type in ["factual", "reasoning", "comparative"]
    
    def test_analyze_query_complexity(self):
        """测试查询复杂度分析"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        # 短查询（长度 < 50）
        simple = retriever._analyze_query("简单查询")
        assert simple.complexity == "simple"
        
        # 长查询（长度 >= 50 才会被判断为 complex）
        # 源码判断条件: len(query) >= 50 时为 complex
        complex_query = "这是一个非常长的复杂查询，它包含了很多细节信息和背景知识，需要进行复杂的多步骤处理和深度分析才能得到准确完整的答案"
        complex_analysis = retriever._analyze_query(complex_query)
        assert complex_analysis.complexity == "complex", f"Query length: {len(complex_query)} should be >= 50"
    
    def test_retrieve_with_hyde(self):
        """测试 HyDE 增强检索"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=True)
        
        results = retriever.retrieve_with_hyde("什么是深度学习？")
        
        assert isinstance(results, list)
    
    def test_retrieve_with_hyde_disabled(self):
        """测试禁用 HyDE 时的回退"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve_with_hyde("什么是深度学习？")
        
        # 应该回退到普通检索
        assert isinstance(results, list)


class TestQueryAnalysis:
    """QueryAnalysis 数据类测试"""
    
    def test_create_query_analysis(self):
        """测试创建查询分析结果"""
        analysis = QueryAnalysis(
            original_query="测试查询",
            rewritten_query="重写后的查询",
            query_type="factual",
            entities=["entity1", "entity2"],
            intent="search",
            complexity="simple"
        )
        
        assert analysis.original_query == "测试查询"
        assert analysis.rewritten_query == "重写后的查询"
        assert analysis.query_type == "factual"
        assert len(analysis.entities) == 2
        assert analysis.complexity == "simple"
    
    def test_query_analysis_defaults(self):
        """测试查询分析默认值"""
        analysis = QueryAnalysis(original_query="test")
        
        assert analysis.rewritten_query is None
        assert analysis.query_type == "factual"
        assert analysis.entities == []
        assert analysis.intent is None
        assert analysis.complexity == "simple"


class TestRetrievalResult:
    """RetrievalResult 数据类测试"""
    
    def test_create_retrieval_result(self):
        """测试创建检索结果"""
        result = RetrievalResult(
            memory_id="mem-001",
            content="检索到的内容",
            score=0.95,
            source="vector",
            metadata={"key": "value"},
            retrieval_path=["step1", "step2"]
        )
        
        assert result.memory_id == "mem-001"
        assert result.content == "检索到的内容"
        assert result.score == 0.95
        assert result.source == "vector"
        assert result.metadata["key"] == "value"
        assert len(result.retrieval_path) == 2
    
    def test_retrieval_result_defaults(self):
        """测试检索结果默认值"""
        result = RetrievalResult(
            memory_id="mem-001",
            content="test",
            score=0.5,
            source="vector"
        )
        
        assert result.metadata == {}
        assert result.retrieval_path == []


class TestSetDomainConfig:
    """设置领域配置测试"""
    
    def test_set_domain_config(self):
        """测试设置领域配置"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        # 初始状态
        assert retriever.domain_config is None
        
        # 如果 domain 模块可用，可以设置配置
        # 这里只测试方法存在
        assert hasattr(retriever, 'set_domain_config')


class TestMultiHopRetrieve:
    """多跳检索测试"""
    
    def test_multi_hop_retrieve_basic(self):
        """测试基本多跳检索"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        # 多跳检索可能返回空结果（取决于图谱状态）
        results = retriever.multi_hop_retrieve("测试实体", hops=2)
        
        assert isinstance(results, list)
    
    def test_multi_hop_retrieve_traces(self):
        """测试多跳检索追踪"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory)
        
        retriever.multi_hop_retrieve("测试实体", hops=3)
        trace = retriever.get_retrieval_trace()
        
        # 应该记录多跳检索步骤
        assert any("Multi-hop" in step for step in trace)


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_query(self):
        """测试空查询"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve("")
        
        # 应该能处理空查询
        assert isinstance(results, list)
    
    def test_very_long_query(self):
        """测试超长查询"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        long_query = "这是一个测试查询" * 100
        results = retriever.retrieve(long_query)
        
        assert isinstance(results, list)
    
    def test_unicode_query(self):
        """测试 Unicode 查询"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        unicode_query = "你好世界 Hello 🌍 مرحبا"
        results = retriever.retrieve(unicode_query)
        
        assert isinstance(results, list)
    
    def test_zero_top_k(self):
        """测试 top_k=0"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        results = retriever.retrieve("测试", top_k=0)
        
        # 应该返回空列表
        assert results == []
    
    def test_negative_min_score(self):
        """测试负数最低分数"""
        memory = MemoryManager()
        retriever = AdaptiveRetriever(memory=memory, enable_hyde=False)
        
        # 不应抛出异常
        results = retriever.retrieve("测试", min_score=-0.5)
        
        assert isinstance(results, list)
