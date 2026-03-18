"""
NecoRAG Intent Module - 语义意图分类模块

提供语义意图分类、路由策略和查询分析功能，
在用户查询到达检索层之前进行语义分析和意图识别。

主要组件:
- IntentType: 意图类型枚举
- IntentResult: 意图分类结果
- IntentRoutingStrategy: 路由策略
- IntentConfig: 意图分类配置
- IntentClassifier: 意图分类器
- IntentRouter: 意图路由器
- SemanticAnalyzer: 语义分析器（统一接口）

使用示例:
```python
from src.intent import SemanticAnalyzer, IntentConfig

# 快速使用
from src.intent import quick_analyze
result = quick_analyze("什么是深度学习？")
print(result["intent"])  # "explanation"

# 完整使用
analyzer = SemanticAnalyzer()
result = analyzer.analyze("如何配置 PyTorch？")
print(result["routing_strategy"]["enable_hyde"])  # False

# 自定义配置
config = IntentConfig.advanced()
analyzer = SemanticAnalyzer(config)
```
"""

# 数据模型
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


__all__ = [
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
]
