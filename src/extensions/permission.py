"""
权限控制系统
"""

from typing import List, Set
from enum import Enum

from .models import User, UserRole, UserPermission

class Role:
    """角色定义"""
    
    # 管理员角色 - 拥有所有权限
    ADMIN = {
        "name": "管理员",
        "permissions": [
            UserPermission.SYSTEM_ADMIN,
            UserPermission.USER_MANAGE,
            UserPermission.CONFIG_MANAGE,
            UserPermission.DATA_READ,
            UserPermission.DATA_WRITE,
            UserPermission.DATA_DELETE,
            UserPermission.API_ACCESS,
            UserPermission.API_RATE_LIMIT_BYPASS,
            UserPermission.DASHBOARD_VIEW,
            UserPermission.DASHBOARD_EDIT,
            UserPermission.DASHBOARD_ADMIN
        ]
    }
    
    # 开发者角色 - 系统开发和维护
    DEVELOPER = {
        "name": "开发者",
        "permissions": [
            UserPermission.DATA_READ,
            UserPermission.DATA_WRITE,
            UserPermission.API_ACCESS,
            UserPermission.DASHBOARD_VIEW,
            UserPermission.DASHBOARD_EDIT
        ]
    }
    
    # 普通用户角色 - 基本使用权限
    USER = {
        "name": "普通用户",
        "permissions": [
            UserPermission.DATA_READ,
            UserPermission.API_ACCESS,
            UserPermission.DASHBOARD_VIEW
        ]
    }
    
    # 访客角色 - 只读权限
    GUEST = {
        "name": "访客",
        "permissions": [
            UserPermission.DATA_READ
        ]
    }

class PermissionService:
    """权限服务"""
    
    def __init__(self):
        # 角色权限映射
        self.role_permissions = {
            UserRole.ADMIN: Role.ADMIN["permissions"],
            UserRole.DEVELOPER: Role.DEVELOPER["permissions"],
            UserRole.USER: Role.USER["permissions"],
            UserRole.GUEST: Role.GUEST["permissions"]
        }
    
    def get_role_permissions(self, role: UserRole) -> List[UserPermission]:
        """获取角色权限"""
        return self.role_permissions.get(role, [])
    
    def get_user_permissions(self, user: User) -> Set[UserPermission]:
        """获取用户所有权限（包括角色权限和个人权限）"""
        permissions = set(user.permissions)
        
        # 添加角色权限
        for role in user.roles:
            role_perms = self.role_permissions.get(role, [])
            permissions.update(role_perms)
        
        return permissions
    
    def check_permission(self, user: User, permission: UserPermission) -> bool:
        """检查用户是否具有指定权限"""
        user_permissions = self.get_user_permissions(user)
        return permission in user_permissions
    
    def check_any_permission(self, user: User, permissions: List[UserPermission]) -> bool:
        """检查用户是否具有任意一个权限"""
        user_permissions = self.get_user_permissions(user)
        return any(perm in user_permissions for perm in permissions)
    
    def check_all_permissions(self, user: User, permissions: List[UserPermission]) -> bool:
        """检查用户是否具有所有权限"""
        user_permissions = self.get_user_permissions(user)
        return all(perm in user_permissions for perm in permissions)
    
    def add_permission_to_user(self, user: User, permission: UserPermission) -> User:
        """为用户添加权限"""
        if permission not in user.permissions:
            user.permissions.append(permission)
        return user
    
    def remove_permission_from_user(self, user: User, permission: UserPermission) -> User:
        """从用户移除权限"""
        if permission in user.permissions:
            user.permissions.remove(permission)
        return user
    
    def assign_role_to_user(self, user: User, role: UserRole) -> User:
        """为用户分配角色"""
        if role not in user.roles:
            user.roles.append(role)
        return user
    
    def remove_role_from_user(self, user: User, role: UserRole) -> User:
        """从用户移除角色"""
        if role in user.roles:
            user.roles.remove(role)
        return user

# 权限检查装饰器
def check_permission(permission: UserPermission):
    """权限检查装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取当前用户（假设通过依赖注入）
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="未提供用户信息"
                )
            
            # 检查权限
            permission_service = PermissionService()
            if not permission_service.check_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"缺少权限: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: UserPermission):
    """权限要求装饰器（同步版本）"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401,
                    detail="未提供用户信息"
                )
            
            # 检查权限
            permission_service = PermissionService()
            if not permission_service.check_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"缺少权限: {permission.value}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 预定义的权限检查函数
def require_admin(func):
    """要求管理员权限"""
    return check_permission(UserPermission.SYSTEM_ADMIN)(func)

def require_data_write(func):
    """要求数据写入权限"""
    return check_permission(UserPermission.DATA_WRITE)(func)

def require_dashboard_edit(func):
    """要求仪表板编辑权限"""
    return check_permission(UserPermission.DASHBOARD_EDIT)(func)