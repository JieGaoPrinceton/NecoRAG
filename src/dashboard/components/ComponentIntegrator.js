/**
 * NecoRAG 调试面板组件集成器
 * 负责动态加载和集成各种可视化组件
 */

class ComponentIntegrator {
    constructor() {
        this.loadedComponents = new Map();
        this.componentPaths = {
            'retrieval-timeline': '/components/RetrievalTraceTimeline.html',
            'evidence-grid': '/components/EvidenceCard.html',
            'reasoning-chart': '/components/ReasoningChainChart.html'
        };
    }

    /**
     * 动态加载组件
     */
    async loadComponent(componentName, containerId, data = null) {
        try {
            // 检查组件是否已加载
            if (this.loadedComponents.has(componentName)) {
                return this.loadedComponents.get(componentName);
            }

            const componentPath = this.componentPaths[componentName];
            if (!componentPath) {
                throw new Error(`未知组件: ${componentName}`);
            }

            // 加载组件HTML
            const response = await fetch(componentPath);
            if (!response.ok) {
                throw new Error(`加载组件失败: ${response.status}`);
            }

            const htmlContent = await response.text();
            
            // 创建组件实例
            const component = this.createComponentInstance(componentName, htmlContent, data);
            this.loadedComponents.set(componentName, component);
            
            // 渲染到指定容器
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = component.render();
                component.mount();
            }

            return component;

        } catch (error) {
            console.error(`加载组件 ${componentName} 失败:`, error);
            return null;
        }
    }

    /**
     * 创建组件实例
     */
    createComponentInstance(name, html, data) {
        switch(name) {
            case 'retrieval-timeline':
                return new RetrievalTimelineComponent(html, data);
            case 'evidence-grid':
                return new EvidenceGridComponent(html, data);
            case 'reasoning-chart':
                return new ReasoningChartComponent(html, data);
            default:
                throw new Error(`不支持的组件类型: ${name}`);
        }
    }

    /**
     * 更新组件数据
     */
    updateComponent(componentName, data) {
        const component = this.loadedComponents.get(componentName);
        if (component) {
            component.update(data);
        }
    }

    /**
     * 卸载组件
     */
    unloadComponent(componentName) {
        const component = this.loadedComponents.get(componentName);
        if (component) {
            component.destroy();
            this.loadedComponents.delete(componentName);
        }
    }
}

/**
 * 检索时间轴组件
 */
class RetrievalTimelineComponent {
    constructor(htmlTemplate, data) {
        this.htmlTemplate = htmlTemplate;
        this.data = data || [];
        this.element = null;
    }

    render() {
        // 提取模板中的主要内容
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.htmlTemplate;
        
        const templateContent = tempDiv.querySelector('#timeline-content') || tempDiv;
        return templateContent.innerHTML;
    }

    mount() {
        this.element = document.getElementById('retrieval-timeline-component');
        if (this.element) {
            this.initializeTimeline();
            this.update(this.data);
        }
    }

    initializeTimeline() {
        // 初始化时间轴的交互功能
        this.setupEventListeners();
    }

    update(newData) {
        this.data = newData;
        this.renderTimeline();
    }

    renderTimeline() {
        if (!this.element) return;

        if (!this.data || this.data.length === 0) {
            this.element.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #64748b;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                    <p>暂无检索路径数据</p>
                </div>
            `;
            return;
        }

        const timelineHtml = this.data.map((step, index) => `
            <div class="timeline-item" data-step="${index}">
                <div class="timeline-marker ${this.getStepStatusClass(step.status)}">
                    ${this.getStepIcon(step.type)}
                </div>
                <div class="timeline-content">
                    <div class="step-header">
                        <h4 class="step-title">${this.getStepTitle(step.type)}</h4>
                        <span class="step-time">${step.timestamp ? new Date(step.timestamp).toLocaleTimeString() : ''}</span>
                    </div>
                    <div class="step-details">
                        <p class="step-description">${step.description || ''}</p>
                        ${step.duration ? `<span class="step-duration">${step.duration}ms</span>` : ''}
                        ${step.confidence ? `<span class="step-confidence">置信度: ${(step.confidence * 100).toFixed(1)}%</span>` : ''}
                    </div>
                    ${step.entities ? `
                        <div class="step-entities">
                            <strong>识别实体:</strong> 
                            ${step.entities.map(entity => 
                                `<span class="entity-tag">${entity.type}: ${entity.value}</span>`
                            ).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');

        this.element.innerHTML = `
            <div class="retrieval-timeline">
                <div class="timeline-header">
                    <h3>检索路径时间轴</h3>
                    <div class="timeline-stats">
                        <span>总步骤: ${this.data.length}</span>
                        <span>总耗时: ${this.calculateTotalDuration()}ms</span>
                    </div>
                </div>
                <div class="timeline-container">
                    ${timelineHtml}
                </div>
            </div>
        `;

        this.setupStepInteractions();
    }

    getStepStatusClass(status) {
        const statusMap = {
            'success': 'success',
            'pending': 'pending',
            'failed': 'failed',
            'processing': 'processing'
        };
        return statusMap[status] || 'pending';
    }

    getStepIcon(type) {
        const iconMap = {
            'query_analysis': '🔍',
            'entity_recognition': '🏷️',
            'vector_retrieval': '📊',
            'graph_reasoning': '🔗',
            'result_fusion': '🔄',
            'answer_generation': '💬'
        };
        return iconMap[type] || '🔹';
    }

    getStepTitle(type) {
        const titleMap = {
            'query_analysis': '查询分析',
            'entity_recognition': '实体识别',
            'vector_retrieval': '向量检索',
            'graph_reasoning': '图谱推理',
            'result_fusion': '结果融合',
            'answer_generation': '答案生成'
        };
        return titleMap[type] || type;
    }

    calculateTotalDuration() {
        return this.data.reduce((total, step) => total + (step.duration || 0), 0);
    }

    setupEventListeners() {
        // 全局事件监听器
    }

    setupStepInteractions() {
        // 为每个步骤添加交互功能
        const stepItems = this.element.querySelectorAll('.timeline-item');
        stepItems.forEach(item => {
            item.addEventListener('click', () => {
                this.highlightStep(item.dataset.step);
            });
        });
    }

    highlightStep(stepIndex) {
        // 高亮选中的步骤
        const stepItems = this.element.querySelectorAll('.timeline-item');
        stepItems.forEach(item => item.classList.remove('highlighted'));
        stepItems[stepIndex].classList.add('highlighted');
        
        // 触发自定义事件
        const event = new CustomEvent('stepSelected', {
            detail: { step: this.data[stepIndex], index: parseInt(stepIndex) }
        });
        document.dispatchEvent(event);
    }

    destroy() {
        if (this.element) {
            this.element.innerHTML = '';
        }
    }
}

/**
 * 证据网格组件
 */
class EvidenceGridComponent {
    constructor(htmlTemplate, data) {
        this.htmlTemplate = htmlTemplate;
        this.data = data || [];
        this.element = null;
        this.sortField = 'relevance_score';
        this.sortOrder = 'desc';
    }

    render() {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.htmlTemplate;
        const templateContent = tempDiv.querySelector('#evidence-content') || tempDiv;
        return templateContent.innerHTML;
    }

    mount() {
        this.element = document.getElementById('evidence-grid-component');
        if (this.element) {
            this.initializeGrid();
            this.update(this.data);
        }
    }

    initializeGrid() {
        this.setupFilters();
        this.setupSorting();
    }

    update(newData) {
        this.data = newData;
        this.renderGrid();
    }

    renderGrid() {
        if (!this.element) return;

        if (!this.data || this.data.length === 0) {
            this.element.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #64748b;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📄</div>
                    <p>暂无证据数据</p>
                </div>
            `;
            return;
        }

        // 排序数据
        const sortedData = [...this.data].sort((a, b) => {
            const aVal = a[this.sortField];
            const bVal = b[this.sortField];
            const modifier = this.sortOrder === 'asc' ? 1 : -1;
            return (aVal > bVal ? 1 : -1) * modifier;
        });

        const gridHtml = sortedData.map(evidence => `
            <div class="evidence-card ${this.getEvidenceQualityClass(evidence.relevance_score)}" 
                 data-evidence-id="${evidence.evidence_id}">
                <div class="evidence-header">
                    <div class="evidence-title">
                        <span class="evidence-icon">${this.getEvidenceIcon(evidence.source_type)}</span>
                        <h4>${evidence.title || '未命名证据'}</h4>
                    </div>
                    <div class="evidence-score">
                        <span class="score-value">${(evidence.relevance_score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="evidence-content">
                    <p class="evidence-snippet">${this.truncateText(evidence.content, 150)}</p>
                    
                    <div class="evidence-metadata">
                        <span class="metadata-item">
                            <strong>来源:</strong> ${evidence.source || '未知'}
                        </span>
                        <span class="metadata-item">
                            <strong>时间:</strong> ${evidence.timestamp ? new Date(evidence.timestamp).toLocaleString() : 'N/A'}
                        </span>
                        ${evidence.entity_coverage ? `
                            <span class="metadata-item">
                                <strong>实体覆盖:</strong> ${evidence.entity_coverage.join(', ')}
                            </span>
                        ` : ''}
                    </div>
                </div>
                
                <div class="evidence-actions">
                    <button class="btn-small" onclick="viewEvidenceDetail('${evidence.evidence_id}')">查看详情</button>
                    <button class="btn-small" onclick="pinEvidence('${evidence.evidence_id}')">固定</button>
                </div>
            </div>
        `).join('');

        this.element.innerHTML = `
            <div class="evidence-grid-container">
                <div class="grid-controls">
                    <div class="grid-filters">
                        <select id="sourceFilter" onchange="filterBySource(this.value)">
                            <option value="">所有来源</option>
                            <option value="vector_db">向量数据库</option>
                            <option value="knowledge_graph">知识图谱</option>
                            <option value="external_api">外部API</option>
                        </select>
                        
                        <select id="qualityFilter" onchange="filterByQuality(this.value)">
                            <option value="">所有质量</option>
                            <option value="high">高质量 (>80%)</option>
                            <option value="medium">中等质量 (50-80%)</option>
                            <option value="low">低质量 (<50%)</option>
                        </select>
                    </div>
                    
                    <div class="grid-sorting">
                        <span>排序:</span>
                        <select id="sortField" onchange="changeSortField(this.value)">
                            <option value="relevance_score">相关度</option>
                            <option value="timestamp">时间</option>
                            <option value="source">来源</option>
                        </select>
                        <button id="sortOrder" onclick="toggleSortOrder()">↓</button>
                    </div>
                </div>
                
                <div class="evidence-grid">
                    ${gridHtml}
                </div>
                
                <div class="grid-summary">
                    <p>共找到 ${this.data.length} 个证据，平均相关度 ${(this.calculateAverageScore() * 100).toFixed(1)}%</p>
                </div>
            </div>
        `;

        this.setupGridInteractions();
    }

    getEvidenceQualityClass(score) {
        if (score >= 0.8) return 'high-quality';
        if (score >= 0.5) return 'medium-quality';
        return 'low-quality';
    }

    getEvidenceIcon(sourceType) {
        const iconMap = {
            'vector_db': '🗄️',
            'knowledge_graph': '🕸️',
            'external_api': '🌐',
            'document_store': '📚'
        };
        return iconMap[sourceType] || '📄';
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    calculateAverageScore() {
        if (this.data.length === 0) return 0;
        return this.data.reduce((sum, evidence) => sum + evidence.relevance_score, 0) / this.data.length;
    }

    setupFilters() {
        // 设置过滤器逻辑
    }

    setupSorting() {
        // 设置排序逻辑
    }

    setupGridInteractions() {
        // 设置网格交互功能
    }

    destroy() {
        if (this.element) {
            this.element.innerHTML = '';
        }
    }
}

/**
 * 推理图表组件
 */
class ReasoningChartComponent {
    constructor(htmlTemplate, data) {
        this.htmlTemplate = htmlTemplate;
        this.data = data || [];
        this.element = null;
    }

    render() {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = this.htmlTemplate;
        const templateContent = tempDiv.querySelector('#chart-content') || tempDiv;
        return templateContent.innerHTML;
    }

    mount() {
        this.element = document.getElementById('reasoning-chart-component');
        if (this.element) {
            this.initializeChart();
            this.update(this.data);
        }
    }

    initializeChart() {
        this.setupChartControls();
    }

    update(newData) {
        this.data = newData;
        this.renderChart();
    }

    renderChart() {
        if (!this.element) return;

        if (!this.data || this.data.length === 0) {
            this.element.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: #64748b;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🤔</div>
                    <p>暂无推理数据</p>
                </div>
            `;
            return;
        }

        this.element.innerHTML = `
            <div class="reasoning-chart-container">
                <div class="chart-controls">
                    <div class="chart-type-selector">
                        <button class="btn-small active" onclick="switchChartType('confidence')">置信度趋势</button>
                        <button class="btn-small" onclick="switchChartType('iterations')">迭代次数</button>
                        <button class="btn-small" onclick="switchChartType('hallucination')">幻觉检测</button>
                    </div>
                </div>
                
                <div class="chart-display">
                    <canvas id="reasoningChartCanvas" width="800" height="400"></canvas>
                </div>
                
                <div class="chart-insights">
                    <h4>推理洞察</h4>
                    <div class="insight-item">
                        <span class="insight-label">最终置信度:</span>
                        <span class="insight-value">${this.getFinalConfidence()}%</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-label">推理迭代:</span>
                        <span class="insight-value">${this.data.length} 次</span>
                    </div>
                    <div class="insight-item">
                        <span class="insight-label">收敛速度:</span>
                        <span class="insight-value">${this.getConvergenceSpeed()}</span>
                    </div>
                </div>
            </div>
        `;

        this.drawChart();
        this.setupChartInteractions();
    }

    drawChart() {
        const canvas = document.getElementById('reasoningChartCanvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // 清空画布
        ctx.clearRect(0, 0, width, height);
        
        // 绘制坐标系
        this.drawCoordinateSystem(ctx, width, height);
        
        // 绘制置信度曲线
        this.drawConfidenceCurve(ctx, width, height);
        
        // 绘制关键点标记
        this.drawKeyPoints(ctx, width, height);
    }

    drawCoordinateSystem(ctx, width, height) {
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        
        // 绘制网格线
        for (let i = 0; i <= 10; i++) {
            const x = (width - 100) * (i / 10) + 50;
            const y = height - 50 - (height - 100) * (i / 10);
            
            // 垂直线
            ctx.beginPath();
            ctx.moveTo(x, 50);
            ctx.lineTo(x, height - 50);
            ctx.stroke();
            
            // 水平线
            ctx.beginPath();
            ctx.moveTo(50, y);
            ctx.lineTo(width - 50, y);
            ctx.stroke();
        }
    }

    drawConfidenceCurve(ctx, width, height) {
        if (this.data.length === 0) return;

        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 3;
        ctx.beginPath();

        this.data.forEach((step, index) => {
            const x = 50 + (width - 100) * (index / Math.max(this.data.length - 1, 1));
            const y = height - 50 - (height - 100) * (step.confidence || 0);
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();
    }

    drawKeyPoints(ctx, width, height) {
        this.data.forEach((step, index) => {
            const x = 50 + (width - 100) * (index / Math.max(this.data.length - 1, 1));
            const y = height - 50 - (height - 100) * (step.confidence || 0);
            
            // 绘制点
            ctx.fillStyle = '#3b82f6';
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fill();
            
            // 绘制标签
            ctx.fillStyle = '#1e293b';
            ctx.font = '12px Arial';
            ctx.fillText(`第${index + 1}次`, x - 15, y - 10);
        });
    }

    getFinalConfidence() {
        if (this.data.length === 0) return 0;
        const lastStep = this.data[this.data.length - 1];
        return ((lastStep.confidence || 0) * 100).toFixed(1);
    }

    getConvergenceSpeed() {
        if (this.data.length < 2) return 'N/A';
        
        const confidences = this.data.map(step => step.confidence || 0);
        const variance = this.calculateVariance(confidences);
        
        if (variance < 0.01) return '快速收敛';
        if (variance < 0.05) return '中等收敛';
        return '缓慢收敛';
    }

    calculateVariance(numbers) {
        const mean = numbers.reduce((sum, num) => sum + num, 0) / numbers.length;
        const squaredDiffs = numbers.map(num => Math.pow(num - mean, 2));
        return squaredDiffs.reduce((sum, diff) => sum + diff, 0) / numbers.length;
    }

    setupChartControls() {
        // 设置图表控制逻辑
    }

    setupChartInteractions() {
        // 设置图表交互功能
    }

    destroy() {
        if (this.element) {
            this.element.innerHTML = '';
        }
    }
}

// 全局实例
const componentIntegrator = new ComponentIntegrator();

// 导出到全局作用域
window.ComponentIntegrator = ComponentIntegrator;
window.componentIntegrator = componentIntegrator;