"""User Profile Manager - 用户画像管理器

管理用户画像，分析用户偏好，包括：
- 专业水平检测（beginner/intermediate/expert）
- 风格偏好检测（简洁/详细/技术性/通俗化）
- 查询历史跟踪

支持 LLM 增强模式和简单规则退化模式。
"""

import re
from typing import Dict, Optional, List, TYPE_CHECKING
from datetime import datetime
from .models import UserProfile, Interaction

if TYPE_CHECKING:
    from src.core.base import BaseLLMClient


class UserProfileManager:
    """
    用户画像管理器
    
    功能：
    - 管理用户画像
    - 分析用户偏好
    - 跟踪交互历史
    - 检测专业水平和风格偏好
    
    支持 LLM 增强模式，也可退化为基于规则的检测。
    """
    
    # 专业水平检测关键词
    EXPERT_KEYWORDS = {
        'architecture', 'microservices', 'distributed', 'scalability',
        'optimization', 'algorithm', 'complexity', 'concurrency',
        'asynchronous', 'protocol', 'latency', 'throughput',
        '架构', '分布式', '微服务', '可扩展性', '复杂度',
        '并发', '异步', '协议', '性能优化', '算法'
    }
    
    INTERMEDIATE_KEYWORDS = {
        'api', 'database', 'framework', 'library', 'function',
        'class', 'method', 'variable', 'debug', 'error',
        '接口', '数据库', '框架', '函数', '类',
        '方法', '变量', '调试', '错误', '配置'
    }
    
    BEGINNER_KEYWORDS = {
        'what is', 'how to', 'basic', 'simple', 'tutorial',
        'example', 'beginner', 'learn', 'start',
        '什么是', '怎么', '如何', '基础', '简单',
        '入门', '学习', '教程', '示例'
    }
    
    # 风格检测模式
    CONCISE_PATTERNS = [
        r'^[\u4e00-\u9fa5\w\s]{1,20}[?？]?$',  # 短查询
        r'简要|简单|直接|快速',
    ]
    
    DETAILED_PATTERNS = [
        r'详细|全面|完整|深入|具体',
        r'explain in detail|comprehensive|thorough',
    ]
    
    TECHNICAL_PATTERNS = [
        r'技术|实现|代码|原理|底层',
        r'implementation|technical|code|underlying',
    ]
    
    POPULAR_PATTERNS = [
        r'通俗|易懂|简单说|举例',
        r'simple terms|easy|layman|example',
    ]
    
    def __init__(
        self,
        working_memory,
        profile_ttl: int = 86400,
        max_history: int = 100,
        llm_client: Optional["BaseLLMClient"] = None
    ):
        """
        初始化用户画像管理器
        
        Args:
            working_memory: 工作记忆
            profile_ttl: 画像 TTL（秒）
            max_history: 最大历史记录数
            llm_client: LLM 客户端（可选，用于高级检测）
        """
        self.working_memory = working_memory
        self.profile_ttl = profile_ttl
        self.max_history = max_history
        self._llm_client = llm_client
        
        # 画像缓存
        self._profiles: Dict[str, UserProfile] = {}
    
    @property
    def llm_enabled(self) -> bool:
        """检查 LLM 是否可用"""
        return self._llm_client is not None
    
    def set_llm_client(self, llm_client: Optional["BaseLLMClient"]) -> None:
        """
        设置 LLM 客户端
        
        Args:
            llm_client: LLM 客户端实例
        """
        self._llm_client = llm_client
    
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
            "interaction_style": profile.preferred_tone.value if hasattr(profile.preferred_tone, 'value') else str(profile.preferred_tone),
            "professional_level": profile.knowledge_level
        }
    
    def detect_style(self, user_id: str, use_llm: bool = False) -> str:
        """
        检测用户交互风格
        
        基于用户的查询历史分析偏好的回答风格。
        
        Args:
            user_id: 用户 ID
            use_llm: 是否使用 LLM 进行高级检测（默认 False）
            
        Returns:
            str: 检测到的风格（concise/detailed/technical/popular）
        """
        profile = self.get_profile(user_id)
        queries = profile.query_history
        
        if not queries:
            return self._get_default_style(profile)
        
        # 如果启用 LLM 且可用，使用 LLM 进行高级检测
        if use_llm and self._llm_client is not None:
            return self._llm_detect_style(queries)
        
        # 否则使用基于规则的检测
        return self._rule_based_style_detection(queries)
    
    def _rule_based_style_detection(self, queries: List[str]) -> str:
        """
        基于规则的风格检测
        
        Args:
            queries: 查询历史
            
        Returns:
            str: 检测到的风格
        """
        style_scores = {
            'concise': 0,
            'detailed': 0,
            'technical': 0,
            'popular': 0
        }
        
        for query in queries:
            query_lower = query.lower()
            
            # 检查各类模式
            for pattern in self.CONCISE_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    style_scores['concise'] += 1
            
            for pattern in self.DETAILED_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    style_scores['detailed'] += 1
            
            for pattern in self.TECHNICAL_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    style_scores['technical'] += 1
            
            for pattern in self.POPULAR_PATTERNS:
                if re.search(pattern, query, re.IGNORECASE):
                    style_scores['popular'] += 1
            
            # 短查询倾向于简洁风格
            if len(query) < 30:
                style_scores['concise'] += 0.5
            elif len(query) > 100:
                style_scores['detailed'] += 0.5
        
        # 找出得分最高的风格
        if max(style_scores.values()) == 0:
            return 'standard'  # 默认风格
        
        return max(style_scores, key=style_scores.get)
    
    def _llm_detect_style(self, queries: List[str]) -> str:
        """
        使用 LLM 检测用户风格偏好
        
        Args:
            queries: 查询历史
            
        Returns:
            str: 检测到的风格
        """
        # 取最近的查询进行分析
        recent_queries = queries[-10:] if len(queries) > 10 else queries
        queries_text = '\n'.join([f"- {q}" for q in recent_queries])
        
        prompt = f"""请分析以下用户查询，判断用户偏好的回答风格：

{queries_text}

可选风格：
- concise: 简洁明了，喜欢直接的答案
- detailed: 详细全面，喜欢完整的解释
- technical: 技术性强，喜欢深入的技术细节
- popular: 通俗易懂，喜欢用简单语言解释

请只输出一个风格名称（concise/detailed/technical/popular）："""
        
        try:
            result = self._llm_client.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            ).strip().lower()
            
            # 验证输出
            valid_styles = {'concise', 'detailed', 'technical', 'popular'}
            if result in valid_styles:
                return result
            
            # 尝试提取有效的风格名称
            for style in valid_styles:
                if style in result:
                    return style
            
            return 'standard'
        except Exception:
            # LLM 调用失败时退化
            return self._rule_based_style_detection(queries)
    
    def _get_default_style(self, profile: UserProfile) -> str:
        """获取默认风格"""
        # 尝试从 profile 元数据中获取
        if hasattr(profile, 'metadata') and 'interaction_style' in profile.metadata:
            return profile.metadata['interaction_style']
        return 'standard'
    
    def detect_professional_level(self, user_id: str, use_llm: bool = False) -> str:
        """
        检测用户专业水平
        
        基于用户的查询词汇和问题复杂度估计专业等级。
        
        Args:
            user_id: 用户 ID
            use_llm: 是否使用 LLM 进行高级检测（默认 False）
            
        Returns:
            str: 检测到的专业水平（beginner/intermediate/expert）
        """
        profile = self.get_profile(user_id)
        queries = profile.query_history
        
        if not queries:
            return self._get_default_level(profile)
        
        # 如果启用 LLM 且可用，使用 LLM 进行高级检测
        if use_llm and self._llm_client is not None:
            return self._llm_detect_level(queries)
        
        # 否则使用基于规则的检测
        return self._rule_based_level_detection(queries)
    
    def _rule_based_level_detection(self, queries: List[str]) -> str:
        """
        基于规则的专业水平检测
        
        Args:
            queries: 查询历史
            
        Returns:
            str: 检测到的专业水平
        """
        level_scores = {
            'expert': 0,
            'intermediate': 0,
            'beginner': 0
        }
        
        total_words = 0
        avg_query_length = 0
        
        for query in queries:
            query_lower = query.lower()
            words = set(re.findall(r'[\w\u4e00-\u9fa5]+', query_lower))
            total_words += len(words)
            avg_query_length += len(query)
            
            # 检查关键词匹配
            expert_matches = len(words & self.EXPERT_KEYWORDS)
            intermediate_matches = len(words & self.INTERMEDIATE_KEYWORDS)
            beginner_matches = len(words & self.BEGINNER_KEYWORDS)
            
            # 专家关键词权重更高
            level_scores['expert'] += expert_matches * 3
            level_scores['intermediate'] += intermediate_matches * 2
            level_scores['beginner'] += beginner_matches * 1.5
            
            # 检查问题复杂度（通过长度和结构）
            if len(query) > 150 and ('?' in query or '？' in query):
                level_scores['expert'] += 1
            elif len(query) < 30:
                level_scores['beginner'] += 0.5
        
        # 平均查询长度也是一个指标
        if queries:
            avg_query_length /= len(queries)
            if avg_query_length > 100:
                level_scores['expert'] += 1
            elif avg_query_length < 40:
                level_scores['beginner'] += 1
        
        # 找出得分最高的级别
        if max(level_scores.values()) == 0:
            return 'intermediate'  # 默认级别
        
        return max(level_scores, key=level_scores.get)
    
    def _llm_detect_level(self, queries: List[str]) -> str:
        """
        使用 LLM 检测用户专业水平
        
        Args:
            queries: 查询历史
            
        Returns:
            str: 检测到的专业水平
        """
        # 取最近的查询进行分析
        recent_queries = queries[-10:] if len(queries) > 10 else queries
        queries_text = '\n'.join([f"- {q}" for q in recent_queries])
        
        prompt = f"""请分析以下用户查询，判断用户的专业水平：

{queries_text}

可选级别：
- beginner: 初学者，提问简单基础问题
- intermediate: 中级用户，有一定基础，问题涉及实践应用
- expert: 专家级别，问题深入复杂，涉及高级概念

请只输出一个级别名称（beginner/intermediate/expert）："""
        
        try:
            result = self._llm_client.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            ).strip().lower()
            
            # 验证输出
            valid_levels = {'beginner', 'intermediate', 'expert'}
            if result in valid_levels:
                return result
            
            # 尝试提取有效的级别名称
            for level in valid_levels:
                if level in result:
                    return level
            
            return 'intermediate'
        except Exception:
            # LLM 调用失败时退化
            return self._rule_based_level_detection(queries)
    
    def _get_default_level(self, profile: UserProfile) -> str:
        """获取默认专业水平"""
        # 优先使用 knowledge_level（protocols.py 中的字段）
        if hasattr(profile, 'knowledge_level') and profile.knowledge_level:
            return profile.knowledge_level
        return 'intermediate'
    
    def analyze_user_comprehensive(
        self,
        user_id: str,
        use_llm: bool = False
    ) -> Dict:
        """
        综合分析用户画像
        
        返回完整的用户分析结果，包括专业水平、风格偏好、关键词等。
        
        Args:
            user_id: 用户 ID
            use_llm: 是否使用 LLM 增强
            
        Returns:
            Dict: 综合分析结果
        """
        profile = self.get_profile(user_id)
        preference = self.analyze_preference(user_id)
        
        return {
            'user_id': user_id,
            'professional_level': self.detect_professional_level(user_id, use_llm),
            'interaction_style': self.detect_style(user_id, use_llm),
            'top_keywords': preference.get('top_keywords', []),
            'total_queries': preference.get('total_queries', 0),
            'llm_enhanced': use_llm and self._llm_client is not None,
            'created_at': profile.created_at.isoformat() if hasattr(profile, 'created_at') else None,
            'updated_at': profile.updated_at.isoformat() if hasattr(profile, 'updated_at') else None
        }
