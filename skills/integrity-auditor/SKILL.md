---
name: integrity-auditor
description: Integrity audit — use when the user wants to verify citations, check that numbers in the paper match analysis output, detect AI writing patterns, or audit data-to-paper traceability. Looks for paper file at paper/main.tex; asks user for path if absent.
version: 7.0.0
produces:
  - audit/audit_report.md
output_dir: audit/
---

# Integrity Auditor

## 职责边界

**所需信息**：论文文件路径。  
**产出**：`audit/audit_report.md` + `audit/citation_verification.json`。  
**完成标准**：所有引用有验证状态，数字一致性全部核查，AI写作模式已扫描全文。  
**不做**：引用搜索执行（→ paper-search-mcp via web-access）、论文修改（→ paper-writer）。

---

## Step 1 — 收集所需信息

查找顺序：
1. 读取 `papers/<project>/paper/main.tex`（如存在）
2. 用户在对话中提供了其他路径或上传了论文文件
3. 仍缺失时，向用户追问："论文文件在哪里？提供路径或上传文件即可。"

同时检查以下文件（如存在则用于对照验证）：
- `papers/<project>/literature/references.bib` — 引用核对
- `papers/<project>/analysis/output/` — 数字一致性核对

**完成标准**：论文文件已找到，告知用户将检查的维度和数量。

```
"我将对论文进行以下维度的审查：
  1. 引用验证 — 检查每条引用是否真实存在
  2. 数字一致性 — 论文中的数字是否与实证结果匹配
  3. AI 写作检测 — 是否有明显的 AI 写作痕迹
  4. 数据可追溯性 — 每张表/图是否有源文件

预计检查 [X] 条引用和 [Y] 张表格。开始？"
```

---

## Step 2 — 引用验证

使用 paper-search-mcp 验证每条 BibTeX 引用：

```
验证流程（每条引用）:

1. 从 references.bib 提取: 标题、作者、年份、期刊/会议
2. 用 paper-search-mcp search_papers() 搜索
3. 用 get_paper_details() 确认完整元数据
4. 对比验证:
   - 标题是否匹配（允许小差异如大小写）
   - 作者是否匹配（至少第一作者）
   - 年份是否匹配
   - 期刊/会议是否匹配
5. 分级:
   - verified: 所有字段匹配
   - unverified: API 超时或未找到（但不一定假）
   - suspicious: 部分匹配但有出入
   - fabricated: 所有数据库均找不到匹配
```

Fallback（paper-search-mcp 不可用时）：
- web-access WebSearch 搜索论文标题
- WebFetch 访问 DOI 链接验证
- 标记为 "manual_verification_needed"

发现问题时立即记录，不等全部检查完再说。严重问题（如引用不存在）立即告知用户。

**完成标准**：所有 BibTeX 条目已逐一验证并有状态标注。

---

## Step 3 — 数字一致性

```
检查项:
1. 摘要中的数字 ↔ 正文中的数字 ↔ 表格中的数字
2. 正文描述的系数方向/显著性 ↔ 对应表格
3. 样本量: 各表格的 N 是否一致（相同样本应该 N 一样）
4. 描述性统计中的 N ↔ 回归表中的 N
5. 百分比/比例计算是否正确

常见错误:
- 摘要说"增加了 15%"但表格显示系数是 0.12
- 正文说"在 1% 水平显著"但 p 值实际是 0.03
- 不同表格使用同一样本但 N 不同
- 描述性统计的变量范围与实证不一致
```

**完成标准**：摘要/正文/表格的数字一致性已全部核查，不一致处已记录。

---

## Step 4 — AI 写作模式检测

加载 `skills/shared/ai-writing-patterns.md`，对全文逐节扫描每种模式。

报告格式：
- 给出具体位置和原文（精确到段落）
- 对照 patterns 文件给出修改建议
- 按 patterns 文件中的严重程度分级标注

**完成标准**：全文已扫描，所有 AI 写作模式发现已记录并有修改建议。

---

## Step 5 — 数据可追溯性

```
检查: 论文中每张表/图是否有对应的源文件

对照表:
  论文 Table 1 ← analysis/output/descriptive.tex ✓
  论文 Table 2 ← analysis/output/baseline_regression.tex ✓
  论文 Figure 1 ← analysis/output/fig1_xxx.pdf ✓
  论文 Table 5 ← ??? [无对应文件] ✗

发现无源文件的表/图时: 标记为 "source_missing"
```

**完成标准**：每张表/图的来源核查完毕，无源文件的已标注。

---

## 证据分级

| 等级 | 含义 | 处理建议 |
|------|------|---------|
| verified | 标题、作者、年份均匹配 | 无需处理 |
| unverified | 无法确认（API 超时/未找到）但不一定假 | 建议用户手动确认 |
| suspicious | 部分匹配但有出入（如年份差1年） | 用户必须确认并修正 |
| fabricated | 所有数据库均找不到任何匹配 | 必须删除或替换 |

---

## 质量 Checklist

- [ ] 所有 BibTeX 条目已逐一验证
- [ ] 数字一致性检查覆盖了摘要、正文、表格
- [ ] AI 写作模式已扫描全文
- [ ] 每张表/图有可追溯的源文件
- [ ] 所有问题已按严重程度分级
- [ ] 给出了具体的修复建议

---

## 输出

```
papers/<project>/audit/citation_verification.json   — 每条引用的验证结果
papers/<project>/audit/audit_report.md              — 完整审查报告（主输出）
```

**命名规则**：固定放在 `audit/` 目录根部。

### 审查报告结构（`audit_report.md`）

```markdown
# 学术诚信审查报告
## 概要
- 引用总数: X 条
- 验证结果: verified X / unverified X / suspicious X / fabricated X
- 数字一致性: 发现 X 处不一致
- AI 写作痕迹: [轻微/中等/明显]
- 数据可追溯性: X/Y 张表有源文件

## 需要立即修复的问题
[按严重程度列出]

## 建议改善
[轻微问题]

## 详细检查记录
[每条引用的验证细节]
```

---

## 完成后的标准输出

```
✅ 审查完成

📄 审查报告已生成: audit/audit_report.md

📊 结果概要:
  - 引用: [38/42 验证通过] [1 条可疑] [1 条疑似不存在]
  - 数字: [3 处不一致需修正]
  - AI 痕迹: [轻微，已标注修改建议]
  - 可追溯: [41/42 表格有源文件]

🚨 需要立即处理:
  1. 引用 [key] 在所有学术数据库中找不到 → 建议删除或替换
  2. 表 3 第 2 列系数与正文描述不一致 → 核对后修正

⚠️ 建议改善:
  3. 引用 [key] 年份可能有误（API 显示 2021 而非 2020）
  4. 第 2 节有 3 处 AI 过渡词可以改善

需要我帮你修复这些问题吗？
```

---

## 行为准则

1. **绝不自动删除引用** — 只报告和推荐，用户决定
2. **可以审查外部论文** — 给定 PDF 或 .bib 路径即可
3. **不评判研究质量** — 只检查诚信和一致性
4. **所有发现都给修复建议** — 不只说问题是什么，说怎么改
