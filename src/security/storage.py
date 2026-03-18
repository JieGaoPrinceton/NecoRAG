"""
用户存储和会话管理
"""

from typing import Optional, Dict, List
from datetime import datetime
import json
from ..memory.backends.base import BaseMemoryBackend
from ..memory.backends.memory_store import InMemoryStore
from .models import User, UserRole, UserPermission


class UserStorage:
    """用户存储管理"""
    
    def __init__(self, backend: BaseMemoryBackend = None):
        self.backend = backend or InMemoryStore()
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """确保必要的索引存在"""
        # 在实际实现中，这里会创建数据库索引
        pass
    
    async def create_user(self, user: User) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = await self.get_user_by_username(user.username)
        if existing_user:
            raise ValueError(f"用户名 '{user.username}' 已存在")
        
        # 检查邮箱是否已存在
        if user.email:
            existing_email = await self.get_user_by_email(user.email)
            if existing_email:
                raise ValueError(f"邮箱 '{user.email}' 已存在")
        
        # 设置默认角色
        if not user.roles:
            user.roles = [UserRole.USER]
        
        # 存储用户
        key = f"user:{user.id}"
        await self.backend.set(key, user.model_dump())
        
        # 创建索引
        await self.backend.set(f"username:{user.username}", user.id)
        if user.email:
            await self.backend.set(f"email:{user.email}", user.id)
        
        return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        key = f"user:{user_id}"
        data = await self.backend.get(key)
        if data:
            return User(**data)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_id = await self.backend.get(f"username:{username}")
        if user_id:
            return await self.get_user(user_id)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user_id = await self.backend.get(f"email:{email}")
        if user_id:
            return await self.get_user(user_id)
        return None
    
    async def update_user(self, user: User) -> User:
        """更新用户信息"""
        existing_user = await self.get_user(user.id)
        if not existing_user:
            raise ValueError(f"用户 '{user.id}' 不存在")
        
        # 更新索引（如果用户名或邮箱发生变化）
        if existing_user.username != user.username:
            await self.backend.delete(f"username:{existing_user.username}")
            await self.backend.set(f"username:{user.username}", user.id)
        
        if existing_user.email != user.email:
            if existing_user.email:
                await self.backend.delete(f"email:{existing_user.email}")
            if user.email:
                await self.backend.set(f"email:{user.email}", user.id)
        
        # 更新用户数据
        key = f"user:{user.id}"
        await self.backend.set(key, user.model_dump())
        
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # 删除索引
        await self.backend.delete(f"username:{user.username}")
        if user.email:
            await self.backend.delete(f"email:{user.email}")
        
        # 删除用户数据
        key = f"user:{user_id}"
        await self.backend.delete(key)
        
        return True
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """列出用户"""
        # 在实际实现中，这会使用数据库查询
        # 这里简化实现，遍历所有用户键
        users = []
        # 模拟分页查询
        for i in range(skip, skip + limit):
            user_id = f"user_{i}"
            user = await self.get_user(user_id)
            if user:
                users.append(user)
        return users
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        
        # 验证密码（在实际应用中，这里会使用 AuthService 的 verify_password 方法）
        # 这里简化处理
        if user.hashed_password == password:  # 注意：实际应用中不应明文存储密码
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            await self.update_user(user)
            return user
        
        return None


class SessionManager:
    """会话管理"""
    
    def __init__(self, backend: BaseMemoryBackend = None):
        self.backend = backend or InMemoryStore()
        self.session_timeout = 3600  # 1小时
    
    async def create_session(self, user_id: str, session_data: dict = None) -> str:
        """创建会话"""
        import secrets
        session_id = secrets.token_urlsafe(32)
        
        session_info = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_access": datetime.utcnow().isoformat(),
            "data": session_data or {}
        }
        
        key = f"session:{session_id}"
        await self.backend.set(key, session_info, ttl=self.session_timeout)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话信息"""
        key = f"session:{session_id}"
        session_info = await self.backend.get(key)
        
        if session_info:
            # 更新最后访问时间
            session_info["last_access"] = datetime.utcnow().isoformat()
            await self.backend.set(key, session_info, ttl=self.session_timeout)
            return session_info
        
        return None
    
    async def update_session(self, session_id: str, session_data: dict) -> bool:
        """更新会话数据"""
        key = f"session:{session_id}"
        session_info = await self.backend.get(key)
        
        if session_info:
            session_info["data"].update(session_data)
            session_info["last_access"] = datetime.utcnow().isoformat()
            await self.backend.set(key, session_info, ttl=self.session_timeout)
            return True
        
        return False
    
    async def destroy_session(self, session_id: str) -> bool:
        """销毁会话"""
        key = f"session:{session_id}"
        return await self.backend.delete(key)
    
    async def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        # 内存存储会自动清理过期数据
        # 在数据库实现中，这里会执行清理查询
        return 0


# 全局实例
user_storage = UserStorage()
session_manager = SessionManager()