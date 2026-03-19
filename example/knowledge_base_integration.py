#!/usr/bin/env python3
"""
NecoRAG 知识库管理模块 - 实际应用集成示例

演示如何在真实的 RAG 系统中使用知识库管理模块
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.domain.knowledge_base import KnowledgeBaseManager, create_example_knowledge_base
from src.domain.config import KeywordLevel, DomainConfigManager
from src.domain.weight_calculator import DocumentMetadata, CompositeWeightCalculator
from datetime import datetime


def example_1_initialize_knowledge():
    """示例 1: 初始化领域知识库"""
    print("=" * 60)
    print("示例 1: 初始化领域知识库")
    print("=" * 60)
    
    # 创建知识库管理器
    kb_manager = KnowledgeBaseManager()
    
    # 方式 1: 使用预定义的示例知识库
    ai_kb = create_example_knowledge_base()
    kb_manager.knowledge_bases["ai_ml"] = ai_kb
    
    print(f"✅ 已加载 AI/ML 领域知识库")
    print(f"   关键字：{len(ai_kb.keywords)} 个")
    print(f"   FAQ: {len(ai_kb.faqs)} 条")
    
    # 方式 2: 创建自定义知识库
    custom_kb = kb_manager.create_knowledge_base(
        domain_id="custom_domain",
        name="自定义领域知识库",
        description="根据业务需求定制的知识库"
    )
    
    # 添加业务相关的关键字
    custom_kb.add_keyword(
        keyword="业务术语 A",
        level=KeywordLevel.CORE,
        weight=1.8,
        description="核心业务概念"
    )
    
    custom_kb.add_keyword(
        keyword="技术栈 B",
        level=KeywordLevel.IMPORTANT,
        weight=1.3,
        aliases=["Tech B"],
        description="关键技术"
    )
    
    # 添加业务 FAQ
    custom_kb.add_faq(
        question="如何处理业务场景 X？",
        answer="针对业务场景 X，建议采用以下步骤：1) 需求分析；2) 方案设计；3) 实施落地。",
        keywords=["业务场景", "实施方法"],
        category="业务流程"
    )
    
    print(f"✅ 已创建自定义知识库")
    print(f"   关键字：{len(custom_kb.keywords)} 个")
    print(f"   FAQ: {len(custom_kb.faqs)} 条")
    print()


def example_2_query_enhancement():
    """示例 2: 使用知识库增强查询理解"""
    print("=" * 60)
    print("示例 2: 使用知识库增强查询理解")
    print("=" * 60)
    
    kb_manager = KnowledgeBaseManager()
    kb = create_example_knowledge_base()
    kb_manager.knowledge_bases["ai_ml"] = kb
    
    # 模拟用户查询
    user_query = "如何提高 RAG 系统的检索效果？"
    
    print(f"用户查询：{user_query}")
    print()
    
    # 1. 从知识库中搜索相关 FAQ
    faq_results = kb.search_faqs(user_query, top_k=3)
    
    if faq_results:
        print(f"📚 找到 {len(faq_results)} 条相关 FAQ:")
        for score, faq in faq_results:
            print(f"   匹配度：{score:.2f}")
            print(f"   Q: {faq.question}")
            print(f"   A: {faq.answer[:50]}...")
            print()
    
    # 2. 提取查询中的关键字
    query_keywords = kb.extract_keywords_from_text(user_query)
    print(f"🔑 查询中的关键字：{query_keywords}")
    
    # 3. 计算查询的领域相关性
    domain_relevance = 0.0
    for keyword in query_keywords:
        if keyword.lower() in kb.keywords:
            weight = kb.keywords[keyword.lower()].weight
            domain_relevance += weight
    
    print(f"📊 查询领域相关性评分：{domain_relevance:.2f}")
    print()


def example_3_document_weighting():
    """示例 3: 在文档检索中使用知识库权重"""
    print("=" * 60)
    print("示例 3: 在文档检索中使用知识库权重")
    print("=" * 60)
    
    from src.domain import DomainConfig, DomainConfigManager
    from src.domain.weight_calculator import DocumentMetadata, WeightCalculatorFactory
    
    # 创建领域配置
    domain_manager = DomainConfigManager()
    domain_config = domain_manager.create_domain(
        domain_name="AI 领域",
        domain_id="ai_domain"
    )
    
    # 创建知识库并添加关键字
    kb_manager = KnowledgeBaseManager()
    kb = kb_manager.create_knowledge_base(
        domain_id="ai_domain",
        name="AI 知识库"
    )
    
    kb.add_keyword("机器学习", KeywordLevel.CORE, 1.8)
    kb.add_keyword("深度学习", KeywordLevel.CORE, 1.8)
    kb.add_keyword("神经网络", KeywordLevel.IMPORTANT, 1.3)
    
    # 创建权重计算器
    calculator_factory = WeightCalculatorFactory(domain_manager)
    calculator = calculator_factory.create_calculator(domain_config)
    
    print("📄 文档 1: 关于机器学习的文章")
    doc1 = DocumentMetadata(
        doc_id="doc1",
        content="本文介绍机器学习的基本概念和算法，包括监督学习和无监督学习。",
        created_at=datetime.now(),
        tags=["机器学习", "算法"]
    )
    
    print("📄 文档 2: 关于烹饪技巧的文章")
    doc2 = DocumentMetadata(
        doc_id="doc2",
        content="本文介绍中式烹饪的技巧和方法，包括炒菜、蒸菜等。",
        created_at=datetime.now(),
        tags=["烹饪", "美食"]
    )
    
    # 假设有基础相似度分数
    base_scores = [
        (0.85, doc1),  # 机器学习文档，基础分高
        (0.75, doc2),  # 烹饪文档，基础分较低
    ]
    
    print("\n🔢 加权计算结果:")
    for base_score, doc in base_scores:
        weighted_result = calculator.calculate_weight(
            base_score=base_score,
            doc_metadata=doc,
            query="机器学习是什么"
        )
        
        print(f"\n{doc.doc_id}:")
        print(f"   基础分数：{base_score:.3f}")
        print(f"   最终分数：{weighted_result.final_score:.3f}")
        print(f"   说明：{weighted_result.explanation}")
    
    print()


def example_4_batch_import():
    """示例 4: 批量导入数据"""
    print("=" * 60)
    print("示例 4: 批量导入数据")
    print("=" * 60)
    
    import json
    import tempfile
    from pathlib import Path
    
    kb_manager = KnowledgeBaseManager()
    kb = kb_manager.create_knowledge_base(
        domain_id="batch_import",
        name="批量导入示例"
    )
    
    # 准备批量数据
    keywords_data = {
        "keywords": [
            {
                "keyword": "云计算",
                "level": "core",
                "weight": 1.8,
                "aliases": ["cloud computing"],
                "description": "基于互联网的计算服务"
            },
            {
                "keyword": "容器化",
                "level": "important",
                "weight": 1.3,
                "aliases": ["containerization"],
                "description": "应用封装技术"
            },
            {
                "keyword": "微服务",
                "level": "important",
                "weight": 1.3,
                "aliases": ["microservices"],
                "description": "分布式架构风格"
            }
        ]
    }
    
    # 创建临时文件
    temp_file = Path(tempfile.mktemp(suffix=".json"))
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(keywords_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 创建批量导入文件：{temp_file}")
    
    # 执行批量导入
    count = kb_manager.import_keywords_from_file(
        domain_id="batch_import",
        filepath=str(temp_file),
        format="json"
    )
    
    print(f"✅ 成功导入 {count} 个关键字")
    print(f"   当前关键字列表：{list(kb.keywords.keys())}")
    
    # 清理临时文件
    temp_file.unlink()
    print()


def example_5_continuous_learning():
    """示例 5: 持续学习和扩充"""
    print("=" * 60)
    print("示例 5: 持续学习和扩充")
    print("=" * 60)
    
    kb_manager = KnowledgeBaseManager()
    kb = kb_manager.create_knowledge_base(
        domain_id="learning_system",
        name="自学习知识库"
    )
    
    # 初始知识
    kb.add_keyword("人工智能", KeywordLevel.CORE, 1.8)
    
    print("🌱 初始知识库状态:")
    print(f"   关键字：{list(kb.keywords.keys())}")
    
    # 从用户交互数据中学习
    user_interactions = [
        "我想了解深度学习的知识",
        "神经网络和机器学习有什么区别？",
        "强化学习在机器人中的应用",
        "自然语言处理需要用到哪些技术？",
        "计算机视觉中的深度学习模型",
    ]
    
    print(f"\n📚 收集到 {len(user_interactions)} 条用户交互数据")
    
    # 提取新关键字
    all_new_words = set()
    for interaction in user_interactions:
        words = kb.extract_keywords_from_text(interaction)
        all_new_words.update(words)
    
    print(f"💡 提取到新词：{all_new_words}")
    
    # 统计频率并建议
    word_freq = {}
    for interaction in user_interactions:
        words = kb.extract_keywords_from_text(interaction)
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # 过滤掉已有的
    existing = set(kb.keywords.keys())
    suggestions = [
        (word, freq) for word, freq in word_freq.items()
        if word not in existing and freq >= 2
    ]
    
    print(f"\n🎯 建议添加的关键字（出现>=2 次）:")
    for word, freq in sorted(suggestions, key=lambda x: x[1], reverse=True):
        print(f"   {word}: {freq} 次")
    
    # 自动添加高频词
    added_count = 0
    for word, freq in suggestions:
        if freq >= 3:
            level = KeywordLevel.IMPORTANT
            weight = 1.3
        else:
            level = KeywordLevel.NORMAL
            weight = 1.0
        
        kb.add_keyword(
            keyword=word,
            level=level,
            weight=weight,
            description=f"从用户交互中提取（出现{freq}次）"
        )
        added_count += 1
    
    print(f"\n✅ 自动添加了 {added_count} 个新关键字")
    print(f"📊 当前知识库关键字总数：{len(kb.keywords)}")
    print()


def main():
    """运行所有应用示例"""
    print("\n" + "=" * 60)
    print("NecoRAG 知识库管理模块 - 实际应用集成示例")
    print("=" * 60 + "\n")
    
    try:
        example_1_initialize_knowledge()
        example_2_query_enhancement()
        example_3_document_weighting()
        example_4_batch_import()
        example_5_continuous_learning()
        
        print("=" * 60)
        print("✅ 所有应用示例运行完成！")
        print("=" * 60)
        print("\n💡 提示：这些示例展示了知识库管理模块在实际 RAG 系统中的典型应用场景")
        print("   - 初始化领域知识")
        print("   - 增强查询理解")
        print("   - 文档权重计算")
        print("   - 批量数据导入")
        print("   - 持续学习扩充")
        
        return 0
        
    except Exception as e:
        print(f"❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
