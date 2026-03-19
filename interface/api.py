"""
RESTful API 服务
提供知识库查询、插入、更新、删除等HTTP接口
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Dict, Any

from .models import (
    QueryRequest, QueryResponse, InsertRequest, 
    UpdateRequest, DeleteRequest, HealthStatus
)
from .knowledge_service import knowledge_service

# 尝试导入插件市场路由（可选模块）
try:
    from src.marketplace.api import marketplace_router
    _marketplace_available = True
except ImportError:
    _marketplace_available = False


def create_api_app() -> FastAPI:
    """创建API应用"""
    app = FastAPI(
        title="NecoRAG Knowledge API",
        description="NecoRAG 知识库 RESTful API 接口",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger = logging.getLogger(__name__)
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "Welcome to NecoRAG Knowledge API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    @app.get("/health", response_model=HealthStatus)
    async def health_check():
        """健康检查"""
        try:
            stats = await knowledge_service.get_knowledge_stats()
            return HealthStatus(
                status="healthy",
                components={
                    "knowledge_service": "healthy",
                    "memory_layers": "healthy",
                    "retrieval_engine": "healthy"
                },
                uptime=stats.get("uptime", 0),
                timestamp=stats.get("timestamp")
            )
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return HealthStatus(
                status="unhealthy",
                components={"knowledge_service": "unhealthy"},
                uptime=0,
                timestamp=""
            )
    
    @app.post("/query", response_model=QueryResponse)
    async def query_knowledge(request: QueryRequest):
        """知识查询接口"""
        try:
            response = await knowledge_service.query_knowledge(request)
            return response
        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )
    
    @app.post("/insert")
    async def insert_knowledge(request: InsertRequest):
        """知识插入接口"""
        try:
            result = await knowledge_service.insert_knowledge(request)
            return result
        except Exception as e:
            logger.error(f"插入失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"插入失败: {str(e)}"
            )
    
    @app.put("/update")
    async def update_knowledge(request: UpdateRequest):
        """知识更新接口"""
        try:
            result = await knowledge_service.update_knowledge(request)
            return result
        except Exception as e:
            logger.error(f"更新失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"更新失败: {str(e)}"
            )
    
    @app.delete("/delete")
    async def delete_knowledge(request: DeleteRequest):
        """知识删除接口"""
        try:
            result = await knowledge_service.delete_knowledge(request)
            return result
        except Exception as e:
            logger.error(f"删除失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除失败: {str(e)}"
            )
    
    @app.get("/stats")
    async def get_statistics():
        """获取知识库统计信息"""
        try:
            stats = await knowledge_service.get_knowledge_stats()
            return stats
        except Exception as e:
            logger.error(f"获取统计失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取统计失败: {str(e)}"
            )
    
    @app.get("/suggestions/{query}")
    async def get_query_suggestions(query: str):
        """获取查询建议"""
        try:
            # 这里可以实现更智能的建议生成
            suggestions = [f"{query}相关", f"{query}应用", f"{query}发展"]
            return {"query": query, "suggestions": suggestions}
        except Exception as e:
            logger.error(f"生成建议失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"生成建议失败: {str(e)}"
            )
    
    # 挂载插件市场路由（如果可用）
    if _marketplace_available:
        app.include_router(marketplace_router, prefix="/api/v1/marketplace")
        logger.info("插件市场 API 路由已挂载")
    
    return app


def run_api_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """运行API服务器"""
    app = create_api_app()
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_api_server()