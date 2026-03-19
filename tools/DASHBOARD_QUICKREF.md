# 📋 知识库健康仪表盘 - 快速参考卡

## 🚀 一键启动

```bash
./tools/start_knowledge_dashboard.sh
```

**访问**: `http://localhost:8000/knowledge-health`

---

## 📁 核心文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 📄 **仪表盘组件** | `src/dashboard/components/KnowledgeHealthDashboard.html` | 主界面 (28KB) |
| 📚 **使用指南** | `src/dashboard/KNOWLEDGE_HEALTH_DASHBOARD_GUIDE.md` | 详细文档 (10KB) |
| 🎨 **UI 视觉指南** | `src/dashboard/UI_VISUAL_GUIDE.md` | 界面说明 |
| ✅ **测试脚本** | `src/dashboard/test_knowledge_health_dashboard.py` | 功能测试 |
| 🔧 **启动脚本** | `tools/start_knowledge_dashboard.sh` | 快速启动 |

---

## 🎯 核心功能

### 6 大可视化组件

1. **📊 关键指标卡** - 总知识量、今日新增、平均新鲜度
2. **🎛️ 健康仪表盘** - 综合评分 0-100 分
3. **📈 增长趋势图** - 7/30/90 天切换
4. **🔥 领域热力图** - 各领域覆盖率
5. **⬡ 质量雷达图** - 五维度评估
6. **⏱️ 更新时间线** - 实时/定时/事件触发

---

## 🎨 颜色编码

| 状态 | 颜色 | 分数范围 |
|------|------|---------|
| 🟢 **健康** | #4CAF50 | 80-100 分 |
| 🟡 **一般** | #FFC107 | 60-80 分 |
| 🟠 **预警** | #FF9800 | 40-60 分 |
| 🔴 **严重** | #F44336 | 0-40 分 |

---

## 📊 API 端点

```python
# 获取完整仪表盘数据
GET /api/knowledge/dashboard

# 获取增长趋势
GET /api/knowledge/growth?days=30

# 获取更新时间线
GET /api/knowledge/timeline?limit=20

# 获取健康报告
GET /api/knowledge/health

# 获取知识库指标
GET /api/knowledge/metrics
```

---

## ⚙️ 配置参数

### 刷新频率
```javascript
// 默认：每 5 秒自动刷新
setInterval(loadDashboardData, 5000);
```

### 健康评分权重
```python
health_score = (
    0.2 * coverage +      # 覆盖度
    0.3 * freshness +     # 新鲜度
    0.3 * quality +       # 质量
    0.2 * connectivity    # 连通性
)
```

---

## 🐛 快速故障排查

### 问题 1: 显示"计算中..."
**解决**: 确保 NecoRAG 实例已初始化
```python
server.set_necorag(necorag_instance)
```

### 问题 2: 图表不显示
**解决**: 
1. 检查后端服务是否运行
2. 验证 API：`curl http://localhost:8000/api/knowledge/dashboard`
3. 清除浏览器缓存

### 问题 3: 样式错乱
**解决**: 
- 硬刷新（Ctrl+Shift+R）
- 检查 CSS 路径
- 查看控制台错误

---

## 📱 响应式断点

| 设备 | 宽度 | 布局 |
|------|------|------|
| 🖥️ 桌面 | >1200px | 多栏网格 |
| 📱 平板 | 768-1200px | 双栏布局 |
| 📱 手机 | <768px | 单列堆叠 |

---

## 🎯 测试命令

```bash
# 运行功能测试
python src/dashboard/test_knowledge_health_dashboard.py

# 预期输出
✅ 通过 - 文件存在性
✅ 通过 - 使用指南
✅ 通过 - HTML 结构
✅ 通过 - API 端点
✅ 通过 - 响应式设计
总计：5/5 项测试通过
```

---

## 📚 文档导航

- 📘 **主文档**: [KNOWLEDGE_HEALTH_DASHBOARD_GUIDE.md](./src/dashboard/KNOWLEDGE_HEALTH_DASHBOARD_GUIDE.md)
- 🎨 **UI 指南**: [UI_VISUAL_GUIDE.md](./src/dashboard/UI_VISUAL_GUIDE.md)
- 📝 **总结**: [IMPLEMENTATION_SUMMARY.md](./src/dashboard/IMPLEMENTATION_SUMMARY.md)
- ✅ **报告**: [KNOWLEDGE_DASHBOARD_COMPLETE_REPORT.md](./KNOWLEDGE_DASHBOARD_COMPLETE_REPORT.md)

---

## 💡 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F5` | 刷新数据 |
| `Ctrl+Shift+R` | 硬刷新（清缓存） |
| `Ctrl+0` | 重置缩放 |
| `Space` | 页面下翻 |

---

## 🔮 待开发功能

- [ ] PDF 导出
- [ ] 告警设置
- [ ] 暗黑模式
- [ ] WebSocket 推送
- [ ] 数据下钻

---

## 📞 支持

**版本**: v3.0.1-alpha  
**日期**: 2026-03-19  
**兼容性**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

## ✨ 一句话总结

> 🎉 **零依赖、全功能、现代化的知识库健康监控仪表盘**

---

**快速开始**: `./tools/start_knowledge_dashboard.sh` → 自动打开浏览器查看！🚀
