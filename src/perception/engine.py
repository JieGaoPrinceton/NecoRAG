"""
Perception Engine - 感知引擎主类
支持弹性文档切割和多种分块策略
"""

from typing import List, Optional
import logging
import time
from src.perception.parser import DocumentParser
from src.perception.chunker import ChunkStrategy
from src.perception.tagger import ContextualTagger
from src.perception.encoder import VectorEncoder
from src.perception.models import ParsedDocument, EncodedChunk, Chunk
import uuid


logger = logging.getLogger(__name__)


class PerceptionEngine:
    """
    Perception Engine - 感知引擎
    
    多模态数据的高精度编码与情境标记
    支持弹性切割、语义切割、固定大小切割等多种模式
    """
    
    def __init__(
        self,
        model: str = "BGE-M3",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        enable_ocr: bool = True,
        # 弹性切割配置参数
        min_chunk_size: int = 1024,
        target_chunk_size: int = 2048,
        max_chunk_size: int = 5120,
        enable_elastic_chunking: bool = True,
        chunk_strategy: str = "elastic",
        semantic_boundaries: Optional[List[str]] = None
    ):
        """
        初始化引擎
        
        Args:
            model: 向量化模型
            chunk_size: 基础分块大小（兼容模式）
            chunk_overlap: 分块重叠长度
            enable_ocr: 是否启用 OCR
            min_chunk_size: 弹性切割最小块大小
            target_chunk_size: 弹性切割目标块大小
            max_chunk_size: 弹性切割最大块大小
            enable_elastic_chunking: 是否启用弹性切割
            chunk_strategy: 默认切割策略 (elastic, semantic, fixed, structural, sentence)
            semantic_boundaries: 语义边界优先级
        """
        self.parser = DocumentParser(enable_ocr=enable_ocr)
        
        # 初始化分块策略，传入弹性切割配置
        self.chunker = ChunkStrategy(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
            target_chunk_size=target_chunk_size,
            max_chunk_size=max_chunk_size,
            enable_elastic=enable_elastic_chunking,
            semantic_boundaries=semantic_boundaries
        )
        
        self.tagger = ContextualTagger()
        self.encoder = VectorEncoder(model_name=model)
        
        # 保存默认切割策略
        self.chunk_strategy = chunk_strategy
        self.enable_elastic_chunking = enable_elastic_chunking
    
    def parse_document(self, file_path: str) -> ParsedDocument:
        """
        解析文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            ParsedDocument: 解析后的文档
        """
        logger.info(f"Parsing document: {file_path}")
        try:
            result = self.parser.parse(file_path)
            logger.info(f"Document parsed successfully: {len(result.chunks)} chunks")
            return result
        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {e}", exc_info=True)
            raise
    
    def process(self, parsed_doc: ParsedDocument) -> List[EncodedChunk]:
        """
        处理解析后的文档，生成编码块
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            List[EncodedChunk]: 编码后的文本块列表
        """
        _start = time.time()
        encoded_chunks = []
        
        logger.debug(f"Processing {len(parsed_doc.chunks)} chunks from {parsed_doc.file_path}")
        
        for chunk in parsed_doc.chunks:
            # 编码
            dense, sparse, entities = self.encoder.encode(chunk.content)
            
            # 生成情境标签
            context_tags = self.tagger.generate_tags(chunk)
            
            # 创建编码块
            encoded_chunk = EncodedChunk(
                content=chunk.content,
                chunk_id=str(uuid.uuid4()),
                dense_vector=dense,
                sparse_vector=sparse,
                entities=entities,
                context_tags=context_tags,
                metadata={
                    **chunk.metadata,
                    "source_file": parsed_doc.file_path,
                    "chunk_index": chunk.position
                }
            )
            
            encoded_chunks.append(encoded_chunk)
        
        _elapsed = time.time() - _start
        logger.debug(f"Encoding completed: {len(encoded_chunks)} chunks in {_elapsed:.3f}s")
        
        return encoded_chunks
    
    def process_file(self, file_path: str) -> List[EncodedChunk]:
        """
        一站式处理：解析文档 + 编码 + 打标
        
        Args:
            file_path: 文档路径
            
        Returns:
            List[EncodedChunk]: 编码后的文本块列表
        """
        # 解析文档
        parsed_doc = self.parse_document(file_path)
        
        # 处理并编码
        return self.process(parsed_doc)
    
    def process_text(
        self, 
        text: str, 
        strategy: Optional[str] = None
    ) -> List[EncodedChunk]:
        """
        处理纯文本
        
        使用统一入口进行分块，支持多种切割策略。
        
        Args:
            text: 文本内容
            strategy: 切割策略（可选）
                - "elastic": 弹性切割（智能调整块大小）
                - "semantic": 语义切割（按段落）
                - "fixed": 固定大小切割
                - "structural": 结构化切割
                - "sentence": 句子级切割
                - None: 使用默认策略
            
        Returns:
            List[EncodedChunk]: 编码后的文本块列表
        """
        # 使用统一入口进行分块，根据配置选择策略
        effective_strategy = strategy or self.chunk_strategy
        logger.info(f"Processing text with strategy: {effective_strategy}")
        chunks = self.chunker.chunk(text, strategy=effective_strategy)
        
        logger.info(f"Text chunked into {len(chunks)} chunks")
        
        # 创建临时文档
        parsed_doc = ParsedDocument(
            file_path="text_input",
            content=text,
            chunks=chunks
        )
        
        # 处理
        return self.process(parsed_doc)
