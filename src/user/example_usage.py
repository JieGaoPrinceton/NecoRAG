"""
多用户系统使用示例

演示如何使用个人工作空间、公共贡献空间和团队协作空间
"""

import asyncio
from datetime import datetime
from src.user import (
    UserManager,
    WorkspaceManager,
    PermissionManager,
    AccessControl,
    UserProfile,
    UserRole,
    TeamRole,
    PermissionType,
    SpaceType
)


async def example_user_management():
    """示例 1: 用户管理"""
    print("=" * 60)
    print("示例 1: 用户管理")
    print("=" * 60)
    
    # 创建用户管理器
    user_manager = UserManager()
    
    # 创建新用户
    user = await user_manager.create_user(
        username="Alice",
        email="alice@example.com",
        password_hash="hashed_password_here",
        bio="AI 研究员，专注于自然语言处理",
        expertise_domains=["AI", "NLP", "Machine Learning"]
    )
    
    print(f"✅ 创建用户：{user.username} (ID: {user.user_id})")
    print(f"   角色：{user.role.value}")
    print(f"   擅长领域：{user.expertise_domains}")
    
    # 更新用户资料
    await user_manager.update_user_profile(
        user_id=user.user_id,
        updates={
            "bio": "资深 AI 研究员，10 年 NLP 经验",
            "private_config": {"theme": "dark", "language": "zh-CN"}
        }
    )
    
    print(f"✅ 更新用户资料成功")
    
    # 获取用户信息
    retrieved_user = await user_manager.get_user(user.user_id)
    print(f"   更新后的简介：{retrieved_user.bio}")
    
    # 更新贡献积分
    await user_manager.update_contribution_score(user.user_id, 50)
    print(f"✅ 贡献积分：{retrieved_user.contribution_score}")
    
    return user_manager, user


async def example_personal_workspace(user_manager: UserManager, user: UserProfile):
    """示例 2: 个人工作空间"""
    print("\n" + "=" * 60)
    print("示例 2: 个人工作空间")
    print("=" * 60)
    
    # 创建工作空间管理器
    workspace_manager = WorkspaceManager()
    
    # 为用户创建个人空间
    personal_space = await workspace_manager.create_personal_space(user.user_id)
    print(f"✅ 创建个人空间：{personal_space.name}")
    print(f"   空间 ID: {personal_space.space_id}")
    
    # 上传文档到个人空间
    doc_id = await workspace_manager.upload_to_personal(
        user_id=user.user_id,
        document_data={
            "title": "深度学习入门教程",
            "content": "深度学习是机器学习的一个分支...",
            "size": 10240
        }
    )
    print(f"✅ 上传文档：{doc_id}")
    print(f"   文档数量：{personal_space.documents_count}")
    
    # 在个人空间检索
    results = await workspace_manager.search_in_personal(
        user_id=user.user_id,
        query="深度学习",
        top_k=5
    )
    print(f"✅ 检索结果：{len(results)} 条")
    
    return workspace_manager


async def example_public_contribution(workspace_manager: WorkspaceManager, user: UserProfile):
    """示例 3: 公共贡献空间"""
    print("\n" + "=" * 60)
    print("示例 3: 公共贡献空间")
    print("=" * 60)
    
    # 提交知识贡献
    contribution = await workspace_manager.submit_contribution(
        user_id=user.user_id,
        knowledge_id="doc_123",
        title="Transformer 模型详解",
        content="Transformer 是一种基于自注意力机制的深度学习模型...",
        domain="AI"
    )
    
    print(f"✅ 提交贡献：{contribution.title}")
    print(f"   质量评分：{contribution.quality_score:.2f}")
    print(f"   状态：{contribution.status}")
    
    # 审核贡献（模拟领域专家）
    if contribution.quality_score >= 0.7:
        approved = await workspace_manager.approve_contribution(
            contribution_id=contribution.contribution_id,
            reviewer_id="expert_001",
            comments="内容质量高，批准入库"
        )
        print(f"✅ 贡献已批准：{approved}")
        
        # 更新贡献者积分
        user_manager = UserManager()
        await user_manager.update_contribution_score(
            user.user_id,
            score_delta=20,
            contribution_id=contribution.contribution_id
        )
        print(f"✅ 贡献积分 +20，当前积分：{user.contribution_score}")


async def example_team_collaboration(workspace_manager: WorkspaceManager, user: UserProfile):
    """示例 4: 团队协作空间"""
    print("\n" + "=" * 60)
    print("示例 4: 团队协作空间")
    print("=" * 60)
    
    # 创建团队空间
    team_space = await workspace_manager.create_team_space(
        name="NLP 研究小组",
        description="专注于自然语言处理技术研究",
        creator_id=user.user_id,
        level="team"
    )
    
    print(f"✅ 创建团队：{team_space.name}")
    print(f"   团队 ID: {team_space.space_id}")
    print(f"   成员数：{team_space.members_count}")
    
    # 添加团队成员
    await workspace_manager.add_team_member(
        space_id=team_space.space_id,
        user_id="user_bob",
        role=TeamRole.MEMBER,
        permissions=[PermissionType.READ, PermissionType.WRITE]
    )
    print(f"✅ 添加成员 Bob")
    
    await workspace_manager.add_team_member(
        space_id=team_space.space_id,
        user_id="user_charlie",
        role=TeamRole.ADMIN,
        permissions=[
            PermissionType.READ,
            PermissionType.WRITE,
            PermissionType.SHARE,
            PermissionType.AUDIT
        ]
    )
    print(f"✅ 添加管理员 Charlie")
    
    # 分享团队知识到公共空间
    shared = await workspace_manager.share_team_to_public(
        space_id=team_space.space_id,
        knowledge_ids=["team_doc_1", "team_doc_2"],
        requester_id=user.user_id
    )
    print(f"✅ 分享到公共空间：{shared}")


async def example_permission_control():
    """示例 5: 权限控制"""
    print("\n" + "=" * 60)
    print("示例 5: 权限控制")
    print("=" * 60)
    
    # 创建权限管理器
    permission_manager = PermissionManager()
    access_control = AccessControl(permission_manager)
    
    # 创建测试用户
    user_manager = UserManager()
    user = await user_manager.create_user(
        username="TestUser",
        email="test@example.com",
        password_hash="password"
    )
    
    # 检查权限
    can_read = permission_manager.check_permission(
        user=user,
        permission=PermissionType.READ,
        space_type=SpaceType.PUBLIC
    )
    print(f"✅ 用户在公共空间的读取权限：{can_read}")
    
    can_share = permission_manager.can_share_to_public(user)
    print(f"✅ 用户可以分享到公共空间：{can_share}")
    
    # 访问控制决策
    allowed = access_control.can_access(
        user=user,
        resource_type="document",
        resource_id="doc_123",
        action="read",
        context={
            "space_type": SpaceType.PUBLIC.value,
            "space_id": "public_space"
        }
    )
    print(f"✅ 访问控制决策：{'允许' if allowed else '拒绝'}")
    
    # 记录审计日志
    access_control.log_access(
        user=user,
        action="read",
        resource="doc_123",
        result=allowed
    )
    
    # 获取审计轨迹
    logs = access_control.get_access_logs(user_id=user.user_id)
    print(f"✅ 审计日志记录数：{len(logs)}")


async def main():
    """主函数"""
    print("🧠 NecoRAG 多用户系统示例演示")
    print("=" * 60)
    
    # 示例 1: 用户管理
    user_manager, user = await example_user_management()
    
    # 示例 2: 个人工作空间
    workspace_manager = await example_personal_workspace(user_manager, user)
    
    # 示例 3: 公共贡献空间
    await example_public_contribution(workspace_manager, user)
    
    # 示例 4: 团队协作空间
    await example_team_collaboration(workspace_manager, user)
    
    # 示例 5: 权限控制
    await example_permission_control()
    
    print("\n" + "=" * 60)
    print("✨ 所有示例演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
