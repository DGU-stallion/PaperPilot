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
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
step()  { echo -e "${BLUE}[→]${NC} $1"; }

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
        PAPERPILOT_DIR="$(pwd)"
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
    PAPERPILOT_DIR="$(pwd)"
}

# --- 创建虚拟环境并安装 ---
setup_venv() {
    if [ ! -d ".venv" ]; then
        info "创建虚拟环境..."
        $PYTHON -m venv .venv
    else
        info "虚拟环境已存在"
    fi

    source .venv/bin/activate 2>/dev/null || . .venv/bin/activate

    info "安装依赖（Standard 档位）..."
    pip install --upgrade pip -q
    pip install -r install/requirements-standard.txt -q
    info "依赖安装完成"
}

# --- 检测已安装的 Agent 并注册 skill ---
register_skill() {
    step "检测已安装的 AI 编程助手..."

    REGISTERED=0

    # 各 Agent 的 skills 目录（全局级）
    # Claude Code
    if [ -d "$HOME/.claude" ] || command -v claude &>/dev/null; then
        mkdir -p "$HOME/.claude/skills/paperpilot"
        ln -sf "$PAPERPILOT_DIR/SKILL.md" "$HOME/.claude/skills/paperpilot/SKILL.md"
        info "Claude Code → ~/.claude/skills/paperpilot/ (symlink)"
        REGISTERED=$((REGISTERED + 1))
    fi

    # Kiro
    if [ -d "$HOME/.kiro" ] || command -v kiro &>/dev/null; then
        mkdir -p "$HOME/.kiro/skills/paperpilot"
        ln -sf "$PAPERPILOT_DIR/SKILL.md" "$HOME/.kiro/skills/paperpilot/SKILL.md"
        info "Kiro → ~/.kiro/skills/paperpilot/ (symlink)"
        REGISTERED=$((REGISTERED + 1))
    fi

    # Cursor
    if [ -d "$HOME/.cursor" ] || [ -d "$HOME/Library/Application Support/Cursor" ]; then
        mkdir -p "$HOME/.cursor/skills/paperpilot"
        ln -sf "$PAPERPILOT_DIR/SKILL.md" "$HOME/.cursor/skills/paperpilot/SKILL.md"
        info "Cursor → ~/.cursor/skills/paperpilot/ (symlink)"
        REGISTERED=$((REGISTERED + 1))
    fi

    # Codex
    if [ -d "$HOME/.codex" ] || command -v codex &>/dev/null; then
        mkdir -p "$HOME/.codex/skills/paperpilot"
        ln -sf "$PAPERPILOT_DIR/SKILL.md" "$HOME/.codex/skills/paperpilot/SKILL.md"
        info "Codex → ~/.codex/skills/paperpilot/ (symlink)"
        REGISTERED=$((REGISTERED + 1))
    fi

    # OpenCode
    if [ -d "$HOME/.config/opencode" ] || command -v opencode &>/dev/null; then
        mkdir -p "$HOME/.config/opencode/skill/paperpilot"
        ln -sf "$PAPERPILOT_DIR/SKILL.md" "$HOME/.config/opencode/skill/paperpilot/SKILL.md"
        info "OpenCode → ~/.config/opencode/skill/paperpilot/ (symlink)"
        REGISTERED=$((REGISTERED + 1))
    fi

    if [ "$REGISTERED" -eq 0 ]; then
        warn "未检测到已安装的 Agent。你可以手动注册："
        echo "    mkdir -p ~/.claude/skills/paperpilot"
        echo "    ln -s $PAPERPILOT_DIR/SKILL.md ~/.claude/skills/paperpilot/SKILL.md"
    else
        info "已注册到 $REGISTERED 个 Agent（通过 symlink，自动跟随仓库更新）"
    fi
}

# --- 运行诊断 ---
run_doctor() {
    info "运行环境诊断..."
    echo ""
    .venv/bin/python install/bootstrap.py --check --profile standard 2>/dev/null || warn "诊断脚本执行异常，跳过"
    echo ""
}

# --- 输出摘要 ---
print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    info "PaperPilot 安装完成！"
    echo ""
    echo "  仓库路径: $PAPERPILOT_DIR"
    echo "  Python:   $PY_VERSION"
    echo "  档位:     Standard"
    echo ""
    echo "━━━ 使用方式 ━━━"
    echo ""
    echo "  1. 创建论文项目目录并进入"
    echo "  2. 启动你的 AI 编程助手"
    echo "  3. 输入 /paperpilot 或直接描述需求"
    echo ""
    echo "  PaperPilot 已注册为全局 skill，所有项目中均可使用。"
    echo "  更新：cd $PAPERPILOT_DIR && git pull"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
    register_skill
    run_doctor
    print_summary
}

main "$@"
