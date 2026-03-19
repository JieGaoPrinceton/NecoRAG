"""
Organization Layer - 组织层

提供组织架构、部门管理、跨组织协作等组织级功能
"""

from .org_models import (
    Organization,
    OrganizationMembership,
    OrganizationRole,
    OrganizationType,
    Department,
    WorkspaceHierarchy,
    WorkspaceConfig,
)
from .org_manager import OrganizationManager, WorkspaceManager

__all__ = [
    # Models
    'Organization',
    'OrganizationMembership',
    'OrganizationRole',
    'OrganizationType',
    'Department',
    'WorkspaceHierarchy',
    'WorkspaceConfig',
    
    # Managers
    'OrganizationManager',
    'WorkspaceManager',
]
