"""
Skill Evaluation Harness

Provides a framework for running skill evaluations:
1. Load prompt sets (test cases)
2. Run checks against artifacts
3. Aggregate results and report

This is a lightweight alternative to external eval frameworks,
tailored for PaperPilot's research workflow skills.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .checks import CheckRegistry, CheckResult


@dataclass
class EvalCase:
    """A single evaluation test case."""
    id: str
    description: str
    skill: str
    prompt: str
    expected_checks: list[str]
    should_trigger: bool = True
    context: dict = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> "EvalCase":
        return cls(
            id=data["id"],
            description=data.get("description", ""),
            skill=data["skill"],
            prompt=data["prompt"],
            expected_checks=data.get("expected_checks", []),
            should_trigger=data.get("should_trigger", True),
            context=data.get("context", {}),
        )


@dataclass
class EvalResult:
    """Result of evaluating a single test case."""
    case_id: str
    skill: str
    passed: bool
    checks: list[CheckResult]
    duration_ms: float
    error: Optional[str] = None
    
    @property
    def check_summary(self) -> str:
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        return f"{passed}/{total} checks passed"


@dataclass
class EvalReport:
    """Aggregated evaluation report."""
    skill: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[EvalResult]
    duration_ms: float
    
    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed_cases / self.total_cases
    
    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "pass_rate": round(self.pass_rate * 100, 1),
            "duration_ms": round(self.duration_ms, 2),
            "results": [
                {
                    "case_id": r.case_id,
                    "passed": r.passed,
                    "check_summary": r.check_summary,
                    "error": r.error,
                }
                for r in self.results
            ],
        }
    
    def summary(self) -> str:
        status = "✓" if self.pass_rate == 100 else "✗"
        return (
            f"{status} {self.skill}: {self.pass_rate:.1f}% pass rate "
            f"({self.passed_cases}/{self.total_cases} cases, {self.duration_ms:.0f}ms)"
        )


class SkillEvalHarness:
    """
    Harness for running skill evaluations.
    
    Usage:
        harness = SkillEvalHarness()
        harness.load_prompts("tests/skill_evals/prompts/literature_survey.json")
        
        # For artifact-based evaluation (no agent call):
        report = harness.evaluate_artifacts(
            skill="literature-survey",
            artifacts={"literature_review": review_content, "candidate_papers": papers_content}
        )
        
        # For full simulation (requires agent):
        report = harness.evaluate_with_agent(skill="literature-survey", agent_fn=run_agent)
    """
    
    def __init__(self):
        self.registry = CheckRegistry()
        self.cases: dict[str, list[EvalCase]] = {}  # skill -> cases
    
    def load_prompts(self, path: str | Path) -> None:
        """Load prompt set from JSON file."""
        path = Path(path)
        with open(path) as f:
            data = json.load(f)
        
        skill = data.get("skill", path.stem)
        cases = [EvalCase.from_dict(c) for c in data.get("cases", [])]
        
        if skill not in self.cases:
            self.cases[skill] = []
        self.cases[skill].extend(cases)
    
    def load_prompts_dir(self, directory: str | Path) -> None:
        """Load all prompt sets from a directory."""
        directory = Path(directory)
        for path in directory.glob("*.json"):
            self.load_prompts(path)
    
    def evaluate_artifacts(
        self,
        skill: str,
        artifacts: dict[str, str],
        case_filter: Optional[list[str]] = None,
    ) -> EvalReport:
        """
        Evaluate skill output artifacts against expected checks.
        
        Args:
            skill: Skill name
            artifacts: Dict of artifact_name -> content
            case_filter: Optional list of case IDs to run (runs all if None)
        
        Returns:
            EvalReport with aggregated results
        """
        cases = self.cases.get(skill, [])
        if case_filter:
            cases = [c for c in cases if c.id in case_filter]
        
        results = []
        start_time = time.time()
        
        for case in cases:
            result = self._run_case(case, artifacts)
            results.append(result)
        
        total_time = (time.time() - start_time) * 1000
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        return EvalReport(
            skill=skill,
            total_cases=len(results),
            passed_cases=passed,
            failed_cases=failed,
            results=results,
            duration_ms=total_time,
        )
    
    def _run_case(self, case: EvalCase, artifacts: dict[str, str]) -> EvalResult:
        """Run a single test case."""
        start = time.time()
        checks = []
        
        try:
            # Combine all artifacts into one content string for checks
            # In practice, specific checks may need specific artifacts
            combined_content = "\n\n".join(artifacts.values())
            
            for check_id in case.expected_checks:
                # Merge case context with check-specific context
                context = {**case.context}
                result = self.registry.run(check_id, combined_content, context)
                checks.append(result)
            
            all_passed = all(c.passed for c in checks)
            
            return EvalResult(
                case_id=case.id,
                skill=case.skill,
                passed=all_passed,
                checks=checks,
                duration_ms=(time.time() - start) * 1000,
            )
        
        except Exception as e:
            return EvalResult(
                case_id=case.id,
                skill=case.skill,
                passed=False,
                checks=checks,
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )
    
    def create_prompt_template(self, skill: str, output_path: str | Path) -> None:
        """Generate a template prompt set file for a skill."""
        template = {
            "skill": skill,
            "description": f"Evaluation cases for {skill}",
            "cases": [
                {
                    "id": f"{skill}_basic_1",
                    "description": "Basic functionality test",
                    "skill": skill,
                    "prompt": "Example prompt for the skill",
                    "expected_checks": ["markdown_has_content"],
                    "should_trigger": True,
                    "context": {},
                },
                {
                    "id": f"{skill}_negative_1",
                    "description": "Negative test - should NOT trigger",
                    "skill": skill,
                    "prompt": "Unrelated prompt that should not trigger this skill",
                    "expected_checks": [],
                    "should_trigger": False,
                    "context": {},
                },
            ],
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
