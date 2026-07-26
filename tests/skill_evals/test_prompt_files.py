#!/usr/bin/env python3
"""
Test that all prompt files are valid and loadable.

Run with: pytest tests/skill_evals/test_prompt_files.py -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

PROMPTS_DIR = ROOT / "tests" / "skill_evals" / "prompts"


class PromptFileValidationTests(unittest.TestCase):
    """Validate all prompt files have correct structure."""

    def setUp(self):
        self.prompt_files = list(PROMPTS_DIR.glob("*.json"))

    def test_prompt_files_exist(self):
        """At least some prompt files exist."""
        self.assertGreater(len(self.prompt_files), 0, "No prompt files found")

    def test_all_prompt_files_valid_json(self):
        """All prompt files are valid JSON."""
        for path in self.prompt_files:
            with self.subTest(file=path.name):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    self.assertIsInstance(data, dict)
                except json.JSONDecodeError as e:
                    self.fail(f"{path.name} is not valid JSON: {e}")

    def test_all_prompt_files_have_required_fields(self):
        """All prompt files have skill and cases fields."""
        for path in self.prompt_files:
            with self.subTest(file=path.name):
                with open(path) as f:
                    data = json.load(f)
                
                self.assertIn("skill", data, f"{path.name} missing 'skill' field")
                self.assertIn("cases", data, f"{path.name} missing 'cases' field")
                self.assertIsInstance(data["cases"], list)
                self.assertGreater(len(data["cases"]), 0, f"{path.name} has no cases")

    def test_all_cases_have_required_fields(self):
        """All cases have id, prompt, expected_checks fields."""
        required_case_fields = ["id", "prompt", "expected_checks"]
        
        for path in self.prompt_files:
            with open(path) as f:
                data = json.load(f)
            
            for case in data["cases"]:
                with self.subTest(file=path.name, case=case.get("id", "unknown")):
                    for field in required_case_fields:
                        self.assertIn(
                            field, case,
                            f"Case '{case.get('id')}' missing '{field}'"
                        )

    def test_case_ids_unique_within_file(self):
        """Case IDs are unique within each file."""
        for path in self.prompt_files:
            with self.subTest(file=path.name):
                with open(path) as f:
                    data = json.load(f)
                
                ids = [c["id"] for c in data["cases"]]
                self.assertEqual(
                    len(ids), len(set(ids)),
                    f"Duplicate case IDs in {path.name}"
                )

    def test_negative_cases_have_should_trigger_false(self):
        """Cases with 'negative' in ID should have should_trigger=false."""
        for path in self.prompt_files:
            with open(path) as f:
                data = json.load(f)
            
            for case in data["cases"]:
                if "negative" in case["id"]:
                    with self.subTest(file=path.name, case=case["id"]):
                        self.assertFalse(
                            case.get("should_trigger", True),
                            f"Negative case '{case['id']}' should have should_trigger=false"
                        )


class PromptFileLoadTests(unittest.TestCase):
    """Test that harness can load all prompt files."""

    def test_harness_loads_all_prompts(self):
        """SkillEvalHarness can load all prompt files."""
        from tests.skill_evals.harness import SkillEvalHarness
        
        harness = SkillEvalHarness()
        harness.load_prompts_dir(PROMPTS_DIR)
        
        # Should have loaded multiple skills
        self.assertGreater(len(harness.cases), 0)
        
        # Check some expected skills are present
        expected_skills = ["literature-survey", "data-collector", "paper-writer"]
        for skill in expected_skills:
            self.assertIn(skill, harness.cases, f"Missing skill: {skill}")

    def test_expected_checks_are_registered(self):
        """All expected_checks reference registered check functions."""
        from tests.skill_evals.harness import SkillEvalHarness
        from tests.skill_evals.checks import CheckRegistry
        
        registry = CheckRegistry()
        
        for path in PROMPTS_DIR.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
            
            for case in data["cases"]:
                for check_id in case["expected_checks"]:
                    with self.subTest(file=path.name, case=case["id"], check=check_id):
                        check_fn = registry.get(check_id)
                        self.assertIsNotNone(
                            check_fn,
                            f"Unknown check '{check_id}' in {path.name}:{case['id']}"
                        )


if __name__ == "__main__":
    unittest.main()
