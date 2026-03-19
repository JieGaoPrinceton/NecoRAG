"""
NecoRAG 领域知识库管理模块

支持导入和管理基础关键字、FAQ 文本，并提供知识扩充功能
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
import os
import re
from pathlib import Path

from .config import (
    DomainConfig, 
    KeywordLevel, 
    KeywordConfig,
    DomainConfigManager
)


@dataclass
class FAQItem:
    """FAQ 条目"""
    question: str
    answer: str
    keywords: List[str] = field(default_factory=list)
    category: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    view_count: int = 0
    helpful_count: int = 0
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "question": self.question,
            "answer": self.answer,
            "keywords": self.keywords,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "view_count": self.view_count,
            "helpful_count": self.helpful_count,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FAQItem":
        """从字典创建"""
        item = cls(
            question=data["question"],
            answer=data["answer"],
            keywords=data.get("keywords", []),
            category=data.get("category", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            view_count=data.get("view_count", 0),
            helpful_count=data.get("helpful_count", 0),
        )
        return item


@dataclass
class KnowledgeBase:
    """知识库数据结构"""
    domain_id: str
    name: str
    description: str = ""
    keywords: Dict[str, KeywordConfig] = field(default_factory=dict)
    faqs: Dict[str, FAQItem] = field(default_factory=dict)  # key: question
    expansion_history: List[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def add_keyword(self, keyword: str, level: KeywordLevel, 
                    weight: float, aliases: List[str] = None,
                    description: str = "") -> bool:
        """添加关键字"""
        if keyword.lower() in self.keywords:
            return False
        
        config = KeywordConfig(
            keyword=keyword,
            level=level,
            weight=weight,
            aliases=aliases or [],
            description=description
        )
        self.keywords[keyword.lower()] = config
        
        # 同时为别名建立索引
        for alias in config.aliases:
            if alias.lower() not in self.keywords:
                self.keywords[alias.lower()] = config
        
        return True
    
    def add_faq(self, question: str, answer: str, 
                keywords: List[str] = None, category: str = "") -> bool:
        """添加 FAQ"""
        if question.lower() in self.faqs:
            return False
        
        faq = FAQItem(
            question=question,
            answer=answer,
            keywords=keywords or [],
            category=category
        )
        self.faqs[question.lower()] = faq
        return True
    
    def get_faq(self, question: str) -> Optional[FAQItem]:
        """获取 FAQ"""
        return self.faqs.get(question.lower())
    
    def search_faqs(self, query: str, top_k: int = 5) -> List[Tuple[float, FAQItem]]:
        """搜索 FAQ"""
        results = []
        query_lower = query.lower()
        
        for faq in self.faqs.values():
            score = 0.0
            
            # 问题匹配
            if query_lower in faq.question.lower():
                score += 0.5
            
            # 答案匹配
            if query_lower in faq.answer.lower():
                score += 0.3
            
            # 关键字匹配
            matched_keywords = [kw for kw in faq.keywords if query_lower in kw.lower()]
            if matched_keywords:
                score += 0.2 * len(matched_keywords)
            
            if score > 0:
                results.append((score, faq))
        
        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]
    
    def extract_keywords_from_text(self, text: str) -> Set[str]:
        """从文本中提取可能的关键字"""
        keywords = set()
        
        # 1. 查找已有的关键字
        for kw in self.keywords.keys():
            if kw.lower() in text.lower():
                keywords.add(kw)
        
        # 2. 提取新词（简单的名词短语提取）
        # 匹配中文名词（2-4 个字）
        chinese_nouns = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        for noun in chinese_nouns:
            if noun not in keywords and len(noun) >= 2:
                keywords.add(noun)
        
        # 匹配英文术语（首字母大写的单词或缩写）
        english_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        abbreviations = re.findall(r'\b[A-Z]{2,}\b', text)
        
        for term in english_terms + abbreviations:
            if term.lower() not in keywords:
                keywords.add(term)
        
        return keywords
    
    def suggest_new_keywords(self, text_corpus: List[str], 
                            min_frequency: int = 3) -> List[Tuple[str, int]]:
        """
        从文本语料中建议新的关键字
        
        Args:
            text_corpus: 文本语料列表
            min_frequency: 最小出现频率
        
        Returns:
            [(keyword, frequency), ...] 按频率降序排列
        """
        word_freq = {}
        
        for text in text_corpus:
            extracted = self.extract_keywords_from_text(text)
            for word in extracted:
                word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1
        
        # 过滤掉已有的关键字
        existing = set(self.keywords.keys())
        suggestions = [
            (word, freq) for word, freq in word_freq.items()
            if word not in existing and freq >= min_frequency
        ]
        
        # 按频率排序
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions
    
    def record_expansion(self, operation: str, details: dict) -> None:
        """记录知识扩充历史"""
        self.expansion_history.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "domain_id": self.domain_id,
            "name": self.name,
            "description": self.description,
            "keywords": {
                k: {
                    "keyword": v.keyword,
                    "level": v.level.value,
                    "weight": v.weight,
                    "aliases": v.aliases,
                    "description": v.description
                }
                for k, v in self.keywords.items()
                if k == v.keyword.lower()
            },
            "faqs": {k: v.to_dict() for k, v in self.faqs.items()},
            "expansion_history": self.expansion_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeBase":
        """从字典创建"""
        kb = cls(
            domain_id=data["domain_id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )
        
        # 加载关键字
        for kw_data in data.get("keywords", {}).values():
            kb.add_keyword(
                keyword=kw_data["keyword"],
                level=KeywordLevel(kw_data["level"]),
                weight=kw_data["weight"],
                aliases=kw_data.get("aliases", []),
                description=kw_data.get("description", "")
            )
        
        # 加载 FAQ
        for faq_data in data.get("faqs", {}).values():
            faq = FAQItem.from_dict(faq_data)
            kb.faqs[faq.question.lower()] = faq
        
        # 加载历史
        kb.expansion_history = data.get("expansion_history", [])
        
        return kb


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, storage_dir: str = None):
        """
        初始化知识库管理器
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), "knowledge_bases"
        )
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def create_knowledge_base(self, domain_id: str, 
                             name: str, description: str = "") -> KnowledgeBase:
        """创建知识库"""
        kb = KnowledgeBase(
            domain_id=domain_id,
            name=name,
            description=description
        )
        self.knowledge_bases[domain_id] = kb
        return kb
    
    def get_knowledge_base(self, domain_id: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self.knowledge_bases.get(domain_id)
    
    def load_knowledge_base(self, domain_id: str) -> Optional[KnowledgeBase]:
        """从文件加载知识库"""
        filepath = os.path.join(self.storage_dir, f"{domain_id}.json")
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        kb = KnowledgeBase.from_dict(data)
        self.knowledge_bases[domain_id] = kb
        return kb
    
    def save_knowledge_base(self, domain_id: str) -> bool:
        """保存知识库到文件"""
        kb = self.knowledge_bases.get(domain_id)
        if not kb:
            return False
        
        filepath = os.path.join(self.storage_dir, f"{domain_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(kb.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    
    def import_keywords_from_file(self, domain_id: str, 
                                  filepath: str, format: str = "json") -> int:
        """
        从文件导入关键字
        
        Args:
            domain_id: 领域 ID
            filepath: 文件路径
            format: 文件格式 (json/csv/txt)
        
        Returns:
            成功导入的关键字数量
        """
        kb = self.get_knowledge_base(domain_id)
        if not kb:
            kb = self.load_knowledge_base(domain_id)
        
        if not kb:
            raise ValueError(f"知识库不存在：{domain_id}")
        
        count = 0
        
        if format == "json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for kw_data in data.get("keywords", []):
                success = kb.add_keyword(
                    keyword=kw_data.get("keyword", ""),
                    level=KeywordLevel(kw_data.get("level", "normal")),
                    weight=kw_data.get("weight", 1.0),
                    aliases=kw_data.get("aliases", []),
                    description=kw_data.get("description", "")
                )
                if success:
                    count += 1
        
        elif format == "txt":
            # 简单文本格式：每行一个关键字
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    keyword = line.strip()
                    if keyword:
                        success = kb.add_keyword(
                            keyword=keyword,
                            level=KeywordLevel.NORMAL,
                            weight=1.0
                        )
                        if success:
                            count += 1
        
        kb.record_expansion("import_keywords", {
            "filepath": filepath,
            "format": format,
            "count": count
        })
        
        return count
    
    def import_faqs_from_file(self, domain_id: str, 
                              filepath: str, format: str = "json") -> int:
        """
        从文件导入 FAQ
        
        Args:
            domain_id: 领域 ID
            filepath: 文件路径
            format: 文件格式 (json/csv/txt)
        
        Returns:
            成功导入的 FAQ 数量
        """
        kb = self.get_knowledge_base(domain_id)
        if not kb:
            kb = self.load_knowledge_base(domain_id)
        
        if not kb:
            raise ValueError(f"知识库不存在：{domain_id}")
        
        count = 0
        
        if format == "json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for faq_data in data.get("faqs", []):
                success = kb.add_faq(
                    question=faq_data.get("question", ""),
                    answer=faq_data.get("answer", ""),
                    keywords=faq_data.get("keywords", []),
                    category=faq_data.get("category", "")
                )
                if success:
                    count += 1
        
        elif format == "csv":
            import csv
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    success = kb.add_faq(
                        question=row.get("question", ""),
                        answer=row.get("answer", ""),
                        keywords=row.get("keywords", "").split(";"),
                        category=row.get("category", "")
                    )
                    if success:
                        count += 1
        
        kb.record_expansion("import_faqs", {
            "filepath": filepath,
            "format": format,
            "count": count
        })
        
        return count
    
    def expand_from_corpus(self, domain_id: str, 
                          text_corpus: List[str], 
                          min_frequency: int = 3,
                          auto_add: bool = False) -> List[Tuple[str, int]]:
        """
        从语料库扩充知识库
        
        Args:
            domain_id: 领域 ID
            text_corpus: 文本语料列表
            min_frequency: 最小出现频率
            auto_add: 是否自动添加到知识库
        
        Returns:
            建议的新关键字列表
        """
        kb = self.get_knowledge_base(domain_id)
        if not kb:
            kb = self.load_knowledge_base(domain_id)
        
        if not kb:
            raise ValueError(f"知识库不存在：{domain_id}")
        
        suggestions = kb.suggest_new_keywords(text_corpus, min_frequency)
        
        if auto_add and suggestions:
            added_count = 0
            for keyword, freq in suggestions:
                # 根据频率自动判断等级
                if freq >= min_frequency * 3:
                    level = KeywordLevel.IMPORTANT
                    weight = 1.3
                elif freq >= min_frequency * 2:
                    level = KeywordLevel.NORMAL
                    weight = 1.0
                else:
                    level = KeywordLevel.PERIPHERAL
                    weight = 0.7
                
                success = kb.add_keyword(
                    keyword=keyword,
                    level=level,
                    weight=weight,
                    description=f"从语料库自动提取 (出现{freq}次)"
                )
                if success:
                    added_count += 1
            
            kb.record_expansion("auto_expand_from_corpus", {
                "suggestions_count": len(suggestions),
                "added_count": added_count,
                "min_frequency": min_frequency
            })
        
        return suggestions
    
    def list_all_domains(self) -> List[str]:
        """列出所有知识库领域"""
        return list(self.knowledge_bases.keys())
    
    def sync_to_domain_config(self, domain_id: str) -> bool:
        """
        将知识库同步到领域配置
        
        Args:
            domain_id: 领域 ID
        
        Returns:
            是否成功
        """
        kb = self.get_knowledge_base(domain_id)
        if not kb:
            return False
        
        # 这里可以集成到现有的 DomainConfigManager
        # 暂不实现，留待后续扩展
        
        return True


def create_example_knowledge_base() -> KnowledgeBase:
    """创建示例知识库（AI/机器学习领域）"""
    kb = KnowledgeBase(
        domain_id="ai_ml",
        name="人工智能与机器学习知识库",
        description="涵盖 AI/ML 领域的基础知识和常见问题"
    )
    
    # 添加基础关键字
    core_keywords = [
        ("深度学习", ["deep learning", "DL"], "神经网络多层学习方法"),
        ("机器学习", ["machine learning", "ML"], "从数据中学习的算法"),
        ("神经网络", ["neural network", "NN"], "模拟生物神经网络的计算模型"),
        ("大语言模型", ["LLM", "large language model"], "大规模预训练语言模型"),
        ("RAG", ["检索增强生成", "retrieval augmented generation"], "结合检索的生成方法"),
    ]
    for kw, aliases, desc in core_keywords:
        kb.add_keyword(kw, KeywordLevel.CORE, 1.8, aliases, desc)
    
    # 添加基础 FAQ
    faqs = [
        (
            "什么是 RAG？",
            "RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合信息检索和文本生成的技术。它先从知识库中检索相关信息，然后基于这些信息生成回答，可以提高生成的准确性和可解释性。",
            ["RAG", "检索增强生成", "信息检索"],
            "基础概念"
        ),
        (
            "如何微调大语言模型？",
            "微调大语言模型通常包括以下步骤：1) 准备特定任务的训练数据；2) 选择合适的预训练模型；3) 设置学习率和训练轮数；4) 在训练数据上进行微调；5) 验证和测试模型性能。常用工具包括 Hugging Face Transformers、PEFT 等。",
            ["微调", "大语言模型", "训练"],
            "实践指南"
        ),
        (
            "向量数据库的作用是什么？",
            "向量数据库专门用于存储和检索高维向量数据。在 RAG 系统中，它将文档 embedding 后的向量存储起来，支持快速的相似度搜索，找到与查询最相关的文档片段。常见的向量数据库有 Milvus、Pinecone、Weaviate 等。",
            ["向量数据库", "embedding", "相似度搜索"],
            "技术组件"
        ),
    ]
    for question, answer, keywords, category in faqs:
        kb.add_faq(question, answer, keywords, category)
    
    return kb
