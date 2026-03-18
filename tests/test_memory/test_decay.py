"""
测试 NecoRAG 记忆衰减模块

测试内容：
- 记忆衰减计算
- 不同衰减策略
- 归档判断
- 记忆强化
"""

import pytest
import math
from datetime import datetime, timedelta

from src.memory.decay import MemoryDecay
from src.memory.models import MemoryItem, MemoryLayer


class TestMemoryDecayInit:
    """MemoryDecay 初始化测试"""
    
    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        decay = MemoryDecay()
        
        assert decay.decay_rate == 0.1
        assert decay.archive_threshold == 0.05
    
    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        decay = MemoryDecay(decay_rate=0.2, archive_threshold=0.1)
        
        assert decay.decay_rate == 0.2
        assert decay.archive_threshold == 0.1


class TestWeightCalculation:
    """权重计算测试"""
    
    def test_calculate_weight_immediate(self):
        """测试刚创建的记忆权重"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=now
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 刚创建的记忆，衰减应该很小
        # weight ≈ 1.0 * e^0 * (1 + log10(1)) = 1.0 * 1.0 = 1.0
        assert weight >= 0.9
    
    def test_calculate_weight_after_one_day(self):
        """测试一天后的记忆权重"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 衰减后权重应该小于初始权重
        # weight = 1.0 * e^(-0.1 * 1) * (1 + log10(1)) ≈ 0.905 * 1.0
        expected = math.exp(-0.1 * 1) * (1 + math.log10(1))
        assert abs(weight - expected) < 0.01
    
    def test_calculate_weight_after_ten_days(self):
        """测试十天后的记忆权重"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        ten_days_ago = now - timedelta(days=10)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=ten_days_ago
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 十天后衰减显著
        # weight = 1.0 * e^(-0.1 * 10) * 1.0 ≈ 0.368
        expected = math.exp(-0.1 * 10)
        assert abs(weight - expected) < 0.01
        assert weight < 0.5
    
    def test_calculate_weight_with_high_access_count(self):
        """测试高访问次数对权重的影响"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        # 低访问次数
        memory_low = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        # 高访问次数
        memory_high = MemoryItem(
            memory_id="mem-002",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=99,  # 100次访问
            created_at=one_day_ago
        )
        
        weight_low = decay.calculate_weight(memory_low, current_time=now)
        weight_high = decay.calculate_weight(memory_high, current_time=now)
        
        # 高访问次数应该有更高的权重
        assert weight_high > weight_low
    
    def test_calculate_weight_with_initial_weight(self):
        """测试初始权重对计算的影响"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory_high_init = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=2.0,  # 高初始权重
            access_count=0,
            created_at=one_day_ago
        )
        
        memory_low_init = MemoryItem(
            memory_id="mem-002",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5,  # 低初始权重
            access_count=0,
            created_at=one_day_ago
        )
        
        weight_high = decay.calculate_weight(memory_high_init, current_time=now)
        weight_low = decay.calculate_weight(memory_low_init, current_time=now)
        
        # 初始权重高的应该有更高的计算权重
        assert weight_high > weight_low


class TestBatchDecay:
    """批量衰减测试"""
    
    def test_apply_decay_empty_list(self):
        """测试空列表的批量衰减"""
        decay = MemoryDecay()
        
        updates = decay.apply_decay([])
        
        assert updates == {}
    
    def test_apply_decay_single_memory(self):
        """测试单个记忆的批量衰减"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        updates = decay.apply_decay([memory], current_time=now)
        
        assert "mem-001" in updates
        assert updates["mem-001"] < 1.0
        # 内存对象也应该被更新
        assert memory.weight == updates["mem-001"]
    
    def test_apply_decay_multiple_memories(self):
        """测试多个记忆的批量衰减"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        
        memories = []
        for i in range(5):
            days_ago = now - timedelta(days=i * 2)
            memories.append(MemoryItem(
                memory_id=f"mem-{i:03d}",
                content=f"test {i}",
                layer=MemoryLayer.L2_SEMANTIC,
                weight=1.0,
                access_count=0,
                created_at=days_ago
            ))
        
        updates = decay.apply_decay(memories, current_time=now)
        
        assert len(updates) == 5
        # 较旧的记忆应该有更低的权重
        assert updates["mem-004"] < updates["mem-000"]


class TestArchiveDecision:
    """归档决策测试"""
    
    def test_archive_low_weight_empty_list(self):
        """测试空列表的归档判断"""
        decay = MemoryDecay()
        
        to_archive = decay.archive_low_weight([])
        
        assert to_archive == []
    
    def test_archive_low_weight_none_below_threshold(self):
        """测试没有低权重记忆的情况"""
        decay = MemoryDecay(archive_threshold=0.05)
        
        memories = [
            MemoryItem(memory_id="mem-001", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.5),
            MemoryItem(memory_id="mem-002", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.8),
            MemoryItem(memory_id="mem-003", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.3),
        ]
        
        to_archive = decay.archive_low_weight(memories)
        
        assert to_archive == []
    
    def test_archive_low_weight_some_below_threshold(self):
        """测试部分记忆低于阈值的情况"""
        decay = MemoryDecay(archive_threshold=0.2)
        
        memories = [
            MemoryItem(memory_id="mem-001", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.5),
            MemoryItem(memory_id="mem-002", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.1),  # 低于阈值
            MemoryItem(memory_id="mem-003", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.15),  # 低于阈值
            MemoryItem(memory_id="mem-004", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.8),
        ]
        
        to_archive = decay.archive_low_weight(memories)
        
        assert len(to_archive) == 2
        assert "mem-002" in to_archive
        assert "mem-003" in to_archive
    
    def test_archive_low_weight_custom_threshold(self):
        """测试自定义阈值的归档判断"""
        decay = MemoryDecay(archive_threshold=0.1)
        
        memories = [
            MemoryItem(memory_id="mem-001", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.15),
            MemoryItem(memory_id="mem-002", content="test", layer=MemoryLayer.L2_SEMANTIC, weight=0.05),
        ]
        
        # 使用默认阈值
        to_archive_default = decay.archive_low_weight(memories)
        assert "mem-002" in to_archive_default
        assert "mem-001" not in to_archive_default
        
        # 使用自定义阈值
        to_archive_custom = decay.archive_low_weight(memories, threshold=0.2)
        assert "mem-002" in to_archive_custom
        assert "mem-001" in to_archive_custom
    
    def test_should_archive_true(self):
        """测试应该归档的情况"""
        decay = MemoryDecay(archive_threshold=0.1)
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.05  # 低于阈值
        )
        
        assert decay.should_archive(memory) is True
    
    def test_should_archive_false(self):
        """测试不应该归档的情况"""
        decay = MemoryDecay(archive_threshold=0.1)
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5  # 高于阈值
        )
        
        assert decay.should_archive(memory) is False


class TestReinforce:
    """记忆强化测试"""
    
    def test_reinforce_basic(self):
        """测试基本强化"""
        decay = MemoryDecay()
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5,
            access_count=0
        )
        
        new_weight = decay.reinforce(memory)
        
        assert new_weight == 0.75  # 0.5 * 1.5
        assert memory.weight == 0.75
        assert memory.access_count == 1
    
    def test_reinforce_custom_factor(self):
        """测试自定义强化因子"""
        decay = MemoryDecay()
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5,
            access_count=0
        )
        
        new_weight = decay.reinforce(memory, boost_factor=2.0)
        
        assert new_weight == 1.0  # 0.5 * 2.0
        assert memory.weight == 1.0
    
    def test_reinforce_max_weight_limit(self):
        """测试强化的最大权重限制"""
        decay = MemoryDecay()
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.5,
            access_count=0
        )
        
        new_weight = decay.reinforce(memory, boost_factor=2.0)
        
        # 应该被限制在 2.0
        assert new_weight == 2.0
        assert memory.weight == 2.0
    
    def test_reinforce_updates_access_count(self):
        """测试强化更新访问次数"""
        decay = MemoryDecay()
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5,
            access_count=5
        )
        
        decay.reinforce(memory)
        
        assert memory.access_count == 6
    
    def test_reinforce_updates_last_accessed(self):
        """测试强化更新最后访问时间"""
        decay = MemoryDecay()
        old_time = datetime.now() - timedelta(hours=1)
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.5,
            access_count=0,
            last_accessed=old_time
        )
        
        decay.reinforce(memory)
        
        assert memory.last_accessed > old_time


class TestDecayRate:
    """衰减率测试"""
    
    def test_high_decay_rate(self):
        """测试高衰减率"""
        decay = MemoryDecay(decay_rate=0.5)  # 高衰减率
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 高衰减率应该导致更快的权重下降
        assert weight < 0.7
    
    def test_low_decay_rate(self):
        """测试低衰减率"""
        decay = MemoryDecay(decay_rate=0.01)  # 低衰减率
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 低衰减率应该导致更慢的权重下降
        assert weight > 0.95
    
    def test_zero_decay_rate(self):
        """测试零衰减率"""
        decay = MemoryDecay(decay_rate=0.0)
        now = datetime.now()
        one_day_ago = now - timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=one_day_ago
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 零衰减率不应导致衰减
        # weight = 1.0 * e^0 * (1 + log10(1)) = 1.0
        assert weight == 1.0


class TestEdgeCases:
    """边界情况测试"""
    
    def test_very_old_memory(self):
        """测试非常旧的记忆"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        very_old = now - timedelta(days=365)  # 一年前
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=very_old
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 应该接近零但不为零
        assert weight > 0
        assert weight < 0.01
    
    def test_future_created_at(self):
        """测试未来创建时间（异常情况）"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        future = now + timedelta(days=1)
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=0,
            created_at=future
        )
        
        # 不应抛出异常
        weight = decay.calculate_weight(memory, current_time=now)
        # 负时间间隔会导致权重增加
        assert weight >= 1.0
    
    def test_zero_initial_weight(self):
        """测试零初始权重"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=0.0,  # 零初始权重
            access_count=5,
            created_at=now
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 零乘以任何数都是零
        assert weight == 0.0
    
    def test_very_high_access_count(self):
        """测试非常高的访问次数"""
        decay = MemoryDecay(decay_rate=0.1)
        now = datetime.now()
        
        memory = MemoryItem(
            memory_id="mem-001",
            content="test",
            layer=MemoryLayer.L2_SEMANTIC,
            weight=1.0,
            access_count=10000,  # 非常高的访问次数
            created_at=now
        )
        
        weight = decay.calculate_weight(memory, current_time=now)
        
        # 高访问次数应该显著提高权重
        # frequency_factor = 1 + log10(10001) ≈ 1 + 4 = 5
        assert weight > 4
