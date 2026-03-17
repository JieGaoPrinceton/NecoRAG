"""
Dashboard Server - FastAPI 服务器
提供 RESTful API 和 Web UI
"""

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path

from src.dashboard.config_manager import ConfigManager
from src.dashboard.models import RAGProfile, DashboardStats


# Pydantic 模型用于 API
class CreateProfileRequest(BaseModel):
    """创建 Profile 请求"""
    profile_name: str
    description: str = ""


class UpdateProfileRequest(BaseModel):
    """更新 Profile 请求"""
    profile_name: Optional[str] = None
    description: Optional[str] = None
    whiskers_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    retrieval_config: Optional[Dict[str, Any]] = None
    grooming_config: Optional[Dict[str, Any]] = None
    purr_config: Optional[Dict[str, Any]] = None


class ModuleParametersUpdate(BaseModel):
    """模块参数更新请求"""
    module: str
    parameters: Dict[str, Any]


class DashboardServer:
    """
    Dashboard 服务器
    
    功能：
    - 配置管理 API
    - 模块监控 API
    - Web UI 界面
    - 统计信息展示
    """
    
    def __init__(
        self,
        config_dir: str = "./configs",
        host: str = "0.0.0.0",
        port: int = 8000
    ):
        """
        初始化 Dashboard 服务器
        
        Args:
            config_dir: 配置目录
            host: 主机地址
            port: 端口号
        """
        self.host = host
        self.port = port
        self.config_manager = ConfigManager(config_dir)
        
        # 创建 FastAPI 应用
        self.app = FastAPI(
            title="NecoRAG Dashboard",
            description="NecoRAG 配置管理和监控界面",
            version="1.0.0"
        )
        
        # 配置 CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._setup_routes()
        
        # 统计信息
        self.stats = DashboardStats()
    
    def _setup_routes(self):
        """设置路由"""
        
        # ========== Profile 管理 API ==========
        
        @self.app.get("/api/profiles", response_model=List[Dict])
        async def get_all_profiles():
            """获取所有 Profile"""
            profiles = self.config_manager.get_all_profiles()
            return [p.to_dict() for p in profiles]
        
        @self.app.get("/api/profiles/{profile_id}", response_model=Dict)
        async def get_profile(profile_id: str):
            """获取单个 Profile"""
            profile = self.config_manager.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            return profile.to_dict()
        
        @self.app.get("/api/profiles/active", response_model=Dict)
        async def get_active_profile():
            """获取当前活动的 Profile"""
            profile = self.config_manager.get_active_profile()
            if not profile:
                raise HTTPException(status_code=404, detail="No active profile")
            return profile.to_dict()
        
        @self.app.post("/api/profiles", response_model=Dict)
        async def create_profile(request: CreateProfileRequest):
            """创建新 Profile"""
            profile = self.config_manager.create_profile(
                profile_name=request.profile_name,
                description=request.description
            )
            return profile.to_dict()
        
        @self.app.put("/api/profiles/{profile_id}", response_model=Dict)
        async def update_profile(profile_id: str, request: UpdateProfileRequest):
            """更新 Profile"""
            updates = request.dict(exclude_unset=True)
            success = self.config_manager.update_profile(profile_id, updates)
            if not success:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            profile = self.config_manager.get_profile(profile_id)
            return profile.to_dict()
        
        @self.app.delete("/api/profiles/{profile_id}")
        async def delete_profile(profile_id: str):
            """删除 Profile"""
            success = self.config_manager.delete_profile(profile_id)
            if not success:
                raise HTTPException(status_code=404, detail="Profile not found")
            return {"message": "Profile deleted"}
        
        @self.app.post("/api/profiles/{profile_id}/activate")
        async def activate_profile(profile_id: str):
            """激活 Profile"""
            success = self.config_manager.set_active_profile(profile_id)
            if not success:
                raise HTTPException(status_code=404, detail="Profile not found")
            return {"message": "Profile activated"}
        
        @self.app.post("/api/profiles/{profile_id}/duplicate", response_model=Dict)
        async def duplicate_profile(profile_id: str, new_name: str):
            """复制 Profile"""
            profile = self.config_manager.duplicate_profile(profile_id, new_name)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            return profile.to_dict()
        
        @self.app.post("/api/profiles/{profile_id}/export")
        async def export_profile(profile_id: str, export_path: str):
            """导出 Profile"""
            success = self.config_manager.export_profile(profile_id, export_path)
            if not success:
                raise HTTPException(status_code=400, detail="Export failed")
            return {"message": "Profile exported"}
        
        @self.app.post("/api/profiles/import", response_model=Dict)
        async def import_profile(import_path: str):
            """导入 Profile"""
            profile = self.config_manager.import_profile(import_path)
            if not profile:
                raise HTTPException(status_code=400, detail="Import failed")
            return profile.to_dict()
        
        # ========== 模块参数管理 API ==========
        
        @self.app.get("/api/profiles/{profile_id}/modules/{module}", response_model=Dict)
        async def get_module_parameters(profile_id: str, module: str):
            """获取模块参数"""
            profile = self.config_manager.get_profile(profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            if module not in ['whiskers', 'memory', 'retrieval', 'grooming', 'purr']:
                raise HTTPException(status_code=400, detail="Invalid module name")
            
            config = getattr(profile, f"{module}_config")
            return {
                "module": module,
                "parameters": config.parameters,
                "description": config.description
            }
        
        @self.app.put("/api/profiles/{profile_id}/modules/{module}")
        async def update_module_parameters(
            profile_id: str,
            module: str,
            request: ModuleParametersUpdate
        ):
            """更新模块参数"""
            if module not in ['whiskers', 'memory', 'retrieval', 'grooming', 'purr']:
                raise HTTPException(status_code=400, detail="Invalid module name")
            
            updates = {f"{module}_config": request.parameters}
            success = self.config_manager.update_profile(profile_id, updates)
            if not success:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            return {"message": "Module parameters updated"}
        
        # ========== 统计信息 API ==========
        
        @self.app.get("/api/stats", response_model=Dict)
        async def get_stats():
            """获取统计信息"""
            return {
                "total_documents": self.stats.total_documents,
                "total_chunks": self.stats.total_chunks,
                "total_queries": self.stats.total_queries,
                "active_sessions": self.stats.active_sessions,
                "memory_usage": self.stats.memory_usage,
                "performance_metrics": self.stats.performance_metrics
            }
        
        @self.app.post("/api/stats/reset")
        async def reset_stats():
            """重置统计信息"""
            self.stats = DashboardStats()
            return {"message": "Stats reset"}
        
        # ========== Web UI ==========
        
        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """返回 Dashboard UI"""
            html_file = Path(__file__).parent / "static" / "index.html"
            if html_file.exists():
                return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
            else:
                # 返回简单的 HTML
                return self._get_simple_ui()
        
        # 静态文件服务
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    def _get_simple_ui(self) -> str:
        """返回简单 UI"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>NecoRAG Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1 { margin-bottom: 20px; }
        .profiles { margin-bottom: 30px; }
        .profile-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            background: #f9f9f9;
        }
        .profile-card.active {
            border-color: #4CAF50;
            background: #f1f8f4;
        }
        .module-config {
            background: #fff;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }
        .param-group { margin-bottom: 20px; }
        .param-row { margin-bottom: 10px; }
        .param-row label { display: inline-block; width: 200px; font-weight: bold; }
        .param-row input { padding: 5px; width: 300px; }
        .btn {
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn-primary { background: #2196F3; color: white; }
        .btn-success { background: #4CAF50; color: white; }
        .btn-danger { background: #f44336; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NecoRAG Dashboard</h1>
        
        <div class="profiles">
            <h2>配置 Profiles</h2>
            <div id="profile-list"></div>
        </div>
        
        <div class="stats">
            <h2>统计信息</h2>
            <div id="stats-display"></div>
        </div>
    </div>
    
    <script>
        // 加载 Profiles
        async function loadProfiles() {
            const response = await fetch('/api/profiles');
            const profiles = await response.json();
            
            const container = document.getElementById('profile-list');
            container.innerHTML = '';
            
            profiles.forEach(profile => {
                const card = document.createElement('div');
                card.className = 'profile-card' + (profile.is_active ? ' active' : '');
                card.innerHTML = `
                    <h3>${profile.profile_name} ${profile.is_active ? '(活动)' : ''}</h3>
                    <p>${profile.description}</p>
                    <p><small>创建: ${new Date(profile.created_at).toLocaleString()}</small></p>
                    <button class="btn btn-success" onclick="activateProfile('${profile.profile_id}')">激活</button>
                    <button class="btn btn-primary" onclick="viewProfile('${profile.profile_id}')">查看配置</button>
                `;
                container.appendChild(card);
            });
        }
        
        // 激活 Profile
        async function activateProfile(profileId) {
            await fetch(`/api/profiles/${profileId}/activate`, { method: 'POST' });
            loadProfiles();
        }
        
        // 查看 Profile
        async function viewProfile(profileId) {
            const response = await fetch(`/api/profiles/${profileId}`);
            const profile = await response.json();
            console.log(profile);
            alert('Profile 详情已打印到控制台');
        }
        
        // 加载统计信息
        async function loadStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            const container = document.getElementById('stats-display');
            container.innerHTML = `
                <p>文档总数: ${stats.total_documents}</p>
                <p>块总数: ${stats.total_chunks}</p>
                <p>查询总数: ${stats.total_queries}</p>
                <p>活动会话: ${stats.active_sessions}</p>
            `;
        }
        
        // 初始化
        loadProfiles();
        loadStats();
        
        // 定时刷新
        setInterval(loadStats, 5000);
    </script>
</body>
</html>
        """
    
    def run(self):
        """启动服务器"""
        print(f"\n{'='*60}")
        print(f"  NecoRAG Dashboard 启动中...")
        print(f"  访问地址: http://{self.host}:{self.port}")
        print(f"  API 文档: http://{self.host}:{self.port}/docs")
        print(f"{'='*60}\n")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
