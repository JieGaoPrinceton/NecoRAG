"""
向量编码器

生成多类型向量表示：稠密向量、稀疏向量、实体三元组
支持依赖注入 LLM 客户端以便替换不同的向量化实现。
"""

from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
import re

# 尝试导入 numpy，如果不可用则使用纯 Python 实现
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from src.perception.models import Chunk

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class VectorEncoder:
    """
    向量编码器
    
    生成稠密向量、稀疏向量、实体三元组。
    支持通过 LLM 客户端进行向量化，也支持独立运行（使用内置实现）。
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        model_name: str = "BGE-M3",
        vector_dimension: int = 768
    ):
        """
        初始化编码器
        
        Args:
            llm_client: LLM 客户端（可选，用于向量化）
            model_name: 向量化模型名称
            vector_dimension: 向量维度
        """
        self._llm_client = llm_client
        self._model_name = model_name
        self._vector_dimension = vector_dimension
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(
                    model_name=f"mock-{model_name}",
                    embedding_dim=vector_dimension
                )
            except ImportError:
                # 如果 core 模块不可用，使用内置实现
                self._llm_client = None
    
    @property
    def model_name(self) -> str:
        """返回模型名称"""
        return self._model_name
    
    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return self._vector_dimension
    
    def encode(self, text: str) -> Tuple[List[float], Dict[str, float], List[Tuple]]:
        """
        编码文本，生成多类型表示
        
        Args:
            text: 文本内容
            
        Returns:
            Tuple: (稠密向量, 稀疏向量, 实体三元组)
        """
        dense = self.encode_dense(text)
        sparse = self.encode_sparse(text)
        entities = self.extract_entities(text)
        
        return dense, sparse, entities
    
    def encode_dense(self, text: str) -> List[float]:
        """
        生成稠密向量
        
        Args:
            text: 文本内容
            
        Returns:
            List[float]: 稠密向量
        """
        # 优先使用 LLM 客户端
        if self._llm_client is not None:
            return self._llm_client.embed(text)
        
        # 回退到内置实现
        return self._builtin_dense_encode(text)
    
    def encode_dense_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成稠密向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[List[float]]: 稠密向量列表
        """
        if self._llm_client is not None:
            return self._llm_client.embed_batch(texts)
        
        return [self._builtin_dense_encode(text) for text in texts]
    
    def encode_sparse(self, text: str) -> Dict[str, float]:
        """
        生成稀疏向量（关键词权重）
        
        使用 TF-IDF 风格的词频统计。
        
        Args:
            text: 文本内容
            
        Returns:
            Dict[str, float]: 关键词权重字典
        """
        # 分词：支持中英文
        words = self._tokenize(text)
        
        # 统计词频
        word_freq: Dict[str, int] = {}
        for word in words:
            if self._is_valid_token(word):
                word_freq[word] = word_freq.get(word, 0) + 1
        
        if not word_freq:
            return {}
        
        # 归一化
        max_freq = max(word_freq.values())
        return {word: freq / max_freq for word, freq in word_freq.items()}
    
    def extract_entities(self, text: str) -> List[Tuple[str, str, str]]:
        """
        提取实体三元组 (主体, 关系, 客体)
        
        使用简单的规则提取，可通过 LLM 客户端增强。
        
        Args:
            text: 文本内容
            
        Returns:
            List[Tuple]: 实体三元组列表
        """
        entities = []
        
        # 简单的模式匹配提取
        # 模式: "A 是 B" / "A is B"
        patterns = [
            r'([^，。,\.\s]+)是([^，。,\.\s]+)',
            r'([A-Za-z\u4e00-\u9fff]+)\s+is\s+([A-Za-z\u4e00-\u9fff]+)',
            r'([^，。,\.\s]+)属于([^，。,\.\s]+)',
            r'([^，。,\.\s]+)包含([^，。,\.\s]+)',
        ]
        
        relation_map = {
            '是': 'is_a',
            'is': 'is_a',
            '属于': 'belongs_to',
            '包含': 'contains',
        }
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:
                    subject, obj = match
                    # 确定关系类型
                    for key, relation in relation_map.items():
                        if key in pattern:
                            entities.append((subject.strip(), relation, obj.strip()))
                            break
        
        return entities
    
    def _builtin_dense_encode(self, text: str) -> List[float]:
        """
        内置的稠密向量编码（确定性伪向量）
        
        基于文本哈希生成确定性向量，确保相同输入产生相同输出。
        """
        import hashlib
        import random
        
        # 使用文本哈希作为随机种子
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        
        # 生成单位向量
        vector = [rng.gauss(0, 1) for _ in range(self._vector_dimension)]
        
        # 归一化
        norm = sum(x*x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词（支持中英文）
        """
        # 简单分词：按空格和标点分割
        # 中文按字符分割，英文按单词分割
        tokens = []
        
        # 先按空格分割
        parts = text.lower().split()
        
        for part in parts:
            # 检查是否包含中文
            if re.search(r'[\u4e00-\u9fff]', part):
                # 中文：按字符分割（简化处理）
                chinese_chars = re.findall(r'[\u4e00-\u9fff]+', part)
                for chars in chinese_chars:
                    # 双字词切分
                    for i in range(len(chars) - 1):
                        tokens.append(chars[i:i+2])
            else:
                # 英文：整个单词
                word = re.sub(r'[^\w]', '', part)
                if word:
                    tokens.append(word)
        
        return tokens
    
    def _is_valid_token(self, token: str) -> bool:
        """
        检查是否为有效的 token
        """
        # 过滤停用词和过短的词
        stopwords = {
            '的', '了', '是', '在', '和', '与', '或', '这', '那', '有',
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'to', 'of', 'in', 'for', 'on', 'with', 'as', 'at', 'by'
        }
        
        return len(token) >= 2 and token not in stopwords
