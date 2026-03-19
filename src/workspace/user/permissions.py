"""
权限管理与访问控制

实现基于角色和属性的细粒度权限控制（RBAC + ABAC）
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import logging

from .models import (
    UserProfile, UserRole, QueryRecord,
    PersonalSpace, PublicContributionSpace, HybridCollaborationSpace,
    TeamMembership, TeamRole, PermissionType, SpaceType
)

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """访问级别"""
    NONE = 0  # 无权限
    READ = 1  # 只读
    WRITE = 2  # 读写
    ADMIN = 3  # 管理


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        # 角色到权限的映射
        self.role_permissions: Dict[UserRole, Set[PermissionType]] = {
            UserRole.USER: {
                PermissionType.READ,
                PermissionType.WRITE
            },
            UserRole.CONTRIBUTOR: {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.SHARE,
                PermissionType.AUDIT
            },
            UserRole.DOMAIN_EXPERT: {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.SHARE,
                PermissionType.AUDIT,
                PermissionType.MANAGE
            },
            UserRole.ADMIN: {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.DELETE,
                PermissionType.SHARE,
                PermissionType.AUDIT,
                PermissionType.MANAGE
            }
        }
        
        # 团队角色到权限的映射
        self.team_role_permissions: Dict[TeamRole, Set[PermissionType]] = {
            TeamRole.GUEST: {PermissionType.READ},
            TeamRole.MEMBER: {
                PermissionType.READ,
                PermissionType.WRITE
            },
            TeamRole.ADMIN: {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.DELETE,
                PermissionType.SHARE,
                PermissionType.AUDIT
            },
            TeamRole.OWNER: {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.DELETE,
                PermissionType.SHARE,
                PermissionType.AUDIT,
                PermissionType.MANAGE
            }
        }
    
    def get_user_permissions(
        self,
        user: UserProfile,
        space_type: SpaceType,
        space_id: Optional[str] = None
    ) -> Set[PermissionType]:
        """获取用户在指定空间的权限"""
        
        if space_type == SpaceType.PERSONAL:
            # 个人空间：只有空间所有者有完全权限
            return self._get_personal_space_permissions(user, space_id)
        
        elif space_type == SpaceType.PUBLIC:
            # 公共空间：基于用户角色
            return self.role_permissions.get(user.role, set())
        
        elif space_type == SpaceType.TEAM:
            # 团队空间：基于团队成员角色
            return self._get_team_permissions(user, space_id)
        
        return set()
    
    def _get_personal_space_permissions(
        self,
        user: UserProfile,
        space_id: Optional[str]
    ) -> Set[PermissionType]:
        """获取个人空间权限"""
        # 检查是否是空间所有者
        if user.personal_space_id == space_id:
            return {
                PermissionType.READ,
                PermissionType.WRITE,
                PermissionType.DELETE,
                PermissionType.SHARE,
                PermissionType.MANAGE
            }
        return set()
    
    def _get_team_permissions(
        self,
        user: UserProfile,
        space_id: Optional[str]
    ) -> Set[PermissionType]:
        """获取团队空间权限"""
        if not space_id:
            return set()
        
        # 查找用户在团队中的成员资格
        for membership in user.team_memberships:
            if membership.team_id == space_id:
                return self.team_role_permissions.get(membership.role, set())
        
        return set()
    
    def check_permission(
        self,
        user: UserProfile,
        permission: PermissionType,
        space_type: SpaceType,
        space_id: Optional[str] = None
    ) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user, space_type, space_id)
        has_permission = permission in user_permissions
        
        if not has_permission:
            logger.warning(
                f"User {user.user_id} lacks permission {permission.value} "
                f"in space {space_type.value}:{space_id}"
            )
        
        return has_permission
    
    def can_share_to_public(self, user: UserProfile) -> bool:
        """检查用户是否可以分享到公共空间"""
        return user.role in [
            UserRole.CONTRIBUTOR,
            UserRole.DOMAIN_EXPERT,
            UserRole.ADMIN
        ]
    
    def can_audit_contribution(self, user: UserProfile, domain: str) -> bool:
        """检查用户是否可以审核指定领域的贡献"""
        if user.role == UserRole.ADMIN:
            return True
        
        if user.role == UserRole.DOMAIN_EXPERT:
            return domain in user.expertise_domains
        
        if user.role == UserRole.CONTRIBUTOR:
            return True  # 贡献者可以参与初审
        
        return False


class AccessControl:
    """访问控制器"""
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        # 访问日志
        self.access_logs: List[Dict[str, Any]] = []
    
    def can_access(
        self,
        user: UserProfile,
        resource_type: str,
        resource_id: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        检查用户是否可以访问资源（ABAC 模型）
        
        Args:
            user: 用户对象
            resource_type: 资源类型（document/query/space 等）
            resource_id: 资源 ID
            action: 操作类型（read/write/delete/share）
            context: 上下文信息（包含空间类型、时间等属性）
        
        Returns:
            bool: 是否允许访问
        """
        # 记录访问尝试
        access_attempt = {
            "user_id": user.user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "context": context or {},
            "timestamp": datetime.now(),
            "allowed": False
        }
        
        # 基于属性的访问控制决策
        allowed = self._evaluate_access(user, resource_type, action, context)
        access_attempt["allowed"] = allowed
        
        # 记录审计日志
        self.access_logs.append(access_attempt)
        
        if not allowed:
            logger.warning(
                f"Access denied: user={user.user_id}, "
                f"resource={resource_type}:{resource_id}, action={action}"
            )
        
        return allowed
    
    def _evaluate_access(
        self,
        user: UserProfile,
        resource_type: str,
        action: str,
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """评估访问权限"""
        if not context:
            return False
        
        space_type = context.get("space_type")
        space_id = context.get("space_id")
        
        # 将操作映射到权限类型
        action_to_permission = {
            "read": PermissionType.READ,
            "write": PermissionType.WRITE,
            "delete": PermissionType.DELETE,
            "share": PermissionType.SHARE
        }
        
        required_permission = action_to_permission.get(action)
        if not required_permission:
            return False
        
        # 检查权限
        return self.permission_manager.check_permission(
            user,
            required_permission,
            space_type,
            space_id
        )
    
    def log_access(
        self,
        user: UserProfile,
        action: str,
        resource: str,
        result: bool,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录访问日志（用于审计）"""
        log_entry = {
            "user_id": user.user_id,
            "action": action,
            "resource": resource,
            "result": "success" if result else "denied",
            "details": details or {},
            "timestamp": datetime.now()
        }
        self.access_logs.append(log_entry)
    
    def get_access_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """获取访问日志"""
        logs = self.access_logs
        
        # 过滤条件
        if user_id:
            logs = [l for l in logs if l["user_id"] == user_id]
        if start_time:
            logs = [l for l in logs if l["timestamp"] >= start_time]
        if end_time:
            logs = [l for l in logs if l["timestamp"] <= end_time]
        
        return logs
    
    def audit_trail(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的完整审计轨迹"""
        return self.get_access_logs(user_id=user_id)


class PrivacyProtection:
    """隐私保护工具类"""
    
    @staticmethod
    def encrypt_personal_data(data: Dict[str, Any], encryption_key: str) -> str:
        """加密个人数据"""
        # TODO: 实现实际的加密逻辑（使用 AES-256）
        import json
        import base64
        # 简化示例
        encrypted = base64.b64encode(json.dumps(data).encode()).decode()
        return encrypted
    
    @staticmethod
    def decrypt_personal_data(encrypted_data: str, encryption_key: str) -> Dict[str, Any]:
        """解密个人数据"""
        # TODO: 实现实际的解密逻辑
        import json
        import base64
        # 简化示例
        decrypted = json.loads(base64.b64decode(encrypted_data.encode()).decode())
        return decrypted
    
    @staticmethod
    def anonymize_query(query: str) -> str:
        """匿名化查询内容"""
        # TODO: 实现敏感信息检测和替换
        return query
    
    @staticmethod
    def should_retain_query(
        query_record: QueryRecord,
        retention_days: int = 30
    ) -> bool:
        """检查查询记录是否应该保留"""
        from datetime import timedelta
        
        age = datetime.now() - query_record.timestamp
        return age < timedelta(days=retention_days)
    
    @staticmethod
    def purge_expired_data(
        data_store: List[Any],
        retention_checker: callable
    ) -> int:
        """清理过期数据"""
        original_count = len(data_store)
        data_store[:] = [d for d in data_store if retention_checker(d)]
        purged_count = original_count - len(data_store)
        
        if purged_count > 0:
            logger.info(f"Purged {purged_count} expired records")
        
        return purged_count
