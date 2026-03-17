"""
NecoRAG 领域权重使用示例

演示如何配置和使用领域知识权重系统
"""

from datetime import datetime, timedelta
from src.domain import (
    DomainConfig,
    DomainConfigManager,
    KeywordLevel,
    DomainLevel,
    CompositeWeightCalculator,
    TemporalWeightCalculator,
    DomainRelevanceCalculator,
    DocumentMetadata,
    DecayPresets,
    create_example_domain,
)


def example_domain_config():
    """示例1：创建和配置领域"""
    print("=" * 60)
    print("示例1：创建领域配置")
    print("=" * 60)
    
    # 方法1：使用预设的示例领域（AI/ML）
    ai_domain = create_example_domain()
    print(f"\n预设领域：{ai_domain.domain_name}")
    print(f"关键字数量：{len(ai_domain.keywords)}")
    
    # 方法2：自定义领域
    custom_domain = DomainConfig(
        domain_name="金融科技",
        domain_id="fintech",
        description="金融科技领域知识库"
    )
    
    # 添加核心关键字
    custom_domain.add_keyword(
        keyword="区块链",
        level=KeywordLevel.CORE,
        weight=1.8,
        aliases=["blockchain", "链"],
        description="分布式账本技术"
    )
    custom_domain.add_keyword(
        keyword="数字货币",
        level=KeywordLevel.CORE,
        weight=1.7,
        aliases=["cryptocurrency", "加密货币", "虚拟货币"],
        description="基于密码学的数字资产"
    )
    
    # 添加重要关键字
    custom_domain.add_keyword(
        keyword="智能合约",
        level=KeywordLevel.IMPORTANT,
        weight=1.4,
        aliases=["smart contract"],
        description="自动执行的合约协议"
    )
    
    # 配置权重因子
    custom_domain.keyword_factor = 1.2   # 增强关键字权重
    custom_domain.temporal_factor = 1.0  # 标准时间权重
    custom_domain.domain_factor = 1.5    # 增强领域权重
    
    print(f"\n自定义领域：{custom_domain.domain_name}")
    print(f"关键字数量：{len(custom_domain.keywords)}")
    
    return custom_domain


def example_temporal_weight():
    """示例2：时间权重计算"""
    print("\n" + "=" * 60)
    print("示例2：时间权重计算")
    print("=" * 60)
    
    # 使用普通领域的衰减配置
    calculator = TemporalWeightCalculator(DecayPresets.normal_domain())
    
    now = datetime.now()
    
    # 测试不同时间的文档
    test_dates = [
        ("刚发布", now),
        ("1周前", now - timedelta(days=7)),
        ("1个月前", now - timedelta(days=30)),
        ("3个月前", now - timedelta(days=90)),
        ("1年前", now - timedelta(days=365)),
        ("3年前", now - timedelta(days=1095)),
    ]
    
    print("\n文档时间权重对比：")
    print("-" * 50)
    for name, doc_time in test_dates:
        weight = calculator.calculate_weight(doc_time, now)
        tier = calculator.get_temporal_tier(doc_time, now)
        desc = calculator.get_weight_description(weight)
        print(f"{name:12} | 权重: {weight:.3f} | 层级: {tier.value:12} | {desc}")
    
    # 测试快速变化领域
    print("\n快速变化领域（如新闻）的衰减：")
    fast_calculator = TemporalWeightCalculator(DecayPresets.fast_changing_domain())
    print("-" * 50)
    for name, doc_time in test_dates[:4]:
        weight = fast_calculator.calculate_weight(doc_time, now)
        print(f"{name:12} | 权重: {weight:.3f}")


def example_relevance_scoring():
    """示例3：领域相关性评分"""
    print("\n" + "=" * 60)
    print("示例3：领域相关性评分")
    print("=" * 60)
    
    # 使用 AI/ML 领域
    domain = create_example_domain()
    calculator = DomainRelevanceCalculator(domain)
    
    # 测试文本
    test_texts = [
        "深度学习是机器学习的一个重要分支，使用神经网络进行特征学习。",
        "Transformer 架构是大语言模型的基础，采用注意力机制处理序列。",
        "向量数据库用于存储和检索高维向量，是 RAG 系统的核心组件。",
        "今天天气很好，适合出去散步。",
        "Python 是一种流行的编程语言，广泛用于数据分析。",
    ]
    
    print("\n文本领域相关性评分：")
    print("-" * 70)
    for text in test_texts:
        score = calculator.calculate_relevance(text)
        print(f"\n文本: {text[:40]}...")
        print(f"  领域等级: {score.domain_level.value}")
        print(f"  关键字得分: {score.keyword_score:.2f}")
        print(f"  密度得分: {score.density_score:.2f}")
        print(f"  权重乘数: {score.weight_multiplier:.2f}")
        print(f"  匹配关键字: {', '.join(score.keyword_matches.keys()) if score.keyword_matches else '无'}")


def example_composite_weight():
    """示例4：综合权重计算"""
    print("\n" + "=" * 60)
    print("示例4：综合权重计算")
    print("=" * 60)
    
    # 创建领域配置
    domain = create_example_domain()
    calculator = CompositeWeightCalculator(domain)
    
    now = datetime.now()
    
    # 模拟文档
    documents = [
        DocumentMetadata(
            doc_id="doc1",
            content="深度学习和神经网络是机器学习的核心技术，广泛应用于图像识别。",
            created_at=now - timedelta(days=7),
        ),
        DocumentMetadata(
            doc_id="doc2",
            content="Python 编程语言的基础语法教程。",
            created_at=now - timedelta(days=30),
        ),
        DocumentMetadata(
            doc_id="doc3",
            content="Transformer 和大语言模型 LLM 的最新进展研究报告。",
            created_at=now - timedelta(days=3),
        ),
        DocumentMetadata(
            doc_id="doc4",
            content="旅游攻略：如何规划一次完美的假期。",
            created_at=now - timedelta(days=1),
        ),
    ]
    
    # 模拟基础相似度分数
    base_scores = [0.85, 0.80, 0.82, 0.78]
    
    print("\n文档综合权重计算：")
    print("-" * 80)
    
    results = []
    for doc, base_score in zip(documents, base_scores):
        weighted = calculator.calculate_weight(base_score, doc)
        results.append((doc.doc_id, base_score, weighted.final_score, weighted))
    
    # 按最终分数排序
    results.sort(key=lambda x: x[2], reverse=True)
    
    for doc_id, base, final, ws in results:
        print(f"\n{doc_id}:")
        print(f"  基础分数: {base:.3f}")
        print(f"  关键字权重: {ws.keyword_weight:.2f}")
        print(f"  时间权重: {ws.temporal_weight:.2f}")
        print(f"  领域权重: {ws.domain_weight:.2f}")
        print(f"  最终分数: {final:.3f}")


def example_config_persistence():
    """示例5：配置持久化"""
    print("\n" + "=" * 60)
    print("示例5：配置持久化")
    print("=" * 60)
    
    import tempfile
    import os
    
    # 使用临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建配置管理器
    manager = DomainConfigManager(config_dir=temp_dir)
    
    # 创建领域
    domain = manager.create_domain(
        domain_name="测试领域",
        domain_id="test_domain",
        description="用于演示的测试领域"
    )
    domain.add_keyword("测试", KeywordLevel.CORE, 1.8, ["test"])
    domain.add_keyword("示例", KeywordLevel.IMPORTANT, 1.3, ["example"])
    
    # 保存
    manager.save_domain("test_domain")
    print(f"\n配置已保存到: {temp_dir}")
    
    # 模拟重新加载
    new_manager = DomainConfigManager(config_dir=temp_dir)
    loaded_domain = new_manager.load_domain("test_domain")
    
    if loaded_domain:
        print(f"配置已加载: {loaded_domain.domain_name}")
        print(f"关键字数量: {len(loaded_domain.keywords)}")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def main():
    """主函数"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      NecoRAG 领域权重系统演示                            ║")
    print("║  Domain Knowledge & Weight Management Demo               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # 运行示例
    example_domain_config()
    example_temporal_weight()
    example_relevance_scoring()
    example_composite_weight()
    example_config_persistence()
    
    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
