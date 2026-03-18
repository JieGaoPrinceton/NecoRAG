"""LLM 客户端扩展基类

从 core.base 继承基础 LLM 客户端抽象, 并提供默认实现和工具函数。
消除重复定义, 统一到 core.base 作为抽象来源。
"""

from typing import List, AsyncIterator, Optional, Dict, Any

# 从核心抽象层导入基类（唯一的抽象定义来源）
from src.core.base import (
    BaseLLMClient as _CoreBaseLLMClient,
    BaseAsyncLLMClient as _CoreBaseAsyncLLMClient
)


class BaseLLMClient(_CoreBaseLLMClient):
    """
    LLM 客户端扩展基类（同步版本）
    
    继承自 core.base.BaseLLMClient，提供默认实现和工具方法。
    子类需要实现：generate, embed, model_name, embedding_dimension
    """
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量文本向量化（默认实现：逐个调用）
        
        覆盖父类的抽象方法，提供默认实现。
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 向量列表
        """
        return [self.embed(text) for text in texts]
    
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


class BaseAsyncLLMClient(_CoreBaseAsyncLLMClient):
    """
    LLM 客户端扩展基类（异步版本）
    
    继承自 core.base.BaseAsyncLLMClient，提供默认实现。
    子类需要实现：generate, embed
    """
    
    async def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式生成文本（默认实现：一次性返回）
        
        覆盖父类的抽象方法，提供默认实现。
        """
        result = await self.generate(prompt, **kwargs)
        yield result
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量异步向量化（默认实现）"""
        import asyncio
        tasks = [self.embed(text) for text in texts]
        return await asyncio.gather(*tasks)


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
