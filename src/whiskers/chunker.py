"""
分块策略
支持多种分块模式
"""

from typing import List
from src.whiskers.models import Chunk


class ChunkStrategy:
    """
    分块策略
    
    支持语义分块、固定大小分块、结构分块等
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        初始化分块策略
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 分块重叠长度
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_by_semantic(self, content: str) -> List[Chunk]:
        """
        语义分块
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
            
        TODO: 实现基于语义相似度的智能分块
        """
        # 最小实现：按段落分割
        paragraphs = content.split('\n\n')
        chunks = []
        current_pos = 0
        
        for i, para in enumerate(paragraphs):
            if para.strip():
                start = content.find(para, current_pos)
                chunks.append(Chunk(
                    content=para.strip(),
                    index=i,
                    start_char=start,
                    end_char=start + len(para)
                ))
                current_pos = start + len(para)
        
        return chunks
    
    def chunk_by_fixed_size(self, content: str, size: int = None) -> List[Chunk]:
        """
        固定大小分块
        
        Args:
            content: 文本内容
            size: 块大小（None 则使用默认值）
            
        Returns:
            List[Chunk]: 文本块列表
        """
        chunk_size = size or self.chunk_size
        chunks = []
        
        for i in range(0, len(content), chunk_size - self.chunk_overlap):
            chunk_content = content[i:i + chunk_size]
            if chunk_content.strip():
                chunks.append(Chunk(
                    content=chunk_content,
                    index=len(chunks),
                    start_char=i,
                    end_char=min(i + chunk_size, len(content))
                ))
        
        return chunks
    
    def chunk_by_structure(self, content: str) -> List[Chunk]:
        """
        结构化分块（基于标题、段落等）
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
            
        TODO: 实现基于文档结构的分块
        """
        # 最小实现：按段落分割
        return self.chunk_by_semantic(content)
