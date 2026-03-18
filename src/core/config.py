"""
NecoRAG 统一配置管理

提供全局配置类和模块配置基类，支持从文件、环境变量加载配置。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Type, TypeVar
from enum import Enum
import os
import json
from pathlib import Path


T = TypeVar('T', bound='BaseConfig')


class LLMProvider(Enum):
    """LLM 提供商"""
    MOCK = "mock"           # 演示用Mock
    OPENAI = "openai"       # OpenAI API
    OLLAMA = "ollama"       # 本地 Ollama
    VLLM = "vllm"           # vLLM 服务
    AZURE = "azure"         # Azure OpenAI
    ANTHROPIC = "anthropic" # Claude


class VectorDBProvider(Enum):
    """向量数据库提供商"""
    MEMORY = "memory"       # 内存存储
    QDRANT = "qdrant"       # Qdrant
    MILVUS = "milvus"       # Milvus
    CHROMA = "chroma"       # ChromaDB


class GraphDBProvider(Enum):
    """图数据库提供商"""
    MEMORY = "memory"       # 内存存储
    NEO4J = "neo4j"         # Neo4j
    NEBULA = "nebula"       # NebulaGraph


# ============== 基础配置类 ==============

@dataclass
class BaseConfig:
    """配置基类"""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """从字典创建"""
        return cls(**data)
    
    def save(self, path: str):
        """保存到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls: Type[T], path: str) -> T:
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# ============== LLM 配置 ==============

@dataclass
class LLMConfig(BaseConfig):
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.MOCK
    model_name: str = "mock-model"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 60
    
    # 嵌入模型配置
    embedding_model: str = "mock-embedding"
    embedding_dimension: int = 768
    
    def __post_init__(self):
        # 从环境变量加载 API Key
        if self.api_key is None:
            env_key = f"{self.provider.value.upper()}_API_KEY"
            self.api_key = os.environ.get(env_key)


# ============== 感知层配置 ==============

@dataclass
class PerceptionConfig(BaseConfig):
    """感知层配置"""
    # 分块配置
    chunk_size: int = 512
    chunk_overlap: int = 50
    chunk_strategy: str = "semantic"  # fixed, semantic, structural
    
    # 标签配置
    enable_time_tag: bool = True
    enable_emotion_tag: bool = True
    enable_importance_tag: bool = True
    enable_topic_tag: bool = True
    
    # 解析配置
    supported_formats: List[str] = field(
        default_factory=lambda: ["txt", "md", "pdf", "docx", "html"]
    )


# ============== 记忆层配置 ==============

@dataclass
class MemoryConfig(BaseConfig):
    """记忆层配置"""
    # L1 工作记忆配置
    working_memory_ttl: int = 3600  # 秒
    working_memory_max_items: int = 100
    
    # L2 语义记忆配置
    vector_db_provider: VectorDBProvider = VectorDBProvider.MEMORY
    vector_db_url: Optional[str] = None
    vector_collection_name: str = "necorag_semantic"
    
    # L3 情景图谱配置
    graph_db_provider: GraphDBProvider = GraphDBProvider.MEMORY
    graph_db_url: Optional[str] = None
    max_relation_depth: int = 5
    
    # 衰减配置
    decay_rate: float = 0.1
    decay_threshold: float = 0.1  # 低于此权重的记忆将被归档


# ============== 检索层配置 ==============

@dataclass
class RetrievalConfig(BaseConfig):
    """检索层配置"""
    # 基础检索配置
    default_top_k: int = 10
    vector_weight: float = 0.7
    graph_weight: float = 0.3
    
    # Pounce 机制配置
    enable_early_termination: bool = True
    confidence_threshold: float = 0.85
    min_results: int = 3
    
    # HyDE 配置
    enable_hyde: bool = True
    hyde_temperature: float = 0.5
    
    # 重排序配置
    enable_rerank: bool = True
    rerank_top_k: int = 20
    novelty_penalty: float = 0.1


# ============== 巩固层配置 ==============

@dataclass
class RefinementConfig(BaseConfig):
    """巩固层配置"""
    # Generator-Critic-Refiner 循环配置
    max_iterations: int = 3
    confidence_threshold: float = 0.8
    
    # 幻觉检测配置
    factual_threshold: float = 0.7
    logical_threshold: float = 0.7
    evidence_threshold: float = 0.6
    
    # 知识固化配置
    enable_consolidation: bool = True
    consolidation_interval: int = 3600  # 秒
    
    # 记忆修剪配置
    enable_pruning: bool = True
    pruning_threshold: float = 0.2


# ============== 响应层配置 ==============

@dataclass
class ResponseConfig(BaseConfig):
    """响应层配置"""
    # 默认响应风格
    default_tone: str = "professional"  # professional, friendly, humorous
    default_detail_level: int = 2  # 1-4
    
    # 思维链可视化
    enable_thinking_chain: bool = True
    show_retrieval_path: bool = True
    show_evidence_sources: bool = True
    
    # 输出格式
    output_format: str = "markdown"  # text, markdown, html


# ============== 领域配置 ==============

@dataclass
class DomainWeightConfig(BaseConfig):
    """领域权重配置"""
    # 权重因子
    keyword_factor: float = 1.0   # α: 关键字权重因子
    temporal_factor: float = 1.0  # β: 时间权重因子
    domain_factor: float = 1.0    # γ: 领域权重因子
    
    # 时间衰减
    decay_rate: float = 0.001  # λ: 每天衰减率
    evergreen_enabled: bool = True  # 是否启用常青知识


@dataclass
class KnowledgeEvolutionConfig(BaseConfig):
    """知识库更新与演化配置"""
    # 实时更新
    enable_realtime_update: bool = True
    realtime_quality_threshold: float = 0.6
    auto_approve_threshold: float = 0.85
    
    # 定时更新
    enable_scheduled_update: bool = True
    batch_update_interval: int = 86400  # 24小时
    
    # 变更日志
    enable_change_log: bool = True
    enable_rollback: bool = True
    
    # 健康度阈值
    health_warning_threshold: float = 60.0
    health_critical_threshold: float = 40.0
    
    # 查询驱动知识积累
    enable_query_driven_accumulation: bool = True


# ============== 全局配置 ==============

@dataclass
class NecoRAGConfig(BaseConfig):
    """NecoRAG 全局配置"""
    # 项目信息
    project_name: str = "NecoRAG"
    version: str = "1.0.0-alpha"
    debug: bool = False
    
    # 各层配置
    llm: LLMConfig = field(default_factory=LLMConfig)
    perception: PerceptionConfig = field(default_factory=PerceptionConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    refinement: RefinementConfig = field(default_factory=RefinementConfig)
    response: ResponseConfig = field(default_factory=ResponseConfig)
    domain_weight: DomainWeightConfig = field(default_factory=DomainWeightConfig)
    knowledge_evolution: KnowledgeEvolutionConfig = field(default_factory=KnowledgeEvolutionConfig)
    
    # 数据目录
    data_dir: str = "./data"
    config_dir: str = "./configs"
    log_dir: str = "./logs"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NecoRAGConfig":
        """从字典创建（递归处理子配置）"""
        # 处理枚举类型
        if 'llm' in data and isinstance(data['llm'], dict):
            if 'provider' in data['llm'] and isinstance(data['llm']['provider'], str):
                data['llm']['provider'] = LLMProvider(data['llm']['provider'])
            data['llm'] = LLMConfig(**data['llm'])
        
        if 'memory' in data and isinstance(data['memory'], dict):
            if 'vector_db_provider' in data['memory'] and isinstance(data['memory']['vector_db_provider'], str):
                data['memory']['vector_db_provider'] = VectorDBProvider(data['memory']['vector_db_provider'])
            if 'graph_db_provider' in data['memory'] and isinstance(data['memory']['graph_db_provider'], str):
                data['memory']['graph_db_provider'] = GraphDBProvider(data['memory']['graph_db_provider'])
            data['memory'] = MemoryConfig(**data['memory'])
        
        # 处理其他子配置
        config_classes = {
            'perception': PerceptionConfig,
            'retrieval': RetrievalConfig,
            'refinement': RefinementConfig,
            'response': ResponseConfig,
            'domain_weight': DomainWeightConfig,
            'knowledge_evolution': KnowledgeEvolutionConfig,
        }
        
        for key, config_class in config_classes.items():
            if key in data and isinstance(data[key], dict):
                data[key] = config_class(**data[key])
        
        return cls(**data)


# ============== 配置加载函数 ==============

def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = "NECORAG"
) -> NecoRAGConfig:
    """
    加载配置
    
    优先级：环境变量 > 配置文件 > 默认值
    
    Args:
        config_path: 配置文件路径
        env_prefix: 环境变量前缀
        
    Returns:
        NecoRAGConfig: 配置对象
    """
    config = NecoRAGConfig()
    
    # 从配置文件加载
    if config_path and Path(config_path).exists():
        config = NecoRAGConfig.load(config_path)
    
    # 从环境变量覆盖关键配置
    env_mappings = {
        f"{env_prefix}_DEBUG": ("debug", lambda x: x.lower() == "true"),
        f"{env_prefix}_LLM_PROVIDER": ("llm.provider", lambda x: LLMProvider(x)),
        f"{env_prefix}_LLM_MODEL": ("llm.model_name", str),
        f"{env_prefix}_LLM_API_KEY": ("llm.api_key", str),
        f"{env_prefix}_VECTOR_DB": ("memory.vector_db_provider", lambda x: VectorDBProvider(x)),
        f"{env_prefix}_VECTOR_DB_URL": ("memory.vector_db_url", str),
        f"{env_prefix}_GRAPH_DB": ("memory.graph_db_provider", lambda x: GraphDBProvider(x)),
        f"{env_prefix}_GRAPH_DB_URL": ("memory.graph_db_url", str),
    }
    
    for env_key, (config_path_str, converter) in env_mappings.items():
        env_value = os.environ.get(env_key)
        if env_value is not None:
            _set_nested_attr(config, config_path_str, converter(env_value))
    
    return config


def _set_nested_attr(obj: Any, path: str, value: Any):
    """设置嵌套属性"""
    parts = path.split('.')
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)


# ============== 预设配置 ==============

class ConfigPresets:
    """预设配置"""
    
    @staticmethod
    def development() -> NecoRAGConfig:
        """开发环境配置"""
        config = NecoRAGConfig(debug=True)
        config.llm.provider = LLMProvider.MOCK
        config.memory.vector_db_provider = VectorDBProvider.MEMORY
        config.memory.graph_db_provider = GraphDBProvider.MEMORY
        return config
    
    @staticmethod
    def production() -> NecoRAGConfig:
        """生产环境配置"""
        config = NecoRAGConfig(debug=False)
        config.refinement.max_iterations = 5
        config.retrieval.enable_rerank = True
        return config
    
    @staticmethod
    def minimal() -> NecoRAGConfig:
        """最小配置（快速启动）"""
        config = NecoRAGConfig()
        config.llm.provider = LLMProvider.MOCK
        config.retrieval.enable_hyde = False
        config.retrieval.enable_rerank = False
        config.refinement.max_iterations = 1
        config.response.enable_thinking_chain = False
        return config
