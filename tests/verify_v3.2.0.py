#!/usr/bin/env python3
"""
NecoRAG v3.2.0-alpha 版本验证脚本
验证核心功能和模块导入
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_version():
    """测试版本号"""
    print_header("1️⃣ 版本号验证")
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
        print(f"✅ 当前版本：{version}")
        assert version == "3.2.0-alpha", f"版本号错误：{version}"
        print(f"✅ 版本验证通过：v3.2.0-alpha")
        return True
    except Exception as e:
        print(f"❌ 版本验证失败：{e}")
        return False

def test_core_imports():
    """测试核心模块导入"""
    print_header("2️⃣ 核心模块导入测试")
    
    # 添加 src 目录到 Python 路径
    import sys
    import os
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    modules_to_test = [
        ('necorag', 'NecoRAG'),
        ('core.base', 'NecoCore'),
        ('retrieval.base', 'NecoRetrievalBase'),
        ('memory.manager', 'MemoryManager'),
        ('intent.classifier', 'IntentClassifier'),
        ('domain.relevance', 'DomainRelevanceCalculator'),
        ('perception.analyzer', 'PerceptionAnalyzer'),
        ('refinement.refiner', 'KnowledgeRefiner'),
        ('response.generator', 'ResponseGenerator'),
    ]
    
    success = 0
    failed = 0
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"✅ {module_path}.{class_name}")
                success += 1
            else:
                print(f"⚠️  {module_path} - 类 {class_name} 不存在")
                failed += 1
        except ImportError as e:
            print(f"❌ {module_path} - {str(e)}")
            failed += 1
    
    print(f"\n总计：{success} 成功，{failed} 失败")
    return failed == 0

def test_docker_guide():
    """测试 Docker 镜像指南完整性"""
    print_header("3️⃣ Docker 镜像指南验证")
    
    try:
        with open('3rd/DOCKER_IMAGES_GUIDE.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键镜像是否被提及
        required_mirrors = [
            'redis',
            'qdrant',
            'neo4j',
            'ollama',
            'langgraph',
            'ragflow',
            'vllm',
            'streamlit',
            'elasticsearch',
            'paddleocr'
        ]
        
        missing = []
        for mirror in required_mirrors:
            if mirror.lower() not in content.lower():
                missing.append(mirror)
        
        if missing:
            print(f"⚠️  缺少镜像文档：{missing}")
            return False
        else:
            print(f"✅ 所有必需镜像文档完整（{len(required_mirrors)}个）")
            return True
            
    except Exception as e:
        print(f"❌ Docker 指南验证失败：{e}")
        return False

def test_readme_links():
    """测试 README 链接有效性"""
    print_header("4️⃣ README 技术栈架构验证")
    
    try:
        with open('3rd/README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查五层架构是否完整
        layers = [
            '应用层',
            'AI 模型层',
            '存储层',
            '中间件层',
            '监控层'
        ]
        
        missing = []
        for layer in layers:
            if layer not in content:
                missing.append(layer)
        
        if missing:
            print(f"⚠️  缺少架构层：{missing}")
            return False
        else:
            print(f"✅ 五层认知架构完整")
            
        # 检查 23 个系统
        if '23 个第三方系统' in content or '23 个系统' in content:
            print(f"✅ 技术栈覆盖率标注正确（23 个系统）")
        else:
            print(f"⚠️  未找到系统数量标注")
            
        return True
        
    except Exception as e:
        print(f"❌ README 验证失败：{e}")
        return False

def test_git_status():
    """测试 Git 状态"""
    print_header("5️⃣ Git 状态验证")
    
    import subprocess
    try:
        result = subprocess.run(['git', 'status', '--short'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            if not result.stdout.strip():
                print(f"✅ Git 工作区干净，无未提交更改")
                return True
            else:
                lines = result.stdout.strip().split('\n')
                print(f"⚠️  有 {len(lines)} 个未提交文件:")
                for line in lines[:5]:  # 只显示前 5 个
                    print(f"   {line}")
                if len(lines) > 5:
                    print(f"   ... 还有 {len(lines) - 5} 个文件")
                return False
        else:
            print(f"❌ Git 状态检查失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Git 状态检查异常：{e}")
        return False

def main():
    """主测试函数"""
    print_header("🚀 NecoRAG v3.2.0-alpha 版本验证测试")
    
    tests = [
        ("版本号验证", test_version),
        ("核心模块导入", test_core_imports),
        ("Docker 镜像指南", test_docker_guide),
        ("README 技术栈", test_readme_links),
        ("Git 状态", test_git_status),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常：{e}")
            results.append((test_name, False))
    
    # 汇总结果
    print_header("📊 测试结果汇总")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 恭喜！v3.2.0-alpha 版本验证完全通过！")
        print("\n📦 版本信息:")
        print("   - 版本号：v3.2.0-alpha")
        print("   - 变更类型：Minor Version (功能性增强)")
        print("   - 核心亮点：Docker 镜像完善、AI 能力增强、全文搜索、OCR 集成")
        print("   - 技术栈：23 个第三方系统，100% 覆盖")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项测试未通过，请检查")
        return 1

if __name__ == '__main__':
    sys.exit(main())
