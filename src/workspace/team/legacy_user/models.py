"""
多用户系统数据模型

实现用户画像、知识空间、权限等相关的数据模型
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class UserRole(Enum):
    """用户角色枚举"""
    USER = "user"  # 普通用户
    CONTRIBUTOR = "contributor"  # 贡献者
    DOMAIN_EXPERT = "domain_expert"  # 领域专家
    ADMIN = "admin"  # 管理员


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


class SpaceType(Enum):
    """空间类型枚举"""
    PERSONAL = "personal"  # 个人工作空间
    PUBLIC = "public"  # 公共贡献空间
    TEAM = "team"  # 混合协作空间


@dataclass
class UserPreference:
    """用户偏好模型"""
    tone: str = "professional"  # 响应风格：professional/friendly/humorous
    detail_level: int = 3  # 详细程度：1-4
    preferred_domains: List[str] = field(default_factory=list)  # 偏好领域
    notification_enabled: bool = True  # 启用通知
    privacy_mode: bool = False  # 隐私模式
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tone": self.tone,
            "detail_level": self.detail_level,
            "preferred_domains": self.preferred_domains,
            "notification_enabled": self.notification_enabled,
            "privacy_mode": self.privacy_mode
        }


@dataclass
class QueryRecord:
    """查询记录"""
    query_id: str
    user_id: str
    query_text: str
    timestamp: datetime
    results_count: int = 0
    space_type: SpaceType = SpaceType.PERSONAL
    is_private: bool = False  # 是否为隐私查询
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query_id": self.query_id,
            "user_id": self.user_id,
            "query_text": self.query_text,
            "timestamp": self.timestamp.isoformat(),
            "results_count": self.results_count,
            "space_type": self.space_type.value,
            "is_private": self.is_private
        }


@dataclass
class KnowledgeContribution:
    """知识贡献"""
    contribution_id: str
    contributor_id: str
    knowledge_id: str
    title: str
    content: str
    domain: str
    status: str = "pending"  # pending/reviewed/approved/rejected
    quality_score: float = 0.0
    submit_time: datetime = field(default_factory=datetime.now)
    review_time: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    review_comments: Optional[str] = None
    citations_count: int = 0  # 被引用次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "contribution_id": self.contribution_id,
            "contributor_id": self.contributor_id,
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "content": self.content,
            "domain": self.domain,
            "status": self.status,
            "quality_score": self.quality_score,
            "submit_time": self.submit_time.isoformat(),
            "review_time": self.review_time.isoformat() if self.review_time else None,
            "reviewer_id": self.reviewer_id,
            "review_comments": self.review_comments,
            "citations_count": self.citations_count
        }


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
class UserProfile:
    """用户画像"""
    # 基础信息（公开可见）
    user_id: str
    username: str
    email: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    expertise_domains: List[str] = field(default_factory=list)
    contribution_score: int = 0
    role: UserRole = UserRole.USER
    
    # 个人隐私（仅自己可见）
    private_config: Dict[str, Any] = field(default_factory=dict)
    preference_model: UserPreference = field(default_factory=UserPreference)
    
    # 知识空间权限
    personal_space_id: Optional[str] = None
    shared_contributions: List[str] = field(default_factory=list)  # 已分享的知识贡献 ID 列表
    team_memberships: List[TeamMembership] = field(default_factory=list)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    def get_public_info(self) -> Dict[str, Any]:
        """获取公开信息"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "expertise_domains": self.expertise_domains,
            "contribution_score": self.contribution_score,
            "role": self.role.value
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（包含私有信息）"""
        return {
            **self.get_public_info(),
            "email": self.email,
            "private_config": self.private_config,
            "preference_model": self.preference_model.to_dict(),
            "personal_space_id": self.personal_space_id,
            "shared_contributions": self.shared_contributions,
            "team_memberships": [m.to_dict() for m in self.team_memberships],
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None
        }


@dataclass
class PersonalSpace:
    """个人工作空间"""
    space_id: str
    user_id: str
    name: str = "个人工作空间"
    description: str = ""
    
    # 存储配置
    memory_config: Dict[str, Any] = field(default_factory=lambda: {
        "l1_redis_instance": "redis://localhost:6379/0",
        "l2_qdrant_collection": "personal_vectors_{user_id}",
        "l3_neo4j_subgraph": "personal_graph_{user_id}"
    })
    
    # 统计信息
    documents_count: int = 0
    vectors_count: int = 0
    storage_used_bytes: int = 0
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "space_id": self.space_id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "memory_config": self.memory_config,
            "documents_count": self.documents_count,
            "vectors_count": self.vectors_count,
            "storage_used_bytes": self.storage_used_bytes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class PublicContributionSpace:
    """公共贡献空间"""
    space_id: str = "public_space"
    name: str = "公共知识库"
    description: str = "社区共享的知识库"
    
    # 统计信息
    total_contributions: int = 0
    active_contributors: int = 0
    domains_covered: List[str] = field(default_factory=list)
    
    # 审核配置
    auto_review_enabled: bool = True
    min_quality_threshold: float = 0.7
    expert_review_required: bool = True
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "space_id": self.space_id,
            "name": self.name,
            "description": self.description,
            "total_contributions": self.total_contributions,
            "active_contributors": self.active_contributors,
            "domains_covered": self.domains_covered,
            "auto_review_enabled": self.auto_review_enabled,
            "min_quality_threshold": self.min_quality_threshold,
            "expert_review_required": self.expert_review_required,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class HybridCollaborationSpace:
    """混合协作空间"""
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
