# PaperPilot Skill Testing Guide

本文档介绍 PaperPilot 的 skill 测试框架，帮助开发者验证和改进 skills。

## 测试架构概览

```
tests/
├── skill_evals/           # Skill 输出质量检查
│   ├── __init__.py
│   ├── checks.py          # 确定性检查函数
│   ├── harness.py         # 评估运行器
│   ├── test_demo_paper_artifacts.py  # demo-paper 回归测试
│   └── prompts/           # 测试用例 JSON
├── e2e/                   # 端到端测试
│   └── test_golden_paper.py
├── fixtures/              # 测试数据
└── test_golden_path.py    # 工作流引擎测试
```

## 快速开始

### 运行全部测试

```bash
pytest tests/ -v
```

### 只运行 skill 相关测试

```bash
# 检查 demo-paper artifacts
pytest tests/skill_evals/test_demo_paper_artifacts.py -v

# 运行 artifact 验证和 check 单元测试
pytest tests/e2e/test_golden_paper.py -v
```

## Skill Evaluation Framework

### 1. Check Registry

`checks.py` 提供了一组确定性检查函数，用于验证 skill 输出的结构和质量。

#### 可用检查

| Check ID | 用途 | 参数 |
|----------|------|------|
| `lit_has_papers` | 文献列表至少有 N 篇论文 | `min_papers` (默认 10) |
| `lit_has_urls` | 文献有 URL 或 DOI | `min_urls` (默认 5) |
| `lit_has_verification_status` | 有验证状态标记 (✓/△/✗) | - |
| `lit_bilingual_search` | 包含中英文内容 | - |
| `data_has_source` | 记录了数据来源 | - |
| `data_has_variables` | 定义了必要变量 | `required_vars` |
| `analysis_has_regression_table` | 有回归表格结构 | - |
| `analysis_latex_valid` | LaTeX 大括号平衡 | - |
| `paper_has_sections` | 包含必要章节 | `required_sections` |
| `paper_no_placeholders` | 无占位符文本 | - |
| `paper_citations_exist` | 有引用 | `min_citations` (默认 5) |
| `markdown_has_content` | 有实质内容 | `min_chars` (默认 100) |
| `json_valid` | 是有效 JSON | - |

#### 使用示例

```python
from tests.skill_evals.checks import CheckRegistry

registry = CheckRegistry()

# 检查文献综述
content = Path("literature/literature_review.md").read_text()
result = registry.run("lit_bilingual_search", content, {})

if result.passed:
    print("✓ 中英文双语覆盖")
else:
    print(f"✗ {result.message}")
```

### 2. Eval Harness

`harness.py` 提供批量运行评估用例的能力。

```python
from tests.skill_evals.harness import SkillEvalHarness

harness = SkillEvalHarness()
harness.load_prompts("tests/skill_evals/prompts/literature_survey.json")

# 评估已有 artifacts
report = harness.evaluate_artifacts(
    skill="literature-survey",
    artifacts={
        "literature_review": review_content,
        "candidate_papers": papers_content,
    }
)

print(report.summary())
# ✓ literature-survey: 100.0% pass rate (6/6 cases, 12ms)
```

### 3. 测试用例格式

测试用例存放在 `prompts/*.json`：

```json
{
  "skill": "literature-survey",
  "description": "文献搜索 skill 评估用例",
  "cases": [
    {
      "id": "lit_basic_chinese",
      "description": "中文主题基础搜索",
      "skill": "literature-survey",
      "prompt": "帮我搜索数字经济与就业的相关文献",
      "expected_checks": [
        "lit_has_papers",
        "lit_bilingual_search",
        "lit_has_urls"
      ],
      "should_trigger": true,
      "context": {
        "min_papers": 10
      }
    }
  ]
}
```

## 添加新 Skill 测试

### 步骤 1: 添加检查函数

在 `checks.py` 中添加新的检查：

```python
def check_my_skill_output(content: str, context: dict) -> CheckResult:
    """检查 my-skill 的输出。"""
    # 实现检查逻辑
    passed = "expected_pattern" in content
    return CheckResult(
        passed=passed,
        check_id="my_skill_output",
        message="检查通过" if passed else "未找到预期内容",
    )
```

然后在 `CheckRegistry._register_builtin_checks()` 中注册：

```python
self.register("my_skill_output", check_my_skill_output)
```

### 步骤 2: 创建测试用例

创建 `prompts/my_skill.json`：

```json
{
  "skill": "my-skill",
  "cases": [
    {
      "id": "my_skill_basic",
      "prompt": "测试 prompt",
      "expected_checks": ["my_skill_output", "markdown_has_content"],
      "context": {"min_chars": 200}
    }
  ]
}
```

### 步骤 3: 添加回归测试

如果 skill 会产生 demo-paper artifacts，在 `test_demo_paper_artifacts.py` 中添加测试：

```python
def test_my_skill_artifact(self):
    """My skill artifact meets quality standards."""
    if "my_artifact" not in self.artifacts:
        self.skipTest("my_artifact not found")
    
    result = self.registry.run(
        "my_skill_output",
        self.artifacts["my_artifact"],
        {"some_param": "value"}
    )
    self.assertTrue(result.passed, result.message)
```

## 发布检查清单

每次发布新版本前，运行以下检查：

```bash
# 1. 运行全部测试
pytest tests/ -v

# 2. 重点检查 demo-paper artifacts
pytest tests/skill_evals/test_demo_paper_artifacts.py -v

# 3. 检查版本更新
python install/bootstrap.py --check
```

### 理想的发布流程

1. **更新 skill** — 修改 `skills/xxx/SKILL.md`
2. **重跑 demo-paper** — 作为用户完整运行一遍 skill
3. **验证 artifacts** — 运行 `pytest tests/skill_evals/ -v`
4. **提交** — 同时提交 skill 和更新后的 demo-paper

> 💡 demo-paper 不是静态模板，而是每次发布时由 skill 实际运行产生的验证结果。

## 测试设计原则

基于业界最佳实践：

1. **确定性检查** — 不依赖 LLM，检查可重复
2. **结构优先** — 先检查结构（有引用、有章节），再检查质量
3. **负面测试** — 验证错误输入被正确拒绝
4. **隔离测试** — 每个测试独立，不依赖其他测试的副作用

## 参考资料

- [Addy Osmani - agent-skills](https://github.com/nicholasgriffintn/OpenAgent) — 过程优先于散文
- [Philipp Schmid - testing-skills](https://www.philschmid.de/evaluate-llm) — prompt sets, deterministic checks
- [Microsoft Vally](https://github.com/microsoft/Vally) — lint + eval 分离
