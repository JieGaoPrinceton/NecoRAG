"""
测试 NecoRAG 数据协议模块

测试内容：
- 所有统一数据模型的创建和字段验证
- Query, Chunk, Entity, Relation, Response, UserProfile 等
- 枚举类型测试
"""

import pytest
from datetime import datetime

from src.core.protocols import (
    # 枚举类型
    DocumentType,
    ChunkType,
    MemoryLayer,
    RetrievalSource,
    ResponseTone,
    DetailLevel,
    IntentType,
    # 文档相关
    Document,
    Chunk,
    ContextTag,
    # 向量相关
    Embedding,
    EncodedChunk,
    # 记忆相关
    Memory,
    Entity,
    Relation,
    # 查询相关
    Query,
    RetrievalResult,
    # 响应相关
    GeneratedAnswer,
    CritiqueResult,
    HallucinationReport,
    Response,
    # 用户相关
    UserProfile,
)


class TestEnumTypes:
    """枚举类型测试类"""
    
    def test_document_type_enum(self):
        """测试文档类型枚举"""
        assert DocumentType.TEXT.value == "text"
        assert DocumentType.PDF.value == "pdf"
        assert DocumentType.WORD.value == "word"
        assert DocumentType.MARKDOWN.value == "markdown"
        assert DocumentType.HTML.value == "html"
        assert DocumentType.JSON.value == "json"
        assert DocumentType.UNKNOWN.value == "unknown"
    
    def test_chunk_type_enum(self):
        """测试分块类型枚举"""
        assert ChunkType.FIXED.value == "fixed"
        assert ChunkType.SEMANTIC.value == "semantic"
        assert ChunkType.STRUCTURAL.value == "structural"
        assert ChunkType.ELASTIC.value == "elastic"
        assert ChunkType.SENTENCE.value == "sentence"
    
    def test_memory_layer_enum(self):
        """测试记忆层级枚举"""
        assert MemoryLayer.L1_WORKING.value == "working"
        assert MemoryLayer.L2_SEMANTIC.value == "semantic"
        assert MemoryLayer.L3_EPISODIC.value == "episodic"
    
    def test_retrieval_source_enum(self):
        """测试检索来源枚举"""
        assert RetrievalSource.VECTOR.value == "vector"
        assert RetrievalSource.GRAPH.value == "graph"
        assert RetrievalSource.HYDE.value == "hyde"
        assert RetrievalSource.HYBRID.value == "hybrid"
    
    def test_response_tone_enum(self):
        """测试响应语气枚举"""
        assert ResponseTone.PROFESSIONAL.value == "professional"
        assert ResponseTone.FRIENDLY.value == "friendly"
        assert ResponseTone.HUMOROUS.value == "humorous"
    
    def test_detail_level_enum(self):
        """测试详细程度枚举"""
        assert DetailLevel.BRIEF.value == 1
        assert DetailLevel.STANDARD.value == 2
        assert DetailLevel.DETAILED.value == 3
        assert DetailLevel.COMPREHENSIVE.value == 4
    
    def test_intent_type_enum(self):
        """测试意图类型枚举"""
        assert IntentType.FACTUAL.value == "factual"
        assert IntentType.COMPARATIVE.value == "comparative"
        assert IntentType.REASONING.value == "reasoning"
        assert IntentType.EXPLANATION.value == "explanation"
        assert IntentType.SUMMARIZATION.value == "summarization"
        assert IntentType.PROCEDURAL.value == "procedural"
        assert IntentType.EXPLORATORY.value == "exploratory"


class TestDocument:
    """Document 数据类测试"""
    
    def test_create_document_default(self):
        """测试创建默认文档"""
        doc = Document()
        
        assert doc.doc_id is not None
        assert doc.content == ""
        assert doc.doc_type == DocumentType.TEXT
        assert doc.file_path is None
        assert doc.title is None
        assert doc.metadata == {}
        assert isinstance(doc.created_at, datetime)
    
    def test_create_document_with_content(self, sample_document):
        """测试创建带内容的文档"""
        assert sample_document.doc_id == "test-doc-001"
        assert "测试文档" in sample_document.content
        assert sample_document.doc_type == DocumentType.TEXT
        assert sample_document.title == "测试文档"
        assert sample_document.metadata["source"] == "test"
    
    def test_document_auto_title_from_path(self):
        """测试从路径自动设置标题"""
        doc = Document(file_path="/path/to/document.txt")
        
        assert doc.title == "document.txt"


class TestChunk:
    """Chunk 数据类测试"""
    
    def test_create_chunk_default(self):
        """测试创建默认分块"""
        chunk = Chunk()
        
        assert chunk.chunk_id is not None
        assert chunk.content == ""
        assert chunk.doc_id is None
        assert chunk.chunk_type == ChunkType.FIXED
        assert chunk.position == 0
        assert chunk.metadata == {}
    
    def test_create_chunk_with_content(self, sample_chunks):
        """测试创建带内容的分块"""
        chunk = sample_chunks[0]
        
        assert chunk.chunk_id == "chunk-001"
        assert "第一个测试分块" in chunk.content
        assert chunk.doc_id == "test-doc-001"
        assert chunk.chunk_type == ChunkType.SEMANTIC
    
    def test_chunk_position_info(self):
        """测试分块位置信息"""
        chunk = Chunk(
            content="test",
            position=5,
            start_char=100,
            end_char=200
        )
        
        assert chunk.position == 5
        assert chunk.start_char == 100
        assert chunk.end_char == 200
    
    def test_chunk_linked_list(self):
        """测试分块链表结构"""
        chunk = Chunk(
            content="middle",
            prev_chunk_id="prev-001",
            next_chunk_id="next-001"
        )
        
        assert chunk.prev_chunk_id == "prev-001"
        assert chunk.next_chunk_id == "next-001"


class TestContextTag:
    """ContextTag 数据类测试"""
    
    def test_create_context_tag_default(self):
        """测试创建默认情境标签"""
        tag = ContextTag()
        
        assert tag.time_tag is None
        assert tag.emotion_tag is None
        assert tag.importance == 0.5
        assert tag.topics == []
        assert tag.entities == []
    
    def test_create_context_tag_with_values(self):
        """测试创建带值的情境标签"""
        tag = ContextTag(
            time_tag="2024-01",
            emotion_tag="neutral",
            importance=0.8,
            topics=["AI", "ML"],
            entities=["GPT", "Transformer"]
        )
        
        assert tag.time_tag == "2024-01"
        assert tag.emotion_tag == "neutral"
        assert tag.importance == 0.8
        assert "AI" in tag.topics
        assert "GPT" in tag.entities


class TestEmbedding:
    """Embedding 数据类测试"""
    
    def test_create_embedding_default(self):
        """测试创建默认嵌入"""
        emb = Embedding()
        
        assert emb.embedding_id is not None
        assert emb.chunk_id == ""
        assert emb.dense_vector == []
        assert emb.sparse_vector == {}
        assert emb.dimension == 0
    
    def test_embedding_auto_dimension(self):
        """测试嵌入自动计算维度"""
        emb = Embedding(
            dense_vector=[0.1, 0.2, 0.3, 0.4]
        )
        
        assert emb.dimension == 4
    
    def test_embedding_with_sparse_vector(self):
        """测试带稀疏向量的嵌入"""
        emb = Embedding(
            dense_vector=[0.1, 0.2],
            sparse_vector={"token1": 0.5, "token2": 0.3}
        )
        
        assert emb.sparse_vector["token1"] == 0.5


class TestEncodedChunk:
    """EncodedChunk 数据类测试"""
    
    def test_create_encoded_chunk(self):
        """测试创建编码分块"""
        ec = EncodedChunk(
            content="test content",
            dense_vector=[0.1, 0.2, 0.3],
            entities=[("subject", "relation", "object")]
        )
        
        assert ec.content == "test content"
        assert len(ec.dense_vector) == 3
        assert len(ec.entities) == 1


class TestMemory:
    """Memory 数据类测试"""
    
    def test_create_memory_default(self):
        """测试创建默认记忆"""
        mem = Memory()
        
        assert mem.memory_id is not None
        assert mem.content == ""
        assert mem.layer == MemoryLayer.L2_SEMANTIC
        assert mem.vector == []
        assert mem.weight == 1.0
        assert mem.access_count == 0
    
    def test_create_memory_with_content(self, sample_memory):
        """测试创建带内容的记忆"""
        assert sample_memory.memory_id == "memory-001"
        assert "深度学习" in sample_memory.content
        assert sample_memory.layer == MemoryLayer.L2_SEMANTIC
    
    def test_memory_update_access(self):
        """测试更新记忆访问信息"""
        mem = Memory(access_count=0)
        old_time = mem.last_accessed
        
        mem.update_access()
        
        assert mem.access_count == 1
        assert mem.last_accessed >= old_time


class TestEntity:
    """Entity 数据类测试"""
    
    def test_create_entity_default(self):
        """测试创建默认实体"""
        entity = Entity()
        
        assert entity.entity_id is not None
        assert entity.name == ""
        assert entity.entity_type == "unknown"
        assert entity.properties == {}
    
    def test_create_entity_with_content(self, sample_entity):
        """测试创建带内容的实体"""
        assert sample_entity.entity_id == "entity-001"
        assert sample_entity.name == "深度学习"
        assert sample_entity.entity_type == "concept"
        assert sample_entity.properties["domain"] == "AI"


class TestRelation:
    """Relation 数据类测试"""
    
    def test_create_relation_default(self):
        """测试创建默认关系"""
        rel = Relation()
        
        assert rel.relation_id is not None
        assert rel.source_id == ""
        assert rel.target_id == ""
        assert rel.relation_type == ""
        assert rel.weight == 1.0
    
    def test_create_relation_with_content(self, sample_relation):
        """测试创建带内容的关系"""
        assert sample_relation.relation_id == "relation-001"
        assert sample_relation.source_id == "entity-001"
        assert sample_relation.target_id == "entity-002"
        assert sample_relation.relation_type == "related_to"
        assert sample_relation.weight == 0.8


class TestQuery:
    """Query 数据类测试"""
    
    def test_create_query_default(self):
        """测试创建默认查询"""
        query = Query()
        
        assert query.query_id is not None
        assert query.text == ""
        assert query.user_id is None
        assert query.session_id is None
        assert query.vector is None
        assert query.filters == {}
        assert query.top_k == 10
        assert query.threshold == 0.0
    
    def test_create_query_with_content(self, sample_query):
        """测试创建带内容的查询"""
        assert sample_query.query_id == "query-001"
        assert sample_query.text == "什么是深度学习？"
        assert sample_query.user_id == "user-001"
        assert sample_query.session_id == "session-001"
        assert sample_query.top_k == 5


class TestRetrievalResult:
    """RetrievalResult 数据类测试"""
    
    def test_create_retrieval_result_default(self):
        """测试创建默认检索结果"""
        result = RetrievalResult()
        
        assert result.result_id is not None
        assert result.memory_id == ""
        assert result.content == ""
        assert result.score == 0.0
        assert result.source == RetrievalSource.VECTOR
        assert result.retrieval_path == []
    
    def test_create_retrieval_result_with_content(self):
        """测试创建带内容的检索结果"""
        result = RetrievalResult(
            memory_id="mem-001",
            content="检索到的内容",
            score=0.95,
            source=RetrievalSource.HYBRID,
            retrieval_path=["step1", "step2"]
        )
        
        assert result.memory_id == "mem-001"
        assert result.score == 0.95
        assert result.source == RetrievalSource.HYBRID


class TestGeneratedAnswer:
    """GeneratedAnswer 数据类测试"""
    
    def test_create_generated_answer(self):
        """测试创建生成的答案"""
        answer = GeneratedAnswer(
            content="生成的答案内容",
            confidence=0.85,
            evidence=["证据1", "证据2"],
            sources=["source1"]
        )
        
        assert answer.content == "生成的答案内容"
        assert answer.confidence == 0.85
        assert len(answer.evidence) == 2


class TestCritiqueResult:
    """CritiqueResult 数据类测试"""
    
    def test_create_critique_result(self):
        """测试创建批判结果"""
        critique = CritiqueResult(
            is_valid=False,
            issues=["问题1", "问题2"],
            suggestions=["建议1"],
            scores={"accuracy": 0.7, "completeness": 0.8}
        )
        
        assert critique.is_valid is False
        assert len(critique.issues) == 2
        assert critique.scores["accuracy"] == 0.7


class TestHallucinationReport:
    """HallucinationReport 数据类测试"""
    
    def test_create_hallucination_report(self):
        """测试创建幻觉检测报告"""
        report = HallucinationReport(
            has_hallucination=True,
            factual_score=0.6,
            logical_score=0.8,
            evidence_score=0.5,
            issues=["事实不一致"]
        )
        
        assert report.has_hallucination is True
        assert report.factual_score == 0.6
        assert len(report.issues) == 1


class TestResponse:
    """Response 数据类测试"""
    
    def test_create_response_default(self):
        """测试创建默认响应"""
        resp = Response()
        
        assert resp.response_id is not None
        assert resp.query_id == ""
        assert resp.content == ""
        assert resp.confidence == 0.0
        assert resp.sources == []
        assert resp.thinking_chain == []
        assert resp.tone == ResponseTone.PROFESSIONAL
        assert resp.detail_level == DetailLevel.STANDARD
    
    def test_create_response_with_content(self):
        """测试创建带内容的响应"""
        resp = Response(
            query_id="query-001",
            content="回答内容",
            confidence=0.9,
            tone=ResponseTone.FRIENDLY,
            detail_level=DetailLevel.DETAILED,
            citations=["cite1", "cite2"]
        )
        
        assert resp.query_id == "query-001"
        assert resp.confidence == 0.9
        assert resp.tone == ResponseTone.FRIENDLY
        assert len(resp.citations) == 2


class TestUserProfile:
    """UserProfile 数据类测试"""
    
    def test_create_user_profile_default(self):
        """测试创建默认用户画像"""
        profile = UserProfile()
        
        assert profile.user_id is not None
        assert profile.name is None
        assert profile.profession is None
        assert profile.knowledge_level == "intermediate"
        assert profile.preferred_tone == ResponseTone.PROFESSIONAL
        assert profile.preferred_detail == DetailLevel.STANDARD
        assert profile.interests == []
        assert profile.interaction_count == 0
    
    def test_create_user_profile_with_content(self, sample_user_profile):
        """测试创建带内容的用户画像"""
        assert sample_user_profile.user_id == "user-001"
        assert sample_user_profile.name == "测试用户"
        assert sample_user_profile.profession == "developer"
        assert sample_user_profile.knowledge_level == "intermediate"
        assert "AI" in sample_user_profile.interests
