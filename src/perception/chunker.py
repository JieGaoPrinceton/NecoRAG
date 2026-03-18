"""
分块策略
支持多种分块模式，包括弹性分块、语义分块、固定大小分块等
"""

import re
from typing import List, Optional, Tuple
from src.perception.models import Chunk


class ChunkStrategy:
    """
    分块策略
    
    支持弹性分块、语义分块、固定大小分块、结构分块、句子分块等多种模式
    """
    
    def __init__(
        self, 
        chunk_size: int = 512, 
        chunk_overlap: int = 50,
        min_chunk_size: int = 1024,
        target_chunk_size: int = 2048,
        max_chunk_size: int = 5120,
        enable_elastic: bool = True,
        semantic_boundaries: Optional[List[str]] = None
    ):
        """
        初始化分块策略
        
        Args:
            chunk_size: 固定分块大小（兼容模式使用）
            chunk_overlap: 分块重叠长度
            min_chunk_size: 弹性分块最小块大小（字符），避免碎片化
            target_chunk_size: 弹性分块目标块大小（字符），理想切割大小
            max_chunk_size: 弹性分块最大块大小（字符），超过则强制切割
            enable_elastic: 是否启用弹性切割
            semantic_boundaries: 语义边界优先级列表，如 ["paragraph", "sentence", "clause"]
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.enable_elastic = enable_elastic
        self.semantic_boundaries = semantic_boundaries or ["paragraph", "sentence", "clause"]
    
    def chunk(self, content: str, strategy: Optional[str] = None) -> List[Chunk]:
        """
        统一分块入口方法
        
        根据指定策略对文本进行分块，默认使用弹性分块。
        
        Args:
            content: 文本内容
            strategy: 分块策略，可选值：
                - "elastic": 弹性分块（默认）
                - "semantic": 语义分块（按段落）
                - "fixed": 固定大小分块
                - "structural": 结构化分块
                - "sentence": 句子级分块
                - None: 根据 enable_elastic 配置自动选择
        
        Returns:
            List[Chunk]: 文本块列表
        """
        # 如果未指定策略，根据配置选择默认策略
        if strategy is None:
            strategy = "elastic" if self.enable_elastic else "fixed"
        
        # 根据策略路由到对应方法
        strategy_methods = {
            "elastic": self.chunk_by_elastic,
            "semantic": self.chunk_by_semantic,
            "fixed": self.chunk_by_fixed_size,
            "structural": self.chunk_by_structure,
            "sentence": self.chunk_by_sentence,
        }
        
        method = strategy_methods.get(strategy)
        if method is None:
            raise ValueError(f"不支持的分块策略: {strategy}，支持的策略: {list(strategy_methods.keys())}")
        
        return method(content)
    
    # ============== 弹性分块核心实现 ==============
    
    def chunk_by_elastic(self, content: str) -> List[Chunk]:
        """
        弹性分块
        
        智能调整块大小，在语义边界处切割，保证每个块在合理大小范围内。
        
        算法流程：
        1. 按段落分割文本
        2. 合并过小的段落（< min_chunk_size）
        3. 拆分过大的段落（> max_chunk_size）
        4. 添加重叠上下文
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
        """
        if not content or not content.strip():
            return []
        
        # 第一步：按段落分割
        paragraphs = self._split_into_paragraphs(content)
        
        # 第二步：合并过小的段落
        merged = self._merge_small_chunks(paragraphs, self.min_chunk_size, self.target_chunk_size)
        
        # 第三步：拆分过大的段落
        final_texts = []
        for text in merged:
            if len(text) > self.max_chunk_size:
                final_texts.extend(self._split_large_chunk(text, self.max_chunk_size))
            else:
                final_texts.append(text)
        
        # 第四步：添加重叠并创建 Chunk 对象
        chunk_data = self._add_overlap(final_texts, self.chunk_overlap)
        
        # 构建 Chunk 列表
        chunks = []
        for i, (text, start, end) in enumerate(chunk_data):
            chunks.append(Chunk(
                content=text,
                index=i,
                start_char=start,
                end_char=end,
                metadata={
                    "chunk_strategy": "elastic",
                    "semantic_boundary": self._detect_boundary_type(text)
                }
            ))
        
        return chunks
    
    def chunk_by_sentence(self, content: str) -> List[Chunk]:
        """
        句子级分块
        
        按句子边界分割文本，每个句子作为一个独立的块。
        支持中英文句子分割。
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
        """
        if not content or not content.strip():
            return []
        
        sentences = self._split_into_sentences(content)
        chunks = []
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                # 计算在原文中的位置
                start = content.find(sentence, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(sentence)
                
                chunks.append(Chunk(
                    content=sentence.strip(),
                    index=i,
                    start_char=start,
                    end_char=end,
                    metadata={
                        "chunk_strategy": "sentence",
                        "semantic_boundary": "sentence"
                    }
                ))
                current_pos = end
        
        return chunks
    
    def chunk_by_semantic(self, content: str) -> List[Chunk]:
        """
        语义分块
        
        按段落分割文本，保持语义完整性。
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
        """
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
                    end_char=start + len(para),
                    metadata={
                        "chunk_strategy": "semantic",
                        "semantic_boundary": "paragraph"
                    }
                ))
                current_pos = start + len(para)
        
        return chunks
    
    def chunk_by_fixed_size(self, content: str, size: int = None) -> List[Chunk]:
        """
        固定大小分块
        
        使用滑动窗口按固定大小切割文本。
        
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
                    end_char=min(i + chunk_size, len(content)),
                    metadata={
                        "chunk_strategy": "fixed",
                        "semantic_boundary": "none"
                    }
                ))
        
        return chunks
    
    def chunk_by_structure(self, content: str) -> List[Chunk]:
        """
        结构化分块（基于标题、段落等）
        
        Args:
            content: 文本内容
            
        Returns:
            List[Chunk]: 文本块列表
        """
        # 使用语义分块作为基础实现
        chunks = self.chunk_by_semantic(content)
        # 更新 metadata
        for chunk in chunks:
            chunk.metadata["chunk_strategy"] = "structural"
        return chunks
    
    # ============== 辅助方法 ==============
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        将文本按段落分割
        
        使用双换行符作为段落分隔符。
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 段落列表
        """
        # 按双换行符分割
        paragraphs = re.split(r'\n\s*\n', text)
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本按句子分割
        
        支持中英文标点：
        - 中文：。！？
        - 英文：. ! ?
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 句子列表
        """
        # 中英文句子分割正则
        # 匹配句号、感叹号、问号后的位置（但不切割缩写如 Mr. Dr. 等）
        sentence_pattern = r'(?<=[。！？.!?])\s*(?=[^.!?。！？]|$)'
        
        # 先用简单分割
        sentences = re.split(sentence_pattern, text)
        
        # 清理和过滤
        result = []
        for s in sentences:
            s = s.strip()
            if s:
                result.append(s)
        
        return result
    
    def _split_into_clauses(self, text: str) -> List[str]:
        """
        将文本按子句分割
        
        使用逗号、分号等作为分隔符，支持中英文：
        - 中文：，、；
        - 英文：, ;
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 子句列表
        """
        # 中英文子句分割
        clause_pattern = r'[，,；;、]'
        clauses = re.split(clause_pattern, text)
        return [c.strip() for c in clauses if c.strip()]
    
    def _merge_small_chunks(
        self, 
        paragraphs: List[str], 
        min_size: int, 
        target_size: int
    ) -> List[str]:
        """
        合并过小的段落
        
        将小于 min_size 的段落向后合并，直到接近 target_size。
        
        Args:
            paragraphs: 段落列表
            min_size: 最小块大小
            target_size: 目标块大小
            
        Returns:
            List[str]: 合并后的文本块列表
        """
        if not paragraphs:
            return []
        
        merged = []
        current = paragraphs[0]
        
        for para in paragraphs[1:]:
            combined_len = len(current) + len(para) + 2  # +2 for "\n\n"
            
            # 如果当前块太小且合并后不会超过目标大小太多，则合并
            if len(current) < min_size and combined_len <= target_size * 1.2:
                current = current + "\n\n" + para
            # 如果当前块小于目标大小且合并后接近目标大小，也可以合并
            elif len(current) < target_size and combined_len <= target_size:
                current = current + "\n\n" + para
            else:
                # 保存当前块，开始新块
                if current.strip():
                    merged.append(current)
                current = para
        
        # 添加最后一个块
        if current.strip():
            merged.append(current)
        
        return merged
    
    def _split_large_chunk(self, text: str, max_size: int) -> List[str]:
        """
        拆分过大的文本块
        
        优先按句子边界拆分，然后按子句边界，最后强制在词边界切割。
        
        Args:
            text: 文本内容
            max_size: 最大块大小
            
        Returns:
            List[str]: 拆分后的文本块列表
        """
        if len(text) <= max_size:
            return [text]
        
        result = []
        remaining = text
        
        while len(remaining) > max_size:
            # 尝试在 max_size 范围内找到最后一个句子边界
            chunk = remaining[:max_size]
            
            # 优先级1：句子边界（。！？.!?）
            sentence_end = self._find_last_sentence_boundary(chunk)
            if sentence_end > max_size * 0.3:  # 确保不会切得太小
                result.append(remaining[:sentence_end].strip())
                remaining = remaining[sentence_end:].strip()
                continue
            
            # 优先级2：子句边界（，,；;）
            clause_end = self._find_last_clause_boundary(chunk)
            if clause_end > max_size * 0.3:
                result.append(remaining[:clause_end].strip())
                remaining = remaining[clause_end:].strip()
                continue
            
            # 优先级3：强制在词边界切割
            word_end = self._find_last_word_boundary(chunk)
            if word_end > max_size * 0.3:
                result.append(remaining[:word_end].strip())
                remaining = remaining[word_end:].strip()
                continue
            
            # 最后手段：强制在 max_size 处切割
            result.append(remaining[:max_size].strip())
            remaining = remaining[max_size:].strip()
        
        # 添加剩余部分
        if remaining.strip():
            result.append(remaining.strip())
        
        return result
    
    def _find_last_sentence_boundary(self, text: str) -> int:
        """
        找到文本中最后一个句子边界位置
        
        Args:
            text: 文本内容
            
        Returns:
            int: 边界位置，未找到返回 -1
        """
        # 中英文句子结束标点
        sentence_ends = ['。', '！', '？', '.', '!', '?']
        last_pos = -1
        
        for char in sentence_ends:
            pos = text.rfind(char)
            if pos > last_pos:
                last_pos = pos
        
        return last_pos + 1 if last_pos >= 0 else -1
    
    def _find_last_clause_boundary(self, text: str) -> int:
        """
        找到文本中最后一个子句边界位置
        
        Args:
            text: 文本内容
            
        Returns:
            int: 边界位置，未找到返回 -1
        """
        # 中英文子句结束标点
        clause_ends = ['，', '；', ',', ';', '、']
        last_pos = -1
        
        for char in clause_ends:
            pos = text.rfind(char)
            if pos > last_pos:
                last_pos = pos
        
        return last_pos + 1 if last_pos >= 0 else -1
    
    def _find_last_word_boundary(self, text: str) -> int:
        """
        找到文本中最后一个词边界位置
        
        对于英文，在空格处切割；对于中文，每个字符都可以是边界。
        
        Args:
            text: 文本内容
            
        Returns:
            int: 边界位置，未找到返回 -1
        """
        # 尝试找空格（英文词边界）
        space_pos = text.rfind(' ')
        if space_pos > 0:
            return space_pos
        
        # 如果没有空格，检查是否主要是 CJK 字符
        # CJK 字符每个都可以作为边界，直接返回文本长度的一半
        cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if cjk_count > len(text) * 0.3:
            return len(text) * 2 // 3  # 在 2/3 处切割
        
        return -1
    
    def _add_overlap(
        self, 
        chunks: List[str], 
        overlap_size: int
    ) -> List[Tuple[str, int, int]]:
        """
        在相邻块间添加重叠上下文
        
        Args:
            chunks: 文本块列表
            overlap_size: 重叠大小（字符数）
            
        Returns:
            List[Tuple[str, int, int]]: (文本, 起始位置, 结束位置) 元组列表
        """
        if not chunks:
            return []
        
        result = []
        current_pos = 0
        
        for i, chunk in enumerate(chunks):
            start_pos = current_pos
            
            # 添加前一个块的末尾作为上下文（除了第一个块）
            if i > 0 and overlap_size > 0:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-overlap_size:] if len(prev_chunk) > overlap_size else prev_chunk
                chunk_with_overlap = overlap_text + " " + chunk
            else:
                chunk_with_overlap = chunk
            
            end_pos = start_pos + len(chunk)
            result.append((chunk_with_overlap, start_pos, end_pos))
            current_pos = end_pos + 2  # 加上段落分隔符的长度
        
        return result
    
    def _detect_boundary_type(self, text: str) -> str:
        """
        检测文本使用的语义边界类型
        
        Args:
            text: 文本内容
            
        Returns:
            str: 边界类型（paragraph, sentence, clause, forced）
        """
        # 检查是否包含多个段落
        if '\n\n' in text or '\n' in text:
            return "paragraph"
        
        # 检查是否有句子结束标点
        sentence_ends = ['。', '！', '？', '.', '!', '?']
        for char in sentence_ends:
            if char in text[:-1]:  # 排除最后一个字符
                return "sentence"
        
        # 检查是否有子句标点
        clause_ends = ['，', '；', ',', ';']
        for char in clause_ends:
            if char in text:
                return "clause"
        
        return "forced"
