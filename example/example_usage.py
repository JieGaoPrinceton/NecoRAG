"""
NecoRAG 完整使用示例

演示如何使用 NecoRAG 框架的各个组件
"""

from src import PerceptionEngine, MemoryManager, AdaptiveRetriever, RefinementAgent, ResponseInterface
from src.perception.models import EncodedChunk
import numpy as np


def example_perception():
    """
    示例1：使用 Perception Engine 处理文档
    """
    print("=" * 60)
    print("示例1：Perception Engine - 文档解析与编码")
    print("=" * 60)
    
    # 初始化引擎
    engine = PerceptionEngine(
        model="BGE-M3",
        chunk_size=512,
        chunk_overlap=50
    )
    
    # 处理文本（实际使用时可传入文件路径）
    text = """
    深度学习是机器学习的一个分支，它使用多层神经网络来学习数据的表示。
    深度学习在图像识别、自然语言处理和语音识别等领域取得了巨大成功。
    常见的深度学习框架包括 TensorFlow、PyTorch 和 Keras。
    """
    
    # 编码文本
    encoded_chunks = engine.process_text(text)
    
    print(f"\n处理结果：生成 {len(encoded_chunks)} 个编码块\n")
    
    for i, chunk in enumerate(encoded_chunks[:2]):
        print(f"块 {i+1}:")
        print(f"  内容: {chunk.content[:100]}...")
        print(f"  向量维度: {chunk.dense_vector.shape}")
        print(f"  情境标签: {chunk.context_tags.sentiment_tag}")
        print(f"  重要性: {chunk.context_tags.importance_score:.2f}")
        print()
    
    return encoded_chunks


def example_memory(encoded_chunks):
    """
    示例2：使用 Memory Manager 存储和检索知识
    """
    print("=" * 60)
    print("示例2：Memory Manager - 知识存储与检索")
    print("=" * 60)
    
    # 初始化记忆管理器
    memory = MemoryManager()
    
    # 存储知识
    memory_ids = []
    for chunk in encoded_chunks:
        memory_id = memory.store(chunk)
        memory_ids.append(memory_id)
    
    print(f"\n存储完成，共 {len(memory_ids)} 条记忆\n")
    
    # 模拟查询向量
    query_vector = np.random.randn(1024).astype(np.float32)
    
    # 检索知识
    results = memory.retrieve(
        query="深度学习的应用",
        query_vector=query_vector,
        top_k=5
    )
    
    print(f"检索到 {len(results)} 条相关记忆\n")
    
    for i, result in enumerate(results[:3]):
        print(f"结果 {i+1}:")
        print(f"  内容: {result.content[:100]}...")
        print(f"  权重: {result.weight:.2f}")
        print()
    
    # 记忆巩固
    memory.consolidate()
    print("记忆巩固完成\n")
    
    return memory


def example_retrieval(memory):
    """
    示例3：使用 Adaptive Retriever 智能检索
    """
    print("=" * 60)
    print("示例3：Adaptive Retriever - 智能检索与重排序")
    print("=" * 60)
    
    # 初始化检索器
    retriever = AdaptiveRetriever(
        memory=memory,
        reranker_model="BGE-Reranker-v2",
        confidence_threshold=0.85,
        enable_hyde=True
    )
    
    # 执行检索
    query = "深度学习有哪些应用领域？"
    query_vector = np.random.randn(1024).astype(np.float32)
    
    results = retriever.retrieve(
        query=query,
        query_vector=query_vector,
        top_k=5
    )
    
    print(f"\n查询: {query}")
    print(f"检索到 {len(results)} 条结果\n")
    
    for i, result in enumerate(results[:3]):
        print(f"结果 {i+1}:")
        print(f"  内容: {result.content[:100]}...")
        print(f"  分数: {result.score:.3f}")
        print(f"  来源: {result.source}")
        print()
    
    # 查看检索路径
    print("检索路径追踪:")
    for step in retriever.get_retrieval_trace():
        print(f"  - {step}")
    print()
    
    return results


def example_refinement(evidence):
    """
    示例4：使用 Refinement Agent 生成和验证答案
    """
    print("=" * 60)
    print("示例4：Refinement Agent - 答案生成与幻觉检测")
    print("=" * 60)
    
    # 初始化精炼代理
    refinement = RefinementAgent(
        llm_model="default",
        memory=None,  # 示例中不需要 memory
        max_iterations=3
    )
    
    # 准备证据
    evidence_texts = [e.content for e in evidence[:3]]
    
    # 处理查询
    query = "深度学习有哪些应用领域？"
    result = refinement.process(query, evidence_texts)
    
    print(f"\n查询: {query}")
    print(f"\n答案:\n{result.answer}")
    print(f"\n置信度: {result.confidence:.2f}")
    print(f"迭代次数: {result.iterations}")
    print(f"引用数: {len(result.citations)}")
    
    if result.hallucination_report:
        print(f"\n幻觉检测:")
        print(f"  是否幻觉: {result.hallucination_report.is_hallucination}")
        print(f"  事实一致性: {result.hallucination_report.fact_score:.2f}")
        print(f"  证据支撑度: {result.hallucination_report.support_score:.2f}")
    
    return result


def example_response(refinement_result, memory):
    """
    示例5：使用 Response Interface 生成交互响应
    """
    print("=" * 60)
    print("示例5：Response Interface - 情境自适应交互")
    print("=" * 60)
    
    # 初始化交互接口
    interface = ResponseInterface(
        memory=memory,
        default_tone="friendly",
        default_detail_level=2
    )
    
    # 生成响应
    query = "深度学习有哪些应用领域？"
    response = interface.respond(
        query=query,
        refinement_result=refinement_result,
        session_id="user_123",
        tone="friendly",
        detail_level=2
    )
    
    print(f"\n查询: {query}")
    print(f"\n响应:\n{response.content}")
    print(f"\n语气: {response.tone}")
    print(f"详细程度: Level {response.detail_level}")
    
    print(f"\n思维链可视化:")
    print(response.thinking_chain)
    
    # 获取用户偏好
    preference = interface.get_user_preference("user_123")
    print(f"\n用户偏好分析:")
    print(f"  总查询数: {preference['total_queries']}")
    print(f"  交互风格: {preference['interaction_style']}")
    
    return response


def main():
    """
    主函数：演示完整的 NecoRAG 工作流程
    """
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         NecoRAG - 完整工作流程演示                      ║")
    print("║     Let's make AI think like a brain! 🧠               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # 1. 感知层：Perception Engine
    encoded_chunks = example_perception()
    
    # 2. 记忆层：Memory Manager
    memory = example_memory(encoded_chunks)
    
    # 3. 检索层：Adaptive Retriever
    retrieval_results = example_retrieval(memory)
    
    # 4. 巩固层：Refinement Agent
    refinement_result = example_refinement(retrieval_results)
    
    # 5. 交互层：Response Interface
    response = example_response(refinement_result, memory)
    
    print("\n" + "=" * 60)
    print("演示完成！NecoRAG 各模块协同工作示例结束")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
