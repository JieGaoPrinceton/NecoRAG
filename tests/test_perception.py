# -*- coding: utf-8 -*-
"""
感知引擎测试 - 文档解析、分块、编码、标注
"""

import pytest
import numpy as np
from datetime import datetime

from src.perception import (
    PerceptionEngine,
    DocumentParser,
    ChunkStrategy,
    ContextualTagger,
    VectorEncoder,
)
from src.perception.models import Chunk, ParsedDocument, EncodedChunk, ContextTags


# ═══════════════════════════════════════════════════════════
# DocumentParser 测试
# ═══════════════════════════════════════════════════════════

class TestDocumentParser:
    """文档解析器测试"""

    def test_init(self):
        parser = DocumentParser()
        assert parser is not None

    def test_parse_text_file(self, temp_text_file):
        parser = DocumentParser()
        result = parser.parse(temp_text_file)
        assert isinstance(result, ParsedDocument)
        assert result.file_path == temp_text_file
        assert len(result.content) > 0
        assert result.parsed_at is not None

    def test_parse_returns_chunks(self, temp_text_file):
        parser = DocumentParser()
        result = parser.parse(temp_text_file)
        assert isinstance(result.chunks, list)

    def test_extract_tables(self):
        parser = DocumentParser()
        tables = parser.extract_tables("some content")
        assert isinstance(tables, list)

    def test_extract_images(self):
        parser = DocumentParser()
        images = parser.extract_images("some content")
        assert isinstance(images, list)


# ═══════════════════════════════════════════════════════════
# ChunkStrategy 测试
# ═══════════════════════════════════════════════════════════

class TestChunkStrategy:
    """分块策略测试"""

    def test_init(self):
        chunker = ChunkStrategy(chunk_size=256, chunk_overlap=30)
        assert chunker.chunk_size == 256
        assert chunker.chunk_overlap == 30

    def test_semantic_chunking(self, sample_text):
        chunker = ChunkStrategy()
        chunks = chunker.chunk_by_semantic(sample_text)
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_semantic_chunking_splits_paragraphs(self, sample_text):
        """语义分块按段落分割"""
        chunker = ChunkStrategy()
        chunks = chunker.chunk_by_semantic(sample_text)
        # 4 paragraphs separated by \n\n
        assert len(chunks) >= 2

    def test_fixed_size_chunking(self, sample_text):
        chunker = ChunkStrategy(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_by_fixed_size(sample_text, size=20)
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_fixed_size_with_overlap(self):
        text = "a" * 100
        chunker = ChunkStrategy(chunk_size=30, chunk_overlap=10)
        chunks = chunker.chunk_by_fixed_size(text, size=30)
        assert len(chunks) > 1

    def test_structure_chunking_fallback(self, sample_text):
        """结构分块应回退到语义分块"""
        chunker = ChunkStrategy()
        chunks = chunker.chunk_by_structure(sample_text)
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_chunk_has_correct_fields(self, sample_text):
        chunker = ChunkStrategy()
        chunks = chunker.chunk_by_semantic(sample_text)
        for chunk in chunks:
            assert hasattr(chunk, "content")
            assert hasattr(chunk, "index")
            assert hasattr(chunk, "start_char")
            assert hasattr(chunk, "end_char")
            assert hasattr(chunk, "metadata")


# ═══════════════════════════════════════════════════════════
# VectorEncoder 测试
# ═══════════════════════════════════════════════════════════

class TestVectorEncoder:
    """向量编码器测试"""

    def test_init(self):
        encoder = VectorEncoder()
        assert encoder is not None

    def test_encode_dense(self):
        encoder = VectorEncoder(vector_dimension=768)
        vector = encoder.encode_dense("测试文本")
        assert isinstance(vector, list)
        assert len(vector) == 768

    def test_encode_dense_deterministic(self):
        """相同文本应产生相同向量"""
        encoder = VectorEncoder(vector_dimension=768)
        v1 = encoder.encode_dense("相同文本")
        v2 = encoder.encode_dense("相同文本")
        assert v1 == v2

    def test_encode_sparse(self):
        encoder = VectorEncoder()
        sparse = encoder.encode_sparse("人工智能 机器学习 深度学习")
        assert isinstance(sparse, dict)
        assert len(sparse) > 0

    def test_extract_entities(self):
        encoder = VectorEncoder()
        entities = encoder.extract_entities("人工智能是计算机科学的分支")
        assert isinstance(entities, list)

    def test_encode_full(self):
        encoder = VectorEncoder(vector_dimension=768)
        dense, sparse, entities = encoder.encode("人工智能是重要的技术领域")
        assert isinstance(dense, list)
        assert isinstance(sparse, dict)
        assert isinstance(entities, list)

    def test_encode_dense_batch(self):
        encoder = VectorEncoder(vector_dimension=128)
        texts = ["文本一", "文本二", "文本三"]
        results = encoder.encode_dense_batch(texts)
        assert len(results) == 3
        for v in results:
            assert len(v) == 128


# ═══════════════════════════════════════════════════════════
# ContextualTagger 测试
# ═══════════════════════════════════════════════════════════

class TestContextualTagger:
    """上下文标注器测试"""

    def test_init(self):
        tagger = ContextualTagger()
        assert tagger is not None

    def test_generate_tags(self, sample_chunk):
        tagger = ContextualTagger()
        tags = tagger.generate_tags(sample_chunk)
        assert isinstance(tags, ContextTags)

    def test_sentiment_positive(self):
        tagger = ContextualTagger()
        chunk = Chunk(content="这个结果非常好，表现优秀", index=0, start_char=0, end_char=10, metadata={})
        tag = tagger.generate_sentiment_tag(chunk)
        assert tag == "positive"

    def test_sentiment_negative(self):
        tagger = ContextualTagger()
        chunk = Chunk(content="这是一个失败的项目，效果很差", index=0, start_char=0, end_char=10, metadata={})
        tag = tagger.generate_sentiment_tag(chunk)
        assert tag == "negative"

    def test_sentiment_neutral(self):
        tagger = ContextualTagger()
        chunk = Chunk(content="今天天气一般", index=0, start_char=0, end_char=6, metadata={})
        tag = tagger.generate_sentiment_tag(chunk)
        assert tag == "neutral"

    def test_importance_score(self, sample_chunk):
        tagger = ContextualTagger()
        score = tagger.generate_importance_tag(sample_chunk)
        assert 0 <= score <= 1

    def test_topic_tags(self, sample_chunk):
        tagger = ContextualTagger()
        topics = tagger.generate_topic_tags(sample_chunk)
        assert isinstance(topics, list)

    def test_time_tag(self, sample_chunk):
        tagger = ContextualTagger()
        time_tag = tagger.generate_time_tag(sample_chunk)
        # 可能返回 None 或字符串
        assert time_tag is None or isinstance(time_tag, str)


# ═══════════════════════════════════════════════════════════
# PerceptionEngine 集成测试
# ═══════════════════════════════════════════════════════════

class TestPerceptionEngine:
    """感知引擎集成测试"""

    def test_init(self):
        engine = PerceptionEngine()
        assert engine is not None

    def test_process_text(self, sample_text):
        engine = PerceptionEngine()
        results = engine.process_text(sample_text)
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, EncodedChunk) for r in results)

    def test_process_file(self, temp_text_file):
        engine = PerceptionEngine()
        results = engine.process_file(temp_text_file)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_encoded_chunk_fields(self, sample_text):
        engine = PerceptionEngine()
        results = engine.process_text(sample_text)
        for chunk in results:
            assert chunk.content is not None
            assert chunk.chunk_id is not None
            assert chunk.dense_vector is not None
            assert chunk.sparse_vector is not None
            assert chunk.context_tags is not None
            assert chunk.created_at is not None

    def test_parse_document(self, temp_text_file):
        engine = PerceptionEngine()
        doc = engine.parse_document(temp_text_file)
        assert isinstance(doc, ParsedDocument)
        assert doc.content is not None

    def test_process_parsed_doc(self, sample_parsed_doc):
        engine = PerceptionEngine()
        results = engine.process(sample_parsed_doc)
        assert isinstance(results, list)
        assert len(results) > 0
