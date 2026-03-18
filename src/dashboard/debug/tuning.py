"""
参数调优服务 - Parameter Tuning Service
提供RAG系统参数的实时调整、A/B测试和优化建议功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ParameterType(str, Enum):
    """参数类型枚举"""
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"
    RANGE = "range"


class OptimizationStrategy(str, Enum):
    """优化策略枚举"""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GRADIENT_BASED = "gradient_based"


@dataclass
class ParameterConfig:
    """参数配置数据模型"""
    name: str
    param_type: ParameterType
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    choices: Optional[List[Any]] = None
    step: Optional[float] = None
    description: str = ""
    category: str = "general"
    is_tunable: bool = True
    impact_level: str = "medium"  # low, medium, high
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['param_type'] = self.param_type.value
        return data


@dataclass
class ParameterValue:
    """参数值数据模型"""
    name: str
    value: Any
    timestamp: datetime
    source: str = "manual"  # manual, auto, ab_test
    experiment_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class ExperimentConfig:
    """实验配置数据模型"""
    experiment_id: str
    name: str
    parameters: Dict[str, Any]
    strategy: OptimizationStrategy
    iterations: int
    timeout_seconds: int
    target_metric: str
    baseline_config: Dict[str, Any]
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['strategy'] = self.strategy.value
        return data


@dataclass
class ExperimentResult:
    """实验结果数据模型"""
    experiment_id: str
    iteration: int
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    duration_ms: int
    timestamp: datetime
    improvement: Optional[float] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ParameterStore(ABC):
    """参数存储抽象基类"""
    
    @abstractmethod
    async def get_parameter(self, name: str) -> Optional[ParameterValue]:
        """获取参数值"""
        pass
    
    @abstractmethod
    async def set_parameter(self, name: str, value: Any, source: str = "manual") -> bool:
        """设置参数值"""
        pass
    
    @abstractmethod
    async def get_all_parameters(self) -> Dict[str, ParameterValue]:
        """获取所有参数"""
        pass


class InMemoryParameterStore(ParameterStore):
    """内存参数存储实现"""
    
    def __init__(self):
        self.parameters: Dict[str, ParameterValue] = {}
        self.parameter_configs: Dict[str, ParameterConfig] = {}
        self.lock = asyncio.Lock()
    
    async def register_parameter(self, config: ParameterConfig):
        """注册参数配置"""
        async with self.lock:
            self.parameter_configs[config.name] = config
            # 设置默认值
            if config.name not in self.parameters:
                self.parameters[config.name] = ParameterValue(
                    name=config.name,
                    value=config.default_value,
                    timestamp=datetime.now(),
                    source="default"
                )
            logger.info(f"注册参数: {config.name}")
    
    async def get_parameter(self, name: str) -> Optional[ParameterValue]:
        """获取参数值"""
        return self.parameters.get(name)
    
    async def set_parameter(self, name: str, value: Any, source: str = "manual") -> bool:
        """设置参数值"""
        async with self.lock:
            if name not in self.parameter_configs:
                logger.warning(f"参数 {name} 未注册")
                return False
            
            # 验证参数值
            if not self._validate_parameter_value(name, value):
                logger.warning(f"参数值无效: {name} = {value}")
                return False
            
            self.parameters[name] = ParameterValue(
                name=name,
                value=value,
                timestamp=datetime.now(),
                source=source
            )
            
            logger.info(f"设置参数: {name} = {value} (来源: {source})")
            return True
    
    async def get_all_parameters(self) -> Dict[str, ParameterValue]:
        """获取所有参数"""
        return self.parameters.copy()
    
    async def get_parameters_by_category(self, category: str) -> Dict[str, ParameterValue]:
        """按类别获取参数"""
        result = {}
        for name, param in self.parameters.items():
            config = self.parameter_configs.get(name)
            if config and config.category == category:
                result[name] = param
        return result
    
    def _validate_parameter_value(self, name: str, value: Any) -> bool:
        """验证参数值"""
        config = self.parameter_configs.get(name)
        if not config:
            return False
        
        try:
            # 类型验证
            if config.param_type == ParameterType.INTEGER:
                if not isinstance(value, int):
                    return False
                if config.min_value is not None and value < config.min_value:
                    return False
                if config.max_value is not None and value > config.max_value:
                    return False
                    
            elif config.param_type == ParameterType.FLOAT:
                if not isinstance(value, (int, float)):
                    return False
                if config.min_value is not None and value < config.min_value:
                    return False
                if config.max_value is not None and value > config.max_value:
                    return False
                    
            elif config.param_type == ParameterType.BOOLEAN:
                if not isinstance(value, bool):
                    return False
                    
            elif config.param_type == ParameterType.ENUM:
                if config.choices and value not in config.choices:
                    return False
                    
            elif config.param_type == ParameterType.RANGE:
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    return False
                if config.min_value is not None and value[0] < config.min_value:
                    return False
                if config.max_value is not None and value[1] > config.max_value:
                    return False
                    
        except Exception as e:
            logger.error(f"参数验证失败 {name}: {e}")
            return False
        
        return True


class ParameterOptimizer:
    """参数优化器"""
    
    def __init__(self, parameter_store: ParameterStore):
        """
        初始化参数优化器
        
        Args:
            parameter_store: 参数存储
        """
        self.parameter_store = parameter_store
        self.experiments: Dict[str, ExperimentConfig] = {}
        self.experiment_results: Dict[str, List[ExperimentResult]] = {}
        self.optimizers: Dict[OptimizationStrategy, Callable] = {}
        self.result_handlers: List[Callable] = []
        
        # 注册默认优化器
        self._register_default_optimizers()
    
    def _register_default_optimizers(self):
        """注册默认优化器"""
        self.optimizers[OptimizationStrategy.GRID_SEARCH] = self._grid_search_optimizer
        self.optimizers[OptimizationStrategy.RANDOM_SEARCH] = self._random_search_optimizer
    
    def register_optimizer(self, strategy: OptimizationStrategy, optimizer_func: Callable):
        """
        注册自定义优化器
        
        Args:
            strategy: 优化策略
            optimizer_func: 优化器函数
        """
        self.optimizers[strategy] = optimizer_func
        logger.info(f"注册优化器: {strategy.value}")
    
    def add_result_handler(self, handler: Callable):
        """
        添加结果处理器
        
        Args:
            handler: 结果处理函数
        """
        self.result_handlers.append(handler)
    
    async def create_experiment(self, 
                              name: str,
                              parameters: List[str],
                              strategy: OptimizationStrategy,
                              iterations: int,
                              target_metric: str,
                              timeout_seconds: int = 3600) -> str:
        """
        创建优化实验
        
        Args:
            name: 实验名称
            parameters: 要优化的参数列表
            strategy: 优化策略
            iterations: 迭代次数
            target_metric: 目标指标
            timeout_seconds: 超时时间
            
        Returns:
            实验ID
        """
        experiment_id = f"exp_{int(datetime.now().timestamp() * 1000)}"
        
        # 获取当前参数配置作为基准
        current_params = await self.parameter_store.get_all_parameters()
        baseline_config = {name: param.value for name, param in current_params.items() 
                          if name in parameters}
        
        # 创建实验配置
        config = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            parameters={name: True for name in parameters},  # 标记要优化的参数
            strategy=strategy,
            iterations=iterations,
            timeout_seconds=timeout_seconds,
            target_metric=target_metric,
            baseline_config=baseline_config,
            created_at=datetime.now()
        )
        
        self.experiments[experiment_id] = config
        self.experiment_results[experiment_id] = []
        
        logger.info(f"创建实验: {experiment_id} ({name})")
        return experiment_id
    
    async def run_experiment(self, experiment_id: str) -> bool:
        """
        运行实验
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            是否成功启动
        """
        if experiment_id not in self.experiments:
            logger.error(f"实验不存在: {experiment_id}")
            return False
        
        config = self.experiments[experiment_id]
        if config.status != "pending":
            logger.warning(f"实验状态不正确: {config.status}")
            return False
        
        # 更新状态
        config.status = "running"
        
        try:
            # 获取优化器
            optimizer = self.optimizers.get(config.strategy)
            if not optimizer:
                raise ValueError(f"不支持的优化策略: {config.strategy}")
            
            # 运行优化
            await optimizer(config)
            config.status = "completed"
            logger.info(f"实验完成: {experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"实验执行失败 {experiment_id}: {e}")
            config.status = "failed"
            return False
    
    async def _grid_search_optimizer(self, config: ExperimentConfig):
        """网格搜索优化器"""
        # 获取参数配置
        param_configs = {}
        for param_name in config.parameters.keys():
            # 这里应该从parameter_store获取参数配置
            pass
        
        # 生成参数组合（简化版）
        # 实际实现需要根据参数类型和范围生成网格
        
        # 运行每次迭代
        for i in range(config.iterations):
            # 生成参数组合
            params = self._generate_grid_params(param_configs, i)
            
            # 应用参数
            for name, value in params.items():
                await self.parameter_store.set_parameter(name, value, f"experiment_{config.experiment_id}")
            
            # 运行评估（模拟）
            metrics = await self._evaluate_parameters(params, config.target_metric)
            
            # 记录结果
            result = ExperimentResult(
                experiment_id=config.experiment_id,
                iteration=i,
                parameters=params,
                metrics=metrics,
                duration_ms=1000,  # 模拟值
                timestamp=datetime.now()
            )
            
            self.experiment_results[config.experiment_id].append(result)
            
            # 调用结果处理器
            for handler in self.result_handlers:
                try:
                    await handler(result)
                except Exception as e:
                    logger.error(f"结果处理器执行失败: {e}")
    
    async def _random_search_optimizer(self, config: ExperimentConfig):
        """随机搜索优化器"""
        # 类似网格搜索，但参数值随机生成
        pass
    
    def _generate_grid_params(self, param_configs: Dict, iteration: int) -> Dict[str, Any]:
        """生成网格参数组合"""
        # 简化实现，实际需要复杂的空间划分逻辑
        params = {}
        for name, config in param_configs.items():
            if config.param_type == ParameterType.INTEGER:
                # 简单的线性划分
                range_size = config.max_value - config.min_value
                step = range_size / 10  # 10个等级
                value = config.min_value + (iteration % 10) * step
                params[name] = int(value)
            elif config.param_type == ParameterType.FLOAT:
                range_size = config.max_value - config.min_value
                step = range_size / 10
                value = config.min_value + (iteration % 10) * step
                params[name] = float(value)
        return params
    
    async def _evaluate_parameters(self, params: Dict[str, Any], target_metric: str) -> Dict[str, float]:
        """评估参数配置"""
        # 模拟评估结果
        # 实际实现需要调用真实的评估函数
        return {
            target_metric: 0.85 + (hash(str(params)) % 100) / 1000,  # 模拟分数
            "response_time": 150 + (hash(str(params)) % 200),
            "accuracy": 0.90 + (hash(str(params)) % 50) / 1000
        }
    
    async def get_experiment_results(self, experiment_id: str) -> List[ExperimentResult]:
        """
        获取实验结果
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            实验结果列表
        """
        return self.experiment_results.get(experiment_id, [])
    
    async def get_best_parameters(self, experiment_id: str, metric: str = None) -> Optional[Dict[str, Any]]:
        """
        获取最优参数配置
        
        Args:
            experiment_id: 实验ID
            metric: 评估指标（默认使用实验配置的目标指标）
            
        Returns:
            最优参数配置
        """
        if experiment_id not in self.experiments:
            return None
        
        config = self.experiments[experiment_id]
        results = self.experiment_results.get(experiment_id, [])
        
        if not results:
            return None
        
        target_metric = metric or config.target_metric
        
        # 找到最佳结果
        best_result = max(results, key=lambda r: r.metrics.get(target_metric, 0))
        
        return best_result.parameters


# 默认RAG参数配置
DEFAULT_RAG_PARAMETERS = [
    ParameterConfig(
        name="top_k",
        param_type=ParameterType.INTEGER,
        default_value=10,
        min_value=1,
        max_value=100,
        description="检索返回的文档数量",
        category="retrieval",
        impact_level="high"
    ),
    ParameterConfig(
        name="similarity_threshold",
        param_type=ParameterType.FLOAT,
        default_value=0.7,
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        description="相似度阈值",
        category="retrieval",
        impact_level="medium"
    ),
    ParameterConfig(
        name="rerank_enabled",
        param_type=ParameterType.BOOLEAN,
        default_value=True,
        description="是否启用重排序",
        category="reranking",
        impact_level="medium"
    ),
    ParameterConfig(
        name="rerank_top_k",
        param_type=ParameterType.INTEGER,
        default_value=5,
        min_value=1,
        max_value=20,
        description="重排序返回的文档数量",
        category="reranking",
        impact_level="low"
    ),
    ParameterConfig(
        name="temperature",
        param_type=ParameterType.FLOAT,
        default_value=0.7,
        min_value=0.0,
        max_value=2.0,
        step=0.1,
        description="生成温度",
        category="generation",
        impact_level="high"
    ),
    ParameterConfig(
        name="max_tokens",
        param_type=ParameterType.INTEGER,
        default_value=2048,
        min_value=100,
        max_value=8192,
        description="最大生成token数",
        category="generation",
        impact_level="medium"
    )
]


# 使用示例和测试函数
async def demo_parameter_tuning():
    """演示参数调优功能"""
    
    # 创建参数存储
    param_store = InMemoryParameterStore()
    
    # 注册默认参数
    for param_config in DEFAULT_RAG_PARAMETERS:
        await param_store.register_parameter(param_config)
    
    # 创建优化器
    optimizer = ParameterOptimizer(param_store)
    
    # 添加结果处理器
    async def result_handler(result: ExperimentResult):
        print(f"📊 实验结果 #{result.iteration}: {result.metrics}")
    
    optimizer.add_result_handler(result_handler)
    
    # 创建实验
    experiment_id = await optimizer.create_experiment(
        name="RAG参数优化实验",
        parameters=["top_k", "similarity_threshold", "temperature"],
        strategy=OptimizationStrategy.GRID_SEARCH,
        iterations=5,
        target_metric="accuracy"
    )
    
    print(f"创建实验: {experiment_id}")
    
    # 运行实验
    success = await optimizer.run_experiment(experiment_id)
    print(f"实验执行: {'成功' if success else '失败'}")
    
    # 获取最优参数
    best_params = await optimizer.get_best_parameters(experiment_id)
    print(f"最优参数: {best_params}")
    
    # 查看所有参数
    all_params = await param_store.get_all_parameters()
    print(f"当前参数:")
    for name, param in all_params.items():
        print(f"  {name}: {param.value} (来源: {param.source})")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_parameter_tuning())