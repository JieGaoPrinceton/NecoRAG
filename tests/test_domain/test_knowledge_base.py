#!/usr/bin/env python3
"""
NecoRAG 知识库管理模块测试
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from src.domain.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseManager,
    FAQItem,
    create_example_knowledge_base,
)
from src.domain.config import KeywordLevel


class TestFAQItem:
    """测试 FAQItem 类"""
    
    def test_create_faq(self):
        """测试创建 FAQ"""
        faq = FAQItem(
            question="什么是 RAG？",
            answer="RAG 是检索增强生成",
            keywords=["RAG", "检索"],
            category="基础概念"
        )
        
        assert faq.question == "什么是 RAG？"
        assert faq.answer == "RAG 是检索增强生成"
        assert len(faq.keywords) == 2
        assert faq.category == "基础概念"
        assert isinstance(faq.created_at, datetime)
    
    def test_faq_to_dict(self):
        """测试 FAQ 转换为字典"""
        faq = FAQItem(
            question="测试问题",
            answer="测试回答"
        )
        
        data = faq.to_dict()
        assert data["question"] == "测试问题"
        assert data["answer"] == "测试回答"
        assert "created_at" in data
    
    def test_faq_from_dict(self):
        """测试从字典创建 FAQ"""
        data = {
            "question": "测试问题",
            "answer": "测试回答",
            "keywords": ["测试"],
            "category": "测试分类",
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "view_count": 0,
            "helpful_count": 0,
        }
        
        faq = FAQItem.from_dict(data)
        assert faq.question == "测试问题"
        assert faq.answer == "测试回答"
        assert len(faq.keywords) == 1


class TestKnowledgeBase:
    """测试 KnowledgeBase 类"""
    
    def test_create_knowledge_base(self):
        """测试创建知识库"""
        kb = KnowledgeBase(
            domain_id="test_domain",
            name="测试知识库",
            description="用于测试"
        )
        
        assert kb.domain_id == "test_domain"
        assert kb.name == "测试知识库"
        assert len(kb.keywords) == 0
        assert len(kb.faqs) == 0
    
    def test_add_keyword(self):
        """测试添加关键字"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        
        success = kb.add_keyword(
            keyword="机器学习",
            level=KeywordLevel.CORE,
            weight=1.8,
            aliases=["ML"],
            description="从数据中学习"
        )
        
        assert success is True
        assert "机器学习" in kb.keywords
        assert "ml" in kb.keywords  # 别名也应该被索引
        
        # 重复添加应该失败
        success2 = kb.add_keyword(
            keyword="机器学习",
            level=KeywordLevel.NORMAL,
            weight=1.0
        )
        assert success2 is False
    
    def test_add_faq(self):
        """测试添加 FAQ"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        
        success = kb.add_faq(
            question="什么是 AI？",
            answer="人工智能",
            keywords=["AI", "人工智能"],
            category="基础"
        )
        
        assert success is True
        assert "什么是 ai？" in kb.faqs
        
        # 重复添加应该失败
        success2 = kb.add_faq(
            question="什么是 AI？",
            answer="另一个答案"
        )
        assert success2 is False
    
    def test_search_faqs(self):
        """测试搜索 FAQ"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        
        kb.add_faq("如何提高检索质量？", "优化分块策略", ["检索", "质量"])
        kb.add_faq("什么是 RAG？", "检索增强生成", ["RAG", "检索"])
        kb.add_faq("深度学习是什么？", "神经网络多层学习", ["深度学习"])
        
        results = kb.search_faqs("检索", top_k=2)
        
        assert len(results) >= 1
        # 第一个结果应该包含"检索"关键字
        scores = [score for score, _ in results]
        assert scores[0] >= scores[-1] if len(scores) > 1 else True
    
    def test_extract_keywords_from_text(self):
        """测试从文本提取关键字"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)
        
        text = "机器学习是人工智能的核心技术。深度学习很重要。"
        keywords = kb.extract_keywords_from_text(text)
        
        assert "机器学习" in keywords
        # 应该也能提取一些新词
        assert len(keywords) >= 1
    
    def test_suggest_new_keywords(self):
        """测试建议新关键字"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)
        
        corpus = [
            "机器学习很重要",
            "深度学习是机器学习的分支",
            "神经网络用于深度学习",
            "强化学习也是机器学习",
        ]
        
        suggestions = kb.suggest_new_keywords(corpus, min_frequency=2)
        
        # 应该建议"深度学习"（出现 2 次）
        suggestion_words = [word for word, _ in suggestions]
        assert "深度学习" in suggestion_words or "深度" in suggestion_words
    
    def test_knowledge_base_to_dict(self):
        """测试知识库转换为字典"""
        kb = KnowledgeBase(domain_id="test", name="Test")
        kb.add_keyword("测试", KeywordLevel.NORMAL, 1.0)
        kb.add_faq("问题", "回答")
        
        data = kb.to_dict()
        
        assert data["domain_id"] == "test"
        assert data["name"] == "Test"
        assert "keywords" in data
        assert "faqs" in data


class TestKnowledgeBaseManager:
    """测试 KnowledgeBaseManager 类"""
    
    @pytest.fixture
    def temp_manager(self):
        """创建临时目录的管理器"""
        temp_dir = tempfile.mkdtemp()
        manager = KnowledgeBaseManager(storage_dir=temp_dir)
        yield manager
        shutil.rmtree(temp_dir)
    
    def test_create_knowledge_base(self, temp_manager):
        """测试创建知识库"""
        kb = temp_manager.create_knowledge_base(
            domain_id="test",
            name="测试",
            description="描述"
        )
        
        assert kb.domain_id == "test"
        assert temp_manager.get_knowledge_base("test") == kb
    
    def test_save_and_load(self, temp_manager):
        """测试保存和加载"""
        # 创建并填充知识库
        kb = temp_manager.create_knowledge_base(
            domain_id="test",
            name="测试知识库"
        )
        kb.add_keyword("关键字", KeywordLevel.NORMAL, 1.0)
        kb.add_faq("问题", "回答")
        
        # 保存
        success = temp_manager.save_knowledge_base("test")
        assert success is True
        
        # 清空内存
        temp_manager.knowledge_bases.clear()
        
        # 加载
        loaded_kb = temp_manager.load_knowledge_base("test")
        
        assert loaded_kb is not None
        assert loaded_kb.name == "测试知识库"
        assert len(loaded_kb.keywords) == 1
        assert len(loaded_kb.faqs) == 1
    
    def test_import_keywords_from_json(self, temp_manager):
        """测试从 JSON 导入关键字"""
        import json
        
        # 创建测试文件
        temp_file = Path(temp_manager.storage_dir) / "test_keywords.json"
        test_data = {
            "keywords": [
                {
                    "keyword": "测试关键字 1",
                    "level": "normal",
                    "weight": 1.0,
                    "aliases": [],
                    "description": "测试"
                },
                {
                    "keyword": "测试关键字 2",
                    "level": "important",
                    "weight": 1.3,
                    "aliases": ["alias"],
                    "description": "测试"
                }
            ]
        }
        
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 创建知识库
        temp_manager.create_knowledge_base(domain_id="test", name="Test")
        
        # 导入
        count = temp_manager.import_keywords_from_file(
            domain_id="test",
            filepath=str(temp_file),
            format="json"
        )
        
        assert count == 2
        
        kb = temp_manager.get_knowledge_base("test")
        assert "测试关键字 1" in kb.keywords
        assert "测试关键字 2" in kb.keywords
    
    def test_list_domains(self, temp_manager):
        """测试列出所有领域"""
        temp_manager.create_knowledge_base("domain1", "领域 1")
        temp_manager.create_knowledge_base("domain2", "领域 2")
        
        domains = temp_manager.list_all_domains()
        
        assert len(domains) == 2
        assert "domain1" in domains
        assert "domain2" in domains


class TestExampleKnowledgeBase:
    """测试示例知识库"""
    
    def test_create_example(self):
        """测试创建示例知识库"""
        kb = create_example_knowledge_base()
        
        assert kb.domain_id == "ai_ml"
        assert len(kb.keywords) > 0
        assert len(kb.faqs) > 0
        
        # 检查是否有关键字
        assert any("深度学习" in kw for kw in kb.keywords.keys())
        
        # 检查是否有 FAQ
        assert any("RAG" in faq.question for faq in kb.faqs.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
