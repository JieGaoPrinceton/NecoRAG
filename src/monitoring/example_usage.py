"""
监控模块使用示例
"""

import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from . import (
    monitoring_service,
    system_metrics,
    app_metrics,
    health_checker,
    alert_manager,
    create_monitoring_app
)


# ==================== 基础使用示例 ====================

async def basic_monitoring_example():
    """基础监控使用示例"""
    print("=== 基础监控示例 ===")
    
    # 1. 收集系统指标
    print("\n1. 收集系统指标:")
    system_data = system_metrics.collect_system_metrics()
    print(f"   CPU 使用率: {system_data['cpu_usage_percent']:.1f}%")
    print(f"   内存使用率: {system_data['memory_usage_percent']:.1f}%")
    print(f"   磁盘使用率: {system_data['disk_usage_percent']:.1f}%")
    
    # 2. 执行健康检查
    print("\n2. 执行健康检查:")
    health_results = await health_checker.run_all_checks()
    for result in health_results[:3]:  # 显示前3个检查结果
        print(f"   {result.name}: {result.status.value} - {result.message}")
    
    # 3. 评估告警
    print("\n3. 评估告警规则:")
    alerts = await alert_manager.evaluate_rules(metrics_data=system_data)
    print(f"   触发告警数量: {len(alerts)}")
    for alert in alerts:
        print(f"   - {alert.summary} ({alert.level.value})")


# ==================== Web 应用集成示例 ====================

def create_main_app():
    """创建主应用并集成监控"""
    app = FastAPI(title="NecoRAG Main App")
    
    # 添加监控中间件
    @app.middleware("http")
    async def monitoring_middleware(request: Request, call_next):
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 记录指标
        duration = time.time() - start_time
        app_metrics.record_api_call(
            str(request.url.path),
            response.status_code,
            duration
        )
        
        return response
    
    # 模拟 API 端点
    @app.get("/api/search")
    async def search_documents(query: str = "test"):
        """模拟搜索 API"""
        # 模拟处理时间
        await asyncio.sleep(0.1)
        
        # 记录 RAG 响应时间
        app_metrics.record_rag_response_time(0.1, success=True)
        
        return {"results": [f"Result for: {query}"], "count": 1}
    
    @app.get("/api/status")
    async def get_status():
        """获取应用状态"""
        return {"status": "running", "timestamp": time.time()}
    
    return app


# ==================== 监控服务独立运行示例 ====================

async def run_standalone_monitoring():
    """独立运行监控服务示例"""
    print("=== 独立监控服务示例 ===")
    
    try:
        # 启动监控服务
        await monitoring_service.start()
        print("✓ 监控服务已启动")
        
        # 运行一段时间
        for i in range(10):
            print(f"\n第 {i+1} 轮监控:")
            
            # 收集指标
            metrics = system_metrics.collect_system_metrics()
            print(f"  系统指标已收集")
            
            # 执行健康检查
            health_results = await health_checker.run_all_checks()
            healthy_count = len([r for r in health_results if r.status == "healthy"])
            print(f"  健康检查: {healthy_count}/{len(health_results)} 项正常")
            
            # 评估告警
            alerts = await alert_manager.evaluate_rules(metrics_data=metrics)
            if alerts:
                print(f"  新触发告警: {len(alerts)} 个")
                for alert in alerts:
                    print(f"    - {alert.summary}")
            
            await asyncio.sleep(5)  # 等待5秒
        
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        # 停止监控服务
        await monitoring_service.stop()
        print("✓ 监控服务已停止")


# ==================== 完整应用示例 ====================

async def run_full_application():
    """运行完整应用示例"""
    print("=== 完整应用示例 ===")
    
    # 创建主应用
    main_app = create_main_app()
    
    # 挂载监控应用
    monitoring_app = create_monitoring_app()
    main_app.mount("/monitoring", monitoring_app)
    
    # 启动监控服务
    await monitoring_service.start()
    print("✓ 监控服务已启动")
    
    try:
        # 启动 Web 服务器
        config = uvicorn.Config(
            main_app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        print("✓ Web 服务器已启动")
        print("访问地址:")
        print("  主应用: http://localhost:8000")
        print("  监控仪表板: http://localhost:8000/monitoring/")
        print("  监控 API: http://localhost:8000/monitoring/api/v1/monitoring/dashboard")
        print("\n按 Ctrl+C 停止服务")
        
        await server.serve()
        
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        # 清理资源
        await monitoring_service.stop()
        print("✓ 服务已停止")


# ==================== 自定义监控示例 ====================

async def custom_monitoring_example():
    """自定义监控示例"""
    print("=== 自定义监控示例 ===")
    
    # 1. 添加自定义健康检查
    async def check_custom_component():
        """自定义组件健康检查"""
        try:
            # 模拟检查逻辑
            await asyncio.sleep(0.1)
            return {
                "status": "healthy",
                "message": "自定义组件运行正常",
                "details": {"component_version": "1.0.0"}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"自定义组件异常: {str(e)}"
            }
    
    health_checker.register_check("custom_component", check_custom_component)
    print("✓ 已注册自定义健康检查")
    
    # 2. 添加自定义告警规则
    from .alerts import AlertRule, AlertLevel
    
    custom_rule = AlertRule(
        name="high_custom_metric",
        expression="custom_metric > 100",
        level=AlertLevel.WARNING,
        description="自定义指标过高"
    )
    alert_manager.add_alert_rule(custom_rule)
    print("✓ 已添加自定义告警规则")
    
    # 3. 记录自定义指标
    system_metrics.record_metric("custom_metric", 42.5)
    print("✓ 已记录自定义指标")
    
    # 4. 执行检查
    results = await health_checker.run_all_checks()
    alerts = await alert_manager.evaluate_rules()
    
    print(f"自定义健康检查结果: {[r for r in results if r.name == 'custom_component'][0].status}")
    print(f"自定义告警触发: {len(alerts)} 个")


# ==================== 性能测试示例 ====================

async def performance_test_example():
    """性能测试示例"""
    print("=== 性能测试示例 ===")
    
    # 测试指标收集性能
    start_time = time.time()
    for i in range(100):
        system_metrics.collect_system_metrics()
    collect_time = time.time() - start_time
    print(f"100次指标收集耗时: {collect_time:.3f}秒 ({collect_time*10:.1f}ms/次)")
    
    # 测试健康检查性能
    start_time = time.time()
    await health_checker.run_all_checks()
    check_time = time.time() - start_time
    print(f"健康检查耗时: {check_time:.3f}秒")
    
    # 测试告警评估性能
    start_time = time.time()
    await alert_manager.evaluate_rules()
    eval_time = time.time() - start_time
    print(f"告警评估耗时: {eval_time:.3f}秒")


# ==================== 主函数 ====================

async def main():
    """主函数 - 运行各种示例"""
    print("NecoRAG 监控模块使用示例")
    print("=" * 50)
    
    # 运行基础示例
    await basic_monitoring_example()
    
    # 运行自定义示例
    await custom_monitoring_example()
    
    # 运行性能测试
    await performance_test_example()
    
    print("\n" + "=" * 50)
    print("示例运行完成!")
    print("\n可选操作:")
    print("1. 运行独立监控服务: python -m src.monitoring.example standalone")
    print("2. 运行完整应用: python -m src.monitoring.example full")
    print("3. 运行性能测试: python -m src.monitoring.example perf")


# 命令行入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "standalone":
            asyncio.run(run_standalone_monitoring())
        elif mode == "full":
            asyncio.run(run_full_application())
        elif mode == "perf":
            asyncio.run(performance_test_example())
        else:
            print(f"未知模式: {mode}")
            print("可用模式: standalone, full, perf")
    else:
        asyncio.run(main())