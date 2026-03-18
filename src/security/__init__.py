"""
NecoRAG Security Module

安全认证模块，提供用户身份验证、权限控制和安全防护功能。

功能包括：
- JWT Token 认证
- OAuth2.0 集成
- RBAC 权限控制
- 安全防护机制
"""

__version__ = "1.0.0"
__author__ = "NecoRAG Security Team"

# 认证服务
from .auth import (
    AuthService,
    JWTAuthService,
    OAuth2Service,
    get_current_user,
    get_current_active_user
)

# 权限控制
from .permission import (
    PermissionService,
    Role,
    Permission,
    check_permission,
    require_permission
)

# 安全防护
from .protection import (
    SecurityMiddleware,
    RateLimiter,
    CSRFProtection,
    XSSProtection
)

# 数据模型
from .models import (
    User,
    UserRole,
    UserPermission,
    TokenData,
    SecurityConfig,
    OAuth2Provider
)

# 存储管理
from .storage import (
    UserStorage,
    SessionManager,
    user_storage,
    session_manager
)

# 配置管理
from .config import (
    SecurityManager,
    security_manager,
    get_security_config
)

__all__ = [
    # 认证服务
    "AuthService",
    "JWTAuthService", 
    "OAuth2Service",
    "get_current_user",
    "get_current_active_user",
    
    # 权限控制
    "PermissionService",
    "Role",
    "Permission",
    "check_permission",
    "require_permission",
    
    # 安全防护
    "SecurityMiddleware",
    "RateLimiter",
    "CSRFProtection", 
    "XSSProtection",
    "ComprehensiveSecurityMiddleware",
    
    # 数据模型
    "User",
    "UserRole",
    "UserPermission",
    "TokenData",
    "SecurityConfig",
    "OAuth2Provider",
    
    # 存储管理
    "UserStorage",
    "SessionManager",
    "user_storage",
    "session_manager",
    
    # 配置管理
    "SecurityManager",
    "security_manager",
    "get_security_config"
]