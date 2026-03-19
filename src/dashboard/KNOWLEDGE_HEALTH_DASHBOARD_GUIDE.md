# 📊 知识库健康仪表盘使用指南

## 概述

知识库健康仪表盘 (Knowledge Health Dashboard) 是 NecoRAG Dashboard 的核心组件，提供知识库状态的全方位可视化监控。

**文件位置**: `/src/dashboard/components/KnowledgeHealthDashboard.html`

## 功能特性

### 1. 关键指标卡 (Key Metrics Cards)

展示三个核心指标：

- **总知识量**: 知识库中所有条目的总数
- **今日新增**: 当天新增的知识条目数
- **平均新鲜度**: 知识库的平均年龄（天）

**视觉设计**:
- 左侧彩色边框标识状态（绿色=良好，黄色=警告，红色=危险）
- 大号数字显示（32px 粗体）
- 趋势指示器显示变化方向

### 2. 综合健康度仪表盘 (Health Score Gauge)

**评分范围**: 0-100 分

**颜色编码**:
- 🟢 80-100: 绿色（健康）
- 🟡 60-80: 黄色（一般）
- 🟠 40-60: 橙色（预警）
- 🔴 0-40: 红色（严重）

**动画效果**:
- 指针从 0 旋转到当前分数（1 秒缓动）
- 数字滚动增长效果

**评分维度**:
- 新鲜度 (Freshness): 知识的时效性
- 覆盖度 (Coverage): 领域覆盖完整性
- 连通性 (Connectivity): 知识关联程度
- 准确性 (Accuracy): 内容质量评估

### 3. 知识增长趋势图 (Growth Trend Chart)

**图表类型**: 面积折线图

**时间范围**:
- 7 天（短期趋势）
- 30 天（月度趋势）- 默认
- 90 天（长期趋势）

**交互功能**:
- 鼠标悬停显示具体数值
- 点击时间按钮切换周期
- 平滑曲线和渐变填充

### 4. 领域覆盖热力图 (Domain Coverage Heatmap)

**展示内容**:
- 各领域的知识覆盖率百分比
- 水平条形图可视化
- 按覆盖率降序排列

**颜色映射**:
- >80%: 深绿色（覆盖充分）
- 60-80%: 浅绿色（覆盖良好）
- 40-60%: 黄色（需要补充）
- <40%: 橙色（严重不足）

**交互**:
- 悬停显示精确百分比
- 点击展开子领域详情（待实现）

### 5. 知识质量雷达图 (Quality Radar Chart)

**五个维度**:
1. **新鲜度**: 知识更新及时性
2. **覆盖度**: 领域覆盖全面性
3. **连通性**: 知识关联紧密度
4. **准确性**: 内容事实正确性
5. **多样性**: 知识类型丰富度

**评分制**: 5 星制或百分制

**可视化**: 蓝色半透明填充多边形

### 6. 更新时间线 (Update Timeline)

**事件类型**:
- 🔵 实时更新 (Realtime): 查询驱动的知识积累
- 🟢 定时任务 (Scheduled): 定期批量更新
- 🟠 事件触发 (Event-driven): 外部数据源变更

**展示信息**:
- 时间戳（相对时间格式）
- 事件标题和描述
- 影响统计（新增/修改/删除数量）

**自动刷新**: 每 5 秒追加新记录

## API 接口

仪表盘通过以下 RESTful API 获取数据：

### 获取完整仪表盘数据
```javascript
GET /api/knowledge/dashboard
```

**响应结构**:
```json
{
  "health": {
    "score": 87,
    "level": "healthy",
    "dimensions": {...}
  },
  "summary": {
    "total_entries": 125432,
    "today_new": 342,
    "avg_age_days": 45
  },
  "growth_trend": {
    "data": [
      {"date": "2026-03-01", "value": 120},
      {"date": "2026-03-02", "value": 135},
      ...
    ]
  },
  "layer_distribution": {
    "domains": [
      {"name": "AI", "coverage": 85},
      {"name": "数据库", "coverage": 75},
      ...
    ]
  },
  "decay_radar": {
    "dimensions": [
      {"name": "新鲜度", "score": 4.5},
      {"name": "覆盖度", "score": 5.0},
      ...
    ]
  },
  "update_timeline": {
    "events": [
      {
        "timestamp": "2026-03-19T09:00:00Z",
        "type": "realtime",
        "title": "新增查询知识",
        "description": "从用户查询中学习 23 条新知识",
        "stats": {"added": 23}
      }
    ]
  }
}
```

### 获取增长趋势
```javascript
GET /api/knowledge/growth?days=30
```

参数 `days`: 7 | 30 | 90

### 获取更新时间线
```javascript
GET /api/knowledge/timeline?limit=20
```

参数 `limit`: 返回事件数量（默认 20）

## 使用方法

### 1. 启动 Dashboard

```bash
cd /Users/ll/NecoRAG
python src/dashboard/dashboard.py --port 8000
```

### 2. 访问仪表盘

浏览器打开：
```
http://localhost:8000/knowledge-health
```

或者直接在文件中打开：
```
file:///path/to/src/dashboard/components/KnowledgeHealthDashboard.html
```

### 3. 集成到现有 Dashboard

在 `server.py` 中添加路由：

```python
@app.get("/knowledge-health", response_class=HTMLResponse)
async def get_knowledge_health_dashboard():
    """返回知识库健康仪表盘"""
    html_file = Path(__file__).parent / "components" / "KnowledgeHealthDashboard.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Dashboard not found")
```

## 自定义配置

### 颜色主题

在 CSS 中修改根变量：

```css
:root {
    --primary-blue: #667eea;       /* 主色调 - 蓝 */
    --primary-purple: #764ba2;     /* 主色调 - 紫 */
    --success-green: #4CAF50;      /* 成功 - 绿 */
    --warning-yellow: #FFC107;     /* 警告 - 黄 */
    --danger-red: #F44336;         /* 危险 - 红 */
    --info-orange: #FF9800;        /* 信息 - 橙 */
}
```

### 刷新频率

修改 JavaScript 中的定时器：

```javascript
// 每 5 秒自动刷新
setInterval(loadDashboardData, 5000); // 单位：毫秒
```

### 图表样式

调整 SVG 图表参数：

```javascript
// 雷达图半径
const radius = 100;

// 增长图表边距
const padding = 40;
```

## 响应式设计

### 桌面端 (>1200px)
```
┌─────────────┬──────────────────┐
│  健康仪表盘  │   增长趋势图      │
├─────────────┼──────────────────┤
│  领域热力图  │   衰减雷达图      │
├─────────────┴──────────────────┤
│         更新时间线              │
└────────────────────────────────┘
```

### 平板端 (768px-1200px)
```
┌─────────────────────────────┐
│      健康仪表盘 (全宽)       │
├─────────────────────────────┤
│      增长趋势图 (全宽)       │
├─────────────────────────────┤
│  领域热力图  │  衰减雷达图   │
├─────────────────────────────┤
│         更新时间线           │
└─────────────────────────────┘
```

### 移动端 (<768px)
```
┌──────────────┐
│ 健康仪表盘   │
├──────────────┤
│ 关键指标卡   │
├──────────────┤
│ 增长趋势图   │
├──────────────┤
│ 领域热力图   │
├──────────────┤
│ 衰减雷达图   │
├──────────────┤
│ 更新时间线   │
└──────────────┘
```

## 性能优化

### 1. 虚拟滚动
当时间线超过 50 条时自动启用虚拟滚动，只渲染可见区域。

### 2. 防抖处理
窗口大小调整时使用防抖（debounce），避免频繁重绘。

### 3. 数据缓存
本地缓存最近一次请求结果，减少重复 API 调用。

### 4. 懒加载
图表库按需加载，首屏仅加载必要组件。

## 故障排查

### 问题 1: 数据显示"计算中..."

**原因**: NecoRAG 实例未初始化

**解决方案**:
```python
# 在 server.py 中确保设置 NecoRAG 引用
server.set_necorag(necorag_instance)
```

### 问题 2: 图表不显示

**原因**: API 返回空数据

**解决方案**:
1. 检查后端服务是否运行
2. 验证 API 端点：`curl http://localhost:8000/api/knowledge/dashboard`
3. 查看浏览器控制台错误信息

### 问题 3: 样式错乱

**原因**: CSS 文件路径错误或缓存

**解决方案**:
1. 清除浏览器缓存（Ctrl+Shift+Delete）
2. 检查 HTML 文件中的 CSS 路径
3. 使用开发者工具检查元素样式

## 扩展开发

### 添加新的指标卡

在 HTML 中添加：

```html
<div class="metric-card">
    <div class="metric-value" id="new-metric">0</div>
    <div class="metric-label">新指标名称</div>
    <div class="metric-trend trend-up">↑ 趋势描述</div>
</div>
```

在 JavaScript 中更新：

```javascript
function updateNewMetric(value) {
    animateValue('new-metric', value);
}
```

### 添加新的图表类型

1. 在 HTML 中添加容器
2. 在 JavaScript 中编写绘制函数
3. 在 `loadDashboardData()` 中调用更新函数

### 添加导出功能

```javascript
function exportReport() {
    const data = {
        health: currentHealth,
        metrics: currentMetrics,
        timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-health-${Date.now()}.json`;
    a.click();
}
```

## 最佳实践

1. **定期查看健康度**: 每天至少查看一次健康仪表盘，及时发现潜在问题
2. **关注趋势变化**: 重点关注增长趋势和衰减雷达的变化
3. **优化低分维度**: 根据雷达图识别薄弱环节并针对性优化
4. **设置告警阈值**: 当健康度低于 60 分时采取措施
5. **导出历史报告**: 定期导出报告用于长期分析和对比

## 技术栈

- **前端框架**: 原生 HTML + CSS + JavaScript（零依赖）
- **图表库**: 内联 SVG（无需外部库）
- **样式**: CSS Grid + Flexbox
- **动画**: CSS Transitions + requestAnimationFrame
- **API**: Fetch API

## 兼容性

- **现代浏览器**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **移动端**: iOS Safari 14+, Android Chrome 90+
- **分辨率**: 最低支持 320px 宽度

## 未来规划

- [ ] 导出 PDF 报告功能
- [ ] 自定义告警规则
- [ ] 多维度对比分析
- [ ] 实时 WebSocket 推送
- [ ] 暗黑模式支持
- [ ] 更多图表类型（饼图、柱状图等）
- [ ] 数据下钻功能（点击查看详情）

## 相关文档

- [NecoRAG Dashboard 使用指南](../README.md)
- [知识演化系统文档](../../knowledge_evolution/README.md)
- [API 参考文档](../../interface/README.md)

---

**最后更新**: 2026-03-19  
**版本**: v3.1.0-alpha  
**作者**: NecoRAG Team
