"""
Perception Engine - 感知引擎主类
"""

from typing import List, Optional
from src.perception.parser import DocumentParser
from src.perception.chunker import ChunkStrategy
from src.perception.tagger import ContextualTagger
from src.perception.encoder import VectorEncoder
from src.perception.models import ParsedDocument, EncodedChunk, Chunk
import uuid


class PerceptionEngine:
    """
    Perception Engine - 感知引擎
    
    多模态数据的高精度编码与情境标记
    """
    
    def __init__(
        self,
        model: str = "BGE-M3",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        enable_ocr: bool = True
    ):
        """
        初始化引擎
        
        Args:
            model: 向量化模型
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            enable_ocr: 是否启用 OCR
        """
        self.parser = DocumentParser(enable_ocr=enable_ocr)
        self.chunker = ChunkStrategy(chunk_size, chunk_overlap)
        self.tagger = ContextualTagger()
        self.encoder = VectorEncoder(model_name=model)
    
    def parse_document(self, file_path: str) -> ParsedDocument:
        """
        解析文档
        
        Args:
            file_path: 文档路径
            
        Returns:
            ParsedDocument: 解析后的文档
        """
        return self.parser.parse(file_path)
    
    def process(self, parsed_doc: ParsedDocument) -> List[EncodedChunk]:
        """
        处理解析后的文档，生成编码块
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            List[EncodedChunk]: 编码后的文本块列表
        """
        encoded_chunks = []
        
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
                    "chunk_index": chunk.index
                }
            )
            
            encoded_chunks.append(encoded_chunk)
        
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
    
    def process_text(self, text: str) -> List[EncodedChunk]:
        """
        处理纯文本
        
        Args:
            text: 文本内容
            
        Returns:
            List[EncodedChunk]: 编码后的文本块列表
        """
        # 分块
        chunks = self.chunker.chunk_by_fixed_size(text)
        
        # 创建临时文档
        parsed_doc = ParsedDocument(
            file_path="text_input",
            content=text,
            chunks=chunks
        )
        
        # 处理
        return self.process(parsed_doc)
