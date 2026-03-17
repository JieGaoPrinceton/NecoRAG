"""
NecoRAG 综合权重计算器

整合关键字权重、时间权重和领域相关性权重，计算最终检索权重
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .config import DomainConfig, DomainConfigManager
from .temporal_weight import TemporalWeightCalculator, TemporalWeightConfig
from .relevance import DomainRelevanceCalculator, RelevanceScore


@dataclass
class DocumentMetadata:
    """文档元数据"""
    doc_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_evergreen: bool = False              # 是否为常青内容
    source_domain: Optional[str] = None     # 来源领域
    tags: List[str] = field(default_factory=list)
    custom_weight: float = 1.0              # 自定义权重加成


@dataclass
class WeightedScore:
    """加权评分结果"""
    doc_id: str
    base_score: float              # 原始相似度分数
    keyword_weight: float          # 关键字权重
    temporal_weight: float         # 时间权重
    domain_weight: float           # 领域权重
    final_score: float             # 最终加权分数
    
    # 详细信息
    relevance_score: Optional[RelevanceScore] = None
    explanation: str = ""
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "doc_id": self.doc_id,
            "base_score": self.base_score,
            "keyword_weight": self.keyword_weight,
            "temporal_weight": self.temporal_weight,
            "domain_weight": self.domain_weight,
            "final_score": self.final_score,
            "explanation": self.explanation,
        }


class CompositeWeightCalculator:
    """综合权重计算器"""
    
    def __init__(self, domain_config: DomainConfig):
        """
        初始化综合权重计算器
        
        Args:
            domain_config: 领域配置
        """
        self.domain_config = domain_config
        
        # 初始化子计算器
        temporal_config = TemporalWeightConfig(
            decay_rate=domain_config.decay_rate,
            enabled=domain_config.enable_temporal_decay
        )
        self.temporal_calculator = TemporalWeightCalculator(temporal_config)
        self.relevance_calculator = DomainRelevanceCalculator(domain_config)
        
        # 权重因子系数
        self.alpha = domain_config.keyword_factor    # 关键字因子
        self.beta = domain_config.temporal_factor    # 时间因子
        self.gamma = domain_config.domain_factor     # 领域因子
    
    def calculate_weight(self, 
                         base_score: float,
                         doc_metadata: DocumentMetadata,
                         query: Optional[str] = None,
                         current_time: Optional[datetime] = None) -> WeightedScore:
        """
        计算综合权重
        
        公式: final_weight = base_score × α × keyword_weight × β × temporal_weight × γ × domain_weight
        
        Args:
            base_score: 基础相似度分数（如向量相似度）
            doc_metadata: 文档元数据
            query: 查询文本（用于计算查询相关性）
            current_time: 当前时间
        
        Returns:
            WeightedScore: 加权评分结果
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 1. 计算关键字权重
        relevance_score = self.relevance_calculator.calculate_relevance(
            doc_metadata.content
        )
        keyword_weight = relevance_score.keyword_score
        # 确保最小值为 0.5，最大值为 2.0
        keyword_weight = max(0.5, min(2.0, keyword_weight)) if keyword_weight > 0 else 1.0
        
        # 2. 计算时间权重
        doc_time = doc_metadata.updated_at or doc_metadata.created_at
        temporal_weight = self.temporal_calculator.calculate_weight(
            document_time=doc_time,
            current_time=current_time,
            is_evergreen=doc_metadata.is_evergreen
        )
        
        # 3. 获取领域权重
        domain_weight = relevance_score.weight_multiplier
        
        # 4. 计算最终分数
        final_score = (
            base_score 
            * (self.alpha * keyword_weight)
            * (self.beta * temporal_weight)
            * (self.gamma * domain_weight)
            * doc_metadata.custom_weight
        )
        
        # 生成说明
        explanation = self._generate_explanation(
            base_score, keyword_weight, temporal_weight, 
            domain_weight, final_score, relevance_score
        )
        
        return WeightedScore(
            doc_id=doc_metadata.doc_id,
            base_score=base_score,
            keyword_weight=keyword_weight,
            temporal_weight=temporal_weight,
            domain_weight=domain_weight,
            final_score=final_score,
            relevance_score=relevance_score,
            explanation=explanation
        )
    
    def _generate_explanation(self, base_score: float, keyword_weight: float,
                               temporal_weight: float, domain_weight: float,
                               final_score: float, 
                               relevance_score: RelevanceScore) -> str:
        """生成评分说明"""
        return (
            f"基础分{base_score:.3f} × "
            f"关键字{keyword_weight:.2f}(α={self.alpha}) × "
            f"时间{temporal_weight:.2f}(β={self.beta}) × "
            f"领域{domain_weight:.2f}(γ={self.gamma}) = "
            f"最终{final_score:.3f} | "
            f"{relevance_score.explanation}"
        )
    
    def batch_calculate(self, 
                        scored_docs: List[Tuple[float, DocumentMetadata]],
                        query: Optional[str] = None,
                        current_time: Optional[datetime] = None) -> List[WeightedScore]:
        """
        批量计算权重
        
        Args:
            scored_docs: [(基础分数, 文档元数据), ...]
            query: 查询文本
            current_time: 当前时间
        
        Returns:
            List[WeightedScore]: 加权评分结果列表
        """
        return [
            self.calculate_weight(score, metadata, query, current_time)
            for score, metadata in scored_docs
        ]
    
    def rerank_by_weight(self, 
                          scored_docs: List[Tuple[float, DocumentMetadata]],
                          query: Optional[str] = None,
                          top_k: Optional[int] = None) -> List[WeightedScore]:
        """
        根据综合权重重新排序
        
        Args:
            scored_docs: [(基础分数, 文档元数据), ...]
            query: 查询文本
            top_k: 返回前 k 个结果
        
        Returns:
            List[WeightedScore]: 排序后的结果
        """
        weighted_scores = self.batch_calculate(scored_docs, query)
        
        # 按最终分数降序排序
        weighted_scores.sort(key=lambda x: x.final_score, reverse=True)
        
        if top_k is not None:
            weighted_scores = weighted_scores[:top_k]
        
        return weighted_scores
    
    def update_factors(self, alpha: float = None, 
                       beta: float = None, gamma: float = None) -> None:
        """
        更新权重因子系数
        
        Args:
            alpha: 关键字因子
            beta: 时间因子
            gamma: 领域因子
        """
        if alpha is not None:
            self.alpha = alpha
        if beta is not None:
            self.beta = beta
        if gamma is not None:
            self.gamma = gamma


class WeightCalculatorFactory:
    """权重计算器工厂"""
    
    def __init__(self, config_manager: Optional[DomainConfigManager] = None):
        self.config_manager = config_manager or DomainConfigManager()
        self._calculators: Dict[str, CompositeWeightCalculator] = {}
    
    def get_calculator(self, domain_id: str) -> Optional[CompositeWeightCalculator]:
        """
        获取指定领域的权重计算器
        
        Args:
            domain_id: 领域ID
        
        Returns:
            CompositeWeightCalculator: 权重计算器
        """
        if domain_id in self._calculators:
            return self._calculators[domain_id]
        
        domain_config = self.config_manager.get_domain(domain_id)
        if domain_config is None:
            domain_config = self.config_manager.load_domain(domain_id)
        
        if domain_config:
            calculator = CompositeWeightCalculator(domain_config)
            self._calculators[domain_id] = calculator
            return calculator
        
        return None
    
    def get_active_calculator(self) -> Optional[CompositeWeightCalculator]:
        """获取当前活动领域的计算器"""
        active_domain = self.config_manager.get_active_domain()
        if active_domain:
            return self.get_calculator(active_domain.domain_id)
        return None
    
    def create_calculator(self, domain_config: DomainConfig) -> CompositeWeightCalculator:
        """
        创建权重计算器
        
        Args:
            domain_config: 领域配置
        
        Returns:
            CompositeWeightCalculator: 权重计算器
        """
        calculator = CompositeWeightCalculator(domain_config)
        self._calculators[domain_config.domain_id] = calculator
        self.config_manager.domains[domain_config.domain_id] = domain_config
        return calculator


def create_weight_calculator(domain_config: DomainConfig) -> CompositeWeightCalculator:
    """
    创建权重计算器的便捷函数
    
    Args:
        domain_config: 领域配置
    
    Returns:
        CompositeWeightCalculator: 权重计算器
    """
    return CompositeWeightCalculator(domain_config)


def quick_rerank(base_scores: List[Tuple[str, float, str, datetime]],
                 domain_config: DomainConfig,
                 top_k: int = 10) -> List[WeightedScore]:
    """
    快速重排序便捷函数
    
    Args:
        base_scores: [(doc_id, score, content, created_at), ...]
        domain_config: 领域配置
        top_k: 返回前 k 个
    
    Returns:
        List[WeightedScore]: 排序后的结果
    """
    calculator = CompositeWeightCalculator(domain_config)
    
    scored_docs = [
        (score, DocumentMetadata(
            doc_id=doc_id,
            content=content,
            created_at=created_at
        ))
        for doc_id, score, content, created_at in base_scores
    ]
    
    return calculator.rerank_by_weight(scored_docs, top_k=top_k)
