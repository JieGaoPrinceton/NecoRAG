"""
Team Layer - 团队数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TeamRole(Enum):
    """团队角色枚举"""
    OWNER = "owner"  # 团队所有者
    ADMIN = "admin"  # 团队管理员
    MEMBER = "member"  # 团队成员
    GUEST = "guest"  # 访客


class PermissionType(Enum):
    """权限类型枚举"""
    READ = "read"  # 读取
    WRITE = "write"  # 写入
    DELETE = "delete"  # 删除
    SHARE = "share"  # 分享
    AUDIT = "audit"  # 审核
    MANAGE = "manage"  # 管理


@dataclass
class TeamMembership:
    """团队成员资格"""
    team_id: str
    user_id: str
    role: TeamRole
    permissions: List[PermissionType] = field(default_factory=list)
    joined_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def has_permission(self, permission: PermissionType) -> bool:
        """检查是否有指定权限"""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "team_id": self.team_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "permissions": [p.value for p in self.permissions],
            "joined_at": self.joined_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


@dataclass
class HybridCollaborationSpace:
    """混合协作空间（团队级）"""
    space_id: str
    name: str
    description: str
    parent_org_id: Optional[str] = None  # 所属组织 ID
    
    # 层级结构
    level: str = "team"  # organization/team/project
    parent_space_id: Optional[str] = None  # 父空间 ID
    child_spaces: List[str] = field(default_factory=list)  # 子空间 ID 列表
    
    # 成员和权限
    members: List[TeamMembership] = field(default_factory=list)
    max_members: int = 100
    
    # 知识配置
    knowledge_sync_with_public: bool = False  # 是否与公共知识同步
    allow_share_to_public: bool = True  # 是否允许分享到公共空间
    
    # 统计信息
    documents_count: int = 0
    members_count: int = 0
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_member(self, membership: TeamMembership):
        """添加成员"""
        self.members.append(membership)
        self.members_count = len(self.members)
    
    def remove_member(self, user_id: str):
        """移除成员"""
        self.members = [m for m in self.members if m.user_id != user_id]
        self.members_count = len(self.members)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "space_id": self.space_id,
            "name": self.name,
            "description": self.description,
            "parent_org_id": self.parent_org_id,
            "level": self.level,
            "parent_space_id": self.parent_space_id,
            "child_spaces": self.child_spaces,
            "members": [m.to_dict() for m in self.members],
            "max_members": self.max_members,
            "knowledge_sync_with_public": self.knowledge_sync_with_public,
            "allow_share_to_public": self.allow_share_to_public,
            "documents_count": self.documents_count,
            "members_count": self.members_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
