#!/usr/bin/env python3
"""Agent Guide interface — structured next-step recommendations.

Each skill execution returns an agent_guide dict that the meta-skill
(paper-agent) uses to recommend the next action to the user.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.paper_state import scan_project

# Skill ordering for recommendations
SKILL_ORDER = [
    "topic-explorer",
    "paper-search",
    "literature-review",
    "data-collector",
    "paper-writer",
    "integrity-auditor",
]

# Map skill → dimension in paper_state scanner
SKILL_TO_DIMENSION = {
    "topic-explorer": "research_question",
    "paper-search": "literature",
    "literature-review": "literature",
    "data-collector": "data",
    "paper-writer": "writing",
    "integrity-auditor": "reproducibility",
}

# Skills that require optional dependencies
OPTIONAL_SKILLS: dict[str, dict[str, str]] = {}


def _is_skill_ready(skill_name: str) -> bool:
    """Check if an optional skill has its dependencies installed."""
    if skill_name not in OPTIONAL_SKILLS:
        return True
    import importlib.util
    pkg = OPTIONAL_SKILLS[skill_name]["check"]
    return importlib.util.find_spec(pkg) is not None


def get_agent_guide(
    completed_skill: str,
    artifacts: list[str],
    context_written: list[str] | None = None,
    project_dir: Path | str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a structured agent guide after skill completion.

    Args:
        completed_skill: Name of the skill that just finished.
        artifacts: Relative paths of produced files.
        context_written: Context store keys that were written.
        project_dir: Project root (for state inspection).
        warnings: Any warnings to surface.

    Returns:
        Structured guide dict with next_steps recommendations.
    """
    guide: dict[str, Any] = {
        "completed": completed_skill,
        "artifacts": artifacts,
        "context_written": context_written or [],
        "next_steps": [],
        "warnings": warnings or [],
    }

    # If we have a project dir, use state to determine readiness
    if project_dir:
        try:
            report = scan_project(project_dir)
            guide["project_readiness"] = report["overall_readiness"]

            # Find skills whose dimensions are not ready
            for skill in SKILL_ORDER:
                if skill == completed_skill:
                    continue
                dim_name = SKILL_TO_DIMENSION.get(skill)
                if not dim_name:
                    continue
                dim = report["dimensions"].get(dim_name, {})
                if dim.get("status") == "ready":
                    continue

                ready = _is_skill_ready(skill)
                step: dict[str, Any] = {
                    "skill": skill,
                    "reason": dim.get("blockers", ["证据不足"])[0] if dim.get("blockers") else "可以推进",
                    "ready": ready,
                }
                if not ready:
                    step["install_hint"] = OPTIONAL_SKILLS.get(skill, {}).get("install_hint", "")
                guide["next_steps"].append(step)

                if len(guide["next_steps"]) >= 3:
                    break
        except Exception:
            pass

    # Fallback: if no project-based recommendations, use ordering
    if not guide["next_steps"]:
        try:
            current_idx = SKILL_ORDER.index(completed_skill)
        except ValueError:
            current_idx = -1

        for skill in SKILL_ORDER[current_idx + 1:]:
            ready = _is_skill_ready(skill)
            step = {
                "skill": skill,
                "reason": "按研究流程顺序推进",
                "ready": ready,
            }
            if not ready:
                step["install_hint"] = OPTIONAL_SKILLS.get(skill, {}).get("install_hint", "")
            guide["next_steps"].append(step)
            if len(guide["next_steps"]) >= 3:
                break

    return guide
