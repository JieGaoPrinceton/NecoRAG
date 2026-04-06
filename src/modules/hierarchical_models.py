"""
NecoRAG 层次化意图模型模块

支持三级意图体系：
- L1: 大类意图（宏观意图）
- L2: 详细意图（具体意图）
- L3: 最细节意图（原子意图）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import json


class IntentLevel(Enum):
    """意图层级枚举"""
    L1 = "l1"      # 大类意图（宏观）
    L2 = "l2"      # 详细意图（具体）
    L3 = "l3"      # 最细节意图（原子）


@dataclass
class HierarchicalIntent:
    """
    层次化意图节点
    
    每个意图节点可以包含子意图，形成树状结构
    
    Attributes:
        intent_id: 意图唯一标识
        name: 意图名称
        level: 意图层级 (L1/L2/L3)
        description: 意图描述
        parent_id: 父意图 ID（L1 为 None）
        children: 子意图列表
        keywords: 意图关键词
        examples: 意图示例查询
        routing_config: 路由配置
        metadata: 元数据
    """
    intent_id: str
    name: str
    level: IntentLevel
    description: str = ""
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)  # 子意图 ID 列表
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    routing_config: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "intent_id": self.intent_id,
            "name": self.name,
            "level": self.level.value,
            "description": self.description,
            "parent_id": self.parent_id,
            "children": self.children,
            "keywords": self.keywords,
            "examples": self.examples,
            "routing_config": self.routing_config,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "HierarchicalIntent":
        """从字典创建"""
        return cls(
            intent_id=data["intent_id"],
            name=data["name"],
            level=IntentLevel(data["level"]),
            description=data.get("description", ""),
            parent_id=data.get("parent_id"),
            children=data.get("children", []),
            keywords=data.get("keywords", []),
            examples=data.get("examples", []),
            routing_config=data.get("routing_config", {}),
            metadata=data.get("metadata", {}),
        )
    
    def add_child(self, child_id: str) -> None:
        """添加子意图 ID"""
        if child_id not in self.children:
            self.children.append(child_id)
    
    def remove_child(self, child_id: str) -> None:
        """移除子意图 ID"""
        if child_id in self.children:
            self.children.remove(child_id)
    
    def add_keyword(self, keyword: str) -> None:
        """添加关键词"""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
    
    def add_example(self, example: str) -> None:
        """添加示例查询"""
        if example not in self.examples:
            self.examples.append(example)


@dataclass
class IntentHierarchyTree:
    """
    层次化意图树
    
    管理完整的三级意图体系
    
    Attributes:
        tree_id: 意图树唯一标识
        name: 意图树名称
        description: 意图树描述
        roots: L1 根节点列表
        all_intents: 所有意图节点（ID -> 节点）
    """
    tree_id: str
    name: str
    description: str = ""
    roots: List[str] = field(default_factory=list)  # L1 意图 ID 列表
    all_intents: Dict[str, HierarchicalIntent] = field(default_factory=dict)
    
    def add_intent(self, intent: HierarchicalIntent) -> bool:
        """添加意图节点"""
        if intent.intent_id in self.all_intents:
            return False
        
        self.all_intents[intent.intent_id] = intent
        
        # 如果是 L1，添加到根节点
        if intent.level == IntentLevel.L1 and intent.intent_id not in self.roots:
            self.roots.append(intent.intent_id)
        
        # 如果有父节点，建立父子关系
        if intent.parent_id and intent.parent_id in self.all_intents:
            parent = self.all_intents[intent.parent_id]
            parent.add_child(intent.intent_id)
        
        return True
    
    def get_intent(self, intent_id: str) -> Optional[HierarchicalIntent]:
        """获取意图节点"""
        return self.all_intents.get(intent_id)
    
    def get_children(self, intent_id: str) -> List[HierarchicalIntent]:
        """获取子意图列表"""
        intent = self.get_intent(intent_id)
        if not intent:
            return []
        
        return [
            self.all_intents[child_id]
            for child_id in intent.children
            if child_id in self.all_intents
        ]
    
    def get_siblings(self, intent_id: str) -> List[HierarchicalIntent]:
        """获取兄弟意图列表"""
        intent = self.get_intent(intent_id)
        if not intent or not intent.parent_id:
            # L1 的兄弟节点是其他 L1 节点
            return [
                self.all_intents[root_id]
                for root_id in self.roots
                if root_id != intent_id
            ]
        
        parent = self.get_intent(intent.parent_id)
        if not parent:
            return []
        
        return [
            self.all_intents[child_id]
            for child_id in parent.children
            if child_id != intent_id
        ]
    
    def get_path_to_root(self, intent_id: str) -> List[HierarchicalIntent]:
        """获取到根节点的路径"""
        path = []
        current_id = intent_id
        
        while current_id:
            intent = self.get_intent(current_id)
            if not intent:
                break
            
            path.insert(0, intent)
            current_id = intent.parent_id
        
        return path
    
    def get_l2_intents(self, l1_intent_id: str) -> List[HierarchicalIntent]:
        """获取指定 L1 下的所有 L2 意图"""
        l1_intent = self.get_intent(l1_intent_id)
        if not l1_intent or l1_intent.level != IntentLevel.L1:
            return []
        
        return [
            intent for intent in self.get_children(l1_intent_id)
            if intent.level == IntentLevel.L2
        ]
    
    def get_l3_intents(self, l2_intent_id: str) -> List[HierarchicalIntent]:
        """获取指定 L2 下的所有 L3 意图"""
        l2_intent = self.get_intent(l2_intent_id)
        if not l2_intent or l2_intent.level != IntentLevel.L2:
            return []
        
        return [
            intent for intent in self.get_children(l2_intent_id)
            if intent.level == IntentLevel.L3
        ]
    
    def find_leaf_intents(self, intent_id: str) -> List[HierarchicalIntent]:
        """查找指定意图下的所有叶子节点（L3）"""
        intent = self.get_intent(intent_id)
        if not intent:
            return []
        
        # 如果已经是 L3，返回自己
        if intent.level == IntentLevel.L3:
            return [intent]
        
        # 否则递归查找所有子节点的叶子
        leaf_intents = []
        for child_id in intent.children:
            leaf_intents.extend(self.find_leaf_intents(child_id))
        
        return leaf_intents
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "tree_id": self.tree_id,
            "name": self.name,
            "description": self.description,
            "roots": self.roots,
            "all_intents": {
                k: v.to_dict() for k, v in self.all_intents.items()
            },
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "IntentHierarchyTree":
        """从字典创建"""
        tree = cls(
            tree_id=data["tree_id"],
            name=data["name"],
            description=data.get("description", ""),
            roots=data.get("roots", []),
        )
        
        # 先创建所有节点
        for intent_id, intent_data in data.get("all_intents", {}).items():
            intent = HierarchicalIntent.from_dict(intent_data)
            tree.all_intents[intent_id] = intent
        
        # 再建立父子关系
        for intent in tree.all_intents.values():
            if intent.level == IntentLevel.L1 and intent.intent_id not in tree.roots:
                tree.roots.append(intent.intent_id)
            
            if intent.parent_id:
                parent = tree.get_intent(intent.parent_id)
                if parent:
                    parent.add_child(intent.intent_id)
        
        return tree
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        验证意图树的完整性
        
        Returns:
            (是否有效，错误信息列表)
        """
        errors = []
        
        # 检查所有 L2 是否有 L1 父节点
        for intent in self.all_intents.values():
            if intent.level == IntentLevel.L2 and not intent.parent_id:
                errors.append(f"L2 意图 {intent.intent_id} 缺少 L1 父节点")
            
            # 检查所有 L3 是否有 L2 父节点
            if intent.level == IntentLevel.L3 and not intent.parent_id:
                errors.append(f"L3 意图 {intent.intent_id} 缺少 L2 父节点")
            
            # 检查子节点引用是否存在
            for child_id in intent.children:
                if child_id not in self.all_intents:
                    errors.append(f"意图 {intent.intent_id} 引用了不存在的子节点 {child_id}")
        
        # 检查是否有循环依赖
        visited = set()
        for root_id in self.roots:
            if not self._has_cycle(root_id, visited, set()):
                continue
        
        return len(errors) == 0, errors
    
    def _has_cycle(self, intent_id: str, visited: Set[str], path: Set[str]) -> bool:
        """检测是否有循环依赖"""
        if intent_id in path:
            return True
        
        if intent_id in visited:
            return False
        
        visited.add(intent_id)
        path.add(intent_id)
        
        intent = self.get_intent(intent_id)
        if intent:
            for child_id in intent.children:
                if self._has_cycle(child_id, visited, path):
                    return True
        
        path.remove(intent_id)
        return False


def create_default_hierarchy_tree(tree_name: str = "默认意图体系") -> IntentHierarchyTree:
    """
    创建默认的三级意图树
    
    Args:
        tree_name: 意图树名称
    
    Returns:
        IntentHierarchyTree: 默认意图树
    """
    tree = IntentHierarchyTree(
        tree_id="default_hierarchy",
        name=tree_name,
        description="NecoRAG 默认三级意图体系"
    )
    
    # 定义 5 个基础 L1 意图
    l1_intents = [
        ("knowledge_query", "知识查询", "查询事实性知识和信息"),
        ("task_guidance", "任务指导", "获取操作步骤和方法指导"),
        ("analysis_reasoning", "分析推理", "进行分析、比较和推理"),
        ("creative_exploration", "创造探索", "创造性思维和探索性问题"),
        ("conversation_interaction", "对话交互", "日常对话和交互"),
    ]
    
    for intent_id, name, desc in l1_intents:
        intent = HierarchicalIntent(
            intent_id=intent_id,
            name=name,
            level=IntentLevel.L1,
            description=desc
        )
        tree.add_intent(intent)
    
    # 为每个 L1 添加一些 L2 子意图
    l2_templates = {
        "knowledge_query": [
            ("fact_lookup", "事实查证", "查找具体事实和数据"),
            ("concept_explanation", "概念解释", "理解概念和术语"),
            ("definition_inquiry", "定义询问", "查询定义和含义"),
        ],
        "task_guidance": [
            ("step_by_step_guide", "逐步指导", "详细的操作步骤"),
            ("best_practices", "最佳实践", "推荐的方法和技巧"),
            ("troubleshooting", "故障排除", "问题解决和调试"),
        ],
        "analysis_reasoning": [
            ("comparison_analysis", "对比分析", "比较不同事物的差异"),
            ("causal_reasoning", "因果推理", "分析原因和结果"),
            ("evaluation_judgment", "评估判断", "评价和判断优劣"),
        ],
        "creative_exploration": [
            ("idea_generation", "创意生成", "产生新想法和方案"),
            ("scenario_exploration", "场景探索", "探索不同可能性"),
            ("recommendation_request", "推荐请求", "寻求建议和推荐"),
        ],
        "conversation_interaction": [
            ("greeting_farewell", "问候告别", "打招呼和社会礼仪"),
            ("opinion_sharing", "观点分享", "交流看法和感受"),
            ("clarification", "澄清确认", "确认理解和澄清疑问"),
        ],
    }
    
    for l1_id, l2_list in l2_templates.items():
        for l2_id, name, desc in l2_list:
            intent = HierarchicalIntent(
                intent_id=l2_id,
                name=name,
                level=IntentLevel.L2,
                description=desc,
                parent_id=l1_id
            )
            tree.add_intent(intent)
    
    return tree
