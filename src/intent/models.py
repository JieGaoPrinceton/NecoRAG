"""
NecoRAG 意图分类数据模型

定义意图相关的枚举类型、数据结构和路由策略
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum


class IntentType(Enum):
    """
    意图类型枚举
    
    Enum for query intent types in NecoRAG semantic analysis.
    """
    FACTUAL = "factual"           # 事实查询: 查找具体事实或数据
    COMPARATIVE = "comparative"   # 比较分析: 对比不同概念或事物
    REASONING = "reasoning"       # 推理演绎: 因果关系或逻辑推理
    EXPLANATION = "explanation"   # 概念解释: 定义或解释某个概念
    SUMMARIZATION = "summarization"  # 摘要总结: 概括或总结内容
    PROCEDURAL = "procedural"     # 操作指导: 步骤或方法指引
    EXPLORATORY = "exploratory"   # 探索发散: 开放式探索或列举


@dataclass
class IntentResult:
    """
    意图分类结果
    
    Intent classification result containing primary and secondary intents.
    
    Attributes:
        primary_intent: 主要意图类型
        confidence: 置信度 (0-1)
        secondary_intents: 次要意图及其置信度列表
        keywords: 从查询中提取的关键词
        entities: 识别出的实体
    """
    primary_intent: IntentType
    confidence: float
    secondary_intents: List[Tuple[IntentType, float]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """验证置信度范围"""
        self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "primary_intent": self.primary_intent.value,
            "confidence": self.confidence,
            "secondary_intents": [
                {"intent": intent.value, "confidence": conf}
                for intent, conf in self.secondary_intents
            ],
            "keywords": self.keywords,
            "entities": self.entities
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "IntentResult":
        """从字典创建"""
        return cls(
            primary_intent=IntentType(data["primary_intent"]),
            confidence=data["confidence"],
            secondary_intents=[
                (IntentType(item["intent"]), item["confidence"])
                for item in data.get("secondary_intents", [])
            ],
            keywords=data.get("keywords", []),
            entities=data.get("entities", [])
        )
    
    def get_top_intents(self, n: int = 3) -> List[Tuple[IntentType, float]]:
        """
        获取置信度最高的 N 个意图
        
        Args:
            n: 返回的意图数量
            
        Returns:
            按置信度排序的意图列表
        """
        all_intents = [(self.primary_intent, self.confidence)] + self.secondary_intents
        return sorted(all_intents, key=lambda x: x[1], reverse=True)[:n]


@dataclass
class IntentRoutingStrategy:
    """
    意图路由策略
    
    Routing strategy that determines how retrieval should be configured
    based on the detected intent.
    
    Attributes:
        retrieval_mode: 检索模式 (vector, graph, hybrid, hyde)
        weight_adjustments: 各权重因子的调整系数
        enable_graph_search: 是否启用图谱搜索
        enable_hyde: 是否启用 HyDE 增强
        top_k: 检索返回数量
        rerank_strategy: 重排序策略
    """
    retrieval_mode: str = "hybrid"
    weight_adjustments: Dict[str, float] = field(default_factory=dict)
    enable_graph_search: bool = False
    enable_hyde: bool = False
    top_k: int = 10
    rerank_strategy: str = "relevance"  # relevance, diversity, recency
    
    def __post_init__(self):
        """初始化默认权重调整"""
        if not self.weight_adjustments:
            self.weight_adjustments = {
                "keyword_factor": 1.0,
                "temporal_factor": 1.0,
                "domain_factor": 1.0,
                "semantic_factor": 1.0
            }
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "retrieval_mode": self.retrieval_mode,
            "weight_adjustments": self.weight_adjustments,
            "enable_graph_search": self.enable_graph_search,
            "enable_hyde": self.enable_hyde,
            "top_k": self.top_k,
            "rerank_strategy": self.rerank_strategy
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "IntentRoutingStrategy":
        """从字典创建"""
        return cls(
            retrieval_mode=data.get("retrieval_mode", "hybrid"),
            weight_adjustments=data.get("weight_adjustments", {}),
            enable_graph_search=data.get("enable_graph_search", False),
            enable_hyde=data.get("enable_hyde", False),
            top_k=data.get("top_k", 10),
            rerank_strategy=data.get("rerank_strategy", "relevance")
        )
    
    def merge_with(self, other: "IntentRoutingStrategy", weight: float = 0.5) -> "IntentRoutingStrategy":
        """
        与另一个策略融合
        
        Args:
            other: 另一个路由策略
            weight: 当前策略的权重 (0-1)
            
        Returns:
            融合后的策略
        """
        other_weight = 1.0 - weight
        
        # 融合权重调整
        merged_weights = {}
        all_keys = set(self.weight_adjustments.keys()) | set(other.weight_adjustments.keys())
        for key in all_keys:
            w1 = self.weight_adjustments.get(key, 1.0)
            w2 = other.weight_adjustments.get(key, 1.0)
            merged_weights[key] = w1 * weight + w2 * other_weight
        
        # 融合 top_k（取加权平均后向上取整）
        merged_top_k = int(self.top_k * weight + other.top_k * other_weight + 0.5)
        
        # 根据权重决定布尔值
        enable_graph = self.enable_graph_search if weight >= 0.5 else other.enable_graph_search
        enable_hyde = self.enable_hyde if weight >= 0.5 else other.enable_hyde
        
        # 选择权重较大的检索模式
        retrieval_mode = self.retrieval_mode if weight >= 0.5 else other.retrieval_mode
        rerank_strategy = self.rerank_strategy if weight >= 0.5 else other.rerank_strategy
        
        return IntentRoutingStrategy(
            retrieval_mode=retrieval_mode,
            weight_adjustments=merged_weights,
            enable_graph_search=enable_graph,
            enable_hyde=enable_hyde,
            top_k=merged_top_k,
            rerank_strategy=rerank_strategy
        )


@dataclass
class SemanticAnalysisResult:
    """
    语义分析完整结果
    
    Complete semantic analysis result combining intent classification
    and routing strategy.
    
    Attributes:
        intent_result: 意图分类结果
        routing_strategy: 路由策略
        query_normalized: 归一化后的查询
        intent_weight: 意图权重因子
        analysis_metadata: 分析元数据
    """
    intent_result: IntentResult
    routing_strategy: IntentRoutingStrategy
    query_normalized: str = ""
    intent_weight: float = 1.0
    analysis_metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "intent_result": self.intent_result.to_dict(),
            "routing_strategy": self.routing_strategy.to_dict(),
            "query_normalized": self.query_normalized,
            "intent_weight": self.intent_weight,
            "analysis_metadata": self.analysis_metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SemanticAnalysisResult":
        """从字典创建"""
        return cls(
            intent_result=IntentResult.from_dict(data["intent_result"]),
            routing_strategy=IntentRoutingStrategy.from_dict(data["routing_strategy"]),
            query_normalized=data.get("query_normalized", ""),
            intent_weight=data.get("intent_weight", 1.0),
            analysis_metadata=data.get("analysis_metadata", {})
        )
