# 贡献指南

感谢你考虑为 NecoRAG 做贡献！

## 🎯 贡献方式

### 1. 报告问题 🐛

如果你发现了 bug 或有功能建议：

1. 在 [Issues](https://gitee.com/qijie2026/NecoRAG/issues) 中搜索是否已存在
2. 如果不存在，创建新 Issue
3. 使用清晰的标题和详细的描述
4. 提供复现步骤（如果是 bug）

### 2. 提交代码 💻

#### 开发环境设置

```bash
# 1. Fork 项目
# 在 Gitee 上点击 Fork

# 2. 克隆你的 Fork
git clone https://gitee.com/YOUR_USERNAME/NecoRAG.git
cd NecoRAG

# 3. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 4. 安装依赖
pip install -r requirements.txt

# 5. 运行测试
python test_imports.py
```

#### 代码规范

- **Python 版本**: 3.9+
- **代码风格**: PEP 8
- **类型注解**: 尽量添加类型注解
- **文档字符串**: 使用中文文档字符串

#### 提交规范

使用语义化提交消息：

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具链
```

示例：
```
feat(memory): 添加 L3 图谱权重衰减机制
fix(retrieval): 修复 Pounce 阈值判断逻辑
docs(whiskers): 更新分块策略文档
```

#### Pull Request 流程

1. 创建特性分支
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. 提交更改
   ```bash
   git add .
   git commit -m "feat: 添加某某功能"
   ```

3. 推送到 Fork
   ```bash
   git push origin feature/amazing-feature
   ```

4. 创建 Pull Request
   - 在 Gitee 上创建 PR
   - 填写 PR 模板
   - 等待审核

### 3. 改进文档 📝

文档改进是最容易的贡献方式：

- 修复拼写错误
- 改进表述
- 添加示例
- 翻译文档

### 4. 分享想法 💡

- 在 Discussions 中分享你的想法
- 写博客文章介绍 NecoRAG
- 在社交媒体上分享

## 📋 开发指南

### 模块结构

```
necorag/
├── whiskers/      # 感知层
├── memory/        # 记忆层
├── retrieval/     # 检索层
├── grooming/      # 巩固层
├── purr/          # 交互层
└── dashboard/     # 配置管理
```

### 添加新功能

1. 在对应模块中添加代码
2. 更新模块的 `__init__.py`
3. 添加单元测试
4. 更新文档

### 测试

```bash
# 运行导入测试
python test_imports.py

# 运行完整示例
python example_usage.py

# 启动 Dashboard 测试
python start_dashboard.py
```

## 🎨 设计原则

1. **模块化**: 每个模块独立，职责单一
2. **可扩展**: 预留接口，易于扩展
3. **可解释**: 输出可追溯，过程可视化
4. **高效**: 优化性能，减少冗余

## 📊 性能基准

请确保你的更改不会显著降低性能：

- 导入时间: < 2s
- 基础操作: < 100ms
- Dashboard 启动: < 5s

## 🔍 代码审查

所有 PR 都需要经过审查：

1. 代码质量
2. 测试覆盖
3. 文档完整性
4. 性能影响

## 📝 许可证

通过贡献代码，你同意你的代码将在 MIT 许可证下发布。

## 🙏 感谢

感谢所有贡献者的付出！

---

<div align="center">

**让我们一起打造更好的 NecoRAG！** 🐱🧠

</div>
