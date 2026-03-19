#!/usr/bin/env python3
"""
NecoRAG 知识库管理模块简单测试
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.domain.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseManager,
    FAQItem,
    create_example_knowledge_base,
)
from src.domain.config import KeywordLevel


def test_basic():
    """基础功能测试"""
    print("=" * 60)
    print("基础功能测试")
    print("=" * 60)
    
    # 测试创建知识库
    kb = KnowledgeBase(domain_id="test", name="测试知识库")
    assert kb.domain_id == "test"
    assert kb.name == "测试知识库"
    print("✅ 知识库创建成功")
    
    # 测试添加关键字
    success = kb.add_keyword(
        keyword="机器学习",
        level=KeywordLevel.CORE,
        weight=1.8,
        aliases=["ML"],
        description="从数据中学习"
    )
    assert success is True
    assert "机器学习" in kb.keywords
    print("✅ 关键字添加成功")
    
    # 测试添加 FAQ
    success = kb.add_faq(
        question="什么是 AI？",
        answer="人工智能",
        keywords=["AI", "人工智能"],
        category="基础"
    )
    assert success is True
    assert len(kb.faqs) == 1
    print("✅ FAQ 添加成功")
    
    # 测试搜索 FAQ
    results = kb.search_faqs("人工智能", top_k=5)
    assert len(results) > 0
    print(f"✅ FAQ 搜索成功，找到 {len(results)} 条结果")
    
    # 测试提取关键字
    text = "机器学习是人工智能的核心技术。深度学习很重要。"
    keywords = kb.extract_keywords_from_text(text)
    assert "机器学习" in keywords
    print(f"✅ 关键字提取成功，提取到 {len(keywords)} 个关键字")
    
    print()


def test_manager():
    """管理器功能测试"""
    print("=" * 60)
    print("管理器功能测试")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    manager = KnowledgeBaseManager(storage_dir=temp_dir)
    
    # 测试创建知识库
    kb = manager.create_knowledge_base(
        domain_id="test_domain",
        name="测试知识库",
        description="用于测试"
    )
    assert kb.domain_id == "test_domain"
    print("✅ 管理器创建知识库成功")
    
    # 添加数据
    kb.add_keyword("测试关键字", KeywordLevel.NORMAL, 1.0)
    kb.add_faq("测试问题", "测试回答")
    
    # 测试保存
    success = manager.save_knowledge_base("test_domain")
    assert success is True
    print("✅ 知识库保存成功")
    
    # 清空内存并重新加载
    manager.knowledge_bases.clear()
    loaded_kb = manager.load_knowledge_base("test_domain")
    
    assert loaded_kb is not None
    assert loaded_kb.name == "测试知识库"
    assert len(loaded_kb.keywords) == 1
    assert len(loaded_kb.faqs) == 1
    print("✅ 知识库加载成功")
    
    # 清理
    shutil.rmtree(temp_dir)
    print()


def test_example():
    """示例知识库测试"""
    print("=" * 60)
    print("示例知识库测试")
    print("=" * 60)
    
    kb = create_example_knowledge_base()
    
    assert kb.domain_id == "ai_ml"
    assert len(kb.keywords) > 0
    assert len(kb.faqs) > 0
    print(f"✅ 示例知识库创建成功")
    print(f"   - 关键字数：{len(kb.keywords)}")
    print(f"   - FAQ 数：{len(kb.faqs)}")
    
    # 检查是否有关键字
    has_dl = any("深度学习" in kw for kw in kb.keywords.keys())
    assert has_dl
    print("✅ 包含预期关键字（深度学习）")
    
    # 检查是否有 FAQ
    has_rag_faq = any("RAG" in faq.question for faq in kb.faqs.values())
    assert has_rag_faq
    print("✅ 包含预期 FAQ（RAG 相关）")
    
    print()


def test_corpus_expansion():
    """语料库扩充测试"""
    print("=" * 60)
    print("语料库扩充测试")
    print("=" * 60)
    
    kb = KnowledgeBase(domain_id="test", name="Test")
    kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)
    
    corpus = [
        "机器学习很重要",
        "深度学习是机器学习的分支",
        "神经网络用于深度学习",
        "强化学习也是机器学习",
        "监督学习需要标注数据",
    ]
    
    # 测试建议新关键字
    suggestions = kb.suggest_new_keywords(corpus, min_frequency=2)
    print(f"✅ 建议新关键字：{len(suggestions)} 个")
    
    if suggestions:
        print(f"   建议列表：{[word for word, _ in suggestions[:5]]}")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("NecoRAG 知识库管理模块测试")
    print("=" * 60 + "\n")
    
    try:
        test_basic()
        test_manager()
        test_example()
        test_corpus_expansion()
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
