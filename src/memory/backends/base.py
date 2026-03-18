"""
存储后端抽象基类

定义向量存储和图存储的统一接口。
此模块的基类继承自 core.base，并提供更具体的存储层接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# 从核心抽象层导入基类
from src.core.base import (
    BaseVectorStore as CoreBaseVectorStore,
    BaseGraphStore as CoreBaseGraphStore
)


@dataclass
class VectorRecord:
    """向量记录"""
    id: str
    vector: List[float]
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    score: float
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphNode:
    """图节点"""
    id: str
    name: str
    node_type: str = "entity"
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphEdge:
    """图边"""
    id: str
    source_id: str
    target_id: str
    edge_type: str = "related"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class BaseVectorStore(CoreBaseVectorStore):
    """
    向量存储抽象基类
    
    继承自 core.base.BaseVectorStore，提供更具体的存储层接口。
    """
    
    @abstractmethod
    def upsert(self, records: List[VectorRecord]) -> List[str]:
        """
        插入或更新向量记录
        
        Args:
            records: 向量记录列表
            
        Returns:
            List[str]: 成功插入/更新的记录ID列表
        """
        pass
    
    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        向量相似度搜索
        
        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filters: 元数据过滤条件
            threshold: 最小相似度阈值
            
        Returns:
            List[SearchResult]: 搜索结果列表（按相似度降序）
        """
        pass
    
    @abstractmethod
    def get(self, ids: List[str]) -> List[Optional[VectorRecord]]:
        """
        批量获取向量记录
        
        Args:
            ids: 记录ID列表
            
        Returns:
            List[Optional[VectorRecord]]: 记录列表（不存在返回None）
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> int:
        """
        删除向量记录
        
        Args:
            ids: 待删除的记录ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """返回记录总数"""
        pass
    
    def clear(self) -> int:
        """
        清空所有记录
        
        Returns:
            int: 删除的记录数
        """
        raise NotImplementedError("clear() not implemented")
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回向量维度"""
        pass


class BaseGraphStore(ABC):
    """
    图存储抽象基类
    
    提供存储层的图存储接口。
    注：本类使用 Node/Edge 术语，与 core.base.BaseGraphStore 的 Entity/Relation 术语不同，
    两者服务于不同的抽象层次。
    """
    
    @abstractmethod
    def add_node(self, node: GraphNode) -> str:
        """
        添加节点
        
        Args:
            node: 节点对象
            
        Returns:
            str: 节点ID
        """
        pass
    
    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> str:
        """
        添加边
        
        Args:
            edge: 边对象
            
        Returns:
            str: 边ID
        """
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[GraphNode]: 节点对象或None
        """
        pass
    
    @abstractmethod
    def get_neighbors(
        self,
        node_id: str,
        edge_types: Optional[List[str]] = None,
        direction: str = "both"  # in, out, both
    ) -> List[Tuple[GraphNode, GraphEdge]]:
        """
        获取邻居节点
        
        Args:
            node_id: 节点ID
            edge_types: 边类型过滤
            direction: 方向（in=入边, out=出边, both=双向）
            
        Returns:
            List[Tuple[GraphNode, GraphEdge]]: (邻居节点, 连接边) 列表
        """
        pass
    
    @abstractmethod
    def traverse(
        self,
        start_id: str,
        max_depth: int = 2,
        edge_types: Optional[List[str]] = None
    ) -> List[GraphNode]:
        """
        图遍历
        
        Args:
            start_id: 起始节点ID
            max_depth: 最大深度
            edge_types: 边类型过滤
            
        Returns:
            List[GraphNode]: 遍历到的节点列表
        """
        pass
    
    @abstractmethod
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[GraphNode]]:
        """
        查找两节点间的路径
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            max_depth: 最大搜索深度
            
        Returns:
            Optional[List[GraphNode]]: 路径节点列表或None
        """
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """
        删除节点（及相关边）
        
        Args:
            node_id: 节点ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool:
        """
        删除边
        
        Args:
            edge_id: 边ID
            
        Returns:
            bool: 是否成功
        """
        pass
    
    @abstractmethod
    def node_count(self) -> int:
        """返回节点总数"""
        pass
    
    @abstractmethod
    def edge_count(self) -> int:
        """返回边总数"""
        pass
    
    def search_nodes(
        self,
        name_pattern: Optional[str] = None,
        node_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[GraphNode]:
        """
        搜索节点
        
        Args:
            name_pattern: 名称模式匹配
            node_type: 节点类型
            properties: 属性过滤
            limit: 返回数量限制
            
        Returns:
            List[GraphNode]: 匹配的节点列表
        """
        raise NotImplementedError("search_nodes() not implemented")
