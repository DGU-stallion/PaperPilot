"""
PaperPilot Skill Evaluation Framework

This module provides a lightweight harness for testing skills:
1. Prompt-based evaluation: Does the skill trigger correctly?
2. Deterministic checks: Does the output meet structural requirements?
3. Golden path tests: Does the full workflow produce valid artifacts?

Based on industry best practices from:
- Addy Osmani's agent-skills (process over prose, anti-rationalization)
- Philipp Schmid's testing-skills (prompt sets, deterministic checks)
- Microsoft Vally (lint + eval separation)
"""

from .harness import SkillEvalHarness, EvalResult, EvalReport, EvalCase
from .checks import CheckRegistry, CheckResult

__all__ = ["SkillEvalHarness", "EvalResult", "CheckResult", "CheckRegistry"]
