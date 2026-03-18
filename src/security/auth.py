"""
认证服务实现
"""

import jwt
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, TokenData, SecurityConfig
from ..core.config import NecoRAGConfig

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证
oauth2_scheme = HTTPBearer()

class AuthService:
    """基础认证服务"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """验证密码强度"""
        if len(password) < self.config.password_min_length:
            return False, f"密码长度至少 {self.config.password_min_length} 位"
        
        if self.config.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        
        if self.config.password_require_lowercase and not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        
        if self.config.password_require_digits and not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        
        if self.config.password_require_special and not any(not c.isalnum() for c in password):
            return False, "密码必须包含特殊字符"
        
        return True, "密码强度符合要求"

class JWTAuthService(AuthService):
    """JWT 认证服务"""
    
    def __init__(self, config: SecurityConfig):
        super().__init__(config)
        self.secret_key = config.jwt_secret_key
        self.algorithm = config.jwt_algorithm
        self.expire_minutes = config.jwt_expire_minutes
    
    def create_access_token(self, user: User) -> str:
        """创建访问令牌"""
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode = {
            "user_id": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles],
            "permissions": [perm.value for perm in user.permissions],
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> TokenData:
        """解码访问令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(**payload)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已过期"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的 Token"
            )
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
    ) -> User:
        """获取当前用户（依赖注入）"""
        token = credentials.credentials
        token_data = self.decode_access_token(token)
        
        # 这里应该从数据库获取用户信息
        # 暂时返回模拟用户
        user = User(
            id=token_data.user_id,
            username=token_data.username,
            roles=token_data.roles,
            permissions=token_data.permissions
        )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用"
            )
        
        return user
    
    async def get_current_active_user(
        self, 
        current_user: User = Depends(get_current_user)
    ) -> User:
        """获取当前活跃用户"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户未激活"
            )
        return current_user

class OAuth2Service:
    """OAuth2 认证服务"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.states: Dict[str, Any] = {}  # 存储 OAuth 状态
    
    def generate_state(self) -> str:
        """生成随机状态值"""
        return secrets.token_urlsafe(32)
    
    def create_oauth_url(self, provider: str, redirect_uri: str) -> str:
        """创建 OAuth 认证 URL"""
        if provider not in self.config.oauth2_providers:
            raise ValueError(f"不支持的 OAuth 提供商: {provider}")
        
        provider_config = self.config.oauth2_providers[provider]
        state = self.generate_state()
        
        # 存储状态
        self.states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow()
        }
        
        # 构建认证 URL（示例）
        auth_url = f"https://{provider}.com/oauth/authorize?"
        auth_url += f"client_id={provider_config['client_id']}&"
        auth_url += f"redirect_uri={redirect_uri}&"
        auth_url += f"state={state}&"
        auth_url += "scope=read:user"
        
        return auth_url
    
    def handle_callback(self, code: str, state: str) -> User:
        """处理 OAuth 回调"""
        if state not in self.states:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的状态参数"
            )
        
        state_data = self.states.pop(state)
        
        # 这里应该调用 OAuth 提供商的 API 获取用户信息
        # 暂时返回模拟用户
        user = User(
            id=f"oauth_{state_data['provider']}_123456",
            username=f"{state_data['provider']}_user",
            email="oauth@example.com",
            hashed_password="",  # OAuth 用户不需要密码
            is_active=True,
            roles=["user"]
        )
        
        return user

# 依赖注入函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    config: SecurityConfig = Depends()
) -> User:
    """获取当前用户依赖"""
    auth_service = JWTAuthService(config)
    return await auth_service.get_current_user(credentials)

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户依赖"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未激活"
        )
    return current_user