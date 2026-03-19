#!/usr/bin/env python3
"""
NecoRAG 意图初始化与扩充完整示例

演示如何：
1. 预定义 3-6 个基础意图
2. 构建三级意图体系
3. 通过 AI 学习进行意图细分和扩充
"""

import sys
from typing import List
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.intent import (
    IntentInitializer,
    IntentKnowledgeManager,
    IntentExpander,
    IntentLevel,
)


def example_1_quick_setup():
    """示例 1: 快速设置基础意图体系"""
    print("=" * 60)
    print("示例 1: 快速设置基础意图体系（从模板选择）")
    print("=" * 60)
    
    # 创建初始化工具
    initializer = IntentInitializer()
    
    # 选择 4 个基础意图模板（用户可以选 3-6 个）
    selected_templates = [
        'knowledge_base',      # 知识查询
        'task_guidance',       # 任务指导
        'analysis_reasoning',  # 分析推理
        'creative_exploration', # 创造探索
    ]
    
    print(f"\n📋 选择的 {len(selected_templates)} 个基础意图:")
    for template_key in selected_templates:
        template = initializer.intent_templates[template_key]
        print(f"   - {template['name']}: {template['description']}")
    
    # 快速设置
    tree = initializer.quick_setup(
        template_keys=selected_templates,
        tree_name="我的意图体系 v1.0"
    )
    
    print(f"\n✅ 成功创建意图树：{tree.name}")
    print(f"   - L1 意图数量：{len(tree.roots)}")
    print(f"   - 总意图节点数：{len(tree.all_intents)}")
    
    # 显示层级结构
    print("\n📊 意图层级结构:")
    for l1_id in tree.roots:
        l1_intent = tree.get_intent(l1_id)
        print(f"\n  L1: {l1_intent.name} ({l1_intent.description})")
        
        # 获取 L2 子意图
        l2_intents = tree.get_l2_intents(l1_id)
        for l2 in l2_intents:
            print(f"    ├─ L2: {l2.name} - {l2.description}")
    
    # 保存配置
    filepath = initializer.save_configuration("my_intent_system.json")
    print(f"\n💾 配置已保存到：{filepath}")
    
    return initializer, tree


def example_2_custom_hierarchy():
    """示例 2: 完全自定义意图体系"""
    print("\n" + "=" * 60)
    print("示例 2: 完全自定义意图体系")
    print("=" * 60)
    
    initializer = IntentInitializer()
    
    # 定义完全自定义的意图结构
    custom_intents = [
        {
            "name": "技术咨询",
            "description": "技术相关的问题和咨询",
            "keywords": ["技术", "开发", "编程", "系统"],
            "l2_children": [
                {"name": "代码问题", "description": "代码编写和调试", "keywords": ["代码", "bug", "错误"]},
                {"name": "架构设计", "description": "系统架构和设计", "keywords": ["架构", "设计", "模式"]},
                {"name": "性能优化", "description": "性能调优", "keywords": ["性能", "优化", "加速"]},
            ]
        },
        {
            "name": "业务支持",
            "description": "业务流程和支持",
            "keywords": ["业务", "流程", "管理"],
            "l2_children": [
                {"name": "流程指导", "description": "业务流程指导", "keywords": ["流程", "步骤"]},
                {"name": "政策咨询", "description": "政策和规定", "keywords": ["政策", "规定"]},
            ]
        },
        {
            "name": "学习交流",
            "description": "学习和交流活动",
            "keywords": ["学习", "交流", "讨论"],
            "l2_children": [
                {"name": "概念理解", "description": "理解概念", "keywords": ["概念", "理解"]},
                {"name": "经验分享", "description": "经验交流", "keywords": ["经验", "分享"]},
                {"name": "资源推荐", "description": "学习资源", "keywords": ["资源", "推荐"]},
            ]
        },
    ]
    
    # 创建自定义意图树
    tree = initializer.create_custom_hierarchy(
        custom_intents=custom_intents,
        tree_name="定制化意图体系"
    )
    
    print(f"\n✅ 创建自定义意图树：{tree.name}")
    print(f"   - L1 数量：{len(tree.roots)}")
    
    # 显示结构
    for l1_id in tree.roots:
        l1 = tree.get_intent(l1_id)
        print(f"\n  📁 {l1.name}: {l1.description}")
        print(f"     关键词：{l1.keywords}")
        
        l2_intents = tree.get_l2_intents(l1_id)
        for l2 in l2_intents:
            print(f"     └─ {l2.name}: {l2.description}")
    
    return initializer, tree


def example_3_add_l3_intents():
    """示例 3: 手动添加 L3 细节意图"""
    print("\n" + "=" * 60)
    print("示例 3: 手动添加 L3 细节意图")
    print("=" * 60)
    
    initializer, tree = example_1_quick_setup()
    
    # 获取第一个 L2 意图
    first_l1_id = tree.roots[0]
    l2_intents = tree.get_l2_intents(first_l1_id)
    
    if l2_intents:
        target_l2 = l2_intents[0]
        print(f"\n🎯 为 L2 意图 '{target_l2.name}' 添加 L3 子意图")
        
        # 定义 L3 意图
        l3_intents = [
            {
                "name": "简单事实查询",
                "description": "查询简单的事实性问题",
                "keywords": ["是什么", "定义", "含义"],
                "examples": ["什么是机器学习？", "AI 的定义是什么？"]
            },
            {
                "name": "复杂事实验证",
                "description": "验证复杂的事实信息",
                "keywords": ["真实性", "验证", "确认"],
                "examples": ["这个数据准确吗？", "如何验证这个消息？"]
            },
        ]
        
        # 添加 L3 意图
        success = initializer.add_l3_intents(target_l2.intent_id, l3_intents)
        
        if success:
            print(f"✅ 成功添加 {len(l3_intents)} 个 L3 意图")
            
            # 显示 L3 层级
            l3_intents = tree.get_l3_intents(target_l2.intent_id)
            for l3 in l3_intents:
                print(f"     └─ L3: {l3.name}")
                print(f"        关键词：{l3.keywords[:3]}")
                print(f"        示例：{l3.examples[:2]}")
    
    return initializer, tree


def example_4_ai_expansion():
    """示例 4: 通过 AI 学习自动扩充意图"""
    print("\n" + "=" * 60)
    print("示例 4: 通过 AI 学习自动扩充意图")
    print("=" * 60)
    
    initializer = IntentInitializer()
    tree = initializer.quick_setup(['knowledge_base', 'task_guidance', 'analysis_reasoning'])
    
    # 模拟收集到的用户查询数据
    learning_queries = {
        # L2 意图 ID -> 查询列表
    }
    
    # 为每个 L2 意图生成一些示例查询
    for l1_id in tree.roots:
        l2_intents = tree.get_l2_intents(l1_id)
        for l2 in l2_intents:
            # 根据 L2 的名称生成模拟查询
            sample_queries = generate_sample_queries(l2.name)
            learning_queries[l2.intent_id] = sample_queries
    
    print(f"\n📚 准备学习数据：{sum(len(v) for v in learning_queries.values())} 条查询")
    
    # 自动填充 L3 意图
    created_count = initializer.auto_populate_l3(learning_queries)
    
    print(f"✅ 自动创建了 {created_count} 个 L3 意图")
    
    # 统计结果
    stats = {}
    for l1_id in tree.roots:
        l2_intents = tree.get_l2_intents(l1_id)
        for l2 in l2_intents:
            l3_intents = tree.get_l3_intents(l2.intent_id)
            if l3_intents:
                stats[f"{l1_id}>{l2.name}"] = len(l3_intents)
    
    if stats:
        print("\n📊 L3 意图分布:")
        for path, count in stats.items():
            print(f"   {path}: {count} 个 L3 子意图")
    
    # 保存版本
    version_path = initializer.knowledge_manager.save_version(
        version_name="AI 扩充后的版本",
        description=f"自动创建了{created_count}个L3 意图"
    )
    print(f"\n💾 版本已保存：{version_path}")
    
    return initializer, tree


def example_5_continuous_learning():
    """示例 5: 持续学习和意图细化"""
    print("\n" + "=" * 60)
    print("示例 5: 持续学习和意图细化")
    print("=" * 60)
    
    from src.intent import IntentExpander, create_intent_knowledge_manager
    
    # 创建知识管理器
    knowledge_manager = create_intent_knowledge_manager()
    knowledge_manager.load_default_tree()
    
    # 创建扩充器
    expander = IntentExpander(knowledge_manager)
    
    # 模拟一批新的用户查询
    new_queries = [
        "如何安装 Python 环境？",
        "Python 虚拟环境怎么使用？",
        "pip 安装失败怎么办？",
        "如何配置 Python 镜像源？",
        "Python 版本管理工具哪个好？",
        "深度学习框架有哪些？",
        "TensorFlow 和 PyTorch 有什么区别？",
        "如何选择适合的深度学习框架？",
        "神经网络的基本原理是什么？",
        "反向传播算法是怎么工作的？",
    ]
    
    print(f"\n📥 收到 {len(new_queries)} 条新查询")
    
    # 发现新的意图模式
    candidates = expander.discover_new_intents(new_queries, min_frequency=2)
    
    print(f"💡 发现 {len(candidates)} 个新意图候选")
    for i, candidate in enumerate(candidates[:3], 1):
        print(f"\n  候选{i}:")
        print(f"    基础意图：{candidate['base_intent']}")
        print(f"    关键词：{candidate['keywords'][:3]}")
        print(f"    频率：{candidate['frequency']}")
        print(f"    置信度：{candidate['confidence']:.2f}")
    
    # 扩展现有意图
    if knowledge_manager.current_tree and knowledge_manager.current_tree.roots:
        first_l1 = knowledge_manager.current_tree.roots[0]
        
        new_l2_ids = expander.expand_intent_hierarchy(
            parent_intent_id=first_l1,
            queries=new_queries,
            expansion_strategy="auto"
        )
        
        if new_l2_ids:
            print(f"\n✅ 扩展了 {len(new_l2_ids)} 个新的 L2 子意图")
    
    return expander, knowledge_manager.current_tree


def example_6_save_and_load():
    """示例 6: 保存和加载意图体系"""
    print("\n" + "=" * 60)
    print("示例 6: 保存和加载意图体系")
    print("=" * 60)
    
    initializer = IntentInitializer()
    tree = initializer.quick_setup(['knowledge_base', 'task_guidance', 'analysis_reasoning'])
    
    # 保存
    config_file = initializer.save_configuration("intent_system_backup.json")
    print(f"💾 配置已保存到：{config_file}")
    
    # 导出学习数据
    learning_file = "learning_data_export.json"
    initializer.knowledge_manager.export_learning_data(learning_file)
    print(f"📚 学习数据已导出到：{learning_file}")
    
    # 获取统计信息
    stats = initializer.knowledge_manager.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"   总意图数：{stats.get('total_intents', 0)}")
    print(f"   L1 数量：{stats.get('l1_count', 0)}")
    print(f"   L2 数量：{stats.get('l2_count', 0)}")
    print(f"   L3 数量：{stats.get('l3_count', 0)}")
    print(f"   总示例数：{stats.get('total_examples', 0)}")
    
    # 列出可用版本
    versions = initializer.knowledge_manager.list_versions()
    if versions:
        print(f"\n📜 可用版本:")
        for v in versions[:3]:
            print(f"   - {v['version_name']} ({v['timestamp']})")
    
    return initializer, tree


def generate_sample_queries(intent_name: str) -> List[str]:
    """根据意图名称生成模拟查询"""
    query_templates = {
        "事实查证": ["XX 是什么时候成立的？", "谁发明了计算机？", "地球有多大年纪？"],
        "概念解释": ["什么是量子计算？", "请解释一下区块链", "人工智能是什么意思？"],
        "定义询问": ["机器学习的定义", "深度学习的定义是什么？", "请定义自然语言处理"],
        "逐步指导": ["如何安装 Python？", "怎么配置 Git？", "教我写 Hello World 程序"],
        "最佳实践": ["Python 编码规范", "如何写出优雅的代码？", "软件开发的最佳实践"],
        "故障排除": ["代码报错了怎么办？", "程序运行不起来", "遇到 bug 如何解决？"],
        "对比分析": ["Python 和 Java 哪个更好？", "MySQL 和 PostgreSQL 的区别", "前端和后端的差异"],
        "因果推理": ["为什么天空是蓝的？", "为什么会下雨？", "AI 为什么会犯错？"],
        "评估判断": ["哪个编程语言最适合新手？", "这款手机值得买吗？", "这个方案可行吗？"],
    }
    
    base_queries = query_templates.get(intent_name, [f"关于{intent_name}的问题"])
    
    # 添加一些变体
    variations = []
    for q in base_queries:
        variations.append(q)
        variations.append(q.replace("？", "?"))
        variations.append(q.replace("什么", "啥"))
    
    return variations[:8]


def main():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("NecoRAG 意图初始化与扩充完整示例")
    print("=" * 70)
    
    try:
        # 示例 1: 快速设置
        init1, tree1 = example_1_quick_setup()
        
        # 示例 2: 自定义
        init2, tree2 = example_2_custom_hierarchy()
        
        # 示例 3: 添加 L3
        init3, tree3 = example_3_add_l3_intents()
        
        # 示例 4: AI 扩充
        init4, tree4 = example_4_ai_expansion()
        
        # 示例 5: 持续学习
        expander, tree5 = example_5_continuous_learning()
        
        # 示例 6: 保存加载
        init6, tree6 = example_6_save_and_load()
        
        print("\n" + "=" * 70)
        print("✅ 所有示例运行完成！")
        print("=" * 70)
        
        print("\n📝 提示:")
        print("   - 生成的配置文件保存在当前目录")
        print("   - 可以修改示例中的参数来定制意图体系")
        print("   - 使用 get_setup_guide() 查看详细的设置指南")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
