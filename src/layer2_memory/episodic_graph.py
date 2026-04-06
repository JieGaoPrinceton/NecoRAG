"""
L3 情景图谱 (Neo4j/NebulaGraph)
实体关系网络，多跳推理与因果链条
"""

from typing import Dict, List, Optional
from .models import Entity, Relation, GraphPath


class EpisodicGraph:
    """
    L3 情景图谱
    
    特性：
    - 实体关系存储
    - 多跳推理
    - 因果链条追踪
    - 结构化记忆
    """
    
    def __init__(self, max_relation_depth: int = 5):
        """
        初始化情景图谱
        
        Args:
            max_relation_depth: 最大关系深度
        """
        self.max_relation_depth = max_relation_depth
        # 最小实现：使用内存图结构
        self._entities: Dict[str, Entity] = {}
        self._relations: Dict[str, List[Relation]] = {}  # source_id -> relations
    
    def add_entity(self, entity: Entity) -> str:
        """
        添加实体
        
        Args:
            entity: 实体对象
            
        Returns:
            str: 实体 ID
            
        TODO: 集成 Neo4j/NebulaGraph
        """
        self._entities[entity.entity_id] = entity
        if entity.entity_id not in self._relations:
            self._relations[entity.entity_id] = []
        return entity.entity_id
    
    def add_relation(self, source: str, target: str, relation: Relation) -> str:
        """
        添加关系
        
        Args:
            source: 源实体 ID
            target: 目标实体 ID
            relation: 关系对象
            
        Returns:
            str: 关系 ID
        """
        relation.source_id = source
        relation.target_id = target
        
        if source not in self._relations:
            self._relations[source] = []
        
        self._relations[source].append(relation)
        return f"{source}->{target}"
    
    def multi_hop_query(
        self,
        start_entity: str,
        hops: int = 3,
        relation_types: Optional[List[str]] = None
    ) -> List[GraphPath]:
        """
        多跳查询
        
        Args:
            start_entity: 起始实体 ID
            hops: 跳数
            relation_types: 关系类型过滤
            
        Returns:
            List[GraphPath]: 图谱路径列表
            
        TODO: 实现 BFS/DFS 多跳搜索
        """
        # 最小实现：简单的 BFS
        paths = []
        self._bfs(start_entity, hops, [], paths, relation_types)
        return paths
    
    def _bfs(
        self,
        current: str,
        remaining_hops: int,
        current_path: List[str],
        paths: List[GraphPath],
        relation_types: Optional[List[str]]
    ):
        """BFS 辅助函数"""
        if remaining_hops == 0:
            return
        
        relations = self._relations.get(current, [])
        
        for relation in relations:
            # 过滤关系类型
            if relation_types and relation.relation_type not in relation_types:
                continue
            
            new_path = current_path + [current, relation.target_id]
            
            # 创建 GraphPath
            graph_path = GraphPath(
                nodes=new_path,
                edges=current_path + [relation] if current_path else [relation],
                total_strength=1.0  # 简化实现
            )
            paths.append(graph_path)
            
            # 递归
            self._bfs(relation.target_id, remaining_hops - 1, new_path, paths, relation_types)
    
    def find_causal_chain(self, event: str) -> List[Relation]:
        """
        查找因果链条
        
        Args:
            event: 事件实体 ID
            
        Returns:
            List[Relation]: 因果关系链
            
        TODO: 实现因果关系追踪
        """
        # 最小实现：查找所有 "causes" 类型的关系
        causal_relations = []
        
        relations = self._relations.get(event, [])
        for relation in relations:
            if relation.relation_type in ["causes", "leads_to", "results_in"]:
                causal_relations.append(relation)
        
        return causal_relations
    
    def get_related_entities(
        self,
        entity_id: str,
        depth: int = 2
    ) -> List[Entity]:
        """
        获取相关实体
        
        Args:
            entity_id: 实体 ID
            depth: 搜索深度
            
        Returns:
            List[Entity]: 相关实体列表
        """
        visited = set()
        related = []
        
        def _traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            if current_id in self._entities and current_id != entity_id:
                related.append(self._entities[current_id])
            
            # 遍历出边
            for relation in self._relations.get(current_id, []):
                _traverse(relation.target_id, current_depth + 1)
        
        _traverse(entity_id, 0)
        return related
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        获取实体
        
        Args:
            entity_id: 实体 ID
            
        Returns:
            Optional[Entity]: 实体对象
        """
        return self._entities.get(entity_id)
