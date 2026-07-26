#!/usr/bin/env python3
"""
Test existing demo-paper artifacts against skill checks.

This validates that the current demo-paper output meets the quality
standards defined by the skill evaluation checks. It serves as a
regression test - if these fail, something broke.

Run with: pytest tests/skill_evals/test_demo_paper_artifacts.py -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tests.skill_evals.harness import SkillEvalHarness
from tests.skill_evals.checks import CheckRegistry

DEMO_PAPER = ROOT / "papers" / "demo-paper"


class DemoPaperArtifactTests(unittest.TestCase):
    """Validate demo-paper artifacts meet quality standards."""

    def setUp(self):
        self.registry = CheckRegistry()
        self.harness = SkillEvalHarness()
        
        # Load demo-paper artifacts
        self.artifacts = {}
        artifact_files = [
            ("literature_review", DEMO_PAPER / "literature" / "literature_review.md"),
            ("references_bib", DEMO_PAPER / "literature" / "references.bib"),
            ("research_proposal", DEMO_PAPER / "topics" / "00_research_proposal.md"),
            ("main_tex", DEMO_PAPER / "paper" / "main.tex"),
            ("introduction", DEMO_PAPER / "paper" / "sections" / "01_introduction.tex"),
            ("baseline_regression", DEMO_PAPER / "analysis" / "output" / "02_baseline_regression.tex"),
        ]
        
        for name, path in artifact_files:
            if path.exists():
                self.artifacts[name] = path.read_text(encoding="utf-8", errors="replace")

    # =========================================================================
    # Literature Survey Checks
    # =========================================================================
    
    def test_literature_review_has_content(self):
        """Literature review has meaningful content."""
        if "literature_review" not in self.artifacts:
            self.skipTest("literature_review.md not found")
        
        result = self.registry.run(
            "markdown_has_content",
            self.artifacts["literature_review"],
            {"min_chars": 500}
        )
        self.assertTrue(result.passed, result.message)

    def test_literature_review_bilingual(self):
        """Literature review covers Chinese and English sources."""
        if "literature_review" not in self.artifacts:
            self.skipTest("literature_review.md not found")
        
        result = self.registry.run(
            "lit_bilingual_search",
            self.artifacts["literature_review"],
            {}
        )
        self.assertTrue(result.passed, result.message)

    def test_references_bib_has_entries(self):
        """References.bib has bibliographic entries."""
        if "references_bib" not in self.artifacts:
            self.skipTest("references.bib not found")
        
        content = self.artifacts["references_bib"]
        # Count @article, @book, @inproceedings entries
        import re
        entries = len(re.findall(r"@\w+\{", content))
        self.assertGreaterEqual(entries, 5, f"Expected at least 5 bib entries, found {entries}")

    # =========================================================================
    # Paper Structure Checks
    # =========================================================================
    
    def test_paper_main_tex_valid(self):
        """main.tex has balanced LaTeX braces."""
        if "main_tex" not in self.artifacts:
            self.skipTest("main.tex not found")
        
        result = self.registry.run(
            "analysis_latex_valid",
            self.artifacts["main_tex"],
            {}
        )
        self.assertTrue(result.passed, result.message)

    def test_paper_has_sections(self):
        """Paper includes required sections."""
        if "main_tex" not in self.artifacts:
            self.skipTest("main.tex not found")
        
        content = self.artifacts["main_tex"]
        # Check for section includes or inline sections
        required = ["introduction", "literature", "empirical", "conclusion"]
        for section in required:
            self.assertIn(
                section.lower(),
                content.lower(),
                f"Section '{section}' not found in main.tex"
            )

    def test_paper_no_placeholders(self):
        """Paper has no placeholder text."""
        if "introduction" not in self.artifacts:
            self.skipTest("01_introduction.tex not found")
        
        result = self.registry.run(
            "paper_no_placeholders",
            self.artifacts["introduction"],
            {}
        )
        self.assertTrue(result.passed, result.message)

    def test_paper_has_citations(self):
        """Paper introduction has citations."""
        if "introduction" not in self.artifacts:
            self.skipTest("01_introduction.tex not found")
        
        result = self.registry.run(
            "paper_citations_exist",
            self.artifacts["introduction"],
            {"min_citations": 3}
        )
        self.assertTrue(result.passed, result.message)

    # =========================================================================
    # Empirical Analysis Checks
    # =========================================================================
    
    def test_baseline_regression_has_table(self):
        """Baseline regression output has table structure."""
        if "baseline_regression" not in self.artifacts:
            self.skipTest("02_baseline_regression.tex not found")
        
        result = self.registry.run(
            "analysis_has_regression_table",
            self.artifacts["baseline_regression"],
            {}
        )
        self.assertTrue(result.passed, result.message)

    def test_baseline_regression_latex_valid(self):
        """Baseline regression LaTeX is valid."""
        if "baseline_regression" not in self.artifacts:
            self.skipTest("02_baseline_regression.tex not found")
        
        result = self.registry.run(
            "analysis_latex_valid",
            self.artifacts["baseline_regression"],
            {}
        )
        self.assertTrue(result.passed, result.message)

    # =========================================================================
    # Research Proposal Checks
    # =========================================================================
    
    def test_research_proposal_has_content(self):
        """Research proposal has meaningful content."""
        if "research_proposal" not in self.artifacts:
            self.skipTest("00_research_proposal.md not found")
        
        result = self.registry.run(
            "markdown_has_content",
            self.artifacts["research_proposal"],
            {"min_chars": 200}
        )
        self.assertTrue(result.passed, result.message)


class DemoPaperDirectoryStructureTests(unittest.TestCase):
    """Validate demo-paper has expected directory structure."""

    def test_topics_directory_exists(self):
        """topics/ directory exists."""
        self.assertTrue((DEMO_PAPER / "topics").is_dir())

    def test_literature_directory_exists(self):
        """literature/ directory exists."""
        self.assertTrue((DEMO_PAPER / "literature").is_dir())

    def test_data_directory_exists(self):
        """data/ directory exists."""
        self.assertTrue((DEMO_PAPER / "data").is_dir())

    def test_analysis_directory_exists(self):
        """analysis/ directory exists."""
        self.assertTrue((DEMO_PAPER / "analysis").is_dir())

    def test_paper_directory_exists(self):
        """paper/ directory exists."""
        self.assertTrue((DEMO_PAPER / "paper").is_dir())

    def test_clean_data_exists(self):
        """Clean data file exists."""
        clean_dir = DEMO_PAPER / "data" / "clean"
        # Check for any data file (csv, dta, parquet)
        data_files = list(clean_dir.glob("*.csv")) + list(clean_dir.glob("*.dta")) + list(clean_dir.glob("*.parquet"))
        self.assertGreater(len(data_files), 0, "No clean data files found")


if __name__ == "__main__":
    unittest.main()
