# 👥 多用户系统与知识空间管理模块

## 📖 模块概述

本模块实现了 NecoRAG 的**多用户系统与知识空间架构**，支持个人工作空间、公共贡献空间和混合协作空间三种知识管理场景。

## 🏗️ 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                    多用户系统架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户层 (User Layer)                                        │
│  ├── UserProfile (用户画像)                                 │
│  ├── UserPreference (用户偏好)                              │
│  └── QueryRecord (查询记录)                                 │
│                                                             │
│  权限层 (Permission Layer)                                  │
│  ├── PermissionManager (权限管理器)                         │
│  ├── AccessControl (访问控制器)                             │
│  └── PrivacyProtection (隐私保护)                           │
│                                                             │
│  空间层 (Space Layer)                                       │
│  ├── PersonalWorkspace (个人工作空间)                       │
│  ├── PublicContributionSpace (公共贡献空间)                 │
│  └── HybridCollaborationSpace (混合协作空间)                │
│                                                             │
│  管理层 (Management Layer)                                  │
│  ├── UserManager (用户管理器)                               │
│  └── WorkspaceManager (空间管理器)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 核心功能

### 1. 用户画像与权限管理

- **用户角色**: USER → CONTRIBUTOR → DOMAIN_EXPERT → ADMIN
- **权限类型**: READ, WRITE, DELETE, SHARE, AUDIT, MANAGE
- **隐私保护**: 数据隔离、加密存储、审计追踪

### 2. 个人工作空间 (Personal Workspace)

**特性**:
- 私有知识库和个性化配置
- L1/L2/L3 记忆分区独立
- 隐私保护查询
- 临时知识候选池

**使用示例**:
```python
from src.user import UserManager, WorkspaceManager

# 创建用户
user_manager = UserManager()
user = await user_manager.create_user(
    username="Alice",
    email="alice@example.com",
    password_hash="hashed_password"
)

# 创建个人空间
workspace_manager = WorkspaceManager()
space = await workspace_manager.create_personal_space(user.user_id)

# 上传文档
doc_id = await workspace_manager.upload_to_personal(
    user_id=user.user_id,
    document_data={"title": "My Document", "content": "..."}
)

# 检索
results = await workspace_manager.search_in_personal(
    user_id=user.user_id,
    query="search query",
    top_k=5
)
```

### 3. 公共贡献空间 (Public Contribution Space)

**贡献流程**:
```
提交贡献 → 自动质量评估 → 专家审核 → 批准/拒绝 → 更新积分
```

**激励机制**:
- 贡献积分 = 基础分 + 质量系数 + 被引用次数
- 领域声望 = 领域内贡献加权求和
- 贡献等级 = 累计积分 + 声望阈值

**使用示例**:
```python
# 提交贡献
contribution = await workspace_manager.submit_contribution(
    user_id=user.user_id,
    knowledge_id="know_001",
    title="Transformer 详解",
    content="Transformer 是一种...",
    domain="AI"
)

# 审核（专家）
approved = await workspace_manager.approve_contribution(
    contribution_id=contribution.contribution_id,
    reviewer_id="expert_001",
    comments="内容质量高"
)

# 更新积分
await user_manager.update_contribution_score(
    user.user_id,
    score_delta=20,
    contribution_id=contribution.contribution_id
)
```

### 4. 混合协作空间 (Hybrid Collaboration Space)

**层级结构**:
```
组织 (Organization)
├── 团队 A (Team A)
│   ├── 项目 A1 (Project A1)
│   └── 项目 A2 (Project A2)
└── 团队 B (Team B)
```

**团队角色**: OWNER → ADMIN → MEMBER → GUEST

**使用示例**:
```python
# 创建团队
team = await workspace_manager.create_team_space(
    name="NLP 研究小组",
    description="专注于 NLP 技术研究",
    creator_id=user.user_id
)

# 添加成员
await workspace_manager.add_team_member(
    space_id=team.space_id,
    user_id="user_bob",
    role=TeamRole.MEMBER,
    permissions=[PermissionType.READ, PermissionType.WRITE]
)

# 分享到公共空间
shared = await workspace_manager.share_team_to_public(
    space_id=team.space_id,
    knowledge_ids=["doc_1", "doc_2"],
    requester_id=user.user_id
)
```

## 🔐 安全与隐私

### 权限检查
```python
from src.user import PermissionManager, AccessControl

permission_manager = PermissionManager()
access_control = AccessControl(permission_manager)

# 检查权限
can_read = permission_manager.check_permission(
    user=user,
    permission=PermissionType.READ,
    space_type=SpaceType.PUBLIC
)

# 访问控制决策
allowed = access_control.can_access(
    user=user,
    resource_type="document",
    resource_id="doc_001",
    action="read",
    context={"space_type": "public", "space_id": "public_space"}
)
```

### 隐私保护
- **数据隔离**: 个人空间与公共空间物理隔离
- **加密存储**: AES-256 加密个人隐私数据
- **审计追踪**: 全操作日志记录
- **遗忘权**: 支持彻底删除个人数据
- **数据可携带**: 导出为标准格式 (JSON/Markdown)

## 📊 跨空间知识流动

### 流动规则

| 流向 | 规则 | 说明 |
|------|------|------|
| 个人 → 公共 | 申请 + 审核 | 确保质量 |
| 公共 → 个人 | 自动授权 | 自由引用 |
| 团队 → 公共 | 管理员审批 | 批量分享 |
| 公共 → 团队 | 镜像同步 | 支持离线 |
| 个人 ↔ 团队 | 基于权限 | 自动流转 |

### 冲突解决
- **优先级**: 公共空间 > 团队空间 > 个人空间
- **版本合并**: 支持手动/自动合并
- **差异对比**: 可视化工具
- **变更通知**: 自动通知相关方

## 🧪 测试

运行测试:
```bash
pytest tests/test_user/test_multi_user_system.py -v
```

运行示例:
```bash
python src/user/example_usage.py
```

## 📝 数据模型

详细的数据模型定义请参考：
- [`src/user/models.py`](src/user/models.py) - 完整数据模型
- [`src/user/manager.py`](src/user/manager.py) - 管理器实现
- [`src/user/permissions.py`](src/user/permissions.py) - 权限控制

## 🚀 后续计划

### Phase 2: 模块详细设计 (进行中) 🔄
- [ ] 个人空间详细设计（存储结构、索引优化）
- [ ] 公共空间审核流程实现
- [ ] 贡献追踪与激励系统
- [ ] 跨空间知识流动协议

### Phase 3: 技术实现 (计划中) 📅
- [ ] 用户认证与授权服务
- [ ] 个人空间管理服务
- [ ] 公共贡献审核平台
- [ ] 团队协作空间管理
- [ ] 知识溯源与版本控制

### Phase 4: 测试与优化 (计划中) 📅
- [ ] 单元测试与集成测试
- [ ] 性能优化（大规模用户并发）
- [ ] 安全审计与渗透测试
- [ ] 用户体验优化

## 📚 相关文档

- [主设计文档](../../design/design.md) - 第三章核心架构设计
- [多用户系统设计](../../design/MULTI_USER_SYSTEM_DESIGN.md) - 详细设计说明
- [安全模块](../security/README.md) - 安全与认证

## 🎉 总结

本模块为 NecoRAG 提供了完整的**多用户系统与知识空间管理能力**，实现了：

1. ✅ **个人隐私保护**：每个用户拥有独立的私有工作空间
2. ✅ **知识共享激励**：通过贡献机制鼓励用户分享知识
3. ✅ **灵活协作**：支持团队/组织级别的半公开知识共享
4. ✅ **安全可控**：多层安全防护，符合法规要求

让 AI 像大脑一样思考，像社会一样协作！🧠🌐
