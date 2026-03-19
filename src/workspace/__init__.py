"""
NecoRAG Workspace - 三级用户系统

提供从个人 (User) → 团队 (Team) → 组织 (Organization) 的完整架构支持

层级结构:
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
"""

from . import user
from . import team
from . import organization

# 导出主要组件，方便使用
from .user import (
    UserManager,
    UserProfile,
    UserPreference,
    PermissionManager,
    AccessControl,
)

from .team import (
    TeamManager,
    TeamMembership,
    HybridCollaborationSpace,
)

from .organization import (
    OrganizationManager,
    WorkspaceManager,
    Organization,
    Department,
)

__all__ = [
    # User Layer
    'user',
    'UserManager',
    'UserProfile',
    'UserPreference',
    'PermissionManager',
    'AccessControl',
    
    # Team Layer
    'team',
    'TeamManager',
    'TeamMembership',
    'HybridCollaborationSpace',
    
    # Organization Layer
    'organization',
    'OrganizationManager',
    'WorkspaceManager',
    'Organization',
    'Department',
]
