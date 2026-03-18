"""
Adaptive Learning 集体智慧聚合器

从所有用户的交互中提炼共性智慧：
- 识别共同的知识盲点
- 提取高效的查询模式
- 发现知识趋势
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from collections import defaultdict

from .config import AdaptiveLearningConfig
from .models import CommunityInsight

if TYPE_CHECKING:
    from .feedback import FeedbackCollector
    from .preference_predictor import PreferencePredictor


logger = logging.getLogger(__name__)


class CollectiveIntelligence:
    """
    集体智慧聚合器
    
    从所有用户的交互中提炼共性智慧：
    - 识别共同的知识盲点
    - 提取高效的查询模式
    - 发现知识趋势
    """
    
    def __init__(
        self, 
        config: AdaptiveLearningConfig = None, 
        feedback_collector: 'FeedbackCollector' = None,
        preference_predictor: 'PreferencePredictor' = None
    ):
        """
        初始化集体智慧聚合器
        
        Args:
            config: 自适应学习配置
            feedback_collector: 反馈收集器（可选）
            preference_predictor: 偏好预测器（可选）
        """
        self.config = config or AdaptiveLearningConfig.default()
        self._feedback_collector = feedback_collector
        self._preference_predictor = preference_predictor
        self._insights: List[CommunityInsight] = []
        
        # 内部统计数据
        self._query_topics: Dict[str, int] = defaultdict(int)  # topic -> count
        self._low_satisfaction_topics: Dict[str, List[float]] = defaultdict(list)  # topic -> [scores]
        self._query_patterns: Dict[str, int] = defaultdict(int)  # pattern -> count
        self._last_insight_generation: Optional[datetime] = None
    
    def record_query_data(
        self, 
        query: str, 
        topics: List[str], 
        satisfaction: float,
        hit: bool = True
    ) -> None:
        """
        记录查询数据用于集体智慧分析
        
        Args:
            query: 查询内容
            topics: 涉及的主题
            satisfaction: 满意度
            hit: 是否命中
        """
        if not self.config.enable_collective_learning:
            return
        
        # 更新主题频率
        for topic in topics:
            self._query_topics[topic] += 1
            
            # 记录低满意度
            if satisfaction < 0.5:
                self._low_satisfaction_topics[topic].append(satisfaction)
        
        # 提取查询模式（简化版：基于关键词模式）
        pattern = self._extract_query_pattern(query)
        if pattern:
            self._query_patterns[pattern] += 1
    
    def _extract_query_pattern(self, query: str) -> Optional[str]:
        """
        提取查询模式
        
        Args:
            query: 查询内容
            
        Returns:
            Optional[str]: 查询模式
        """
        # 简单的模式提取：基于问题类型
        patterns = [
            ("什么是", "definition"),
            ("如何", "how_to"),
            ("为什么", "why"),
            ("怎么", "how_to"),
            ("区别", "comparison"),
            ("比较", "comparison"),
            ("优缺点", "pros_cons"),
            ("最佳实践", "best_practice"),
            ("例子", "example"),
            ("推荐", "recommendation"),
        ]
        
        query_lower = query.lower()
        for keyword, pattern in patterns:
            if keyword in query_lower:
                return pattern
        
        return "general"
    
    def identify_common_gaps(self) -> List[Dict[str, Any]]:
        """
        识别社群共同的知识盲区
        
        统计多用户遇到的低满意度查询主题
        
        Returns:
            List[Dict]: 知识盲区列表
        """
        if not self.config.enable_collective_learning:
            return []
        
        gaps = []
        
        for topic, scores in self._low_satisfaction_topics.items():
            if len(scores) >= self.config.min_users_for_insight:
                avg_satisfaction = sum(scores) / len(scores)
                
                if avg_satisfaction < 0.4:  # 平均满意度低于40%
                    gaps.append({
                        "topic": topic,
                        "affected_queries": len(scores),
                        "avg_satisfaction": avg_satisfaction,
                        "severity": "high" if avg_satisfaction < 0.25 else "medium",
                    })
        
        # 按严重程度和影响范围排序
        gaps.sort(key=lambda x: (x["severity"] == "high", x["affected_queries"]), reverse=True)
        
        return gaps[:10]  # 返回 Top 10
    
    def extract_best_practices(self) -> List[Dict[str, Any]]:
        """
        提取最佳查询实践
        
        - 高满意度的查询模式
        - 有效的查询改写方式
        
        Returns:
            List[Dict]: 最佳实践列表
        """
        if not self.config.enable_collective_learning:
            return []
        
        best_practices = []
        
        # 分析查询模式的成功率
        if self._feedback_collector:
            summary = self._feedback_collector.get_feedback_summary()
            patterns = self._feedback_collector.analyze_feedback_patterns()
            
            # 高满意度的查询类型
            for query_type, satisfaction in patterns.get("query_type_satisfaction", {}).items():
                if satisfaction > 0.7:
                    best_practices.append({
                        "type": "query_pattern",
                        "pattern": query_type,
                        "satisfaction": satisfaction,
                        "description": f"使用 '{query_type}' 类型的查询通常获得较高满意度",
                    })
        
        # 分析有效的查询模式
        popular_patterns = sorted(
            self._query_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for pattern, count in popular_patterns:
            if count >= self.config.min_users_for_insight:
                best_practices.append({
                    "type": "popular_pattern",
                    "pattern": pattern,
                    "usage_count": count,
                    "description": f"'{pattern}' 是常用的查询模式",
                })
        
        return best_practices
    
    def detect_trending_topics(self) -> List[Dict[str, Any]]:
        """
        检测热门话题趋势
        
        近期查询频率上升最快的主题
        
        Returns:
            List[Dict]: 热门话题列表
        """
        if not self.config.enable_collective_learning:
            return []
        
        # 按频率排序主题
        sorted_topics = sorted(
            self._query_topics.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        trending = []
        for topic, count in sorted_topics[:10]:
            trending.append({
                "topic": topic,
                "query_count": count,
                "trend": "rising" if count > 5 else "stable",
            })
        
        return trending
    
    def generate_insights(self) -> List[CommunityInsight]:
        """
        生成综合洞察报告
        
        Returns:
            List[CommunityInsight]: 洞察列表
        """
        if not self.config.enable_collective_learning:
            return []
        
        # 检查是否需要刷新
        if self._last_insight_generation:
            time_since_last = (datetime.now() - self._last_insight_generation).total_seconds()
            if time_since_last < self.config.insight_refresh_interval:
                return self._insights  # 返回缓存的洞察
        
        new_insights = []
        
        # 1. 知识盲区洞察
        gaps = self.identify_common_gaps()
        for gap in gaps[:3]:  # Top 3 gaps
            insight = CommunityInsight(
                insight_type="gap",
                title=f"知识盲区: {gap['topic']}",
                description=f"主题 '{gap['topic']}' 的查询满意度较低 ({gap['avg_satisfaction']:.1%})，"
                           f"影响 {gap['affected_queries']} 个查询",
                affected_users=gap['affected_queries'],
                confidence=0.8 if gap['severity'] == 'high' else 0.6,
                data=gap,
            )
            new_insights.append(insight)
        
        # 2. 最佳实践洞察
        best_practices = self.extract_best_practices()
        for practice in best_practices[:3]:  # Top 3 practices
            insight = CommunityInsight(
                insight_type="best_practice",
                title=f"最佳实践: {practice['pattern']}",
                description=practice['description'],
                affected_users=practice.get('usage_count', 0),
                confidence=0.7,
                data=practice,
            )
            new_insights.append(insight)
        
        # 3. 趋势洞察
        trending = self.detect_trending_topics()
        for topic_info in trending[:3]:  # Top 3 trending
            if topic_info['query_count'] >= self.config.min_users_for_insight:
                insight = CommunityInsight(
                    insight_type="trend",
                    title=f"热门话题: {topic_info['topic']}",
                    description=f"主题 '{topic_info['topic']}' 近期查询量为 {topic_info['query_count']}",
                    affected_users=topic_info['query_count'],
                    confidence=0.6,
                    data=topic_info,
                )
                new_insights.append(insight)
        
        # 4. 用户群体洞察（如果有偏好预测器）
        if self._preference_predictor:
            profiles_summary = self._preference_predictor.get_all_profiles_summary()
            
            if profiles_summary.get("total_users", 0) >= self.config.min_users_for_insight:
                # 专业度分布洞察
                expertise_dist = profiles_summary.get("expertise_distribution", {})
                dominant_level = max(expertise_dist.items(), key=lambda x: x[1])[0] if expertise_dist else "unknown"
                
                insight = CommunityInsight(
                    insight_type="user_profile",
                    title="用户群体特征",
                    description=f"用户群体主要为 {dominant_level} 级别，"
                               f"共 {profiles_summary.get('total_users', 0)} 个用户，"
                               f"近7天活跃 {profiles_summary.get('active_users_7d', 0)} 人",
                    affected_users=profiles_summary.get('total_users', 0),
                    confidence=0.75,
                    data=profiles_summary,
                )
                new_insights.append(insight)
        
        # 更新缓存
        self._insights = new_insights
        self._last_insight_generation = datetime.now()
        
        # 限制洞察数量
        if len(self._insights) > self.config.max_insights:
            self._insights = self._insights[:self.config.max_insights]
        
        logger.info(f"Generated {len(new_insights)} community insights")
        
        return self._insights
    
    def get_insights(self) -> List[CommunityInsight]:
        """
        获取当前洞察列表
        
        Returns:
            List[CommunityInsight]: 洞察列表
        """
        return self._insights
    
    def get_insights_summary(self) -> Dict[str, Any]:
        """
        获取洞察汇总
        
        Returns:
            Dict: 洞察汇总信息
        """
        if not self._insights:
            return {
                "total_insights": 0,
                "by_type": {},
                "last_generated": None,
            }
        
        by_type = defaultdict(int)
        for insight in self._insights:
            by_type[insight.insight_type] += 1
        
        return {
            "total_insights": len(self._insights),
            "by_type": dict(by_type),
            "last_generated": self._last_insight_generation.isoformat() if self._last_insight_generation else None,
            "insights": [i.to_dict() for i in self._insights[:5]],  # 最近5条
        }
    
    def get_knowledge_coverage_growth(self) -> float:
        """
        计算知识覆盖增长率
        
        基于主题多样性增长
        
        Returns:
            float: 知识覆盖增长率
        """
        # 简化计算：基于主题数量
        total_topics = len(self._query_topics)
        
        if total_topics < 5:
            return 0.0
        
        # 假设基准是10个主题
        baseline = 10
        growth = (total_topics - baseline) / baseline if total_topics > baseline else 0.0
        
        return max(0.0, min(1.0, growth))
