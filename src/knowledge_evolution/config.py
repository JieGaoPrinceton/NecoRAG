"""
Knowledge Evolution 配置类

定义知识库更新与演化模块的配置选项。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Type, TypeVar
import json


T = TypeVar('T', bound='KnowledgeEvolutionConfig')


@dataclass
class KnowledgeEvolutionConfig:
    """
    知识库更新与演化配置
    
    Configuration for knowledge base update and evolution operations.
    """
    
    # ========== 实时更新配置 ==========
    enable_realtime_update: bool = True
    realtime_quality_threshold: float = 0.6   # 实时入库最低质量分
    candidate_pool_max_size: int = 1000       # 候选池最大容量
    auto_approve_threshold: float = 0.85      # 自动审批阈值
    
    # ========== 定时更新配置 ==========
    enable_scheduled_update: bool = True
    batch_update_interval: int = 86400        # 批量更新间隔（秒），默认24小时
    batch_update_time: str = "03:00"          # 批量更新时间（HH:MM）
    index_rebuild_interval: int = 604800      # 索引重建间隔（秒），默认7天
    
    # ========== 增量更新配置 ==========
    enable_change_log: bool = True
    change_log_max_entries: int = 10000       # 变更日志最大条目
    enable_rollback: bool = True              # 是否支持回滚
    rollback_window_hours: int = 72           # 回滚窗口（小时）
    
    # ========== 量化指标配置 ==========
    metrics_calculation_interval: int = 3600  # 指标计算间隔（秒）
    health_warning_threshold: float = 60.0    # 健康预警阈值
    health_critical_threshold: float = 40.0   # 健康严重阈值
    metrics_history_limit: int = 720          # 指标历史保留数量（30天*24小时）
    
    # ========== 查询日志配置 ==========
    enable_query_logging: bool = True
    query_log_max_entries: int = 10000        # 查询日志最大条目
    hit_threshold: float = 0.5                # 命中阈值（相似度）
    
    # ========== 权重配置（用于健康度计算）==========
    scale_weight: float = 0.2                 # 规模指标权重
    freshness_weight: float = 0.3             # 新鲜度权重
    quality_weight: float = 0.3               # 质量权重
    connectivity_weight: float = 0.2          # 连通性权重
    
    # ========== 评分配置（用于候选评估）==========
    relevance_weight: float = 0.4             # 相关性评分权重
    novelty_weight: float = 0.3               # 新颖性评分权重
    credibility_weight: float = 0.3           # 可信度评分权重
    
    # ========== 知识积累配置 ==========
    enable_query_driven_accumulation: bool = True  # 启用查询驱动知识积累
    accumulate_high_quality_answers: bool = True   # 积累高质量回答
    min_answer_confidence: float = 0.8             # 最低回答置信度
    gap_detection_enabled: bool = True             # 启用知识缺口检测
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """从字典创建"""
        # 只保留有效的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
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
    def default(cls) -> "KnowledgeEvolutionConfig":
        """
        默认配置
        
        Returns:
            KnowledgeEvolutionConfig: 默认配置实例
        """
        return cls()
    
    @classmethod
    def aggressive(cls) -> "KnowledgeEvolutionConfig":
        """
        积极更新策略
        
        特点：
        - 更低的质量阈值，允许更多知识入库
        - 更低的自动审批阈值
        - 更频繁的批量更新
        
        Returns:
            KnowledgeEvolutionConfig: 积极策略配置
        """
        return cls(
            realtime_quality_threshold=0.5,
            auto_approve_threshold=0.7,
            batch_update_interval=43200,  # 12小时
            health_warning_threshold=50.0,
            min_answer_confidence=0.7,
        )
    
    @classmethod
    def conservative(cls) -> "KnowledgeEvolutionConfig":
        """
        保守更新策略
        
        特点：
        - 更高的质量阈值，确保知识质量
        - 更高的自动审批阈值
        - 更长的批量更新间隔
        
        Returns:
            KnowledgeEvolutionConfig: 保守策略配置
        """
        return cls(
            realtime_quality_threshold=0.8,
            auto_approve_threshold=0.95,
            batch_update_interval=172800,  # 48小时
            health_warning_threshold=70.0,
            min_answer_confidence=0.9,
        )
    
    @classmethod
    def minimal(cls) -> "KnowledgeEvolutionConfig":
        """
        最小配置（仅核心功能）
        
        特点：
        - 禁用定时更新
        - 禁用变更日志
        - 禁用查询驱动积累
        
        Returns:
            KnowledgeEvolutionConfig: 最小配置
        """
        return cls(
            enable_realtime_update=True,
            enable_scheduled_update=False,
            enable_change_log=False,
            enable_rollback=False,
            enable_query_logging=False,
            enable_query_driven_accumulation=False,
            gap_detection_enabled=False,
        )
    
    def validate(self) -> bool:
        """
        验证配置有效性
        
        Returns:
            bool: 配置是否有效
            
        Raises:
            ValueError: 配置无效时抛出
        """
        errors = []
        
        # 阈值验证
        if not 0.0 <= self.realtime_quality_threshold <= 1.0:
            errors.append("realtime_quality_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.auto_approve_threshold <= 1.0:
            errors.append("auto_approve_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.health_warning_threshold <= 100.0:
            errors.append("health_warning_threshold must be between 0.0 and 100.0")
        if not 0.0 <= self.health_critical_threshold <= 100.0:
            errors.append("health_critical_threshold must be between 0.0 and 100.0")
        
        # 逻辑验证
        if self.health_critical_threshold >= self.health_warning_threshold:
            errors.append("health_critical_threshold must be less than health_warning_threshold")
        if self.realtime_quality_threshold > self.auto_approve_threshold:
            errors.append("realtime_quality_threshold should not exceed auto_approve_threshold")
        
        # 权重验证
        weight_sum = self.scale_weight + self.freshness_weight + self.quality_weight + self.connectivity_weight
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"Health weights should sum to 1.0, got {weight_sum}")
        
        score_weight_sum = self.relevance_weight + self.novelty_weight + self.credibility_weight
        if abs(score_weight_sum - 1.0) > 0.01:
            errors.append(f"Score weights should sum to 1.0, got {score_weight_sum}")
        
        # 间隔验证
        if self.batch_update_interval < 3600:
            errors.append("batch_update_interval should be at least 3600 seconds (1 hour)")
        if self.metrics_calculation_interval < 60:
            errors.append("metrics_calculation_interval should be at least 60 seconds")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
        
        return True


# 预设配置别名
DEFAULT_CONFIG = KnowledgeEvolutionConfig.default
AGGRESSIVE_CONFIG = KnowledgeEvolutionConfig.aggressive
CONSERVATIVE_CONFIG = KnowledgeEvolutionConfig.conservative
MINIMAL_CONFIG = KnowledgeEvolutionConfig.minimal
