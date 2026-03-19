"""
多用户系统与知识空间管理模块

提供从个人 (user) → 团队 (team) → 组织 (workspace/organization) 的三级架构完整实现
"""

from .models import (
    UserProfile,
    UserPreference,
    QueryRecord,
    KnowledgeContribution,
    TeamMembership,
    TeamRole,
    PermissionType,
    PersonalSpace,
    PublicContributionSpace,
    HybridCollaborationSpace,
    SpaceType,
    UserRole,
)
from .manager import UserManager, WorkspaceManager as TeamWorkspaceManager
from .permissions import PermissionManager, AccessControl
from .org_models import (
    Organization,
    OrganizationMembership,
    OrganizationRole,
    OrganizationType,
    Department,
    WorkspaceHierarchy,
    WorkspaceConfig,
)
from .org_manager import OrganizationManager, WorkspaceManager as OrgWorkspaceManager

__all__ = [
    # Models - User & Team
    'UserProfile',
    'UserPreference',
    'QueryRecord',
    'KnowledgeContribution',
    'TeamMembership',
    'TeamRole',
    'PermissionType',
    'PersonalSpace',
    'PublicContributionSpace',
    'HybridCollaborationSpace',
    'SpaceType',
    'UserRole',
    
    # Models - Organization
    'Organization',
    'OrganizationMembership',
    'OrganizationRole',
    'OrganizationType',
    'Department',
    'WorkspaceHierarchy',
    'WorkspaceConfig',
    
    # Managers - User & Team
    'UserManager',
    'TeamWorkspaceManager',
    'PermissionManager',
    'AccessControl',
    
    # Managers - Organization
    'OrganizationManager',
    'OrgWorkspaceManager',
]
