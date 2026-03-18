# 🔄 NecoRAG 知识演化系统

## 📋 目录说明

本目录包含 NecoRAG 的知识演化模块，实现知识库的自进化、实时更新和健康管理。

## 📁 文件结构

```
knowledge_evolution/
├── __init__.py                 # 包初始化与导出 ⭐
├── updater.py                  # 知识更新器 ⭐
├── scheduler.py                # 调度管理器 ⭐
├── metrics.py                  # 量化指标计算 ⭐
├── models.py                   # 数据模型定义
├── config.py                   # 演化配置管理
└── visualizer.py               # 可视化展示 ⭐
```

## 🎯 核心功能

### 1. [updater.py](./updater.py) - 知识更新器 ⭐

**功能**: 管理知识的实时和批量更新

**更新模式**:

#### a) 实时更新 (Real-time Update)
- **触发**: 用户查询/反馈即时触发
- **范围**: L1 工作记忆、热点索引
- **延迟**: <2 秒
- **场景**: 会话上下文、高频知识热更新

```python
async def update_realtime(
    self,
    query: str,
    response: str,
    user_feedback: Optional[Feedback] = None
):
    """实时更新工作记忆"""
    
    # 1. 提取新知识
    knowledge = await self.extract_knowledge(query, response)
    
    # 2. 质量评估
    quality = self.evaluate_quality(knowledge)
    
    if quality > THRESHOLD:
        # 3. 写入 L1 工作记忆（带 TTL）
        await self.l1_memory.set(
            key=knowledge.id,
            value=knowledge,
            ttl=3600  # 1 小时过期
        )
        
        # 4. 标记为热点候选
        await self.mark_as_hot_candidate(knowledge)
```

#### b) 定时批量更新 (Scheduled Batch Update)
- **触发**: 定时任务（如每日凌晨 3 点）
- **范围**: L2 语义向量、L3 情景图谱
- **场景**: 向量索引重建、图谱关系维护、大规模知识入库

```python
async def update_scheduled(self, schedule_type: str):
    """定时批量更新"""
    
    if schedule_type == "daily":
        # 每日凌晨执行
        await self._rebuild_vector_index()
        await self._optimize_graph()
        await self._merge_candidates()
        
    elif schedule_type == "weekly":
        # 每周执行
        await self._prune_low_quality()
        await self._update_embeddings()
        await self._calculate_metrics()
```

#### c) 事件触发更新 (Event-Driven Update)
- **触发**: 外部数据源变更、知识库健康度下降
- **范围**: 受影响的知识分区
- **场景**: 数据源同步、质量修复

```python
async def update_on_event(self, event: KnowledgeEvent):
    """事件触发更新"""
    
    if event.type == EventType.DATA_SOURCE_CHANGE:
        # 外部数据源变更
        await self.sync_external_data(event.source_id)
        
    elif event.type == EventType.HEALTH_DEGRADATION:
        # 健康度下降告警
        await self.diagnose_and_fix(event.metrics)
```

### 2. [scheduler.py](./scheduler.py) - 调度管理器 ⭐

**功能**: 管理所有定时任务和更新计划

**支持的调度器**:
1. **APScheduler** (轻量级) - 默认选择
2. **Celery** (分布式) - 大规模部署

**调度配置**:
```python
@dataclass
class SchedulerConfig:
    # 实时更新
    realtime_enabled: bool = True
    realtime_batch_size: int = 100
    
    # 定时任务
    daily_update_time: str = "03:00"  # 凌晨 3 点
    weekly_update_day: str = "Sunday"  # 周日
    
    # 任务配置
    tasks: List[TaskConfig] = field(default_factory=list)
    
    # 分布式配置（Celery）
    celery_broker: str = "redis://localhost:6379/0"
    celery_backend: str = "redis://localhost:6379/0"
```

**任务示例**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

# 添加每日任务
scheduler.add_job(
    func=knowledge_updater.update_scheduled,
    trigger=CronTrigger(hour=3, minute=0),
    args=['daily'],
    id='daily_update',
    name='每日知识更新'
)

# 添加每周任务
scheduler.add_job(
    func=knowledge_updater.weekly_maintenance,
    trigger=CronTrigger(day_of_week='sun', hour=2),
    id='weekly_maintenance',
    name='每周维护'
)

# 启动调度器
scheduler.start()
```

### 3. [metrics.py](./metrics.py) - 量化指标计算 ⭐

**功能**: 计算知识库健康度的各项指标

**指标体系**:

#### 规模指标
```python
@dataclass
class ScaleMetrics:
    total_entries: int          # 知识条目总数
    l1_count: int              # L1 工作记忆数量
    l2_count: int              # L2 向量数量
    l3_nodes: int              # L3 图谱节点数
    l3_edges: int              # L3 图谱边数
    vector_coverage: float     # 向量覆盖率 (%)
```

#### 新鲜度指标
```python
@dataclass
class FreshnessMetrics:
    avg_age_days: float        # 平均知识年龄 (天)
    recent_update_rate: float  # 近 7 天更新率 (%)
    decay_distribution: Dict   # 各权重区间分布
    half_life: float           # 知识半衰期 (天)
```

#### 质量指标
```python
@dataclass
class QualityMetrics:
    retrieval_hit_rate: float  # 检索命中率 (%)
    knowledge_fragmentation: float  # 碎片率 (%)
    redundancy_rate: float     # 冗余度 (%)
    accuracy_score: float      # 准确性评分 (0-1)
```

#### 连通性指标
```python
@dataclass
class ConnectivityMetrics:
    avg_degree: float          # 平均度数
    connectivity_ratio: float  # 连通率 (%)
    isolated_nodes: int        # 孤立节点数
    avg_path_length: float     # 平均路径长度
```

**综合健康度公式**:
```python
def calculate_health_score(
    coverage: float,      # 向量覆盖率
    freshness: float,     # 新鲜度评分
    quality: float,       # 质量评分
    connectivity: float   # 连通性评分
) -> float:
    """计算综合健康度"""
    
    # 默认权重：覆盖 20%, 新鲜 30%, 质量 30%, 连通 20%
    weights = {"coverage": 0.2, "freshness": 0.3, 
               "quality": 0.3, "connectivity": 0.2}
    
    score = (
        coverage * weights["coverage"] +
        freshness * weights["freshness"] +
        quality * weights["quality"] +
        connectivity * weights["connectivity"]
    )
    
    return score * 100  # 转换为 0-100 分
```

### 4. [visualizer.py](./visualizer.py) - 可视化展示 ⭐

**功能**: 为 Dashboard 提供可视化数据接口

**提供的数据**:
1. **健康仪表盘数据**
2. **增长趋势图表**
3. **领域覆盖热力图**
4. **知识衰减雷达图**
5. **更新时间线**

**使用示例**:
```python
from src.knowledge_evolution import KnowledgeVisualizer

visualizer = KnowledgeVisualizer()

# 获取完整仪表盘数据
dashboard_data = visualizer.get_dashboard_data()

print(dashboard_data.keys())
# dict_keys(['health', 'summary', 'growth_trend', 
#            'layer_distribution', 'decay_radar', 
#            'update_timeline', 'metrics'])

# 获取健康分数
health = dashboard_data['health']
print(f"健康分数：{health['score']}")  # 87/100
print(f"健康等级：{health['level_text']}")  # "健康"

# 获取增长趋势
growth = dashboard_data['growth_trend']
for point in growth['data']:
    print(f"{point['date']}: {point['value']} 条")
```

## 📊 知识库健康仪表盘

### 仪表盘布局

```
┌──────────────────────────────────────────────────────────────┐
│                   知识库健康仪表盘                             │
├──────────┬──────────┬──────────┬─────────────────────────────┤
│ 总知识量  │ 今日新增  │ 健康分数  │        知识增长趋势          │
│ 125,432  │ +342     │ 87/100   │  ▁▂▃▄▅▆▇█ (近 30 天)          │
├──────────┴──────────┴──────────┤                             │
│      领域覆盖热力图              │        知识衰减雷达图        │
│  ████░░░░  AI (85%)            │     新鲜度 ★★★★☆           │
│  ██████░░  数据库 (75%)        │     覆盖度 ★★★★★           │
│  ██░░░░░░  网络 (25%)          │     连通性 ★★★☆☆           │
├─────────────────────────────────┴────────────────────────────┤
│                    最近更新时间线                              │
│  09:00 [实时] 新增 23 条查询知识                               │
│  03:00 [定时] 向量索引重建完成，更新 1,204 条                    │
│  00:00 [定时] 图谱关系维护，修剪 56 条弱关联                     │
└──────────────────────────────────────────────────────────────┘
```

### 访问方式

**Web 界面**: `http://localhost:8000/knowledge-health`

**API 接口**:
```python
# 获取完整数据
GET /api/knowledge/dashboard

# 获取健康报告
GET /api/knowledge/health

# 获取增长趋势
GET /api/knowledge/growth?days=30

# 获取更新时间线
GET /api/knowledge/timeline?limit=20
```

## 🔧 配置管理

### [config.py](./config.py) - 演化配置

```python
@dataclass
class KnowledgeEvolutionConfig:
    # 实时更新配置
    realtime_batch_size: int = 100
    realtime_flush_interval: int = 5  # 秒
    
    # 定时更新配置
    daily_update_hour: int = 3  # 凌晨 3 点
    weekly_update_day: int = 6  # 周日
    
    # 知识候选池配置
    candidate_pool_size: int = 1000
    auto_approve_threshold: float = 0.9
    
    # 质量评估配置
    min_credibility: float = 0.7
    min_relevance: float = 0.6
    min_novelty: float = 0.3
    
    # 遗忘衰减配置
    decay_rate: float = 0.1
    archive_threshold: float = 0.05
    
    # 可视化配置
    dashboard_refresh_interval: int = 5  # 秒
    growth_chart_days: int = 30  # 默认显示 30 天
```

## 🎨 设计模式

### 1. 观察者模式 - 更新通知

```python
class KnowledgeUpdateObserver:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, event: KnowledgeEvent):
        for observer in self.observers:
            observer.update(event)


# 使用示例
observer = KnowledgeUpdateObserver()

# 注册观察者（Dashboard、日志、告警等）
observer.attach(DashboardUpdater())
observer.attach(LogRecorder())
observer.attach(HealthMonitor())

# 触发通知
observer.notify(KnowledgeEvent.NEW_KNOWLEDGE)
```

### 2. 模板方法模式 - 更新流程

```python
class KnowledgeUpdater(ABC):
    """更新器抽象类"""
    
    def execute_update(self, data: Any):
        """模板方法 - 定义更新流程"""
        
        # 1. 前置检查
        self.pre_check(data)
        
        # 2. 质量评估
        quality = self.evaluate_quality(data)
        
        # 3. 去重检测
        if self.is_duplicate(data):
            return
        
        # 4. 执行更新（子类实现）
        self.do_update(data, quality)
        
        # 5. 后置处理
        self.post_process()
    
    @abstractmethod
    def do_update(self, data: Any, quality: float):
        """子类实现具体更新逻辑"""
        pass
```

### 3. 单例模式 - 调度器管理

```python
class SchedulerManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.scheduler = AsyncIOScheduler()
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls()
```

## 🧪 测试示例

### 单元测试

```python
# tests/test_knowledge_evolution/test_metrics.py
def test_health_score_calculation():
    metrics = KnowledgeMetrics()
    
    # 模拟健康状态
    coverage = 0.85
    freshness = 0.90
    quality = 0.80
    connectivity = 0.75
    
    score = metrics.calculate_health_score(
        coverage=coverage,
        freshness=freshness,
        quality=quality,
        connectivity=connectivity
    )
    
    expected = (
        0.85*0.2 + 0.90*0.3 + 0.80*0.3 + 0.75*0.2
    ) * 100
    
    assert abs(score - expected) < 0.01
    assert 80 <= score <= 85
```

### 集成测试

```python
# tests/test_knowledge_evolution/test_updater_integration.py
async def test_realtime_update_pipeline():
    updater = KnowledgeUpdater()
    
    # 模拟查询和回答
    query = "什么是 Transformer?"
    response = "Transformer 是一种..."
    
    # 执行实时更新
    await updater.update_realtime(query, response)
    
    # 验证 L1 工作记忆已更新
    l1_items = await updater.l1_memory.get_all()
    assert len(l1_items) > 0
    
    # 验证候选池有记录
    candidates = await updater.get_pending_candidates()
    assert any(c.query == query for c in candidates)
```

## 🐛 常见问题

### Q1: 定时任务不执行？

**排查步骤**:
```python
# 1. 检查调度器状态
print(scheduler.running)  # 应该为 True

# 2. 查看已注册任务
for job in scheduler.get_jobs():
    print(f"{job.name}: {job.next_run_time}")

# 3. 检查时区设置
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler(timezone='Asia/Shanghai')
```

### Q2: 健康分数偏低？

**诊断方法**:
```python
# 获取详细指标
metrics = calculator.calculate_all_metrics()

# 分析各项得分
print(f"覆盖率：{metrics.coverage}")
print(f"新鲜度：{metrics.freshness}")
print(f"质量：{metrics.quality}")
print(f"连通性：{metrics.connectivity}")

# 找出薄弱环节
if metrics.freshness < 0.6:
    print("⚠️  新鲜度不足，需要更新知识")
if metrics.connectivity < 0.5:
    print("⚠️  连通性差，需要建立更多关联")
```

### Q3: 实时更新延迟高？

**优化方案**:
```python
# 1. 启用批处理
config.realtime_batch_size = 100  # 累积 100 条一起处理

# 2. 异步处理
await updater.update_realtime_async(query, response)

# 3. 降低刷新频率
config.realtime_flush_interval = 10  # 10 秒刷新一次
```

## 📚 API 参考

### 完整使用示例

```python
from src.knowledge_evolution import (
    KnowledgeUpdater,
    KnowledgeScheduler,
    KnowledgeMetrics,
    KnowledgeVisualizer
)

# 1. 创建更新器
updater = KnowledgeUpdater()

# 2. 创建调度器
scheduler = KnowledgeScheduler()
scheduler.start()

# 3. 创建指标计算器
metrics = KnowledgeMetrics()

# 4. 创建可视化器
visualizer = KnowledgeVisualizer()

# 5. 实时监控循环
while True:
    # 计算当前指标
    current_metrics = metrics.calculate_all()
    
    # 更新仪表盘
    dashboard_data = visualizer.get_dashboard_data()
    
    # 检查健康度
    if current_metrics.health_score < 60:
        print("⚠️  健康度预警!")
        await updater.diagnose_and_optimize()
    
    await asyncio.sleep(5)  # 5 秒检查一次
```

## 🔗 相关链接

- [知识演化系统设计](../../docs/wiki/知识演化系统/架构设计.md)
- [健康仪表盘 UI](../dashboard/README.md#知识库健康仪表盘)
- [实时更新机制](../../docs/wiki/知识演化系统/实时更新引擎.md)

## 📞 维护信息

**负责人**: Knowledge Evolution Team  
**最后更新**: 2026-03-19  
**测试覆盖率**: >80%  
**文档状态**: ✅ 完善

---

*知识演化系统让 NecoRAG 从"静态知识库"进化为"活体知识库"，越用越智能。*
