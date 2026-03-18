"""
NecoRAG 调试面板实战应用示例
展示如何在实际项目中集成和使用调试面板
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any
import json

# 假设这是您的NecoRAG检索系统
class NecoRAGRetriever:
    """模拟的NecoRAG检索系统"""
    
    def __init__(self):
        self.debug_enabled = True
        
    async def search(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """执行检索操作"""
        # 在实际应用中，这里会集成真实的调试面板
        if self.debug_enabled:
            # 创建调试会话
            from src.dashboard.debug import DebugSession, EvidenceInfo, RetrievalStep
            
            session = DebugSession(query=query, user_id=user_id or str(uuid.uuid4()))
            print(f"🔍 创建调试会话: {session.session_id}")
            
            try:
                # 1. 查询预处理
                print("   → 执行查询预处理...")
                preprocess_step = RetrievalStep(
                    name="查询预处理",
                    description="分词、语义分析和查询扩展"
                )
                await asyncio.sleep(0.1)  # 模拟处理时间
                
                preprocess_step.complete(
                    output_data={
                        "processed_query": self._preprocess_query(query),
                        "tokens": ["人工智能", "发展", "历程"],
                        "intent": "informational"
                    },
                    metrics={"latency": 0.1, "tokens_processed": 3}
                )
                session.add_retrieval_step(preprocess_step)
                
                # 2. 向量检索
                print("   → 执行向量检索...")
                vector_step = RetrievalStep(
                    name="向量检索",
                    description="基于语义相似度的文档检索"
                )
                await asyncio.sleep(0.2)
                
                candidates = self._vector_search(preprocess_step.output_data["processed_query"])
                vector_step.complete(
                    output_data={
                        "candidates": [c["id"] for c in candidates],
                        "scores": [c["score"] for c in candidates],
                        "vectors_compared": 1000
                    },
                    metrics={"latency": 0.2, "candidates_found": len(candidates)}
                )
                session.add_retrieval_step(vector_step)
                
                # 3. 关键词检索
                print("   → 执行关键词检索...")
                keyword_step = RetrievalStep(
                    name="关键词检索",
                    description="基于BM25算法的精确匹配"
                )
                await asyncio.sleep(0.15)
                
                keyword_results = self._keyword_search(query)
                keyword_step.complete(
                    output_data={
                        "matches": [m["id"] for m in keyword_results],
                        "scores": [m["score"] for m in keyword_results]
                    },
                    metrics={"latency": 0.15, "exact_matches": len(keyword_results)}
                )
                session.add_retrieval_step(keyword_step)
                
                # 4. 结果融合
                print("   → 执行结果融合...")
                fusion_step = RetrievalStep(
                    name="结果融合",
                    description="混合检索结果的权重融合"
                )
                await asyncio.sleep(0.1)
                
                fused_results = self._fuse_results(
                    vector_results=candidates,
                    keyword_results=keyword_results
                )
                fusion_step.complete(
                    output_data={
                        "final_ranking": [r["id"] for r in fused_results[:5]],
                        "confidence_scores": [r["confidence"] for r in fused_results[:5]]
                    },
                    metrics={"latency": 0.1, "final_candidates": len(fused_results)}
                )
                session.add_retrieval_step(fusion_step)
                
                # 5. 添加证据信息
                print("   → 收集证据信息...")
                for i, result in enumerate(fused_results[:3]):
                    evidence = EvidenceInfo(
                        source=result["source"],
                        content=result["content"],
                        relevance_score=result["confidence"],
                        metadata={
                            "document_id": result["id"],
                            "chunk_index": result.get("chunk", 0),
                            "source_type": result.get("type", "unknown")
                        }
                    )
                    session.add_evidence(evidence)
                
                # 6. 完成会话
                session.complete_session({
                    "accuracy": 0.92,
                    "confidence": 0.88,
                    "user_satisfaction": 0.91,
                    "total_latency": session.total_duration
                })
                
                print(f"   ✅ 检索完成，会话ID: {session.session_id}")
                print(f"   📊 总耗时: {session.total_duration:.2f}秒")
                print(f"   🎯 返回结果: {len(fused_results)}个")
                
                return {
                    "results": fused_results[:5],
                    "session_id": session.session_id,
                    "debug_info": {
                        "total_steps": len(session.retrieval_steps),
                        "evidence_count": len(session.evidence),
                        "performance": session.performance_metrics
                    }
                }
                
            except Exception as e:
                # 标记会话失败
                session.fail_session(str(e))
                print(f"   ❌ 检索失败: {e}")
                raise
                
        else:
            # 非调试模式的简单实现
            return await self._simple_search(query)
    
    def _preprocess_query(self, query: str) -> str:
        """查询预处理"""
        # 简化的预处理逻辑
        return query.lower().strip()
    
    def _vector_search(self, processed_query: str) -> List[Dict]:
        """向量检索模拟"""
        return [
            {"id": "doc_001", "score": 0.92, "content": "人工智能的发展历程可以追溯到1950年代..."},
            {"id": "doc_002", "score": 0.87, "content": "机器学习作为AI的重要分支，在近年来快速发展..."},
            {"id": "doc_003", "score": 0.85, "content": "深度学习技术的突破为AI应用带来了革命性变化..."}
        ]
    
    def _keyword_search(self, query: str) -> List[Dict]:
        """关键词检索模拟"""
        return [
            {"id": "doc_004", "score": 0.95, "content": "人工智能简史：从图灵测试到现代AI"},
            {"id": "doc_005", "score": 0.88, "content": "AI发展的关键里程碑和技术突破"}
        ]
    
    def _fuse_results(self, vector_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """结果融合"""
        # 简单的融合策略
        all_results = {}
        
        # 处理向量检索结果
        for result in vector_results:
            all_results[result["id"]] = {
                "id": result["id"],
                "content": result["content"],
                "confidence": result["score"] * 0.7,  # 权重0.7
                "source": "vector"
            }
        
        # 处理关键词检索结果
        for result in keyword_results:
            if result["id"] in all_results:
                all_results[result["id"]]["confidence"] += result["score"] * 0.3  # 权重0.3
            else:
                all_results[result["id"]] = {
                    "id": result["id"],
                    "content": result["content"],
                    "confidence": result["score"] * 0.3,
                    "source": "keyword"
                }
        
        # 按置信度排序
        return sorted(all_results.values(), key=lambda x: x["confidence"], reverse=True)
    
    async def _simple_search(self, query: str) -> Dict:
        """非调试模式的简单搜索"""
        await asyncio.sleep(0.3)
        return {
            "results": [
                {"id": "simple_001", "content": "简单搜索结果1"},
                {"id": "simple_002", "content": "简单搜索结果2"}
            ]
        }

class ProductionDebugger:
    """生产环境调试工具"""
    
    def __init__(self):
        self.enabled = False
        self.sample_rate = 0.1  # 10%的采样率
        
    def should_debug(self, user_id: str = None) -> bool:
        """决定是否启用调试"""
        if not self.enabled:
            return False
            
        # 基于用户ID或随机采样决定
        if user_id:
            # 基于用户ID的哈希值决定
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
            return (hash_val % 100) < (self.sample_rate * 100)
        else:
            # 随机采样
            return hash(str(time.time())) % 100 < (self.sample_rate * 100)
    
    async def debug_search(self, retriever: NecoRAGRetriever, query: str, user_id: str = None):
        """带调试的搜索"""
        original_debug_state = retriever.debug_enabled
        
        try:
            # 根据策略决定是否启用调试
            retriever.debug_enabled = self.should_debug(user_id)
            
            result = await retriever.search(query, user_id)
            
            if retriever.debug_enabled:
                print(f"🎯 调试会话已完成: {result.get('session_id', 'N/A')}")
            
            return result
            
        finally:
            # 恢复原始状态
            retriever.debug_enabled = original_debug_state

async def batch_processing_example():
    """批处理示例"""
    print("📦 批处理检索示例")
    print("=" * 40)
    
    retriever = NecoRAGRetriever()
    debugger = ProductionDebugger()
    debugger.enabled = True
    debugger.sample_rate = 1.0  # 100%采样用于演示
    
    queries = [
        "人工智能的发展历程",
        "机器学习算法有哪些类型",
        "深度学习的应用场景",
        "自然语言处理的挑战",
        "计算机视觉技术现状"
    ]
    
    results = []
    start_time = time.time()
    
    for i, query in enumerate(queries, 1):
        print(f"\n📝 处理查询 {i}/{len(queries)}: {query}")
        try:
            result = await debugger.debug_search(retriever, query, f"user_{i}")
            results.append({
                "query": query,
                "result_count": len(result["results"]),
                "session_id": result.get("session_id"),
                "latency": result.get("debug_info", {}).get("performance", {}).get("total_latency", 0)
            })
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
            results.append({"query": query, "error": str(e)})
    
    total_time = time.time() - start_time
    
    print(f"\n📊 批处理统计:")
    print(f"   总查询数: {len(queries)}")
    print(f"   成功处理: {len([r for r in results if 'error' not in r])}")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   平均响应时间: {total_time/len(queries):.2f}秒")
    
    # 显示详细结果
    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        if "error" in result:
            print(f"   {i}. {result['query']} - ❌ {result['error']}")
        else:
            print(f"   {i}. {result['query']} - ✅ {result['result_count']}结果 "
                  f"(会话:{result['session_id'][:8]}..., 耗时:{result['latency']:.2f}s)")

async def performance_comparison_example():
    """性能对比示例"""
    print("\n⚡ 性能对比示例")
    print("=" * 40)
    
    retriever = NecoRAGRetriever()
    
    # 调试模式测试
    print("🔬 调试模式测试:")
    retriever.debug_enabled = True
    debug_start = time.time()
    debug_result = await retriever.search("性能测试查询", "perf_test_user")
    debug_time = time.time() - debug_start
    
    print(f"   调试模式耗时: {debug_time:.3f}秒")
    print(f"   会话ID: {debug_result['session_id']}")
    print(f"   检索步骤: {debug_result['debug_info']['total_steps']}步")
    print(f"   证据数量: {debug_result['debug_info']['evidence_count']}个")
    
    # 非调试模式测试
    print("\n🚀 非调试模式测试:")
    retriever.debug_enabled = False
    normal_start = time.time()
    normal_result = await retriever.search("性能测试查询", "perf_test_user")
    normal_time = time.time() - normal_start
    
    print(f"   正常模式耗时: {normal_time:.3f}秒")
    print(f"   性能开销: {((debug_time - normal_time) / normal_time * 100):.1f}%")

def configuration_example():
    """配置示例"""
    print("\n⚙️  配置管理示例")
    print("=" * 40)
    
    # 调试配置
    debug_config = {
        "enabled": True,
        "sample_rate": 0.1,  # 10%采样
        "log_level": "INFO",
        "storage_ttl": "7d",  # 7天过期
        "max_sessions": 1000,
        "websocket_enabled": True
    }
    
    # 生产配置
    production_config = {
        "enabled": True,
        "sample_rate": 0.01,  # 1%采样
        "log_level": "WARNING",
        "storage_ttl": "30d",  # 30天过期
        "max_sessions": 10000,
        "websocket_enabled": False  # 生产环境通常关闭WebSocket
    }
    
    print("开发环境配置:")
    print(json.dumps(debug_config, indent=2, ensure_ascii=False))
    
    print("\n生产环境配置:")
    print(json.dumps(production_config, indent=2, ensure_ascii=False))

async def main():
    """主函数"""
    print("🤖 NecoRAG 调试面板实战应用示例")
    print("=" * 50)
    
    # 运行各个示例
    await batch_processing_example()
    await performance_comparison_example()
    configuration_example()
    
    print("\n" + "=" * 50)
    print("✨ 所有示例执行完成!")
    print("💡 提示: 访问 http://localhost:8001 查看调试面板界面")

if __name__ == "__main__":
    asyncio.run(main())