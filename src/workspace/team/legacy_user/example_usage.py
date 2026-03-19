"""
三级用户系统使用示例

演示从个人 (user) → 团队 (team) → 组织 (workspace/organization) 的完整使用流程
"""

import asyncio
from src.workspace.team.user import (
    UserManager,
    TeamWorkspaceManager,
    OrganizationManager,
    OrgWorkspaceManager,
    UserProfile,
    OrganizationType,
    OrganizationRole,
    TeamRole,
    PermissionType,
)


async def main():
    """主函数"""
    print("=" * 70)
    print("🏢 NecoRAG 三级用户系统演示")
    print("=" * 70)
    
    # ========== 初始化 ==========
    user_manager = UserManager()
    team_workspace_manager = TeamWorkspaceManager()
    org_manager = OrganizationManager()
    workspace_manager = OrgWorkspaceManager(org_manager)
    
    # ========== 第一级：创建用户 ==========
    print("\n📍 第一级：创建用户")
    print("-" * 70)
    
    alice = await user_manager.create_user(
        username="Alice",
        email="alice@example.com",
        password_hash="hashed_password_123",
        expertise_domains=["AI", "Machine Learning"]
    )
    print(f"✅ 创建用户：{alice.username} (ID: {alice.user_id})")
    
    bob = await user_manager.create_user(
        username="Bob",
        email="bob@example.com",
        password_hash="hashed_password_456",
        expertise_domains=["NLP", "Deep Learning"]
    )
    print(f"✅ 创建用户：{bob.username} (ID: {bob.user_id})")
    
    charlie = await user_manager.create_user(
        username="Charlie",
        email="charlie@example.com",
        password_hash="hashed_password_789",
        expertise_domains=["Computer Vision"]
    )
    print(f"✅ 创建用户：{charlie.username} (ID: {charlie.user_id})")
    
    # ========== 第二级：创建组织（工作空间） ==========
    print("\n📍 第二级：创建组织")
    print("-" * 70)
    
    # 创建公司级别的组织
    tech_company = await workspace_manager.create_workspace(
        name="科技创新有限公司",
        workspace_type=OrganizationType.COMPANY,
        description="专注于人工智能技术研发",
        creator_id=alice.user_id
    )
    print(f"✅ 创建组织：{tech_company.name} (ID: {tech_company.org_id})")
    
    # 添加成员到组织
    await org_manager.add_member(
        org_id=tech_company.org_id,
        user_id=bob.user_id,
        role=OrganizationRole.MEMBER,
        department="研发部",
        title="高级算法工程师"
    )
    print(f"✅ 添加成员：{bob.username} 加入 {tech_company.name}")
    
    await org_manager.add_member(
        org_id=tech_company.org_id,
        user_id=charlie.user_id,
        role=OrganizationRole.MEMBER,
        department="研发部",
        title="算法工程师"
    )
    print(f"✅ 添加成员：{charlie.username} 加入 {tech_company.name}")
    
    # ========== 第三级：在组织内创建团队 ==========
    print("\n📍 第三级：创建团队")
    print("-" * 70)
    
    # 在公司内创建 NLP 团队
    nlp_team = await workspace_manager.create_team_in_workspace(
        org_id=tech_company.org_id,
        team_name="NLP 研究小组",
        description="专注于自然语言处理技术研究",
        creator_id=alice.user_id
    )
    print(f"✅ 创建团队：{nlp_team.name} (ID: {nlp_team.space_id})")
    
    # 在公司内创建 CV 团队
    cv_team = await workspace_manager.create_team_in_workspace(
        org_id=tech_company.org_id,
        team_name="计算机视觉团队",
        description="专注于计算机视觉技术研究",
        creator_id=charlie.user_id
    )
    print(f"✅ 创建团队：{cv_team.name} (ID: {cv_team.space_id})")
    
    # ========== 团队管理 ==========
    print("\n📊 团队管理")
    print("-" * 70)
    
    # 添加 Bob 到 NLP 团队
    from src.workspace.team.user import TeamMembership
    
    bob_membership = TeamMembership(
        team_id=nlp_team.space_id,
        user_id=bob.user_id,
        role=TeamRole.MEMBER,
        permissions=[PermissionType.READ, PermissionType.WRITE]
    )
    nlp_team.add_member(bob_membership)
    print(f"✅ 添加成员：{bob.username} 加入 {nlp_team.name}")
    
    # 添加 Alice 到 CV 团队作为顾问
    alice_advisor_membership = TeamMembership(
        team_id=cv_team.space_id,
        user_id=alice.user_id,
        role=TeamRole.ADMIN,
        permissions=[
            PermissionType.READ,
            PermissionType.WRITE,
            PermissionType.AUDIT
        ]
    )
    cv_team.add_member(alice_advisor_membership)
    print(f"✅ 添加成员：{alice.username} 以管理员身份加入 {cv_team.name}")
    
    # ========== 查看用户层级结构 ==========
    print("\n🌳 用户层级结构")
    print("-" * 70)
    
    alice_hierarchy = await workspace_manager.get_user_complete_hierarchy(alice.user_id)
    print(f"\n👤 {alice.username} 的组织架构:")
    print(f"  所属组织数：{len(alice_hierarchy['organizations'])}")
    for org in alice_hierarchy['organizations']:
        print(f"    - {org['name']} ({org['role']})")
        for dept in org['departments']:
            print(f"      └─ 部门：{dept['name']} ({dept['title'] or '无职位'})")
    
    print(f"  所属团队数：{len(alice_hierarchy['teams'])}")
    for team in alice_hierarchy['teams']:
        print(f"    - {team['name']} ({team['role']})")
    
    bob_hierarchy = await workspace_manager.get_user_complete_hierarchy(bob.user_id)
    print(f"\n👤 {bob.username} 的组织架构:")
    print(f"  所属组织数：{len(bob_hierarchy['organizations'])}")
    for org in bob_hierarchy['organizations']:
        print(f"    - {org['name']} ({org['role']})")
        for dept in org['departments']:
            print(f"      └─ 部门：{dept['name']} ({dept['title'] or '无职位'})")
    
    print(f"  所属团队数：{len(bob_hierarchy['teams'])}")
    for team in bob_hierarchy['teams']:
        print(f"    - {team['name']} ({team['role']})")
    
    # ========== 组织统计 ==========
    print("\n📈 组织统计")
    print("-" * 70)
    
    company_stats = await org_manager.get_organization_stats(tech_company.org_id)
    if company_stats:
        print(f"\n🏢 {company_stats['name']}")
        print(f"  总成员数：{company_stats['total_members']}")
        print(f"  活跃成员：{company_stats['active_members']}")
        print(f"  团队数量：{company_stats['total_teams']}")
        print(f"  部门数量：{company_stats['total_departments']}")
        print(f"  组织类型：{company_stats['org_type']}")
    
    # ========== 跨团队协作 ==========
    print("\n🤝 跨团队协作")
    print("-" * 70)
    
    # 模拟跨组织协作
    collaboration_result = await workspace_manager.cross_organization_collaboration(
        source_org_id=tech_company.org_id,
        target_org_id=tech_company.org_id,  # 实际场景中会是不同的组织
        user_id=alice.user_id,
        resource_type="document",
        resource_id="doc_001"
    )
    
    if collaboration_result:
        print(f"✅ 跨团队协作成功：{alice.username} 分享了文档 doc_001")
    else:
        print(f"❌ 跨团队协作失败")
    
    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("✨ 三级用户系统演示完成")
    print("=" * 70)
    print("\n📋 系统架构:")
    print("  Level 1: User (个人)")
    print("           ├── Alice, Bob, Charlie")
    print("           └── 每个用户有个人空间和权限")
    print()
    print("  Level 2: Team (团队)")
    print("           ├── NLP 研究小组")
    print("           ├── 计算机视觉团队")
    print("           └── 每个团队有独立的协作空间")
    print()
    print("  Level 3: Organization (组织)")
    print("           └── 科技创新有限公司")
    print("               ├── 研发部")
    print("               ├── 多个团队")
    print("               └── 完整的组织架构和权限体系")
    print()
    print("🎯 核心特性:")
    print("  ✅ 个人隐私保护 - 每个用户有独立的个人空间")
    print("  ✅ 灵活团队协作 - 支持多团队、多角色")
    print("  ✅ 组织架构管理 - 完整的公司/部门/团队层级")
    print("  ✅ 细粒度权限 - RBAC + ABAC 混合权限模型")
    print("  ✅ 跨组织协作 - 支持不同组织间的知识共享")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
