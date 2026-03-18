"""
NecoRAG 意图分类配置模块

定义意图分类器的配置参数和默认策略
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Type, TypeVar
import json
import os

from .models import IntentType, IntentRoutingStrategy


T = TypeVar('T', bound='IntentConfig')


@dataclass
class IntentConfig:
    """
    意图分类配置类
    
    Intent classification configuration with classifier settings,
    routing strategies, and weight configurations.
    
    Attributes:
        classifier_backend: 分类器后端 (rule_based, fasttext, transformer)
        model_name: Transformer 模型名称
        confidence_threshold: 置信度阈值
        enable_multi_intent: 是否支持多意图识别
        max_intents: 最大意图数量
        intent_weights: 各意图类型的默认权重
        routing_strategies: 各意图对应的路由策略
    """
    
    # 分类器配置
    classifier_backend: str = "rule_based"  # rule_based | fasttext | transformer
    model_name: str = "bert-base-chinese"   # Transformer 模型名
    fasttext_model_path: Optional[str] = None  # FastText 模型路径
    
    # 分类参数
    confidence_threshold: float = 0.6       # 置信度阈值
    enable_multi_intent: bool = True        # 是否支持多意图
    max_intents: int = 3                    # 最大意图数
    
    # 意图权重（用于检索时的权重调整）
    intent_weights: Dict[str, float] = field(default_factory=dict)
    
    # 各意图的路由策略
    routing_strategies: Dict[str, IntentRoutingStrategy] = field(default_factory=dict)
    
    # 关键词模式配置（用于规则分类）
    keyword_patterns: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化默认值"""
        # 设置默认意图权重
        if not self.intent_weights:
            self.intent_weights = self._default_intent_weights()
        
        # 设置默认路由策略
        if not self.routing_strategies:
            self.routing_strategies = self._default_routing_strategies()
        
        # 设置默认关键词模式
        if not self.keyword_patterns:
            self.keyword_patterns = self._default_keyword_patterns()
    
    def _default_intent_weights(self) -> Dict[str, float]:
        """默认意图权重配置"""
        return {
            IntentType.FACTUAL.value: 1.0,
            IntentType.COMPARATIVE.value: 1.2,
            IntentType.REASONING.value: 1.3,
            IntentType.EXPLANATION.value: 1.1,
            IntentType.SUMMARIZATION.value: 1.0,
            IntentType.PROCEDURAL.value: 1.1,
            IntentType.EXPLORATORY.value: 0.9,
        }
    
    def _default_routing_strategies(self) -> Dict[str, IntentRoutingStrategy]:
        """默认路由策略配置"""
        return {
            # 事实查询：精确检索，高置信度
            IntentType.FACTUAL.value: IntentRoutingStrategy(
                retrieval_mode="vector",
                weight_adjustments={"keyword_factor": 1.2, "semantic_factor": 1.0},
                enable_graph_search=False,
                enable_hyde=False,
                top_k=5,
                rerank_strategy="relevance"
            ),
            
            # 比较分析：需要多源信息，启用图谱
            IntentType.COMPARATIVE.value: IntentRoutingStrategy(
                retrieval_mode="hybrid",
                weight_adjustments={"keyword_factor": 1.0, "domain_factor": 1.3},
                enable_graph_search=True,
                enable_hyde=True,
                top_k=15,
                rerank_strategy="diversity"
            ),
            
            # 推理演绎：需要上下文和关系，强化图谱
            IntentType.REASONING.value: IntentRoutingStrategy(
                retrieval_mode="hybrid",
                weight_adjustments={"semantic_factor": 1.3, "temporal_factor": 0.8},
                enable_graph_search=True,
                enable_hyde=True,
                top_k=12,
                rerank_strategy="relevance"
            ),
            
            # 概念解释：语义检索为主
            IntentType.EXPLANATION.value: IntentRoutingStrategy(
                retrieval_mode="vector",
                weight_adjustments={"semantic_factor": 1.2, "keyword_factor": 1.1},
                enable_graph_search=False,
                enable_hyde=True,
                top_k=8,
                rerank_strategy="relevance"
            ),
            
            # 摘要总结：广泛检索
            IntentType.SUMMARIZATION.value: IntentRoutingStrategy(
                retrieval_mode="vector",
                weight_adjustments={"keyword_factor": 1.0, "temporal_factor": 1.2},
                enable_graph_search=False,
                enable_hyde=False,
                top_k=15,
                rerank_strategy="relevance"
            ),
            
            # 操作指导：精确匹配，关注步骤
            IntentType.PROCEDURAL.value: IntentRoutingStrategy(
                retrieval_mode="vector",
                weight_adjustments={"keyword_factor": 1.3, "semantic_factor": 1.0},
                enable_graph_search=False,
                enable_hyde=False,
                top_k=10,
                rerank_strategy="relevance"
            ),
            
            # 探索发散：广泛检索，多样性
            IntentType.EXPLORATORY.value: IntentRoutingStrategy(
                retrieval_mode="hybrid",
                weight_adjustments={"domain_factor": 1.2, "keyword_factor": 0.9},
                enable_graph_search=True,
                enable_hyde=True,
                top_k=20,
                rerank_strategy="diversity"
            ),
        }
    
    def _default_keyword_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        默认关键词模式配置（用于基于规则的分类）
        
        每个意图类型配置中英文关键词模式
        """
        return {
            IntentType.EXPLANATION.value: {
                "patterns_zh": [
                    "什么是", "是什么", "什么叫", "怎么理解", "如何理解",
                    "定义", "含义", "意思", "概念", "解释一下", "介绍一下",
                    "是指", "指的是", "啥意思", "啥是"
                ],
                "patterns_en": [
                    "what is", "what are", "what does", "define", "definition",
                    "meaning of", "explain", "what's", "describe"
                ],
                "weight": 1.5
            },
            IntentType.PROCEDURAL.value: {
                "patterns_zh": [
                    "如何", "怎么", "怎样", "怎么样", "怎么做", "如何做",
                    "步骤", "方法", "流程", "操作", "实现", "搭建", "配置",
                    "安装", "设置", "使用方法", "教程", "指南"
                ],
                "patterns_en": [
                    "how to", "how do", "how can", "steps to", "guide",
                    "tutorial", "instructions", "procedure", "setup", "configure"
                ],
                "weight": 1.4
            },
            IntentType.COMPARATIVE.value: {
                "patterns_zh": [
                    "区别", "差异", "不同", "对比", "比较", "哪个好",
                    "优缺点", "异同", "相比", "和.*比", "与.*区别",
                    "选哪个", "更好", "优劣"
                ],
                "patterns_en": [
                    "difference", "compare", "comparison", "vs", "versus",
                    "better than", "pros and cons", "which is better", "differ"
                ],
                "weight": 1.4
            },
            IntentType.REASONING.value: {
                "patterns_zh": [
                    "为什么", "为何", "原因", "为啥", "怎么会",
                    "导致", "因为", "所以", "因此", "推导", "推理",
                    "分析", "原理", "机制"
                ],
                "patterns_en": [
                    "why", "reason", "cause", "because", "therefore",
                    "how come", "explain why", "analyze", "mechanism"
                ],
                "weight": 1.3
            },
            IntentType.SUMMARIZATION.value: {
                "patterns_zh": [
                    "总结", "概括", "归纳", "要点", "摘要", "简述",
                    "概述", "提炼", "核心", "关键点", "重点"
                ],
                "patterns_en": [
                    "summarize", "summary", "overview", "brief", "key points",
                    "main points", "recap", "outline", "tldr"
                ],
                "weight": 1.2
            },
            IntentType.EXPLORATORY.value: {
                "patterns_zh": [
                    "有哪些", "有什么", "列出", "列举", "都有",
                    "包括", "种类", "类型", "分类", "例子", "案例",
                    "推荐", "建议"
                ],
                "patterns_en": [
                    "list", "what are the", "types of", "kinds of",
                    "examples", "categories", "recommend", "suggest"
                ],
                "weight": 1.1
            },
            IntentType.FACTUAL.value: {
                "patterns_zh": [
                    "是多少", "多少", "哪里", "哪个", "谁", "什么时候",
                    "时间", "地点", "数量", "日期", "版本"
                ],
                "patterns_en": [
                    "how many", "how much", "when", "where", "who",
                    "which", "what time", "what date", "version"
                ],
                "weight": 1.0
            },
        }
    
    def get_intent_weight(self, intent_type: IntentType) -> float:
        """获取意图权重"""
        return self.intent_weights.get(intent_type.value, 1.0)
    
    def get_routing_strategy(self, intent_type: IntentType) -> IntentRoutingStrategy:
        """获取路由策略"""
        strategy = self.routing_strategies.get(intent_type.value)
        if strategy is None:
            # 返回默认策略
            return IntentRoutingStrategy()
        return strategy
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "classifier_backend": self.classifier_backend,
            "model_name": self.model_name,
            "fasttext_model_path": self.fasttext_model_path,
            "confidence_threshold": self.confidence_threshold,
            "enable_multi_intent": self.enable_multi_intent,
            "max_intents": self.max_intents,
            "intent_weights": self.intent_weights,
            "routing_strategies": {
                k: v.to_dict() for k, v in self.routing_strategies.items()
            },
            "keyword_patterns": self.keyword_patterns,
        }
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """从字典创建"""
        # 处理路由策略
        routing_strategies = {}
        for k, v in data.get("routing_strategies", {}).items():
            if isinstance(v, dict):
                routing_strategies[k] = IntentRoutingStrategy.from_dict(v)
            else:
                routing_strategies[k] = v
        
        return cls(
            classifier_backend=data.get("classifier_backend", "rule_based"),
            model_name=data.get("model_name", "bert-base-chinese"),
            fasttext_model_path=data.get("fasttext_model_path"),
            confidence_threshold=data.get("confidence_threshold", 0.6),
            enable_multi_intent=data.get("enable_multi_intent", True),
            max_intents=data.get("max_intents", 3),
            intent_weights=data.get("intent_weights", {}),
            routing_strategies=routing_strategies,
            keyword_patterns=data.get("keyword_patterns", {}),
        )
    
    def save(self, path: str):
        """保存到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls: Type[T], path: str) -> T:
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def default(cls: Type[T]) -> T:
        """返回默认配置"""
        return cls()
    
    @classmethod
    def minimal(cls: Type[T]) -> T:
        """返回最小配置（仅规则分类，无额外依赖）"""
        config = cls()
        config.classifier_backend = "rule_based"
        config.enable_multi_intent = False
        config.max_intents = 1
        return config
    
    @classmethod
    def advanced(cls: Type[T]) -> T:
        """返回高级配置（使用 Transformer）"""
        config = cls()
        config.classifier_backend = "transformer"
        config.enable_multi_intent = True
        config.max_intents = 3
        config.confidence_threshold = 0.5
        return config
