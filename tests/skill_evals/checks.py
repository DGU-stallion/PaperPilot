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
        # Topic explorer checks
        self.register("topic_has_research_question", check_topic_has_research_question)
        self.register("topic_question_is_explanatory", check_topic_question_is_explanatory)
        self.register("topic_has_puzzle", check_topic_has_puzzle)
        self.register("topic_has_story_line", check_topic_has_story_line)
        self.register("topic_has_boundary", check_topic_has_boundary)
        self.register("topic_has_feasibility", check_topic_has_feasibility)

        # Literature survey checks
        self.register("lit_has_papers", check_lit_has_papers)
        self.register("lit_has_urls", check_lit_has_urls)
        self.register("lit_has_verification_status", check_lit_has_verification_status)
        self.register("lit_bilingual_search", check_lit_bilingual_search)
        
        # Data collector checks
        self.register("data_has_source", check_data_has_source)
        self.register("data_has_variables", check_data_has_variables)
        self.register("data_mode_declared", check_data_mode_declared)
        self.register("data_has_triangle_verification", check_data_has_triangle_verification)
        self.register("data_no_exec_details", check_data_no_exec_details)

        # Empirical analysis checks
        self.register("analysis_has_regression_table", check_analysis_has_regression_table)
        self.register("analysis_latex_valid", check_analysis_latex_valid)
        self.register("analysis_has_parallel_trend", check_analysis_has_parallel_trend)
        self.register("analysis_has_full_sample", check_analysis_has_full_sample)
        
        # Paper writer checks
        self.register("paper_has_sections", check_paper_has_sections)
        self.register("paper_no_placeholders", check_paper_no_placeholders)
        self.register("paper_citations_exist", check_paper_citations_exist)
        self.register("paper_no_ai_patterns", check_paper_no_ai_patterns)
        self.register("paper_numbers_traceable", check_paper_numbers_traceable)

        # Integrity auditor checks
        self.register("audit_has_verification_status", check_audit_has_verification_status)
        self.register("audit_has_numerical_check", check_audit_has_numerical_check)
        self.register("audit_uses_shared_ai_patterns", check_audit_uses_shared_ai_patterns)
        self.register("audit_no_auto_delete", check_audit_no_auto_delete)

        # General checks
        self.register("file_exists", check_file_exists)
        self.register("json_valid", check_json_valid)
        self.register("markdown_has_content", check_markdown_has_content)


# =============================================================================
# Topic Explorer Checks
# =============================================================================

def check_topic_has_research_question(content: str, context: dict) -> CheckResult:
    """Check that the proposal contains a clear research question section."""
    patterns = [
        r"研究问题",
        r"research question",
        r"核心问题",
        r"本文.*研究",
        r"本文.*解释",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="topic_has_research_question",
        message="Research question section found" if found else "No research question section found",
    )


def check_topic_question_is_explanatory(content: str, context: dict) -> CheckResult:
    """Check that the research question is explanatory/mechanistic, not merely descriptive.

    Looks for 'why/how/mechanism/condition' framing rather than 'what/describe/how to'.
    """
    # Positive signals: explanatory / mechanistic framing
    explanatory_patterns = [
        r"为什么",
        r"通过什么.*机制",
        r"什么条件",
        r"如何.*转化",
        r"why\b",
        r"mechanism",
        r"how.*lead",
        r"under what condition",
        r"驱动因素",
        r"形成机制",
        r"影响机制",
    ]
    # Negative signals: purely descriptive framing
    descriptive_patterns = [
        r"如何.*实现.*路径",   # "如何实现XX路径" — descriptive
        r"发展历程",
        r"做了什么",
    ]

    has_explanatory = any(re.search(p, content, re.IGNORECASE) for p in explanatory_patterns)
    has_descriptive_only = (
        not has_explanatory
        and any(re.search(p, content, re.IGNORECASE) for p in descriptive_patterns)
    )

    passed = has_explanatory and not has_descriptive_only

    if has_explanatory:
        msg = "Research question appears explanatory/mechanistic"
    elif has_descriptive_only:
        msg = "Research question appears purely descriptive — should be upgraded to explanatory"
    else:
        msg = "Could not determine question type — check manually"

    return CheckResult(
        passed=passed,
        check_id="topic_question_is_explanatory",
        message=msg,
        details={"has_explanatory": has_explanatory, "has_descriptive_only": has_descriptive_only},
    )


def check_topic_has_puzzle(content: str, context: dict) -> CheckResult:
    """Check that the proposal identifies a research puzzle / phenomenon worth explaining."""
    patterns = [
        r"值得.*解释",
        r"反直觉",
        r"puzzle",
        r"现象",
        r"为什么.*不是.*而是",
        r"奇怪",
        r"矛盾",
        r"研究.*动机",
        r"研究背景",
        r"现实背景",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="topic_has_puzzle",
        message="Research puzzle / motivating phenomenon found" if found else "No research puzzle identified",
    )


def check_topic_has_story_line(content: str, context: dict) -> CheckResult:
    """Check that the proposal contains an explicit story line / causal chain."""
    patterns = [
        r"故事",
        r"story",
        r"因果",
        r"→|->|↓",          # arrow characters indicating a chain
        r"causal chain",
        r"解释链",
        r"主线",
        r"逻辑.*链",
        r"一句话.*论文",
        r"本文.*解释.*发现",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="topic_has_story_line",
        message="Story line / causal chain found" if found else "No explicit story line found — required before finalising proposal",
    )


def check_topic_has_boundary(content: str, context: dict) -> CheckResult:
    """Check that the proposal states what is OUT of scope (research boundary)."""
    patterns = [
        r"不.*研究",
        r"不.*讨论",
        r"超出.*范围",
        r"研究边界",
        r"边界",
        r"范围.*限定",
        r"not.*study",
        r"out of scope",
        r"beyond.*scope",
        r"局限",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="topic_has_boundary",
        message="Research boundary / out-of-scope statement found" if found else "No research boundary defined",
    )


def check_topic_has_feasibility(content: str, context: dict) -> CheckResult:
    """Check that the proposal addresses data / evidence feasibility."""
    patterns = [
        r"数据.*来源|来源.*数据",
        r"数据.*可得",
        r"可行性",
        r"data.*source",
        r"feasib",
        r"年报|公告|财报",
        r"数据库",
        r"样本",
        r"案例.*获取",
        r"公开.*数据",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="topic_has_feasibility",
        message="Feasibility / data source addressed" if found else "No feasibility assessment found",
    )


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


# =============================================================================
# Data Collector Checks (new — aligned with skill boundary v7)
# =============================================================================

def check_data_mode_declared(content: str, context: dict) -> CheckResult:
    """Check that 02_data_report.md declares which collection mode was used.

    Boundary: data-collector must identify its mode (case_evidence / panel_data /
    qualitative / descriptive) and record it in the report.
    """
    modes = [
        r"案例证据模式",
        r"面板数据模式",
        r"质性素材模式",
        r"资料汇编模式",
        r"case.?evidence",
        r"panel.?data.?mode",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in modes)
    return CheckResult(
        passed=found,
        check_id="data_mode_declared",
        message="Collection mode declared in report" if found else
                "No collection mode found — report must state case_evidence / panel_data / qualitative / descriptive",
    )


def check_data_has_triangle_verification(content: str, context: dict) -> CheckResult:
    """Check that the evidence timeline contains triangle-verification status markers.

    Boundary: data-collector is responsible for ≥2-source cross-verification of
    core facts. Status markers (✓ 双源 / △ 单源) must appear in the output.
    """
    dual = len(re.findall(r"✓.*双源|双源.*✓|dual.?source|两.*来源", content, re.IGNORECASE))
    single = len(re.findall(r"△.*单源|单源.*△|single.?source", content, re.IGNORECASE))
    total = dual + single
    passed = total > 0
    return CheckResult(
        passed=passed,
        check_id="data_has_triangle_verification",
        message=f"Verification markers found: ✓双源={dual} △单源={single}" if passed else
                "No triangle-verification status markers found — core facts need ≥2-source validation",
        details={"dual_source": dual, "single_source": single},
    )


def check_data_no_exec_details(content: str, context: dict) -> CheckResult:
    """Check that data-collector output contains no web-execution details.

    Boundary: execution details (curl commands, mirror URLs, Sci-Hub paths) belong
    to web-access, not data-collector. Their presence signals a boundary violation.
    """
    violations = [
        r"curl\s+-[LlOo]",
        r"sci-hub\.(st|ru|se)",
        r"同名词干",
        r"filetype:pdf.*tavily|tavily.*filetype:pdf",
        r"WebFetch.*下载|下载.*WebFetch",
    ]
    found = [p for p in violations if re.search(p, content, re.IGNORECASE)]
    passed = len(found) == 0
    return CheckResult(
        passed=passed,
        check_id="data_no_exec_details",
        message="No web-execution details found (boundary clean)" if passed else
                f"Boundary violation: execution details found ({len(found)} pattern(s)) — delegate to web-access",
        details={"violated_patterns": found},
    )


# =============================================================================
# Empirical Analysis Checks (new — aligned with skill boundary v7)
# =============================================================================

def check_analysis_has_parallel_trend(content: str, context: dict) -> CheckResult:
    """Check that DID analysis includes a parallel trend test.

    Boundary: empirical-analysis must not skip the parallel trend check when
    the identification strategy is DID. Absence is a completion-criterion failure.
    """
    patterns = [
        r"平行趋势",
        r"parallel.?trend",
        r"pre.?trend",
        r"事前.*系数|事前.*不显著",
        r"event.?stud",
        r"共同趋势",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="analysis_has_parallel_trend",
        message="Parallel trend test found" if found else
                "No parallel trend test found — required for DID identification",
    )


def check_analysis_has_full_sample(content: str, context: dict) -> CheckResult:
    """Check that analysis reports full-sample baseline, not only sub-samples.

    Boundary: empirical-analysis must report all pre-registered results including
    full-sample baseline to prevent p-hacking. Sub-sample-only output is a violation.
    """
    patterns = [
        r"全样本|full.?sample|whole.?sample",
        r"基准回归|baseline.?regress",
        r"Panel\s*[AB].*全|全.*Panel\s*[AB]",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="analysis_has_full_sample",
        message="Full-sample baseline result found" if found else
                "No full-sample baseline found — all pre-registered results must be reported",
    )


# =============================================================================
# Paper Writer Checks (new — aligned with skill boundary v7)
# =============================================================================

# High-frequency AI writing patterns drawn from skills/shared/ai-writing-patterns.md
_AI_PATTERNS_ZH = [
    r"值得注意的是",
    r"不难发现",
    r"由此可见",
    r"近年来[，,]随着",
    r"综上所述",
    r"一方面.*另一方面.*一方面.*另一方面",  # repeated pair
    r"为.*提供了新的视角",
    r"为.*提供了.*思路",
    r"深远.*影响|影响.*深远",
]

_AI_PATTERNS_EN = [
    r"[Ii]t is worth noting that",
    r"[Nn]otably[,，]",
    r"[Tt]his study contributes to the literature by",
    r"[Ii]t should be noted that",
    r"[Ii]t is important to note",
]


def check_paper_no_ai_patterns(content: str, context: dict) -> CheckResult:
    """Check that paper output avoids high-frequency AI writing patterns.

    Boundary: paper-writer must actively avoid patterns listed in
    skills/shared/ai-writing-patterns.md (preventive role).
    Threshold: fail if any single pattern appears >3 times (mild = warn, not fail)
    or any pattern appears >8 times (明显 = fail).
    """
    threshold_fail = context.get("threshold_fail", 8)
    threshold_warn = context.get("threshold_warn", 3)

    hits: dict[str, int] = {}
    for p in _AI_PATTERNS_ZH + _AI_PATTERNS_EN:
        count = len(re.findall(p, content, re.IGNORECASE))
        if count > 0:
            hits[p] = count

    max_count = max(hits.values(), default=0)
    total_hits = sum(hits.values())

    passed = max_count <= threshold_fail
    if max_count > threshold_fail:
        msg = f"AI writing pattern overuse detected: max {max_count} occurrences of one pattern (threshold: {threshold_fail})"
    elif max_count > threshold_warn:
        msg = f"AI writing patterns present ({total_hits} total hits) — review recommended"
    else:
        msg = f"AI writing patterns within acceptable range ({total_hits} total hits)"

    return CheckResult(
        passed=passed,
        check_id="paper_no_ai_patterns",
        message=msg,
        details={"hits": {k: v for k, v in hits.items() if v > threshold_warn}},
    )


def check_paper_numbers_traceable(content: str, context: dict) -> CheckResult:
    """Check that paper body references analysis output files rather than bare numbers.

    Boundary: paper-writer must not self-generate regression coefficients.
    Positive signal: \\input{} or \\include{} references to analysis/output/*.tex,
    or explicit citations like 'Table X' that map to a source file.
    Negative signal: bare decimal numbers (e.g. 0.234) with no surrounding
    table-reference context.
    """
    # Positive: LaTeX input/include of analysis output
    traceable = re.findall(
        r"\\(?:input|include)\{[^}]*(?:analysis|output|baseline|regression|robustness)[^}]*\}",
        content, re.IGNORECASE,
    )
    # Positive: explicit table references
    table_refs = re.findall(r"[Tt]able\s+\d+|表\s*\d+", content)

    passed = len(traceable) > 0 or len(table_refs) > 0
    return CheckResult(
        passed=passed,
        check_id="paper_numbers_traceable",
        message=f"Traceable references found: {len(traceable)} \\input/\\include, {len(table_refs)} table refs" if passed else
                "No traceable number sources found — coefficients must come from analysis/output/, not be self-generated",
        details={"latex_inputs": len(traceable), "table_refs": len(table_refs)},
    )


# =============================================================================
# Integrity Auditor Checks (new — aligned with skill boundary v7)
# =============================================================================

def check_audit_has_verification_status(content: str, context: dict) -> CheckResult:
    """Check that audit report records per-citation verification status.

    Boundary: integrity-auditor is the single source of truth for the four-level
    citation classification (verified / unverified / suspicious / fabricated).
    All four levels must appear in the report to confirm full coverage.
    """
    required = ["verified", "unverified", "suspicious", "fabricated"]
    found = [level for level in required if re.search(level, content, re.IGNORECASE)]
    missing = [level for level in required if level not in found]
    passed = len(missing) == 0
    return CheckResult(
        passed=passed,
        check_id="audit_has_verification_status",
        message=f"All 4 verification levels present" if passed else
                f"Missing levels: {missing} — audit report must classify every citation",
        details={"found": found, "missing": missing},
    )


def check_audit_has_numerical_check(content: str, context: dict) -> CheckResult:
    """Check that audit report includes a numerical consistency section.

    Boundary: integrity-auditor must cross-check numbers between abstract,
    body text, and tables. Evidence: presence of consistency-check language.
    """
    patterns = [
        r"数字.*一致|一致.*数字",
        r"numerical.?consist",
        r"系数.*不一致|不一致.*系数",
        r"摘要.*正文|正文.*表格",
        r"数字一致性",
        r"[Nn]umerical.?check",
        r"[Cc]oefficient.*match|match.*coefficient",
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="audit_has_numerical_check",
        message="Numerical consistency check section found" if found else
                "No numerical consistency check found — abstract/body/table cross-check is required",
    )


def check_audit_uses_shared_ai_patterns(content: str, context: dict) -> CheckResult:
    """Check that audit report's AI-writing section references the shared patterns file.

    Boundary: integrity-auditor must load skills/shared/ai-writing-patterns.md
    (not maintain its own list). Positive signal: reference to the shared file path
    OR presence of severity levels defined there (轻微/中等/明显).
    """
    patterns = [
        r"ai.writing.patterns",
        r"shared.*patterns|patterns.*shared",
        r"轻微|中等|明显",          # severity levels from shared file
        r"mild|moderate|severe",    # English equivalents
    ]
    found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
    return CheckResult(
        passed=found,
        check_id="audit_uses_shared_ai_patterns",
        message="Shared AI-writing pattern reference found" if found else
                "Audit report does not reference shared AI-writing patterns — load skills/shared/ai-writing-patterns.md",
    )


def check_audit_no_auto_delete(content: str, context: dict) -> CheckResult:
    """Check that audit report recommends action but does not auto-delete citations.

    Boundary: integrity-auditor must never auto-delete — only report and recommend.
    Positive signal: 'suggest'/'recommend'/'建议' near 'delete'/'删除'.
    Negative signal: bare imperative delete without qualifier.
    """
    # Red flag: unqualified deletion commands
    auto_delete = re.findall(
        r"(?:已自动|自动.*删除|auto.*delet|delet.*automatically)",
        content, re.IGNORECASE,
    )
    # Green flag: recommendations
    recommend = re.findall(
        r"建议.*删除|建议.*替换|recommend.*delet|suggest.*remov",
        content, re.IGNORECASE,
    )

    passed = len(auto_delete) == 0
    if not passed:
        msg = f"Auto-deletion detected ({len(auto_delete)} instance(s)) — auditor must only recommend, never auto-delete"
    elif len(recommend) > 0:
        msg = f"Report uses recommendation language (not auto-delete) — boundary respected"
    else:
        msg = "No auto-deletion found"

    return CheckResult(
        passed=passed,
        check_id="audit_no_auto_delete",
        message=msg,
        details={"auto_delete_hits": auto_delete, "recommend_hits": recommend},
    )
