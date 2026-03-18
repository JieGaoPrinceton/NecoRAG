"""
多用户系统与知识空间管理模块

提供个人工作空间、公共贡献空间和混合协作空间的完整实现
"""

from .models import (
    UserProfile,
    UserPreference,
    QueryRecord,
    KnowledgeContribution,
    TeamMembership,
    TeamRole,
    Permission,
    PersonalSpace,
    PublicContributionSpace,
    HybridCollaborationSpace,
)
from .manager import UserManager, WorkspaceManager
from .permissions import PermissionManager, AccessControl

__all__ = [
    # Models
    'UserProfile',
    'UserPreference',
    'QueryRecord',
    'KnowledgeContribution',
    'TeamMembership',
    'TeamRole',
    'Permission',
    'PersonalSpace',
    'PublicContributionSpace',
    'HybridCollaborationSpace',
    # Managers
    'UserManager',
    'WorkspaceManager',
    'PermissionManager',
    'AccessControl',
]
