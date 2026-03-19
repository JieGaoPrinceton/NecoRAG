# Workspace 三级用户系统 - 快速参考

## 🎯 一句话介绍

NecoRAG Workspace = **User（个人）→ Team（团队）→ Organization（组织）** 的完整三级架构

## ⚡ 30 秒上手

### 最简使用方式

```python
from src.workspace import UserManager, TeamManager, OrganizationManager

# Level 1: 创建用户
user_manager = UserManager()
alice = await user_manager.create_user("Alice", "alice@example.com")

# Level 2: 创建团队
team_manager = TeamManager()
nlp_team = await team_manager.create_team("NLP 小组", creator_id=alice.user_id)

# Level 3: 创建组织
org_manager = OrganizationManager()
company = await org_manager.create_organization("科技公司", creator_id=alice.user_id)
```

## 📋 常用 API 速查

### User Layer（个人层）

| 功能 | API | 示例 |
|------|-----|------|
| 创建用户 | `UserManager.create_user()` | `await mgr.create_user(name, email)` |
| 获取用户 | `UserManager.get_user()` | `user = await mgr.get_user(user_id)` |
| 更新资料 | `UserManager.update_user_profile()` | `await mgr.update(user_id, updates)` |
| 权限检查 | `PermissionManager.check_permission()` | `can_read = mgr.check(user, READ)` |

### Team Layer（团队层）

| 功能 | API | 示例 |
|------|-----|------|
| 创建团队 | `TeamManager.create_team()` | `team = await mgr.create_team(name)` |
| 添加成员 | `TeamManager.add_member()` | `await mgr.add_member(team_id, user_id)` |
| 移除成员 | `TeamManager.remove_member()` | `await mgr.remove_member(team_id, user_id)` |
| 获取统计 | `TeamManager.get_team_stats()` | `stats = await mgr.get_stats(team_id)` |

### Organization Layer（组织层）

| 功能 | API | 示例 |
|------|-----|------|
| 创建组织 | `OrganizationManager.create_organization()` | `org = await mgr.create_org(name)` |
| 添加成员 | `OrganizationManager.add_member()` | `await mgr.add_member(org_id, user_id)` |
| 创建部门 | `OrganizationManager.create_department()` | `dept = await mgr.create_dept(org_id, name)` |
| 获取统计 | `OrganizationManager.get_organization_stats()` | `stats = await mgr.get_stats(org_id)` |

## 🗂️ 目录结构

```
src/workspace/
├── user/              # 个人层
│   ├── models.py     # 用户模型
│   ├── manager.py    # 用户管理
│   └── permissions.py # 权限管理
│
├── team/              # 团队层
│   ├── models.py     # 团队模型
│   └── manager.py    # 团队管理
│
└── organization/      # 组织层
    ├── org_models.py # 组织模型
    └── org_manager.py # 组织管理
```

## 🎨 典型使用场景

### 场景 1：创业公司

```python
# 创建公司
company = await org_manager.create_organization(
    "AI 初创公司",
    org_type=OrganizationType.COMPANY
)

# 创建部门
await org_manager.create_department(company.org_id, "技术部")

# 创建团队
await team_manager.create_team(
    "核心开发组",
    parent_org_id=company.org_id
)
```

### 场景 2：开源社区

```python
# 创建社区
community = await org_manager.create_organization(
    "开源社区",
    org_type=OrganizationType.COMMUNITY,
    settings={"allow_public_join": True}
)

# 创建专项小组
await team_manager.create_team(
    "文档翻译组",
    parent_org_id=community.org_id
)
```

### 场景 3：学校实验室

```python
# 创建实验室
lab = await org_manager.create_organization(
    "AI 实验室",
    org_type=OrganizationType.SCHOOL
)

# 创建研究小组
await team_manager.create_team(
    "机器学习组",
    parent_org_id=lab.org_id
)
```

## 🔐 权限速查

### 用户角色权限

```
USER         → READ, WRITE
CONTRIBUTOR  → + SHARE, AUDIT  
DOMAIN_EXPERT → + MANAGE
ADMIN        → ALL
```

### 团队角色权限

```
GUEST   → READ
MEMBER  → READ, WRITE
ADMIN   → + DELETE, SHARE, AUDIT
OWNER   → ALL
```

### 组织角色权限

```
INTERN   → READ
MEMBER   → READ, WRITE
SENIOR   → + PARTICIPATE
MANAGER  → + TEAM_MANAGE
DIRECTOR → + DEPT_MANAGE
CEO      → + EXECUTIVE
OWNER    → ALL
```

## ⚠️ 常见问题

**Q: 如何导入模块？**
```python
from src.workspace import UserManager, TeamManager, OrganizationManager
```

**Q: 如何获取用户的完整层级？**
```python
hierarchy = await workspace_manager.get_user_complete_hierarchy(user_id)
```

**Q: 如何实现跨组织协作？**
```python
result = await workspace_manager.cross_organization_collaboration(
    source_org_id, target_org_id, user_id, resource_type, resource_id
)
```

## 📖 更多文档

- [WORKSPACE_README.md](WORKSPACE_README.md) - 总体架构
- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - 重构总结
- [team/user/README.md](team/user/README.md) - 原有多用户系统

---

**快速开始，就这么简单！** ✨

*NecoRAG Workspace © 2026*
