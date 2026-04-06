"""
NecoRAG 语义分析器模块

提供统一的语义分析接口，整合意图分类和路由功能
"""

from typing import Dict, Optional, List, Any
import logging

from .models import (
    IntentType,
    IntentResult,
    IntentRoutingStrategy,
    SemanticAnalysisResult
)
from .config import IntentConfig
from .classifier import IntentClassifier
from .router import IntentRouter


logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """
    语义分析器
    
    Semantic analyzer that provides a unified interface for intent
    classification, routing, and query enhancement.
    
    整合意图分类和路由的高层接口，提供完整的语义分析功能。
    
    使用示例:
    ```python
    from src.intent import SemanticAnalyzer
    
    # 使用默认配置
    analyzer = SemanticAnalyzer()
    
    # 完整分析
    result = analyzer.analyze("什么是深度学习？")
    print(result["intent"])  # "explanation"
    print(result["confidence"])  # 0.85
    print(result["routing_strategy"]["enable_hyde"])  # True
    
    # 快速获取意图
    intent = analyzer.get_intent("如何配置 GPU？")
    print(intent.primary_intent)  # IntentType.PROCEDURAL
    
    # 获取路由策略
    strategy = analyzer.get_routing_strategy("对比 PyTorch 和 TensorFlow")
    print(strategy.enable_graph_search)  # True
    ```
    """
    
    def __init__(self, config: IntentConfig = None):
        """
        初始化语义分析器
        
        Args:
            config: 意图分类配置，None 则使用默认配置
        """
        self.config = config or IntentConfig.default()
        self._classifier = IntentClassifier(self.config)
        self._router = IntentRouter(self.config)
        
        logger.info("SemanticAnalyzer initialized")
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        执行完整的语义分析
        
        包括意图分类、路由策略确定、查询增强等。
        
        Args:
            query: 用户查询文本
            
        Returns:
            Dict: 完整的语义分析结果
            {
                "query": str,  # 原始查询
                "query_normalized": str,  # 归一化查询
                "intent": str,  # 主要意图
                "confidence": float,  # 置信度
                "secondary_intents": List[Dict],  # 次要意图
                "keywords": List[str],  # 关键词
                "entities": List[str],  # 实体
                "routing_strategy": Dict,  # 路由策略
                "intent_weight": float,  # 意图权重因子
                "retrieval_params": Dict,  # 检索参数
            }
        """
        # 意图分类
        intent_result = self._classifier.classify(query)
        
        # 获取路由策略
        routing_strategy = self._router.route(intent_result)
        
        # 计算意图权重
        intent_weight = self._router.get_weight_factor(intent_result)
        
        # 获取检索参数
        retrieval_params = self._router.get_retrieval_params(intent_result)
        
        # 查询归一化
        query_normalized = self._normalize_query(query)
        
        return {
            "query": query,
            "query_normalized": query_normalized,
            "intent": intent_result.primary_intent.value,
            "confidence": intent_result.confidence,
            "secondary_intents": [
                {"intent": i.value, "confidence": c}
                for i, c in intent_result.secondary_intents
            ],
            "keywords": intent_result.keywords,
            "entities": intent_result.entities,
            "routing_strategy": routing_strategy.to_dict(),
            "intent_weight": intent_weight,
            "retrieval_params": retrieval_params,
        }
    
    def analyze_detailed(self, query: str) -> SemanticAnalysisResult:
        """
        执行详细的语义分析，返回结构化对象
        
        Args:
            query: 用户查询文本
            
        Returns:
            SemanticAnalysisResult: 结构化的分析结果
        """
        intent_result = self._classifier.classify(query)
        routing_strategy = self._router.route(intent_result)
        intent_weight = self._router.get_weight_factor(intent_result)
        query_normalized = self._normalize_query(query)
        
        return SemanticAnalysisResult(
            intent_result=intent_result,
            routing_strategy=routing_strategy,
            query_normalized=query_normalized,
            intent_weight=intent_weight,
            analysis_metadata={
                "classifier_backend": self._classifier.get_backend(),
                "query_length": len(query),
            }
        )
    
    def get_intent(self, query: str) -> IntentResult:
        """
        快速获取意图分类结果
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentResult: 意图分类结果
        """
        return self._classifier.classify(query)
    
    def get_routing_strategy(self, query: str) -> IntentRoutingStrategy:
        """
        获取查询的路由策略
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentRoutingStrategy: 路由策略
        """
        intent_result = self._classifier.classify(query)
        return self._router.route(intent_result)
    
    def get_intent_weight(self, query: str) -> float:
        """
        获取查询的意图权重因子
        
        Args:
            query: 用户查询文本
            
        Returns:
            float: 意图权重因子
        """
        intent_result = self._classifier.classify(query)
        return self._router.get_weight_factor(intent_result)
    
    def get_intent_type(self, query: str) -> IntentType:
        """
        获取查询的主要意图类型
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentType: 意图类型枚举
        """
        intent_result = self._classifier.classify(query)
        return intent_result.primary_intent
    
    def should_use_graph(self, query: str) -> bool:
        """
        判断查询是否应该使用图谱搜索
        
        Args:
            query: 用户查询文本
            
        Returns:
            bool: 是否启用图谱搜索
        """
        intent_result = self._classifier.classify(query)
        return self._router.should_use_graph(intent_result)
    
    def should_use_hyde(self, query: str) -> bool:
        """
        判断查询是否应该使用 HyDE 增强
        
        Args:
            query: 用户查询文本
            
        Returns:
            bool: 是否启用 HyDE
        """
        intent_result = self._classifier.classify(query)
        return self._router.should_use_hyde(intent_result)
    
    def get_optimal_top_k(self, query: str) -> int:
        """
        获取查询的最优 top_k 值
        
        Args:
            query: 用户查询文本
            
        Returns:
            int: 推荐的检索数量
        """
        intent_result = self._classifier.classify(query)
        return self._router.get_optimal_top_k(intent_result)
    
    def batch_analyze(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析查询
        
        Args:
            queries: 查询列表
            
        Returns:
            分析结果列表
        """
        return [self.analyze(query) for query in queries]
    
    def explain(self, query: str) -> str:
        """
        生成分析结果的人类可读解释
        
        Args:
            query: 用户查询文本
            
        Returns:
            str: 分析解释
        """
        intent_result = self._classifier.classify(query)
        routing_explanation = self._router.explain_routing(intent_result)
        
        parts = [
            f"查询: {query}",
            f"分析结果: {routing_explanation}",
        ]
        
        if intent_result.keywords:
            parts.append(f"关键词: {', '.join(intent_result.keywords)}")
        
        if intent_result.entities:
            parts.append(f"实体: {', '.join(intent_result.entities)}")
        
        return "\n".join(parts)
    
    def _normalize_query(self, query: str) -> str:
        """
        归一化查询文本
        
        Args:
            query: 原始查询
            
        Returns:
            str: 归一化后的查询
        """
        # 去除多余空白
        normalized = " ".join(query.split())
        
        # 去除尾部标点符号
        normalized = normalized.rstrip("?？!！。.")
        
        return normalized
    
    @property
    def classifier(self) -> IntentClassifier:
        """获取内部分类器实例"""
        return self._classifier
    
    @property
    def router(self) -> IntentRouter:
        """获取内部路由器实例"""
        return self._router
    
    def set_backend(self, backend: str):
        """
        设置分类器后端
        
        Args:
            backend: 后端名称 (rule_based, fasttext, transformer)
        """
        self._classifier.set_backend(backend)


def create_analyzer(
    backend: str = "rule_based",
    **config_kwargs
) -> SemanticAnalyzer:
    """
    创建语义分析器的便捷函数
    
    Args:
        backend: 分类器后端
        **config_kwargs: 其他配置参数
        
    Returns:
        SemanticAnalyzer: 语义分析器实例
    """
    config = IntentConfig.default()
    config.classifier_backend = backend
    
    for key, value in config_kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return SemanticAnalyzer(config)


def quick_analyze(query: str) -> Dict[str, Any]:
    """
    快速分析查询的便捷函数
    
    Args:
        query: 查询文本
        
    Returns:
        Dict: 分析结果
    """
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(query)
