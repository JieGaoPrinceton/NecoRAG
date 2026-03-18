/**
 * NecoRAG 响应式设计工具库
 * 提供响应式布局、设备检测和UI适配功能
 */

class ResponsiveManager {
    constructor() {
        this.breakpoints = {
            xs: 0,
            sm: 640,
            md: 768,
            lg: 1024,
            xl: 1280,
            xxl: 1536
        };
        
        this.currentBreakpoint = this.getCurrentBreakpoint();
        this.listeners = [];
        this.resizeObserver = null;
        
        this.init();
    }
    
    init() {
        // 监听窗口大小变化
        window.addEventListener('resize', this.handleResize.bind(this));
        
        // 初始化当前断点
        this.updateBreakpoint();
        
        // 创建 ResizeObserver 监听容器变化
        if (window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(this.handleResize.bind(this));
        }
    }
    
    getCurrentBreakpoint() {
        const width = window.innerWidth;
        
        if (width >= this.breakpoints.xxl) return 'xxl';
        if (width >= this.breakpoints.xl) return 'xl';
        if (width >= this.breakpoints.lg) return 'lg';
        if (width >= this.breakpoints.md) return 'md';
        if (width >= this.breakpoints.sm) return 'sm';
        return 'xs';
    }
    
    updateBreakpoint() {
        const newBreakpoint = this.getCurrentBreakpoint();
        
        if (newBreakpoint !== this.currentBreakpoint) {
            const oldBreakpoint = this.currentBreakpoint;
            this.currentBreakpoint = newBreakpoint;
            
            // 触发断点变化事件
            this.triggerBreakpointChange(oldBreakpoint, newBreakpoint);
        }
    }
    
    handleResize() {
        this.updateBreakpoint();
    }
    
    onBreakpointChange(callback) {
        this.listeners.push(callback);
    }
    
    triggerBreakpointChange(oldBreakpoint, newBreakpoint) {
        const event = {
            oldBreakpoint,
            newBreakpoint,
            timestamp: Date.now()
        };
        
        this.listeners.forEach(callback => {
            try {
                callback(event);
            } catch (error) {
                console.error('断点变化监听器执行失败:', error);
            }
        });
    }
    
    isMobile() {
        return this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm';
    }
    
    isTablet() {
        return this.currentBreakpoint === 'md';
    }
    
    isDesktop() {
        return this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl' || this.currentBreakpoint === 'xxl';
    }
    
    getBreakpoint() {
        return this.currentBreakpoint;
    }
    
    getBreakpointWidth(breakpoint) {
        return this.breakpoints[breakpoint] || 0;
    }
    
    observeElement(element) {
        if (this.resizeObserver && element) {
            this.resizeObserver.observe(element);
        }
    }
    
    unobserveElement(element) {
        if (this.resizeObserver && element) {
            this.resizeObserver.unobserve(element);
        }
    }
    
    destroy() {
        window.removeEventListener('resize', this.handleResize.bind(this));
        
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
        
        this.listeners = [];
    }
}

class ThemeManager {
    constructor() {
        this.themes = {
            light: 'light',
            dark: 'dark',
            auto: 'auto'
        };
        
        this.currentTheme = this.getStoredTheme() || 'auto';
        this.systemTheme = this.getSystemTheme();
        
        this.init();
    }
    
    init() {
        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', this.handleSystemThemeChange.bind(this));
        }
        
        // 应用当前主题
        this.applyTheme();
    }
    
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }
    
    handleSystemThemeChange(event) {
        this.systemTheme = event.matches ? 'dark' : 'light';
        
        if (this.currentTheme === 'auto') {
            this.applyTheme();
        }
    }
    
    getStoredTheme() {
        try {
            return localStorage.getItem('nc-theme');
        } catch (error) {
            console.warn('无法读取主题设置:', error);
            return null;
        }
    }
    
    storeTheme(theme) {
        try {
            localStorage.setItem('nc-theme', theme);
        } catch (error) {
            console.warn('无法保存主题设置:', error);
        }
    }
    
    setTheme(theme) {
        if (Object.values(this.themes).includes(theme)) {
            this.currentTheme = theme;
            this.storeTheme(theme);
            this.applyTheme();
        }
    }
    
    applyTheme() {
        const themeToApply = this.currentTheme === 'auto' ? this.systemTheme : this.currentTheme;
        const root = document.documentElement;
        
        // 移除所有主题类
        root.classList.remove('theme-light', 'theme-dark');
        
        // 应用新主题
        root.classList.add(`theme-${themeToApply}`);
        
        // 触发自定义事件
        const event = new CustomEvent('themechange', {
            detail: {
                theme: themeToApply,
                previousTheme: this.getPreviousTheme()
            }
        });
        document.dispatchEvent(event);
    }
    
    getPreviousTheme() {
        const root = document.documentElement;
        if (root.classList.contains('theme-light')) return 'light';
        if (root.classList.contains('theme-dark')) return 'dark';
        return 'light';
    }
    
    getCurrentTheme() {
        return this.currentTheme === 'auto' ? this.systemTheme : this.currentTheme;
    }
    
    toggleTheme() {
        const current = this.getCurrentTheme();
        const newTheme = current === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }
    
    destroy() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.removeEventListener('change', this.handleSystemThemeChange.bind(this));
        }
    }
}

class LayoutManager {
    constructor() {
        this.sidebar = null;
        this.mainContent = null;
        this.header = null;
        this.footer = null;
        
        this.isSidebarCollapsed = false;
        this.isMobileMenuOpen = false;
        
        this.init();
    }
    
    init() {
        this.detectLayoutElements();
        this.setupResponsiveBehavior();
        this.setupEventListeners();
    }
    
    detectLayoutElements() {
        this.sidebar = document.querySelector('.nc-sidebar');
        this.mainContent = document.querySelector('.nc-main-content');
        this.header = document.querySelector('.nc-header');
        this.footer = document.querySelector('.nc-footer');
    }
    
    setupResponsiveBehavior() {
        responsiveManager.onBreakpointChange(this.handleBreakpointChange.bind(this));
        
        // 初始布局调整
        this.adjustLayoutForBreakpoint(responsiveManager.getBreakpoint());
    }
    
    setupEventListeners() {
        // 侧边栏切换按钮
        const sidebarToggle = document.querySelector('[data-toggle="sidebar"]');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
        }
        
        // 移动端菜单按钮
        const mobileMenuToggle = document.querySelector('[data-toggle="mobile-menu"]');
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', this.toggleMobileMenu.bind(this));
        }
        
        // 点击外部关闭移动端菜单
        document.addEventListener('click', this.handleDocumentClick.bind(this));
    }
    
    handleBreakpointChange(event) {
        this.adjustLayoutForBreakpoint(event.newBreakpoint);
    }
    
    adjustLayoutForBreakpoint(breakpoint) {
        if (responsiveManager.isMobile()) {
            this.handleMobileLayout();
        } else if (responsiveManager.isTablet()) {
            this.handleTabletLayout();
        } else {
            this.handleDesktopLayout();
        }
    }
    
    handleMobileLayout() {
        // 移动端布局：隐藏侧边栏，显示汉堡菜单
        if (this.sidebar) {
            this.sidebar.classList.add('nc-sidebar-mobile');
            this.sidebar.classList.remove('nc-sidebar-expanded');
        }
        
        if (this.mainContent) {
            this.mainContent.classList.add('nc-main-content-full');
        }
        
        // 关闭侧边栏
        this.isSidebarCollapsed = true;
    }
    
    handleTabletLayout() {
        // 平板布局：可折叠侧边栏
        if (this.sidebar) {
            this.sidebar.classList.remove('nc-sidebar-mobile');
            this.sidebar.classList.remove('nc-sidebar-expanded');
        }
        
        if (this.mainContent) {
            this.mainContent.classList.remove('nc-main-content-full');
        }
    }
    
    handleDesktopLayout() {
        // 桌面布局：展开侧边栏
        if (this.sidebar) {
            this.sidebar.classList.remove('nc-sidebar-mobile');
            this.sidebar.classList.add('nc-sidebar-expanded');
        }
        
        if (this.mainContent) {
            this.mainContent.classList.remove('nc-main-content-full');
        }
        
        this.isSidebarCollapsed = false;
    }
    
    toggleSidebar() {
        if (!this.sidebar) return;
        
        this.isSidebarCollapsed = !this.isSidebarCollapsed;
        
        if (this.isSidebarCollapsed) {
            this.sidebar.classList.remove('nc-sidebar-expanded');
        } else {
            this.sidebar.classList.add('nc-sidebar-expanded');
        }
        
        // 触发自定义事件
        const event = new CustomEvent('sidebartoggle', {
            detail: {
                collapsed: this.isSidebarCollapsed
            }
        });
        document.dispatchEvent(event);
    }
    
    toggleMobileMenu() {
        this.isMobileMenuOpen = !this.isMobileMenuOpen;
        
        if (this.sidebar) {
            if (this.isMobileMenuOpen) {
                this.sidebar.classList.add('nc-sidebar-mobile-open');
            } else {
                this.sidebar.classList.remove('nc-sidebar-mobile-open');
            }
        }
        
        // 防止背景滚动
        document.body.style.overflow = this.isMobileMenuOpen ? 'hidden' : '';
    }
    
    handleDocumentClick(event) {
        // 点击侧边栏外部时关闭移动端菜单
        if (this.isMobileMenuOpen && 
            this.sidebar && 
            !this.sidebar.contains(event.target) &&
            !event.target.closest('[data-toggle="mobile-menu"]')) {
            this.toggleMobileMenu();
        }
    }
    
    destroy() {
        document.removeEventListener('click', this.handleDocumentClick.bind(this));
    }
}

class ComponentManager {
    constructor() {
        this.components = new Map();
        this.intersectionObserver = null;
        this.mutationObserver = null;
        
        this.init();
    }
    
    init() {
        // 创建 Intersection Observer 用于懒加载
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver(
                this.handleIntersection.bind(this),
                {
                    rootMargin: '50px',
                    threshold: 0.1
                }
            );
        }
        
        // 创建 Mutation Observer 监听 DOM 变化
        this.mutationObserver = new MutationObserver(this.handleMutations.bind(this));
        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        // 初始化现有组件
        this.scanAndInitializeComponents();
    }
    
    scanAndInitializeComponents() {
        // 扫描并初始化所有带有 nc-component 属性的元素
        const componentElements = document.querySelectorAll('[nc-component]');
        
        componentElements.forEach(element => {
            this.initializeComponent(element);
        });
    }
    
    initializeComponent(element) {
        const componentName = element.getAttribute('nc-component');
        const componentId = element.id || `comp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        if (this.components.has(componentId)) {
            console.warn(`组件 ${componentId} 已存在`);
            return;
        }
        
        // 创建组件实例
        const component = {
            id: componentId,
            name: componentName,
            element: element,
            initialized: false,
            observers: []
        };
        
        // 根据组件类型进行特定初始化
        this.setupComponentType(component);
        
        // 开始观察组件可见性
        if (this.intersectionObserver) {
            this.intersectionObserver.observe(element);
        }
        
        this.components.set(componentId, component);
    }
    
    setupComponentType(component) {
        switch (component.name) {
            case 'chart':
                this.setupChartComponent(component);
                break;
            case 'table':
                this.setupTableComponent(component);
                break;
            case 'form':
                this.setupFormComponent(component);
                break;
            case 'card':
                this.setupCardComponent(component);
                break;
            default:
                this.setupGenericComponent(component);
        }
    }
    
    setupChartComponent(component) {
        // 图表组件特定设置
        component.type = 'chart';
        component.resizeHandler = this.debounce(() => {
            // 重新渲染图表
            if (component.chartInstance) {
                component.chartInstance.resize();
            }
        }, 250);
        
        window.addEventListener('resize', component.resizeHandler);
        component.observers.push(() => {
            window.removeEventListener('resize', component.resizeHandler);
        });
    }
    
    setupTableComponent(component) {
        // 表格组件特定设置
        component.type = 'table';
        component.virtualScroll = this.enableVirtualScroll(component.element);
    }
    
    setupFormComponent(component) {
        // 表单组件特定设置
        component.type = 'form';
        component.validator = this.setupFormValidation(component.element);
    }
    
    setupCardComponent(component) {
        // 卡片组件特定设置
        component.type = 'card';
        component.collapsible = this.makeCollapsible(component.element);
    }
    
    setupGenericComponent(component) {
        // 通用组件设置
        component.type = 'generic';
    }
    
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const component = this.findComponentByElement(entry.target);
                if (component && !component.initialized) {
                    this.activateComponent(component);
                }
            }
        });
    }
    
    handleMutations(mutations) {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // 检查新添加的元素是否是组件
                    if (node.hasAttribute && node.hasAttribute('nc-component')) {
                        this.initializeComponent(node);
                    }
                    
                    // 检查子元素
                    const componentChildren = node.querySelectorAll?.('[nc-component]') || [];
                    componentChildren.forEach(child => {
                        this.initializeComponent(child);
                    });
                }
            });
        });
    }
    
    findComponentByElement(element) {
        for (const [id, component] of this.components) {
            if (component.element === element) {
                return component;
            }
        }
        return null;
    }
    
    activateComponent(component) {
        component.initialized = true;
        
        // 触发组件激活事件
        const event = new CustomEvent('componentactivate', {
            detail: {
                component: component
            }
        });
        component.element.dispatchEvent(event);
        
        // 执行组件特定的激活逻辑
        this.executeComponentActivation(component);
    }
    
    executeComponentActivation(component) {
        // 根据组件类型执行特定激活逻辑
        switch (component.type) {
            case 'chart':
                this.activateChartComponent(component);
                break;
            case 'table':
                this.activateTableComponent(component);
                break;
            case 'form':
                this.activateFormComponent(component);
                break;
            case 'card':
                this.activateCardComponent(component);
                break;
        }
    }
    
    activateChartComponent(component) {
        // 激活图表组件
        if (window.ECharts) {
            component.chartInstance = echarts.init(component.element);
            // 加载图表数据和配置
            this.loadChartData(component);
        }
    }
    
    activateTableComponent(component) {
        // 激活表格组件
        this.enhanceTableFunctionality(component);
    }
    
    activateFormComponent(component) {
        // 激活表单组件
        this.enhanceFormFunctionality(component);
    }
    
    activateCardComponent(component) {
        // 激活卡片组件
        this.enhanceCardFunctionality(component);
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    enableVirtualScroll(element) {
        // 启用虚拟滚动（简化实现）
        return false;
    }
    
    setupFormValidation(element) {
        // 设置表单验证
        return null;
    }
    
    makeCollapsible(element) {
        // 使元素可折叠
        return false;
    }
    
    loadChartData(component) {
        // 加载图表数据
    }
    
    enhanceTableFunctionality(component) {
        // 增强表格功能
    }
    
    enhanceFormFunctionality(component) {
        // 增强表单功能
    }
    
    enhanceCardFunctionality(component) {
        // 增强卡片功能
    }
    
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
        }
        
        // 清理所有组件
        this.components.forEach(component => {
            component.observers.forEach(unsubscribe => {
                unsubscribe();
            });
        });
        
        this.components.clear();
    }
}

// 工具函数
const ncUtils = {
    // 防抖函数
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },
    
    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    // 深度合并对象
    deepMerge(target, source) {
        const output = Object.assign({}, target);
        if (this.isObject(target) && this.isObject(source)) {
            Object.keys(source).forEach(key => {
                if (this.isObject(source[key])) {
                    if (!(key in target)) {
                        Object.assign(output, { [key]: source[key] });
                    } else {
                        output[key] = this.deepMerge(target[key], source[key]);
                    }
                } else {
                    Object.assign(output, { [key]: source[key] });
                }
            });
        }
        return output;
    },
    
    // 检查是否为对象
    isObject(item) {
        return (item && typeof item === 'object' && !Array.isArray(item));
    },
    
    // 格式化数字
    formatNumber(num, decimals = 2) {
        return new Intl.NumberFormat('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(num);
    },
    
    // 格式化日期
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return new Intl.DateTimeFormat('zh-CN', { ...defaultOptions, ...options }).format(new Date(date));
    },
    
    // 生成唯一ID
    generateId(prefix = 'nc') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },
    
    // 检测设备类型
    getDeviceType() {
        const userAgent = navigator.userAgent;
        
        if (/mobile/i.test(userAgent)) return 'mobile';
        if (/tablet/i.test(userAgent)) return 'tablet';
        return 'desktop';
    },
    
    // 检测操作系统
    getOperatingSystem() {
        const userAgent = navigator.userAgent;
        
        if (/windows/i.test(userAgent)) return 'Windows';
        if (/mac/i.test(userAgent)) return 'macOS';
        if (/linux/i.test(userAgent)) return 'Linux';
        if (/android/i.test(userAgent)) return 'Android';
        if (/ios|iphone|ipad/i.test(userAgent)) return 'iOS';
        return 'Unknown';
    }
};

// 全局实例
const responsiveManager = new ResponsiveManager();
const themeManager = new ThemeManager();
const layoutManager = new LayoutManager();
const componentManager = new ComponentManager();

// 导出到全局作用域
window.NC = {
    ResponsiveManager,
    ThemeManager,
    LayoutManager,
    ComponentManager,
    responsiveManager,
    themeManager,
    layoutManager,
    componentManager,
    utils: ncUtils
};

// DOM 加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 应用主题
    themeManager.applyTheme();
    
    // 初始化布局
    layoutManager.init();
    
    // 初始化组件
    componentManager.init();
});

export {
    ResponsiveManager,
    ThemeManager,
    LayoutManager,
    ComponentManager,
    responsiveManager,
    themeManager,
    layoutManager,
    componentManager,
    ncUtils
};