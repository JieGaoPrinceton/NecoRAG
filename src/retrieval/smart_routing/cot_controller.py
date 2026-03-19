"""
CoT思维链控制器 (CoT Controller)

智能触发与深度调节
"""

from typing import Dict, Any, Optional
from enum import Enum
import asyncio
import random


class CoTDepth(Enum):
    """CoT 深度等级"""
    L1_MINIMAL = 1  # 精简版 (1-2 步)
    L2_STANDARD = 2  # 标准版 (3-4 步)
    L3_DETAILED = 3  # 详细版 (5-7 步)
    L4_EXPLORATORY = 4  # 探索版 (7+ 步)


class CoTController:
    """
    CoT思维链控制器
    
    功能:
    1. 智能触发判断
    2. 动态深度调节
    3. 性能监控
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 配置参数
        self.min_complexity = self.config.get('min_complexity', 0.7)
        self.max_steps = self.config.get('max_steps', 7)
        self.graph_max_hops = self.config.get('graph_max_hops', 3)
        self.evidence_min_count = self.config.get('evidence_min_count', 3)
        
        # 触发概率基数
        self.base_trigger_probabilities = {
            'reasoning_inference': 0.9,
            'exploratory': 0.7,
            'concept_explanation': 0.5,
            'comparative_analysis': 0.4,
            'summarization': 0.3,
            'procedural': 0.2,
            'factual_query': 0.1,
        }
        
        # 统计信息
        self._trigger_count = 0
        self._total_queries = 0
    
    def should_trigger_cot(
        self,
        query: str,
        intent_type: str,
        complexity: float,
        confidence: float
    ) -> bool:
        """
        判断是否应该触发 CoT
        
        Args:
            query: 查询文本
            intent_type: 意图类型
            complexity: 复杂度 (0-1)
            confidence: 置信度 (0-1)
            
        Returns:
            bool: 是否触发
        """
        self._total_queries += 1
        
        # 基础概率
        base_prob = self.base_trigger_probabilities.get(intent_type, 0.3)
        
        # 复杂度调节
        if complexity >= 0.8:
            base_prob += 0.2
        elif complexity <= 0.3:
            base_prob -= 0.2
        
        # 低置信度调节
        if confidence < 0.6:
            base_prob += 0.15
        
        # 查询长度调节 (长查询更可能需要推理)
        if len(query) > 100:
            base_prob += 0.1
        
        # 包含推理关键词
        reasoning_keywords = [
            '为什么', '如何证明', '原因', '逻辑', '推理',
            'why', 'how to prove', 'reason', 'logic'
        ]
        if any(kw in query.lower() for kw in reasoning_keywords):
            base_prob += 0.15
        
        # 随机触发
        should_trigger = random.random() < base_prob
        
        if should_trigger:
            self._trigger_count += 1
        
        return should_trigger
    
    async def determine_depth(
        self,
        query: str,
        user_profile: Optional[Dict[str, Any]],
        intent_result: Any
    ) -> CoTDepth:
        """
        动态确定 CoT 推理深度
        
        Args:
            query: 查询
            user_profile: 用户画像
            intent_result: 意图识别结果
            
        Returns:
            CoTDepth: 深度等级
        """
        base_depth = 2  # 默认标准版
        
        # 意图复杂度调节
        if hasattr(intent_result, 'complexity'):
            if intent_result.complexity >= 0.8:
                base_depth += 2
            elif intent_result.complexity <= 0.4:
                base_depth -= 1
        
        # 用户专业度调节
        if user_profile:
            expertise_domains = user_profile.get('expertise_domains', {})
            domain = getattr(intent_result, 'domain', None)
            
            if domain and domain in expertise_domains:
                expertise = expertise_domains[domain]
                if expertise >= 0.8:
                    base_depth -= 1  # 专家减少步骤
                elif expertise <= 0.3:
                    base_depth += 2  # 新手增加步骤
        
        # 用户显式偏好
        if user_profile:
            preference = user_profile.get('preference', {})
            cot_detail = preference.get('cot_detail', 'standard')
            
            if cot_detail == 'minimal':
                base_depth -= 1
            elif cot_detail == 'maximal':
                base_depth += 2
        
        # 上下文调节 (追问场景简化)
        if self._is_followup_query(query):
            base_depth -= 1
        
        # 限制在合理范围内
        final_depth_value = max(1, min(base_depth, 4))
        
        # 映射到枚举
        depth_map = {
            1: CoTDepth.L1_MINIMAL,
            2: CoTDepth.L2_STANDARD,
            3: CoTDepth.L3_DETAILED,
            4: CoTDepth.L4_EXPLORATORY,
        }
        
        return depth_map[final_depth_value]
    
    def _is_followup_query(self, query: str) -> bool:
        """判断是否为追问"""
        followup_indicators = [
            '那', '那么', '接着', '然后', '继续',
            '还有', '另外', '再问', 'follow-up', 'then'
        ]
        return any(indicator in query.lower() for indicator in followup_indicators)
    
    def get_max_steps_for_depth(self, depth: CoTDepth) -> int:
        """获取指定深度的最大步骤数"""
        max_steps_map = {
            CoTDepth.L1_MINIMAL: 2,
            CoTDepth.L2_STANDARD: 4,
            CoTDepth.L3_DETAILED: 7,
            CoTDepth.L4_EXPLORATORY: 10,
        }
        return min(max_steps_map[depth], self.max_steps)
    
    def get_trigger_rate(self) -> float:
        """获取 CoT 触发率"""
        if self._total_queries == 0:
            return 0.0
        return self._trigger_count / self._total_queries
    
    def reset_stats(self):
        """重置统计信息"""
        self._trigger_count = 0
        self._total_queries = 0
