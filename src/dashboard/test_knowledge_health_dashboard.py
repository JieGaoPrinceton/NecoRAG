"""
知识库健康仪表盘测试脚本

测试 Dashboard 组件的功能完整性
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_dashboard_file_exists():
    """测试仪表盘文件是否存在"""
    dashboard_file = Path(__file__).parent / "components" / "KnowledgeHealthDashboard.html"
    
    print(f"📄 检查仪表盘文件...")
    print(f"   路径：{dashboard_file.absolute()}")
    
    if dashboard_file.exists():
        print(f"   ✅ 文件存在")
        size = dashboard_file.stat().st_size
        print(f"   📊 文件大小：{size:,} 字节 ({size/1024:.2f} KB)")
        return True
    else:
        print(f"   ❌ 文件不存在")
        return False


def test_guide_file_exists():
    """测试使用指南文档是否存在"""
    guide_file = Path(__file__).parent / "KNOWLEDGE_HEALTH_DASHBOARD_GUIDE.md"
    
    print(f"\n📚 检查使用指南文档...")
    print(f"   路径：{guide_file.absolute()}")
    
    if guide_file.exists():
        print(f"   ✅ 文档存在")
        size = guide_file.stat().st_size
        print(f"   📊 文档大小：{size:,} 字节 ({size/1024:.2f} KB)")
        return True
    else:
        print(f"   ❌ 文档不存在")
        return False


def test_html_structure():
    """测试 HTML 结构完整性"""
    dashboard_file = Path(__file__).parent / "components" / "KnowledgeHealthDashboard.html"
    
    print(f"\n🔍 检查 HTML 结构...")
    
    if not dashboard_file.exists():
        print(f"   ❌ 文件不存在，跳过测试")
        return False
    
    content = dashboard_file.read_text(encoding='utf-8')
    
    # 检查必要的 HTML 标签
    required_tags = [
        '<!DOCTYPE html>',
        '<html',
        '<head>',
        '</head>',
        '<body>',
        '</body>',
        '</html>'
    ]
    
    all_present = True
    for tag in required_tags:
        if tag.lower() in content.lower():
            print(f"   ✅ 包含 {tag}")
        else:
            print(f"   ❌ 缺少 {tag}")
            all_present = False
    
    # 检查关键组件
    components = [
        'class="dashboard-container"',
        'class="header"',
        'class="metrics-cards"',
        'health-gauge-card',
        'growth-chart-card',
        'domain-heatmap-card',
        'radar-chart-card',
        'timeline-card'
    ]
    
    print(f"\n🧩 检查核心组件...")
    for component in components:
        if component in content:
            # 提取组件名称
            if '=' in component:
                name = component.split('=')[1].strip('"')
            else:
                name = component
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ 缺少 {component}")
            all_present = False
    
    # 检查 CSS 变量
    css_vars = [
        '--primary-blue',
        '--success-green',
        '--warning-yellow',
        '--danger-red'
    ]
    
    print(f"\n🎨 检查 CSS 样式...")
    for css_var in css_vars:
        if css_var in content:
            print(f"   ✅ {css_var}")
        else:
            print(f"   ❌ 缺少 {css_var}")
    
    # 检查 JavaScript 函数
    js_functions = [
        'loadDashboardData',
        'updateMetricsCards',
        'updateHealthGauge',
        'updateGrowthChart',
        'updateDomainHeatmap',
        'updateRadarChart',
        'updateTimeline'
    ]
    
    print(f"\n⚙️ 检查 JavaScript 功能...")
    for func in js_functions:
        if f'function {func}' in content or f'{func} =' in content:
            print(f"   ✅ {func}()")
        else:
            print(f"   ❌ 缺少 {func}()")
    
    return all_present


def test_api_endpoints():
    """测试 API 端点配置"""
    server_file = Path(__file__).parent / "server.py"
    
    print(f"\n🔌 检查 API 端点...")
    
    if not server_file.exists():
        print(f"   ❌ server.py 不存在")
        return False
    
    content = server_file.read_text(encoding='utf-8')
    
    # 检查路由
    routes = [
        'get_knowledge_health_dashboard',
        'KnowledgeHealthDashboard.html'
    ]
    
    all_configured = True
    for route in routes:
        if route in content:
            print(f"   ✅ 配置：{route}")
        else:
            print(f"   ❌ 未配置：{route}")
            all_configured = False
    
    # 检查知识演化 API（在 server.py 中）
    knowledge_apis = [
        'get_knowledge_metrics',
        'get_knowledge_health',
        'get_knowledge_dashboard'
    ]
    
    print(f"\n📡 检查知识库 API...")
    for api in knowledge_apis:
        if api in content:
            print(f"   ✅ {api}")
        else:
            print(f"   ❌ 缺少 {api}")
            all_configured = False
    
    return all_configured


def test_responsive_design():
    """测试响应式设计支持"""
    dashboard_file = Path(__file__).parent / "components" / "KnowledgeHealthDashboard.html"
    
    print(f"\n📱 检查响应式设计...")
    
    if not dashboard_file.exists():
        return False
    
    content = dashboard_file.read_text(encoding='utf-8')
    
    # 检查媒体查询
    media_queries = [
        '@media (max-width: 1200px)',
        '@media (max-width: 768px)'
    ]
    
    for mq in media_queries:
        if mq in content:
            print(f"   ✅ 平板/移动端适配：{mq}")
        else:
            print(f"   ⚠️  缺少 {mq}")
    
    # 检查网格布局
    if 'display: grid' in content and 'grid-template-columns' in content:
        print(f"   ✅ CSS Grid 布局")
    else:
        print(f"   ⚠️  未使用 CSS Grid")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("  知识库健康仪表盘 - 功能完整性测试")
    print("=" * 70)
    
    results = []
    
    # 运行各项测试
    results.append(("文件存在性", test_dashboard_file_exists()))
    results.append(("使用指南", test_guide_file_exists()))
    results.append(("HTML 结构", test_html_structure()))
    results.append(("API 端点", test_api_endpoints()))
    results.append(("响应式设计", test_responsive_design()))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print("-" * 70)
    print(f"总计：{passed}/{total} 项测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！仪表盘已准备就绪。")
        print("\n📌 使用方法:")
        print("   1. 启动 Dashboard: python src/dashboard/dashboard.py")
        print("   2. 访问仪表盘：http://localhost:8000/knowledge-health")
    else:
        print(f"\n⚠️  有 {total - passed} 项测试未通过，请检查配置。")
    
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
