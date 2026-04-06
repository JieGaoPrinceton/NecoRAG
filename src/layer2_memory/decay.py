"""
记忆衰减机制
模拟生物记忆的巩固与遗忘
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .models import MemoryItem


class MemoryDecay:
    """
    记忆衰减机制
    
    公式：weight(t) = initial_weight × e^(-λt) × access_frequency
    
    功能：
    - 动态权重衰减
    - 低频访问知识降权
    - 重要知识强化
    - 自动归档
    """
    
    def __init__(
        self,
        decay_rate: float = 0.1,
        archive_threshold: float = 0.05
    ):
        """
        初始化衰减机制
        
        Args:
            decay_rate: 衰减速率 λ
            archive_threshold: 归档阈值
        """
        self.decay_rate = decay_rate
        self.archive_threshold = archive_threshold
    
    def calculate_weight(
        self,
        memory: MemoryItem,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        计算当前权重
        
        Args:
            memory: 记忆项
            current_time: 当前时间（None 则使用当前时间）
            
        Returns:
            float: 当前权重
        """
        if current_time is None:
            current_time = datetime.now()
        
        # 计算时间间隔（秒）
        time_elapsed = (current_time - memory.created_at).total_seconds()
        
        # 转换为天
        days_elapsed = time_elapsed / (24 * 3600)
        
        # 应用衰减公式
        import math
        decayed_weight = memory.weight * math.exp(-self.decay_rate * days_elapsed)
        
        # 加入访问频率因子
        frequency_factor = 1 + math.log10(memory.access_count + 1)
        
        return decayed_weight * frequency_factor
    
    def apply_decay(
        self,
        memories: List[MemoryItem],
        current_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        批量应用衰减
        
        Args:
            memories: 记忆项列表
            current_time: 当前时间
            
        Returns:
            Dict[str, float]: 记忆 ID -> 新权重
        """
        updates = {}
        
        for memory in memories:
            new_weight = self.calculate_weight(memory, current_time)
            memory.weight = new_weight
            updates[memory.memory_id] = new_weight
        
        return updates
    
    def archive_low_weight(
        self,
        memories: List[MemoryItem],
        threshold: Optional[float] = None
    ) -> List[str]:
        """
        归档低权重记忆
        
        Args:
            memories: 记忆项列表
            threshold: 归档阈值（None 则使用默认值）
            
        Returns:
            List[str]: 应归档的记忆 ID 列表
        """
        threshold = threshold or self.archive_threshold
        to_archive = []
        
        for memory in memories:
            if memory.weight < threshold:
                to_archive.append(memory.memory_id)
        
        return to_archive
    
    def reinforce(
        self,
        memory: MemoryItem,
        boost_factor: float = 1.5
    ) -> float:
        """
        强化记忆权重
        
        Args:
            memory: 记忆项
            boost_factor: 强化因子
            
        Returns:
            float: 新权重
        """
        memory.weight *= boost_factor
        memory.access_count += 1
        memory.last_accessed = datetime.now()
        
        # 限制最大权重
        memory.weight = min(memory.weight, 2.0)
        
        return memory.weight
    
    def should_archive(self, memory: MemoryItem) -> bool:
        """
        判断是否应该归档
        
        Args:
            memory: 记忆项
            
        Returns:
            bool: 是否应归档
        """
        return memory.weight < self.archive_threshold
