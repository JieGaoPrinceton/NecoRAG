"""
Team Layer - 团队管理器
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import logging

from .models import (
    TeamMembership,
    TeamRole,
    PermissionType,
    HybridCollaborationSpace,
)

logger = logging.getLogger(__name__)


class TeamManager:
    """团队管理器"""
    
    def __init__(self):
        self.teams: Dict[str, HybridCollaborationSpace] = {}
    
    async def create_team(
        self,
        name: str,
        description: str = "",
        creator_id: str = "",
        parent_org_id: Optional[str] = None
    ) -> HybridCollaborationSpace:
        """创建团队"""
        space_id = f"team_{uuid.uuid4().hex[:8]}"
        
        team = HybridCollaborationSpace(
            space_id=space_id,
            name=name,
            description=description,
            parent_org_id=parent_org_id,
            level="team"
        )
        
        # 创建者自动成为团队所有者
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
            team.add_member(owner_membership)
        
        self.teams[space_id] = team
        logger.info(f"Team created: {space_id}, name: {name}, by: {creator_id}")
        return team
    
    async def get_team(self, team_id: str) -> Optional[HybridCollaborationSpace]:
        """获取团队信息"""
        return self.teams.get(team_id)
    
    async def add_member(
        self,
        team_id: str,
        user_id: str,
        role: TeamRole = TeamRole.MEMBER,
        permissions: Optional[List[PermissionType]] = None,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """添加团队成员"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        membership = TeamMembership(
            team_id=team_id,
            user_id=user_id,
            role=role,
            permissions=permissions or [],
            expires_at=expires_at
        )
        
        team.add_member(membership)
        logger.info(f"Member added to team {team_id}: user {user_id} as {role.value}")
        return True
    
    async def remove_member(self, team_id: str, user_id: str) -> bool:
        """移除团队成员"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        team.remove_member(user_id)
        logger.info(f"Member removed from team {team_id}: user {user_id}")
        return True
    
    async def update_team(
        self,
        team_id: str,
        updates: Dict[str, Any],
        updater_id: str
    ) -> Optional[HybridCollaborationSpace]:
        """更新团队信息"""
        team = self.teams.get(team_id)
        if not team:
            return None
        
        # 检查权限
        member = next((m for m in team.members if m.user_id == updater_id), None)
        if not member or not member.has_permission(PermissionType.MANAGE):
            logger.warning(f"User {updater_id} lacks manage permission for team {team_id}")
            return None
        
        # 更新信息
        for key in ["name", "description", "max_members"]:
            if key in updates:
                setattr(team, key, updates[key])
        
        team.updated_at = datetime.now()
        logger.info(f"Team updated: {team_id} by {updater_id}")
        return team
    
    async def get_team_stats(self, team_id: str) -> Optional[Dict[str, Any]]:
        """获取团队统计信息"""
        team = self.teams.get(team_id)
        if not team:
            return None
        
        return {
            "team_id": team.space_id,
            "name": team.name,
            "members_count": team.members_count,
            "documents_count": team.documents_count,
            "created_at": team.created_at.isoformat()
        }
