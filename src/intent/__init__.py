"""
NecoRAG Intent Module - 语义意图分类模块

提供语义意图分类、路由策略和查询分析功能，
在用户查询到达检索层之前进行语义分析和意图识别。

支持三级层次化意图体系：
- L1: 大类意图（宏观意图）
- L2: 详细意图（具体意图）  
- L3: 最细节意图（原子意图）

主要组件:
- 基础组件:
  - IntentType: 意图类型枚举
  - IntentResult: 意图分类结果
  - IntentRoutingStrategy: 路由策略
  - IntentConfig: 意图分类配置
  - IntentClassifier: 意图分类器
  - SemanticAnalyzer: 语义分析器

- 层次化意图管理:
  - IntentLevel: 意图层级枚举
  - HierarchicalIntent: 层次化意图节点
  - IntentHierarchyTree: 意图树
  - IntentKnowledgeManager: 意图知识管理器
  - IntentExpander: 意图扩充器
  - IntentInitializer: 意图初始化工具

使用示例:
```python
# 基础使用
from src.intent import SemanticAnalyzer, quick_analyze
result = quick_analyze("什么是深度学习？")

# 层次化意图管理
from src.intent import IntentInitializer
initializer = IntentInitializer()
tree = initializer.quick_setup(['knowledge_base', 'task_guidance', 'analysis_reasoning'])
```
"""

# 基础数据模型
from .models import (
    IntentType,
    IntentResult,
    IntentRoutingStrategy,
    SemanticAnalysisResult,
)

# 配置
from .config import IntentConfig

# 分类器
from .classifier import IntentClassifier

# 路由器
from .router import IntentRouter, AdaptiveRouter

# 语义分析器
from .semantic_analyzer import (
    SemanticAnalyzer,
    create_analyzer,
    quick_analyze,
)

# 层次化意图管理
from .hierarchical_models import (
    IntentLevel,
    HierarchicalIntent,
    IntentHierarchyTree,
    create_default_hierarchy_tree,
)

# 意图知识库
from .intent_knowledge import (
    IntentKnowledgeManager,
    create_intent_knowledge_manager,
)

# 意图扩充器
from .intent_expander import (
    IntentExpander,
    create_intent_expander,
)

# 意图初始化
from .intent_initializer import (
    IntentInitializer,
    create_intent_initializer,
)


__all__ = [
    # ===== 基础组件 =====
    # 数据模型
    "IntentType",
    "IntentResult",
    "IntentRoutingStrategy",
    "SemanticAnalysisResult",
    
    # 配置
    "IntentConfig",
    
    # 分类器
    "IntentClassifier",
    
    # 路由器
    "IntentRouter",
    "AdaptiveRouter",
    
    # 语义分析器
    "SemanticAnalyzer",
    "create_analyzer",
    "quick_analyze",
    
    # ===== 层次化意图管理 =====
    # 层次化模型
    "IntentLevel",
    "HierarchicalIntent",
    "IntentHierarchyTree",
    "create_default_hierarchy_tree",
    
    # 知识库管理
    "IntentKnowledgeManager",
    "create_intent_knowledge_manager",
    
    # 扩充器
    "IntentExpander",
    "create_intent_expander",
    
    # 初始化工具
    "IntentInitializer",
    "create_intent_initializer",
]
