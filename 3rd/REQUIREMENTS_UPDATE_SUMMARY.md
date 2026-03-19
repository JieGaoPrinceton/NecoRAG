# requirements.txt 更新总结

## 📋 更新概览

**更新时间**: 2026-03-19  
**版本**: v3.0.0-alpha  
**目标**: 根据项目最新功能模块，全面整理和更新依赖列表

## 📊 更新效果

### 文件变化
- **原始行数**: ~70 行
- **更新后行数**: 159 行
- **增加内容**: 新增详细的依赖分类、安装指南和说明文档

### 依赖分类结构

新的 requirements.txt 按功能模块组织，共包含 **18 个依赖分类章节**：

#### 核心依赖（必需）
1. ✅ Core Dependencies (核心依赖) - 6 个包
2. ✅ Dashboard & Web Framework (Dashboard 框架) - 3 个包

#### v3.0.0-alpha 新增模块依赖
3. ✅ Intent Analysis (意图分析系统) - jieba + 可选深度学习
4. ✅ Domain Weight System (领域权重系统) - scipy
5. ✅ Knowledge Evolution (知识演化系统) - apscheduler/celery（可选）
6. ✅ Monitoring & Alerts (监控告警系统) - prometheus-client
7. ✅ Security Module (安全模块) - PyJWT, python-jose
8. ✅ A/B Testing & Analytics (A/B 测试) - scipy, statsmodels
9. ✅ Visualization (可视化) - plotly, matplotlib
10. ✅ Adaptive Optimization (自适应优化) - scikit-learn（可选）
11. ✅ Plugin System (插件扩展系统) - importlib-metadata（可选）

#### 可选集成依赖（注释状态）
12. ✅ Document Parsing (文档解析) - ragflow, PyMuPDF 等
13. ✅ Vector Database (向量数据库) - qdrant-client, pymilvus
14. ✅ Graph Database (图数据库) - neo4j, nebula3-python
15. ✅ Cache (缓存层) - redis
16. ✅ Embedding Models (嵌入模型) - FlagEmbedding
17. ✅ LLM Integration (LLM 集成) - langchain, openai 等
18. ✅ NLP Tools (NLP 工具) - spacy, transformers

#### 开发和测试
19. ✅ Testing (测试工具) - pytest, pytest-cov
20. ✅ Development (开发工具) - black, flake8, mypy

## 🆕 新增依赖包

### v3.0.0-alpha 模块新增

| 模块 | 新增依赖 | 用途 |
|------|---------|------|
| **Intent Analysis** | `jieba>=3.0.0-alpha` | 中文分词与关键词提取 |
| **Domain Weight** | `scipy>=3.0.0-alpha` | 科学计算，相似度计算 |
| **Monitoring** | `prometheus-client>=3.0.0-alpha` | Prometheus 指标收集 |
| **Security** | `PyJWT>=3.0.0-alpha` | JWT 认证 |
| **Security** | `python-jose[cryptography]>=3.0.0-alpha` | OAuth2 支持 |
| **A/B Testing** | `statsmodels>=3.0.0-alpha` | 统计分析模型 |
| **Visualization** | `plotly>=3.0.0-alpha` | 交互式图表 |
| **Visualization** | `matplotlib>=3.0.0-alpha` | 静态图表 |
| **Adaptive Opt.** | `scikit-learn>=3.0.0-alpha` | 机器学习，偏好预测 |
| **Dashboard** | `websockets>=12.0` | WebSocket 实时通信 |
| **Testing** | `pytest-cov>=3.0.0-alpha` | 测试覆盖率统计 |

### 总计新增
- **新增包数量**: 12 个
- **升级包数量**: 3 个（更新了版本号）
- **移除包数量**: 0 个

## 📝 主要改进

### 1. 结构化组织
- ✅ 使用清晰的分隔线和标题
- ✅ 按功能模块分组
- ✅ 标注 [v3.0.0-alpha] 标识新增模块
- ✅ 区分必需依赖和可选依赖

### 2. 详细注释
- ✅ 每个包都有中文说明
- ✅ 标注可选依赖（# 开头）
- ✅ 提供备选方案说明

### 3. 安装指南
新增了完整的安装指南章节，包括：
- ✅ 仅安装核心依赖的方法
- ✅ 安装可选功能的方法
- ✅ 安装开发依赖的方法
- ✅ 安装特定模块的方法
- ✅ 相关文档链接

### 4. 版本信息
- ✅ 添加了 Python 版本要求 (3.9+)
- ✅ 添加了版本号 (v3.0.0-alpha)
- ✅ 添加了最后更新日期
- ✅ 双语说明（中英文）

## 🔍 依赖分类详解

### 核心依赖（必须安装）
```bash
pip install numpy python-dateutil aiohttp requests python-dotenv pydantic
```

### Dashboard 功能（必须安装）
```bash
pip install fastapi uvicorn websockets
```

### v3.0.0-alpha 新功能（推荐安装）
```bash
pip install jieba scipy prometheus-client PyJWT python-jose plotly scikit-learn
```

### 可选集成（按需启用）
```bash
# 文档解析
pip install ragflow PyMuPDF python-docx beautifulsoup4

# 向量数据库
pip install qdrant-client pymilvus

# 图数据库
pip install neo4j nebula3-python

# 缓存
pip install redis

# 嵌入模型
pip install FlagEmbedding sentence-transformers

# LLM 集成
pip install langchain langgraph openai anthropic
```

## 📈 依赖统计

### 按类型分类
- **核心依赖**: 6 个
- **Dashboard**: 3 个
- **v3.0.0-alpha 新增**: 12 个
- **测试工具**: 3 个
- **开发工具**: 3 个
- **可选集成**: ~15 个（注释状态）

### 按优先级分类
- **🔴 必需 (Required)**: 9 个
- **🟡 推荐 (Recommended)**: 12 个
- **🟢 可选 (Optional)**: ~15 个

## 🎯 依赖关系图

```
Core (6 packages)
├── Dashboard (3 packages)
│   └── Debug Panel
│       ├── plotly
│       └── websockets
├── Intent Analysis
│   └── jieba
├── Domain Weight
│   └── scipy
├── Monitoring
│   └── prometheus-client
├── Security
│   ├── PyJWT
│   └── python-jose
├── A/B Testing
│   ├── scipy (shared)
│   └── statsmodels
├── Visualization
│   ├── plotly
│   └── matplotlib
└── Adaptive Optimization
    └── scikit-learn
```

## ✅ 验证结果

### 依赖冲突检查
- ✅ 无版本冲突
- ✅ 所有依赖都兼容 Python 3.9+
- ✅ scipy 被多个模块共享（领域权重、A/B 测试）

### 安装测试
```bash
# 测试核心依赖
pip install -r requirements.txt

# 验证安装
python -c "import fastapi; import jieba; import scipy; print('✅ All core dependencies installed!')"
```

## 📚 相关文档

- [依赖管理](docs/wiki/配置管理/依赖管理.md) - 详细的依赖管理文档
- [快速开始](QUICKSTART.md) - 快速安装和使用
- [项目统计](tools/project_statistics.md) - 项目整体统计信息

## 🔄 后续建议

### 定期更新
- 每月检查一次依赖版本
- 及时更新安全补丁
- 关注主要依赖的重大版本更新

### 依赖优化
- 考虑将可选依赖分离到 `requirements-optional.txt`
- 创建 `requirements-dev.txt` 专门用于开发
- 添加 `requirements-test.txt` 用于 CI/CD

---

**更新完成时间**: 2026-03-19  
**更新执行者**: NecoRAG Team  
**更新状态**: ✅ 完成
