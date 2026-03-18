"""
情境标签生成器
为每个 Chunk 自动打标，模拟猫胡须对环境微变化的感知
"""

from typing import List, Optional, Dict, Any
from src.perception.models import Chunk, ContextTags
from src.core.base import BaseTagger


class ContextualTagger(BaseTagger):
    """
    情境标签生成器
    
    为文本块生成时间、情感、重要性、主题等标签
    """
    
    def __init__(
        self,
        sentiment_model: str = "default",
        importance_threshold: float = 0.5
    ):
        """
        初始化标签生成器
        
        Args:
            sentiment_model: 情感分析模型
            importance_threshold: 重要性阈值
        """
        self.sentiment_model = sentiment_model
        self.importance_threshold = importance_threshold
    
    def generate_tags(self, chunk: Chunk) -> ContextTags:
        """
        生成完整情境标签
        
        Args:
            chunk: 文本块
            
        Returns:
            ContextTags: 情境标签
        """
        return ContextTags(
            time_tag=self.generate_time_tag(chunk),
            sentiment_tag=self.generate_sentiment_tag(chunk),
            importance_score=self.generate_importance_tag(chunk),
            topic_tags=self.generate_topic_tags(chunk)
        )
    
    def tag(self, chunk: Chunk) -> Dict[str, Any]:
        """
        为分块生成情境标签（抽象基类接口实现）
        
        Args:
            chunk: 分块对象
            
        Returns:
            Dict[str, Any]: 标签字典
        """
        tags = self.generate_tags(chunk)
        return {
            "time_tag": tags.time_tag,
            "sentiment_tag": tags.sentiment_tag,
            "importance_score": tags.importance_score,
            "topic_tags": tags.topic_tags
        }
    
    def generate_time_tag(self, chunk: Chunk) -> str:
        """
        生成时间标签
        
        Args:
            chunk: 文本块
            
        Returns:
            str: 时间标签
            
        TODO: 实现时间实体识别
        """
        # 最小实现：检测文档元数据
        if 'created_at' in chunk.metadata:
            return f"created:{chunk.metadata['created_at']}"
        return "unknown"
    
    def generate_sentiment_tag(self, chunk: Chunk) -> str:
        """
        生成情感标签
        
        Args:
            chunk: 文本块
            
        Returns:
            str: 情感标签（positive/negative/neutral）
            
        TODO: 集成情感分析模型
        """
        # 最小实现：简单关键词检测
        content = chunk.content.lower()
        
        positive_words = ['好', '优秀', '成功', '高兴', 'happy', 'good', 'great']
        negative_words = ['坏', '失败', '错误', '悲伤', 'bad', 'fail', 'error']
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def generate_importance_tag(self, chunk: Chunk) -> float:
        """
        生成重要性评分
        
        Args:
            chunk: 文本块
            
        Returns:
            float: 重要性评分 (0-1)
            
        TODO: 实现基于内容质量、信息密度的评分
        """
        # 最小实现：基于长度和关键词密度
        content = chunk.content
        
        # 信息密度指标
        word_count = len(content.split())
        unique_words = len(set(content.split()))
        
        if word_count == 0:
            return 0.0
        
        diversity = unique_words / word_count
        length_factor = min(len(content) / 500, 1.0)
        
        return (diversity + length_factor) / 2
    
    def generate_topic_tags(self, chunk: Chunk) -> List[str]:
        """
        生成主题标签
        
        Args:
            chunk: 文本块
            
        Returns:
            List[str]: 主题标签列表
            
        TODO: 实现主题分类和关键词提取
        """
        # 最小实现：提取高频词
        words = chunk.content.lower().split()
        word_freq = {}
        
        for word in words:
            if len(word) > 3:  # 过滤短词
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 返回前3个高频词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:3]]
