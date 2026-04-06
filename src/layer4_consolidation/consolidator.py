"""
Knowledge Consolidator - 知识固化器

负责高质量 QA 对的持久化、知识去重和合并。
"""

import hashlib
import time
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass, field

from .models import KnowledgeGap, QueryPattern

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


@dataclass
class QAPair:
    """QA 对"""
    qa_id: str
    query: str
    answer: str
    confidence: float
    evidence: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsolidationResult:
    """固化结果"""
    stored_count: int
    deduplicated_count: int
    merged_count: int
    gaps_identified: int
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeConsolidator:
    """
    知识固化器
    
    功能：
    1. 分析高频未命中 Query
    2. 自动补充知识缺口
    3. 合并碎片化知识
    4. 更新过时信息
    5. 持久化高质量 QA 对
    """
    
    def __init__(
        self,
        memory_manager=None,
        llm_client: Optional["BaseLLMClient"] = None,
        min_query_frequency: int = 5,
        quality_threshold: float = 0.7,
        similarity_threshold: float = 0.85
    ):
        """
        初始化知识固化器
        
        Args:
            memory_manager: 记忆管理器
            llm_client: LLM 客户端（用于知识合并和去重）
            min_query_frequency: 最小查询频率阈值
            quality_threshold: 质量阈值（高于此值的 QA 对才会被固化）
            similarity_threshold: 相似度阈值（用于去重）
        """
        self.memory = memory_manager
        self._llm_client = llm_client
        self.min_query_frequency = min_query_frequency
        self.quality_threshold = quality_threshold
        self.similarity_threshold = similarity_threshold
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-consolidator")
            except ImportError:
                self._llm_client = None
        
        # 内存中的 QA 缓存（用于去重检测）
        self._qa_cache: Dict[str, QAPair] = {}
        
        # 查询日志
        self._query_log: List[Dict[str, Any]] = []
        
        # 知识合并提示词
        self._merge_prompt = """请将以下相关的知识片段合并为一个完整、连贯的知识条目。

## 待合并片段
{fragments}

## 合并要求
1. 保留所有重要信息
2. 消除重复内容
3. 保持逻辑连贯
4. 使用清晰的结构

请输出合并后的知识内容："""
    
    async def run_consolidation_cycle(self) -> ConsolidationResult:
        """
        运行固化周期
        
        Returns:
            ConsolidationResult: 固化结果
        """
        start_time = time.time()
        
        stored_count = 0
        deduplicated_count = 0
        merged_count = 0
        
        # 1. 分析查询模式
        query_patterns = self.analyze_query_patterns()
        
        # 2. 识别知识缺口
        knowledge_gaps = self.identify_knowledge_gaps(query_patterns)
        
        # 3. 补充知识缺口
        for gap in knowledge_gaps:
            success = await self.fill_knowledge_gap(gap)
            if success:
                stored_count += 1
        
        # 4. 处理待固化的 QA 对
        pending_qas = self._get_pending_qa_pairs()
        for qa in pending_qas:
            # 去重检查
            if self._is_duplicate(qa):
                deduplicated_count += 1
                continue
            
            # 固化存储
            if await self._store_qa_pair(qa):
                stored_count += 1
        
        # 5. 合并碎片知识
        merged_count = await self.merge_fragments()
        
        # 6. 更新图谱连接
        await self.update_graph_connections()
        
        duration_ms = (time.time() - start_time) * 1000
        
        return ConsolidationResult(
            stored_count=stored_count,
            deduplicated_count=deduplicated_count,
            merged_count=merged_count,
            gaps_identified=len(knowledge_gaps),
            duration_ms=duration_ms,
            metadata={
                "patterns_analyzed": len(query_patterns),
                "timestamp": time.time()
            }
        )
    
    def analyze_query_patterns(self) -> List[QueryPattern]:
        """
        分析查询模式
        
        从查询日志中提取高频查询模式
        
        Returns:
            List[QueryPattern]: 查询模式列表
        """
        if not self._query_log:
            return []
        
        # 统计查询频率
        query_stats: Dict[str, Dict[str, Any]] = {}
        
        for log in self._query_log:
            query = log.get("query", "").strip().lower()
            if not query:
                continue
            
            # 简单的模式提取（可以用更复杂的方法）
            pattern = self._extract_pattern(query)
            
            if pattern not in query_stats:
                query_stats[pattern] = {
                    "count": 0,
                    "hits": 0,
                    "examples": []
                }
            
            query_stats[pattern]["count"] += 1
            if log.get("hit", False):
                query_stats[pattern]["hits"] += 1
            
            if len(query_stats[pattern]["examples"]) < 5:
                query_stats[pattern]["examples"].append(query)
        
        # 转换为 QueryPattern 列表
        patterns = []
        for pattern, stats in query_stats.items():
            count = stats["count"]
            if count >= self.min_query_frequency:
                hit_rate = stats["hits"] / count if count > 0 else 0
                patterns.append(QueryPattern(
                    pattern=pattern,
                    count=count,
                    hit_rate=hit_rate,
                    examples=stats["examples"]
                ))
        
        # 按频率排序
        patterns.sort(key=lambda p: p.count, reverse=True)
        
        return patterns
    
    def identify_knowledge_gaps(
        self,
        patterns: List[QueryPattern]
    ) -> List[KnowledgeGap]:
        """
        识别知识缺口
        
        Args:
            patterns: 查询模式列表
            
        Returns:
            List[KnowledgeGap]: 知识缺口列表
        """
        gaps = []
        
        for pattern in patterns:
            # 如果命中率低且频率高，说明存在知识缺口
            if pattern.hit_rate < 0.3 and pattern.count >= self.min_query_frequency:
                gap_id = f"gap_{self._hash_text(pattern.pattern)[:8]}"
                gap = KnowledgeGap(
                    gap_id=gap_id,
                    topic=pattern.pattern,
                    description=f"高频未命中查询模式: {pattern.pattern}",
                    frequency=pattern.count,
                    metadata={
                        "hit_rate": pattern.hit_rate,
                        "examples": pattern.examples
                    }
                )
                gaps.append(gap)
        
        return gaps
    
    async def fill_knowledge_gap(self, gap: KnowledgeGap) -> bool:
        """
        填补知识缺口
        
        Args:
            gap: 知识缺口
            
        Returns:
            bool: 是否成功
        """
        # 如果没有 memory_manager，无法填补
        if self.memory is None:
            return False
        
        # 记录知识缺口以便后续处理
        gap_record = {
            "gap_id": gap.gap_id,
            "topic": gap.topic,
            "description": gap.description,
            "frequency": gap.frequency,
            "timestamp": time.time(),
            "status": "identified"
        }
        
        # 尝试通过 memory_manager 存储缺口记录
        try:
            if hasattr(self.memory, 'store_metadata'):
                await self.memory.store_metadata("knowledge_gaps", gap.gap_id, gap_record)
            return True
        except Exception:
            return False
    
    async def merge_fragments(self) -> int:
        """
        合并碎片知识
        
        将相似的知识片段合并为完整的知识条目
        
        Returns:
            int: 合并的数量
        """
        if self.memory is None:
            return 0
        
        merged_count = 0
        
        # 获取可能需要合并的片段
        fragments = self._identify_mergeable_fragments()
        
        if not fragments:
            return 0
        
        # 按主题分组
        topic_groups = self._group_by_topic(fragments)
        
        for topic, group_fragments in topic_groups.items():
            if len(group_fragments) < 2:
                continue
            
            # 使用 LLM 合并（如果可用）
            if self._llm_client is not None:
                merged_content = await self._llm_merge_fragments(group_fragments)
            else:
                merged_content = self._rule_based_merge(group_fragments)
            
            if merged_content:
                # 存储合并后的知识
                success = await self._store_merged_knowledge(topic, merged_content, group_fragments)
                if success:
                    merged_count += 1
        
        return merged_count
    
    async def update_graph_connections(self) -> int:
        """
        更新图谱连接
        
        基于新固化的知识更新知识图谱中的关系
        
        Returns:
            int: 更新的连接数
        """
        if self.memory is None:
            return 0
        
        updated_count = 0
        
        # 获取最近固化的 QA 对
        recent_qas = self._get_recent_qa_pairs(limit=100)
        
        for qa in recent_qas:
            # 提取实体和关系
            entities = self._extract_entities(qa.answer)
            
            # 更新图谱连接
            for entity in entities:
                try:
                    if hasattr(self.memory, 'update_entity_connection'):
                        await self.memory.update_entity_connection(
                            entity=entity,
                            qa_id=qa.qa_id,
                            confidence=qa.confidence
                        )
                        updated_count += 1
                except Exception:
                    continue
        
        return updated_count
    
    def record_query(
        self,
        query: str,
        hit: bool,
        confidence: float = 0.0,
        answer: Optional[str] = None,
        evidence: Optional[List[str]] = None
    ) -> None:
        """
        记录查询（用于后续分析）
        
        Args:
            query: 查询文本
            hit: 是否命中
            confidence: 置信度
            answer: 答案（可选）
            evidence: 证据（可选）
        """
        log_entry = {
            "query": query,
            "hit": hit,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        self._query_log.append(log_entry)
        
        # 如果是高质量回答，加入待固化队列
        if hit and confidence >= self.quality_threshold and answer:
            qa = QAPair(
                qa_id=f"qa_{self._hash_text(query)[:8]}_{int(time.time())}",
                query=query,
                answer=answer,
                confidence=confidence,
                evidence=evidence or []
            )
            self._add_to_cache(qa)
        
        # 限制日志大小
        if len(self._query_log) > 10000:
            self._query_log = self._query_log[-5000:]
    
    async def store_qa_pair(
        self,
        query: str,
        answer: str,
        confidence: float,
        evidence: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        存储高质量 QA 对
        
        Args:
            query: 查询
            answer: 答案
            confidence: 置信度
            evidence: 证据
            metadata: 元数据
            
        Returns:
            Optional[str]: QA ID，失败返回 None
        """
        if confidence < self.quality_threshold:
            return None
        
        qa = QAPair(
            qa_id=f"qa_{self._hash_text(query)[:8]}_{int(time.time())}",
            query=query,
            answer=answer,
            confidence=confidence,
            evidence=evidence or [],
            metadata=metadata or {}
        )
        
        # 去重检查
        if self._is_duplicate(qa):
            return None
        
        # 存储
        success = await self._store_qa_pair(qa)
        return qa.qa_id if success else None
    
    # ============== 私有方法 ==============
    
    def _extract_pattern(self, query: str) -> str:
        """
        从查询中提取模式
        
        简单实现：提取关键词组合
        """
        import re
        
        # 移除标点和停用词
        stopwords = {'的', '了', '是', '在', '和', '与', '或', '吗', '呢', '啊',
                     'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a'}
        
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', query.lower())
        keywords = [w for w in words if len(w) >= 2 and w not in stopwords]
        
        # 取前3个关键词作为模式
        return ' '.join(keywords[:3]) if keywords else query[:20]
    
    def _hash_text(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _is_duplicate(self, qa: QAPair) -> bool:
        """
        检查 QA 对是否重复
        """
        query_hash = self._hash_text(qa.query.lower().strip())
        
        if query_hash in self._qa_cache:
            cached = self._qa_cache[query_hash]
            # 如果新的置信度更高，替换缓存
            if qa.confidence > cached.confidence:
                self._qa_cache[query_hash] = qa
                return False
            return True
        
        return False
    
    def _add_to_cache(self, qa: QAPair) -> None:
        """添加到缓存"""
        query_hash = self._hash_text(qa.query.lower().strip())
        
        # 检查是否已存在更高质量的版本
        if query_hash in self._qa_cache:
            if qa.confidence <= self._qa_cache[query_hash].confidence:
                return
        
        self._qa_cache[query_hash] = qa
        
        # 限制缓存大小
        if len(self._qa_cache) > 1000:
            # 移除置信度最低的条目
            sorted_items = sorted(
                self._qa_cache.items(),
                key=lambda x: x[1].confidence
            )
            for key, _ in sorted_items[:200]:
                del self._qa_cache[key]
    
    def _get_pending_qa_pairs(self) -> List[QAPair]:
        """获取待固化的 QA 对"""
        return list(self._qa_cache.values())
    
    def _get_recent_qa_pairs(self, limit: int = 100) -> List[QAPair]:
        """获取最近的 QA 对"""
        sorted_qas = sorted(
            self._qa_cache.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_qas[:limit]
    
    async def _store_qa_pair(self, qa: QAPair) -> bool:
        """存储 QA 对到持久化存储"""
        if self.memory is None:
            # 无持久化存储，仅保留在缓存中
            self._add_to_cache(qa)
            return True
        
        try:
            if hasattr(self.memory, 'store_qa'):
                await self.memory.store_qa(
                    qa_id=qa.qa_id,
                    query=qa.query,
                    answer=qa.answer,
                    confidence=qa.confidence,
                    evidence=qa.evidence,
                    metadata=qa.metadata
                )
            return True
        except Exception:
            return False
    
    def _identify_mergeable_fragments(self) -> List[Dict[str, Any]]:
        """识别可合并的知识片段"""
        # 从缓存中获取相似的 QA 对
        fragments = []
        
        for qa in self._qa_cache.values():
            fragments.append({
                "id": qa.qa_id,
                "topic": self._extract_pattern(qa.query),
                "content": qa.answer,
                "confidence": qa.confidence
            })
        
        return fragments
    
    def _group_by_topic(
        self,
        fragments: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按主题分组"""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for fragment in fragments:
            topic = fragment.get("topic", "unknown")
            if topic not in groups:
                groups[topic] = []
            groups[topic].append(fragment)
        
        return groups
    
    async def _llm_merge_fragments(
        self,
        fragments: List[Dict[str, Any]]
    ) -> Optional[str]:
        """使用 LLM 合并片段"""
        if not self._llm_client:
            return None
        
        fragments_text = "\n\n".join([
            f"[片段{i+1}]\n{f['content']}"
            for i, f in enumerate(fragments)
        ])
        
        prompt = self._merge_prompt.format(fragments=fragments_text)
        
        try:
            return self._llm_client.generate(prompt, temperature=0.3)
        except Exception:
            return self._rule_based_merge(fragments)
    
    def _rule_based_merge(
        self,
        fragments: List[Dict[str, Any]]
    ) -> str:
        """基于规则合并片段"""
        # 按置信度排序，优先保留高置信度内容
        sorted_fragments = sorted(
            fragments,
            key=lambda x: x.get("confidence", 0),
            reverse=True
        )
        
        # 简单合并：保留最高置信度的内容，附加其他内容的补充信息
        if not sorted_fragments:
            return ""
        
        main_content = sorted_fragments[0]["content"]
        
        if len(sorted_fragments) > 1:
            supplements = []
            for f in sorted_fragments[1:3]:  # 最多补充2个
                # 提取与主内容不重复的部分
                supplement = f["content"][:200]
                if supplement not in main_content:
                    supplements.append(supplement)
            
            if supplements:
                main_content += "\n\n补充信息：" + " ".join(supplements)
        
        return main_content
    
    async def _store_merged_knowledge(
        self,
        topic: str,
        content: str,
        source_fragments: List[Dict[str, Any]]
    ) -> bool:
        """存储合并后的知识"""
        if self.memory is None:
            return False
        
        try:
            if hasattr(self.memory, 'store_merged'):
                await self.memory.store_merged(
                    topic=topic,
                    content=content,
                    source_ids=[f["id"] for f in source_fragments],
                    timestamp=time.time()
                )
            return True
        except Exception:
            return False
    
    def _extract_entities(self, text: str) -> List[str]:
        """从文本中提取实体"""
        import re
        
        # 简单实现：提取名词短语
        # 中文：连续的汉字（2-10个字符）
        # 英文：首字母大写的词
        
        entities = []
        
        # 中文实体
        chinese_entities = re.findall(r'[\u4e00-\u9fff]{2,10}', text)
        entities.extend(chinese_entities[:10])
        
        # 英文实体（首字母大写）
        english_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(english_entities[:5])
        
        return list(set(entities))
