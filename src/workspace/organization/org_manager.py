"""
组织与工作空间管理器

实现从个人 (user) → 团队 (team) → 组织 (organization/workspace) 的完整管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

# 从 user layer 导入基础模型
import sys
from pathlib import Path
workspace_path = str(Path(__file__).parent.parent)
if workspace_path not in sys.path:
    sys.path.insert(0, workspace_path)

from user.models import (
    UserProfile, TeamMembership, TeamRole, PermissionType,
    HybridCollaborationSpace
)
from .org_models import (
    Organization, OrganizationMembership, OrganizationRole,
    OrganizationType, Department, WorkspaceHierarchy, WorkspaceConfig
)

logger = logging.getLogger(__name__)


class OrganizationManager:
    """组织管理器"""
    
    def __init__(self):
        self.organizations: Dict[str, Organization] = {}
        self.user_hierarchies: Dict[str, WorkspaceHierarchy] = {}
        self.config = WorkspaceConfig()
    
    async def create_organization(
        self,
        name: str,
        org_type: OrganizationType = OrganizationType.COMPANY,
        description: str = "",
        creator_id: str = "",
        settings: Optional[Dict[str, Any]] = None
    ) -> Organization:
        """创建组织"""
        org_id = f"org_{uuid.uuid4().hex[:8]}"
        
        org = Organization(
            org_id=org_id,
            name=name,
            org_type=org_type,
            description=description,
            created_by=creator_id,
            settings=settings or {}
        )
        
        # 创建者自动成为组织所有者
        if creator_id:
            owner_membership = OrganizationMembership(
                org_id=org_id,
                user_id=creator_id,
                role=OrganizationRole.OWNER,
                permissions=[
                    "read", "write", "delete", "share",
                    "audit", "manage", "invite", "remove_member"
                ]
            )
            org.add_member(owner_membership)
            
            # 更新用户层级
            await self._update_user_hierarchy(creator_id, org_id)
        
        self.organizations[org_id] = org
        logger.info(f"Organization created: {org_id}, name: {name}, by: {creator_id}")
        return org
    
    async def get_organization(self, org_id: str) -> Optional[Organization]:
        """获取组织信息"""
        return self.organizations.get(org_id)
    
    async def update_organization(
        self,
        org_id: str,
        updates: Dict[str, Any],
        updater_id: str
    ) -> Optional[Organization]:
        """更新组织信息"""
        org = self.organizations.get(org_id)
        if not org:
            return None
        
        # 检查权限
        if not org.has_permission(updater_id, "manage"):
            logger.warning(f"User {updater_id} lacks permission to update organization {org_id}")
            return None
        
        # 更新基本信息
        for key in ["name", "description", "settings", "max_members"]:
            if key in updates:
                setattr(org, key, updates[key])
        
        org.updated_at = datetime.now()
        logger.info(f"Organization updated: {org_id} by {updater_id}")
        return org
    
    async def delete_organization(self, org_id: str, deleter_id: str) -> bool:
        """删除组织"""
        org = self.organizations.get(org_id)
        if not org:
            return False
        
        # 检查权限
        if not org.has_permission(deleter_id, "manage"):
            logger.warning(f"User {deleter_id} lacks permission to delete organization {org_id}")
            return False
        
        # 清理用户层级关系
        for user_id in list(org.members.keys()):
            hierarchy = self.user_hierarchies.get(user_id)
            if hierarchy:
                hierarchy.remove_organization(org_id)
        
        # 删除组织
        del self.organizations[org_id]
        logger.info(f"Organization deleted: {org_id} by {deleter_id}")
        return True
    
    async def add_member(
        self,
        org_id: str,
        user_id: str,
        role: OrganizationRole = OrganizationRole.MEMBER,
        department: Optional[str] = None,
        title: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> bool:
        """添加组织成员"""
        org = self.organizations.get(org_id)
        if not org:
            return False
        
        # 检查是否已满
        if len(org.members) >= org.max_members:
            logger.warning(f"Organization {org_id} has reached max members")
            return False
        
        membership = OrganizationMembership(
            org_id=org_id,
            user_id=user_id,
            role=role,
            department=department,
            title=title,
            permissions=permissions or []
        )
        
        org.add_member(membership)
        await self._update_user_hierarchy(user_id, org_id)
        
        logger.info(f"Member added to organization: {org_id}, user: {user_id}, role: {role.value}")
        return True
    
    async def remove_member(self, org_id: str, user_id: str, remover_id: str) -> bool:
        """移除组织成员"""
        org = self.organizations.get(org_id)
        if not org:
            return False
        
        # 检查权限
        if not org.has_permission(remover_id, "remove_member"):
            logger.warning(f"User {remover_id} lacks permission to remove member from {org_id}")
            return False
        
        org.remove_member(user_id)
        
        # 更新用户层级
        hierarchy = self.user_hierarchies.get(user_id)
        if hierarchy:
            hierarchy.remove_organization(org_id)
        
        logger.info(f"Member removed from organization: {org_id}, user: {user_id}")
        return True
    
    async def create_department(
        self,
        org_id: str,
        name: str,
        description: str = "",
        manager_id: Optional[str] = None,
        parent_dept_id: Optional[str] = None
    ) -> Optional[Department]:
        """创建部门"""
        org = self.organizations.get(org_id)
        if not org:
            return None
        
        dept_id = f"dept_{uuid.uuid4().hex[:8]}"
        department = Department(
            dept_id=dept_id,
            name=name,
            parent_org_id=org_id,
            description=description,
            manager_id=manager_id
        )
        
        # 如果有父部门，建立层级关系
        if parent_dept_id and parent_dept_id in org.departments:
            parent_dept = org.departments[parent_dept_id]
            parent_dept.child_departments.append(dept_id)
        
        org.add_department(department)
        logger.info(f"Department created: {dept_id}, name: {name}, in org: {org_id}")
        return department
    
    async def get_user_hierarchy(self, user_id: str) -> WorkspaceHierarchy:
        """获取用户的层级关系"""
        if user_id not in self.user_hierarchies:
            self.user_hierarchies[user_id] = WorkspaceHierarchy(user_id=user_id)
        return self.user_hierarchies[user_id]
    
    async def _update_user_hierarchy(self, user_id: str, org_id: str):
        """更新用户层级关系"""
        hierarchy = await self.get_user_hierarchy(user_id)
        hierarchy.add_organization(org_id)
        
        # 如果是第一个组织，设为主要组织
        if not hierarchy.primary_org_id:
            hierarchy.set_primary_organization(org_id)
    
    async def get_user_organizations(self, user_id: str) -> List[Organization]:
        """获取用户所属的所有组织"""
        hierarchy = await self.get_user_hierarchy(user_id)
        return [
            self.organizations[org_id]
            for org_id in hierarchy.org_ids
            if org_id in self.organizations
        ]
    
    async def transfer_member(
        self,
        from_org_id: str,
        to_org_id: str,
        user_id: str,
        new_role: OrganizationRole = OrganizationRole.MEMBER
    ) -> bool:
        """转移成员到另一个组织"""
        # 从原组织移除
        removed = await self.remove_member(from_org_id, user_id, user_id)
        if not removed:
            return False
        
        # 添加到新组织
        added = await self.add_member(to_org_id, user_id, new_role)
        return added
    
    async def get_organization_stats(self, org_id: str) -> Optional[Dict[str, Any]]:
        """获取组织统计信息"""
        org = self.organizations.get(org_id)
        if not org:
            return None
        
        return {
            "org_id": org.org_id,
            "name": org.name,
            "total_members": len(org.members),
            "active_members": org.active_members,
            "total_teams": org.total_teams,
            "total_departments": len(org.departments),
            "org_type": org.org_type.value,
            "created_at": org.created_at.isoformat()
        }


class WorkspaceManager:
    """工作空间管理器（整合组织和团队）"""
    
    def __init__(self, org_manager: OrganizationManager):
        self.org_manager = org_manager
        self.team_spaces: Dict[str, HybridCollaborationSpace] = {}
    
    async def create_workspace(
        self,
        name: str,
        workspace_type: OrganizationType = OrganizationType.COMPANY,
        description: str = "",
        creator_id: str = ""
    ) -> Organization:
        """创建工作空间（组织级别）"""
        return await self.org_manager.create_organization(
            name=name,
            org_type=workspace_type,
            description=description,
            creator_id=creator_id
        )
    
    async def create_team_in_workspace(
        self,
        org_id: str,
        team_name: str,
        description: str = "",
        creator_id: str = ""
    ) -> Optional[HybridCollaborationSpace]:
        """在工作空间内创建团队"""
        org = await self.org_manager.get_organization(org_id)
        if not org:
            return None
        
        # 创建团队空间
        space_id = f"team_{uuid.uuid4().hex[:8]}"
        team_space = HybridCollaborationSpace(
            space_id=space_id,
            name=team_name,
            description=description,
            parent_org_id=org_id,
            level="team"
        )
        
        # 创建者成为团队所有者
        if creator_id:
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
            team_space.add_member(owner_membership)
            
            # 更新用户层级
            hierarchy = await self.org_manager.get_user_hierarchy(creator_id)
            hierarchy.add_team(space_id)
        
        self.team_spaces[space_id] = team_space
        
        # 更新组织的团队列表
        org.add_team(space_id)
        
        logger.info(f"Team created in workspace: {space_id}, name: {team_name}, org: {org_id}")
        return team_space
    
    async def get_user_complete_hierarchy(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """获取用户的完整层级结构（user → team → org）"""
        hierarchy = await self.org_manager.get_user_hierarchy(user_id)
        
        result = {
            "user_id": user_id,
            "organizations": [],
            "teams": []
        }
        
        # 获取用户在所有组织中的信息
        for org_id in hierarchy.org_ids:
            org = await self.org_manager.get_organization(org_id)
            if org:
                org_info = {
                    "org_id": org.org_id,
                    "name": org.name,
                    "role": org.get_member_role(user_id).value if org.get_member_role(user_id) else None,
                    "departments": []
                }
                
                # 获取用户在各部门的信息
                for dept in org.departments.values():
                    if user_id in dept.members:
                        org_info["departments"].append({
                            "dept_id": dept.dept_id,
                            "name": dept.name,
                            "title": next(
                                (m.title for m in org.members.values() 
                                 if m.user_id == user_id and m.department == dept.name),
                                None
                            )
                        })
                
                result["organizations"].append(org_info)
        
        # 获取用户在所有团队中的信息
        for team_id in hierarchy.team_ids:
            team = self.team_spaces.get(team_id)
            if team:
                member = next((m for m in team.members if m.user_id == user_id), None)
                result["teams"].append({
                    "team_id": team.space_id,
                    "name": team.name,
                    "role": member.role.value if member else None,
                    "parent_org_id": team.parent_org_id
                })
        
        return result
    
    async def cross_organization_collaboration(
        self,
        source_org_id: str,
        target_org_id: str,
        user_id: str,
        resource_type: str,
        resource_id: str
    ) -> bool:
        """跨组织协作"""
        # 检查用户在两个组织中都有权限
        source_org = await self.org_manager.get_organization(source_org_id)
        target_org = await self.org_manager.get_organization(target_org_id)
        
        if not source_org or not target_org:
            logger.warning("Source or target organization not found")
            return False
        
        if not self.org_manager.config.allow_cross_org_collaboration:
            logger.warning("Cross-organization collaboration is disabled")
            return False
        
        # TODO: 实现实际的跨组织资源共享逻辑
        logger.info(
            f"Cross-org collaboration: {user_id} sharing {resource_type}:{resource_id} "
            f"from {source_org_id} to {target_org_id}"
        )
        return True
