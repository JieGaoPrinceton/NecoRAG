"""
LLM 客户端抽象基类

从 core.base 重新导出，并提供额外的工具函数。
"""

from abc import ABC, abstractmethod
from typing import List, AsyncIterator, Optional, Dict, Any


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类（同步版本）"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本
        """
        pass
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        文本向量化
        
        Args:
            text: 文本内容
            
        Returns:
            List[float]: 向量
        """
        pass
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化（默认实现：逐个调用）
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        return [self.embed(text) for text in texts]
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名称"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """返回嵌入向量维度"""
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        估算 token 数量（默认实现：简单估算）
        
        Args:
            text: 文本内容
            
        Returns:
            int: 估算的 token 数
        """
        # 简单估算：中文约 1.5 字符/token，英文约 4 字符/token
        return max(1, len(text) // 3)


class BaseAsyncLLMClient(ABC):
    """LLM 客户端抽象基类（异步版本）"""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """异步生成文本"""
        pass
    
    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式生成文本（默认实现：一次性返回）
        """
        result = await self.generate(prompt, **kwargs)
        yield result
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """异步文本向量化"""
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量异步向量化"""
        import asyncio
        tasks = [self.embed(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回模型名称"""
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """返回嵌入向量维度"""
        pass


# 工具函数

def create_prompt(
    system: str,
    user: str,
    history: Optional[List[Dict[str, str]]] = None,
    format_type: str = "simple"
) -> str:
    """
    创建标准格式的提示词
    
    Args:
        system: 系统提示
        user: 用户消息
        history: 对话历史 [{"role": "user/assistant", "content": "..."}]
        format_type: 格式类型 (simple, chat, instruct)
        
    Returns:
        str: 格式化后的提示词
    """
    if format_type == "simple":
        return f"{system}\n\n{user}"
    
    elif format_type == "chat":
        parts = [f"System: {system}"]
        if history:
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                parts.append(f"{role}: {msg['content']}")
        parts.append(f"User: {user}")
        parts.append("Assistant:")
        return "\n\n".join(parts)
    
    elif format_type == "instruct":
        parts = [
            f"### System:\n{system}",
            f"### User:\n{user}",
            "### Assistant:"
        ]
        return "\n\n".join(parts)
    
    return f"{system}\n\n{user}"
