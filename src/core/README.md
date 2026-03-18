# ⚙️ NecoRAG 核心基础模块

## 📋 目录说明

本目录包含 NecoRAG 的核心基础组件，提供配置管理、协议定义和 LLM 适配等基础功能。

## 📁 文件结构

```
core/
├── __init__.py              # 包初始化与导出
├── config.py                # 配置管理器 ⭐
├── base.py                  # 基类定义
├── protocols.py             # 协议接口
└── llm/                     # LLM 适配层
    ├── __init__.py
    ├── provider.py          # LLM 提供商抽象
    └── adapter.py           # LLM 适配器
```

## 🎯 核心组件

### 1. [config.py](./config.py) - 配置管理器 ⭐

**功能**: 全局配置管理与参数验证

**主要类**:
```python
class NecoRAGConfig:
    """NecoRAG 全局配置"""
    
    def __init__(
        self,
        # 记忆层配置
        memory_ttl: int = 3600,
        vector_size: int = 1024,
        
        # 检索层配置
        top_k: int = 10,
        rerank_enabled: bool = True,
        
        # 交互层配置
        detail_level: int = 2,
        show_trace: bool = True,
        
        # 多用户配置
        multi_user: bool = False,
        privacy_mode: bool = False
    ):
        pass
```

**特性**:
- ✅ 类型安全（Pydantic 验证）
- ✅ 默认值合理
- ✅ 支持从文件加载
- ✅ 支持环境变量覆盖

**使用示例**:
```python
from src.core.config import NecoRAGConfig

# 创建默认配置
config = NecoRAGConfig()

# 自定义配置
config = NecoRAGConfig(
    top_k=20,
    memory_ttl=7200,
    multi_user=True
)

# 从文件加载
config = NecoRAGConfig.from_yaml("config.yaml")
```

### 2. [base.py](./base.py) - 基类定义

**功能**: 定义所有模块的基础抽象类

**核心基类**:
```python
class BaseModule(ABC):
    """所有模块的基类"""
    
    @abstractmethod
    def initialize(self):
        """初始化模块"""
        pass
    
    @abstractmethod
    def shutdown(self):
        """关闭模块"""
        pass
    
    def health_check(self) -> bool:
        """健康检查"""
        pass


class BaseEngine(BaseModule):
    """引擎类基类（Perception, Retrieval 等）"""
    
    @abstractmethod
    def process(self, input_data) -> Any:
        """处理输入数据"""
        pass


class BaseManager(BaseModule):
    """管理器类基类（Memory, User 等）"""
    
    @abstractmethod
    def get(self, key: str) -> Any:
        """获取数据"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any):
        """设置数据"""
        pass
```

### 3. [protocols.py](./protocols.py) - 协议接口

**功能**: 定义模块间通信协议

**核心协议**:
```python
@runtime_checkable
class Queryable(Protocol):
    """可查询协议"""
    
    def query(self, text: str, **kwargs) -> List[Result]:
        ...


class Storable(Protocol):
    """可存储协议"""
    
    def store(self, data: Any, metadata: Dict):
        ...
    
    def retrieve(self, query: str) -> List[Any]:
        ...


class Processable(Protocol):
    """可处理协议"""
    
    def process(self, input: Any) -> Any:
        ...
    
    def validate(self, output: Any) -> bool:
        ...
```

### 4. [llm/](./llm/) - LLM 适配层

**功能**: 统一不同 LLM 提供商的接口

**支持的提供商**:
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- 阿里巴巴（千问 3.5）⭐ 中文优化
- LLaMA3/Mistral（本地部署）
- 其他兼容 OpenAI API 的模型

**适配器模式**:
```python
from src.core.llm import create_llm_adapter

# 创建适配器（自动根据配置选择）
llm = create_llm_adapter(provider="openai")
llm = create_llm_adapter(provider="qwen")  # 千问 3.5

# 统一接口
response = llm.generate("你的提示词")
embedding = llm.embed("文本")
```

## 🔧 配置系统详解

### 配置层级

1. **默认配置**: 代码中定义的合理默认值
2. **文件配置**: YAML/JSON 配置文件
3. **环境变量**: `.env` 文件或系统环境变量
4. **运行时配置**: 程序运行时动态调整

### 配置优先级

```
运行时配置 > 环境变量 > 文件配置 > 默认配置
```

### 环境变量映射

```python
# .env 示例
APP_ENV=production
LOG_LEVEL=INFO
MEMORY_TTL=7200
TOP_K=15
MULTI_USER=true
```

对应关系:
```
APP_ENV → config.env
LOG_LEVEL → config.log_level
MEMORY_TTL → config.memory_ttl
TOP_K → config.retrieval.top_k
MULTI_USER → config.multi_user
```

## 🎨 设计模式

### 1. 单例模式 - 配置管理

```python
class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. 工厂模式 - LLM 创建

```python
def create_llm_adapter(provider: str) -> BaseLLM:
    """LLM 工厂函数"""
    providers = {
        "openai": OpenAIAdapter,
        "qwen": QwenAdapter,
        "claude": ClaudeAdapter,
    }
    
    adapter_class = providers.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown provider: {provider}")
    
    return adapter_class()
```

### 3. 策略模式 - 配置加载

```python
class ConfigLoader:
    def load(self, path: str) -> Dict:
        if path.endswith(".yaml"):
            return self._load_yaml(path)
        elif path.endswith(".json"):
            return self._load_json(path)
        elif path.endswith(".env"):
            return self._load_env(path)
```

## 📊 性能优化

### 1. 配置缓存

```python
class CachedConfig:
    def __init__(self):
        self._cache = {}
        self._ttl = 60  # 60 秒缓存
    
    def get(self, key: str):
        if key in self._cache:
            cached_time, value = self._cache[key]
            if time.time() - cached_time < self._ttl:
                return value
        # 重新加载
        value = self._load_from_source(key)
        self._cache[key] = (time.time(), value)
        return value
```

### 2. 延迟加载

```python
class LazyConfig:
    def __init__(self):
        self._config = None
    
    @property
    def config(self):
        if self._config is None:
            self._config = self._load_config()
        return self._config
```

## 🧪 测试示例

### 单元测试

```python
# tests/test_core/test_config.py
def test_config_default():
    config = NecoRAGConfig()
    assert config.top_k == 10
    assert config.memory_ttl == 3600

def test_config_custom():
    config = NecoRAGConfig(top_k=20)
    assert config.top_k == 20

def test_config_validation():
    with pytest.raises(ValidationError):
        NecoRAGConfig(top_k=-1)  # 无效值
```

### 集成测试

```python
# tests/test_core/test_protocols.py
def test_queryable_protocol():
    class MockRetriever:
        def query(self, text: str) -> List[Result]:
            return [Result(text=text)]
    
    retriever = MockRetriever()
    assert isinstance(retriever, Queryable)
```

## 🐛 常见问题

### Q1: 配置不生效？

**排查步骤**:
```python
# 1. 检查配置加载顺序
print(config.source)  # 查看配置来源

# 2. 检查环境变量
import os
print(os.getenv("TOP_K"))

# 3. 检查配置文件路径
from pathlib import Path
print(Path("config.yaml").exists())
```

### Q2: LLM 连接失败？

**解决方案**:
```python
# 1. 检查 API Key
from src.core.llm import check_api_key
assert check_api_key("openai")

# 2. 测试连接
llm = create_llm_adapter("openai")
try:
    llm.generate("test")
    print("Connection OK")
except Exception as e:
    print(f"Connection failed: {e}")
```

### Q3: 类型验证失败？

**调试方法**:
```python
from pydantic import ValidationError

try:
    config = NecoRAGConfig(top_k="invalid")
except ValidationError as e:
    print(e.errors())  # 查看详细错误信息
```

## 📚 API 参考

### 配置类完整参数

```python
NecoRAGConfig(
    # 基础配置
    env: str = "development",
    log_level: str = "INFO",
    
    # 感知层配置
    perception: PerceptionConfig = PerceptionConfig(),
    
    # 记忆层配置
    memory_ttl: int = 3600,
    vector_size: int = 1024,
    l1_max_items: int = 1000,
    
    # 检索层配置
    retrieval: RetrievalConfig = RetrievalConfig(),
    top_k: int = 10,
    min_score: float = 0.3,
    
    # 巩固层配置
    refinement: RefinementConfig = RefinementConfig(),
    min_confidence: float = 0.7,
    
    # 交互层配置
    response: ResponseConfig = ResponseConfig(),
    detail_level: int = 2,
    show_trace: bool = True,
    
    # 多用户配置
    multi_user: bool = False,
    privacy_mode: bool = False,
    
    # 领域配置
    domain_keywords: Dict[str, List[str]] = None,
    
    # 安全配置
    auth_enabled: bool = True,
    jwt_secret: str = None
)
```

## 🔗 相关链接

- [配置使用指南](../../docs/wiki/配置管理/配置概览.md)
- [LLM 适配详情](../../docs/wiki/核心架构设计/LLM 适配层.md)
- [协议设计文档](../../design/architecture_framework.md)

## 📞 维护信息

**负责人**: Core Team  
**最后更新**: 2026-03-19  
**测试覆盖率**: >90%  
**文档状态**: ✅ 完善

---

*核心基础模块是项目的基石，保持简洁、稳定、高效是我们的设计原则。*
