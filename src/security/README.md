# NecoRAG 安全认证模块

## 概述

安全认证模块为 NecoRAG 系统提供完整的企业级安全解决方案，包括用户认证、权限控制、安全防护等功能。

## 功能特性

### 🔐 认证服务
- **JWT Token 认证**：基于 JWT 的无状态认证机制
- **OAuth2.0 集成**：支持 GitHub、Google 等第三方登录
- **密码强度验证**：可配置的密码复杂度要求
- **会话管理**：安全的用户会话跟踪

### 👥 权限控制
- **RBAC 模型**：基于角色的访问控制
- **细粒度权限**：支持 API、数据、界面等多维度权限
- **动态权限分配**：运行时权限管理和验证
- **装饰器支持**：便捷的权限检查语法

### 🛡️ 安全防护
- **速率限制**：防止恶意请求和 DDoS 攻击
- **CSRF 防护**：跨站请求伪造保护
- **XSS 防护**：跨站脚本攻击检测和阻止
- **综合安全中间件**：一体化安全防护方案

## 快速开始

### 1. 安装依赖

```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

### 2. 环境变量配置

```bash
# JWT 配置
export JWT_SECRET_KEY="your-super-secret-key-here"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRE_MINUTES=30

# OAuth2 配置（可选）
export GITHUB_CLIENT_ID="your-github-client-id"
export GITHUB_CLIENT_SECRET="your-github-client-secret"
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"

# 安全配置
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_REQUESTS=100
export CSRF_PROTECTION_ENABLED=true
export PASSWORD_MIN_LENGTH=8
```

### 3. 基本使用示例

```python
from fastapi import FastAPI, Depends
from src.security import (
    JWTAuthService, 
    get_current_user,
    User,
    UserPermission,
    check_permission
)

app = FastAPI()

# 创建认证服务
auth_service = JWTAuthService(security_config)

@app.post("/login")
async def login(username: str, password: str):
    """用户登录"""
    user = await user_storage.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="认证失败")
    
    token = auth_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
@check_permission(UserPermission.DATA_READ)
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """受保护的端点"""
    return {"message": f"Hello {current_user.username}"}
```

## 核心组件

### 认证服务 (auth.py)

```python
# JWT 认证
class JWTAuthService(AuthService):
    def create_access_token(self, user: User) -> str:
        """创建 JWT Token"""
    
    def decode_access_token(self, token: str) -> TokenData:
        """解码和验证 Token"""

# OAuth2 服务
class OAuth2Service:
    def create_oauth_url(self, provider: str, redirect_uri: str) -> str:
        """创建 OAuth 授权链接"""
    
    def handle_callback(self, code: str, state: str) -> User:
        """处理 OAuth 回调"""
```

### 权限控制 (permission.py)

```python
# 权限服务
class PermissionService:
    def check_permission(self, user: User, permission: UserPermission) -> bool:
        """检查用户权限"""
    
    def get_user_permissions(self, user: User) -> Set[UserPermission]:
        """获取用户所有权限"""

# 权限装饰器
@check_permission(UserPermission.DATA_WRITE)
async def write_data():
    """只有具备写入权限的用户才能访问"""
```

### 安全防护 (protection.py)

```python
# 综合安全中间件
middleware = ComprehensiveSecurityMiddleware(
    app,
    rate_limit=100,
    csrf_secret="your-csrf-secret",
    enable_xss=True
)

# 单独使用各防护组件
rate_limiter = RateLimiter(app, requests_per_minute=60)
csrf_protection = CSRFProtection(app, secret_key="csrf-secret")
xss_protection = XSSProtection(app)
```

## 用户管理

### 创建用户

```python
from src.security import User, UserRole, user_storage

# 创建新用户
user = User(
    id="user_001",
    username="john_doe",
    email="john@example.com",
    hashed_password=auth_service.get_password_hash("secure_password"),
    roles=[UserRole.USER],
    permissions=[]
)

await user_storage.create_user(user)
```

### 用户认证

```python
# 用户登录验证
authenticated_user = await user_storage.authenticate_user(
    username="john_doe", 
    password="secure_password"
)

if authenticated_user:
    # 生成访问令牌
    token = auth_service.create_access_token(authenticated_user)
```

## 权限模型

### 预定义角色

| 角色 | 权限范围 | 适用场景 |
|------|----------|----------|
| ADMIN | 所有权限 | 系统管理员 |
| DEVELOPER | 开发相关权限 | 开发人员 |
| USER | 基本使用权限 | 普通用户 |
| GUEST | 只读权限 | 访客用户 |

### 权限分类

- **系统管理权限**：用户管理、配置管理、系统设置
- **数据操作权限**：数据读取、写入、删除
- **API 访问权限**：API 调用、速率限制豁免
- **界面权限**：仪表板查看、编辑、管理

## 安全配置

### 密码策略

```python
security_config = SecurityConfig(
    password_min_length=8,          # 最小长度
    password_require_uppercase=True, # 要求大写字母
    password_require_lowercase=True, # 要求小写字母
    password_require_digits=True,    # 要求数字
    password_require_special=True    # 要求特殊字符
)
```

### 速率限制

```python
# 每分钟最多 100 次请求
rate_limiter = RateLimiter(app, requests_per_minute=100)
```

## 高级用法

### 自定义权限

```python
from src.security.models import UserPermission

# 定义自定义权限
class CustomPermission(str, Enum):
    REPORT_GENERATE = "report:generate"
    MODEL_TRAIN = "model:train"

# 使用自定义权限
@check_permission(CustomPermission.REPORT_GENERATE)
async def generate_report():
    pass
```

### 多因素认证

```python
class MFAService:
    async def send_verification_code(self, user: User) -> str:
        """发送验证码"""
        pass
    
    async def verify_code(self, user: User, code: str) -> bool:
        """验证验证码"""
        pass
```

## 测试

```bash
# 运行安全模块测试
pytest tests/test_security/

# 性能测试
python -m pytest tests/test_security/ --benchmark
```

## 最佳实践

1. **密钥管理**：将 JWT 密钥存储在安全的密钥管理系统中
2. **定期轮换**：定期更换 JWT 密钥和 OAuth 凭据
3. **日志审计**：记录所有认证和授权事件
4. **最小权限**：遵循最小权限原则分配用户权限
5. **安全传输**：始终使用 HTTPS 传输敏感数据

## 故障排除

### 常见问题

1. **Token 过期**：检查 JWT_EXPIRE_MINUTES 配置
2. **权限不足**：验证用户角色和权限配置
3. **OAuth 失败**：确认客户端 ID 和密钥正确
4. **速率限制**：调整 RATE_LIMIT_REQUESTS 参数

### 日志配置

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("security")
```

## API 文档

完整的 API 文档可通过 Swagger UI 访问：
```
http://localhost:8000/docs
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进安全模块！

## 许可证

MIT License