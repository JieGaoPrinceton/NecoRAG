"""
多用户系统单元测试
"""

import pytest
from datetime import datetime, timedelta
from src.user.models import (
    UserProfile, UserPreference, UserRole,
    PersonalSpace, PublicContributionSpace, HybridCollaborationSpace,
    KnowledgeContribution, TeamMembership, TeamRole, PermissionType,
    SpaceType
)
from src.user.manager import UserManager, WorkspaceManager
from src.user.permissions import PermissionManager, AccessControl


class TestUserModels:
    """测试用户数据模型"""
    
    def test_user_profile_creation(self):
        """测试用户画像创建"""
        profile = UserProfile(
            user_id="user_001",
            username="Alice",
            email="alice@example.com",
            expertise_domains=["AI", "NLP"]
        )
        
        assert profile.user_id == "user_001"
        assert profile.username == "Alice"
        assert profile.role == UserRole.USER
        assert profile.contribution_score == 0
    
    def test_user_profile_to_dict(self):
        """测试用户画像序列化"""
        profile = UserProfile(
            user_id="user_001",
            username="Alice",
            email="alice@example.com"
        )
        
        data = profile.to_dict()
        assert data["user_id"] == "user_001"
        assert data["username"] == "Alice"
        assert "email" in data
    
    def test_user_preference(self):
        """测试用户偏好"""
        pref = UserPreference(
            tone="friendly",
            detail_level=4,
            preferred_domains=["AI"]
        )
        
        assert pref.tone == "friendly"
        assert pref.detail_level == 4
        assert len(pref.preferred_domains) == 1
    
    def test_knowledge_contribution(self):
        """测试知识贡献模型"""
        contribution = KnowledgeContribution(
            contribution_id="contrib_001",
            contributor_id="user_001",
            knowledge_id="know_001",
            title="Test Article",
            content="This is test content",
            domain="AI"
        )
        
        assert contribution.status == "pending"
        assert contribution.quality_score == 0.0
        assert contribution.citations_count == 0
    
    def test_team_membership(self):
        """测试团队成员资格"""
        membership = TeamMembership(
            team_id="team_001",
            user_id="user_001",
            role=TeamRole.ADMIN,
            permissions=[PermissionType.READ, PermissionType.WRITE]
        )
        
        assert membership.has_permission(PermissionType.READ)
        assert not membership.has_permission(PermissionType.DELETE)


class TestPersonalSpace:
    """测试个人空间"""
    
    def test_personal_space_creation(self):
        """测试个人空间创建"""
        space = PersonalSpace(
            space_id="personal_user_001",
            user_id="user_001"
        )
        
        assert space.user_id == "user_001"
        assert space.documents_count == 0
        assert "l1_redis_instance" in space.memory_config
    
    def test_personal_space_to_dict(self):
        """测试个人空间序列化"""
        space = PersonalSpace(
            space_id="personal_user_001",
            user_id="user_001",
            name="My Space"
        )
        
        data = space.to_dict()
        assert data["space_id"] == "personal_user_001"
        assert data["name"] == "My Space"


class TestPublicContributionSpace:
    """测试公共贡献空间"""
    
    def test_public_space_creation(self):
        """测试公共空间创建"""
        space = PublicContributionSpace()
        
        assert space.space_id == "public_space"
        assert space.auto_review_enabled
        assert space.min_quality_threshold == 0.7


class TestHybridCollaborationSpace:
    """测试混合协作空间"""
    
    def test_team_space_creation(self):
        """测试团队空间创建"""
        space = HybridCollaborationSpace(
            space_id="team_001",
            name="Research Team",
            description="NLP Research"
        )
        
        assert space.level == "team"
        assert space.members_count == 0
        assert space.allow_share_to_public
    
    def test_add_remove_member(self):
        """测试添加和移除成员"""
        space = HybridCollaborationSpace(
            space_id="team_001",
            name="Test Team"
        )
        
        # 添加成员
        membership = TeamMembership(
            team_id="team_001",
            user_id="user_001",
            role=TeamRole.MEMBER
        )
        space.add_member(membership)
        assert space.members_count == 1
        
        # 移除成员
        space.remove_member("user_001")
        assert space.members_count == 0


class TestUserManager:
    """测试用户管理器"""
    
    @pytest.mark.asyncio
    async def test_create_user(self):
        """测试创建用户"""
        manager = UserManager()
        
        user = await manager.create_user(
            username="TestUser",
            email="test@example.com",
            password_hash="hashed_pwd"
        )
        
        assert user.username == "TestUser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER
    
    @pytest.mark.asyncio
    async def test_get_user(self):
        """测试获取用户"""
        manager = UserManager()
        
        created = await manager.create_user(
            username="GetUser",
            email="get@example.com",
            password_hash="pwd"
        )
        
        retrieved = await manager.get_user(created.user_id)
        assert retrieved is not None
        assert retrieved.username == "GetUser"
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self):
        """测试更新用户资料"""
        manager = UserManager()
        
        user = await manager.create_user(
            username="UpdateUser",
            email="update@example.com",
            password_hash="pwd"
        )
        
        updated = await manager.update_user_profile(
            user_id=user.user_id,
            updates={"bio": "New bio"}
        )
        
        assert updated is not None
        assert updated.bio == "New bio"
    
    @pytest.mark.asyncio
    async def test_update_contribution_score(self):
        """测试更新贡献积分"""
        manager = UserManager()
        
        user = await manager.create_user(
            username="ScoreUser",
            email="score@example.com",
            password_hash="pwd"
        )
        
        # 初始积分为 0
        assert user.contribution_score == 0
        
        # 增加积分
        await manager.update_contribution_score(user.user_id, 50)
        assert user.contribution_score == 50
        
        # 再次增加，触发角色升级
        await manager.update_contribution_score(user.user_id, 60)
        assert user.contribution_score == 110
        assert user.role == UserRole.CONTRIBUTOR


class TestWorkspaceManager:
    """测试工作空间管理器"""
    
    @pytest.mark.asyncio
    async def test_create_personal_space(self):
        """测试创建个人空间"""
        manager = WorkspaceManager()
        
        space = await manager.create_personal_space("user_001")
        
        assert space is not None
        assert space.user_id == "user_001"
        assert "personal_user_001" in space.space_id
    
    @pytest.mark.asyncio
    async def test_upload_to_personal(self):
        """测试上传文档到个人空间"""
        manager = WorkspaceManager()
        
        doc_id = await manager.upload_to_personal(
            user_id="user_001",
            document_data={"title": "Test Doc", "size": 1024}
        )
        
        assert doc_id is not None
        
        space = await manager.get_personal_space("user_001")
        assert space.documents_count == 1
    
    @pytest.mark.asyncio
    async def test_submit_contribution(self):
        """测试提交知识贡献"""
        manager = WorkspaceManager()
        
        contribution = await manager.submit_contribution(
            user_id="user_001",
            knowledge_id="know_001",
            title="Test Knowledge",
            content="Content here",
            domain="AI"
        )
        
        assert contribution is not None
        assert contribution.quality_score > 0
        assert contribution.status == "pending"
    
    @pytest.mark.asyncio
    async def test_create_team_space(self):
        """测试创建团队空间"""
        manager = WorkspaceManager()
        
        space = await manager.create_team_space(
            name="Test Team",
            description="Test Description",
            creator_id="user_001"
        )
        
        assert space is not None
        assert space.name == "Test Team"
        assert space.members_count == 1  # 创建者自动成为成员


class TestPermissionManager:
    """测试权限管理器"""
    
    def test_role_permissions(self):
        """测试角色权限映射"""
        manager = PermissionManager()
        
        # 普通用户权限
        user_perms = manager.role_permissions[UserRole.USER]
        assert PermissionType.READ in user_perms
        assert PermissionType.WRITE in user_perms
        
        # 管理员权限
        admin_perms = manager.role_permissions[UserRole.ADMIN]
        assert PermissionType.MANAGE in admin_perms
    
    def test_check_permission(self):
        """测试权限检查"""
        manager = PermissionManager()
        
        user = UserProfile(
            user_id="user_001",
            username="TestUser",
            email="test@example.com",
            role=UserRole.USER
        )
        
        # 检查公共空间读取权限
        can_read = manager.check_permission(
            user=user,
            permission=PermissionType.READ,
            space_type=SpaceType.PUBLIC
        )
        assert can_read is True
        
        # 检查删除权限（普通用户没有）
        can_delete = manager.check_permission(
            user=user,
            permission=PermissionType.DELETE,
            space_type=SpaceType.PUBLIC
        )
        assert can_delete is False
    
    def test_can_share_to_public(self):
        """测试是否可以分享到公共空间"""
        manager = PermissionManager()
        
        # 普通用户不能分享
        user = UserProfile(
            user_id="user_001",
            username="User",
            email="user@example.com",
            role=UserRole.USER
        )
        assert not manager.can_share_to_public(user)
        
        # 贡献者可以分享
        contributor = UserProfile(
            user_id="user_002",
            username="Contributor",
            email="contrib@example.com",
            role=UserRole.CONTRIBUTOR
        )
        assert manager.can_share_to_public(contributor)


class TestAccessControl:
    """测试访问控制"""
    
    def test_can_access(self):
        """测试访问控制决策"""
        permission_manager = PermissionManager()
        access_control = AccessControl(permission_manager)
        
        user = UserProfile(
            user_id="user_001",
            username="TestUser",
            email="test@example.com",
            role=UserRole.USER
        )
        
        # 允许读取公共文档
        allowed = access_control.can_access(
            user=user,
            resource_type="document",
            resource_id="doc_001",
            action="read",
            context={
                "space_type": SpaceType.PUBLIC.value,
                "space_id": "public_space"
            }
        )
        assert allowed is True
    
    def test_access_logging(self):
        """测试访问日志记录"""
        permission_manager = PermissionManager()
        access_control = AccessControl(permission_manager)
        
        user = UserProfile(
            user_id="user_001",
            username="TestUser",
            email="test@example.com"
        )
        
        # 记录访问
        access_control.log_access(
            user=user,
            action="read",
            resource="doc_001",
            result=True
        )
        
        # 获取日志
        logs = access_control.get_access_logs(user_id=user.user_id)
        assert len(logs) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
