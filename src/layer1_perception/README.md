# Whiskers Engine - 胡须感知引擎

## 概述

Whiskers Engine（胡须感知引擎）是 NecoRAG 的**感知层**核心组件，负责多模态数据的高精度编码与情境标记。就像猫的胡须能敏锐感知环境微变化一样，本引擎负责"感知"和"理解"输入的各种数据。

## 核心功能

### 1. 深度文档解析
- 集成 RAGFlow 进行文档深度解析
- 支持 OCR（光学字符识别）
- 表格结构还原
- 文档层级分析
- 支持多种文档格式：PDF、Word、Markdown、HTML 等

### 2. 多维度向量化
- 利用 BGE-M3 模型生成：
  - **稠密向量**：高维语义表示
  - **稀疏向量**：关键词权重表示
  - **实体三元组**：知识图谱构建基础

### 3. 情境标签生成器（创新点）
为每个 Chunk 自动打标，模拟猫胡须的环境感知：
- **时间标签**：文档创建时间、更新时间、时效性
- **情感标签**：正面/负面/中性，情绪强度
- **重要性标签**：基于内容质量、信息密度评分
- **主题标签**：自动分类、关键词提取

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   Whiskers Engine                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   文档解析    │───▶│   分块策略    │              │
│  │  (RAGFlow)   │    │  (Chunking)  │              │
│  └──────────────┘    └──────────────┘              │
│         │                    │                       │
│         ▼                    ▼                       │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   向量化     │    │  情境标签     │              │
│  │  (BGE-M3)    │    │  Generator    │              │
│  └──────────────┘    └──────────────┘              │
│         │                    │                       │
│         └────────┬───────────┘                       │
│                  ▼                                   │
│         ┌──────────────┐                            │
│         │  编码输出     │                            │
│         │   Output     │                            │
│         └──────────────┘                            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 核心类设计

### DocumentParser
文档解析器，负责将各种格式文档转换为统一的结构化表示。

```python
class DocumentParser:
    def parse(file_path: str) -> ParsedDocument
    def extract_tables(content: str) -> List[Table]
    def extract_images(content: str) -> List[Image]
```

### ChunkStrategy
分块策略，支持多种分块模式。

```python
class ChunkStrategy:
    def chunk_by_semantic(content: str) -> List[Chunk]
    def chunk_by_fixed_size(content: str, size: int) -> List[Chunk]
    def chunk_by_structure(content: str) -> List[Chunk]
```

### ContextualTagger
情境标签生成器，为每个 Chunk 添加丰富的元数据。

```python
class ContextualTagger:
    def generate_time_tag(chunk: Chunk) -> TimeTag
    def generate_sentiment_tag(chunk: Chunk) -> SentimentTag
    def generate_importance_tag(chunk: Chunk) -> ImportanceTag
    def generate_topic_tags(chunk: Chunk) -> List[str]
```

### VectorEncoder
向量编码器，生成多类型向量表示。

```python
class VectorEncoder:
    def encode_dense(text: str) -> np.ndarray
    def encode_sparse(text: str) -> Dict[str, float]
    def extract_entities(text: str) -> List[Triple]
```

## 使用示例

```python
from necorag.whiskers import WhiskersEngine

# 初始化引擎
engine = WhiskersEngine(model="BGE-M3")

# 解析文档
parsed_doc = engine.parse_document("report.pdf")

# 编码并打标
encoded_chunks = engine.process(parsed_doc)

for chunk in encoded_chunks:
    print(f"内容: {chunk.content[:50]}...")
    print(f"向量维度: {chunk.dense_vector.shape}")
    print(f"情境标签: {chunk.context_tags}")
    print(f"重要性: {chunk.importance_score}")
```

## 配置参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `chunk_size` | int | 512 | 分块大小（字符数） |
| `chunk_overlap` | int | 50 | 分块重叠长度 |
| `enable_ocr` | bool | True | 是否启用 OCR |
| `sentiment_model` | str | "default" | 情感分析模型 |
| `entity_extractor` | str | "default" | 实体提取器 |

## 性能指标

- **文档解析速度**：PDF 约 10-20 页/秒
- **向量化速度**：约 1000 chunks/秒（GPU）
- **标签生成速度**：约 500 chunks/秒

## 依赖组件

- RAGFlow：文档解析
- BGE-M3：向量化模型
- spaCy：实体识别
- transformers：情感分析

## 扩展性

支持自定义插件：
1. 自定义文档解析器
2. 自定义分块策略
3. 自定义标签生成器
4. 自定义向量编码器

## 后续优化方向

1. 支持更多文档格式（PPT、Excel）
2. 增强表格理解能力
3. 多模态向量化（文本+图片）
4. 增量文档处理
