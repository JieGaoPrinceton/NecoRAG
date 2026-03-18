#!/usr/bin/env python3
"""
NecoRAG 调试面板测试运行器
简化测试执行和结果展示
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """运行所有测试"""
    print("🔍 NecoRAG 调试面板测试套件")
    print("=" * 50)
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    test_dir = project_root / "src" / "dashboard" / "debug"
    
    # 测试文件列表
    test_files = [
        "test_comprehensive.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ 测试文件不存在: {test_file}")
            continue
            
        print(f"\n🏃 运行测试: {test_file}")
        print("-" * 30)
        
        try:
            # 运行测试文件
            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print("✅ 测试通过")
                results[test_file] = {"status": "PASS", "output": result.stdout}
            else:
                print("❌ 测试失败")
                results[test_file] = {"status": "FAIL", "output": result.stderr}
                
        except subprocess.TimeoutExpired:
            print("⏰ 测试超时")
            results[test_file] = {"status": "TIMEOUT", "output": ""}
        except Exception as e:
            print(f"💥 测试执行出错: {e}")
            results[test_file] = {"status": "ERROR", "output": str(e)}
    
    # 显示汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r["status"] == "PASS")
    failed = sum(1 for r in results.values() if r["status"] in ["FAIL", "TIMEOUT", "ERROR"])
    total = len(results)
    
    for test_file, result in results.items():
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌", 
            "TIMEOUT": "⏰",
            "ERROR": "💥"
        }.get(result["status"], "❓")
        
        print(f"{status_icon} {test_file}: {result['status']}")
    
    print(f"\n总计: {passed}/{total} 通过")
    if total > 0:
        print(f"通过率: {passed/total*100:.1f}%")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)