"""
Memory Pruner - 记忆修剪器
模拟猫"舔毛梳理"行为
"""

from typing import List
from datetime import datetime, timedelta


class MemoryPruner:
    """
    记忆修剪器
    
    模拟猫的梳理行为：
    - 清理"脏毛"（噪声数据）
    - 强化"干净毛发"（重要连接）
    - 保持"毛发光泽"（知识时效性）
    """
    
    def __init__(
        self,
        memory_manager,
        noise_threshold: float = 0.1,
        quality_threshold: float = 0.3,
        outdated_days: int = 90
    ):
        """
        初始化记忆修剪器
        
        Args:
            memory_manager: 记忆管理器
            noise_threshold: 噪声判定阈值
            quality_threshold: 质量判定阈值
            outdated_days: 过时天数判定
        """
        self.memory = memory_manager
        self.noise_threshold = noise_threshold
        self.quality_threshold = quality_threshold
        self.outdated_days = outdated_days
    
    def prune(self) -> dict:
        """
        执行记忆修剪
        
        Returns:
            dict: 修剪报告
        """
        # 1. 识别噪声数据
        noise_data = self.identify_noise()
        
        # 2. 识别低质量知识
        low_quality = self.identify_low_quality()
        
        # 3. 识别过时信息
        outdated = self.identify_outdated()
        
        # 4. 执行修剪
        removed = self.remove_items(noise_data + low_quality + outdated)
        
        # 5. 强化重要连接
        reinforced = self.reinforce_connections()
        
        return {
            "removed_count": len(removed),
            "reinforced_count": len(reinforced),
            "noise_count": len(noise_data),
            "low_quality_count": len(low_quality),
            "outdated_count": len(outdated)
        }
    
    def identify_noise(self) -> List[str]:
        """
        识别噪声数据
        
        Returns:
            List[str]: 噪声记忆 ID 列表
        """
        noise_ids = []
        
        for memory_id, memory in self.memory._memory_store.items():
            # 基于权重和访问次数判断噪声
            if memory.weight < self.noise_threshold and memory.access_count < 2:
                noise_ids.append(memory_id)
        
        return noise_ids
    
    def identify_low_quality(self) -> List[str]:
        """
        识别低质量知识
        
        Returns:
            List[str]: 低质量记忆 ID 列表
        """
        low_quality_ids = []
        
        for memory_id, memory in self.memory._memory_store.items():
            # 基于内容长度和权重判断质量
            if len(memory.content) < 20 and memory.weight < self.quality_threshold:
                low_quality_ids.append(memory_id)
        
        return low_quality_ids
    
    def identify_outdated(self) -> List[str]:
        """
        识别过时信息
        
        Returns:
            List[str]: 过时记忆 ID 列表
        """
        outdated_ids = []
        threshold_date = datetime.now() - timedelta(days=self.outdated_days)
        
        for memory_id, memory in self.memory._memory_store.items():
            # 基于最后访问时间判断过时
            if memory.last_accessed < threshold_date:
                outdated_ids.append(memory_id)
        
        return outdated_ids
    
    def remove_items(self, memory_ids: List[str]) -> List[str]:
        """
        移除记忆项
        
        Args:
            memory_ids: 记忆 ID 列表
            
        Returns:
            List[str]: 成功移除的 ID 列表
        """
        removed = []
        
        for memory_id in set(memory_ids):  # 去重
            if self.memory.semantic_memory.delete(memory_id):
                self.memory._memory_store.pop(memory_id, None)
                removed.append(memory_id)
        
        return removed
    
    def reinforce_connections(self) -> List[str]:
        """
        强化重要连接
        
        Returns:
            List[str]: 强化的记忆 ID 列表
            
        TODO: 实现连接强化逻辑
        """
        # 最小实现：返回高频访问的记忆
        reinforced = []
        
        for memory_id, memory in self.memory._memory_store.items():
            if memory.access_count > 5:
                memory.weight *= 1.1  # 强化权重
                reinforced.append(memory_id)
        
        return reinforced
