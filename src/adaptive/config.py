"""
Adaptive Learning 配置类

定义自适应学习引擎的配置选项。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Type, TypeVar
import json


T = TypeVar('T', bound='AdaptiveLearningConfig')


@dataclass
class AdaptiveLearningConfig:
    """
    自适应学习引擎配置
    
    Configuration for the adaptive learning engine.
    """
    
    # ========== 反馈收集配置 ==========
    enable_feedback_collection: bool = True
    feedback_history_size: int = 1000       # 保留的反馈记录数
    implicit_feedback_enabled: bool = True   # 启用隐式反馈
    
    # ========== 用户偏好学习配置 ==========
    enable_preference_learning: bool = True
    preference_update_interval: int = 5      # 每N次交互更新偏好
    expertise_learning_rate: float = 0.1     # 专业度学习速率
    satisfaction_window: int = 20            # 满意度滑动窗口大小
    max_complexity_history: int = 50         # 复杂度历史最大长度
    
    # ========== 策略优化配置 ==========
    enable_strategy_optimization: bool = True
    strategy_learning_rate: float = 0.05     # 策略权重学习率
    min_samples_for_optimization: int = 10   # 最少样本数才开始优化
    exploration_rate: float = 0.1            # 探索率（epsilon-greedy）
    default_strategies: list = field(default_factory=lambda: [
        "vector_search",
        "hybrid_search",
        "graph_enhanced",
        "hyde_enhanced",
    ])
    
    # ========== 集体智慧配置 ==========
    enable_collective_learning: bool = True
    min_users_for_insight: int = 3           # 最少用户数才生成洞察
    insight_refresh_interval: int = 86400    # 洞察刷新间隔（秒）
    max_insights: int = 100                  # 最大洞察数量
    
    # ========== 指标配置 ==========
    metrics_window_days: int = 30            # 指标计算窗口（天）
    trend_comparison_ratio: float = 0.5      # 趋势比较的时间分割比例
    
    # ========== 交互记录配置 ==========
    max_interaction_history: int = 10000     # 最大交互记录数
    interaction_retention_days: int = 90     # 交互记录保留天数
    
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
    def default(cls) -> "AdaptiveLearningConfig":
        """
        默认配置
        
        Returns:
            AdaptiveLearningConfig: 默认配置实例
        """
        return cls()
    
    @classmethod
    def aggressive(cls) -> "AdaptiveLearningConfig":
        """
        积极学习模式
        
        特点：
        - 更频繁的偏好更新
        - 更高的学习速率
        - 更高的探索率
        
        Returns:
            AdaptiveLearningConfig: 积极学习配置
        """
        return cls(
            preference_update_interval=3,
            expertise_learning_rate=0.2,
            strategy_learning_rate=0.1,
            exploration_rate=0.2,
            min_samples_for_optimization=5,
        )
    
    @classmethod
    def conservative(cls) -> "AdaptiveLearningConfig":
        """
        保守学习模式
        
        特点：
        - 更少的偏好更新
        - 更低的学习速率
        - 更低的探索率
        
        Returns:
            AdaptiveLearningConfig: 保守学习配置
        """
        return cls(
            preference_update_interval=10,
            expertise_learning_rate=0.05,
            strategy_learning_rate=0.02,
            exploration_rate=0.05,
            min_samples_for_optimization=20,
        )
    
    @classmethod
    def minimal(cls) -> "AdaptiveLearningConfig":
        """
        最小配置（仅核心功能）
        
        特点：
        - 禁用集体学习
        - 禁用隐式反馈
        
        Returns:
            AdaptiveLearningConfig: 最小配置
        """
        return cls(
            enable_feedback_collection=True,
            implicit_feedback_enabled=False,
            enable_preference_learning=True,
            enable_strategy_optimization=True,
            enable_collective_learning=False,
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
        
        # 范围验证
        if not 0.0 <= self.exploration_rate <= 1.0:
            errors.append("exploration_rate must be between 0.0 and 1.0")
        if not 0.0 < self.expertise_learning_rate <= 1.0:
            errors.append("expertise_learning_rate must be between 0.0 and 1.0")
        if not 0.0 < self.strategy_learning_rate <= 1.0:
            errors.append("strategy_learning_rate must be between 0.0 and 1.0")
        if not 0.0 < self.trend_comparison_ratio < 1.0:
            errors.append("trend_comparison_ratio must be between 0.0 and 1.0")
        
        # 数值验证
        if self.feedback_history_size < 10:
            errors.append("feedback_history_size should be at least 10")
        if self.preference_update_interval < 1:
            errors.append("preference_update_interval should be at least 1")
        if self.min_samples_for_optimization < 1:
            errors.append("min_samples_for_optimization should be at least 1")
        if self.satisfaction_window < 5:
            errors.append("satisfaction_window should be at least 5")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(errors))
        
        return True


# 预设配置别名
DEFAULT_CONFIG = AdaptiveLearningConfig.default
AGGRESSIVE_CONFIG = AdaptiveLearningConfig.aggressive
CONSERVATIVE_CONFIG = AdaptiveLearningConfig.conservative
MINIMAL_CONFIG = AdaptiveLearningConfig.minimal
