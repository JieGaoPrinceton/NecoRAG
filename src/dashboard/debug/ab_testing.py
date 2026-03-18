"""
A/B测试框架 - A/B Testing Framework
支持多配置对比测试、统计分析和结果可视化
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json
import hashlib
from collections import defaultdict
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """测试状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TestType(str, Enum):
    """测试类型枚举"""
    PARAMETER = "parameter"
    ALGORITHM = "algorithm"
    CONFIGURATION = "configuration"
    MODEL = "model"


class StatisticalTest(str, Enum):
    """统计检验类型"""
    T_TEST = "t_test"
    CHI_SQUARE = "chi_square"
    ANOVA = "anova"
    MANN_WHITNEY = "mann_whitney"


@dataclass
class TestVariant:
    """测试变体数据模型"""
    variant_id: str
    name: str
    config: Dict[str, Any]
    weight: float = 1.0  # 流量分配权重
    sample_size: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        return data


@dataclass
class ABTestConfig:
    """A/B测试配置"""
    test_id: str
    test_name: str
    test_type: TestType
    variants: List[TestVariant]
    primary_metric: str
    secondary_metrics: List[str]
    statistical_test: StatisticalTest
    minimum_sample_size: int
    significance_level: float = 0.05
    power: float = 0.8
    duration_days: int = 7
    created_at: datetime = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: TestStatus = TestStatus.PENDING
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.secondary_metrics is None:
            self.secondary_metrics = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.ended_at:
            data['ended_at'] = self.ended_at.isoformat()
        data['test_type'] = self.test_type.value
        data['statistical_test'] = self.statistical_test.value
        data['status'] = self.status.value
        return data


@dataclass
class TestResult:
    """测试结果数据模型"""
    test_id: str
    variant_id: str
    metric_name: str
    sample_size: int
    mean: float
    std_dev: float
    confidence_interval: List[float]
    p_value: float
    statistical_significance: bool
    effect_size: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class TestReport:
    """测试报告数据模型"""
    test_id: str
    winner_variant: Optional[str]
    statistical_confidence: float
    business_impact: float
    recommendations: List[str]
    detailed_results: List[TestResult]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.recommendations is None:
            self.recommendations = []
        if self.detailed_results is None:
            self.detailed_results = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['detailed_results'] = [r.to_dict() for r in self.detailed_results]
        return data


class ABTestingFramework:
    """A/B测试框架"""
    
    def __init__(self):
        self.tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        self.test_reports: Dict[str, TestReport] = {}
        self.variant_assignments: Dict[str, str] = {}  # user_id -> variant_id
        self.metric_collectors: Dict[str, Callable] = {}
        self.statistical_tests: Dict[StatisticalTest, Callable] = {}
        
        # 注册默认统计检验方法
        self._register_statistical_tests()
    
    def _register_statistical_tests(self):
        """注册默认统计检验方法"""
        self.statistical_tests[StatisticalTest.T_TEST] = self._perform_t_test
        self.statistical_tests[StatisticalTest.CHI_SQUARE] = self._perform_chi_square
        self.statistical_tests[StatisticalTest.ANOVA] = self._perform_anova
        self.statistical_tests[StatisticalTest.MANN_WHITNEY] = self._perform_mann_whitney
    
    async def create_test(self, 
                         test_name: str,
                         test_type: TestType,
                         variants: List[Dict[str, Any]],
                         primary_metric: str,
                         secondary_metrics: Optional[List[str]] = None,
                         statistical_test: StatisticalTest = StatisticalTest.T_TEST,
                         minimum_sample_size: int = 1000,
                         significance_level: float = 0.05) -> str:
        """
        创建A/B测试
        
        Args:
            test_name: 测试名称
            test_type: 测试类型
            variants: 变体配置列表
            primary_metric: 主要指标
            secondary_metrics: 次要指标
            statistical_test: 统计检验方法
            minimum_sample_size: 最小样本量
            significance_level: 显著性水平
            
        Returns:
            测试ID
        """
        test_id = f"ab_test_{int(datetime.now().timestamp() * 1000)}"
        
        # 创建变体对象
        test_variants = []
        total_weight = sum(v.get('weight', 1.0) for v in variants)
        
        for i, variant_config in enumerate(variants):
            variant = TestVariant(
                variant_id=f"{test_id}_variant_{i}",
                name=variant_config.get('name', f'Variant {chr(65+i)}'),
                config=variant_config.get('config', {}),
                weight=variant_config.get('weight', 1.0) / total_weight
            )
            test_variants.append(variant)
        
        # 创建测试配置
        config = ABTestConfig(
            test_id=test_id,
            test_name=test_name,
            test_type=test_type,
            variants=test_variants,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            statistical_test=statistical_test,
            minimum_sample_size=minimum_sample_size,
            significance_level=significance_level
        )
        
        self.tests[test_id] = config
        self.test_results[test_id] = []
        
        logger.info(f"创建A/B测试: {test_id} ({test_name})")
        return test_id
    
    async def start_test(self, test_id: str) -> bool:
        """
        启动测试
        
        Args:
            test_id: 测试ID
            
        Returns:
            是否成功启动
        """
        if test_id not in self.tests:
            logger.error(f"测试不存在: {test_id}")
            return False
        
        config = self.tests[test_id]
        if config.status != TestStatus.PENDING:
            logger.warning(f"测试状态不正确: {config.status}")
            return False
        
        config.status = TestStatus.RUNNING
        config.started_at = datetime.now()
        
        logger.info(f"启动A/B测试: {test_id}")
        return True
    
    async def assign_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """
        为用户分配测试变体
        
        Args:
            test_id: 测试ID
            user_id: 用户ID
            
        Returns:
            分配的变体ID
        """
        if test_id not in self.tests:
            return None
        
        config = self.tests[test_id]
        if config.status != TestStatus.RUNNING:
            return None
        
        # 检查是否已有分配
        assignment_key = f"{test_id}_{user_id}"
        if assignment_key in self.variant_assignments:
            return self.variant_assignments[assignment_key]
        
        # 基于哈希的流量分配
        hash_value = int(hashlib.md5(f"{test_id}_{user_id}".encode()).hexdigest()[:8], 16)
        random_value = hash_value % 1000 / 1000.0
        
        cumulative_weight = 0.0
        for variant in config.variants:
            cumulative_weight += variant.weight
            if random_value <= cumulative_weight:
                self.variant_assignments[assignment_key] = variant.variant_id
                variant.sample_size += 1
                return variant.variant_id
        
        # 默认返回第一个变体
        if config.variants:
            variant = config.variants[0]
            self.variant_assignments[assignment_key] = variant.variant_id
            variant.sample_size += 1
            return variant.variant_id
        
        return None
    
    async def record_conversion(self, test_id: str, variant_id: str, user_id: str, 
                              metric_value: float = 1.0):
        """
        记录转化事件
        
        Args:
            test_id: 测试ID
            variant_id: 变体ID
            user_id: 用户ID
            metric_value: 指标值
        """
        if test_id not in self.tests:
            return
        
        config = self.tests[test_id]
        variant = next((v for v in config.variants if v.variant_id == variant_id), None)
        if not variant:
            return
        
        # 更新转化数据
        variant.conversions += 1
        variant.conversion_rate = variant.conversions / variant.sample_size if variant.sample_size > 0 else 0
        
        # 记录指标值
        if config.primary_metric not in variant.metrics:
            variant.metrics[config.primary_metric] = []
        variant.metrics[config.primary_metric].append(metric_value)
    
    async def record_metric(self, test_id: str, variant_id: str, metric_name: str, 
                          value: float):
        """
        记录指标数据
        
        Args:
            test_id: 测试ID
            variant_id: 变体ID
            metric_name: 指标名称
            value: 指标值
        """
        if test_id not in self.tests:
            return
        
        config = self.tests[test_id]
        variant = next((v for v in config.variants if v.variant_id == variant_id), None)
        if not variant:
            return
        
        if metric_name not in variant.metrics:
            variant.metrics[metric_name] = []
        variant.metrics[metric_name].append(value)
    
    async def analyze_test(self, test_id: str) -> Optional[TestReport]:
        """
        分析测试结果
        
        Args:
            test_id: 测试ID
            
        Returns:
            测试报告
        """
        if test_id not in self.tests:
            return None
        
        config = self.tests[test_id]
        if config.status != TestStatus.RUNNING:
            logger.warning(f"测试未在运行中: {test_id}")
            return None
        
        # 检查样本量
        total_samples = sum(v.sample_size for v in config.variants)
        if total_samples < config.minimum_sample_size:
            logger.warning(f"样本量不足: {total_samples} < {config.minimum_sample_size}")
            return None
        
        # 执行统计检验
        results = []
        winner_variant = None
        best_metric_value = float('-inf')
        statistical_confidence = 0.0
        
        # 对主要指标进行分析
        test_function = self.statistical_tests.get(config.statistical_test)
        if test_function:
            primary_results = await test_function(config, config.primary_metric)
            results.extend(primary_results)
            
            # 确定获胜变体
            for result in primary_results:
                if result.statistical_significance and result.effect_size > best_metric_value:
                    winner_variant = result.variant_id
                    best_metric_value = result.effect_size
                    statistical_confidence = 1 - result.p_value
        
        # 分析次要指标
        for secondary_metric in config.secondary_metrics:
            if test_function:
                secondary_results = await test_function(config, secondary_metric)
                results.extend(secondary_results)
        
        # 生成建议
        recommendations = await self._generate_recommendations(config, results, winner_variant)
        
        # 创建报告
        report = TestReport(
            test_id=test_id,
            winner_variant=winner_variant,
            statistical_confidence=statistical_confidence,
            business_impact=best_metric_value if winner_variant else 0.0,
            recommendations=recommendations,
            detailed_results=results
        )
        
        self.test_reports[test_id] = report
        config.status = TestStatus.COMPLETED
        config.ended_at = datetime.now()
        
        logger.info(f"A/B测试分析完成: {test_id}")
        return report
    
    async def _perform_t_test(self, config: ABTestConfig, metric_name: str) -> List[TestResult]:
        """执行t检验"""
        results = []
        
        # 收集各变体的数据
        variant_data = {}
        for variant in config.variants:
            if metric_name in variant.metrics and len(variant.metrics[metric_name]) > 1:
                variant_data[variant.variant_id] = variant.metrics[metric_name]
        
        if len(variant_data) < 2:
            return results
        
        # 两两比较
        variant_ids = list(variant_data.keys())
        for i in range(len(variant_ids)):
            for j in range(i + 1, len(variant_ids)):
                variant_a = variant_ids[i]
                variant_b = variant_ids[j]
                
                data_a = variant_data[variant_a]
                data_b = variant_data[variant_b]
                
                # 执行t检验
                t_stat, p_value = stats.ttest_ind(data_a, data_b)
                
                # 计算效应量
                effect_size = (statistics.mean(data_a) - statistics.mean(data_b)) / \
                             statistics.pooled_std(data_a, data_b) if len(data_a) > 1 and len(data_b) > 1 else 0
                
                # 计算置信区间
                pooled_std = np.sqrt(((len(data_a)-1)*np.var(data_a) + (len(data_b)-1)*np.var(data_b)) / 
                                   (len(data_a) + len(data_b) - 2))
                margin_of_error = 1.96 * pooled_std * np.sqrt(1/len(data_a) + 1/len(data_b))
                mean_diff = statistics.mean(data_a) - statistics.mean(data_b)
                confidence_interval = [mean_diff - margin_of_error, mean_diff + margin_of_error]
                
                result = TestResult(
                    test_id=config.test_id,
                    variant_id=variant_a,
                    metric_name=metric_name,
                    sample_size=len(data_a),
                    mean=statistics.mean(data_a),
                    std_dev=statistics.stdev(data_a) if len(data_a) > 1 else 0,
                    confidence_interval=confidence_interval,
                    p_value=p_value,
                    statistical_significance=p_value < config.significance_level,
                    effect_size=effect_size
                )
                results.append(result)
        
        return results
    
    async def _perform_chi_square(self, config: ABTestConfig, metric_name: str) -> List[TestResult]:
        """执行卡方检验"""
        # 简化实现
        return []
    
    async def _perform_anova(self, config: ABTestConfig, metric_name: str) -> List[TestResult]:
        """执行方差分析"""
        # 简化实现
        return []
    
    async def _perform_mann_whitney(self, config: ABTestConfig, metric_name: str) -> List[TestResult]:
        """执行Mann-Whitney U检验"""
        # 简化实现
        return []
    
    async def _generate_recommendations(self, config: ABTestConfig, results: List[TestResult], 
                                      winner_variant: Optional[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if winner_variant:
            winning_variant = next((v for v in config.variants if v.variant_id == winner_variant), None)
            if winning_variant:
                recommendations.append(f"推荐采用变体 {winning_variant.name} 的配置")
                recommendations.append(f"预计可带来 {winning_variant.conversion_rate*100:.2f}% 的转化率提升")
        
        # 基于统计显著性给出建议
        significant_results = [r for r in results if r.statistical_significance]
        if len(significant_results) > 0:
            recommendations.append("测试结果具有统计显著性，建议推广应用")
        else:
            recommendations.append("测试结果统计显著性不足，建议延长测试时间或调整样本量")
        
        # 基于效应量给出建议
        effect_sizes = [r.effect_size for r in results if r.effect_size is not None]
        if effect_sizes:
            avg_effect = statistics.mean(effect_sizes)
            if abs(avg_effect) > 0.5:
                recommendations.append("效应量较大，业务影响显著")
            elif abs(avg_effect) > 0.2:
                recommendations.append("效应量中等，具有一定业务价值")
            else:
                recommendations.append("效应量较小，业务影响有限")
        
        return recommendations
    
    async def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        获取测试状态
        
        Args:
            test_id: 测试ID
            
        Returns:
            测试状态信息
        """
        if test_id not in self.tests:
            return None
        
        config = self.tests[test_id]
        status_info = config.to_dict()
        
        # 添加实时统计信息
        total_samples = sum(v.sample_size for v in config.variants)
        status_info['total_samples'] = total_samples
        status_info['progress_percentage'] = min(100, (total_samples / config.minimum_sample_size) * 100)
        
        # 变体详细信息
        variant_stats = []
        for variant in config.variants:
            variant_stats.append({
                'variant_id': variant.variant_id,
                'name': variant.name,
                'sample_size': variant.sample_size,
                'conversions': variant.conversions,
                'conversion_rate': variant.conversion_rate,
                'weight': variant.weight
            })
        status_info['variants'] = variant_stats
        
        return status_info
    
    async def pause_test(self, test_id: str) -> bool:
        """暂停测试"""
        if test_id not in self.tests:
            return False
        
        config = self.tests[test_id]
        if config.status == TestStatus.RUNNING:
            config.status = TestStatus.PAUSED
            logger.info(f"暂停A/B测试: {test_id}")
            return True
        return False
    
    async def resume_test(self, test_id: str) -> bool:
        """恢复测试"""
        if test_id not in self.tests:
            return False
        
        config = self.tests[test_id]
        if config.status == TestStatus.PAUSED:
            config.status = TestStatus.RUNNING
            logger.info(f"恢复A/B测试: {test_id}")
            return True
        return False
    
    async def get_all_tests(self) -> List[Dict[str, Any]]:
        """获取所有测试"""
        return [config.to_dict() for config in self.tests.values()]


# 扩展statistics模块
def pooled_std(data1, data2):
    """计算合并标准差"""
    n1, n2 = len(data1), len(data2)
    var1, var2 = np.var(data1, ddof=1), np.var(data2, ddof=1)
    return np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))


# 使用示例和测试函数
async def demo_ab_testing():
    """演示A/B测试功能"""
    
    # 创建测试框架
    ab_framework = ABTestingFramework()
    
    # 创建A/B测试
    test_id = await ab_framework.create_test(
        test_name="检索算法优化测试",
        test_type=TestType.ALGORITHM,
        variants=[
            {
                'name': '原始算法',
                'config': {'algorithm': 'bm25', 'parameters': {'k1': 1.2, 'b': 0.75}},
                'weight': 0.5
            },
            {
                'name': '优化算法',
                'config': {'algorithm': 'bm25+', 'parameters': {'k1': 1.5, 'b': 0.8}},
                'weight': 0.5
            }
        ],
        primary_metric='accuracy',
        secondary_metrics=['response_time', 'user_satisfaction'],
        statistical_test=StatisticalTest.T_TEST,
        minimum_sample_size=500
    )
    
    print(f"创建测试: {test_id}")
    
    # 启动测试
    await ab_framework.start_test(test_id)
    
    # 模拟用户分配和数据收集
    users = [f"user_{i}" for i in range(1000)]
    
    for user_id in users:
        # 分配变体
        variant_id = await ab_framework.assign_variant(test_id, user_id)
        if not variant_id:
            continue
        
        # 模拟用户行为数据
        import random
        if '原始算法' in variant_id:
            accuracy = random.uniform(0.7, 0.85)
            response_time = random.uniform(200, 400)
        else:
            accuracy = random.uniform(0.75, 0.9)
            response_time = random.uniform(150, 350)
        
        # 记录指标
        await ab_framework.record_metric(test_id, variant_id, 'accuracy', accuracy)
        await ab_framework.record_metric(test_id, variant_id, 'response_time', response_time)
        
        # 模拟转化
        if accuracy > 0.8:
            await ab_framework.record_conversion(test_id, variant_id, user_id)
    
    # 分析测试结果
    report = await ab_framework.analyze_test(test_id)
    
    if report:
        print("\n=== A/B测试报告 ===")
        print(f"获胜变体: {report.winner_variant}")
        print(f"统计置信度: {report.statistical_confidence:.3f}")
        print(f"业务影响: {report.business_impact:.3f}")
        print("\n优化建议:")
        for recommendation in report.recommendations:
            print(f"  • {recommendation}")
    
    # 获取测试状态
    status = await ab_framework.get_test_status(test_id)
    print(f"\n测试状态: {status['status']}")
    print(f"总样本数: {status['total_samples']}")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_ab_testing())