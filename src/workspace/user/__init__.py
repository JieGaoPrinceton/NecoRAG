"""
User Layer - 个人用户层

提供用户画像、个人空间、用户偏好等个人级功能
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
    'PermissionType',
    'PersonalSpace',
    'PublicContributionSpace',
    'HybridCollaborationSpace',
    'SpaceType',
    'UserRole',
    
    # Managers
    'UserManager',
    'WorkspaceManager',
    'PermissionManager',
    'AccessControl',
]
