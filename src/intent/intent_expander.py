"""
NecoRAG 意图扩充器模块

通过 AI 学习和知识库对意图进行细分和扩充
支持：
1. 基于用户查询自动发现新意图
2. 从知识库中提取意图模式
3. 智能推荐意图层级结构
4. 意图细化和扩展
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
from datetime import datetime

from .hierarchical_models import (
    HierarchicalIntent,
    IntentHierarchyTree,
    IntentLevel,
)
from .intent_knowledge import IntentKnowledgeManager
from .classifier import IntentClassifier
from .models import IntentType


logger = logging.getLogger(__name__)


class IntentExpander:
    """
    意图扩充器
    
    通过机器学习和知识库进行意图的细分和扩充
    """
    
    def __init__(self, 
                 knowledge_manager: IntentKnowledgeManager,
                 classifier: IntentClassifier = None):
        """
        初始化意图扩充器
        
        Args:
            knowledge_manager: 意图知识管理器
            classifier: 意图分类器（可选）
        """
        self.knowledge_manager = knowledge_manager
        self.classifier = classifier or IntentClassifier()
        
        # 新发现的意图候选
        self.intent_candidates: List[dict] = []
        
        # 已处理的查询缓存
        self.processed_queries: List[dict] = []
    
    def analyze_query_patterns(self, queries: List[str]) -> Dict[str, List[str]]:
        """
        分析查询模式
        
        Args:
            queries: 查询列表
        
        Returns:
            {意图 ID: [相关查询列表]}
        """
        intent_queries = {}
        
        for query in queries:
            # 使用分类器识别意图
            result = self.classifier.classify(query)
            intent_key = result.primary_intent.value
            
            if intent_key not in intent_queries:
                intent_queries[intent_key] = []
            
            intent_queries[intent_key].append(query)
        
        return intent_queries
    
    def discover_new_intents(self, 
                            queries: List[str],
                            min_frequency: int = 3) -> List[dict]:
        """
        从查询中发现新的意图
        
        Args:
            queries: 用户查询列表
            min_frequency: 最小出现频率
        
        Returns:
            新意图候选列表
        """
        logger.info(f"开始从 {len(queries)} 条查询中发现新意图")
        
        # 1. 分析查询模式
        intent_queries = self.analyze_query_patterns(queries)
        
        # 2. 统计每个意图下的查询特征
        new_candidates = []
        
        for intent_key, query_list in intent_queries.items():
            if len(query_list) < min_frequency:
                continue
            
            # 提取共同特征
            common_keywords = self._extract_common_keywords(query_list)
            
            # 检查是否已有类似意图
            similar_intents = self._find_similar_intents(common_keywords)
            
            if not similar_intents:
                # 发现新的意图模式
                candidate = {
                    "base_intent": intent_key,
                    "keywords": common_keywords,
                    "examples": query_list[:5],  # 保存前 5 个示例
                    "frequency": len(query_list),
                    "confidence": self._calculate_confidence(query_list),
                    "suggested_level": self._suggest_level(len(query_list)),
                }
                
                new_candidates.append(candidate)
                self.intent_candidates.append(candidate)
        
        logger.info(f"发现 {len(new_candidates)} 个新意图候选")
        return new_candidates
    
    def expand_intent_hierarchy(self,
                               parent_intent_id: str,
                               queries: List[str],
                               expansion_strategy: str = "auto") -> List[str]:
        """
        扩展现有意图的子意图
        
        Args:
            parent_intent_id: 父意图 ID
            queries: 相关查询列表
            expansion_strategy: 扩展策略 (auto | manual | hybrid)
        
        Returns:
            新创建的子意图 ID 列表
        """
        tree = self.knowledge_manager.current_tree
        if not tree:
            raise ValueError("没有当前意图树")
        
        parent_intent = tree.get_intent(parent_intent_id)
        if not parent_intent:
            raise ValueError(f"父意图不存在：{parent_intent_id}")
        
        logger.info(f"开始为意图 '{parent_intent.name}' 扩展子意图")
        
        # 1. 分析查询，发现不同的主题簇
        clusters = self._cluster_queries(queries)
        
        # 2. 为每个簇创建子意图
        new_intent_ids = []
        
        for cluster_id, cluster_queries in clusters.items():
            if len(cluster_queries) < 2:
                continue
            
            # 提取簇特征
            keywords = self._extract_common_keywords(cluster_queries)
            representative_query = cluster_queries[0]
            
            # 生成子意图名称和描述
            child_name = self._generate_intent_name(keywords, representative_query)
            child_description = self._generate_intent_description(cluster_queries)
            
            # 确定子意图层级
            if parent_intent.level == IntentLevel.L1:
                child_level = IntentLevel.L2
            elif parent_intent.level == IntentLevel.L2:
                child_level = IntentLevel.L3
            else:
                logger.warning(f"无法为 L3 意图 '{parent_intent.name}' 创建子意图")
                continue
            
            # 创建子意图
            child_id = f"{parent_intent_id}_{child_level.value}_{len(new_intent_ids) + 1}"
            
            child_intent = HierarchicalIntent(
                intent_id=child_id,
                name=child_name,
                level=child_level,
                description=child_description,
                parent_id=parent_intent_id,
                keywords=keywords,
                examples=cluster_queries[:5],
            )
            
            # 添加到树中
            tree.add_intent(child_intent)
            new_intent_ids.append(child_id)
            
            logger.info(f"创建子意图：{child_name} ({child_id})")
        
        return new_intent_ids
    
    def refine_intent_details(self,
                             intent_id: str,
                             additional_examples: List[str],
                             auto_enhance: bool = True) -> bool:
        """
        细化意图的细节信息
        
        Args:
            intent_id: 意图 ID
            additional_examples: 额外示例
            auto_enhance: 是否自动增强
        
        Returns:
            是否成功
        """
        tree = self.knowledge_manager.current_tree
        if not tree:
            return False
        
        intent = tree.get_intent(intent_id)
        if not intent:
            return False
        
        logger.info(f"开始细化意图 '{intent.name}'")
        
        # 1. 添加示例
        for example in additional_examples:
            intent.add_example(example)
        
        # 2. 自动增强关键词
        if auto_enhance:
            all_text = " ".join(additional_examples)
            new_keywords = self._extract_keywords_from_text(all_text)
            
            for keyword in new_keywords:
                if keyword not in intent.keywords:
                    intent.add_keyword(keyword)
        
        # 3. 更新路由配置（如果有分类器）
        if self.classifier and intent.examples:
            intent.routing_config = self._infer_routing_config(intent.examples)
        
        return True
    
    def merge_similar_intents(self,
                             intent_ids: List[str],
                             merge_strategy: str = "combine") -> Optional[str]:
        """
        合并相似的意图
        
        Args:
            intent_ids: 要合并的意图 ID 列表
            merge_strategy: 合并策略 (combine | keep_best)
        
        Returns:
            合并后的意图 ID
        """
        tree = self.knowledge_manager.current_tree
        if not tree:
            return None
        
        intents_to_merge = [tree.get_intent(iid) for iid in intent_ids]
        intents_to_merge = [i for i in intents_to_merge if i is not None]
        
        if len(intents_to_merge) < 2:
            return None
        
        logger.info(f"开始合并 {len(intents_to_merge)} 个相似意图")
        
        # 检查是否有共同的父节点
        parent_ids = set(i.parent_id for i in intents_to_merge if i.parent_id)
        
        merged_intent = None
        
        if merge_strategy == "combine":
            # 合并所有特征
            merged_id = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            merged_name = " + ".join(i.name for i in intents_to_merge)
            merged_desc = "合并自：" + ", ".join(i.description for i in intents_to_merge)
            
            merged_keywords = []
            merged_examples = []
            
            for intent in intents_to_merge:
                merged_keywords.extend(intent.keywords)
                merged_examples.extend(intent.examples)
            
            # 去重
            merged_keywords = list(set(merged_keywords))
            merged_examples = list(set(merged_examples))[:10]
            
            merged_intent = HierarchicalIntent(
                intent_id=merged_id,
                name=merged_name,
                level=intents_to_merge[0].level,
                description=merged_desc,
                parent_id=list(parent_ids)[0] if len(parent_ids) == 1 else None,
                keywords=merged_keywords,
                examples=merged_examples,
            )
        
        elif merge_strategy == "keep_best":
            # 保留示例最多的意图
            best_intent = max(intents_to_merge, key=lambda x: len(x.examples))
            merged_intent = best_intent
            
            # 但添加其他意图的关键词和示例
            for intent in intents_to_merge:
                if intent != best_intent:
                    for kw in intent.keywords:
                        merged_intent.add_keyword(kw)
                    for ex in intent.examples[:3]:
                        merged_intent.add_example(ex)
        
        if merged_intent:
            tree.add_intent(merged_intent)
            
            # 移除原来的意图
            for intent in intents_to_merge:
                if intent.parent_id:
                    parent = tree.get_intent(intent.parent_id)
                    if parent:
                        parent.remove_child(intent.intent_id)
                
                del tree.all_intents[intent.intent_id]
            
            logger.info(f"合并完成，新意图 ID: {merged_intent.intent_id}")
            return merged_intent.intent_id
        
        return None
    
    def _extract_common_keywords(self, queries: List[str]) -> List[str]:
        """从查询组中提取共同关键词"""
        all_words = []
        
        for query in queries:
            words = self._tokenize_query(query)
            all_words.extend(words)
        
        # 过滤停用词
        stopwords = {
            '的', '是', '在', '了', '和', '与', '或', '有', '被', '把',
            '这', '那', '什么', '怎么', '如何', '为什么', '哪', '吗', '呢',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
        }
        
        filtered_words = [w for w in all_words if w.lower() not in stopwords and len(w) >= 2]
        
        # 统计词频
        counter = Counter(filtered_words)
        
        # 返回最常见的词
        return [word for word, _ in counter.most_common(10)]
    
    def _tokenize_query(self,query: str) -> List[str]:
        """简单分词"""
        import re
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', query)
        
        # 中文连续字符
        chinese_segments = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        
        return english_words + chinese_segments
    
    def _find_similar_intents(self, keywords: List[str]) -> List[HierarchicalIntent]:
        """查找相似的现有意图"""
        if not self.knowledge_manager.current_tree:
            return []
        
        results = self.knowledge_manager.search_similar_intents(keywords, top_k=3)
        return [intent for intent, score in results if score > 0.3]
    
    def _calculate_confidence(self, queries: List[str]) -> float:
        """计算置信度"""
        if not queries:
            return 0.0
        
        # 基于查询数量和一致性
        count_score = min(1.0, len(queries) / 10.0)
        
        # 检查查询的一致性（简单的重叠度）
        if len(queries) > 1:
            common_words = set(self._tokenize_query(queries[0]))
            for query in queries[1:]:
                common_words &= set(self._tokenize_query(query))
            
            consistency = len(common_words) / max(1, len(common_words) + 5)
        else:
            consistency = 0.5
        
        return (count_score + consistency) / 2
    
    def _suggest_level(self, frequency: int) -> IntentLevel:
        """根据频率建议层级"""
        if frequency >= 20:
            return IntentLevel.L2  # 高频，可能是 L2
        elif frequency >= 5:
            return IntentLevel.L3  # 中频，可能是 L3
        else:
            return IntentLevel.L3  # 低频，也是 L3
    
    def _cluster_queries(self, queries: List[str]) -> Dict[str, List[str]]:
        """简单聚类（基于关键词重叠）"""
        if not queries:
            return {}
        
        clusters = {"default": queries}
        return clusters
    
    def _generate_intent_name(self, keywords: List[str], representative_query: str) -> str:
        """生成意图名称"""
        if keywords:
            return keywords[0]  # 使用最常见的关键词
        return representative_query[:20]  # 或使用查询的前 20 个字符
    
    def _generate_intent_description(self, queries: List[str]) -> str:
        """生成意图描述"""
        sample = queries[0] if queries else "相关查询"
        return f"包含类似'{sample}'的查询"
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        return self._tokenize_query(text)[:10]
    
    def _infer_routing_config(self, examples: List[str]) -> dict:
        """从示例中推断路由配置"""
        # 这里可以根据示例的特征自动推断检索策略
        # 简化版本，返回默认配置
        return {
            "retrieval_mode": "hybrid",
            "top_k": 10,
        }


def create_intent_expander(storage_dir: str = None) -> IntentExpander:
    """
    创建意图扩充器
    
    Args:
        storage_dir: 存储目录
    
    Returns:
        IntentExpander: 扩充器实例
    """
    from .intent_knowledge import create_intent_knowledge_manager
    
    knowledge_manager = create_intent_knowledge_manager(storage_dir)
    return IntentExpander(knowledge_manager)
