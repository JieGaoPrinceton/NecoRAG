"""
示例插件实现
展示如何创建不同类型的插件
"""

from typing import Dict, Any, List
from .base import (
    PerceptionPlugin, MemoryPlugin, RetrievalPlugin, 
    RefinementPlugin, ResponsePlugin, PluginType
)


# 示例：感知层插件 - 文本预处理
class TextPreprocessorPlugin(PerceptionPlugin):
    """文本预处理插件"""
    
    def __init__(self):
        super().__init__(
            plugin_id="text_preprocessor",
            name="文本预处理器",
            version="1.0.0"
        )
    
    @property
    def description(self) -> str:
        return "对输入文本进行预处理，包括清洗、标准化等操作"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def _initialize(self) -> bool:
        self.logger.info("Text preprocessor initialized")
        return True
    
    def _cleanup(self) -> bool:
        self.logger.info("Text preprocessor cleaned up")
        return True
    
    def process_input(self, data: str, context: Dict[str, Any]) -> str:
        """处理输入文本"""
        if not isinstance(data, str):
            return str(data)
        
        # 文本清洗
        cleaned_text = data.strip()
        
        # 标准化处理
        if self.get_config("normalize_case", True):
            cleaned_text = cleaned_text.lower()
        
        # 移除多余空白
        if self.get_config("remove_extra_spaces", True):
            cleaned_text = " ".join(cleaned_text.split())
        
        self.logger.debug(f"Processed text: {cleaned_text[:50]}...")
        return cleaned_text


# 示例：记忆层插件 - 简单缓存
class SimpleCachePlugin(MemoryPlugin):
    """简单缓存插件"""
    
    def __init__(self):
        super().__init__(
            plugin_id="simple_cache",
            name="简单缓存",
            version="1.0.0"
        )
        self._cache = {}
    
    @property
    def description(self) -> str:
        return "提供简单的键值对缓存功能"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def _initialize(self) -> bool:
        self._cache = {}
        self.logger.info("Simple cache initialized")
        return True
    
    def _cleanup(self) -> bool:
        self._cache.clear()
        self.logger.info("Simple cache cleaned up")
        return True
    
    def store(self, data: Any, metadata: Dict[str, Any]) -> str:
        """存储数据到缓存"""
        key = metadata.get("key", str(hash(str(data))))
        self._cache[key] = {
            "data": data,
            "metadata": metadata,
            "timestamp": metadata.get("timestamp")
        }
        self.logger.debug(f"Stored data with key: {key}")
        return key
    
    def retrieve(self, query: Any, **kwargs) -> List[Any]:
        """从缓存检索数据"""
        if isinstance(query, str) and query in self._cache:
            return [self._cache[query]["data"]]
        elif query is None:
            # 返回所有缓存项
            return [item["data"] for item in self._cache.values()]
        return []


# 示例：检索层插件 - 关键词检索
class KeywordRetrievalPlugin(RetrievalPlugin):
    """关键词检索插件"""
    
    def __init__(self):
        super().__init__(
            plugin_id="keyword_retrieval",
            name="关键词检索器",
            version="1.0.0"
        )
        self._documents = []
    
    @property
    def description(self) -> str:
        return "基于关键词匹配的简单检索插件"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def _initialize(self) -> bool:
        # 初始化示例文档
        self._documents = [
            {"id": "1", "content": "人工智能是计算机科学的一个分支", "keywords": ["人工智能", "计算机科学"]},
            {"id": "2", "content": "机器学习是人工智能的重要组成部分", "keywords": ["机器学习", "人工智能"]},
            {"id": "3", "content": "深度学习使用神经网络进行学习", "keywords": ["深度学习", "神经网络"]}
        ]
        self.logger.info("Keyword retrieval initialized with sample documents")
        return True
    
    def _cleanup(self) -> bool:
        self._documents = []
        self.logger.info("Keyword retrieval cleaned up")
        return True
    
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """执行关键词检索"""
        results = []
        query_keywords = query.lower().split()
        
        for doc in self._documents:
            # 计算匹配分数
            matched_keywords = [kw for kw in query_keywords if kw in doc["content"].lower()]
            score = len(matched_keywords) / len(query_keywords) if query_keywords else 0
            
            if score > 0:
                results.append({
                    "id": doc["id"],
                    "content": doc["content"],
                    "score": score,
                    "matched_keywords": matched_keywords
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        self.logger.debug(f"Found {len(results)} results for query: {query}")
        return results


# 示例：巩固层插件 - 数据验证
class DataValidatorPlugin(RefinementPlugin):
    """数据验证插件"""
    
    def __init__(self):
        super().__init__(
            plugin_id="data_validator",
            name="数据验证器",
            version="1.0.0"
        )
    
    @property
    def description(self) -> str:
        return "验证和清理检索到的数据"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def _initialize(self) -> bool:
        self.logger.info("Data validator initialized")
        return True
    
    def _cleanup(self) -> bool:
        self.logger.info("Data validator cleaned up")
        return True
    
    def refine(self, data: Any, context: Dict[str, Any]) -> Any:
        """验证数据"""
        if isinstance(data, list):
            # 验证列表中的每个项目
            validated_data = []
            for item in data:
                if self._validate_item(item):
                    validated_data.append(item)
            return validated_data
        elif isinstance(data, dict):
            # 验证字典
            if self._validate_item(data):
                return data
            else:
                return None
        else:
            # 简单验证
            return data if data else None
    
    def _validate_item(self, item: Any) -> bool:
        """验证单个项目"""
        if item is None:
            return False
        
        if isinstance(item, dict):
            # 检查必需字段
            required_fields = self.get_config("required_fields", [])
            for field in required_fields:
                if field not in item or not item[field]:
                    return False
        
        # 检查数据质量
        min_quality = self.get_config("min_quality", 0.5)
        quality = self._calculate_quality(item)
        
        return quality >= min_quality
    
    def _calculate_quality(self, item: Any) -> float:
        """计算数据质量分数"""
        if isinstance(item, dict):
            # 简单的质量计算：非空字段比例
            total_fields = len(item)
            non_empty_fields = sum(1 for v in item.values() if v)
            return non_empty_fields / total_fields if total_fields > 0 else 0
        return 1.0


# 示例：响应层插件 - 格式化输出
class ResponseFormatterPlugin(ResponsePlugin):
    """响应格式化插件"""
    
    def __init__(self):
        super().__init__(
            plugin_id="response_formatter",
            name="响应格式化器",
            version="1.0.0"
        )
    
    @property
    def description(self) -> str:
        return "格式化最终响应输出"
    
    @property
    def dependencies(self) -> List[str]:
        return []
    
    def _initialize(self) -> bool:
        self.logger.info("Response formatter initialized")
        return True
    
    def _cleanup(self) -> bool:
        self.logger.info("Response formatter cleaned up")
        return True
    
    def generate_response(self, data: Any, context: Dict[str, Any]) -> str:
        """生成格式化响应"""
        format_type = self.get_config("format", "text")
        
        if format_type == "json":
            import json
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == "markdown":
            return self._to_markdown(data)
        else:
            return self._to_text(data)
    
    def _to_text(self, data: Any) -> str:
        """转换为文本格式"""
        if isinstance(data, list):
            lines = []
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    lines.append(f"{i}. {item.get('content', str(item))}")
                else:
                    lines.append(f"{i}. {str(item)}")
            return "\n".join(lines)
        elif isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        else:
            return str(data)
    
    def _to_markdown(self, data: Any) -> str:
        """转换为Markdown格式"""
        if isinstance(data, list):
            lines = ["## 检索结果", ""]
            for i, item in enumerate(data, 1):
                if isinstance(item, dict):
                    lines.append(f"{i}. **{item.get('content', str(item))}**")
                    if 'score' in item:
                        lines.append(f"   匹配度: {item['score']:.2f}")
                else:
                    lines.append(f"{i}. {str(item)}")
                lines.append("")
            return "\n".join(lines)
        else:
            return f"## 响应\n\n{self._to_text(data)}"


# 注册示例插件
def register_example_plugins():
    """注册所有示例插件"""
    from .registry import plugin_registry
    
    example_plugins = [
        TextPreprocessorPlugin,
        SimpleCachePlugin,
        KeywordRetrievalPlugin,
        DataValidatorPlugin,
        ResponseFormatterPlugin
    ]
    
    for plugin_class in example_plugins:
        plugin_registry.register_plugin(plugin_class)