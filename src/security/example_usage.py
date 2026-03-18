"""
安全模块使用示例
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from typing import List

from .models import User, UserRole, UserPermission
from .auth import JWTAuthService, get_current_user
from .permission import PermissionService, check_permission
from .storage import user_storage
from .config import get_security_config

app = FastAPI(title="NecoRAG Security Demo")

# 初始化服务
security_config = get_security_config()
auth_service = JWTAuthService(security_config)
permission_service = PermissionService()


# ==================== 认证示例 ====================

@app.post("/register")
async def register_user(username: str, email: str, password: str):
    """用户注册示例"""
    # 验证密码强度
    is_valid, message = auth_service.validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    # 创建用户
    user = User(
        id=f"user_{int(time.time())}",
        username=username,
        email=email,
        hashed_password=auth_service.get_password_hash(password),
        roles=[UserRole.USER],
        permissions=[]
    )
    
    try:
        created_user = await user_storage.create_user(user)
        return {"message": "用户创建成功", "user_id": created_user.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login")
async def login(username: str, password: str):
    """用户登录示例"""
    user = await user_storage.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建访问令牌
    access_token = auth_service.create_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "username": user.username,
            "roles": [role.value for role in user.roles]
        }
    }


# ==================== 权限控制示例 ====================

@app.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取用户资料（需要认证）"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "roles": [role.value for role in current_user.roles],
        "permissions": [perm.value for perm in current_user.permissions]
    }


@app.get("/admin/users")
@check_permission(UserPermission.USER_MANAGE)
async def list_users(current_user: User = Depends(get_current_user)):
    """列出所有用户（需要管理员权限）"""
    users = await user_storage.list_users()
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": [role.value for role in user.roles]
            }
            for user in users
        ]
    }


@app.post("/data/documents")
@check_permission(UserPermission.DATA_WRITE)
async def create_document(document_data: dict, current_user: User = Depends(get_current_user)):
    """创建文档（需要写入权限）"""
    # 这里实现文档创建逻辑
    return {"message": "文档创建成功", "document_id": "doc_123"}


# ==================== OAuth2 示例 ====================

@app.get("/auth/{provider}/login")
async def oauth_login(provider: str, redirect_uri: str):
    """OAuth2 登录发起"""
    from .auth import OAuth2Service
    oauth_service = OAuth2Service(security_config)
    
    try:
        auth_url = oauth_service.create_oauth_url(provider, redirect_uri)
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/callback")
async def oauth_callback(code: str, state: str, provider: str):
    """OAuth2 回调处理"""
    from .auth import OAuth2Service
    oauth_service = OAuth2Service(security_config)
    
    try:
        user = oauth_service.handle_callback(code, state)
        # 创建或更新用户
        existing_user = await user_storage.get_user_by_email(user.email)
        if existing_user:
            user = existing_user
        else:
            user = await user_storage.create_user(user)
        
        # 生成访问令牌
        access_token = auth_service.create_access_token(user)
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 权限管理示例 ====================

@app.post("/admin/users/{user_id}/permissions")
@check_permission(UserPermission.USER_MANAGE)
async def add_user_permission(
    user_id: str, 
    permission: UserPermission,
    current_user: User = Depends(get_current_user)
):
    """为用户添加权限（管理员功能）"""
    user = await user_storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 添加权限
    permission_service.add_permission_to_user(user, permission)
    await user_storage.update_user(user)
    
    return {"message": f"权限 {permission.value} 已添加给用户 {user.username}"}


@app.delete("/admin/users/{user_id}/permissions/{permission}")
@check_permission(UserPermission.USER_MANAGE)
async def remove_user_permission(
    user_id: str,
    permission: UserPermission,
    current_user: User = Depends(get_current_user)
):
    """移除用户权限（管理员功能）"""
    user = await user_storage.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 移除权限
    permission_service.remove_permission_from_user(user, permission)
    await user_storage.update_user(user)
    
    return {"message": f"权限 {permission.value} 已从用户 {user.username} 移除"}


# ==================== 安全测试端点 ====================

@app.get("/health/security")
async def security_health_check():
    """安全模块健康检查"""
    return {
        "status": "healthy",
        "components": {
            "auth_service": "ok",
            "permission_service": "ok",
            "user_storage": "ok"
        }
    }


@app.get("/debug/permissions")
async def debug_permissions(current_user: User = Depends(get_current_user)):
    """调试：显示当前用户的完整权限信息"""
    permissions = permission_service.get_user_permissions(current_user)
    return {
        "user": current_user.username,
        "roles": [role.value for role in current_user.roles],
        "direct_permissions": [perm.value for perm in current_user.permissions],
        "effective_permissions": [perm.value for perm in permissions],
        "permission_count": len(permissions)
    }


# ==================== 错误处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)