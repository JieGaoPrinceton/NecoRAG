"""
Adaptive Learning 用户偏好预测器

基于用户交互历史，预测和更新用户的偏好模型，
实现个性化的回答风格和内容深度适配。
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from .config import AdaptiveLearningConfig
from .models import UserLearningProfile, UserFeedback, FeedbackType


logger = logging.getLogger(__name__)


class PreferencePredictor:
    """
    用户偏好预测器
    
    基于用户交互历史，预测和更新用户的偏好模型，
    实现个性化的回答风格和内容深度适配。
    """
    
    # 领域关键词映射
    DOMAIN_KEYWORDS = {
        "AI": ["人工智能", "机器学习", "深度学习", "神经网络", "模型", "训练", "ai", "ml", "nlp", "transformer"],
        "database": ["数据库", "sql", "nosql", "索引", "查询", "表", "mongo", "mysql", "redis", "postgresql"],
        "web": ["前端", "后端", "api", "http", "html", "css", "javascript", "react", "vue", "网页"],
        "programming": ["代码", "编程", "函数", "类", "变量", "算法", "python", "java", "c++", "程序"],
        "cloud": ["云", "容器", "docker", "kubernetes", "aws", "azure", "服务器", "部署", "微服务"],
        "security": ["安全", "加密", "认证", "授权", "漏洞", "攻击", "防护", "ssl", "密码"],
        "data": ["数据", "分析", "统计", "可视化", "报表", "etl", "数据仓库", "pandas", "spark"],
    }
    
    # 专业术语（用于估计专业度）
    PROFESSIONAL_TERMS = {
        "high": ["架构", "微服务", "分布式", "一致性", "事务", "幂等", "并发", "异步", "中间件", 
                 "索引优化", "查询计划", "缓存策略", "负载均衡", "容错", "降级"],
        "medium": ["接口", "协议", "配置", "部署", "测试", "调试", "日志", "监控", "性能"],
        "basic": ["怎么", "什么是", "如何", "为什么", "入门", "基础", "简单", "例子"],
    }
    
    def __init__(self, config: AdaptiveLearningConfig = None):
        """
        初始化偏好预测器
        
        Args:
            config: 自适应学习配置
        """
        self.config = config or AdaptiveLearningConfig.default()
        self._user_profiles: Dict[str, UserLearningProfile] = {}  # user_id -> profile
    
    def _get_or_create_profile(self, user_id: str) -> UserLearningProfile:
        """获取或创建用户画像"""
        if user_id not in self._user_profiles:
            self._user_profiles[user_id] = UserLearningProfile(user_id=user_id)
        return self._user_profiles[user_id]
    
    def on_interaction(
        self, 
        user_id: str, 
        query: str, 
        response_quality: float = 0.5,
        query_complexity: float = 0.5,
        topics: List[str] = None
    ) -> None:
        """
        记录一次交互，更新用户画像
        
        Args:
            user_id: 用户ID
            query: 查询内容
            response_quality: 响应质量 (0-1)
            query_complexity: 查询复杂度 (0-1)
            topics: 查询涉及的主题（可选）
        """
        if not self.config.enable_preference_learning:
            return
        
        profile = self._get_or_create_profile(user_id)
        
        # 1. 更新 expertise_scores（根据查询涉及的领域）
        detected_domains = self._detect_domains(query)
        if topics:
            detected_domains.extend(topics)
        
        for domain in detected_domains:
            current_score = profile.expertise_scores.get(domain, 0.5)
            # 查询越复杂，专业度估计越高
            adjustment = (query_complexity - 0.5) * self.config.expertise_learning_rate
            new_score = max(0.0, min(1.0, current_score + adjustment))
            profile.expertise_scores[domain] = new_score
        
        # 2. 更新 query_complexity_trend
        profile.query_complexity_trend.append(query_complexity)
        if len(profile.query_complexity_trend) > self.config.max_complexity_history:
            profile.query_complexity_trend = profile.query_complexity_trend[-self.config.max_complexity_history:]
        
        # 3. 更新 satisfaction_history
        profile.satisfaction_history.append(response_quality)
        if len(profile.satisfaction_history) > self.config.satisfaction_window:
            profile.satisfaction_history = profile.satisfaction_history[-self.config.satisfaction_window:]
        
        # 4. 更新 topic_frequency
        for domain in detected_domains:
            profile.topic_frequency[domain] = profile.topic_frequency.get(domain, 0) + 1
        
        # 5. 更新 active_hours
        current_hour = datetime.now().hour
        profile.active_hours[current_hour] = profile.active_hours.get(current_hour, 0) + 1
        
        # 6. 更新 total_interactions
        profile.total_interactions += 1
        profile.last_interaction = datetime.now()
        
        # 7. 定期更新偏好（每 N 次交互）
        if profile.total_interactions % self.config.preference_update_interval == 0:
            self._update_preferences(profile)
        
        logger.debug(
            f"Updated profile for user {user_id}: "
            f"interactions={profile.total_interactions}, domains={detected_domains}"
        )
    
    def _detect_domains(self, query: str) -> List[str]:
        """
        检测查询涉及的领域
        
        Args:
            query: 查询内容
            
        Returns:
            List[str]: 检测到的领域列表
        """
        query_lower = query.lower()
        detected = []
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in query_lower:
                    detected.append(domain)
                    break
        
        return detected if detected else ["general"]
    
    def _update_preferences(self, profile: UserLearningProfile) -> None:
        """
        根据历史数据更新用户偏好
        
        Args:
            profile: 用户画像
        """
        # 更新 preferred_detail_level
        # 基于查询复杂度趋势：复杂查询多 -> 偏好详细回答
        if profile.query_complexity_trend:
            avg_complexity = sum(profile.query_complexity_trend) / len(profile.query_complexity_trend)
            profile.preferred_detail_level = avg_complexity
        
        # 更新 preferred_tone
        # 这里简化处理：专业度高 -> professional, 否则 -> friendly
        avg_expertise = sum(profile.expertise_scores.values()) / len(profile.expertise_scores) if profile.expertise_scores else 0.5
        if avg_expertise > 0.7:
            profile.preferred_tone = "professional"
        elif avg_expertise < 0.3:
            profile.preferred_tone = "friendly"
        else:
            profile.preferred_tone = "balanced"
    
    def predict_preference(self, user_id: str) -> Dict[str, Any]:
        """
        预测用户偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 预测的用户偏好
        """
        profile = self._user_profiles.get(user_id)
        
        if profile is None or profile.total_interactions < 3:
            # 用户数据不足，返回默认偏好
            return {
                "detail_level": 0.5,
                "tone": "professional",
                "expertise_level": 0.5,
                "top_interests": [],
                "preferred_format": "structured",
                "is_default": True,
            }
        
        # 计算专业度
        expertise_level = sum(profile.expertise_scores.values()) / len(profile.expertise_scores) if profile.expertise_scores else 0.5
        
        # 获取 Top 兴趣
        sorted_topics = sorted(
            profile.topic_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_interests = [t[0] for t in sorted_topics[:5]]
        
        # 推断偏好格式
        if profile.preferred_detail_level > 0.7:
            preferred_format = "detailed"
        elif profile.preferred_detail_level < 0.3:
            preferred_format = "concise"
        else:
            preferred_format = "structured"
        
        return {
            "detail_level": profile.preferred_detail_level,
            "tone": profile.preferred_tone,
            "expertise_level": expertise_level,
            "top_interests": top_interests,
            "preferred_format": preferred_format,
            "is_default": False,
        }
    
    def update_from_feedback(self, user_id: str, feedback: UserFeedback) -> None:
        """
        根据反馈更新偏好模型
        
        Args:
            user_id: 用户ID
            feedback: 用户反馈
        """
        if not self.config.enable_preference_learning:
            return
        
        profile = self._get_or_create_profile(user_id)
        
        # 根据反馈调整偏好
        if feedback.feedback_type == FeedbackType.POSITIVE:
            # 正反馈 → 当前设置合适，轻微强化
            pass  # 保持当前偏好
            
        elif feedback.feedback_type == FeedbackType.NEGATIVE:
            # 负反馈 → 可能需要调整
            # 检查是否有关于详细程度的线索
            comment_lower = feedback.comment.lower()
            
            if any(w in comment_lower for w in ["太长", "太详细", "简洁", "太啰嗦"]):
                # 用户觉得太详细
                profile.preferred_detail_level = max(0.0, profile.preferred_detail_level - 0.1)
                
            elif any(w in comment_lower for w in ["太简单", "不够详细", "更多", "展开"]):
                # 用户觉得不够详细
                profile.preferred_detail_level = min(1.0, profile.preferred_detail_level + 0.1)
                
            elif any(w in comment_lower for w in ["太专业", "看不懂", "通俗"]):
                # 用户觉得太专业
                profile.preferred_tone = "friendly"
                
            elif any(w in comment_lower for w in ["太基础", "深入", "专业"]):
                # 用户觉得太基础
                profile.preferred_tone = "professional"
        
        elif feedback.feedback_type == FeedbackType.CORRECTION:
            # 修正反馈 → 记录但不直接调整偏好
            pass
        
        logger.debug(f"Updated preferences from feedback for user {user_id}")
    
    def estimate_expertise(self, user_id: str, domain: str = "general") -> float:
        """
        估计用户在特定领域的专业度 (0-1)
        
        基于：查询复杂度趋势、使用的专业术语、满意度与内容深度的关系
        
        Args:
            user_id: 用户ID
            domain: 领域名称
            
        Returns:
            float: 专业度估计值 (0-1)
        """
        profile = self._user_profiles.get(user_id)
        
        if profile is None:
            return 0.5  # 默认中等专业度
        
        # 获取领域专业度
        domain_expertise = profile.expertise_scores.get(domain, 0.5)
        
        # 结合查询复杂度趋势
        if profile.query_complexity_trend:
            recent_complexity = sum(profile.query_complexity_trend[-10:]) / min(10, len(profile.query_complexity_trend))
            # 加权平均
            expertise = 0.6 * domain_expertise + 0.4 * recent_complexity
        else:
            expertise = domain_expertise
        
        return max(0.0, min(1.0, expertise))
    
    def estimate_query_complexity(self, query: str) -> float:
        """
        估计查询的复杂度
        
        Args:
            query: 查询内容
            
        Returns:
            float: 复杂度 (0-1)
        """
        complexity = 0.5  # 基础复杂度
        query_lower = query.lower()
        
        # 基于查询长度
        if len(query) > 100:
            complexity += 0.1
        if len(query) > 200:
            complexity += 0.1
        
        # 基于专业术语
        for level, terms in self.PROFESSIONAL_TERMS.items():
            for term in terms:
                if term in query_lower:
                    if level == "high":
                        complexity += 0.15
                    elif level == "medium":
                        complexity += 0.05
                    elif level == "basic":
                        complexity -= 0.1
                    break  # 每个级别只计算一次
        
        # 基于问题类型
        if re.search(r'(为什么|如何|怎么).*(和|与|区别|比较)', query):
            complexity += 0.1  # 比较类问题较复杂
        if re.search(r'(最佳|优化|提升|改进)', query):
            complexity += 0.1  # 优化类问题较复杂
        
        return max(0.0, min(1.0, complexity))
    
    def get_user_profile(self, user_id: str) -> Optional[UserLearningProfile]:
        """
        获取用户学习画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserLearningProfile]: 用户画像，不存在则返回 None
        """
        return self._user_profiles.get(user_id)
    
    def get_all_profiles_summary(self) -> Dict[str, Any]:
        """
        获取所有用户画像摘要
        
        Returns:
            Dict: 用户画像汇总统计
        """
        if not self._user_profiles:
            return {
                "total_users": 0,
                "active_users_7d": 0,
                "avg_interactions": 0.0,
                "expertise_distribution": {},
                "tone_distribution": {},
            }
        
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        
        total_interactions = 0
        active_users_7d = 0
        tone_counts = defaultdict(int)
        expertise_buckets = {"beginner": 0, "intermediate": 0, "advanced": 0}
        
        for profile in self._user_profiles.values():
            total_interactions += profile.total_interactions
            
            if profile.last_interaction >= week_ago:
                active_users_7d += 1
            
            tone_counts[profile.preferred_tone] += 1
            
            # 专业度分桶
            avg_expertise = sum(profile.expertise_scores.values()) / len(profile.expertise_scores) if profile.expertise_scores else 0.5
            if avg_expertise < 0.33:
                expertise_buckets["beginner"] += 1
            elif avg_expertise < 0.66:
                expertise_buckets["intermediate"] += 1
            else:
                expertise_buckets["advanced"] += 1
        
        total_users = len(self._user_profiles)
        
        return {
            "total_users": total_users,
            "active_users_7d": active_users_7d,
            "avg_interactions": total_interactions / total_users if total_users > 0 else 0.0,
            "expertise_distribution": expertise_buckets,
            "tone_distribution": dict(tone_counts),
        }
    
    def get_personalization_accuracy(self) -> float:
        """
        计算个性化准确度
        
        基于用户满意度历史计算
        
        Returns:
            float: 个性化准确度 (0-1)
        """
        if not self._user_profiles:
            return 0.0
        
        satisfaction_scores = []
        
        for profile in self._user_profiles.values():
            if profile.satisfaction_history:
                avg_satisfaction = sum(profile.satisfaction_history) / len(profile.satisfaction_history)
                satisfaction_scores.append(avg_satisfaction)
        
        if not satisfaction_scores:
            return 0.0
        
        return sum(satisfaction_scores) / len(satisfaction_scores)
