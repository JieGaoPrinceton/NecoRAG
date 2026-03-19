"""
用户画像适配器 (User Profile Adapter)

基于用户个人工作空间数据，进行个性化定制
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio


class DetailLevel(Enum):
    """详细度级别"""
    CONCISE = "concise"  # 简洁
    BALANCED = "balanced"  # 平衡
    COMPREHENSIVE = "comprehensive"  # 详细


class Tone(Enum):
    """语调风格"""
    FORMAL = "formal"  # 正式
    CASUAL = "casual"  # 随意
    HUMOROUS = "humorous"  # 幽默


class FormatPreference(Enum):
    """格式偏好"""
    TEXT = "text"
    BULLET_POINTS = "bullet_points"
    TABLE = "table"
    DIAGRAM = "diagram"


class CitationStyle(Enum):
    """引用风格"""
    INLINE = "inline"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    NONE = "none"


@dataclass
class UserStylePreference:
    """用户风格偏好"""
    detail_level: DetailLevel = DetailLevel.BALANCED
    tone: Tone = Tone.FORMAL
    format_preference: FormatPreference = FormatPreference.TEXT
    citation_style: CitationStyle = CitationStyle.INLINE
    example_preference: str = "moderate"  # many, moderate, few, none
    cot_detail: str = "standard"  # minimal, standard, maximal


@dataclass
class UserProfile:
    """用户画像"""
    user_id: str
    username: Optional[str] = None
    expertise_domains: Dict[str, float] = field(default_factory=dict)  # 领域->专业度 (0-1)
    preference: UserStylePreference = field(default_factory=UserStylePreference)
    query_patterns: Dict[str, Any] = field(default_factory=dict)
    satisfaction_history: List[float] = field(default_factory=list)
    language_preference: str = "zh"  # zh, en
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_expertise_level(self, domain: Optional[str] = None) -> float:
        """获取用户在指定领域的专业度"""
        if not domain or domain not in self.expertise_domains:
            # 无特定领域时，返回平均专业度
            if self.expertise_domains:
                return sum(self.expertise_domains.values()) / len(self.expertise_domains)
            return 0.5  # 默认中等
        return self.expertise_domains[domain]
    
    def update_expertise(self, domain: str, delta: float):
        """更新领域专业度"""
        current = self.expertise_domains.get(domain, 0.5)
        self.expertise_domains[domain] = max(0.0, min(1.0, current + delta))
        self.updated_at = datetime.now()
    
    def add_satisfaction_score(self, score: float):
        """添加满意度评分"""
        self.satisfaction_history.append(score)
        # 保留最近 100 次评分
        if len(self.satisfaction_history) > 100:
            self.satisfaction_history = self.satisfaction_history[-100:]
        self.updated_at = datetime.now()
    
    def get_avg_satisfaction(self) -> float:
        """获取平均满意度"""
        if not self.satisfaction_history:
            return 0.0
        return sum(self.satisfaction_history) / len(self.satisfaction_history)


class UserProfileAdapter:
    """
    用户画像适配器
    
    功能:
    1. 获取和管理用户画像
    2. 专业度评估与调节
    3. 风格偏好适配
    4. 实时更新用户画像
    """
    
    def __init__(
        self,
        memory_manager=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            memory_manager: 记忆管理器 (用于访问 L1 工作记忆中的用户数据)
            config: 配置参数
        """
        self.memory_manager = memory_manager
        self.config = config or {}
        
        # 本地缓存 (LRU 缓存)
        self._cache = {}
        self._cache_max_size = self.config.get('cache_max_size', 100)
        
        # 专业度阈值配置
        self.expertise_thresholds = {
            'expert': 0.8,
            'intermediate': 0.5,
            'novice': 0.3,
        }
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        # 检查缓存
        if user_id in self._cache:
            return self._cache[user_id]
        
        # 从记忆管理器加载
        if self.memory_manager:
            profile_data = await self.memory_manager.get_user_profile(user_id)
            if profile_data:
                profile = self._deserialize_profile(profile_data)
                self._cache[user_id] = profile
                return profile
        
        # 创建默认画像
        default_profile = UserProfile(user_id=user_id)
        self._cache[user_id] = default_profile
        return default_profile
    
    def _deserialize_profile(self, data: Dict[str, Any]) -> UserProfile:
        """反序列化用户画像"""
        preference_data = data.get('preference', {})
        preference = UserStylePreference(
            detail_level=DetailLevel(preference_data.get('detail_level', 'balanced')),
            tone=Tone(preference_data.get('tone', 'formal')),
            format_preference=FormatPreference(preference_data.get('format_preference', 'text')),
            citation_style=CitationStyle(preference_data.get('citation_style', 'inline')),
            example_preference=preference_data.get('example_preference', 'moderate'),
            cot_detail=preference_data.get('cot_detail', 'standard'),
        )
        
        return UserProfile(
            user_id=data['user_id'],
            username=data.get('username'),
            expertise_domains=data.get('expertise_domains', {}),
            preference=preference,
            query_patterns=data.get('query_patterns', {}),
            satisfaction_history=data.get('satisfaction_history', []),
            language_preference=data.get('language_preference', 'zh'),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now()),
        )
    
    async def update_profile(
        self,
        user_id: str,
        updates: Dict[str, Any],
        save_to_storage: bool = True
    ):
        """更新用户画像"""
        profile = await self.get_profile(user_id)
        
        # 应用更新
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        
        # 更新缓存
        self._cache[user_id] = profile
        
        # 持久化
        if save_to_storage and self.memory_manager:
            await self.memory_manager.save_user_profile(profile)
    
    async def update_expertise(
        self,
        user_id: str,
        domain: str,
        delta: float,
        is_positive: bool = True
    ):
        """
        更新用户领域专业度
        
        Args:
            user_id: 用户 ID
            domain: 领域名称
            delta: 变化量
            is_positive: 是否为正面反馈
        """
        profile = await self.get_profile(user_id)
        
        # 正面反馈增加专业度，负面反馈减少
        actual_delta = delta if is_positive else -delta * 0.5
        profile.update_expertise(domain, actual_delta)
        
        # 保存
        await self.update_profile(user_id, {'expertise_domains': profile.expertise_domains})
    
    async def update_preference(
        self,
        user_id: str,
        preference_key: str,
        value: Any
    ):
        """更新用户偏好"""
        profile = await self.get_profile(user_id)
        
        if hasattr(profile.preference, preference_key):
            setattr(profile.preference, preference_key, value)
            await self.update_profile(user_id, {'preference': profile.preference})
    
    def get_expertise_category(self, expertise_level: float) -> str:
        """根据专业度数值分类"""
        if expertise_level >= self.expertise_thresholds['expert']:
            return "expert"
        elif expertise_level >= self.expertise_thresholds['intermediate']:
            return "intermediate"
        elif expertise_level >= self.expertise_thresholds['novice']:
            return "novice"
        else:
            return "beginner"
    
    def adapt_response_style(
        self,
        content: str,
        user_profile: UserProfile,
        domain: Optional[str] = None
    ) -> str:
        """
        根据用户画像调整响应风格
        
        Args:
            content: 原始内容
            user_profile: 用户画像
            domain: 领域
            
        Returns:
            调整后的内容
        """
        expertise = user_profile.get_expertise_level(domain)
        category = self.get_expertise_category(expertise)
        preference = user_profile.preference
        
        # 根据专业度调整详细度
        if category == "expert":
            # 专家：简洁、专业术语
            content = self._make_concise(content)
            content = self._use_technical_language(content)
        elif category == "intermediate":
            # 中级：平衡解释
            content = self._add_moderate_explanations(content)
        else:
            # 新手：通俗易懂、类比
            content = self._add_analogies(content)
            content = self._add_detailed_explanations(content)
        
        # 根据格式偏好调整
        if preference.format_preference == FormatPreference.BULLET_POINTS:
            content = self._convert_to_bullet_points(content)
        elif preference.format_preference == FormatPreference.TABLE:
            content = self._convert_to_table(content)
        
        return content
    
    def _make_concise(self, content: str) -> str:
        """简化内容 (去除冗余解释)"""
        # 这里可以实现简化逻辑
        # 例如移除过多的示例、简化句子结构等
        return content  # TODO: 实现简化逻辑
    
    def _use_technical_language(self, content: str) -> str:
        """使用专业术语"""
        # 可以替换通俗表达为专业术语
        return content  # TODO: 实现术语替换
    
    def _add_moderate_explanations(self, content: str) -> str:
        """添加适度解释"""
        return content  # TODO: 实现解释添加
    
    def _add_analogies(self, content: str) -> str:
        """添加类比说明"""
        return content  # TODO: 实现类比生成
    
    def _add_detailed_explanations(self, content: str) -> str:
        """添加详细解释"""
        return content  # TODO: 实现详细解释
    
    def _convert_to_bullet_points(self, content: str) -> str:
        """转换为列表格式"""
        # 简单实现：按句号分割
        sentences = content.split('。')
        bullet_points = [f"- {s.strip()}" for s in sentences if s.strip()]
        return '\n'.join(bullet_points)
    
    def _convert_to_table(self, content: str) -> str:
        """转换为表格格式"""
        # TODO: 实现智能表格转换
        return content
    
    def clear_cache(self, user_id: Optional[str] = None):
        """清除缓存"""
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()
