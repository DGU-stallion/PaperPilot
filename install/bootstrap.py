#!/usr/bin/env python3
"""Dependency-free environment doctor for PaperPilot."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_PACKAGES = ("numpy", "pandas", "statsmodels", "linearmodels")
DATA_PACKAGES = ("openpyxl", "pyarrow")


def _package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command_available(name: str) -> bool:
    return shutil.which(name) is not None


def _capability(available: bool, required: bool, message: str, **details: Any) -> dict[str, Any]:
    return {
        "available": available,
        "required": required,
        "message": message,
        **details,
    }


def _check_update() -> dict[str, Any]:
    """Check if local repo is behind remote. Returns update status info."""
    git_dir = ROOT / ".git"
    if not git_dir.is_dir():
        return {"available": False, "reason": "not_a_git_repo"}

    try:
        # Fetch latest remote info without changing working tree
        subprocess.run(
            ["git", "fetch", "--quiet"],
            cwd=ROOT,
            capture_output=True,
            timeout=10,
        )

        # Get local and remote HEAD commit hashes
        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        remote = subprocess.run(
            ["git", "rev-parse", "@{u}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if local.returncode != 0 or remote.returncode != 0:
            return {"available": False, "reason": "no_upstream_tracking"}

        local_hash = local.stdout.strip()
        remote_hash = remote.stdout.strip()

        if local_hash == remote_hash:
            return {"available": True, "up_to_date": True, "local": local_hash[:8]}

        # Count how many commits behind
        behind = subprocess.run(
            ["git", "rev-list", "--count", f"{local_hash}..{remote_hash}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        behind_count = int(behind.stdout.strip()) if behind.returncode == 0 else 0

        return {
            "available": True,
            "up_to_date": False,
            "local": local_hash[:8],
            "remote": remote_hash[:8],
            "behind": behind_count,
        }

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {"available": False, "reason": "git_command_failed"}


def build_report(profile: str) -> dict[str, Any]:
    analysis_packages = {name: _package_available(name) for name in ANALYSIS_PACKAGES}
    data_packages = {name: _package_available(name) for name in DATA_PACKAGES}
    analysis_available = all(analysis_packages.values())

    xelatex = _command_available("xelatex")
    biber = _command_available("biber")
    latex_available = xelatex and biber

    tavily_package = _package_available("tavily")
    tavily_key = bool(os.environ.get("TAVILY_API_KEY"))
    uv_available = _command_available("uv")
    mcp_configured = (ROOT / ".mcp.json").is_file()
    search_available = (tavily_package and tavily_key) or (uv_available and mcp_configured)

    detected_agents = [
        name
        for name in ("kiro-cli", "claude", "codex", "cursor", "opencode")
        if _command_available(name)
    ]

    analysis_required = profile in {"standard", "full"}
    latex_required = profile == "full"

    capabilities = {
        "python": _capability(
            True,
            True,
            f"Python {platform.python_version()}",
            executable=sys.executable,
            supported=sys.version_info >= (3, 11),
        ),
        "analysis": _capability(
            analysis_available,
            analysis_required,
            "实证分析环境已就绪" if analysis_available else "缺少实证分析依赖",
            packages=analysis_packages,
        ),
        "data_formats": _capability(
            all(data_packages.values()),
            False,
            "Excel/Parquet 支持已就绪" if all(data_packages.values()) else "部分数据格式依赖缺失",
            packages=data_packages,
        ),
        "search": _capability(
            search_available,
            False,
            "至少一个增强搜索后端可用" if search_available else "将依赖宿主 Agent 的搜索能力或手动检索",
            tavily_package=tavily_package,
            tavily_key=tavily_key,
            uv=uv_available,
            mcp_configured=mcp_configured,
        ),
        "latex": _capability(
            latex_available,
            latex_required,
            "本地 LaTeX 编译已就绪" if latex_available else "缺少 xelatex 或 biber，可使用 Overleaf",
            xelatex=xelatex,
            biber=biber,
        ),
        "agent": _capability(
            bool(detected_agents),
            False,
            "检测到 Coding Agent" if detected_agents else "未从 PATH 识别 Coding Agent",
            detected=detected_agents,
        ),
    }

    # Version / update check
    update_info = _check_update()
    if update_info.get("available"):
        if update_info.get("up_to_date"):
            capabilities["update"] = _capability(
                True,
                False,
                f"已是最新版本 ({update_info['local']})",
            )
        else:
            behind = update_info.get("behind", 0)
            capabilities["update"] = _capability(
                True,
                False,
                f"有新版本可用（落后 {behind} 个提交）",
                local=update_info["local"],
                remote=update_info["remote"],
                behind=behind,
            )
    else:
        capabilities["update"] = _capability(
            False,
            False,
            "无法检查更新" + (f"（{update_info.get('reason', '')}）" if update_info.get("reason") else ""),
        )

    recommendations: list[str] = []
    if not analysis_available and analysis_required:
        recommendations.append("在隔离虚拟环境中安装 install/requirements-standard.txt")
    if not all(data_packages.values()) and profile != "lite":
        recommendations.append("安装缺失的数据格式依赖，以支持 Excel 和 Parquet")
    if not search_available:
        recommendations.append("确认宿主 Agent 是否提供 Web 搜索；需要 Tavily 时再配置 API Key")
    if not latex_available:
        recommendations.append("使用 Overleaf，或经用户确认后安装 TeX Live 与 biber")
    if update_info.get("available") and not update_info.get("up_to_date"):
        behind = update_info.get("behind", 0)
        recommendations.append(
            f"PaperPilot 有新版本（落后 {behind} 个提交），运行 git pull 更新 skills 和 pipeline"
        )

    required_ready = all(
        item["available"] and (item.get("supported", True))
        for item in capabilities.values()
        if item["required"]
    )

    return {
        "schema_version": "1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "status": "ready" if required_ready else "degraded",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "capabilities": capabilities,
        "recommendations": recommendations,
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"PaperPilot环境诊断：{report['status']} ({report['profile']})")
    for name, item in report["capabilities"].items():
        marker = "OK" if item["available"] else "--"
        required = " [必需]" if item["required"] else ""
        print(f"[{marker}] {name}{required}: {item['message']}")
    if report["recommendations"]:
        print("\n建议：")
        for recommendation in report["recommendations"]:
            print(f"- {recommendation}")


def main(argv: list[str] | None = None) -> int:
    import sys
    # Ensure stdout can handle UTF-8 (fixes Windows cp1252 crash)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="PaperPilot 无依赖环境诊断")
    parser.add_argument("--check", action="store_true", help="只检测环境，不安装或修改系统")
    parser.add_argument("--profile", choices=("lite", "standard", "full"), default="standard")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON 报告")
    args = parser.parse_args(argv)

    report = build_report(args.profile)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
