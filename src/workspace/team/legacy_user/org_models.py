"""
组织与工作空间数据模型

实现从个人 (user) → 团队 (team) → 组织 (workspace/organization) 的三级架构
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class OrganizationRole(Enum):
    """组织角色枚举"""
    INTERN = "intern"  # 实习生
    MEMBER = "member"  # 普通成员
    SENIOR = "senior"  # 高级成员
    MANAGER = "manager"  # 经理
    DIRECTOR = "director"  # 总监
    CEO = "ceo"  # 首席执行官
    OWNER = "owner"  # 所有者


class OrganizationType(Enum):
    """组织类型枚举"""
    COMPANY = "company"  # 公司
    DEPARTMENT = "department"  # 部门
    TEAM = "team"  # 团队
    PROJECT = "project"  # 项目组
    COMMUNITY = "community"  # 社区
    SCHOOL = "school"  # 学校
    OTHER = "other"  # 其他


@dataclass
class OrganizationMembership:
    """组织成员资格"""
    org_id: str
    user_id: str
    role: OrganizationRole
    department: Optional[str] = None  # 所属部门
    title: Optional[str] = None  # 职位头衔
    joined_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "org_id": self.org_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "department": self.department,
            "title": self.title,
            "joined_at": self.joined_at.isoformat(),
            "is_active": self.is_active,
            "permissions": self.permissions
        }


@dataclass
class Department:
    """部门结构"""
    dept_id: str
    name: str
    parent_org_id: str
    description: str = ""
    manager_id: Optional[str] = None  # 部门负责人
    members: List[str] = field(default_factory=list)  # 成员 ID 列表
    child_departments: List[str] = field(default_factory=list)  # 子部门
    
    def add_member(self, user_id: str):
        """添加成员"""
        if user_id not in self.members:
            self.members.append(user_id)
    
    def remove_member(self, user_id: str):
        """移除成员"""
        if user_id in self.members:
            self.members.remove(user_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "dept_id": self.dept_id,
            "name": self.name,
            "parent_org_id": self.parent_org_id,
            "description": self.description,
            "manager_id": self.manager_id,
            "members": self.members,
            "child_departments": self.child_departments
        }


@dataclass
class Organization:
    """
    组织（工作空间）
    
    这是最高层级的结构，可以包含多个团队和部门
    例如：一个公司、一个学校、一个开源社区等
    """
    org_id: str
    name: str
    org_type: OrganizationType = OrganizationType.COMPANY
    description: str = ""
    
    # 层级结构
    parent_org_id: Optional[str] = None  # 父组织 ID（用于集团 - 子公司结构）
    child_orgs: List[str] = field(default_factory=list)  # 子组织 ID 列表
    
    # 组织架构
    departments: Dict[str, Department] = field(default_factory=dict)  # 部门列表
    teams: List[str] = field(default_factory=list)  # 团队 ID 列表
    
    # 成员管理
    members: Dict[str, OrganizationMembership] = field(default_factory=dict)  # 成员资格
    max_members: int = 10000  # 最大成员数
    
    # 配置
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "allow_public_join": False,  # 允许公开加入
        "require_approval": True,  # 加入需要审批
        "visibility": "private",  # private/public/invite_only
        "default_member_role": OrganizationRole.MEMBER.value
    })
    
    # 统计信息
    total_teams: int = 0
    total_departments: int = 0
    active_members: int = 0
    
    # 元数据
    created_by: str = ""  # 创建者 ID
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_member(self, membership: OrganizationMembership):
        """添加组织成员"""
        self.members[membership.user_id] = membership
        self.active_members = len([m for m in self.members.values() if m.is_active])
    
    def remove_member(self, user_id: str):
        """移除组织成员"""
        if user_id in self.members:
            del self.members[user_id]
            self.active_members = len([m for m in self.members.values() if m.is_active])
    
    def add_team(self, team_id: str):
        """添加团队"""
        if team_id not in self.teams:
            self.teams.append(team_id)
            self.total_teams = len(self.teams)
    
    def remove_team(self, team_id: str):
        """移除团队"""
        if team_id in self.teams:
            self.teams.remove(team_id)
            self.total_teams = len(self.teams)
    
    def add_department(self, department: Department):
        """添加部门"""
        self.departments[department.dept_id] = department
        self.total_departments = len(self.departments)
    
    def get_member_role(self, user_id: str) -> Optional[OrganizationRole]:
        """获取成员在组织中的角色"""
        membership = self.members.get(user_id)
        if membership:
            return membership.role
        return None
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """检查成员是否有指定权限"""
        membership = self.members.get(user_id)
        if not membership:
            return False
        return permission in membership.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "org_id": self.org_id,
            "name": self.name,
            "org_type": self.org_type.value,
            "description": self.description,
            "parent_org_id": self.parent_org_id,
            "child_orgs": self.child_orgs,
            "departments": {k: v.to_dict() for k, v in self.departments.items()},
            "teams": self.teams,
            "members": {k: v.to_dict() for k, v in self.members.items()},
            "max_members": self.max_members,
            "settings": self.settings,
            "total_teams": self.total_teams,
            "total_departments": self.total_departments,
            "active_members": self.active_members,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class WorkspaceHierarchy:
    """
    工作空间层级关系
    
    维护 user → team → organization 的完整层级结构
    """
    user_id: str
    team_ids: List[str] = field(default_factory=list)  # 用户所属的团队
    org_ids: List[str] = field(default_factory=list)  # 用户所属的组织
    primary_org_id: Optional[str] = None  # 主要所属组织
    primary_team_id: Optional[str] = None  # 主要所属团队
    
    def add_team(self, team_id: str):
        """添加团队"""
        if team_id not in self.team_ids:
            self.team_ids.append(team_id)
    
    def remove_team(self, team_id: str):
        """移除团队"""
        if team_id in self.team_ids:
            self.team_ids.remove(team_id)
    
    def add_organization(self, org_id: str):
        """添加组织"""
        if org_id not in self.org_ids:
            self.org_ids.append(org_id)
    
    def remove_organization(self, org_id: str):
        """移除组织"""
        if org_id in self.org_ids:
            self.org_ids.remove(org_id)
            # 如果移除的是主要组织，清空主要组织设置
            if self.primary_org_id == org_id:
                self.primary_org_id = self.org_ids[0] if self.org_ids else None
    
    def set_primary_organization(self, org_id: str):
        """设置主要组织"""
        if org_id in self.org_ids:
            self.primary_org_id = org_id
    
    def set_primary_team(self, team_id: str):
        """设置主要团队"""
        if team_id in self.team_ids:
            self.primary_team_id = team_id
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "team_ids": self.team_ids,
            "org_ids": self.org_ids,
            "primary_org_id": self.primary_org_id,
            "primary_team_id": self.primary_team_id
        }


@dataclass
class WorkspaceConfig:
    """工作空间全局配置"""
    # 存储配置
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    neo4j_uri: str = "bolt://localhost:7687"
    
    # 缓存配置
    cache_ttl_seconds: int = 3600  # 缓存过期时间
    enable_caching: bool = True
    
    # 同步配置
    sync_enabled: bool = True
    sync_interval_minutes: int = 5  # 同步间隔
    
    # 权限配置
    default_visibility: str = "private"
    allow_cross_org_collaboration: bool = True
    
    # 审计配置
    audit_logging_enabled: bool = True
    log_retention_days: int = 90
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "redis_url": self.redis_url,
            "qdrant_url": self.qdrant_url,
            "neo4j_uri": self.neo4j_uri,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_caching": self.enable_caching,
            "sync_enabled": self.sync_enabled,
            "sync_interval_minutes": self.sync_interval_minutes,
            "default_visibility": self.default_visibility,
            "allow_cross_org_collaboration": self.allow_cross_org_collaboration,
            "audit_logging_enabled": self.audit_logging_enabled,
            "log_retention_days": self.log_retention_days
        }
