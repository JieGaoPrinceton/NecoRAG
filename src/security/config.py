"""
安全配置管理
"""

import os
from typing import Dict, List
from pydantic import BaseModel
from .models import SecurityConfig, OAuth2Provider


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> SecurityConfig:
        """加载安全配置"""
        # 从环境变量读取配置
        jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
        
        # OAuth2 配置
        oauth2_providers = {}
        
        # GitHub OAuth 配置
        github_client_id = os.getenv("GITHUB_CLIENT_ID")
        github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        if github_client_id and github_client_secret:
            oauth2_providers[OAuth2Provider.GITHUB] = {
                "client_id": github_client_id,
                "client_secret": github_client_secret,
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_info_url": "https://api.github.com/user"
            }
        
        # Google OAuth 配置
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if google_client_id and google_client_secret:
            oauth2_providers[OAuth2Provider.GOOGLE] = {
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
            }
        
        return SecurityConfig(
            jwt_secret_key=jwt_secret_key,
            jwt_algorithm=jwt_algorithm,
            jwt_expire_minutes=jwt_expire_minutes,
            oauth2_providers=oauth2_providers,
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            csrf_protection_enabled=os.getenv("CSRF_PROTECTION_ENABLED", "true").lower() == "true",
            xss_protection_enabled=os.getenv("XSS_PROTECTION_ENABLED", "true").lower() == "true",
            allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            password_require_uppercase=os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
            password_require_lowercase=os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true",
            password_require_digits=os.getenv("PASSWORD_REQUIRE_DIGITS", "true").lower() == "true",
            password_require_special=os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
        )
    
    def get_config(self) -> SecurityConfig:
        """获取安全配置"""
        return self.config
    
    def update_config(self, new_config: SecurityConfig) -> None:
        """更新安全配置"""
        self.config = new_config
    
    def get_oauth_config(self, provider: OAuth2Provider) -> Dict[str, str]:
        """获取特定 OAuth 提供商的配置"""
        return self.config.oauth2_providers.get(provider, {})
    
    def is_oauth_enabled(self, provider: OAuth2Provider) -> bool:
        """检查 OAuth 提供商是否已启用"""
        return provider in self.config.oauth2_providers


# 全局安全管理器实例
security_manager = SecurityManager()


def get_security_config() -> SecurityConfig:
    """获取安全配置依赖"""
    return security_manager.get_config()