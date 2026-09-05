#!/usr/bin/env python3
"""Tests for the agent guide interface."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.skill_guide import get_agent_guide


class AgentGuideTests(unittest.TestCase):
    def test_guide_returns_required_fields(self):
        guide = get_agent_guide(
            completed_skill="topic-explorer",
            artifacts=["topics/00_research_proposal.md"],
            context_written=["research_question", "y_var"],
        )
        self.assertEqual(guide["completed"], "topic-explorer")
        self.assertIn("topics/00_research_proposal.md", guide["artifacts"])
        self.assertIn("research_question", guide["context_written"])
        self.assertIsInstance(guide["next_steps"], list)
        self.assertIsInstance(guide["warnings"], list)

    def test_guide_recommends_next_skills_by_order(self):
        guide = get_agent_guide(
            completed_skill="topic-explorer",
            artifacts=[],
        )
        skill_names = [s["skill"] for s in guide["next_steps"]]
        self.assertIn("paper-search", skill_names)
        self.assertNotIn("empirical-analysis", skill_names)

    def test_guide_all_core_skills_ready(self):
        guide = get_agent_guide(
            completed_skill="data-collector",
            artifacts=["data/data_report.md"],
        )
        for step in guide["next_steps"]:
            self.assertTrue(step.get("ready", True))

    def test_guide_with_project_dir_uses_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Create minimal evidence for research question
            (root / "topics").mkdir()
            (root / "topics" / "00_research_proposal.md").write_text(
                "研究问题：AI对就业影响\nY: employment\nD: ai_adoption\n识别策略: FE",
                encoding="utf-8",
            )
            state = {
                "context_store": {
                    "research_question": "AI对就业影响",
                    "y_var": "employment",
                    "d_var": "ai_adoption",
                    "identification": "FE",
                }
            }
            (root / "pipeline_state.json").write_text(
                json.dumps(state), encoding="utf-8"
            )

            guide = get_agent_guide(
                completed_skill="topic-explorer",
                artifacts=["topics/00_research_proposal.md"],
                project_dir=root,
            )
            self.assertIn("project_readiness", guide)
            self.assertGreater(len(guide["next_steps"]), 0)
            # Research question is done, so next should be literature or data
            first_skill = guide["next_steps"][0]["skill"]
            self.assertIn(first_skill, ["paper-search", "literature-survey", "literature-review", "data-collector"])

    def test_guide_limits_to_3_recommendations(self):
        guide = get_agent_guide(
            completed_skill="topic-explorer",
            artifacts=[],
        )
        self.assertLessEqual(len(guide["next_steps"]), 3)

    def test_guide_includes_warnings(self):
        guide = get_agent_guide(
            completed_skill="literature-survey",
            artifacts=["literature/review.md"],
            warnings=["3 条引用未验证"],
        )
        self.assertIn("3 条引用未验证", guide["warnings"])


if __name__ == "__main__":
    unittest.main()
