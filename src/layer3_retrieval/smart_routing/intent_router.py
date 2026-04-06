"""
意图路由器 (Intent Router)

基于语义意图分类系统，将查询路由到对应的策略模板
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio


class IntentType(Enum):
    """7 大类语义意图"""
    FACTUAL_QUERY = "factual_query"  # 事实查询
    COMPARATIVE_ANALYSIS = "comparative_analysis"  # 比较分析
    REASONING_INFERENCE = "reasoning_inference"  # 推理演绎
    CONCEPT_EXPLANATION = "concept_explanation"  # 概念解释
    SUMMARIZATION = "summarization"  # 摘要总结
    PROCEDURAL = "procedural"  # 操作指导
    EXPLORATORY = "exploratory"  # 探索发散


@dataclass
class IntentResult:
    """意图识别结果"""
    intent_type: IntentType
    confidence: float
    complexity: float  # 问题复杂度 (0-1)
    domain: Optional[str] = None  # 所属领域
    entities: List[str] = None  # 识别的实体
    sub_intents: List['IntentResult'] = None  # 复合意图
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.sub_intents is None:
            self.sub_intents = []


# 意图对应的默认策略模板
INTENT_STRATEGY_TEMPLATES = {
    IntentType.FACTUAL_QUERY: [
        {"name": "vector_search", "weight": 0.7},
        {"name": "keyword_search", "weight": 0.3},
    ],
    IntentType.COMPARATIVE_ANALYSIS: [
        {"name": "multi_entity_search", "weight": 0.5},
        {"name": "graph_relation", "weight": 0.3},
        {"name": "comparison_generation", "weight": 0.2},
    ],
    IntentType.REASONING_INFERENCE: [
        {"name": "graph_multi_hop", "weight": 0.4},
        {"name": "hyde", "weight": 0.3},
        {"name": "cot_reasoning", "weight": 0.3},
    ],
    IntentType.CONCEPT_EXPLANATION: [
        {"name": "semantic_search", "weight": 0.6},
        {"name": "hierarchical_context", "weight": 0.3},
        {"name": "example_generation", "weight": 0.1},
    ],
    IntentType.SUMMARIZATION: [
        {"name": "broad_search", "weight": 0.5},
        {"name": "aggregation_ranking", "weight": 0.3},
        {"name": "key_point_extraction", "weight": 0.2},
    ],
    IntentType.PROCEDURAL: [
        {"name": "procedural_memory", "weight": 0.6},
        {"name": "temporal_ordering", "weight": 0.3},
        {"name": "step_validation", "weight": 0.1},
    ],
    IntentType.EXPLORATORY: [
        {"name": "spreading_activation", "weight": 0.4},
        {"name": "novelty_priority", "weight": 0.4},
        {"name": "cross_domain_association", "weight": 0.2},
    ],
}

# CoT 触发概率
COT_TRIGGER_PROBABILITY = {
    IntentType.FACTUAL_QUERY: 0.1,
    IntentType.COMPARATIVE_ANALYSIS: 0.4,
    IntentType.REASONING_INFERENCE: 0.9,
    IntentType.CONCEPT_EXPLANATION: 0.5,
    IntentType.SUMMARIZATION: 0.3,
    IntentType.PROCEDURAL: 0.2,
    IntentType.EXPLORATORY: 0.7,
}


class IntentRouter:
    """
    意图路由器
    
    功能:
    1. 语义意图分类
    2. 复杂度评估
    3. 策略模板映射
    """
    
    def __init__(self, intent_classifier=None, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            intent_classifier: 意图分类器实例 (可使用现有的 intent.classifier 模块)
            config: 配置参数
        """
        self.intent_classifier = intent_classifier
        self.config = config or {}
        self.strategy_templates = INTENT_STRATEGY_TEMPLATES.copy()
        self.cot_probabilities = COT_TRIGGER_PROBABILITY.copy()
        
        # 自定义模板注册
        self._custom_templates = {}
    
    async def analyze_intent(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        """
        分析查询的语义意图
        
        Args:
            query: 用户查询
            session_context: 会话上下文
            
        Returns:
            IntentResult: 意图识别结果
        """
        # 使用现有的意图分类器
        if self.intent_classifier:
            classification = await self.intent_classifier.classify(query)
            
            intent_type = self._map_to_intent_type(classification.get('type'))
            confidence = classification.get('confidence', 0.5)
            complexity = classification.get('complexity', 0.5)
            domain = classification.get('domain')
            entities = classification.get('entities', [])
        else:
            # 简单的规则匹配作为 fallback
            intent_type, confidence = self._simple_rule_based_classification(query)
            complexity = self._estimate_complexity(query)
            domain = None
            entities = []
        
        # 复杂度调节
        complexity = self._adjust_complexity(complexity, query, session_context)
        
        return IntentResult(
            intent_type=intent_type,
            confidence=confidence,
            complexity=complexity,
            domain=domain,
            entities=entities
        )
    
    def _map_to_intent_type(self, classification_type: str) -> IntentType:
        """将分类器输出映射到标准意图类型"""
        mapping = {
            'factual': IntentType.FACTUAL_QUERY,
            'comparative': IntentType.COMPARATIVE_ANALYSIS,
            'reasoning': IntentType.REASONING_INFERENCE,
            'concept': IntentType.CONCEPT_EXPLANATION,
            'summary': IntentType.SUMMARIZATION,
            'procedural': IntentType.PROCEDURAL,
            'exploratory': IntentType.EXPLORATORY,
        }
        return mapping.get(classification_type, IntentType.FACTUAL_QUERY)
    
    def _simple_rule_based_classification(
        self,
        query: str
    ) -> tuple[IntentType, float]:
        """简单的规则匹配分类 (fallback 方案)"""
        query_lower = query.lower()
        
        # 事实查询：包含"是什么"、"什么时候"等
        if any(kw in query_lower for kw in ['是什么', '什么时候', '哪里', 'who', 'what', 'when']):
            return IntentType.FACTUAL_QUERY, 0.7
        
        # 比较分析：包含"区别"、"对比"、"哪个更好"等
        if any(kw in query_lower for kw in ['区别', '对比', '哪个好', 'vs', 'versus', 'difference']):
            return IntentType.COMPARATIVE_ANALYSIS, 0.8
        
        # 推理演绎：包含"为什么"、"如何证明"等
        if any(kw in query_lower for kw in ['为什么', '如何证明', '原因', 'why', 'how to prove']):
            return IntentType.REASONING_INFERENCE, 0.75
        
        # 操作指导：包含"如何"、"怎么"等
        if any(kw in query_lower for kw in ['如何', '怎么', '怎样', 'how to', 'steps']):
            return IntentType.PROCEDURAL, 0.7
        
        # 概念解释：包含"什么是"、"解释"等
        if any(kw in query_lower for kw in ['什么是', '解释', '定义', 'meaning', 'define']):
            return IntentType.CONCEPT_EXPLANATION, 0.75
        
        # 默认为事实查询
        return IntentType.FACTUAL_QUERY, 0.5
    
    def _estimate_complexity(self, query: str) -> float:
        """估算问题复杂度"""
        # 基于长度
        length_score = min(len(query) / 100, 1.0) * 0.3
        
        # 基于问句数量
        question_marks = query.count('?') + query.count('？')
        question_score = min(question_marks / 3, 1.0) * 0.4
        
        # 基于连接词
        connectors = ['和', '与', '及', '以及', '并且', '而且', '但是', '然而', 'and', 'but', 'however']
        connector_count = sum(1 for c in connectors if c in query.lower())
        connector_score = min(connector_count / 5, 1.0) * 0.3
        
        return length_score + question_score + connector_score
    
    def _adjust_complexity(
        self,
        base_complexity: float,
        query: str,
        session_context: Optional[Dict[str, Any]]
    ) -> float:
        """根据上下文调整复杂度"""
        adjustments = 0.0
        
        # 跨领域问题增加复杂度
        if session_context and 'multiple_domains' in session_context:
            adjustments += 0.2
        
        # 追问场景降低复杂度
        if session_context and session_context.get('is_followup'):
            adjustments -= 0.1
        
        # 包含专业术语增加复杂度
        technical_terms = ['算法', '架构', '协议', '框架', '模型', 'algorithm', 'architecture']
        if any(term in query.lower() for term in technical_terms):
            adjustments += 0.15
        
        return max(0.0, min(1.0, base_complexity + adjustments))
    
    def get_strategy_template(self, intent_type: IntentType) -> List[Dict[str, Any]]:
        """获取意图对应的策略模板"""
        return self.strategy_templates.get(intent_type, []).copy()
    
    def get_cot_trigger_probability(self, intent_type: IntentType) -> float:
        """获取 CoT 触发概率"""
        return self.cot_probabilities.get(intent_type, 0.3)
    
    def register_custom_template(
        self,
        intent_type: IntentType,
        strategies: List[Dict[str, float]]
    ):
        """注册自定义策略模板"""
        self._custom_templates[intent_type] = strategies
    
    def should_trigger_cot(
        self,
        intent_type: IntentType,
        complexity: float,
        confidence: float
    ) -> bool:
        """判断是否应该触发 CoT"""
        base_probability = self.get_cot_trigger_probability(intent_type)
        
        # 复杂度调节
        if complexity >= 0.8:
            base_probability += 0.2
        elif complexity <= 0.3:
            base_probability -= 0.2
        
        # 低置信度调节
        if confidence < 0.6:
            base_probability += 0.15
        
        # 随机触发 (基于概率)
        import random
        return random.random() < base_probability
