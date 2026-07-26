"""
Deterministic check functions for skill evaluation.

Each check is a pure function: (artifact_content, context) -> CheckResult
Checks should be fast, repeatable, and not require LLM calls.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class CheckResult:
    """Result of a single deterministic check."""
    passed: bool
    check_id: str
    message: str
    details: Optional[dict] = None


# Type alias for check functions
CheckFn = Callable[[str, dict], CheckResult]


class CheckRegistry:
    """Registry of all available checks, organized by skill."""
    
    def __init__(self):
        self._checks: dict[str, CheckFn] = {}
        self._register_builtin_checks()
    
    def register(self, check_id: str, fn: CheckFn) -> None:
        """Register a check function."""
        self._checks[check_id] = fn
    
    def get(self, check_id: str) -> Optional[CheckFn]:
        """Get a check function by ID."""
        return self._checks.get(check_id)
    
    def run(self, check_id: str, content: str, context: dict) -> CheckResult:
        """Run a check and return the result."""
        fn = self.get(check_id)
        if fn is None:
            return CheckResult(
                passed=False,
                check_id=check_id,
                message=f"Unknown check: {check_id}",
            )
        try:
            return fn(content, context)
        except Exception as e:
            return CheckResult(
                passed=False,
                check_id=check_id,
                message=f"Check failed with error: {e}",
            )
    
    def _register_builtin_checks(self) -> None:
        """Register all built-in checks."""
        # Literature survey checks
        self.register("lit_has_papers", check_lit_has_papers)
        self.register("lit_has_urls", check_lit_has_urls)
        self.register("lit_has_verification_status", check_lit_has_verification_status)
        self.register("lit_bilingual_search", check_lit_bilingual_search)
        
        # Data collector checks
        self.register("data_has_source", check_data_has_source)
        self.register("data_has_variables", check_data_has_variables)
        
        # Empirical analysis checks
        self.register("analysis_has_regression_table", check_analysis_has_regression_table)
        self.register("analysis_latex_valid", check_analysis_latex_valid)
        
        # Paper writer checks
        self.register("paper_has_sections", check_paper_has_sections)
        self.register("paper_no_placeholders", check_paper_no_placeholders)
        self.register("paper_citations_exist", check_paper_citations_exist)
        
        # General checks
        self.register("file_exists", check_file_exists)
        self.register("json_valid", check_json_valid)
        self.register("markdown_has_content", check_markdown_has_content)


# =============================================================================
# Literature Survey Checks
# =============================================================================

def check_lit_has_papers(content: str, context: dict) -> CheckResult:
    """Check that literature list contains at least N papers."""
    min_papers = context.get("min_papers", 10)
    
    # Count markdown table rows or numbered list items
    table_rows = len(re.findall(r"^\|[^|]+\|", content, re.MULTILINE))
    list_items = len(re.findall(r"^\d+\.\s+", content, re.MULTILINE))
    
    paper_count = max(table_rows - 1, list_items)  # -1 for header row
    passed = paper_count >= min_papers
    
    return CheckResult(
        passed=passed,
        check_id="lit_has_papers",
        message=f"Found {paper_count} papers (minimum: {min_papers})",
        details={"paper_count": paper_count, "min_required": min_papers},
    )


def check_lit_has_urls(content: str, context: dict) -> CheckResult:
    """Check that papers have URLs or DOIs."""
    # Match URLs (http/https) or DOIs
    urls = re.findall(r"https?://[^\s\)]+", content)
    dois = re.findall(r"10\.\d{4,}/[^\s\)]+", content)
    
    total = len(urls) + len(dois)
    min_urls = context.get("min_urls", 5)
    passed = total >= min_urls
    
    return CheckResult(
        passed=passed,
        check_id="lit_has_urls",
        message=f"Found {len(urls)} URLs and {len(dois)} DOIs (minimum: {min_urls})",
        details={"url_count": len(urls), "doi_count": len(dois)},
    )


def check_lit_has_verification_status(content: str, context: dict) -> CheckResult:
    """Check that papers have verification status markers."""
    # Look for verification markers: ✓, △, ✗, 已验证, 单源, 存疑
    verified = len(re.findall(r"[✓✔]|已验证|verified", content, re.IGNORECASE))
    single_source = len(re.findall(r"[△]|单源|single.?source", content, re.IGNORECASE))
    unverified = len(re.findall(r"[✗✘]|存疑|unverified", content, re.IGNORECASE))
    
    total = verified + single_source + unverified
    passed = total > 0
    
    return CheckResult(
        passed=passed,
        check_id="lit_has_verification_status",
        message=f"Found {total} verification markers (✓:{verified} △:{single_source} ✗:{unverified})",
        details={"verified": verified, "single_source": single_source, "unverified": unverified},
    )


def check_lit_bilingual_search(content: str, context: dict) -> CheckResult:
    """Check that search covered both Chinese and English."""
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", content))
    has_english = bool(re.search(r"[a-zA-Z]{5,}", content))
    
    passed = has_chinese and has_english
    
    return CheckResult(
        passed=passed,
        check_id="lit_bilingual_search",
        message=f"Chinese: {'✓' if has_chinese else '✗'}, English: {'✓' if has_english else '✗'}",
        details={"has_chinese": has_chinese, "has_english": has_english},
    )


# =============================================================================
# Data Collector Checks
# =============================================================================

def check_data_has_source(content: str, context: dict) -> CheckResult:
    """Check that data source is documented."""
    # Look for common data source indicators
    patterns = [
        r"数据来源|data\s*source",
        r"统计局|yearbook|年鉴",
        r"CSMAR|Wind|CNKI|CCER",
        r"https?://",
    ]
    
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    
    return CheckResult(
        passed=found,
        check_id="data_has_source",
        message="Data source documented" if found else "No data source found",
    )


def check_data_has_variables(content: str, context: dict) -> CheckResult:
    """Check that key variables are defined."""
    required_vars = context.get("required_vars", [])
    if not required_vars:
        return CheckResult(
            passed=True,
            check_id="data_has_variables",
            message="No required variables specified",
        )
    
    found = [v for v in required_vars if v.lower() in content.lower()]
    missing = [v for v in required_vars if v.lower() not in content.lower()]
    
    passed = len(missing) == 0
    
    return CheckResult(
        passed=passed,
        check_id="data_has_variables",
        message=f"Found {len(found)}/{len(required_vars)} required variables",
        details={"found": found, "missing": missing},
    )


# =============================================================================
# Empirical Analysis Checks
# =============================================================================

def check_analysis_has_regression_table(content: str, context: dict) -> CheckResult:
    """Check that output contains regression table structure."""
    # Look for LaTeX table markers or common regression output patterns
    has_tabular = "\\begin{tabular}" in content or "\\begin{table}" in content
    has_coefficients = bool(re.search(r"\(\d+\.\d+\)|[\d.]+\*{1,3}", content))
    
    passed = has_tabular or has_coefficients
    
    return CheckResult(
        passed=passed,
        check_id="analysis_has_regression_table",
        message="Regression table structure found" if passed else "No regression table found",
        details={"has_tabular": has_tabular, "has_coefficients": has_coefficients},
    )


def check_analysis_latex_valid(content: str, context: dict) -> CheckResult:
    """Check that LaTeX content has balanced braces."""
    open_braces = content.count("{")
    close_braces = content.count("}")
    
    passed = open_braces == close_braces
    
    return CheckResult(
        passed=passed,
        check_id="analysis_latex_valid",
        message=f"LaTeX braces balanced" if passed else f"Unbalanced braces: {open_braces} open, {close_braces} close",
        details={"open": open_braces, "close": close_braces},
    )


# =============================================================================
# Paper Writer Checks
# =============================================================================

def check_paper_has_sections(content: str, context: dict) -> CheckResult:
    """Check that paper has required sections."""
    required_sections = context.get("required_sections", [
        "引言|introduction",
        "文献|literature",
        "方法|model|methodology",
        "结果|result|empirical",
        "结论|conclusion",
    ])
    
    found = []
    missing = []
    for section in required_sections:
        if re.search(section, content, re.IGNORECASE):
            found.append(section)
        else:
            missing.append(section)
    
    passed = len(missing) == 0
    
    return CheckResult(
        passed=passed,
        check_id="paper_has_sections",
        message=f"Found {len(found)}/{len(required_sections)} required sections",
        details={"found": found, "missing": missing},
    )


def check_paper_no_placeholders(content: str, context: dict) -> CheckResult:
    """Check that paper has no placeholder text."""
    placeholders = [
        r"\[TODO\]",
        r"\[待补充\]",
        r"\[PLACEHOLDER\]",
        r"XXX",
        r"\[插入.*\]",
        r"\[此处.*\]",
    ]
    
    found = []
    for p in placeholders:
        matches = re.findall(p, content, re.IGNORECASE)
        found.extend(matches)
    
    passed = len(found) == 0
    
    return CheckResult(
        passed=passed,
        check_id="paper_no_placeholders",
        message=f"No placeholders found" if passed else f"Found {len(found)} placeholders",
        details={"placeholders": found[:10]},  # Limit to first 10
    )


def check_paper_citations_exist(content: str, context: dict) -> CheckResult:
    """Check that paper has citations."""
    # LaTeX citations
    latex_cites = re.findall(r"\\cite\{[^}]+\}", content)
    # Markdown/text citations like (Author, 2024)
    text_cites = re.findall(r"\([A-Z][a-z]+(?:\s+(?:et\s+al\.|and|&)\s+[A-Z][a-z]+)?,?\s*\d{4}\)", content)
    # Chinese-style citations with full-width parens: （Author, Year） or （中文，2024）
    chinese_cites = re.findall(r"（[A-Za-z\u4e00-\u9fff]+(?:\s+(?:et\s+al\.|and|&|和|等)\s*[A-Za-z\u4e00-\u9fff]*)?[，,]?\s*\d{4}[a-z]?）", content)
    # In-text style: Author (Year) or Author（Year）or 中文作者（Year）
    inline_cites = re.findall(r"[A-Z][a-z]+(?:\s+(?:et\s+al\.|and|&|和)\s+[A-Z][a-z]+)?[（(]\d{4}[a-z]?(?:[,，]\s*\d{4}[a-z]?)*[）)]", content)
    # Chinese author style: 中文（年份）
    chinese_inline = re.findall(r"[\u4e00-\u9fff]+[（(]\d{4}[）)]", content)
    
    total = len(latex_cites) + len(text_cites) + len(chinese_cites) + len(inline_cites) + len(chinese_inline)
    min_citations = context.get("min_citations", 5)
    passed = total >= min_citations
    
    return CheckResult(
        passed=passed,
        check_id="paper_citations_exist",
        message=f"Found {total} citations (minimum: {min_citations})",
        details={
            "latex_citations": len(latex_cites),
            "text_citations": len(text_cites),
            "chinese_citations": len(chinese_cites),
            "inline_citations": len(inline_cites),
            "chinese_inline": len(chinese_inline),
        },
    )


# =============================================================================
# General Checks
# =============================================================================

def check_file_exists(content: str, context: dict) -> CheckResult:
    """Check that a file exists at the given path."""
    path = context.get("path")
    if not path:
        return CheckResult(False, "file_exists", "No path specified")
    
    exists = Path(path).exists()
    
    return CheckResult(
        passed=exists,
        check_id="file_exists",
        message=f"File exists: {path}" if exists else f"File not found: {path}",
    )


def check_json_valid(content: str, context: dict) -> CheckResult:
    """Check that content is valid JSON."""
    try:
        json.loads(content)
        return CheckResult(True, "json_valid", "Valid JSON")
    except json.JSONDecodeError as e:
        return CheckResult(False, "json_valid", f"Invalid JSON: {e}")


def check_markdown_has_content(content: str, context: dict) -> CheckResult:
    """Check that markdown file has meaningful content."""
    # Remove whitespace and count remaining characters
    stripped = re.sub(r"\s+", "", content)
    min_chars = context.get("min_chars", 100)
    
    passed = len(stripped) >= min_chars
    
    return CheckResult(
        passed=passed,
        check_id="markdown_has_content",
        message=f"Content length: {len(stripped)} chars (minimum: {min_chars})",
    )
