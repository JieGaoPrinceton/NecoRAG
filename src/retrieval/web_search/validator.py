"""
Search Result Validator - 搜索结果验证器
对互联网搜索结果进行质量评估、去重和筛选
"""

import re
import logging
from typing import List, Set, Tuple
from urllib.parse import urlparse
import hashlib

from .models import WebSearchResult

logger = logging.getLogger(__name__)


class SearchResultValidator:
    """
    搜索结果验证器
    
    负责对搜索结果进行质量评估、重复检测和内容过滤
    """
    
    def __init__(self, 
                 min_credibility: float = 0.5,
                 min_relevance: float = 0.3,
                 enable_deduplication: bool = True,
                 enable_content_filter: bool = True):
        """
        初始化验证器
        
        Args:
            min_credibility: 最低可信度阈值
            min_relevance: 最低相关性阈值
            enable_deduplication: 是否启用去重
            enable_content_filter: 是否启用内容过滤
        """
        self.min_credibility = min_credibility
        self.min_relevance = min_relevance
        self.enable_deduplication = enable_deduplication
        self.enable_content_filter = enable_content_filter
        
        # 可信域名列表（可根据需要扩展）
        self.trusted_domains = {
            'wikipedia.org', 'github.com', 'stackoverflow.com',
            'medium.com', 'arxiv.org', 'acm.org', 'ieee.org',
            'nature.com', 'science.org', 'mit.edu', 'stanford.edu',
            'harvard.edu', 'ox.ac.uk', 'cam.ac.uk'
        }
        
        # 可疑域名列表
        self.suspicious_domains = {
            'example.com', 'test.com', 'fake-site.com'
        }
    
    def validate_and_filter(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """
        验证和过滤搜索结果
        
        Args:
            results: 原始搜索结果列表
            
        Returns:
            List[WebSearchResult]: 验证后的结果列表
        """
        if not results:
            return []
        
        logger.info(f"Validating {len(results)} search results")
        
        # 1. 内容过滤
        if self.enable_content_filter:
            results = self._filter_content(results)
        
        # 2. 重复检测和去重
        if self.enable_deduplication:
            results = self._deduplicate_results(results)
        
        # 3. 质量评分
        results = self._assess_quality(results)
        
        # 4. 应用阈值过滤
        filtered_results = [
            result for result in results
            if (result.credibility_score >= self.min_credibility and
                result.relevance_score >= self.min_relevance)
        ]
        
        logger.info(f"Validation completed: {len(filtered_results)}/{len(results)} results passed")
        return filtered_results
    
    def _filter_content(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """
        内容过滤
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[WebSearchResult]: 过滤后的结果列表
        """
        filtered = []
        
        for result in results:
            # 检查域名可信度
            domain = urlparse(result.url).netloc.lower()
            
            # 过滤可疑域名
            if any(suspicious in domain for suspicious in self.suspicious_domains):
                logger.debug(f"Filtered suspicious domain: {domain}")
                continue
            
            # 检查内容质量
            if not self._is_content_quality_good(result):
                logger.debug(f"Filtered low quality content: {result.url}")
                continue
            
            # 检查语言一致性
            if not self._is_language_consistent(result):
                logger.debug(f"Filtered inconsistent language: {result.url}")
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _deduplicate_results(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """
        去重处理
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[WebSearchResult]: 去重后的结果列表
        """
        seen_hashes: Set[str] = set()
        deduplicated = []
        
        for result in results:
            # 基于内容哈希去重
            content_hash = self._get_content_hash(result)
            
            if content_hash in seen_hashes:
                logger.debug(f"Duplicate detected: {result.url}")
                continue
            
            seen_hashes.add(content_hash)
            deduplicated.append(result)
        
        return deduplicated
    
    def _assess_quality(self, results: List[WebSearchResult]) -> List[WebSearchResult]:
        """
        质量评分
        
        Args:
            results: 搜索结果列表
            
        Returns:
            List[WebSearchResult]: 评分后的结果列表
        """
        assessed_results = []
        
        for result in results:
            # 评估可信度
            credibility = self._assess_credibility(result)
            
            # 评估相关性
            relevance = self._assess_relevance(result)
            
            # 更新评分
            result.credibility_score = credibility
            result.relevance_score = relevance
            
            assessed_results.append(result)
        
        return assessed_results
    
    def _assess_credibility(self, result: WebSearchResult) -> float:
        """
        评估结果可信度
        
        Args:
            result: 搜索结果
            
        Returns:
            float: 可信度评分 (0-1)
        """
        score = 0.5  # 基础分数
        
        domain = urlparse(result.url).netloc.lower()
        
        # 域名可信度加分
        if any(trusted in domain for trusted in self.trusted_domains):
            score += 0.3
        
        # 域名长度惩罚（过短可能不可信）
        if len(domain) < 5:
            score -= 0.2
        
        # HTTPS加分
        if result.url.startswith('https://'):
            score += 0.1
        
        # 内容质量加分
        if self._has_quality_indicators(result):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _assess_relevance(self, result: WebSearchResult) -> float:
        """
        评估结果相关性
        
        Args:
            result: 搜索结果
            
        Returns:
            float: 相关性评分 (0-1)
        """
        # 这里可以实现更复杂的相关性评估逻辑
        # 目前使用简单的启发式方法
        score = 0.5
        
        # 标题和摘要长度适中加分
        title_length = len(result.title)
        snippet_length = len(result.snippet)
        
        if 10 <= title_length <= 100:
            score += 0.1
        if 50 <= snippet_length <= 500:
            score += 0.1
        
        # 有完整内容加分
        if result.content:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def _is_content_quality_good(self, result: WebSearchResult) -> bool:
        """
        检查内容质量
        
        Args:
            result: 搜索结果
            
        Returns:
            bool: 内容质量是否良好
        """
        # 检查标题质量
        if not result.title or len(result.title.strip()) < 3:
            return False
        
        # 检查摘要质量
        if not result.snippet or len(result.snippet.strip()) < 10:
            return False
        
        # 检查是否包含明显的垃圾内容特征
        spam_indicators = [
            r'\b(buy now|click here|limited time)\b',
            r'http[s]?://[^ ]*\.tk/',
            r'[^a-zA-Z0-9\s]{5,}'
        ]
        
        content = f"{result.title} {result.snippet}".lower()
        for pattern in spam_indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    def _is_language_consistent(self, result: WebSearchResult) -> bool:
        """
        检查语言一致性
        
        Args:
            result: 搜索结果
            
        Returns:
            bool: 语言是否一致
        """
        # 简单的语言检测（可以根据需要扩展）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', result.title + result.snippet))
        english_chars = len(re.findall(r'[a-zA-Z]', result.title + result.snippet))
        
        # 如果主要是中文内容，标记为中文
        if chinese_chars > english_chars:
            result.language = 'zh'
        else:
            result.language = 'en'
        
        # 这里可以添加更严格的语言一致性检查
        return True
    
    def _has_quality_indicators(self, result: WebSearchResult) -> bool:
        """
        检查是否有质量指示器
        
        Args:
            result: 搜索结果
            
        Returns:
            bool: 是否有质量指示器
        """
        quality_indicators = [
            'wikipedia', 'github', 'stackoverflow', 'academic', 'research',
            'official', 'documentation', 'tutorial'
        ]
        
        content = f"{result.title} {result.snippet}".lower()
        return any(indicator in content for indicator in quality_indicators)
    
    def _get_content_hash(self, result: WebSearchResult) -> str:
        """
        获取内容哈希用于去重
        
        Args:
            result: 搜索结果
            
        Returns:
            str: 内容哈希值
        """
        # 使用标题和URL的一部分作为哈希源
        content_for_hash = f"{result.title.lower()}|{urlparse(result.url).netloc}"
        return hashlib.md5(content_for_hash.encode()).hexdigest()
    
    def get_statistics(self, results: List[WebSearchResult]) -> dict:
        """
        获取结果统计信息
        
        Args:
            results: 搜索结果列表
            
        Returns:
            dict: 统计信息
        """
        if not results:
            return {}
        
        credibility_scores = [r.credibility_score for r in results]
        relevance_scores = [r.relevance_score for r in results]
        
        return {
            'total_results': len(results),
            'avg_credibility': sum(credibility_scores) / len(credibility_scores),
            'avg_relevance': sum(relevance_scores) / len(relevance_scores),
            'high_credibility_count': len([s for s in credibility_scores if s >= 0.8]),
            'high_relevance_count': len([s for s in relevance_scores if s >= 0.8]),
            'sources': list(set(r.source for r in results)),
            'domains': list(set(urlparse(r.url).netloc for r in results))
        }