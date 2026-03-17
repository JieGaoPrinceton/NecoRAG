# Purr Interface - 呼噜交互接口

## 概述

Purr Interface（呼噜交互接口）是 NecoRAG 的**交互层**核心组件，负责情境自适应生成与可解释性输出。就像猫通过呼噜声与人类交流一样，本接口负责"表达"和"沟通"，提供人性化的交互体验。

## 核心功能

### 1. 情境自适应生成

```
┌──────────────────────────────────────────────────────┐
│                  Purr Interface                       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  输入 ──┬── 用户画像分析                             │
│         │   · 历史交互风格                            │
│         │   · 偏好领域                                │
│         │   · 专业程度                                │
│         │                                             │
│         ├── Tone 适配                                 │
│         │   · 专业严谨                                │
│         │   · 亲切友好                                │
│         │   · 幽默轻松                                │
│         │                                             │
│         ├── Detail Level 调整                         │
│         │   · 简洁摘要                                │
│         │   · 详细解释                                │
│         │   · 深度分析                                │
│         │                                             │
│         └── 多模态合成                                │
│             · 文本输出                                │
│             · 图表生成                                │
│             · 语音合成                                │
│                                                       │
│              ↓  可解释性输出                          │
│                                                       │
│         ┌─────────────────────┐                      │
│         │   思维链可视化        │                      │
│         │   · 检索路径图        │                      │
│         │   · 证据来源        │                      │
│         │   · 推理过程        │                      │
│         └─────────────────────┘                      │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 2. 用户画像适配

基于 L1 工作记忆中的历史交互，动态调整输出风格：

```python
class UserProfile:
    """
    用户画像
    
    维度：
    - 专业程度：beginner/intermediate/expert
    - 交互风格：formal/casual/humorous
    - 偏好领域：[领域列表]
    - 历史查询：[查询主题]
    """
    user_id: str
    professional_level: str
    interaction_style: str
    preferred_domains: List[str]
    query_history: List[str]
```

**适配策略**：
- **专业程度**：调整术语使用和解释深度
- **交互风格**：选择合适的语气和表达方式
- **偏好领域**：优先展示相关内容
- **历史查询**：避免重复，关联上下文

### 3. Tone 适配

根据用户画像和查询场景，动态调整回答语气：

```python
class ToneAdapter:
    """
    语气适配器
    
    支持多种语气风格：
    - 专业严谨：使用专业术语，逻辑严密
    - 亲切友好：口语化表达，易于理解
    - 幽默轻松：适当使用比喻和幽默元素
    """
    
    def adapt(self, content: str, user_profile: UserProfile) -> str:
        """适配语气"""
        
    def inject_personality(self, content: str, style: str) -> str:
        """注入个性化元素"""
```

**示例**：

- **专业严谨**：
  > "根据知识图谱检索结果，实体 A 与实体 B 存在因果关系，置信度为 0.92。"

- **亲切友好**：
  > "我找到了它们之间的关系！A 确实会导致 B 的发生，这个结论相当可靠哦~"

- **幽默轻松**：
  > "哈哈，又发现了一个有趣的关联！A 和 B 竟然有因果关系，就像吃多了会胖一样自然 😸"

### 4. Detail Level 调整

根据查询复杂度和用户需求，调整输出详细程度：

```python
class DetailLevelAdapter:
    """
    详细程度适配器
    
    层级：
    - Level 1: 简洁摘要（1-2 句话）
    - Level 2: 标准回答（1 段话 + 要点）
    - Level 3: 详细解释（多段落 + 案例）
    - Level 4: 深度分析（完整报告 + 图表）
    """
    
    def adapt(
        self,
        content: str,
        level: int,
        query_complexity: str
    ) -> str:
        """适配详细程度"""
```

**决策逻辑**：

```python
def determine_detail_level(query: str, user_profile: UserProfile) -> int:
    # 简单查询 → Level 1-2
    if query_complexity == "simple":
        return 1 if user_profile.professional_level == "expert" else 2
    
    # 复杂查询 → Level 3-4
    if query_complexity == "complex":
        return 3 if user_profile.professional_level == "beginner" else 4
    
    # 默认
    return 2
```

### 5. 思维链可视化（创新点）

输出不仅包含答案，还展示"检索路径图"，让用户了解 AI 是如何思考的：

```python
class ThinkingChainVisualizer:
    """
    思维链可视化器
    
    展示：
    1. 检索路径：查询 → 实体识别 → 向量检索 → 图谱推理 → 结果融合
    2. 证据来源：每个断言的证据 ID 和相关度
    3. 推理过程：多跳推理的逻辑链条
    """
    
    def visualize(
        self,
        retrieval_trace: List[str],
        evidence: List[str],
        reasoning_chain: List[str]
    ) -> str:
        """生成可视化输出"""
```

**输出示例**：

```
🔍 检索路径：
  1. 查询理解：识别实体"深度学习"、"应用"
  2. 向量检索：在 L2 语义记忆中检索相关内容
  3. 图谱推理：发现"深度学习"→"图像识别"→"自动驾驶"路径
  4. 结果融合：合并 3 条检索结果

📚 证据来源：
  - [证据 1] 《深度学习导论》第3章 (相关度: 0.89)
  - [证据 2] Wikipedia: 深度学习 (相关度: 0.85)
  - [证据 3] 知乎问答 (相关度: 0.72)

🧠 推理过程：
  深度学习 → 应用于 → 图像识别
           → 应用于 → 自然语言处理
           → 应用于 → 自动驾驶

💡 答案：
  深度学习在图像识别、自然语言处理和自动驾驶等领域有广泛应用...
```

### 6. 多模态合成

自动组合多种输出形式：

```python
class MultimodalSynthesizer:
    """
    多模态合成器
    
    支持：
    - 文本输出：结构化文本答案
    - 图表生成：自动生成相关图表
    - 语音合成：TTS 转换为语音
    """
    
    def synthesize(
        self,
        content: str,
        format: str = "text"
    ) -> Union[str, bytes]:
        """合成多模态输出"""
```

## 核心类设计

### PurrInterface
交互接口主类。

```python
class PurrInterface:
    def __init__(
        self,
        memory: MemoryManager,
        llm_model: str = "default"
    )
    
    def respond(
        self,
        query: str,
        grooming_result: GroomingResult,
        session_id: str = None
    ) -> Response
```

### UserProfileManager
用户画像管理器。

```python
class UserProfileManager:
    def get_profile(self, user_id: str) -> UserProfile
    def update_profile(self, user_id: str, interaction: Interaction) -> None
    def analyze_preference(self, user_id: str) -> Dict
```

### ToneAdapter
语气适配器。

```python
class ToneAdapter:
    def adapt(self, content: str, style: str) -> str
    def inject_personality(self, content: str, style: str) -> str
```

### DetailLevelAdapter
详细程度适配器。

```python
class DetailLevelAdapter:
    def adapt(self, content: str, level: int) -> str
    def summarize(self, content: str) -> str
    def expand(self, content: str) -> str
```

### ThinkingChainVisualizer
思维链可视化器。

```python
class ThinkingChainVisualizer:
    def visualize(
        self,
        retrieval_trace: List[str],
        evidence: List[str],
        reasoning_chain: List[str]
    ) -> str
```

### MultimodalSynthesizer
多模态合成器。

```python
class MultimodalSynthesizer:
    def generate_text(self, content: str, format: str) -> str
    def generate_chart(self, data: Dict) -> bytes
    def generate_audio(self, text: str) -> bytes
```

## 使用示例

```python
from necorag.purr import PurrInterface
from necorag.memory import MemoryManager
from necorag.grooming import GroomingAgent

# 初始化
memory = MemoryManager(...)
grooming = GroomingAgent(...)
interface = PurrInterface(memory=memory)

# 处理查询
query = "深度学习有哪些应用？"
evidence = retriever.retrieve(query)
grooming_result = grooming.process(query, evidence)

# 生成交互响应
response = interface.respond(
    query=query,
    grooming_result=grooming_result,
    session_id="user_123"
)

print(response.content)
print(response.thinking_chain)
print(response.metadata)
```

## 交互流程

```
1. 接收查询和梳理结果
   ↓
2. 获取/创建用户画像
   - 从 L1 工作记忆读取历史
   - 分析用户偏好
   ↓
3. 适配输出
   - Tone 适配
   - Detail Level 调整
   - 多模态合成
   ↓
4. 生成思维链可视化
   - 检索路径
   - 证据来源
   - 推理过程
   ↓
5. 返回响应
   - 内容
   - 可视化
   - 元数据
```

## 配置参数

### 用户画像参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `profile_ttl` | int | 86400 | 画像 TTL（秒） |
| `max_history` | int | 100 | 最大历史记录数 |
| `style_detection` | bool | True | 自动风格检测 |

### 语气适配参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_tone` | str | "friendly" | 默认语气 |
| `auto_detect` | bool | True | 自动检测语气 |
| `personality_injection` | bool | True | 注入个性 |

### 详细程度参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `default_level` | int | 2 | 默认详细程度 |
| `auto_adjust` | bool | True | 自动调整 |

### 可视化参数
| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `show_trace` | bool | True | 显示检索路径 |
| `show_evidence` | bool | True | 显示证据来源 |
| `show_reasoning` | bool | True | 显示推理过程 |

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 响应延迟 | < 200ms | 适配和可视化 |
| 用户满意度 | > 85% | 主观评价 |
| 风格匹配度 | > 80% | 自动评估 |
| 可解释性评分 | > 90% | 用户反馈 |

## 依赖组件

- LLM：生成和适配
- MemoryManager：用户画像存储
- GroomingAgent：梳理结果

## 后续优化方向

1. 强化学习优化个性化
2. 多语言支持
3. 情感计算
4. AR/VR 交互
5. 实时协作功能
