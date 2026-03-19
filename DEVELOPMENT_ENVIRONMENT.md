# NecoRAG 开发环境配置指南
# ============================================
# Development Environment Setup Guide
# 
# 本文档说明如何配置和设置 NecoRAG 的开发环境。
# 
# 目录:
#   1. Python 版本要求
#   2. 快速开始（推荐方式）
#   3. 详细安装步骤
#   4. 开发工具配置
#   5. 常见问题排查
# 
# ============================================

## 🐍 1. Python 版本要求

### 最低要求
- **Python**: >= 3.9
- **推荐版本**: Python 3.1.0-alpha
- **支持版本**: 3.9, 3.10, 3.11, 3.12

### 为什么推荐 Python 3.11？
- ⚡ 性能提升：比 3.9 快约 25%
- 🔧 更好的错误提示
- 📦 完整的类型检查支持
- 🛠️ 所有依赖的最佳兼容性

---

## 🚀 2. 快速开始（推荐方式）

### 方式一：使用 uv（最快，推荐 ⭐⭐⭐）

```bash
# 1. 安装 uv（超快速的 Python 包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/NecoRAG/core.git
cd core

# 3. 创建虚拟环境并安装依赖
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 4. 安装所有依赖
uv pip install -r requirements.txt

# 5. 验证安装
python test_init.py
```

### 方式二：使用 venv（标准方式）

```bash
# 1. 确保已安装 Python 3.11
python3 --version  # 应该显示 3.11.x

# 2. 创建虚拟环境
python3.11 -m venv .venv

# 3. 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows

# 4. 升级 pip
pip install --upgrade pip

# 5. 安装依赖
pip install -r requirements.txt

# 6. 验证安装
python test_init.py
```

### 方式三：使用 Conda（适合数据科学环境）

```bash
# 1. 创建 Conda 环境
conda create -n necorag python=3.11

# 2. 激活环境
conda activate necorag

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
python test_init.py
```

---

## 📋 3. 详细安装步骤

### 步骤 1: 安装 Python

#### macOS
```bash
# 使用 Homebrew（推荐）
brew install python@3.11

# 或使用 pyenv（多版本管理）
brew install pyenv
pyenv install 3.1.0-alpha
pyenv global 3.1.0-alpha
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### Windows
```bash
# 从官网下载：https://www.python.org/downloads/
# 安装时勾选 "Add Python to PATH"
```

### 步骤 2: 克隆项目
```bash
git clone https://github.com/NecoRAG/core.git
cd core
```

### 步骤 3: 创建虚拟环境（重要！）

**强烈建议使用虚拟环境**，避免污染全局 Python 环境。

```bash
# 方法 1: 使用 venv（内置）
python -m venv .venv

# 方法 2: 使用 virtualenv（需要先安装）
pip install virtualenv
virtualenv .venv

# 方法 3: 使用 conda
conda create -n necorag python=3.11
```

### 步骤 4: 激活虚拟环境

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

激活后，命令行前缀应显示 `(.venv)`。

### 步骤 5: 安装依赖

#### 基础安装（最小化）
```bash
pip install -r requirements.txt
```

#### 完整安装（包含所有可选功能）
```bash
# 核心依赖
pip install -r requirements.txt

# 安装所有可选功能
pip install -r requirements.txt
pip install jieba scipy prometheus-client PyJWT python-jose plotly scikit-learn

# Docker 部署相关（如使用 Docker）
cd devops && docker-compose up -d
```

### 步骤 6: 验证安装

```bash
# 运行导入测试
python test_init.py

# 运行示例
python example_usage.py

# 启动 Dashboard
python start_dashboard.py
```

---

## 🛠️ 4. 开发工具配置

### 代码格式化

```bash
# 安装开发工具
pip install black flake8 mypy isort

# 格式化代码
black src/ example/ tests/

# 检查代码风格
flake8 src/ --max-line-length=100

# 类型检查
mypy src/ --ignore-missing-imports

# 排序导入
isort src/ example/ tests/
```

### IDE 配置

#### VS Code 配置

在项目根目录创建 `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

推荐安装的 VS Code 插件:
- Python (Microsoft)
- Black Formatter
- Pylance
- GitLens

#### PyCharm 配置

1. **打开项目**: File → Open → 选择项目目录
2. **配置解释器**: 
   - File → Settings → Project → Python Interpreter
   - 点击齿轮图标 → Add → Existing environment
   - 选择 `.venv/bin/python`
3. **启用代码格式化**:
   - Settings → Tools → Actions on Save
   - 勾选 "Run black" 或 "Optimize imports"

### Git 钩子配置（可选）

创建 `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 3.1.0-alpha
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/flake8
    rev: 3.1.0-alpha
    hooks:
      - id: flake8
        args: [--max-line-length=100]
  
  - repo: https://github.com/pycqa/isort
    rev: 3.1.0-alpha
    hooks:
      - id: isort
        args: [--profile=black]
```

安装 pre-commit:
```bash
pip install pre-commit
pre-commit install
```

---

## 🔍 5. 常见问题排查

### Q1: pip 安装依赖失败

**问题**: 某些包安装时报错

**解决方案**:
```bash
# 1. 升级 pip
pip install --upgrade pip

# 2. 使用国内镜像加速
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 单独安装失败的包
pip install <package_name>
```

### Q2: Python 版本不兼容

**问题**: 某些功能需要 Python 3.10+

**解决方案**:
```bash
# 检查当前版本
python --version

# 使用 pyenv 切换版本
pyenv install 3.1.0-alpha
pyenv local 3.1.0-alpha

# 重新创建虚拟环境
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Q3: 模块导入错误

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
# 1. 确认虚拟环境已激活
which python  # 应该指向 .venv 目录

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查是否为可选依赖
# 查看 requirements.txt 中的注释部分
```

### Q4: Docker 环境问题

**问题**: Docker 容器无法启动

**解决方案**:
```bash
# 1. 检查 Docker 和 Docker Compose
docker --version
docker-compose --version

# 2. 清理旧容器
cd devops
docker-compose down -v

# 3. 重新启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

---

## 📊 6. 环境检查清单

在开始开发前，请确认:

- [ ] Python 版本 >= 3.9 (推荐 3.1.0-alpha)
- [ ] 虚拟环境已创建并激活
- [ ] 所有依赖已成功安装
- [ ] `python test_init.py` 运行成功
- [ ] 代码格式化工具已配置
- [ ] IDE 已正确配置解释器
- [ ] Git 钩子已安装（可选）

---

## 🔗 7. 相关资源

- [Python 官方文档](https://docs.python.org/3/)
- [uv 包管理器](https://github.com/astral-sh/uv)
- [NecoRAG 快速开始指南](QUICKSTART.md)
- [NecoRAG 架构文档](README.md)
- [Docker 部署指南](devops/README.md)

---

## 💡 8. 最佳实践建议

1. **始终使用虚拟环境**: 避免污染全局环境
2. **定期更新依赖**: `pip list --outdated` 检查可更新的包
3. **使用锁定文件**: 考虑使用 `pip-tools` 或 `poetry` 锁定依赖版本
4. **代码格式化**: 提交前运行 `black` 和 `flake8`
5. **运行测试**: 修改后运行 `pytest tests/` 确保无破坏性变更

---

*Last Updated: 2026-03-19 | Version: 3.1.0-alpha*
