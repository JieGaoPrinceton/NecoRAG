"""
User Profile Manager - 用户画像管理器
"""

from typing import Dict, Optional, List
from datetime import datetime
from src.response.models import UserProfile, Interaction


class UserProfileManager:
    """
    用户画像管理器
    
    功能：
    - 管理用户画像
    - 分析用户偏好
    - 跟踪交互历史
    """
    
    def __init__(
        self,
        working_memory,
        profile_ttl: int = 86400,
        max_history: int = 100
    ):
        """
        初始化用户画像管理器
        
        Args:
            working_memory: 工作记忆
            profile_ttl: 画像 TTL（秒）
            max_history: 最大历史记录数
        """
        self.working_memory = working_memory
        self.profile_ttl = profile_ttl
        self.max_history = max_history
        
        # 画像缓存
        self._profiles: Dict[str, UserProfile] = {}
    
    def get_profile(self, user_id: str) -> UserProfile:
        """
        获取用户画像
        
        Args:
            user_id: 用户 ID
            
        Returns:
            UserProfile: 用户画像
        """
        # 从缓存获取
        if user_id in self._profiles:
            return self._profiles[user_id]
        
        # 从工作记忆获取
        context = self.working_memory.get_context(user_id)
        
        if "profile" in context:
            profile = context["profile"]
        else:
            # 创建新画像
            profile = UserProfile(user_id=user_id)
        
        # 缓存
        self._profiles[user_id] = profile
        
        return profile
    
    def update_profile(
        self,
        user_id: str,
        interaction: Interaction
    ) -> None:
        """
        更新用户画像
        
        Args:
            user_id: 用户 ID
            interaction: 交互记录
        """
        profile = self.get_profile(user_id)
        
        # 更新查询历史
        profile.query_history.append(interaction.query)
        
        # 限制历史长度
        if len(profile.query_history) > self.max_history:
            profile.query_history = profile.query_history[-self.max_history:]
        
        # 更新时间
        profile.updated_at = datetime.now()
        
        # 更新满意度（如果有）
        if interaction.satisfaction is not None:
            # TODO: 基于满意度调整画像
            pass
        
        # 保存到工作记忆
        self.working_memory.add_context(user_id, {"profile": profile})
    
    def analyze_preference(self, user_id: str) -> Dict:
        """
        分析用户偏好
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Dict: 偏好分析结果
        """
        profile = self.get_profile(user_id)
        
        # 分析查询历史
        query_keywords = {}
        for query in profile.query_history:
            # 提取关键词
            words = query.lower().split()
            for word in words:
                if len(word) > 2:
                    query_keywords[word] = query_keywords.get(word, 0) + 1
        
        # 排序
        top_keywords = sorted(
            query_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "top_keywords": top_keywords,
            "total_queries": len(profile.query_history),
            "interaction_style": profile.interaction_style,
            "professional_level": profile.professional_level
        }
    
    def detect_style(self, user_id: str) -> str:
        """
        检测用户交互风格
        
        Args:
            user_id: 用户 ID
            
        Returns:
            str: 检测到的风格
            
        TODO: 实现基于历史的风格检测
        """
        profile = self.get_profile(user_id)
        return profile.interaction_style
    
    def detect_professional_level(self, user_id: str) -> str:
        """
        检测用户专业水平
        
        Args:
            user_id: 用户 ID
            
        Returns:
            str: 检测到的专业水平
            
        TODO: 实现基于查询的专业水平检测
        """
        profile = self.get_profile(user_id)
        return profile.professional_level
