"""
NecoRAG 领域相关性评分模块

实现基于关键字和文本特征的领域相关性评估
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
from enum import Enum

from .config import DomainConfig, KeywordLevel, DomainLevel


@dataclass
class RelevanceScore:
    """相关性评分结果"""
    domain_level: DomainLevel
    score: float                          # 综合评分 [0, 1]
    weight_multiplier: float              # 权重乘数
    keyword_matches: Dict[str, float]     # 匹配到的关键字及其权重
    keyword_score: float                  # 关键字得分
    density_score: float                  # 关键字密度得分
    confidence: float                     # 置信度 [0, 1]
    explanation: str = ""                 # 评分说明


class DomainRelevanceCalculator:
    """领域相关性计算器"""
    
    def __init__(self, domain_config: DomainConfig):
        """
        初始化领域相关性计算器
        
        Args:
            domain_config: 领域配置
        """
        self.config = domain_config
        self._build_keyword_index()
    
    def _build_keyword_index(self) -> None:
        """构建关键字索引（用于快速匹配）"""
        self.keyword_patterns: Dict[str, Tuple[str, float]] = {}
        
        for keyword, kw_config in self.config.keywords.items():
            # 原始关键字
            pattern = self._create_pattern(keyword)
            self.keyword_patterns[pattern] = (kw_config.keyword, kw_config.weight)
            
            # 别名
            for alias in kw_config.aliases:
                pattern = self._create_pattern(alias)
                self.keyword_patterns[pattern] = (kw_config.keyword, kw_config.weight)
    
    def _create_pattern(self, keyword: str) -> str:
        """创建匹配模式（支持中英文）"""
        # 转义特殊字符
        escaped = re.escape(keyword)
        # 对于英文添加单词边界，中文直接匹配
        if keyword.isascii():
            return r'\b' + escaped + r'\b'
        else:
            return escaped
    
    def extract_keywords(self, text: str) -> Dict[str, Tuple[int, float]]:
        """
        从文本中提取关键字
        
        Args:
            text: 输入文本
        
        Returns:
            Dict[str, Tuple[int, float]]: 关键字 -> (出现次数, 权重)
        """
        text_lower = text.lower()
        matches: Dict[str, Tuple[int, float]] = {}
        
        for pattern, (keyword, weight) in self.keyword_patterns.items():
            try:
                found = re.findall(pattern, text_lower, re.IGNORECASE)
                if found:
                    count = len(found)
                    if keyword in matches:
                        # 更新计数
                        old_count, _ = matches[keyword]
                        matches[keyword] = (old_count + count, weight)
                    else:
                        matches[keyword] = (count, weight)
            except re.error:
                continue
        
        return matches
    
    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        计算关键字得分
        
        公式: score = Σ(keyword_weight[i] × keyword_frequency[i]) / total_keywords
        
        Args:
            text: 输入文本
        
        Returns:
            Tuple[float, Dict[str, float]]: (关键字得分, 匹配到的关键字及权重)
        """
        matches = self.extract_keywords(text)
        
        if not matches:
            return 0.0, {}
        
        total_weighted_score = 0.0
        total_count = 0
        keyword_weights = {}
        
        for keyword, (count, weight) in matches.items():
            weighted = weight * count
            total_weighted_score += weighted
            total_count += count
            keyword_weights[keyword] = weight
        
        # 归一化得分
        if total_count > 0:
            score = total_weighted_score / total_count
            # 限制在合理范围内
            score = min(2.0, max(0.0, score))
        else:
            score = 0.0
        
        return score, keyword_weights
    
    def calculate_keyword_density(self, text: str) -> float:
        """
        计算关键字密度
        
        Args:
            text: 输入文本
        
        Returns:
            float: 关键字密度 [0, 1]
        """
        # 简单分词（按空格和标点）
        words = re.findall(r'\w+', text.lower())
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        matches = self.extract_keywords(text)
        keyword_occurrences = sum(count for count, _ in matches.values())
        
        density = keyword_occurrences / total_words
        # 归一化到 [0, 1]
        return min(1.0, density * 5)  # 假设 20% 密度为满分
    
    def classify_domain_level(self, keyword_score: float, 
                               density_score: float) -> DomainLevel:
        """
        根据关键字得分判定领域相关性等级
        
        Args:
            keyword_score: 关键字得分
            density_score: 关键字密度得分
        
        Returns:
            DomainLevel: 领域相关性等级
        """
        # 综合考虑关键字得分和密度
        combined_score = keyword_score * 0.7 + density_score * 0.3
        
        if combined_score >= 1.2:
            return DomainLevel.CORE
        elif combined_score >= 0.8:
            return DomainLevel.RELATED
        elif combined_score >= 0.4:
            return DomainLevel.PERIPHERAL
        else:
            return DomainLevel.OUT_OF_DOMAIN
    
    def get_domain_weight(self, domain_level: DomainLevel) -> float:
        """
        获取领域等级对应的权重乘数
        
        Args:
            domain_level: 领域等级
        
        Returns:
            float: 权重乘数
        """
        weight_map = {
            DomainLevel.CORE: self.config.core_domain_weight,
            DomainLevel.RELATED: self.config.related_domain_weight,
            DomainLevel.PERIPHERAL: self.config.peripheral_domain_weight,
            DomainLevel.OUT_OF_DOMAIN: self.config.out_of_domain_weight,
        }
        return weight_map.get(domain_level, 1.0)
    
    def calculate_relevance(self, text: str) -> RelevanceScore:
        """
        计算文本的领域相关性评分（主接口）
        
        Args:
            text: 输入文本
        
        Returns:
            RelevanceScore: 相关性评分结果
        """
        # 计算关键字得分
        keyword_score, keyword_matches = self.calculate_keyword_score(text)
        
        # 计算关键字密度
        density_score = self.calculate_keyword_density(text)
        
        # 判定领域等级
        domain_level = self.classify_domain_level(keyword_score, density_score)
        
        # 获取权重乘数
        weight_multiplier = self.get_domain_weight(domain_level)
        
        # 计算综合评分 [0, 1]
        combined_score = min(1.0, (keyword_score * 0.7 + density_score * 0.3) / 1.5)
        
        # 计算置信度（基于匹配数量）
        confidence = min(1.0, len(keyword_matches) / 5)  # 5个以上关键字为满置信度
        
        # 生成说明
        explanation = self._generate_explanation(
            domain_level, keyword_score, density_score, 
            len(keyword_matches), confidence
        )
        
        return RelevanceScore(
            domain_level=domain_level,
            score=combined_score,
            weight_multiplier=weight_multiplier,
            keyword_matches=keyword_matches,
            keyword_score=keyword_score,
            density_score=density_score,
            confidence=confidence,
            explanation=explanation
        )
    
    def _generate_explanation(self, domain_level: DomainLevel,
                               keyword_score: float, density_score: float,
                               match_count: int, confidence: float) -> str:
        """生成评分说明"""
        level_names = {
            DomainLevel.CORE: "核心领域",
            DomainLevel.RELATED: "相关领域",
            DomainLevel.PERIPHERAL: "边缘领域",
            DomainLevel.OUT_OF_DOMAIN: "领域外",
        }
        level_name = level_names.get(domain_level, "未知")
        
        return (
            f"判定为{level_name}，"
            f"匹配{match_count}个关键字，"
            f"关键字得分{keyword_score:.2f}，"
            f"密度得分{density_score:.2f}，"
            f"置信度{confidence:.0%}"
        )
    
    def batch_calculate(self, texts: List[str]) -> List[RelevanceScore]:
        """
        批量计算相关性评分
        
        Args:
            texts: 文本列表
        
        Returns:
            List[RelevanceScore]: 评分结果列表
        """
        return [self.calculate_relevance(text) for text in texts]


class QueryRelevanceEnhancer:
    """查询相关性增强器"""
    
    def __init__(self, domain_config: DomainConfig):
        self.config = domain_config
        self.calculator = DomainRelevanceCalculator(domain_config)
    
    def enhance_query(self, query: str) -> Tuple[str, List[str], float]:
        """
        增强查询（识别并提取关键字）
        
        Args:
            query: 原始查询
        
        Returns:
            Tuple[str, List[str], float]: (增强后的查询, 识别到的关键字, 关键字权重加成)
        """
        matches = self.calculator.extract_keywords(query)
        
        if not matches:
            return query, [], 1.0
        
        keywords = list(matches.keys())
        
        # 计算权重加成
        total_weight = sum(weight for _, (_, weight) in matches.items())
        weight_boost = 1.0 + (total_weight - len(matches)) * 0.1
        weight_boost = min(2.0, max(1.0, weight_boost))
        
        return query, keywords, weight_boost
    
    def expand_query_keywords(self, query: str) -> List[str]:
        """
        扩展查询关键字（添加同义词）
        
        Args:
            query: 原始查询
        
        Returns:
            List[str]: 扩展后的关键字列表
        """
        matches = self.calculator.extract_keywords(query)
        expanded = set()
        
        for keyword in matches.keys():
            expanded.add(keyword)
            # 添加同义词
            kw_config = self.config.keywords.get(keyword.lower())
            if kw_config:
                expanded.update(kw_config.aliases)
        
        return list(expanded)
