"""
安全防护机制
"""

import time
import hashlib
from typing import Dict, Set, Optional
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件基类"""
    
    async def dispatch(self, request: Request, call_next):
        # 安全检查
        if not await self.pre_process(request):
            return Response("Forbidden", status_code=403)
        
        # 处理请求
        response = await call_next(request)
        
        # 后处理
        await self.post_process(request, response)
        
        return response
    
    async def pre_process(self, request: Request) -> bool:
        """请求预处理"""
        return True
    
    async def post_process(self, request: Request, response: Response):
        """响应后处理"""
        pass

class RateLimiter(SecurityMiddleware):
    """速率限制器"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)  # {client_ip: [timestamps]}
    
    async def pre_process(self, request: Request) -> bool:
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # 清理过期请求记录
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if current_time - timestamp < 60  # 1分钟窗口
        ]
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        
        # 记录本次请求
        self.requests[client_ip].append(current_time)
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class CSRFProtection(SecurityMiddleware):
    """CSRF 防护"""
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
        self.sessions: Dict[str, str] = {}  # {session_id: csrf_token}
    
    async def pre_process(self, request: Request) -> bool:
        # 只对修改性请求进行 CSRF 检查
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        
        # 获取 CSRF Token
        csrf_token = request.headers.get("X-CSRF-Token") or \
                    request.form().get("csrf_token")
        
        if not csrf_token:
            return False
        
        # 验证 Token
        session_id = request.cookies.get("session_id")
        if not session_id or session_id not in self.sessions:
            return False
        
        expected_token = self.sessions[session_id]
        return self._secure_compare(csrf_token, expected_token)
    
    def generate_csrf_token(self, session_id: str) -> str:
        """生成 CSRF Token"""
        token = hashlib.sha256(f"{self.secret_key}{session_id}{time.time()}".encode()).hexdigest()
        self.sessions[session_id] = token
        return token
    
    def _secure_compare(self, a: str, b: str) -> bool:
        """安全字符串比较，防止时序攻击"""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        return result == 0

class XSSProtection(SecurityMiddleware):
    """XSS 防护"""
    
    def __init__(self, app):
        super().__init__(app)
        self.dangerous_patterns = [
            '<script', '</script>', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'onclick=', 'onmouseover='
        ]
    
    async def pre_process(self, request: Request) -> bool:
        # 检查查询参数
        for key, value in request.query_params.items():
            if self._contains_xss_pattern(value):
                return False
        
        # 检查表单数据
        if request.method in ["POST", "PUT", "PATCH"]:
            form_data = await request.form()
            for key, value in form_data.items():
                if self._contains_xss_pattern(str(value)):
                    return False
        
        return True
    
    async def post_process(self, request: Request, response: Response):
        # 添加安全头部
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    def _contains_xss_pattern(self, text: str) -> bool:
        """检查是否包含 XSS 攻击模式"""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.dangerous_patterns)

# 安全中间件组合
class ComprehensiveSecurityMiddleware(SecurityMiddleware):
    """综合性安全中间件"""
    
    def __init__(
        self, 
        app,
        rate_limit: int = 100,
        csrf_secret: str = None,
        enable_xss: bool = True
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(app, rate_limit)
        self.csrf_protection = CSRFProtection(app, csrf_secret) if csrf_secret else None
        self.xss_protection = XSSProtection(app) if enable_xss else None
    
    async def pre_process(self, request: Request) -> bool:
        # 速率限制检查
        if not await self.rate_limiter.pre_process(request):
            return False
        
        # CSRF 检查
        if self.csrf_protection and not await self.csrf_protection.pre_process(request):
            return False
        
        # XSS 检查
        if self.xss_protection and not await self.xss_protection.pre_process(request):
            return False
        
        return True
    
    async def post_process(self, request: Request, response: Response):
        # 应用安全头部
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSRF Token 设置
        if self.csrf_protection and request.method == "GET":
            session_id = request.cookies.get("session_id", self._generate_session_id())
            csrf_token = self.csrf_protection.generate_csrf_token(session_id)
            response.set_cookie("csrf_token", csrf_token, httponly=True, secure=True)
        
        # XSS 防护后处理
        if self.xss_protection:
            await self.xss_protection.post_process(request, response)
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return hashlib.sha256(f"session_{time.time()}".encode()).hexdigest()