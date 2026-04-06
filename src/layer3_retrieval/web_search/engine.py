"""
Web Search Engine - 互联网搜索引擎
集成多种搜索引擎API，提供统一的搜索接口
"""

import asyncio
import aiohttp
import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from urllib.parse import quote_plus
import hashlib
import time

from .models import WebSearchResult, WebSearchConfig

logger = logging.getLogger(__name__)


class WebSearchEngine:
    """
    互联网搜索引擎
    
    支持多种搜索引擎API集成，提供异步搜索能力和结果去重
    """
    
    def __init__(self, config: WebSearchConfig):
        """
        初始化搜索引擎
        
        Args:
            config: 搜索配置
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = {}
        self._cache = {}  # 简单的内存缓存
        self._cache_ttl = 3600  # 1小时缓存
        
        # 搜索引擎处理器映射
        self._search_handlers = {
            'google': self._search_google,
            'bing': self._search_bing,
            'duckduckgo': self._search_duckduckgo
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def initialize(self):
        """初始化HTTP会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers={
                    'User-Agent': 'NecoRAG-WebSearch/1.0'
                }
            )
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _check_rate_limit(self, engine: str) -> bool:
        """
        检查速率限制
        
        Args:
            engine: 搜索引擎名称
            
        Returns:
            bool: 是否允许请求
        """
        now = time.time()
        key = f"{engine}"
        
        if key not in self._rate_limiter:
            self._rate_limiter[key] = []
        
        # 清理过期的请求记录
        self._rate_limiter[key] = [
            timestamp for timestamp in self._rate_limiter[key]
            if now - timestamp < 60  # 1分钟窗口
        ]
        
        # 检查是否超过限制
        if len(self._rate_limiter[key]) >= self.config.rate_limit:
            return False
        
        # 记录本次请求
        self._rate_limiter[key].append(now)
        return True
    
    def _get_cache_key(self, query: str, engine: str) -> str:
        """生成缓存键"""
        return hashlib.md5(f"{engine}:{query}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """检查缓存是否有效"""
        if not cache_entry:
            return False
        return (time.time() - cache_entry['timestamp']) < self._cache_ttl
    
    async def search(self, query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
        """
        执行互联网搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            List[WebSearchResult]: 搜索结果列表
        """
        if not self.config.enable_web_search:
            logger.info("Web search is disabled")
            return []
        
        max_results = max_results or self.config.max_results
        
        # 检查缓存
        cache_key = self._get_cache_key(query, ','.join(self.config.search_engines))
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            logger.info(f"Cache hit for query: {query}")
            cached_results = self._cache[cache_key]['results'][:max_results]
            return [WebSearchResult(**result) for result in cached_results]
        
        # 初始化会话
        await self.initialize()
        
        # 并发执行多个搜索引擎
        tasks = []
        for engine in self.config.search_engines:
            if engine in self._search_handlers and self._check_rate_limit(engine):
                task = self._search_handlers[engine](query, max_results)
                tasks.append(task)
        
        if not tasks:
            logger.warning("No available search engines")
            return []
        
        # 执行并发搜索
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并和去重结果
        all_results = []
        seen_urls: Set[str] = set()
        
        for results in results_lists:
            if isinstance(results, Exception):
                logger.error(f"Search engine error: {results}")
                continue
            if not isinstance(results, list):
                continue
                
            for result in results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    all_results.append(result)
        
        # 按综合评分排序
        all_results.sort(key=lambda x: x.composite_score, reverse=True)
        
        # 应用过滤条件
        filtered_results = [
            result for result in all_results
            if (result.credibility_score >= self.config.min_credibility and
                result.relevance_score >= self.config.min_relevance)
        ][:max_results]
        
        # 缓存结果
        self._cache[cache_key] = {
            'results': [result.to_dict() for result in filtered_results],
            'timestamp': time.time()
        }
        
        logger.info(f"Search completed: {len(filtered_results)} results for query '{query}'")
        return filtered_results
    
    async def _search_google(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Google搜索实现
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            List[WebSearchResult]: Google搜索结果
        """
        api_key = self.config.api_keys.get('google_api_key')
        cx = self.config.api_keys.get('google_cx')
        
        if not api_key or not cx:
            logger.warning("Google API key or CX not configured")
            return []
        
        try:
            encoded_query = quote_plus(query)
            url = (
                f"https://www.googleapis.com/customsearch/v1"
                f"?key={api_key}&cx={cx}&q={encoded_query}"
                f"&num={min(max_results, 10)}"
            )
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Google API error: {response.status}")
                    return []
                
                data = await response.json()
                
                results = []
                for item in data.get('items', []):
                    result = WebSearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        snippet=item.get('snippet', ''),
                        source='google',
                        credibility_score=0.9,  # Google结果通常可信度较高
                        relevance_score=0.8
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    async def _search_bing(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Bing搜索实现
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            List[WebSearchResult]: Bing搜索结果
        """
        api_key = self.config.api_keys.get('bing_api_key')
        
        if not api_key:
            logger.warning("Bing API key not configured")
            return []
        
        try:
            encoded_query = quote_plus(query)
            url = f"https://api.bing.microsoft.com/v7.0/search?q={encoded_query}&count={max_results}"
            
            headers = {
                'Ocp-Apim-Subscription-Key': api_key
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Bing API error: {response.status}")
                    return []
                
                data = await response.json()
                
                results = []
                for item in data.get('webPages', {}).get('value', []):
                    result = WebSearchResult(
                        title=item.get('name', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source='bing',
                        credibility_score=0.8,
                        relevance_score=0.7
                    )
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return []
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        DuckDuckGo搜索实现（无需API密钥）
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            
        Returns:
            List[WebSearchResult]: DuckDuckGo搜索结果
        """
        try:
            # DuckDuckGo Instant Answer API
            encoded_query = quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"DuckDuckGo API error: {response.status}")
                    return []
                
                data = await response.json()
                
                results = []
                
                # 处理抽象结果
                if data.get('Abstract'):
                    result = WebSearchResult(
                        title=data.get('Heading', query),
                        url=data.get('AbstractURL', ''),
                        snippet=data.get('Abstract', ''),
                        source='duckduckgo',
                        credibility_score=0.7,
                        relevance_score=0.9
                    )
                    results.append(result)
                
                # 处理相关结果
                for item in data.get('Results', [])[:max_results-1]:
                    if isinstance(item, dict) and item.get('FirstURL'):
                        result = WebSearchResult(
                            title=item.get('Text', ''),
                            url=item.get('FirstURL', ''),
                            snippet='',
                            source='duckduckgo',
                            credibility_score=0.6,
                            relevance_score=0.6
                        )
                        results.append(result)
                
                return results[:max_results]
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []


# 便捷函数
async def search_web(query: str, config: Optional[WebSearchConfig] = None) -> List[WebSearchResult]:
    """
    便捷的网页搜索函数
    
    Args:
        query: 搜索查询
        config: 搜索配置（可选）
        
    Returns:
        List[WebSearchResult]: 搜索结果
    """
    if config is None:
        config = WebSearchConfig()
    
    async with WebSearchEngine(config) as engine:
        return await engine.search(query)