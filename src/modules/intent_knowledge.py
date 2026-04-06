"""
NecoRAG 意图知识库管理模块

集成知识库进行意图学习和扩充
支持：
1. 从知识库中学习意图相关数据
2. 将意图体系存储到知识库
3. 基于知识库进行意图匹配和推荐
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .hierarchical_models import (
    HierarchicalIntent,
    IntentHierarchyTree,
    IntentLevel,
    create_default_hierarchy_tree,
)


class IntentKnowledgeManager:
    """
    意图知识管理器
    
    管理意图相关的知识库，支持持久化和版本控制
    
    Attributes:
        storage_dir: 存储目录
        current_tree: 当前意图树
        version_history: 版本历史
    """
    
    def __init__(self, storage_dir: str = None):
        """
        初始化意图知识管理器
        
        Args:
            storage_dir: 存储目录路径
        """
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(__file__), "intent_knowledge"
        )
        
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 子目录
        self.trees_dir = os.path.join(self.storage_dir, "trees")
        self.versions_dir = os.path.join(self.storage_dir, "versions")
        self.learning_data_dir = os.path.join(self.storage_dir, "learning_data")
        
        for dir_path in [self.trees_dir, self.versions_dir, self.learning_data_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        # 当前加载的意图树
        self.current_tree: Optional[IntentHierarchyTree] = None
        
        # 版本历史
        self.version_history: List[dict] = []
        
        # 学习数据缓存
        self.learning_cache: Dict[str, List[dict]] = {}
    
    def create_tree(self, tree_name: str, description: str = "") -> IntentHierarchyTree:
        """
        创建新的意图树
        
        Args:
            tree_name: 树名称
            description: 描述
        
        Returns:
            IntentHierarchyTree: 新创建的意图树
        """
        tree = IntentHierarchyTree(
            tree_id=f"tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=tree_name,
            description=description
        )
        
        self.current_tree = tree
        return tree
    
    def load_default_tree(self) -> IntentHierarchyTree:
        """
        加载默认意图树
        
        Returns:
            IntentHierarchyTree: 默认意图树
        """
        self.current_tree = create_default_hierarchy_tree()
        return self.current_tree
    
    def load_tree_from_file(self, filepath: str) -> Optional[IntentHierarchyTree]:
        """
        从文件加载意图树
        
        Args:
            filepath: JSON 文件路径
        
        Returns:
            加载的意图树，失败返回 None
        """
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tree = IntentHierarchyTree.from_dict(data)
        self.current_tree = tree
        return tree
    
    def save_current_tree(self, filename: str = None) -> str:
        """
        保存当前意图树到文件
        
        Args:
            filename: 文件名（不含扩展名）
        
        Returns:
            保存的文件路径
        """
        if not self.current_tree:
            raise ValueError("没有当前意图树")
        
        if filename is None:
            filename = f"{self.current_tree.tree_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        filepath = os.path.join(self.trees_dir, f"{filename}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_tree.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def save_version(self, version_name: str, description: str = "") -> str:
        """
        保存当前意图树的版本
        
        Args:
            version_name: 版本名称
            description: 版本描述
        
        Returns:
            版本文件路径
        """
        if not self.current_tree:
            raise ValueError("没有当前意图树")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_id = f"v_{timestamp}"
        
        version_data = {
            "version_id": version_id,
            "version_name": version_name,
            "description": description,
            "timestamp": timestamp,
            "tree_data": self.current_tree.to_dict(),
        }
        
        filepath = os.path.join(self.versions_dir, f"{version_id}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, ensure_ascii=False, indent=2)
        
        # 记录版本历史
        self.version_history.append({
            "version_id": version_id,
            "version_name": version_name,
            "timestamp": timestamp,
            "filepath": filepath,
        })
        
        return filepath
    
    def load_version(self, version_id: str) -> Optional[IntentHierarchyTree]:
        """
        加载指定版本的意图树
        
        Args:
            version_id: 版本 ID
        
        Returns:
            加载的意图树
        """
        filepath = os.path.join(self.versions_dir, f"{version_id}.json")
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        
        tree = IntentHierarchyTree.from_dict(version_data["tree_data"])
        self.current_tree = tree
        return tree
    
    def add_learning_example(self, intent_id: str, query: str, 
                            metadata: dict = None) -> None:
        """
        添加学习示例
        
        Args:
            intent_id: 意图 ID
            query: 用户查询
            metadata: 元数据
        """
        if not self.current_tree:
            raise ValueError("没有当前意图树")
        
        intent = self.current_tree.get_intent(intent_id)
        if not intent:
            raise ValueError(f"意图不存在：{intent_id}")
        
        # 添加到意图的 examples
        intent.add_example(query)
        
        # 同时记录到学习数据
        learning_record = {
            "intent_id": intent_id,
            "query": query,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        
        if intent_id not in self.learning_cache:
            self.learning_cache[intent_id] = []
        
        self.learning_cache[intent_id].append(learning_record)
    
    def get_learning_examples(self, intent_id: str) -> List[dict]:
        """
        获取指定意图的学习示例
        
        Args:
            intent_id: 意图 ID
        
        Returns:
            学习示例列表
        """
        return self.learning_cache.get(intent_id, [])
    
    def export_learning_data(self, filepath: str) -> bool:
        """
        导出学习数据到文件
        
        Args:
            filepath: 导出文件路径
        
        Returns:
            是否成功
        """
        export_data = {
            "export_time": datetime.now().isoformat(),
            "tree_info": self.current_tree.to_dict() if self.current_tree else None,
            "learning_data": self.learning_cache,
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出失败：{e}")
            return False
    
    def import_learning_data(self, filepath: str) -> bool:
        """
        导入学习数据
        
        Args:
            filepath: 导入文件路径
        
        Returns:
            是否成功
        """
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 加载学习数据
            imported_data = import_data.get("learning_data", {})
            for intent_id, examples in imported_data.items():
                if intent_id not in self.learning_cache:
                    self.learning_cache[intent_id] = []
                self.learning_cache[intent_id].extend(examples)
            
            return True
        except Exception as e:
            print(f"导入失败：{e}")
            return False
    
    def search_similar_intents(self, keywords: List[str], 
                              top_k: int = 5) -> List[Tuple[HierarchicalIntent, float]]:
        """
        搜索相似的意图
        
        Args:
            keywords: 关键词列表
            top_k: 返回数量
        
        Returns:
            [(意图节点，相似度分数), ...]
        """
        if not self.current_tree:
            return []
        
        results = []
        keyword_set = set(keywords)
        
        for intent in self.current_tree.all_intents.values():
            score = 0.0
            
            # 关键词匹配
            matched_keywords = set(intent.keywords) & keyword_set
            if matched_keywords:
                score += len(matched_keywords) * 0.3
            
            # 名称匹配
            for kw in keywords:
                if kw.lower() in intent.name.lower():
                    score += 0.5
            
            # 描述匹配
            for kw in keywords:
                if kw.lower() in intent.description.lower():
                    score += 0.2
            
            if score > 0:
                results.append((intent, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_statistics(self) -> dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        if not self.current_tree:
            return {}
        
        stats = {
            "total_intents": len(self.current_tree.all_intents),
            "l1_count": 0,
            "l2_count": 0,
            "l3_count": 0,
            "total_examples": 0,
            "total_keywords": 0,
        }
        
        for intent in self.current_tree.all_intents.values():
            if intent.level == IntentLevel.L1:
                stats["l1_count"] += 1
            elif intent.level == IntentLevel.L2:
                stats["l2_count"] += 1
            elif intent.level == IntentLevel.L3:
                stats["l3_count"] += 1
            
            stats["total_examples"] += len(intent.examples)
            stats["total_keywords"] += len(intent.keywords)
        
        # 平均深度
        if stats["total_intents"] > 0:
            stats["avg_children_per_intent"] = (
                sum(len(intent.children) for intent in self.current_tree.all_intents.values()) 
                / stats["total_intents"]
            )
        
        return stats
    
    def list_versions(self) -> List[dict]:
        """
        列出所有版本
        
        Returns:
            版本信息列表
        """
        return sorted(
            self.version_history,
            key=lambda x: x["timestamp"],
            reverse=True
        )


def create_intent_knowledge_manager(storage_dir: str = None) -> IntentKnowledgeManager:
    """
    创建意图知识管理器
    
    Args:
        storage_dir: 存储目录
    
    Returns:
        IntentKnowledgeManager: 管理器实例
    """
    return IntentKnowledgeManager(storage_dir=storage_dir)
