# Grooming Agent - 梳理校正代理

## 概述

Grooming Agent（梳理校正代理）是 NecoRAG 的**巩固层**核心组件，负责知识的异步固化、幻觉自检与记忆修剪。就像猫通过舔毛来梳理和清洁自己一样，本代理负责"梳理"知识库，保持其准确性和时效性。

## 核心功能

### 1. LangGraph 闭环架构

```
┌──────────────────────────────────────────────────────┐
│                  Grooming Agent                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│           ┌──────────────┐                           │
│           │   Generator  │ 生成答案                  │
│           └──────┬───────┘                           │
│                  │                                    │
│                  ▼                                    │
│           ┌──────────────┐                           │
│           │    Critic    │ 批判评估                  │
│           └──────┬───────┘                           │
│                  │                                    │
│           ┌──────┴───────┐                           │
│           │              │                            │
│      通过验证       未通过验证                        │
│           │              │                            │
│           ▼              ▼                            │
│     ┌──────────┐  ┌──────────────┐                  │
│     │  Refiner │  │ 重新检索/修正 │                  │
│     └──────────┘  └──────────────┘                  │
│           │              │                            │
│           └──────┬───────┘                           │
│                  │                                    │
│                  ▼                                    │
│           ┌──────────────┐                           │
│           │   输出结果   │                           │
│           └──────────────┘                           │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 2. 预测误差最小化

对比生成内容与检索证据，确保答案有据可依：

```python
# 预测误差计算
def calculate_prediction_error(generated_answer: str, evidence: List[str]) -> float:
    """
    计算生成答案与证据之间的误差
    
    返回值越小，说明答案越有据可依
    """
    # 1. 提取答案中的关键断言
    assertions = extract_assertions(generated_answer)
    
    # 2. 验证每个断言是否有证据支持
    error = 0.0
    for assertion in assertions:
        support_score = calculate_support_score(assertion, evidence)
        if support_score < threshold:
            error += (1 - support_score)
    
    return error / len(assertions)
```

**验证策略**：
- **直接引用**：答案是否直接来自证据
- **逻辑推理**：答案是否可通过证据推导
- **反证检测**：证据是否与答案矛盾

### 3. 幻觉自检机制

```python
class HallucinationDetector:
    """
    幻觉检测器
    
    检测类型：
    1. 事实性幻觉：与检索证据矛盾
    2. 逻辑性幻觉：推理链条断裂
    3. 来源性幻觉：无证据支撑的断言
    """
    
    def detect(self, answer: str, evidence: List[str]) -> HallucinationReport:
        # 事实一致性检查
        fact_score = self.check_factual_consistency(answer, evidence)
        
        # 逻辑连贯性检查
        logic_score = self.check_logical_coherence(answer)
        
        # 证据支撑度检查
        support_score = self.check_evidence_support(answer, evidence)
        
        return HallucinationReport(
            is_hallucination=fact_score < 0.7 or support_score < 0.5,
            fact_score=fact_score,
            logic_score=logic_score,
            support_score=support_score
        )
```

**处理策略**：
- 高置信幻觉 → 触发"不知道"回复
- 中等置信幻觉 → 重新检索补充证据
- 低置信幻觉 → 添加警示标注

### 4. 异步知识固化

后台定时任务，分析并优化知识库：

```python
class KnowledgeConsolidator:
    """
    知识固化器
    
    功能：
    1. 分析高频未命中 Query
    2. 自动补充知识缺口
    3. 合并碎片化知识
    4. 更新过时信息
    """
    
    async def run_consolidation_cycle(self):
        # 1. 分析查询日志
        query_patterns = self.analyze_query_patterns()
        
        # 2. 识别知识缺口
        knowledge_gaps = self.identify_knowledge_gaps(query_patterns)
        
        # 3. 补充新知识
        for gap in knowledge_gaps:
            await self.fill_knowledge_gap(gap)
        
        # 4. 合并碎片
        await self.merge_fragments()
        
        # 5. 更新图谱连接
        await self.update_graph_connections()
```

**固化策略**：
- **热点补充**：高频未命中查询 → 自动入库
- **碎片合并**：相似小片段 → 合并成完整文档
- **连接强化**：孤立节点 → 建立关联关系
- **过时清理**：过时信息 → 标记或删除

### 5. 记忆修剪（创新点）

模拟猫"舔毛梳理"行为，清理噪声数据：

```python
class MemoryPruner:
    """
    记忆修剪器
    
    模拟猫的梳理行为：
    - 清理"脏毛"（噪声数据）
    - 强化"干净毛发"（重要连接）
    - 保持"毛发光泽"（知识时效性）
    """
    
    def prune(self) -> PruningReport:
        # 1. 识别噪声数据
        noise_data = self.identify_noise()
        
        # 2. 识别低质量知识
        low_quality = self.identify_low_quality()
        
        # 3. 识别过时信息
        outdated = self.identify_outdated()
        
        # 4. 执行修剪
        removed = self.remove_items(noise_data + low_quality + outdated)
        
        # 5. 强化重要连接
        reinforced = self.reinforce_connections()
        
        return PruningReport(
            removed_count=len(removed),
            reinforced_count=len(reinforced)
        )
```

## 核心类设计

### GroomingAgent
梳理代理主类。

```python
class GroomingAgent:
    def __init__(self, llm: BaseLLM, memory: MemoryManager):
        self.llm = llm
        self.memory = memory
        self.generator = Generator(llm)
        self.critic = Critic(llm)
        self.refiner = Refiner(llm)
        self.hallucination_detector = HallucinationDetector()
        self.consolidator = KnowledgeConsolidator(memory)
        self.pruner = MemoryPruner(memory)
    
    def process(self, query: str, evidence: List[str]) -> GroomingResult:
        """处理查询，生成并验证答案"""
        
    async def run_background_tasks(self) -> None:
        """运行后台固化任务"""
```

### Generator
答案生成器。

```python
class Generator:
    def generate(self, query: str, evidence: List[str], context: Dict) -> GeneratedAnswer:
        """
        基于证据生成答案
        
        Returns:
            GeneratedAnswer: 包含答案和引用
        """
```

### Critic
批判评估器。

```python
class Critic:
    def critique(self, answer: GeneratedAnswer, evidence: List[str]) -> CritiqueReport:
        """
        评估答案质量
        
        Returns:
            CritiqueReport: 包含问题和建议
        """
```

### Refiner
答案修正器。

```python
class Refiner:
    def refine(self, answer: GeneratedAnswer, critique: CritiqueReport) -> RefinedAnswer:
        """
        根据批判修正答案
        """
```

### HallucinationDetector
幻觉检测器。

```python
class HallucinationDetector:
    def detect(self, answer: str, evidence: List[str]) -> HallucinationReport:
        """检测幻觉"""
    
    def check_factual_consistency(self, answer: str, evidence: List[str]) -> float:
        """检查事实一致性"""
    
    def check_evidence_support(self, answer: str, evidence: List[str]) -> float:
        """检查证据支撑度"""
```

### KnowledgeConsolidator
知识固化器。

```python
class KnowledgeConsolidator:
    async def run_consolidation_cycle(self) -> ConsolidationReport:
        """运行固化周期"""
    
    def analyze_query_patterns(self) -> List[QueryPattern]:
        """分析查询模式"""
    
    def identify_knowledge_gaps(self, patterns: List[QueryPattern]) -> List[KnowledgeGap]:
        """识别知识缺口"""
    
    async def fill_knowledge_gap(self, gap: KnowledgeGap) -> bool:
        """填补知识缺口"""
    
    async def merge_fragments(self) -> int:
        """合并碎片知识"""
```

### MemoryPruner
记忆修剪器。

```python
class MemoryPruner:
    def prune(self) -> PruningReport:
        """执行记忆修剪"""
    
    def identify_noise(self) -> List[MemoryItem]:
        """识别噪声数据"""
    
    def identify_low_quality(self) -> List[MemoryItem]:
        """识别低质量知识"""
    
    def identify_outdated(self) -> List[MemoryItem]:
        """识别过时信息"""
```

## 使用示例

```python
from necorag.grooming import GroomingAgent
from necorag.memory import MemoryManager
from necorag.retrieval import PounceRetriever

# 初始化
memory = MemoryManager(...)
retriever = PounceRetriever(...)
grooming = GroomingAgent(llm=..., memory=memory)

# 查询处理
query = "什么是深度学习？"
evidence = retriever.retrieve(query)

result = grooming.process(query, evidence)
print(f"答案: {result.answer}")
print(f"置信度: {result.confidence}")
print(f"引用: {result.citations}")

# 如果检测到幻觉
if result.hallucination_report.is_hallucination:
    print("⚠️ 检测到潜在幻觉")
    print(f"问题: {result.hallucination_report.issues}")

# 启动后台固化任务
await grooming.run_background_tasks()
```

## 工作流程

### 同步处理流程

```
1. 接收查询和证据
   ↓
2. Generator 生成答案
   ↓
3. Critic 评估答案
   ↓
4. HallucinationDetector 检测幻觉
   ↓
5. 判断是否通过
   - 通过 → 返回答案
   - 未通过 → Refiner 修正 → 重新评估
   - 仍不通过 → 返回"不知道"或补充检索
```

### 异步固化流程

```
定时触发（如每小时）
   ↓
1. 分析查询日志
   - 统计未命中查询
   - 识别查询模式
   ↓
2. 识别知识缺口
   - 高频未命中主题
   - 碎片化知识点
   ↓
3. 补充新知识
   - 从外部源获取
   - 或提示管理员补充
   ↓
4. 合并碎片
   - 相似片段合并
   - 建立关联关系
   ↓
5. 更新图谱
   - 添加新实体
   - 强化连接权重
   ↓
6. 修剪低价值
   - 删除噪声
   - 归档低频
```

## 配置参数

### 验证参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `min_confidence` | float | 0.7 | 最低置信度 |
| `max_iterations` | int | 3 | 最大修正次数 |
| `hallucination_threshold` | float | 0.6 | 幻觉判定阈值 |

### 固化参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `consolidation_interval` | int | 3600 | 固化间隔（秒） |
| `min_query_frequency` | int | 5 | 最小查询频率 |
| `gap_fill_strategy` | str | "auto" | 缺口填补策略 |

### 修剪参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `noise_threshold` | float | 0.1 | 噪声判定阈值 |
| `quality_threshold` | float | 0.3 | 质量判定阈值 |
| `outdated_days` | int | 90 | 过时天数判定 |

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 幻觉检测准确率 | > 90% | 正确识别幻觉 |
| 幻觉率 | < 5% | 最终输出幻觉率 |
| 固化延迟 | < 5分钟 | 新知识可检索时间 |
| 修剪效率 | > 1000条/分钟 | 处理速度 |

## 依赖组件

- LangGraph：闭环编排
- LLM：生成、评估、修正
- MemoryManager：知识库访问

## 后续优化方向

1. 强化学习优化修正策略
2. 多模型交叉验证
3. 用户反馈驱动的固化
4. 实时幻觉监控
5. 知识版本管理
