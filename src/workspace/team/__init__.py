"""
Team Layer - 团队协作层

提供团队管理、协作空间、团队成员权限等团队级功能
"""

from .models import (
    TeamMembership,
    TeamRole,
    PermissionType,
    HybridCollaborationSpace,
)
from .manager import TeamManager

__all__ = [
    # Models
    'TeamMembership',
    'TeamRole',
    'PermissionType',
    'HybridCollaborationSpace',
    
    # Managers
    'TeamManager',
]
