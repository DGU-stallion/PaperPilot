#!/usr/bin/env python3
"""
Golden Paper Artifact Validation Tests

These tests validate that skill artifacts meet quality standards.
They complement test_golden_path.py (which tests the workflow engine)
by checking the quality of produced artifacts.

Run with: pytest tests/e2e/test_golden_paper.py -v --tb=short
"""

from __future__ import annotations

import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tests.skill_evals.checks import CheckRegistry


class GoldenPaperArtifactValidationTest(unittest.TestCase):
    """
    Validate that golden path produces correct artifacts.
    
    This creates mock artifacts and validates them against the check registry.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project_dir = Path(self.tmp) / "artifact-test"
        self.project_dir.mkdir()
        self.registry = CheckRegistry()
        
        # Create directory structure
        (self.project_dir / "topics").mkdir()
        (self.project_dir / "literature").mkdir()
        (self.project_dir / "analysis" / "output").mkdir(parents=True)
        (self.project_dir / "paper" / "sections").mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_research_proposal_artifact(self):
        """Research proposal artifact is valid markdown."""
        proposal_path = self.project_dir / "topics" / "00_research_proposal.md"
        proposal_path.write_text("""
# 研究提案：数字化转型与企业就业

## 研究问题
数字化转型是否提升制造业企业就业水平？

## 核心变量
- Y: employment（就业人数）
- D: digital_index（数字化指数）

## 识别策略
固定效应模型（FE）
""")
        
        content = proposal_path.read_text()
        result = self.registry.run("markdown_has_content", content, {"min_chars": 50})
        self.assertTrue(result.passed, result.message)

    def test_regression_table_artifact(self):
        """Regression table artifact is valid LaTeX."""
        table_path = self.project_dir / "analysis" / "output" / "baseline.tex"
        table_path.write_text(r"""
\begin{table}[htbp]
\centering
\caption{基准回归结果}
\begin{tabular}{lcc}
\hline
 & (1) & (2) \\
\hline
digital\_index & 0.150*** & 0.142*** \\
 & (0.050) & (0.048) \\
\hline
N & 1500 & 1500 \\
\hline
\end{tabular}
\end{table}
""")
        
        content = table_path.read_text()
        
        # Check table structure
        result = self.registry.run("analysis_has_regression_table", content, {})
        self.assertTrue(result.passed, result.message)
        
        # Check LaTeX validity
        result = self.registry.run("analysis_latex_valid", content, {})
        self.assertTrue(result.passed, result.message)

    def test_literature_review_artifact(self):
        """Literature review has proper structure."""
        review_path = self.project_dir / "literature" / "literature_review.md"
        review_path.write_text("""
# 文献综述

## 1. 数字化转型的概念与测度

Digital transformation is widely studied. Acemoglu and Restrepo（2018）建立了自动化任务模型。
赵涛等（2020）使用数字普惠金融指数。

## 2. 数字化与就业的关系

已有研究分为两类：
- 替代效应：Autor（2015）指出技术替代劳动
- 补偿效应：创造新岗位

## 3. 研究空白

现有研究不足在于：
1. 时间窗口未覆盖后疫情时期
2. 缺乏非线性效应分析

### 参考文献

- https://doi.org/10.1234/example1
- https://doi.org/10.5678/example2
- 10.9999/sample-doi
""")
        
        content = review_path.read_text()
        
        # Check has meaningful content
        result = self.registry.run("markdown_has_content", content, {"min_chars": 200})
        self.assertTrue(result.passed, result.message)
        
        # Check bilingual
        result = self.registry.run("lit_bilingual_search", content, {})
        self.assertTrue(result.passed, result.message)
        
        # Check has URLs
        result = self.registry.run("lit_has_urls", content, {"min_urls": 2})
        self.assertTrue(result.passed, result.message)

    def test_paper_section_no_placeholders(self):
        """Paper section has no placeholder text."""
        section_path = self.project_dir / "paper" / "sections" / "01_intro.tex"
        section_path.write_text(r"""
\section{引言}

本文研究数字化转型对制造业企业就业的影响。
研究问题具有重要的理论和政策意义。

\subsection{研究背景}

数字经济快速发展，对就业市场产生深远影响。
""")
        
        content = section_path.read_text()
        result = self.registry.run("paper_no_placeholders", content, {})
        self.assertTrue(result.passed, result.message)

    def test_paper_section_with_placeholders_fails(self):
        """Paper section with placeholders should fail check."""
        section_path = self.project_dir / "paper" / "sections" / "02_lit.tex"
        section_path.write_text(r"""
\section{文献综述}

[TODO] 补充文献综述内容

[待补充] 添加更多引用

XXX 这里需要修改
""")
        
        content = section_path.read_text()
        result = self.registry.run("paper_no_placeholders", content, {})
        self.assertFalse(result.passed, "Should detect placeholders")

    def test_citation_check_various_formats(self):
        """Citation check handles multiple formats."""
        content = r"""
引用格式测试：

1. 中文括号：Acemoglu和Restrepo（2018, 2019）
2. 中文作者：赵涛等（2020）
3. LaTeX: \cite{author2021}
4. 行内：Hansen (1999) proposed...
"""
        result = self.registry.run("paper_citations_exist", content, {"min_citations": 3})
        self.assertTrue(result.passed, result.message)
        self.assertGreaterEqual(result.details.get("inline_citations", 0) + 
                                result.details.get("chinese_inline", 0) +
                                result.details.get("latex_citations", 0), 3)


class CheckRegistryUnitTests(unittest.TestCase):
    """Unit tests for individual check functions."""

    def setUp(self):
        self.registry = CheckRegistry()

    def test_lit_has_papers_table_format(self):
        """Papers check works with markdown table."""
        content = """
| 序号 | 论文标题 | 作者 |
|------|---------|------|
| 1 | Paper A | Author 1 |
| 2 | Paper B | Author 2 |
| 3 | Paper C | Author 3 |
"""
        result = self.registry.run("lit_has_papers", content, {"min_papers": 2})
        self.assertTrue(result.passed, result.message)

    def test_lit_has_papers_list_format(self):
        """Papers check works with numbered list."""
        content = """
1. Paper A by Author 1
2. Paper B by Author 2
3. Paper C by Author 3
"""
        result = self.registry.run("lit_has_papers", content, {"min_papers": 2})
        self.assertTrue(result.passed, result.message)

    def test_data_has_source_patterns(self):
        """Data source check recognizes various patterns."""
        patterns_to_test = [
            "数据来源：国家统计局",
            "Data source: World Bank",
            "使用中国统计年鉴数据",
            "从 CSMAR 数据库获取",
            "数据下载自 https://data.gov",
        ]
        
        for pattern in patterns_to_test:
            result = self.registry.run("data_has_source", pattern, {})
            self.assertTrue(result.passed, f"Should match: {pattern}")

    def test_json_valid_check(self):
        """JSON validation check."""
        valid_json = '{"key": "value", "number": 42}'
        invalid_json = '{"key": value}'
        
        result = self.registry.run("json_valid", valid_json, {})
        self.assertTrue(result.passed)
        
        result = self.registry.run("json_valid", invalid_json, {})
        self.assertFalse(result.passed)

    def test_latex_brace_balance(self):
        """LaTeX brace balance check."""
        balanced = r"\begin{table} \end{table}"
        unbalanced = r"\begin{table} {extra"
        
        result = self.registry.run("analysis_latex_valid", balanced, {})
        self.assertTrue(result.passed)
        
        result = self.registry.run("analysis_latex_valid", unbalanced, {})
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
