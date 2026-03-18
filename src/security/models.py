"""
安全数据模型定义
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"           # 管理员
    DEVELOPER = "developer"   # 开发者
    USER = "user"             # 普通用户
    GUEST = "guest"           # 访客

class UserPermission(str, Enum):
    """用户权限枚举"""
    # 系统管理权限
    SYSTEM_ADMIN = "system:admin"           # 系统管理员权限
    USER_MANAGE = "user:manage"             # 用户管理
    CONFIG_MANAGE = "config:manage"         # 配置管理
    
    # 数据操作权限
    DATA_READ = "data:read"                 # 数据读取
    DATA_WRITE = "data:write"               # 数据写入
    DATA_DELETE = "data:delete"             # 数据删除
    
    # API 访问权限
    API_ACCESS = "api:access"               # API 访问
    API_RATE_LIMIT_BYPASS = "api:rate_limit_bypass"  # 绕过速率限制
    
    # Dashboard 权限
    DASHBOARD_VIEW = "dashboard:view"       # 查看仪表板
    DASHBOARD_EDIT = "dashboard:edit"       # 编辑仪表板
    DASHBOARD_ADMIN = "dashboard:admin"     # 仪表板管理

class User(BaseModel):
    """用户模型"""
    id: str = Field(..., description="用户唯一标识")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱")
    hashed_password: str = Field(..., description="加密密码")
    full_name: Optional[str] = Field(None, description="全名")
    roles: List[UserRole] = Field(default=[], description="用户角色列表")
    permissions: List[UserPermission] = Field(default=[], description="用户权限列表")
    is_active: bool = Field(default=True, description="是否激活")
    is_superuser: bool = Field(default=False, description="是否超级用户")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    metadata: Dict[str, Any] = Field(default={}, description="用户元数据")

class TokenData(BaseModel):
    """Token 数据模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    roles: List[UserRole] = Field(default=[], description="用户角色")
    permissions: List[UserPermission] = Field(default=[], description="用户权限")
    expires_at: datetime = Field(..., description="过期时间")
    issued_at: datetime = Field(default_factory=datetime.utcnow, description="签发时间")

class OAuth2Provider(str, Enum):
    """OAuth2 提供商枚举"""
    GITHUB = "github"
    GOOGLE = "google"
    WECHAT = "wechat"
    DINGTALK = "dingtalk"

class OAuth2State(BaseModel):
    """OAuth2 状态模型"""
    provider: OAuth2Provider = Field(..., description="提供商")
    redirect_uri: str = Field(..., description="重定向URI")
    state: str = Field(..., description="状态值")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")

class SecurityConfig(BaseModel):
    """安全配置模型"""
    # JWT 配置
    jwt_secret_key: str = Field(..., description="JWT 密钥")
    jwt_algorithm: str = Field(default="HS256", description="JWT 算法")
    jwt_expire_minutes: int = Field(default=30, description="JWT 过期时间(分钟)")
    
    # OAuth2 配置
    oauth2_providers: Dict[OAuth2Provider, Dict[str, str]] = Field(default={}, description="OAuth2 提供商配置")
    
    # 速率限制配置
    rate_limit_enabled: bool = Field(default=True, description="是否启用速率限制")
    rate_limit_requests: int = Field(default=100, description="每分钟请求数")
    rate_limit_window: int = Field(default=60, description="时间窗口(秒)")
    
    # 安全防护配置
    csrf_protection_enabled: bool = Field(default=True, description="是否启用 CSRF 防护")
    xss_protection_enabled: bool = Field(default=True, description="是否启用 XSS 防护")
    allowed_origins: List[str] = Field(default=["*"], description="允许的跨域来源")
    
    # 密码策略
    password_min_length: int = Field(default=8, description="密码最小长度")
    password_require_uppercase: bool = Field(default=True, description="是否要求大写字母")
    password_require_lowercase: bool = Field(default=True, description="是否要求小写字母")
    password_require_digits: bool = Field(default=True, description="是否要求数字")
    password_require_special: bool = Field(default=True, description="是否要求特殊字符")