"""
NecoRAG 调试面板快速入门示例
展示核心功能的基本使用方法
"""

import asyncio
import time
from datetime import datetime
from src.dashboard.debug import (
    DebugSession, EvidenceInfo, RetrievalStep,
    DebugWebSocketManager, PathAnalyzer,
    PerformanceMonitor, error_handler,
    monitor_performance, handle_errors
)

async def quick_start_example():
    """快速入门示例"""
    print("🚀 NecoRAG 调试面板快速入门示例")
    print("=" * 50)
    
    # 1. 创建调试会话
    print("\n📋 1. 创建调试会话")
    session = DebugSession(
        query="什么是人工智能的发展历程？",
        user_id="demo_user_001"
    )
    print(f"   会话ID: {session.session_id}")
    print(f"   查询内容: {session.query}")
    
    # 2. 模拟检索过程
    print("\n🔍 2. 模拟检索过程")
    
    # 预处理步骤
    preprocessing_step = RetrievalStep(
        name="查询预处理",
        description="分词和语义分析",
        input_data={"raw_query": session.query},
        metrics={"latency": 0.05}
    )
    preprocessing_step.complete(
        output_data={"processed_query": "人工智能 发展 历程"},
        metrics={"tokens": 3, "latency": 0.05}
    )
    session.add_retrieval_step(preprocessing_step)
    print(f"   ✓ 完成: {preprocessing_step.name}")
    
    # 向量检索步骤
    vector_step = RetrievalStep(
        name="向量检索",
        description="基于语义相似度的文档检索",
        input_data={"query_vector": "[0.1, 0.2, ...]"},
        metrics={"latency": 0.15}
    )
    vector_step.complete(
        output_data={
            "candidates": ["doc_001", "doc_002", "doc_003"],
            "scores": [0.92, 0.87, 0.85]
        },
        metrics={"candidates_found": 3, "latency": 0.15}
    )
    session.add_retrieval_step(vector_step)
    print(f"   ✓ 完成: {vector_step.name}")
    
    # 重排序步骤
    rerank_step = RetrievalStep(
        name="结果重排序",
        description="基于上下文的相关性重排序",
        input_data={"candidates": vector_step.output_data["candidates"]},
        metrics={"latency": 0.08}
    )
    rerank_step.complete(
        output_data={"ranked_docs": ["doc_001", "doc_003", "doc_002"]},
        metrics={"final_candidates": 3, "latency": 0.08}
    )
    session.add_retrieval_step(rerank_step)
    print(f"   ✓ 完成: {rerank_step.name}")
    
    # 3. 添加证据信息
    print("\n📄 3. 添加证据信息")
    
    evidences = [
        EvidenceInfo(
            source="vector",
            content="人工智能的发展可以追溯到1950年代...",
            relevance_score=0.92,
            metadata={
                "document_id": "doc_001",
                "chunk_index": 0,
                "source_type": "学术论文"
            }
        ),
        EvidenceInfo(
            source="keyword",
            content="机器学习作为AI的重要分支，在近年来快速发展...",
            relevance_score=0.85,
            metadata={
                "document_id": "doc_002", 
                "chunk_index": 1,
                "source_type": "技术文档"
            }
        ),
        EvidenceInfo(
            source="hybrid",
            content="深度学习的突破推动了AI技术的广泛应用...",
            relevance_score=0.78,
            metadata={
                "document_id": "doc_003",
                "chunk_index": 2, 
                "source_type": "新闻报道"
            }
        )
    ]
    
    for i, evidence in enumerate(evidences, 1):
        session.add_evidence(evidence)
        print(f"   ✓ 添加证据 {i}: 来源={evidence.source}, 相关度={evidence.relevance_score:.2f}")
    
    # 4. 路径分析
    print("\n📊 4. 路径分析")
    analyzer = PathAnalyzer()
    
    # 分析检索路径
    segments = analyzer.analyze_path(session)
    print(f"   检索步骤数: {len(segments)}")
    
    # 检测性能瓶颈
    bottlenecks = analyzer.detect_bottlenecks(segments)
    if bottlenecks:
        print(f"   发现瓶颈: {len(bottlenecks)} 个")
        for bottleneck in bottlenecks:
            print(f"     - {bottleneck.description}")
    else:
        print("   ✓ 未发现明显性能瓶颈")
    
    # 5. 性能监控演示
    print("\n⚡ 5. 性能监控")
    
    # 启动性能监控
    monitor = PerformanceMonitor(sample_interval=0.5)
    await monitor.start_monitoring()
    
    # 模拟一些操作
    @monitor_performance
    @handle_errors({"operation": "demo_processing"})
    async def demo_processing():
        await asyncio.sleep(0.2)
        if time.time() % 3 < 0.5:  # 偶尔模拟错误
            raise ValueError("模拟处理错误")
        return "处理完成"
    
    # 执行几次操作
    for i in range(3):
        try:
            result = await demo_processing()
            print(f"   操作 {i+1}: {result}")
        except Exception as e:
            print(f"   操作 {i+1}: 失败 ({e})")
        await asyncio.sleep(0.3)
    
    # 获取性能报告
    report = monitor.get_performance_report()
    if report['status'] != 'no_data':
        print(f"   CPU使用率: {report['cpu']['current']:.1f}%")
        print(f"   内存使用率: {report['memory']['current']:.1f}%")
    
    await monitor.stop_monitoring()
    
    # 6. 完成会话
    print("\n✅ 6. 完成会话")
    session.complete_session({
        "accuracy": 0.91,
        "confidence": 0.88,
        "user_satisfaction": 0.92
    })
    
    print(f"   会话状态: {session.status.name}")
    print(f"   总耗时: {session.total_duration:.2f}秒")
    print(f"   证据数量: {len(session.evidence)}")
    
    # 7. 会话摘要
    print("\n📋 7. 会话摘要")
    print(f"   查询: {session.query}")
    print(f"   时间: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   性能: 准确率={session.performance_metrics.get('accuracy', 0):.2f}")
    
    print("\n🎉 示例执行完成!")

async def advanced_example():
    """高级功能示例"""
    print("\n🔧 高级功能示例")
    print("=" * 30)
    
    # WebSocket连接演示
    print("\n🔌 WebSocket连接管理")
    ws_manager = DebugWebSocketManager()
    
    # 模拟WebSocket客户端
    class MockWebSocket:
        def __init__(self):
            self.messages = []
        async def send_json(self, data):
            self.messages.append(data)
            print(f"     ← 发送消息: {data.get('type', 'unknown')}")
        async def close(self):
            print("     ← 连接关闭")
    
    # 建立连接
    mock_ws = MockWebSocket()
    client_id = "advanced_demo_client"
    
    connected = await ws_manager.connect(mock_ws, client_id)
    if connected:
        print(f"   ✓ 客户端 {client_id} 连接成功")
        
        # 发送测试消息
        await ws_manager.send_message(client_id, {
            "type": "session_update",
            "session_id": "demo_session_123",
            "status": "active"
        })
        
        # 断开连接
        await ws_manager.disconnect(client_id)
        print(f"   ✓ 客户端 {client_id} 断开连接")
    
    # 错误处理演示
    print("\n🐛 错误处理机制")
    
    # 注册错误回调
    errors_caught = []
    async def error_callback(error_info):
        errors_caught.append(error_info)
        print(f"     ← 捕获错误: {error_info['error_type']}")
    
    error_handler.add_notification_callback(error_callback)
    
    # 触发不同类型错误
    test_errors = [
        ValueError("参数值无效"),
        TypeError("类型不匹配"),
        KeyError("键不存在")
    ]
    
    for error in test_errors:
        await error_handler.handle_error(error, {"context": "advanced_example"})
    
    print(f"   ✓ 共捕获 {len(errors_caught)} 个错误")
    
    # 清理回调
    error_handler.remove_notification_callback(error_callback)

def main():
    """主函数"""
    print("NecoRAG 调试面板演示程序")
    print("=" * 50)
    
    # 运行快速入门示例
    asyncio.run(quick_start_example())
    
    # 运行高级示例
    asyncio.run(advanced_example())
    
    print("\n" + "=" * 50)
    print("✨ 演示程序结束")
    print("现在您可以访问 http://localhost:8000 查看完整的Web界面")

if __name__ == "__main__":
    main()