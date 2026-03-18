# NecoRAG 插件扩展模块

## 概述

插件模块为NecoRAG提供可扩展的架构，支持动态加载和管理各种功能插件，包括感知层、记忆层、检索层、巩固层和响应层插件。

## 功能特性

### 🔌 插件管理
- 动态插件注册和发现
- 依赖关系解析和管理
- 生命周期控制（加载/卸载/启用/禁用）
- 插件配置管理

### 🎯 插件类型
- **感知层插件**：数据预处理、格式转换
- **记忆层插件**：数据存储、缓存管理
- **检索层插件**：搜索算法、索引管理
- **巩固层插件**：数据验证、质量控制
- **响应层插件**：输出格式化、结果呈现

### ⚡ 事件系统
- 事件发布/订阅机制
- 插件间通信
- 系统状态通知

## 快速开始

### 1. 安装依赖
```bash
pip install setuptools
```

### 2. 基本使用

```python
from src.plugins import plugin_manager, plugin_registry

# 发现插件
plugin_manager.discover_and_register_plugins()

# 加载插件
configs = {
    "text_preprocessor": {"normalize_case": True},
    "simple_cache": {},
    "keyword_retrieval": {}
}
results = plugin_manager.load_plugins(configs)

# 使用插件
preprocessor = plugin_registry.get_plugin("text_preprocessor")
if preprocessor:
    processed_text = preprocessor.process_input("Hello World!", {})

# 卸载插件
plugin_manager.unload_plugins(["text_preprocessor"])
```

### 3. 创建自定义插件

```python
from src.plugins.base import PerceptionPlugin

class MyCustomPlugin(PerceptionPlugin):
    def __init__(self):
        super().__init__(
            plugin_id="my_custom_plugin",
            name="我的自定义插件",
            version="1.0.0"
        )
    
    @property
    def description(self) -> str:
        return "这是一个自定义插件示例"
    
    @property
    def dependencies(self) -> List[str]:
        return []  # 依赖的其他插件
    
    def _initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    def _cleanup(self) -> bool:
        # 清理逻辑
        return True
    
    def process_input(self, data: Any, context: Dict[str, Any]) -> Any:
        # 处理逻辑
        return data
```

## API参考

### PluginManager
主要的插件管理接口

```python
# 批量加载插件
load_plugins(plugin_configs: Dict[str, Dict]) -> Dict[str, bool]

# 批量卸载插件
unload_plugins(plugin_ids: List[str] = None) -> Dict[str, bool]

# 启用/禁用插件
enable_plugins(plugin_ids: List[str]) -> Dict[str, bool]
disable_plugins(plugin_ids: List[str]) -> Dict[str, bool]

# 事件处理
register_event_handler(event_name: str, handler: Callable)
emit_event(event_name: str, data: Any = None) -> List[Any]

# 获取插件信息
get_plugins_by_type(plugin_type: PluginType) -> List[BasePlugin]
get_plugin_info(plugin_id: str) -> Optional[Dict[str, Any]]
```

### PluginRegistry
插件注册表管理

```python
# 注册/注销插件
register_plugin(plugin_class: Type[BasePlugin]) -> bool
unregister_plugin(plugin_id: str) -> bool

# 加载/卸载插件实例
load_plugin(plugin_id: str, config: Dict = None) -> Optional[BasePlugin]
unload_plugin(plugin_id: str) -> bool

# 插件发现
discover_plugins(search_paths: List[str] = None) -> int

# 获取插件信息
list_plugins(plugin_type: PluginType = None) -> List[Dict[str, Any]]
```

## 插件开发指南

### 1. 选择合适的基类
根据插件功能选择对应的基类：
- `PerceptionPlugin`：感知层处理
- `MemoryPlugin`：记忆层存储
- `RetrievalPlugin`：检索层搜索
- `RefinementPlugin`：巩固层处理
- `ResponsePlugin`：响应层输出

### 2. 实现必要方法
```python
class MyPlugin(BasePlugin):
    @property
    def description(self) -> str:
        """插件描述"""
        pass
    
    @property
    def dependencies(self) -> List[str]:
        """依赖的插件列表"""
        pass
    
    def _initialize(self) -> bool:
        """初始化逻辑"""
        pass
    
    def _cleanup(self) -> bool:
        """清理逻辑"""
        pass
```

### 3. 配置管理
```python
# 获取配置
config_value = self.get_config("key", default_value)

# 设置配置
self.set_config("key", value)
```

### 4. 日志记录
```python
# 使用内置logger
self.logger.info("信息日志")
self.logger.error("错误日志")
self.logger.debug("调试日志")
```

## 示例插件

模块包含以下示例插件：

1. **TextPreprocessorPlugin**：文本预处理插件
2. **SimpleCachePlugin**：简单缓存插件
3. **KeywordRetrievalPlugin**：关键词检索插件
4. **DataValidatorPlugin**：数据验证插件
5. **ResponseFormatterPlugin**：响应格式化插件

## 性能考虑

### 插件加载优化
- 按依赖关系排序加载
- 支持懒加载机制
- 提供加载状态监控

### 内存管理
- 及时清理不需要的插件实例
- 支持插件资源的显式释放
- 监控内存使用情况

## 故障排除

### 常见问题

1. **插件加载失败**
   - 检查插件类是否正确继承基类
   - 验证_required_方法是否正确实现
   - 查看日志了解具体错误信息

2. **依赖循环**
   - 检查插件间的依赖关系
   - 使用依赖解析工具分析
   - 重新设计插件架构

3. **性能问题**
   - 监控插件执行时间
   - 分析资源使用情况
   - 考虑异步处理机制

## 贡献指南

欢迎提交新的插件实现和改进建议！

### 插件提交要求
1. 遵循插件基类规范
2. 提供完整的文档说明
3. 包含单元测试
4. 通过代码质量检查

## 许可证

MIT License