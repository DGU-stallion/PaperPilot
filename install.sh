#!/usr/bin/env bash
# PaperPilot — 一键安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/DGU-stallion/PaperPilot/main/install.sh | bash
# 或:   git clone ... && cd PaperPilot && bash install.sh

set -euo pipefail

REPO_URL="https://github.com/DGU-stallion/PaperPilot.git"
REPO_DIR="PaperPilot"

# --- 颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# --- 检测 Python ---
detect_python() {
    if command -v python3 &>/dev/null; then
        PYTHON=python3
    elif command -v python &>/dev/null; then
        PYTHON=python
    else
        error "未找到 Python。请安装 Python 3.11+。"
        exit 1
    fi

    PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$($PYTHON -c "import sys; print(sys.version_info.minor)")

    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
        error "Python 版本 $PY_VERSION 过低，需要 3.11+。"
        exit 1
    fi
    info "Python $PY_VERSION"
}

# --- 获取仓库 ---
clone_or_update() {
    if [ -f "SKILL.md" ] && [ -d "skills/" ]; then
        info "当前目录已是 PaperPilot 仓库"
        return
    fi

    if [ -d "$REPO_DIR" ]; then
        info "仓库已存在，更新中..."
        cd "$REPO_DIR"
        git pull --ff-only 2>/dev/null || warn "git pull 失败，使用现有版本"
    else
        info "克隆仓库..."
        git clone "$REPO_URL" "$REPO_DIR"
        cd "$REPO_DIR"
    fi
}

# --- 创建虚拟环境并安装 ---
setup_venv() {
    if [ ! -d ".venv" ]; then
        info "创建虚拟环境..."
        $PYTHON -m venv .venv
    else
        info "虚拟环境已存在"
    fi

    # 激活虚拟环境
    source .venv/bin/activate 2>/dev/null || . .venv/bin/activate

    info "安装依赖（Standard 档位）..."
    pip install --upgrade pip -q
    pip install -r install/requirements-standard.txt -q
    info "依赖安装完成"
}

# --- 运行诊断 ---
run_doctor() {
    info "运行环境诊断..."
    echo ""
    .venv/bin/python install/bootstrap.py --check --profile standard
    echo ""
}

# --- 输出摘要 ---
print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    info "PaperPilot 安装完成！"
    echo ""
    echo "  仓库路径: $(pwd)"
    echo "  Python:   $PY_VERSION"
    echo "  档位:     Standard"
    echo ""
    echo "━━━ 下一步 ━━━"
    echo ""
    echo "  将以下内容发送给你的 Coding Agent（Claude Code / Kiro / Cursor 等）："
    echo ""
    echo "  ┌──────────────────────────────────────────┐"
    echo "  │ 我已安装 PaperPilot，请读取 CLAUDE.md。   │"
    echo "  │                                          │"
    echo "  │ 我想：                                    │"
    echo "  │  1. 开始一篇新论文                        │"
    echo "  │  2. 导入已有论文项目（路径: ...）          │"
    echo "  │  3. 看一下 Demo 了解流程                  │"
    echo "  └──────────────────────────────────────────┘"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# --- 主流程 ---
main() {
    echo ""
    echo "  PaperPilot 安装程序"
    echo "  ═══════════════════"
    echo ""

    detect_python
    clone_or_update
    setup_venv
    run_doctor
    print_summary
}

main "$@"
