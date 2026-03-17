# -*- coding: utf-8 -*-
"""
NecoRAG 模块导入测试
验证所有模块可以正确导入
"""

def test_imports():
    """测试所有模块导入"""
    print("测试 NecoRAG 模块导入...\n")
    
    # 测试主模块
    print("[OK] 导入 necorag")
    import necorag
    
    # 测试 Whiskers Engine
    print("[OK] 导入 necorag.whiskers")
    from necorag.whiskers import WhiskersEngine, DocumentParser, ChunkStrategy
    
    # 测试 Memory
    print("[OK] 导入 necorag.memory")
    from necorag.memory import MemoryManager, WorkingMemory, SemanticMemory
    
    # 测试 Retrieval
    print("[OK] 导入 necorag.retrieval")
    from necorag.retrieval import PounceRetriever, HyDEEnhancer, ReRanker
    
    # 测试 Grooming
    print("[OK] 导入 necorag.grooming")
    from necorag.grooming import GroomingAgent, Generator, Critic
    
    # 测试 Purr
    print("[OK] 导入 necorag.purr")
    from necorag.purr import PurrInterface, UserProfileManager
    
    print("\n" + "="*60)
    print("所有模块导入成功！")
    print("="*60)
    
    # 显示版本信息
    print(f"\nNecoRAG 版本: {necorag.__version__}")
    print(f"作者: {necorag.__author__}")


def test_basic_functionality():
    """测试基础功能"""
    print("\n测试基础功能...\n")
    
    from necorag import WhiskersEngine, MemoryManager
    
    # 测试 Whiskers Engine
    engine = WhiskersEngine()
    print("[OK] WhiskersEngine 初始化成功")
    
    # 测试 Memory Manager
    memory = MemoryManager()
    print("[OK] MemoryManager 初始化成功")
    
    print("\n基础功能测试通过！")


if __name__ == "__main__":
    test_imports()
    test_basic_functionality()
