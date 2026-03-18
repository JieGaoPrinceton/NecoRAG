"""
用户与空间管理器

实现用户管理、个人空间管理、公共贡献空间管理和协作空间管理的核心逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

from .models import (
    UserProfile, UserPreference, UserRole,
    PersonalSpace, PublicContributionSpace, HybridCollaborationSpace,
    KnowledgeContribution, TeamMembership, TeamRole, PermissionType,
    QueryRecord, SpaceType
)

logger = logging.getLogger(__name__)


class UserManager:
    """用户管理器"""
    
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.email_to_user_id: Dict[str, str] = {}
        
    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        avatar_url: Optional[str] = None,
        bio: Optional[str] = None,
        expertise_domains: Optional[List[str]] = None
    ) -> UserProfile:
        """创建新用户"""
        user_id = str(uuid.uuid4())
        
        # 创建用户画像
        profile = UserProfile(
            user_id=user_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
            bio=bio,
            expertise_domains=expertise_domains or [],
            private_config={"password_hash": password_hash}
        )
        
        # 保存用户
        self.users[user_id] = profile
        self.email_to_user_id[email] = user_id
        
        logger.info(f"User created: {user_id}, username: {username}")
        return profile
    
    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """获取用户信息"""
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """通过邮箱获取用户"""
        user_id = self.email_to_user_id.get(email)
        if user_id:
            return self.users.get(user_id)
        return None
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """更新用户资料"""
        profile = self.users.get(user_id)
        if not profile:
            return None
        
        # 更新公开信息
        for key in ["username", "avatar_url", "bio", "expertise_domains"]:
            if key in updates:
                setattr(profile, key, updates[key])
        
        # 更新私有配置
        if "private_config" in updates:
            profile.private_config.update(updates["private_config"])
        
        # 更新偏好
        if "preference_model" in updates:
            pref_data = updates["preference_model"]
            profile.preference_model = UserPreference(**pref_data)
        
        logger.info(f"User profile updated: {user_id}")
        return profile
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户（符合 GDPR 遗忘权）"""
        profile = self.users.get(user_id)
        if not profile:
            return False
        
        # 从索引中移除
        del self.email_to_user_id[profile.email]
        del self.users[user_id]
        
        logger.info(f"User deleted: {user_id}")
        return True
    
    async def export_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """导出用户数据（符合 GDPR 数据可携带权）"""
        profile = self.users.get(user_id)
        if not profile:
            return None
        
        # 导出为标准格式
        export_data = {
            "user_profile": profile.to_dict(),
            "export_time": datetime.now().isoformat(),
            "format_version": "1.0"
        }
        
        logger.info(f"User data exported: {user_id}")
        return export_data
    
    async def update_contribution_score(
        self,
        user_id: str,
        score_delta: int,
        contribution_id: Optional[str] = None
    ) -> bool:
        """更新贡献积分"""
        profile = self.users.get(user_id)
        if not profile:
            return False
        
        profile.contribution_score += score_delta
        
        # 检查是否可以升级角色
        if profile.role == UserRole.USER and profile.contribution_score >= 100:
            profile.role = UserRole.CONTRIBUTOR
            logger.info(f"User promoted to contributor: {user_id}")
        
        if contribution_id:
            profile.shared_contributions.append(contribution_id)
        
        return True


class WorkspaceManager:
    """工作空间管理器"""
    
    def __init__(self):
        self.personal_spaces: Dict[str, PersonalSpace] = {}
        self.public_space = PublicContributionSpace()
        self.team_spaces: Dict[str, HybridCollaborationSpace] = {}
        
    # ========== 个人空间管理 ==========
    
    async def create_personal_space(self, user_id: str) -> PersonalSpace:
        """为用户创建个人工作空间"""
        space_id = f"personal_{user_id}"
        
        space = PersonalSpace(
            space_id=space_id,
            user_id=user_id,
            memory_config={
                "l1_redis_instance": f"redis://localhost:6379/1?db={user_id}",
                "l2_qdrant_collection": f"personal_vectors_{user_id}",
                "l3_neo4j_subgraph": f"personal_graph_{user_id}"
            }
        )
        
        self.personal_spaces[space_id] = space
        logger.info(f"Personal space created: {space_id} for user {user_id}")
        return space
    
    async def get_personal_space(self, user_id: str) -> Optional[PersonalSpace]:
        """获取用户的个人空间"""
        space_id = f"personal_{user_id}"
        return self.personal_spaces.get(space_id)
    
    async def upload_to_personal(
        self,
        user_id: str,
        document_data: Dict[str, Any]
    ) -> Optional[str]:
        """上传文档到个人空间"""
        space = await self.get_personal_space(user_id)
        if not space:
            space = await self.create_personal_space(user_id)
        
        # 模拟文档处理流程
        document_id = str(uuid.uuid4())
        
        # 更新统计
        space.documents_count += 1
        space.storage_used_bytes += document_data.get("size", 0)
        space.updated_at = datetime.now()
        
        logger.info(f"Document uploaded to personal space: {document_id} by user {user_id}")
        return document_id
    
    async def search_in_personal(
        self,
        user_id: str,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """在个人空间内检索"""
        # TODO: 实现实际的向量检索和图谱查询
        logger.info(f"Search in personal space: {query} by user {user_id}")
        return []
    
    # ========== 公共贡献空间管理 ==========
    
    async def submit_contribution(
        self,
        user_id: str,
        knowledge_id: str,
        title: str,
        content: str,
        domain: str
    ) -> KnowledgeContribution:
        """提交知识贡献到公共空间"""
        contribution = KnowledgeContribution(
            contribution_id=str(uuid.uuid4()),
            contributor_id=user_id,
            knowledge_id=knowledge_id,
            title=title,
            content=content,
            domain=domain
        )
        
        # 自动质量评估
        quality_score = await self._auto_evaluate_quality(contribution)
        contribution.quality_score = quality_score
        
        logger.info(
            f"Contribution submitted: {contribution.contribution_id} "
            f"by user {user_id}, quality: {quality_score:.2f}"
        )
        return contribution
    
    async def _auto_evaluate_quality(
        self,
        contribution: KnowledgeContribution
    ) -> float:
        """自动质量评估"""
        # TODO: 实现实际的质量评估算法
        # 基于内容长度、语言质量、原创性等维度评分
        base_score = 0.7
        
        # 内容长度评分
        length_bonus = min(len(contribution.content) / 1000, 0.2)
        
        # 标题质量
        title_bonus = 0.1 if len(contribution.title) > 10 else 0.0
        
        return min(base_score + length_bonus + title_bonus, 1.0)
    
    async def approve_contribution(
        self,
        contribution_id: str,
        reviewer_id: str,
        comments: Optional[str] = None
    ) -> bool:
        """批准知识贡献"""
        # TODO: 实现实际的审核逻辑
        logger.info(f"Contribution approved: {contribution_id} by reviewer {reviewer_id}")
        return True
    
    async def reject_contribution(
        self,
        contribution_id: str,
        reviewer_id: str,
        comments: str
    ) -> bool:
        """拒绝知识贡献"""
        # TODO: 实现实际的拒绝逻辑
        logger.info(f"Contribution rejected: {contribution_id} by reviewer {reviewer_id}")
        return True
    
    # ========== 混合协作空间管理 ==========
    
    async def create_team_space(
        self,
        name: str,
        description: str,
        creator_id: str,
        level: str = "team",
        parent_org_id: Optional[str] = None
    ) -> HybridCollaborationSpace:
        """创建团队协作空间"""
        space_id = f"team_{uuid.uuid4().hex[:8]}"
        
        space = HybridCollaborationSpace(
            space_id=space_id,
            name=name,
            description=description,
            parent_org_id=parent_org_id,
            level=level
        )
        
        # 创建者自动成为团队所有者
        owner_membership = TeamMembership(
            team_id=space_id,
            user_id=creator_id,
            role=TeamRole.OWNER,
            permissions=[
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.DELETE,
                PermissionType.SHARE,
                PermissionType.AUDIT,
                PermissionType.MANAGE
            ]
        )
        space.add_member(owner_membership)
        
        self.team_spaces[space_id] = space
        logger.info(f"Team space created: {space_id} by user {creator_id}")
        return space
    
    async def add_team_member(
        self,
        space_id: str,
        user_id: str,
        role: TeamRole,
        permissions: List[PermissionType],
        expires_at: Optional[datetime] = None
    ) -> bool:
        """添加团队成员"""
        space = self.team_spaces.get(space_id)
        if not space:
            return False
        
        membership = TeamMembership(
            team_id=space_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
            expires_at=expires_at
        )
        
        space.add_member(membership)
        logger.info(f"Member added to team {space_id}: user {user_id} as {role.value}")
        return True
    
    async def remove_team_member(
        self,
        space_id: str,
        user_id: str
    ) -> bool:
        """移除团队成员"""
        space = self.team_spaces.get(space_id)
        if not space:
            return False
        
        space.remove_member(user_id)
        logger.info(f"Member removed from team {space_id}: user {user_id}")
        return True
    
    async def share_team_to_public(
        self,
        space_id: str,
        knowledge_ids: List[str],
        requester_id: str
    ) -> bool:
        """将团队知识分享到公共空间"""
        space = self.team_spaces.get(space_id)
        if not space:
            return False
        
        # 检查权限
        member = next((m for m in space.members if m.user_id == requester_id), None)
        if not member or not member.has_permission(PermissionType.SHARE):
            logger.warning(f"User {requester_id} lacks share permission in team {space_id}")
            return False
        
        # 批量提交到公共空间
        for knowledge_id in knowledge_ids:
            # TODO: 实现实际的分享逻辑
            pass
        
        logger.info(f"Team knowledge shared to public: {len(knowledge_ids)} items from {space_id}")
        return True
    
    # ========== 跨空间知识流动 ==========
    
    async def sync_public_to_team(
        self,
        space_id: str,
        knowledge_ids: List[str]
    ) -> bool:
        """同步公共知识到团队空间"""
        space = self.team_spaces.get(space_id)
        if not space:
            return False
        
        if not space.knowledge_sync_with_public:
            logger.warning(f"Team {space_id} has public sync disabled")
            return False
        
        # TODO: 实现实际的同步逻辑
        logger.info(f"Public knowledge synced to team {space_id}: {len(knowledge_ids)} items")
        return True
    
    async def mirror_public_knowledge(
        self,
        space_id: str,
        enable_offline: bool = True
    ) -> bool:
        """镜像公共知识到团队空间（支持离线使用）"""
        space = self.team_spaces.get(space_id)
        if not space:
            return False
        
        # TODO: 实现实际的镜像逻辑
        logger.info(f"Public knowledge mirrored to team {space_id}, offline: {enable_offline}")
        return True
