#!/usr/bin/env python3
"""
NecoRAG 知识库管理模块使用示例

演示如何导入和管理关键字、FAQ 数据
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.knowledge_base import (
    KnowledgeBaseManager,
    create_example_knowledge_base,
    FAQItem,
)
from src.domain.config import KeywordLevel


def example_basic_usage():
    """基础使用示例"""
    print("=" * 60)
    print("基础使用示例")
    print("=" * 60)
    
    # 创建知识库管理器
    manager = KnowledgeBaseManager()
    
    # 创建示例知识库
    kb = create_example_knowledge_base()
    manager.knowledge_bases["ai_ml"] = kb
    
    print(f"✅ 已创建知识库：{kb.name}")
    print(f"   领域 ID: {kb.domain_id}")
    print(f"   描述：{kb.description}")
    print(f"   关键字数量：{len(kb.keywords)}")
    print(f"   FAQ 数量：{len(kb.faqs)}")
    print()


def example_add_keywords():
    """添加关键字示例"""
    print("=" * 60)
    print("添加关键字示例")
    print("=" * 60)
    
    manager = KnowledgeBaseManager()
    kb = manager.create_knowledge_base(
        domain_id="rag_system",
        name="RAG 系统知识库",
        description="检索增强生成系统相关知识"
    )
    
    # 添加核心关键字
    kb.add_keyword(
        keyword="向量检索",
        level=KeywordLevel.CORE,
        weight=1.8,
        aliases=["vector search", "相似度搜索"],
        description="基于向量相似度的信息检索方法"
    )
    
    # 添加重要关键字
    kb.add_keyword(
        keyword="分块策略",
        level=KeywordLevel.IMPORTANT,
        weight=1.3,
        aliases=["chunking strategy", "文本分块"],
        description="将文档切分为合适大小的策略"
    )
    
    # 添加普通关键字
    kb.add_keyword(
        keyword="召回率",
        level=KeywordLevel.NORMAL,
        weight=1.0,
        aliases=["recall"],
        description="检索系统性能指标"
    )
    
    print(f"✅ 已添加 {len(kb.keywords)} 个关键字")
    
    # 查询关键字权重
    test_words = ["向量检索", "vector search", "分块策略", "召回率"]
    for word in test_words:
        weight = kb.keywords.get(word.lower(), {}).weight if word.lower() in kb.keywords else 1.0
        print(f"   '{word}' 权重：{weight}")
    print()


def example_add_faqs():
    """添加 FAQ 示例"""
    print("=" * 60)
    print("添加 FAQ 示例")
    print("=" * 60)
    
    manager = KnowledgeBaseManager()
    kb = manager.create_knowledge_base(
        domain_id="faq_demo",
        name="FAQ 演示知识库"
    )
    
    # 添加 FAQ
    kb.add_faq(
        question="如何提高 RAG 系统的检索质量？",
        answer="提高 RAG 检索质量的方法包括：1) 优化文本分块策略；2) 使用更好的 embedding 模型；3) 添加重排序步骤；4) 使用混合检索（关键词 + 向量）；5) 调整检索参数如 top_k。",
        keywords=["RAG", "检索质量", "优化"],
        category="性能优化"
    )
    
    kb.add_faq(
        question="什么是 HyDE 技术？",
        answer="HyDE(Hypothetical Document Embeddings) 是一种检索增强技术。它先生成一个假设性的文档作为查询，然后将这个假设文档向量化进行检索，可以提高检索的相关性。",
        keywords=["HyDE", "检索增强", "embedding"],
        category="技术概念"
    )
    
    print(f"✅ 已添加 {len(kb.faqs)} 个 FAQ")
    
    # 搜索 FAQ
    query = "检索质量"
    results = kb.search_faqs(query, top_k=2)
    print(f"\n🔍 搜索 '{query}' 的结果:")
    for score, faq in results:
        print(f"   匹配度：{score:.2f}")
        print(f"   Q: {faq.question}")
        print(f"   A: {faq.answer[:50]}...")
        print()


def example_import_from_file():
    """从文件导入示例"""
    print("=" * 60)
    print("从文件导入示例")
    print("=" * 60)
    
    manager = KnowledgeBaseManager()
    kb = manager.create_knowledge_base(
        domain_id="import_demo",
        name="导入演示知识库"
    )
    
    # 创建示例 JSON 文件
    import json
    temp_file = Path("/tmp/test_keywords.json")
    test_data = {
        "keywords": [
            {
                "keyword": "知识图谱",
                "level": "important",
                "weight": 1.3,
                "aliases": ["knowledge graph", "KG"],
                "description": "结构化知识表示"
            },
            {
                "keyword": "提示工程",
                "level": "normal",
                "weight": 1.0,
                "aliases": ["prompt engineering"],
                "description": "优化提示词的技术"
            }
        ]
    }
    
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 创建测试文件：{temp_file}")
    
    # 从文件导入
    count = manager.import_keywords_from_file(
        domain_id="import_demo",
        filepath=str(temp_file),
        format="json"
    )
    
    print(f"✅ 成功导入 {count} 个关键字")
    
    # 清理临时文件
    temp_file.unlink()
    print()


def example_corpus_expansion():
    """语料库自动扩充示例"""
    print("=" * 60)
    print("语料库自动扩充示例")
    print("=" * 60)
    
    manager = KnowledgeBaseManager()
    kb = manager.create_knowledge_base(
        domain_id="expansion_demo",
        name="语料扩充演示"
    )
    
    # 初始关键字
    kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)
    kb.add_keyword("深度学习", KeywordLevel.CORE, 1.8)
    
    # 模拟语料库
    corpus = [
        "机器学习是人工智能的核心技术之一",
        "深度学习在图像识别中应用广泛",
        "强化学习是机器学习的另一个分支",
        "神经网络是深度学习的基础",
        "监督学习需要标注数据进行训练",
        "无监督学习可以发现数据中的模式",
        "迁移学习可以加速模型训练",
        "联邦学习保护数据隐私",
    ]
    
    print(f"📚 语料库大小：{len(corpus)} 条")
    print(f"📊 初始关键字数：{len(kb.keywords)}")
    
    # 建议新关键字
    suggestions = kb.suggest_new_keywords(corpus, min_frequency=2)
    
    print(f"\n💡 建议的新关键字:")
    for keyword, freq in suggestions[:5]:
        print(f"   {keyword}: 出现 {freq} 次")
    
    # 自动扩充
    added_suggestions = manager.expand_from_corpus(
        domain_id="expansion_demo",
        text_corpus=corpus,
        min_frequency=2,
        auto_add=True
    )
    
    print(f"\n✅ 自动添加了 {len(added_suggestions)} 个新关键字")
    print(f"📊 当前关键字数：{len(kb.keywords)}")
    print()


def example_save_and_load():
    """保存和加载示例"""
    print("=" * 60)
    print("保存和加载示例")
    print("=" * 60)
    
    manager = KnowledgeBaseManager(storage_dir="/tmp/necorag_kb_test")
    
    # 创建并填充知识库
    kb = manager.create_knowledge_base(
        domain_id="test_persistence",
        name="持久化测试知识库"
    )
    
    kb.add_keyword("测试关键字", KeywordLevel.NORMAL, 1.0)
    kb.add_faq("测试问题", "测试回答", ["测试"])
    
    # 保存
    manager.save_knowledge_base("test_persistence")
    print("💾 已保存知识库")
    
    # 重新加载
    manager.knowledge_bases.clear()  # 清空内存
    loaded_kb = manager.load_knowledge_base("test_persistence")
    
    if loaded_kb:
        print("✅ 成功加载知识库")
        print(f"   名称：{loaded_kb.name}")
        print(f"   关键字数：{len(loaded_kb.keywords)}")
        print(f"   FAQ 数：{len(loaded_kb.faqs)}")
    
    # 清理测试文件
    import shutil
    if Path(manager.storage_dir).exists():
        shutil.rmtree(manager.storage_dir)
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("NecoRAG 知识库管理模块示例")
    print("=" * 60 + "\n")
    
    try:
        example_basic_usage()
        example_add_keywords()
        example_add_faqs()
        example_import_from_file()
        example_corpus_expansion()
        example_save_and_load()
        
        print("=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
