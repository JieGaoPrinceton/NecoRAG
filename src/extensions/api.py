"""
NecoRAG 插件市场 - REST API 端点

提供插件市场的 RESTful API 接口，基于 FastAPI 实现。
所有端点通过 MarketplaceClient 统一调用底层服务。
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path, Body
from pydantic import BaseModel, Field

from .client import MarketplaceClient
from .config import MarketplaceConfig

logger = logging.getLogger(__name__)

# 创建路由器
marketplace_router = APIRouter(tags=["marketplace"])

# 全局客户端实例（懒初始化）
_client: Optional[MarketplaceClient] = None


def get_client() -> MarketplaceClient:
    """获取或创建 MarketplaceClient 实例"""
    global _client
    if _client is None:
        _client = MarketplaceClient(MarketplaceConfig())
    return _client


def set_client(client: MarketplaceClient):
    """设置自定义客户端实例（用于测试或自定义配置）"""
    global _client
    _client = client


# ========================================
# Pydantic 请求/响应模型
# ========================================

class SearchRequest(BaseModel):
    """搜索请求模型"""
    q: str = Field(default="", description="搜索关键词")
    category: Optional[str] = Field(default=None, description="分类: official/certified/community")
    plugin_type: Optional[str] = Field(default=None, description="类型: perception/memory/retrieval/refinement/response/utility")
    sort: str = Field(default="relevance", description="排序: relevance/gdi_score/rating/trending/downloads/newest/name")
    tags: Optional[str] = Field(default=None, description="标签过滤，逗号分隔")
    min_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class InstallRequest(BaseModel):
    """安装请求模型"""
    plugin_id: str = Field(..., description="插件 ID")
    version: Optional[str] = Field(default=None, description="指定版本，留空安装最新版")
    force: bool = Field(default=False, description="强制安装（覆盖已安装）")


class UninstallRequest(BaseModel):
    """卸载请求模型"""
    plugin_id: str = Field(..., description="插件 ID")
    force: bool = Field(default=False, description="强制卸载（忽略反向依赖）")


class UpgradeRequest(BaseModel):
    """升级请求模型"""
    plugin_id: str = Field(..., description="插件 ID")
    target_version: Optional[str] = Field(default=None, description="目标版本")


class RatingRequest(BaseModel):
    """评分请求模型"""
    score: float = Field(..., ge=1.0, le=5.0, description="评分 1.0-5.0")
    comment: str = Field(default="", description="评论")
    user_id: str = Field(default="default", description="用户 ID")
    dimensions: Optional[dict] = Field(default=None, description="维度评分")


class AddRepositoryRequest(BaseModel):
    """添加仓库请求模型"""
    name: str = Field(..., description="仓库名称")
    url: str = Field(..., description="仓库 URL")
    repo_type: str = Field(..., description="仓库类型: local/http/github/gitee")
    priority: int = Field(default=0, description="优先级")
    config: Optional[dict] = Field(default=None, description="额外配置")


class PublishRequest(BaseModel):
    """发布插件请求模型"""
    plugin_id: str
    name: str
    version: str
    author: str
    description: str = ""
    plugin_type: str = "utility"
    category: str = "community"
    tags: List[str] = Field(default_factory=list)
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    entry_point: str = ""
    min_necorag_version: str = "0.1.0"
    max_necorag_version: Optional[str] = None
    dependencies: dict = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    package_path: Optional[str] = None


class CanaryRequest(BaseModel):
    """灰度部署请求模型"""
    plugin_id: str
    new_version: str
    percentage: float = Field(default=0.1, ge=0.01, le=1.0)


class PermissionLevelRequest(BaseModel):
    """权限级别请求模型"""
    level: str = Field(..., description="权限级别: minimal/standard/elevated/full")


class RollbackRequest(BaseModel):
    """回滚请求模型"""
    plugin_id: str = Field(..., description="插件 ID")
    to_version: str = Field(..., description="目标版本")


class RefreshGDIRequest(BaseModel):
    """刷新 GDI 请求模型"""
    plugin_id: Optional[str] = Field(default=None, description="插件 ID，留空刷新全部")


class SyncRepoRequest(BaseModel):
    """同步仓库请求模型"""
    source_name: Optional[str] = Field(default=None, description="仓库名称，留空同步全部")


# 通用响应模型
class APIResponse(BaseModel):
    """通用 API 响应模型"""
    success: bool
    message: str = ""
    data: Optional[dict] = None


# ========================================
# 辅助函数
# ========================================

def _safe_to_dict(obj):
    """安全地调用 to_dict 方法"""
    if obj is None:
        return None
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if isinstance(obj, dict):
        return obj
    return vars(obj) if hasattr(obj, '__dict__') else str(obj)


# ========================================
# 搜索和发现端点
# ========================================

@marketplace_router.get("/search")
async def search_plugins(
    q: str = Query(default="", description="搜索关键词"),
    category: Optional[str] = Query(default=None),
    plugin_type: Optional[str] = Query(default=None),
    sort: str = Query(default="relevance"),
    tags: Optional[str] = Query(default=None, description="逗号分隔的标签"),
    min_rating: Optional[float] = Query(default=None, ge=1.0, le=5.0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """搜索插件"""
    try:
        logger.info(f"搜索插件: q={q}, category={category}, type={plugin_type}")
        client = get_client()
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        result = client.search(
            query=q, category=category, plugin_type=plugin_type,
            sort_by=sort, tags=tag_list, min_rating=min_rating,
            page=page, page_size=page_size
        )
        return {
            "plugins": [p.to_dict() for p in result.plugins],
            "total_count": result.total_count,
            "page": result.page,
            "page_size": result.page_size,
            "query": result.query
        }
    except Exception as e:
        logger.error(f"搜索插件失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@marketplace_router.get("/plugins/{plugin_id}")
async def get_plugin_detail(plugin_id: str = Path(...)):
    """获取插件详细信息"""
    try:
        logger.info(f"获取插件详情: {plugin_id}")
        client = get_client()
        info = client.get_plugin_info(plugin_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"插件 {plugin_id} 不存在")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取插件详情失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@marketplace_router.get("/plugins/{plugin_id}/versions")
async def get_plugin_versions(plugin_id: str = Path(...)):
    """获取插件版本列表"""
    try:
        logger.info(f"获取插件版本: {plugin_id}")
        client = get_client()
        releases = client.get_plugin_versions(plugin_id)
        return {"plugin_id": plugin_id, "versions": [r.to_dict() for r in releases]}
    except Exception as e:
        logger.error(f"获取插件版本失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本失败: {str(e)}")


@marketplace_router.get("/trending")
async def get_trending(
    window: str = Query(default="weekly", description="daily/weekly/monthly"),
    limit: int = Query(default=20, ge=1, le=100)
):
    """获取热门趋势插件"""
    try:
        logger.info(f"获取热门趋势: window={window}, limit={limit}")
        client = get_client()
        plugins = client.get_trending(time_window=window, limit=limit)
        return {"trending": [p.to_dict() for p in plugins], "window": window}
    except Exception as e:
        logger.error(f"获取热门趋势失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取趋势失败: {str(e)}")


@marketplace_router.get("/recommendations")
async def get_recommendations(limit: int = Query(default=10, ge=1, le=50)):
    """获取推荐插件"""
    try:
        logger.info(f"获取推荐插件: limit={limit}")
        client = get_client()
        plugins = client.get_recommendations(limit=limit)
        return {"recommendations": [p.to_dict() for p in plugins]}
    except Exception as e:
        logger.error(f"获取推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取推荐失败: {str(e)}")


@marketplace_router.get("/categories")
async def get_categories():
    """获取分类概览"""
    try:
        logger.info("获取分类概览")
        client = get_client()
        return {"categories": client.get_categories()}
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@marketplace_router.get("/tags")
async def get_popular_tags(limit: int = Query(default=30, ge=1, le=100)):
    """获取热门标签"""
    try:
        logger.info(f"获取热门标签: limit={limit}")
        client = get_client()
        return {"tags": client.get_popular_tags(limit=limit)}
    except Exception as e:
        logger.error(f"获取热门标签失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标签失败: {str(e)}")


@marketplace_router.get("/plugins/{plugin_id}/similar")
async def find_similar_plugins(
    plugin_id: str = Path(...),
    limit: int = Query(default=5, ge=1, le=20)
):
    """查找相似插件"""
    try:
        logger.info(f"查找相似插件: {plugin_id}, limit={limit}")
        client = get_client()
        plugins = client.find_similar(plugin_id, limit=limit)
        return {"similar": [p.to_dict() for p in plugins]}
    except Exception as e:
        logger.error(f"查找相似插件失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"查找失败: {str(e)}")


# ========================================
# 安装管理端点
# ========================================

@marketplace_router.post("/install")
async def install_plugin(request: InstallRequest):
    """安装插件"""
    try:
        logger.info(f"安装插件: {request.plugin_id}@{request.version or 'latest'}")
        client = get_client()
        result = client.install(
            plugin_id=request.plugin_id,
            version=request.version,
            force=request.force
        )
        return _safe_to_dict(result)
    except Exception as e:
        logger.error(f"安装插件失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"安装失败: {str(e)}")


@marketplace_router.post("/uninstall")
async def uninstall_plugin(request: UninstallRequest):
    """卸载插件"""
    try:
        logger.info(f"卸载插件: {request.plugin_id}")
        client = get_client()
        result = client.uninstall(
            plugin_id=request.plugin_id,
            force=request.force
        )
        return _safe_to_dict(result)
    except Exception as e:
        logger.error(f"卸载插件失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"卸载失败: {str(e)}")


@marketplace_router.post("/upgrade")
async def upgrade_plugin(request: UpgradeRequest):
    """升级插件"""
    try:
        logger.info(f"升级插件: {request.plugin_id}@{request.target_version or 'latest'}")
        client = get_client()
        result = client.upgrade(
            plugin_id=request.plugin_id,
            target_version=request.target_version
        )
        return _safe_to_dict(result)
    except Exception as e:
        logger.error(f"升级插件失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


@marketplace_router.post("/upgrade-all")
async def upgrade_all_plugins():
    """升级所有插件"""
    try:
        logger.info("升级所有插件")
        client = get_client()
        results = client.upgrade_all()
        return {
            "results": [_safe_to_dict(r) for r in results],
            "total": len(results),
            "succeeded": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success)
        }
    except Exception as e:
        logger.error(f"批量升级失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量升级失败: {str(e)}")


@marketplace_router.get("/installed")
async def list_installed(status: Optional[str] = Query(default=None)):
    """列出已安装插件"""
    try:
        logger.info(f"列出已安装插件: status={status}")
        client = get_client()
        installations = client.list_installed(status=status)
        return {
            "installed": [i.to_dict() for i in installations],
            "total": len(installations)
        }
    except Exception as e:
        logger.error(f"列出已安装插件失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")


@marketplace_router.get("/updates")
async def check_updates():
    """检查可用更新"""
    try:
        logger.info("检查可用更新")
        client = get_client()
        return {"updates": client.check_updates()}
    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查更新失败: {str(e)}")


@marketplace_router.post("/rollback")
async def rollback_plugin(request: RollbackRequest):
    """回滚插件"""
    try:
        logger.info(f"回滚插件: {request.plugin_id}@{request.to_version}")
        client = get_client()
        result = client.rollback(plugin_id=request.plugin_id, to_version=request.to_version)
        return _safe_to_dict(result)
    except Exception as e:
        logger.error(f"回滚插件失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"回滚失败: {str(e)}")


# ========================================
# 评分端点
# ========================================

@marketplace_router.post("/plugins/{plugin_id}/rate")
async def rate_plugin(plugin_id: str = Path(...), request: RatingRequest = Body(...)):
    """为插件评分"""
    try:
        logger.info(f"为插件评分: {plugin_id}, score={request.score}")
        client = get_client()
        rating = client.rate(
            plugin_id=plugin_id,
            score=request.score,
            comment=request.comment,
            user_id=request.user_id,
            dimensions=request.dimensions
        )
        if not rating:
            raise HTTPException(status_code=400, detail="评分失败")
        return rating.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"评分失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")


@marketplace_router.get("/plugins/{plugin_id}/ratings")
async def get_plugin_ratings(
    plugin_id: str = Path(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    """获取插件评分列表"""
    try:
        logger.info(f"获取插件评分: {plugin_id}")
        client = get_client()
        return client.get_ratings(plugin_id, page=page, page_size=page_size)
    except Exception as e:
        logger.error(f"获取评分失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分失败: {str(e)}")


# ========================================
# GDI 评分端点
# ========================================

@marketplace_router.get("/plugins/{plugin_id}/gdi")
async def get_plugin_gdi(plugin_id: str = Path(...)):
    """获取插件 GDI 评分"""
    try:
        logger.info(f"获取 GDI 评分: {plugin_id}")
        client = get_client()
        score = client.get_gdi_score(plugin_id)
        if not score:
            raise HTTPException(status_code=404, detail=f"插件 {plugin_id} 无 GDI 评分")
        return score.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 GDI 评分失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取 GDI 失败: {str(e)}")


@marketplace_router.post("/gdi/refresh")
async def refresh_gdi(request: RefreshGDIRequest = Body(default=RefreshGDIRequest())):
    """刷新 GDI 评分"""
    try:
        logger.info(f"刷新 GDI 评分: plugin_id={request.plugin_id or 'all'}")
        client = get_client()
        return client.refresh_gdi(plugin_id=request.plugin_id)
    except Exception as e:
        logger.error(f"刷新 GDI 失败: {e}")
        raise HTTPException(status_code=500, detail=f"刷新 GDI 失败: {str(e)}")


@marketplace_router.get("/leaderboard")
async def get_leaderboard(
    dimension: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200)
):
    """获取 GDI 排行榜"""
    try:
        logger.info(f"获取排行榜: dimension={dimension}, limit={limit}")
        client = get_client()
        scores = client.get_leaderboard(dimension=dimension, limit=limit)
        return {"leaderboard": [s.to_dict() for s in scores], "dimension": dimension or "overall"}
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取排行榜失败: {str(e)}")


# ========================================
# 仓库管理端点
# ========================================

@marketplace_router.post("/repositories/add")
async def add_repository(request: AddRepositoryRequest):
    """添加仓库源"""
    try:
        logger.info(f"添加仓库: {request.name}")
        client = get_client()
        success = client.add_repository(
            name=request.name, url=request.url,
            repo_type=request.repo_type, priority=request.priority,
            config=request.config
        )
        return {"success": success, "message": "仓库源添加成功" if success else "添加失败"}
    except Exception as e:
        logger.error(f"添加仓库失败 {request.name}: {e}")
        raise HTTPException(status_code=500, detail=f"添加仓库失败: {str(e)}")


@marketplace_router.delete("/repositories/{name}")
async def remove_repository(name: str = Path(...)):
    """移除仓库源"""
    try:
        logger.info(f"移除仓库: {name}")
        client = get_client()
        success = client.remove_repository(name)
        return {"success": success}
    except Exception as e:
        logger.error(f"移除仓库失败 {name}: {e}")
        raise HTTPException(status_code=500, detail=f"移除仓库失败: {str(e)}")


@marketplace_router.get("/repositories")
async def list_repositories():
    """列出所有仓库源"""
    try:
        logger.info("列出所有仓库")
        client = get_client()
        return {"repositories": client.list_repositories()}
    except Exception as e:
        logger.error(f"列出仓库失败: {e}")
        raise HTTPException(status_code=500, detail=f"列出仓库失败: {str(e)}")


@marketplace_router.post("/repositories/sync")
async def sync_repositories(request: SyncRepoRequest = Body(default=SyncRepoRequest())):
    """同步仓库"""
    try:
        logger.info(f"同步仓库: {request.source_name or 'all'}")
        client = get_client()
        results = client.sync_repositories(source_name=request.source_name)
        return {
            "results": [_safe_to_dict(r) for r in results],
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"同步仓库失败: {e}")
        raise HTTPException(status_code=500, detail=f"同步仓库失败: {str(e)}")


# ========================================
# 版本和兼容性端点
# ========================================

@marketplace_router.get("/plugins/{plugin_id}/compatibility")
async def check_compatibility(
    plugin_id: str = Path(...),
    version: str = Query(..., description="要检查的版本")
):
    """检查插件版本兼容性"""
    try:
        logger.info(f"检查兼容性: {plugin_id}@{version}")
        client = get_client()
        return client.check_compatibility(plugin_id, version)
    except Exception as e:
        logger.error(f"检查兼容性失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"检查兼容性失败: {str(e)}")


@marketplace_router.get("/plugins/{plugin_id}/dependencies")
async def get_dependency_tree(
    plugin_id: str = Path(...),
    version: Optional[str] = Query(default=None)
):
    """获取依赖树"""
    try:
        logger.info(f"获取依赖树: {plugin_id}@{version or 'latest'}")
        client = get_client()
        return client.get_dependency_tree(plugin_id, version=version)
    except Exception as e:
        logger.error(f"获取依赖树失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"获取依赖树失败: {str(e)}")


# ========================================
# 灰度部署端点
# ========================================

@marketplace_router.post("/canary/create")
async def create_canary(request: CanaryRequest):
    """创建灰度部署"""
    try:
        logger.info(f"创建灰度部署: {request.plugin_id}@{request.new_version}")
        client = get_client()
        deployment = client.create_canary_deployment(
            plugin_id=request.plugin_id,
            new_version=request.new_version,
            percentage=request.percentage
        )
        if not deployment:
            raise HTTPException(status_code=400, detail="创建灰度部署失败")
        return deployment.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建灰度部署失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"创建灰度部署失败: {str(e)}")


@marketplace_router.get("/canary/{deployment_id}")
async def evaluate_canary(deployment_id: str = Path(...)):
    """评估灰度部署"""
    try:
        logger.info(f"评估灰度部署: {deployment_id}")
        client = get_client()
        return client.evaluate_canary(deployment_id)
    except Exception as e:
        logger.error(f"评估灰度部署失败 {deployment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"评估灰度部署失败: {str(e)}")


@marketplace_router.post("/canary/{deployment_id}/promote")
async def promote_canary(deployment_id: str = Path(...)):
    """推广灰度部署"""
    try:
        logger.info(f"推广灰度部署: {deployment_id}")
        client = get_client()
        return {"success": client.promote_canary(deployment_id)}
    except Exception as e:
        logger.error(f"推广灰度部署失败 {deployment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"推广灰度部署失败: {str(e)}")


@marketplace_router.post("/canary/{deployment_id}/rollback")
async def rollback_canary(deployment_id: str = Path(...)):
    """回滚灰度部署"""
    try:
        logger.info(f"回滚灰度部署: {deployment_id}")
        client = get_client()
        return {"success": client.rollback_canary(deployment_id)}
    except Exception as e:
        logger.error(f"回滚灰度部署失败 {deployment_id}: {e}")
        raise HTTPException(status_code=500, detail=f"回滚灰度部署失败: {str(e)}")


# ========================================
# 安全端点
# ========================================

@marketplace_router.get("/plugins/{plugin_id}/permissions")
async def validate_permissions(plugin_id: str = Path(...)):
    """验证插件权限"""
    try:
        logger.info(f"验证插件权限: {plugin_id}")
        client = get_client()
        result = client.validate_plugin_permissions(plugin_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"插件 {plugin_id} 不存在")
        return result.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证插件权限失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"验证权限失败: {str(e)}")


@marketplace_router.get("/security/report")
async def get_security_report():
    """获取安全报告"""
    try:
        logger.info("获取安全报告")
        client = get_client()
        return client.get_security_report()
    except Exception as e:
        logger.error(f"获取安全报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取安全报告失败: {str(e)}")


@marketplace_router.put("/plugins/{plugin_id}/permission-level")
async def set_permission_level(
    plugin_id: str = Path(...),
    request: PermissionLevelRequest = Body(...)
):
    """设置插件权限级别"""
    try:
        logger.info(f"设置权限级别: {plugin_id} -> {request.level}")
        client = get_client()
        success = client.set_plugin_permission_level(plugin_id, request.level)
        return {"success": success}
    except Exception as e:
        logger.error(f"设置权限级别失败 {plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"设置权限级别失败: {str(e)}")


# ========================================
# 统计和管理端点
# ========================================

@marketplace_router.get("/stats")
async def get_marketplace_stats():
    """获取市场统计"""
    try:
        logger.info("获取市场统计")
        client = get_client()
        return client.get_marketplace_stats()
    except Exception as e:
        logger.error(f"获取市场统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@marketplace_router.post("/publish")
async def publish_plugin(request: PublishRequest):
    """发布插件到市场"""
    try:
        logger.info(f"发布插件: {request.plugin_id}@{request.version}")
        # 导入必要的模型
        from .models import PluginManifest, PluginType, PluginCategory, PluginPermission
        
        # 构建 PluginManifest
        manifest = PluginManifest(
            plugin_id=request.plugin_id,
            name=request.name,
            version=request.version,
            author=request.author,
            description=request.description,
            plugin_type=PluginType(request.plugin_type),
            category=PluginCategory(request.category),
            tags=request.tags,
            license=request.license,
            homepage=request.homepage,
            repository=request.repository,
            entry_point=request.entry_point,
            min_necorag_version=request.min_necorag_version,
            max_necorag_version=request.max_necorag_version,
            dependencies=request.dependencies,
            permissions=[
                PluginPermission(p) for p in request.permissions 
                if p in [e.value for e in PluginPermission]
            ],
        )
        
        client = get_client()
        success = client.publish_plugin(manifest, package_path=request.package_path)
        return {"success": success, "plugin_id": request.plugin_id}
    except (ValueError, KeyError) as e:
        logger.warning(f"无效的插件信息: {e}")
        raise HTTPException(status_code=400, detail=f"无效的插件信息: {str(e)}")
    except Exception as e:
        logger.error(f"发布插件失败 {request.plugin_id}: {e}")
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@marketplace_router.post("/cache/clear")
async def clear_cache():
    """清理缓存"""
    try:
        logger.info("清理缓存")
        client = get_client()
        return client.clear_cache()
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")
