#!/usr/bin/env python3
"""Agent capability declaration and detection.

Each hosting agent (Claude Code, Codex, Kiro, etc.) declares its capabilities
on first load. The skill reads these to gracefully enable/disable features.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from scripts.shared.paths import PAPERS_DIR
from scripts.shared.state import get_current_project, load as load_state
from scripts.workflow import atomic_save

KNOWN_AGENTS = {"antigravity", "agy", "claude-code", "codex", "kiro", "cursor", "opencode", "generic"}

DEFAULT_CAPS: dict[str, Any] = {
    "agent_type": "antigravity",
    "web_search": True,
    "mcp_servers": ["paper-search-mcp"],
    "file_edit": True,
    "shell_exec": True,
    "texlive": False,
}


def detect_local_capabilities() -> dict[str, Any]:
    """Auto-detect locally available tools (does not require agent declaration)."""
    return {
        "texlive": shutil.which("xelatex") is not None,
        "python_analysis": _has_analysis_backend(),
        "biber": shutil.which("biber") is not None,
    }


def _has_analysis_backend() -> bool:
    try:
        import pandas  # noqa: F401
        return True
    except ImportError:
        return False


def declare_capabilities(
    agent_type: str,
    web_search: bool = False,
    mcp_servers: list[str] | None = None,
    project_name: str | None = None,
    papers_dir: Path | None = None,
) -> dict[str, Any]:
    """Declare host agent capabilities into project state.

    Returns the final capabilities dict (merged with local detection).
    """
    if agent_type not in KNOWN_AGENTS:
        agent_type = "generic"

    base = papers_dir or PAPERS_DIR
    name = project_name or get_current_project()
    if not name:
        return {"error": "no active project"}

    state = load_state(name, base)
    local = detect_local_capabilities()

    caps = {
        "agent_type": agent_type,
        "web_search": web_search,
        "mcp_servers": mcp_servers or [],
        "file_edit": True,
        "shell_exec": True,
        "texlive": local["texlive"],
        "python_analysis": local["python_analysis"],
        "biber": local["biber"],
    }

    state["agent_capabilities"] = caps
    atomic_save(name, state, base)
    return caps


def get_capabilities(project_name: str | None = None, papers_dir: Path | None = None) -> dict[str, Any]:
    """Read declared capabilities from project state."""
    base = papers_dir or PAPERS_DIR
    name = project_name or get_current_project()
    if not name:
        return dict(DEFAULT_CAPS)

    state = load_state(name, base)
    caps = state.get("agent_capabilities")
    if caps and isinstance(caps, dict):
        return caps
    return dict(DEFAULT_CAPS)


def capability_matrix(project_name: str | None = None, papers_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Return a feature matrix showing which modules are fully functional.

    Maps module name → {available: bool, reason: str, degraded: bool}
    """
    caps = get_capabilities(project_name, papers_dir)

    matrix = {
        "conceptualize": {"available": True, "degraded": False, "reason": "纯对话，无特殊依赖"},
        "research": {
            "available": True,
            "degraded": not caps.get("web_search", False),
            "reason": "需要 web_search 能力" if not caps.get("web_search") else "完整可用",
        },
        "literature": {"available": True, "degraded": False, "reason": "纯文本处理"},
        "data": {
            "available": caps.get("python_analysis", False),
            "degraded": not caps.get("python_analysis", False),
            "reason": "需要 pandas" if not caps.get("python_analysis") else "完整可用",
        },
        "analyze": {
            "available": caps.get("python_analysis", False),
            "degraded": not caps.get("python_analysis", False),
            "reason": "需要 linearmodels/statsmodels" if not caps.get("python_analysis") else "完整可用",
        },
        "verify": {
            "available": caps.get("python_analysis", False),
            "degraded": not caps.get("python_analysis", False),
            "reason": "需要 linearmodels/statsmodels" if not caps.get("python_analysis") else "完整可用",
        },
        "write": {"available": True, "degraded": False, "reason": "纯文本生成"},
        "format": {
            "available": caps.get("texlive", False),
            "degraded": not caps.get("texlive", False),
            "reason": "需要 xelatex" if not caps.get("texlive") else "完整可用",
        },
    }
    return matrix
