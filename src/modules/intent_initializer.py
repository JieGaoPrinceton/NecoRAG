"""
NecoRAG 意图初始化设置工具

支持用户预定义 3-6 个基础意图，然后自动构建三级意图体系
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .hierarchical_models import (
    HierarchicalIntent,
    IntentHierarchyTree,
    IntentLevel,
)
from .intent_knowledge import IntentKnowledgeManager
from .intent_expander import IntentExpander


class IntentInitializer:
    """
    意图初始化工具
    
    引导用户创建自定义的三级意图体系
    """
    
    def __init__(self, storage_dir: str = None):
        """
        初始化工具
        
        Args:
            storage_dir: 存储目录
        """
        self.storage_dir = storage_dir
        self.knowledge_manager = IntentKnowledgeManager(storage_dir)
        self.expander = IntentExpander(self.knowledge_manager)
        
        # 预设的意图模板
        self.intent_templates = self._load_intent_templates()
    
    def _load_intent_templates(self) -> Dict[str, dict]:
        """加载意图模板"""
        return {
            "knowledge_base": {
                "name": "知识查询",
                "description": "查询事实性知识和信息",
                "default_l2": [
                    {"name": "事实查证", "desc": "查找具体事实和数据"},
                    {"name": "概念解释", "desc": "理解概念和术语"},
                    {"name": "定义询问", "desc": "查询定义和含义"},
                    {"name": "数据检索", "desc": "获取统计数据和信息"},
                ]
            },
            "task_guidance": {
                "name": "任务指导",
                "description": "获取操作步骤和方法指导",
                "default_l2": [
                    {"name": "逐步指导", "desc": "详细的操作步骤"},
                    {"name": "最佳实践", "desc": "推荐的方法和技巧"},
                    {"name": "故障排除", "desc": "问题解决和调试"},
                    {"name": "配置部署", "desc": "系统配置和部署"},
                ]
            },
            "analysis_reasoning": {
                "name": "分析推理",
                "description": "进行分析、比较和推理",
                "default_l2": [
                    {"name": "对比分析", "desc": "比较不同事物的差异"},
                    {"name": "因果推理", "desc": "分析原因和结果"},
                    {"name": "评估判断", "desc": "评价和判断优劣"},
                    {"name": "趋势预测", "desc": "预测发展趋势"},
                ]
            },
            "creative_exploration": {
                "name": "创造探索",
                "description": "创造性思维和探索性问题",
                "default_l2": [
                    {"name": "创意生成", "desc": "产生新想法和方案"},
                    {"name": "场景探索", "desc": "探索不同可能性"},
                    {"name": "推荐请求", "desc": "寻求建议和推荐"},
                    {"name": "方案设计", "desc": "设计方案和规划"},
                ]
            },
            "conversation_interaction": {
                "name": "对话交互",
                "description": "日常对话和交互",
                "default_l2": [
                    {"name": "问候告别", "desc": "打招呼和社会礼仪"},
                    {"name": "观点分享", "desc": "交流看法和感受"},
                    {"name": "澄清确认", "desc": "确认理解和澄清疑问"},
                    {"name": "情感交流", "desc": "情感表达和回应"},
                ]
            },
            "technical_support": {
                "name": "技术支持",
                "description": "技术问题和支持",
                "default_l2": [
                    {"name": "错误处理", "desc": "错误和异常处理"},
                    {"name": "性能优化", "desc": "性能调优和优化"},
                    {"name": "版本兼容", "desc": "版本和兼容性问题"},
                    {"name": "工具使用", "desc": "工具和技术使用"},
                ]
            },
        }
    
    def create_custom_hierarchy(self,
                               custom_intents: List[dict],
                               tree_name: str = "自定义意图体系") -> IntentHierarchyTree:
        """
        创建自定义意图体系
        
        Args:
            custom_intents: 自定义意图列表
                           [{"name": "...", "description": "...", "l2_children": [...]}]
            tree_name: 树名称
        
        Returns:
            IntentHierarchyTree: 创建的意图树
        """
        tree = IntentHierarchyTree(
            tree_id=f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=tree_name,
            description="用户自定义的三级意图体系"
        )
        
        # 创建 L1 意图
        for intent_data in custom_intents:
            l1_id = f"l1_{intent_data['name']}"
            
            l1_intent = HierarchicalIntent(
                intent_id=l1_id,
                name=intent_data["name"],
                level=IntentLevel.L1,
                description=intent_data.get("description", ""),
                keywords=intent_data.get("keywords", []),
            )
            
            tree.add_intent(l1_intent)
            
            # 创建 L2 子意图
            l2_children = intent_data.get("l2_children", [])
            for l2_data in l2_children:
                l2_id = f"{l1_id}_l2_{l2_data['name']}"
                
                l2_intent = HierarchicalIntent(
                    intent_id=l2_id,
                    name=l2_data["name"],
                    level=IntentLevel.L2,
                    description=l2_data.get("description", ""),
                    parent_id=l1_id,
                    keywords=l2_data.get("keywords", []),
                )
                
                tree.add_intent(l2_intent)
        
        self.knowledge_manager.current_tree = tree
        return tree
    
    def quick_setup(self, 
                   template_keys: List[str],
                   tree_name: str = None) -> IntentHierarchyTree:
        """
        快速设置（基于模板）
        
        Args:
            template_keys: 模板键列表（3-6 个）
            tree_name: 树名称
        
        Returns:
            IntentHierarchyTree: 创建的意图树
        """
        if not (3 <= len(template_keys) <= 6):
            raise ValueError(f"请选择 3-6 个意图模板，当前选择了{len(template_keys)}个")
        
        custom_intents = []
        
        for key in template_keys:
            if key not in self.intent_templates:
                raise ValueError(f"未知的模板键：{key}")
            
            template = self.intent_templates[key]
            custom_intents.append({
                "name": template["name"],
                "description": template["description"],
                "l2_children": [
                    {"name": l2["name"], "description": l2["desc"]}
                    for l2 in template["default_l2"]
                ],
            })
        
        if tree_name is None:
            tree_name = f"意图体系_{datetime.now().strftime('%Y%m%d')}"
        
        return self.create_custom_hierarchy(custom_intents, tree_name)
    
    def add_l3_intents(self,
                      l2_intent_id: str,
                      l3_intents: List[dict]) -> bool:
        """
        为 L2 意图添加 L3 子意图
        
        Args:
            l2_intent_id: L2 意图 ID
            l3_intents: L3 意图列表
                       [{"name": "...", "description": "...", "keywords": [...]}]
        
        Returns:
            是否成功
        """
        tree = self.knowledge_manager.current_tree
        if not tree:
            return False
        
        l2_intent = tree.get_intent(l2_intent_id)
        if not l2_intent or l2_intent.level != IntentLevel.L2:
            return False
        
        for l3_data in l3_intents:
            l3_id = f"{l2_intent_id}_l3_{l3_data['name']}"
            
            l3_intent = HierarchicalIntent(
                intent_id=l3_id,
                name=l3_data["name"],
                level=IntentLevel.L3,
                description=l3_data.get("description", ""),
                parent_id=l2_intent_id,
                keywords=l3_data.get("keywords", []),
                examples=l3_data.get("examples", []),
            )
            
            tree.add_intent(l3_intent)
        
        return True
    
    def auto_populate_l3(self,
                        learning_queries: Dict[str, List[str]]) -> int:
        """
        自动填充 L3 意图（基于学习查询）
        
        Args:
            learning_queries: {L2 意图 ID: [查询列表]}
        
        Returns:
            创建的 L3 意图数量
        """
        tree = self.knowledge_manager.current_tree
        if not tree:
            return 0
        
        created_count = 0
        
        for l2_intent_id, queries in learning_queries.items():
            l2_intent = tree.get_intent(l2_intent_id)
            if not l2_intent:
                continue
            
            # 使用扩充器分析查询
            clusters = self.expander._cluster_queries(queries)
            
            # 为每个簇创建 L3 意图
            for cluster_id, cluster_queries in clusters.items():
                if len(cluster_queries) < 2:
                    continue
                
                keywords = self.expander._extract_common_keywords(cluster_queries)
                
                l3_id = f"{l2_intent_id}_l3_auto_{created_count + 1}"
                l3_name = keywords[0] if keywords else f"子意图{created_count + 1}"
                
                l3_intent = HierarchicalIntent(
                    intent_id=l3_id,
                    name=l3_name,
                    level=IntentLevel.L3,
                    description=self.expander._generate_intent_description(cluster_queries),
                    parent_id=l2_intent_id,
                    keywords=keywords,
                    examples=cluster_queries[:5],
                )
                
                tree.add_intent(l3_intent)
                created_count += 1
        
        return created_count
    
    def save_configuration(self, filename: str = None) -> str:
        """
        保存配置到文件
        
        Args:
            filename: 文件名
        
        Returns:
            保存的文件路径
        """
        return self.knowledge_manager.save_current_tree(filename)
    
    def load_configuration(self, filepath: str) -> bool:
        """
        加载配置
        
        Args:
            filepath: 配置文件路径
        
        Returns:
            是否成功
        """
        tree = self.knowledge_manager.load_tree_from_file(filepath)
        return tree is not None
    
    def get_setup_guide(self) -> str:
        """
        获取设置指南
        
        Returns:
            设置指南文本
        """
        guide = """
# NecoRAG 意图初始化设置指南

## 步骤 1: 选择基础意图模板（3-6 个）

可用的模板：
"""
        
        for i, (key, template) in enumerate(self.intent_templates.items(), 1):
            guide += f"\n{i}. **{key}**: {template['name']} - {template['description']}"
        
        guide += """

## 步骤 2: 快速设置示例

```python
from src.intent import IntentInitializer

initializer = IntentInitializer()

# 选择 3-6 个模板
tree = initializer.quick_setup([
    'knowledge_base',      # 知识查询
    'task_guidance',       # 任务指导
    'analysis_reasoning',  # 分析推理
    'creative_exploration', # 创造探索
])
```

## 步骤 3: 自定义 L2 子意图

```python
# 为特定 L1 添加自定义 L2 子意图
custom_l2 = [
    {"name": "自定义子意图 1", "description": "描述 1"},
    {"name": "自定义子意图 2", "description": "描述 2"},
]

# 添加到现有的 L1 意图
# （需要先获取 L1 意图 ID）
```

## 步骤 4: 通过 AI 学习自动填充 L3

```python
# 收集用户查询数据
learning_queries = {
    "l2_intent_id_1": ["查询 1", "查询 2", ...],
    "l2_intent_id_2": ["查询 3", "查询 4", ...],
}

# 自动创建 L3 意图
count = initializer.auto_populate_l3(learning_queries)
print(f"创建了 {count} 个 L3 意图")
```

## 步骤 5: 保存配置

```python
# 保存到文件
filepath = initializer.save_configuration("my_intent_system.json")

# 后续可以重新加载
initializer.load_configuration(filepath)
```

## 最佳实践

1. **从模板开始**: 使用预定义模板作为起点
2. **逐步细化**: 先建立 L1，再扩展 L2，最后填充 L3
3. **数据驱动**: 收集真实用户查询来优化意图体系
4. **定期更新**: 根据使用情况调整意图结构

"""
        return guide


def create_intent_initializer(storage_dir: str = None) -> IntentInitializer:
    """
    创建意图初始化工具
    
    Args:
        storage_dir: 存储目录
    
    Returns:
        IntentInitializer: 初始化工具实例
    """
    return IntentInitializer(storage_dir=storage_dir)
