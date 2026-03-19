# 🏢 NecoRAG Workspace - 三级用户系统

## 📖 概述

NecoRAG Workspace 提供了完整的**三级用户系统架构**，从个人到团队再到组织，支持多层次的协作和知识管理。

```
Workspace (工作空间)
├── User Layer (个人层)
│   ├── UserProfile - 用户画像
│   ├── PersonalSpace - 个人空间
│   └── UserPreference - 用户偏好
│
├── Team Layer (团队层)
│   ├── HybridCollaborationSpace - 混合协作空间
│   ├── TeamMembership - 团队成员资格
│   └── TeamManager - 团队管理
│
└── Organization Layer (组织层)
    ├── Organization - 组织架构
    ├── Department - 部门结构
    └── OrganizationManager - 组织管理
```

## 🎯 快速开始

### 导入模块

```python
from src.workspace import (
    UserManager,           # 用户管理
    TeamManager,          # 团队管理
    OrganizationManager,  # 组织管理
    WorkspaceManager,     # 工作空间管理
)
```

### 分层使用

#### Level 1: User Layer（个人层）

```python
from src.workspace.user import UserManager, UserProfile

# 创建用户
user_manager = UserManager()
alice = await user_manager.create_user(
    username="Alice",
    email="alice@example.com"
)

# 查看用户信息
print(alice.get_public_info())
```

#### Level 2: Team Layer（团队层）

```python
from src.workspace.team import TeamManager, TeamRole

# 创建团队
team_manager = TeamManager()
nlp_team = await team_manager.create_team(
    name="NLP 研究小组",
    creator_id=alice.user_id
)

# 添加成员
await team_manager.add_member(
    team_id=nlp_team.space_id,
    user_id=bob.user_id,
    role=TeamRole.MEMBER
)
```

#### Level 3: Organization Layer（组织层）

```python
from src.workspace.organization import (
    OrganizationManager,
    OrganizationType
)

# 创建组织
org_manager = OrganizationManager()
company = await org_manager.create_organization(
    name="科技创新有限公司",
    org_type=OrganizationType.COMPANY,
    creator_id=alice.user_id
)

# 创建部门
await org_manager.create_department(
    org_id=company.org_id,
    name="研发部"
)
```

## 📁 目录结构

```
src/workspace/
├── __init__.py              # 主模块导出
├── WORKSPACE_README.md      # 本文档
│
├── user/                    # User Layer (个人层)
│   ├── __init__.py
│   ├── models.py           # 用户数据模型
│   ├── manager.py          # 用户管理器
│   └── permissions.py      # 权限管理
│
├── team/                    # Team Layer (团队层)
│   ├── __init__.py
│   ├── models.py           # 团队数据模型
│   └── manager.py          # 团队管理器
│
└── organization/            # Organization Layer (组织层)
    ├── __init__.py
    ├── org_models.py       # 组织数据模型
    └── org_manager.py      # 组织管理器
```

## 🔐 权限系统

### 用户层权限

| 角色 | 权限 |
|------|------|
| USER | READ, WRITE |
| CONTRIBUTOR | READ, WRITE, SHARE, AUDIT |
| DOMAIN_EXPERT | READ, WRITE, SHARE, AUDIT, MANAGE |
| ADMIN | 所有权限 |

### 团队层权限

| 角色 | 权限 |
|------|------|
| GUEST | READ |
| MEMBER | READ, WRITE |
| ADMIN | READ, WRITE, DELETE, SHARE, AUDIT |
| OWNER | 所有权限 |

### 组织层权限

| 角色 | 权限 |
|------|------|
| INTERN | 只读 |
| MEMBER | 读写、参与 |
| SENIOR | 高级成员权限 |
| MANAGER | 团队管理 |
| DIRECTOR | 部门管理 |
| CEO |  executive 权限 |
| OWNER | 完全控制 |

## 🔄 跨层协作

### 用户在多层级中的归属

```python
from src.workspace import WorkspaceManager

workspace_manager = WorkspaceManager(org_manager)

# 获取用户的完整层级结构
hierarchy = await workspace_manager.get_user_complete_hierarchy(user_id)

# 返回：
# {
#     "user_id": "...",
#     "organizations": [...],
#     "teams": [...]
# }
```

### 跨组织协作

```python
result = await workspace_manager.cross_organization_collaboration(
    source_org_id="org_001",
    target_org_id="org_002",
    user_id=alice.user_id,
    resource_type="document",
    resource_id="doc_001"
)
```

## 📊 统计与监控

### 组织统计

```python
stats = await org_manager.get_organization_stats(org_id)
print(stats)
# {
#     "total_members": 50,
#     "active_members": 45,
#     "total_teams": 8,
#     "total_departments": 5
# }
```

### 团队统计

```python
stats = await team_manager.get_team_stats(team_id)
print(stats)
# {
#     "members_count": 10,
#     "documents_count": 25
# }
```

## 🧪 测试

运行示例代码：

```bash
# 设置 PYTHONPATH
export PYTHONPATH=/path/to/NecoRAG:$PYTHONPATH

# 运行演示
python src/workspace/team/user/example_usage.py
```

## 📚 相关文档

- [User Layer 详细文档](user/README.md)
- [Team Layer 详细文档](team/README.md)
- [Organization Layer 详细文档](organization/README.md)
- [原有多用户系统文档](team/user/README.md)

## 🎉 总结

NecoRAG Workspace 的三级用户系统提供了：

1. ✅ **清晰的层级架构** - User → Team → Organization
2. ✅ **灵活的权限控制** - 每层独立的权限系统
3. ✅ **模块化设计** - 各层独立可测试
4. ✅ **易于使用** - 简洁的 API 接口
5. ✅ **可扩展性** - 支持大规模应用

---

*让 AI 像大脑一样思考，像社会一样协作！* 🧠🌐
