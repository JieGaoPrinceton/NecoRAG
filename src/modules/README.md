# 🧠 NecoRAG 自适应优化引擎

## 📋 目录说明

本目录包含 NecoRAG 的自适应学习模块，实现用户偏好预测、策略优化和集体智慧聚合。

## 📁 文件结构

```
adaptive/
├── __init__.py                 # 包初始化与导出 ⭐
├── engine.py                   # 自适应引擎主类 ⭐
├── preference_predictor.py     # 偏好预测器 ⭐
├── strategy_optimizer.py       # 策略优化器 ⭐
├── feedback.py                 # 反馈收集器 ⭐
├── models.py                   # 数据模型定义
└── config.py                   # 自适应配置
```

## 🎯 核心功能

### 1. [engine.py](./engine.py) - 自适应引擎 ⭐

**功能**: 统一协调所有自适应学习和优化功能

**学习层次**:
```python
class AdaptiveLearningEngine:
    """
    三层自适应学习架构
    
    1. 即时适应 (Instant Adaptation)
       - 单次会话内的上下文学习
       - 对应脑机制：工作记忆激活
       - 时间尺度：秒 - 分钟
    
    2. 短期优化 (Short-term Optimization)
       - 跨会话的用户偏好学习
       - 对应脑机制：突触可塑性
       - 时间尺度：天 - 周
    
    3. 长期进化 (Long-term Evolution)
       - 全局策略优化与知识沉淀
       - 对应脑机制：系统巩固
       - 时间尺度：周 - 月
    """
    
    def __init__(self):
        self.preference_predictor = PreferencePredictor()
        self.strategy_optimizer = StrategyOptimizer()
        self.feedback_collector = FeedbackCollector()
        
        # 三层学习
        self.instant_context = SessionContext()
        self.short_term_model = UserPreferenceModel()
        self.long_term_patterns = GlobalPatterns()
```

**使用示例**:
```python
from src.adaptive import AdaptiveEngine

engine = AdaptiveEngine()

# 开始新会话（即时适应）
session = engine.start_session(user_id="user_001")

# 记录交互
engine.record_interaction(
    session=session,
    query="问题文本",
    response=rag_response,
    user_feedback="👍"
)

# 实时更新偏好模型
engine.update_preferences(session.user_id)

# 定期策略优化（后台任务）
await engine.optimize_strategies(period="weekly")
```

### 2. [preference_predictor.py](./preference_predictor.py) - 偏好预测器 ⭐

**功能**: 基于用户历史行为预测偏好

**预测维度**:
```python
@dataclass
class UserPreference:
    # 响应风格
    preferred_tone: str           # "formal", "casual", "friendly"
    detail_level: int             # 1-5 (简略到详细)
    
    # 内容偏好
    preferred_format: str         # "text", "list", "table", "code"
    evidence_required: bool       # 是否需要引用证据
    show_reasoning: bool          # 是否展示推理过程
    
    # 检索偏好
    preferred_strategy: str       # "vector", "graph", "hybrid"
    novelty_preference: float     # 新颖性偏好 (0-1)
    
    # 领域偏好
    expertise_domains: List[str]  # 擅长领域列表
    interest_topics: List[str]    # 兴趣主题
```

**预测算法**:
```python
class PreferencePredictor:
    def predict(self, user_id: str, context: QueryContext) -> UserPreference:
        """预测用户偏好"""
        
        # 1. 提取历史特征
        history = self.get_user_history(user_id)
        features = self.extract_features(history)
        
        # 2. 多模型预测
        predictions = []
        
        # 基于规则的预测
        rule_pred = self.rule_based_predict(features)
        predictions.append(rule_pred)
        
        # 基于协同过滤的预测
        cf_pred = self.collaborative_filter_predict(features)
        predictions.append(cf_pred)
        
        # 基于深度学习的预测（如果有足够数据）
        if len(history) > 100:
            dl_pred = self.deep_learning_predict(features)
            predictions.append(dl_pred)
        
        # 3. 加权融合
        final_pred = self.weighted_fuse(predictions)
        
        return final_pred
```

**中文处理优化（千问 3.5）**:
```python
def analyze_chinese_preference(self, user_interactions: List[Interaction]):
    """中文用户偏好深度分析"""
    
    prompt = f"""
    请分析以下用户交互历史，推断用户偏好：
    
    {format_interactions(user_interactions)}
    
    分析维度：
    1. 回答风格偏好（正式/随意/幽默）
    2. 详细程度偏好（1-5 分）
    3. 内容格式偏好（文字/列表/表格/代码）
    4. 专业度水平（初级/中级/高级/专家）
    5. 潜在兴趣领域
    
    输出 JSON 格式。
    """
    
    analysis = self.qwen_llm.generate(prompt)
    return parse_preference(analysis)
```

### 3. [strategy_optimizer.py](./strategy_optimizer.py) - 策略优化器 ⭐

**功能**: 通过"探索 - 利用"平衡持续优化检索策略

**优化算法**: Thompson Sampling（汤普森采样）

```python
class StrategyOptimizer:
    """
    基于多臂老虎机问题的策略优化
    
    每个检索策略是一个"手臂"，用户满意度是"奖励"
    使用 Thompson Sampling 平衡探索和利用
    """
    
    def __init__(self):
        # 每个策略的成功/失败计数
        self.strategy_stats = {
            "vector": {"success": 0, "failure": 0},
            "graph": {"success": 0, "failure": 0},
            "hybrid": {"success": 0, "failure": 0},
            # ...
        }
    
    def select_strategy(self, intent_type: str) -> str:
        """选择最优策略"""
        
        # Thompson Sampling
        sampled_probs = {}
        for strategy, stats in self.strategy_stats.items():
            # 从 Beta 分布采样
            alpha = stats["success"] + 1
            beta = stats["failure"] + 1
            sampled_probs[strategy] = np.random.beta(alpha, beta)
        
        # 选择采样概率最大的策略
        best_strategy = max(sampled_probs, key=sampled_probs.get)
        return best_strategy
    
    def update_stats(self, strategy: str, success: bool):
        """更新策略统计"""
        if success:
            self.strategy_stats[strategy]["success"] += 1
        else:
            self.strategy_stats[strategy]["failure"] += 1
```

**策略效果追踪表**:
```python
STRATEGY_PERFORMANCE = {
    # 意图类型：{策略：{命中率，满意度，平均延迟}}
    "factual": {
        "vector_exact": {"hit_rate": 0.85, "satisfaction": 4.2, "latency": 120},
        "keyword_boost": {"hit_rate": 0.78, "satisfaction": 3.9, "latency": 95}
    },
    "comparative": {
        "multi_entity": {"hit_rate": 0.82, "satisfaction": 4.5, "latency": 180},
        "graph_relation": {"hit_rate": 0.88, "satisfaction": 4.7, "latency": 250}
    }
}
```

### 4. [feedback.py](./feedback.py) - 反馈收集器 ⭐

**功能**: 收集和处理显式/隐式用户反馈

**反馈类型**:

#### a) 显式反馈
```python
@dataclass
class ExplicitFeedback:
    user_id: str
    query_id: str
    rating: int              # 1-5 星
    thumbs_up: bool          # 👍/👎
    correction: Optional[str]  # 用户修正
    comment: Optional[str]     # 文字评论
```

#### b) 隐式反馈
```python
@dataclass
class ImplicitFeedback:
    user_id: str
    query_id: str
    dwell_time: float        # 停留时间 (秒)
    clicked_results: int     # 点击结果数
    reformulated_query: bool # 是否改写查询
    abandoned: bool          # 是否放弃会话
```

**反馈信号权重**:
```python
FEEDBACK_WEIGHTS = {
    # 显式反馈（高权重）
    "rating_5_star": 1.0,
    "rating_4_star": 0.8,
    "rating_3_star": 0.5,
    "rating_2_star": 0.2,
    "rating_1_star": 0.0,
    "thumbs_up": 0.9,
    "thumbs_down": 0.1,
    
    # 隐式反馈（中权重）
    "long_dwell (>30s)": 0.7,
    "medium_dwell (10-30s)": 0.5,
    "short_dwell (<10s)": 0.3,
    "click_top_result": 0.6,
    "click_multiple": 0.5,
    "no_click": 0.2,
    
    # 负面信号（强惩罚）
    "query_reformulation": 0.3,  # 重新查询表示不满
    "session_abandon": 0.1,      # 放弃会话
    "negative_comment": 0.0      # 负面评论
}
```

**反馈融合算法**:
```python
def fuse_feedback(explicit: ExplicitFeedback, implicit: ImplicitFeedback):
    """融合多种反馈信号"""
    
    score = 0.0
    total_weight = 0.0
    
    # 显式反馈
    if explicit.rating:
        weight = FEEDBACK_WEIGHTS[f"rating_{explicit.rating}_star"]
        score += weight * 2.0  # 显式反馈权重翻倍
        total_weight += 2.0
    
    if explicit.thumbs_up is not None:
        weight = FEEDBACK_WEIGHTS["thumbs_up" if explicit.thumbs_up else "thumbs_down"]
        score += weight
        total_weight += 1.0
    
    # 隐式反馈
    dwell_weight = FEEDBACK_WEIGHTS[self._categorize_dwell(implicit.dwell_time)]
    score += dwell_weight
    total_weight += 1.0
    
    if implicit.reformulated_query:
        score += FEEDBACK_WEIGHTS["query_reformulation"]
        total_weight += 1.0
    
    # 归一化
    final_score = score / total_weight if total_weight > 0 else 0.5
    
    return final_score  # 0-1 范围
```

## 📊 学习指标

### 即时适应指标
```python
@dataclass
class InstantMetrics:
    session_satisfaction: float    # 会话满意度
    context_relevance: float       # 上下文相关性
    adaptation_speed: float        # 适应速度 (秒)
```

### 短期优化指标
```python
@dataclass
class ShortTermMetrics:
    preference_accuracy: float     # 偏好预测准确率
    strategy_improvement: float    # 策略改进幅度
    user_retention: float          # 用户留存率
```

### 长期进化指标
```python
@dataclass
class LongTermMetrics:
    global_satisfaction_trend: float  # 满意度趋势 (30 天)
    knowledge_coverage_growth: float  # 知识覆盖增长率
    system_intelligence_score: float  # 系统智能评分
```

## 🔧 配置管理

### [config.py](./config.py) - 自适应配置

```python
@dataclass
class AdaptiveConfig:
    # 学习率
    instant_learning_rate: float = 0.3
    short_term_learning_rate: float = 0.1
    long_term_learning_rate: float = 0.05
    
    # 探索 - 利用平衡
    exploration_rate: float = 0.2  # 20% 探索新策略
    
    # 反馈配置
    feedback_window_days: int = 30  # 反馈窗口
    min_feedback_samples: int = 10  # 最小样本数
    
    # 偏好预测
    enable_deep_analysis: bool = True  # 启用深度学习分析
    qwen_enabled: bool = True          # 启用千问 3.5 中文分析
    
    # 策略优化
    thompson_sampling_enabled: bool = True
    ab_testing_enabled: bool = True
    
    # 集体智慧
    collective_learning_enabled: bool = True
    expert_weight_boost: float = 1.5   # 专家反馈加权
```

## 🎨 设计模式

### 1. 强化学习 - 策略优化闭环

```python
class ReinforcementLearningLoop:
    """
    MDP (Markov Decision Process) 框架
    
    State: 用户查询意图
    Action: 选择检索策略
    Reward: 用户满意度
    """
    
    def __init__(self):
        self.q_table = defaultdict(lambda: defaultdict(float))
    
    def choose_action(self, state: str) -> str:
        """ε-greedy 策略选择"""
        if random.random() < self.epsilon:
            # 探索：随机选择
            return random.choice(STRATEGIES)
        else:
            # 利用：选择最优策略
            return max(self.q_table[state], key=self.q_table[state].get)
    
    def update(self, state: str, action: str, reward: float, next_state: str):
        """Q-Learning 更新"""
        lr = 0.1  # 学习率
        gamma = 0.9  # 折扣因子
        
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        # Q 值更新公式
        new_q = current_q + lr * (reward + gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
```

### 2. 集成学习 - 多模型预测融合

```python
class EnsemblePredictor:
    """集成多个预测模型"""
    
    def __init__(self):
        self.models = [
            RuleBasedModel(),      # 规则模型
            CollaborativeModel(),  # 协同过滤
            DeepLearningModel()    # 深度学习
        ]
        self.model_weights = [0.3, 0.3, 0.4]
    
    def predict(self, features: Dict) -> UserPreference:
        """加权融合多个模型的预测"""
        predictions = []
        
        for model, weight in zip(self.models, self.model_weights):
            try:
                pred = model.predict(features)
                predictions.append((pred, weight))
            except Exception:
                continue  # 跳过失败模型
        
        # 加权融合
        final_pred = self.weighted_average(predictions)
        return final_pred
```

### 3. 在线学习 - 实时模型更新

```python
class OnlineLearner:
    """在线学习，模型实时更新"""
    
    def __init__(self):
        self.model = initialize_model()
    
    def partial_fit(self, sample: Interaction):
        """增量学习单个样本"""
        
        # 提取特征
        x = self.extract_features(sample)
        y = self.extract_label(sample)
        
        # 增量更新（不重新训练全量）
        self.model.partial_fit(x, y)
    
    def active_learning(self, pool: List[Interaction]) -> List[Interaction]:
        """主动学习：选择最有价值的样本标注"""
        
        # 计算不确定性
        uncertainties = []
        for sample in pool:
            x = self.extract_features(sample)
            uncertainty = self.model.predict_uncertainty(x)
            uncertainties.append((sample, uncertainty))
        
        # 选择最不确定的样本
        top_uncertain = sorted(uncertainties, key=lambda x: x[1])[-10:]
        return [s for s, _ in top_uncertain]
```

## 🧪 测试示例

### 单元测试

```python
# tests/test_adaptive/test_preference_predictor.py
def test_preference_prediction():
    predictor = PreferencePredictor()
    
    # 模拟用户历史
    history = [
        Interaction(rating=5, detail_level=5, tone="formal"),
        Interaction(rating=5, detail_level=4, tone="formal"),
        Interaction(rating=4, detail_level=5, tone="formal"),
    ]
    
    # 预测偏好
    pref = predictor.predict("user_001", history)
    
    assert pref.detail_level >= 4
    assert pref.preferred_tone == "formal"
```

### A/B 测试

```python
# tests/test_adaptive/test_ab_testing.py
def test_ab_testing_framework():
    ab_test = ABTest(
        name="strategy_comparison",
        variants=["vector_only", "hybrid"],
        traffic_split=[0.5, 0.5]
    )
    
    # 分配用户到变体
    variant_a = ab_test.assign_variant("user_001")
    variant_b = ab_test.assign_variant("user_002")
    
    # 收集指标
    ab_test.record_metric("user_001", satisfaction=4.5)
    ab_test.record_metric("user_002", satisfaction=4.2)
    
    # 统计分析
    result = ab_test.analyze()
    print(f"胜者：{result.winner}")
    print(f"置信度：{result.confidence}")
```

## 🐛 常见问题

### Q1: 偏好预测不准确？

**解决方案**:
```python
# 1. 增加训练数据
predictor.add_training_data(more_interactions)

# 2. 调整特征工程
predictor.feature_extractor.add_feature("time_of_day")
predictor.feature_extractor.add_feature("query_complexity")

# 3. 启用深度学习分析（需要足够数据）
config.enable_deep_analysis = True
```

### Q2: 策略优化收敛慢？

**优化方法**:
```python
# 1. 提高学习率
optimizer.learning_rate = 0.3

# 2. 增加探索率
optimizer.exploration_rate = 0.3  # 30% 探索

# 3. 使用汤普森采样（比ε-greedy 更高效）
optimizer.use_thompson_sampling()
```

### Q3: 反馈信号稀疏？

**解决策略**:
```python
# 1. 主动 solicitation 反馈
if session.length > 5:
    ask_for_feedback(user_id)

# 2. 利用隐式反馈
feedback_collector.enable_implicit_tracking()

# 3. 迁移学习（从相似用户）
similar_users = find_similar_users(target_user)
transfer_preferences(similar_users, target_user)
```

## 📚 API 参考

### 完整使用示例

```python
from src.adaptive import AdaptiveEngine, AdaptiveConfig

# 创建配置
config = AdaptiveConfig(
    learning_rates={"instant": 0.3, "short": 0.1, "long": 0.05},
    exploration_rate=0.2,
    enable_deep_analysis=True
)

# 创建引擎
engine = AdaptiveEngine(config=config)

# 开始会话
session = engine.start_session(user_id="user_001")

# 记录交互并实时更新
for interaction in interactions:
    engine.record_interaction(session, interaction)
    engine.update_preferences(session.user_id)

# 定期策略优化
await engine.optimize_strategies(period="daily")

# 查看学习效果
metrics = engine.get_metrics()
print(f"满意度趋势：{metrics.global_satisfaction_trend}")
print(f"策略改进：{metrics.strategy_improvement}")
```

## 🔗 相关链接

- [自适应学习设计](../../design/design.md#多语言自适应学习引擎)
- 用户画像管理](../user/README.md)
- [集体智慧聚合](../../docs/wiki/巩固层模块/集体智慧聚合.md)

## 📞 维护信息

**负责人**: ML Team  
**最后更新**: 2026-03-19  
**测试覆盖率**: >80%  
**文档状态**: ✅ 完善

---

*自适应优化引擎让 NecoRAG 具备"越用越懂你"的能力，实现真正的个性化智能服务。*
