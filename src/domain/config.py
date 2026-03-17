"""
NecoRAG 领域配置模块

定义领域知识、关键字词典和权重配置
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
import json
import os


class KeywordLevel(Enum):
    """关键字权重等级"""
    CORE = "core"              # 核心关键字: 1.5-2.0
    IMPORTANT = "important"    # 重要关键字: 1.2-1.5
    NORMAL = "normal"          # 普通关键字: 1.0
    PERIPHERAL = "peripheral"  # 边缘关键字: 0.5-0.8


class DomainLevel(Enum):
    """领域相关性等级"""
    CORE = "core"              # 核心领域: 1.5
    RELATED = "related"        # 相关领域: 1.0-1.2
    PERIPHERAL = "peripheral"  # 边缘领域: 0.6-0.8
    OUT_OF_DOMAIN = "out"      # 领域外: 0.2-0.4


@dataclass
class KeywordConfig:
    """关键字配置"""
    keyword: str
    level: KeywordLevel
    weight: float
    aliases: List[str] = field(default_factory=list)  # 同义词/别名
    description: str = ""
    
    def __post_init__(self):
        """验证权重范围"""
        weight_ranges = {
            KeywordLevel.CORE: (1.5, 2.0),
            KeywordLevel.IMPORTANT: (1.2, 1.5),
            KeywordLevel.NORMAL: (0.9, 1.1),
            KeywordLevel.PERIPHERAL: (0.5, 0.8),
        }
        min_w, max_w = weight_ranges.get(self.level, (0.1, 2.0))
        if not (min_w <= self.weight <= max_w):
            # 自动修正到范围内
            self.weight = max(min_w, min(max_w, self.weight))


@dataclass
class DomainConfig:
    """领域配置"""
    domain_name: str                           # 领域名称
    domain_id: str                             # 领域唯一标识
    description: str = ""                      # 领域描述
    keywords: Dict[str, KeywordConfig] = field(default_factory=dict)
    related_domains: List[str] = field(default_factory=list)  # 相关领域ID
    
    # 权重系数配置
    keyword_factor: float = 1.0     # α: 关键字权重因子系数
    temporal_factor: float = 1.0    # β: 时间权重因子系数
    domain_factor: float = 1.0      # γ: 领域权重因子系数
    
    # 时间衰减配置
    decay_rate: float = 0.001       # λ: 衰减系数 (每天)
    enable_temporal_decay: bool = True
    
    # 领域权重配置
    core_domain_weight: float = 1.5
    related_domain_weight: float = 1.1
    peripheral_domain_weight: float = 0.7
    out_of_domain_weight: float = 0.3
    
    def add_keyword(self, keyword: str, level: KeywordLevel, 
                    weight: float, aliases: List[str] = None,
                    description: str = "") -> None:
        """添加关键字"""
        config = KeywordConfig(
            keyword=keyword,
            level=level,
            weight=weight,
            aliases=aliases or [],
            description=description
        )
        self.keywords[keyword.lower()] = config
        # 同时为别名建立索引
        for alias in config.aliases:
            self.keywords[alias.lower()] = config
    
    def get_keyword_weight(self, keyword: str) -> float:
        """获取关键字权重"""
        config = self.keywords.get(keyword.lower())
        return config.weight if config else 1.0
    
    def get_all_keywords(self) -> Set[str]:
        """获取所有关键字（包括别名）"""
        return set(self.keywords.keys())
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "domain_name": self.domain_name,
            "domain_id": self.domain_id,
            "description": self.description,
            "keywords": {
                k: {
                    "keyword": v.keyword,
                    "level": v.level.value,
                    "weight": v.weight,
                    "aliases": v.aliases,
                    "description": v.description
                }
                for k, v in self.keywords.items()
                if k == v.keyword.lower()  # 只保存原始关键字，不保存别名
            },
            "related_domains": self.related_domains,
            "keyword_factor": self.keyword_factor,
            "temporal_factor": self.temporal_factor,
            "domain_factor": self.domain_factor,
            "decay_rate": self.decay_rate,
            "enable_temporal_decay": self.enable_temporal_decay,
            "core_domain_weight": self.core_domain_weight,
            "related_domain_weight": self.related_domain_weight,
            "peripheral_domain_weight": self.peripheral_domain_weight,
            "out_of_domain_weight": self.out_of_domain_weight,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DomainConfig":
        """从字典创建"""
        config = cls(
            domain_name=data["domain_name"],
            domain_id=data["domain_id"],
            description=data.get("description", ""),
            related_domains=data.get("related_domains", []),
            keyword_factor=data.get("keyword_factor", 1.0),
            temporal_factor=data.get("temporal_factor", 1.0),
            domain_factor=data.get("domain_factor", 1.0),
            decay_rate=data.get("decay_rate", 0.001),
            enable_temporal_decay=data.get("enable_temporal_decay", True),
            core_domain_weight=data.get("core_domain_weight", 1.5),
            related_domain_weight=data.get("related_domain_weight", 1.1),
            peripheral_domain_weight=data.get("peripheral_domain_weight", 0.7),
            out_of_domain_weight=data.get("out_of_domain_weight", 0.3),
        )
        
        # 加载关键字
        for kw_data in data.get("keywords", {}).values():
            config.add_keyword(
                keyword=kw_data["keyword"],
                level=KeywordLevel(kw_data["level"]),
                weight=kw_data["weight"],
                aliases=kw_data.get("aliases", []),
                description=kw_data.get("description", "")
            )
        
        return config


class DomainConfigManager:
    """领域配置管理器"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.path.join(
            os.path.dirname(__file__), "configs"
        )
        self.domains: Dict[str, DomainConfig] = {}
        self.active_domain: Optional[DomainConfig] = None
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
    
    def create_domain(self, domain_name: str, domain_id: str,
                      description: str = "") -> DomainConfig:
        """创建新领域配置"""
        config = DomainConfig(
            domain_name=domain_name,
            domain_id=domain_id,
            description=description
        )
        self.domains[domain_id] = config
        return config
    
    def get_domain(self, domain_id: str) -> Optional[DomainConfig]:
        """获取领域配置"""
        return self.domains.get(domain_id)
    
    def set_active_domain(self, domain_id: str) -> bool:
        """设置当前活动领域"""
        if domain_id in self.domains:
            self.active_domain = self.domains[domain_id]
            return True
        return False
    
    def get_active_domain(self) -> Optional[DomainConfig]:
        """获取当前活动领域"""
        return self.active_domain
    
    def save_domain(self, domain_id: str) -> bool:
        """保存领域配置到文件"""
        config = self.domains.get(domain_id)
        if not config:
            return False
        
        filepath = os.path.join(self.config_dir, f"{domain_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    
    def load_domain(self, domain_id: str) -> Optional[DomainConfig]:
        """从文件加载领域配置"""
        filepath = os.path.join(self.config_dir, f"{domain_id}.json")
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        config = DomainConfig.from_dict(data)
        self.domains[domain_id] = config
        return config
    
    def load_all_domains(self) -> List[DomainConfig]:
        """加载所有领域配置"""
        loaded = []
        if os.path.exists(self.config_dir):
            for filename in os.listdir(self.config_dir):
                if filename.endswith(".json"):
                    domain_id = filename[:-5]
                    config = self.load_domain(domain_id)
                    if config:
                        loaded.append(config)
        return loaded
    
    def list_domains(self) -> List[str]:
        """列出所有领域ID"""
        return list(self.domains.keys())


def create_example_domain() -> DomainConfig:
    """创建示例领域配置（AI/机器学习领域）"""
    config = DomainConfig(
        domain_name="人工智能与机器学习",
        domain_id="ai_ml",
        description="涵盖人工智能、机器学习、深度学习等相关领域的知识体系"
    )
    
    # 添加核心关键字
    core_keywords = [
        ("深度学习", ["deep learning", "DL"], "神经网络多层学习方法"),
        ("机器学习", ["machine learning", "ML"], "从数据中学习的算法"),
        ("神经网络", ["neural network", "NN"], "模拟生物神经网络的计算模型"),
        ("大语言模型", ["LLM", "large language model"], "大规模预训练语言模型"),
        ("RAG", ["检索增强生成", "retrieval augmented generation"], "结合检索的生成方法"),
        ("Transformer", ["注意力机制"], "基于自注意力的模型架构"),
    ]
    for kw, aliases, desc in core_keywords:
        config.add_keyword(kw, KeywordLevel.CORE, 1.8, aliases, desc)
    
    # 添加重要关键字
    important_keywords = [
        ("向量数据库", ["vector database", "向量库"], "存储和检索向量的数据库"),
        ("嵌入模型", ["embedding model", "向量化模型"], "将文本转换为向量的模型"),
        ("知识图谱", ["knowledge graph", "KG"], "结构化知识表示"),
        ("微调", ["fine-tuning", "精调"], "在预训练模型基础上调整"),
        ("提示工程", ["prompt engineering"], "优化提示词的技术"),
    ]
    for kw, aliases, desc in important_keywords:
        config.add_keyword(kw, KeywordLevel.IMPORTANT, 1.3, aliases, desc)
    
    # 添加普通关键字
    normal_keywords = [
        ("GPU", ["显卡", "图形处理器"], "并行计算硬件"),
        ("Python", [], "主流编程语言"),
        ("训练", ["training"], "模型学习过程"),
        ("推理", ["inference"], "模型预测过程"),
    ]
    for kw, aliases, desc in normal_keywords:
        config.add_keyword(kw, KeywordLevel.NORMAL, 1.0, aliases, desc)
    
    return config
