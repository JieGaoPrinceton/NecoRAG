"""
Dashboard 数据模型
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class ModuleType(Enum):
    """模块类型"""
    PERCEPTION = "perception"
    MEMORY = "memory"
    RETRIEVAL = "retrieval"
    REFINEMENT = "refinement"
    RESPONSE = "response"


@dataclass
class ModuleConfig:
    """模块配置"""
    module_type: ModuleType
    module_name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['module_type'] = self.module_type.value
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModuleConfig':
        """从字典创建"""
        # 子类 (PerceptionConfig 等) 使用无参构造，只需恢复参数和状态
        if cls is not ModuleConfig:
            instance = cls()
            if 'parameters' in data:
                instance.parameters = data['parameters']
            if 'enabled' in data:
                instance.enabled = data['enabled']
            if 'last_updated' in data:
                instance.last_updated = datetime.fromisoformat(data['last_updated'])
            return instance
        data = dict(data)
        data['module_type'] = ModuleType(data['module_type'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class PerceptionConfig(ModuleConfig):
    """Perception Engine 配置"""
    def __init__(self):
        super().__init__(
            module_type=ModuleType.PERCEPTION,
            module_name="Perception Engine",
            description="感知引擎 - 多模态数据的高精度编码与情境标记",
            parameters={
                "chunk_size": 512,
                "chunk_overlap": 50,
                "enable_ocr": True,
                "sentiment_model": "default",
                "entity_extractor": "default",
                "vector_model": "BGE-M3",
                "vector_size": 1024,
            }
        )


@dataclass
class MemoryConfig(ModuleConfig):
    """Memory 配置"""
    def __init__(self):
        super().__init__(
            module_type=ModuleType.MEMORY,
            module_name="Hierarchical Memory",
            description="层级记忆 - 分层存储与管理",
            parameters={
                # L1 配置
                "l1_ttl": 3600,
                "l1_max_session_items": 1000,
                "l1_lru_max_size": 10000,
                # L2 配置
                "l2_vector_size": 1024,
                "l2_collection_name": "necorag",
                "l2_index_type": "HNSW",
                # L3 配置
                "l3_max_relation_depth": 5,
                "l3_enable_causal_graph": True,
                # 衰减配置
                "decay_rate": 0.1,
                "archive_threshold": 0.05,
                "consolidation_interval": 3600,
            }
        )


@dataclass
class RetrievalConfig(ModuleConfig):
    """Retrieval 配置"""
    def __init__(self):
        super().__init__(
            module_type=ModuleType.RETRIEVAL,
            module_name="Adaptive Retrieval",
            description="自适应检索 - 智能化信息检索与重排序",
            parameters={
                "top_k": 10,
                "min_score": 0.3,
                "max_hops": 3,
                "hyde_enabled": True,
                "reranker_model": "BGE-Reranker-v2",
                "novelty_weight": 0.3,
                "diversity_weight": 0.2,
                "redundancy_penalty": 0.4,
                "confidence_threshold": 0.85,
                "min_gain": 0.05,
                "max_iterations": 3,
            }
        )


@dataclass
class RefinementConfig(ModuleConfig):
    """Refinement 配置"""
    def __init__(self):
        super().__init__(
            module_type=ModuleType.REFINEMENT,
            module_name="Refinement Agent",
            description="精炼代理 - 知识固化、幻觉自检与记忆修剪",
            parameters={
                "min_confidence": 0.7,
                "max_iterations": 3,
                "hallucination_threshold": 0.6,
                "consolidation_interval": 3600,
                "min_query_frequency": 5,
                "gap_fill_strategy": "auto",
                "noise_threshold": 0.1,
                "quality_threshold": 0.3,
                "outdated_days": 90,
            }
        )


@dataclass
class ResponseConfig(ModuleConfig):
    """Response 配置"""
    def __init__(self):
        super().__init__(
            module_type=ModuleType.RESPONSE,
            module_name="Response Interface",
            description="响应接口 - 情境自适应生成与可解释性输出",
            parameters={
                "default_tone": "friendly",
                "default_detail_level": 2,
                "profile_ttl": 86400,
                "max_history": 100,
                "style_detection": True,
                "auto_detect": True,
                "personality_injection": True,
                "show_trace": True,
                "show_evidence": True,
                "show_reasoning": True,
            }
        )


@dataclass
class RAGProfile:
    """RAG 配置 Profile"""
    profile_id: str
    profile_name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = False
    perception_config: PerceptionConfig = field(default_factory=PerceptionConfig)
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
    retrieval_config: RetrievalConfig = field(default_factory=RetrievalConfig)
    refinement_config: RefinementConfig = field(default_factory=RefinementConfig)
    response_config: ResponseConfig = field(default_factory=ResponseConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "profile_id": self.profile_id,
            "profile_name": self.profile_name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "perception_config": self.perception_config.to_dict(),
            "memory_config": self.memory_config.to_dict(),
            "retrieval_config": self.retrieval_config.to_dict(),
            "refinement_config": self.refinement_config.to_dict(),
            "response_config": self.response_config.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RAGProfile':
        """从字典创建"""
        return cls(
            profile_id=data['profile_id'],
            profile_name=data['profile_name'],
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_active=data.get('is_active', False),
            perception_config=PerceptionConfig.from_dict(data['perception_config']),
            memory_config=MemoryConfig.from_dict(data['memory_config']),
            retrieval_config=RetrievalConfig.from_dict(data['retrieval_config']),
            refinement_config=RefinementConfig.from_dict(data['refinement_config']),
            response_config=ResponseConfig.from_dict(data['response_config']),
        )
    
    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'RAGProfile':
        """从 JSON 创建"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class DashboardStats:
    """Dashboard 统计信息"""
    total_documents: int = 0
    total_chunks: int = 0
    total_queries: int = 0
    active_sessions: int = 0
    memory_usage: Dict[str, int] = field(default_factory=dict)
    query_history: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
