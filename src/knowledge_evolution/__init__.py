"""
NecoRAG Knowledge Evolution Module - 知识库更新与演化

提供知识库的持续更新、演化和健康度监控功能，包括：
- 查询驱动知识积累
- 实时更新和定时批量更新
- 增量数据库更新
- 知识库量化指标计算
- 可视化数据接口
"""

from .models import (
    # 枚举类型
    UpdateMode,
    UpdateStatus,
    KnowledgeSource,
    CandidateStatus,
    # 数据类
    KnowledgeCandidate,
    UpdateTask,
    ChangeLogEntry,
    KnowledgeMetrics,
    HealthReport,
    QueryRecord,
    GrowthTrend,
)

from .config import (
    KnowledgeEvolutionConfig,
    DEFAULT_CONFIG,
    AGGRESSIVE_CONFIG,
    CONSERVATIVE_CONFIG,
    MINIMAL_CONFIG,
)

from .updater import (
    KnowledgeUpdater,
)

from .metrics import (
    KnowledgeMetricsCalculator,
)

from .scheduler import (
    ScheduledTask,
    UpdateScheduler,
    create_scheduler,
    HAS_APSCHEDULER,
)

from .visualizer import (
    KnowledgeVisualizer,
)


# 便捷函数
def create_knowledge_evolution(
    config: KnowledgeEvolutionConfig = None,
    memory_manager=None,
    auto_start_scheduler: bool = False
):
    """
    创建知识演化模块的便捷函数
    
    Args:
        config: 知识演化配置
        memory_manager: 记忆管理器实例
        auto_start_scheduler: 是否自动启动调度器
        
    Returns:
        Dict: 包含 updater, metrics, scheduler, visualizer 的字典
    """
    config = config or KnowledgeEvolutionConfig.default()
    
    # 创建各组件
    updater = KnowledgeUpdater(config=config, memory_manager=memory_manager)
    metrics = KnowledgeMetricsCalculator(config=config, memory_manager=memory_manager)
    scheduler = UpdateScheduler(config=config, updater=updater, metrics_calculator=metrics)
    visualizer = KnowledgeVisualizer(metrics_calculator=metrics, updater=updater, config=config)
    
    # 自动设置默认任务
    scheduler.setup_default_tasks()
    
    # 可选启动调度器
    if auto_start_scheduler:
        scheduler.start()
    
    return {
        "updater": updater,
        "metrics": metrics,
        "scheduler": scheduler,
        "visualizer": visualizer,
    }


__all__ = [
    # 枚举类型
    "UpdateMode",
    "UpdateStatus",
    "KnowledgeSource",
    "CandidateStatus",
    
    # 数据类
    "KnowledgeCandidate",
    "UpdateTask",
    "ChangeLogEntry",
    "KnowledgeMetrics",
    "HealthReport",
    "QueryRecord",
    "GrowthTrend",
    
    # 配置
    "KnowledgeEvolutionConfig",
    "DEFAULT_CONFIG",
    "AGGRESSIVE_CONFIG",
    "CONSERVATIVE_CONFIG",
    "MINIMAL_CONFIG",
    
    # 核心类
    "KnowledgeUpdater",
    "KnowledgeMetricsCalculator",
    "ScheduledTask",
    "UpdateScheduler",
    "KnowledgeVisualizer",
    
    # 便捷函数
    "create_knowledge_evolution",
    "create_scheduler",
    
    # 标志
    "HAS_APSCHEDULER",
]
