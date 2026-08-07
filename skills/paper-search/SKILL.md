---
name: paper-search
description: Paper search — use when the user wants to find academic literature, build a reference list, verify citations exist, or needs reference expansion from anchor papers. Looks for research direction in research_proposal.md; asks if absent. literature-review reads this output.
version: 2.0.0
produces:
  - literature/paper_search.md
  - literature/pdfs/ (anchor papers auto-downloaded)
  - literature/references.bib (optional, LaTeX only)
output_dir: literature/
---

# Paper Search

**锚点深搜**：先找高质量锚点论文并下载，从其参考文献中提取二次搜索线索，再向外扩展。

## 职责边界

| 所需 | 研究方向 + 核心关键词 |
|------|----------------------|
| 产出 | `paper_search.md`（验证后的文献清单）+ 锚点 PDF |
| 完成 | 锚点 4-6 篇已下载，二次扩展已执行，每条引用有验证状态 |
| 不做 | 综述写作（→ literature-review）；非学术材料（→ data-collector）|

---

## Step 1 — 收集信息

1. 读 `topics/research_proposal.md`，提取：核心概念、研究问题、已提关键词
2. 读对话中用户已提供的方向
3. 缺失则追问（一次一个）："研究方向是什么？想搜哪些理论或关键词？"

**完成**：关键词（中英文）已确定。

---

## Step 2 — 锚点深搜

```
2a  关键词搜索 → 选出 4-6 篇锚点论文
         ↓
2b  下载锚点 PDF（自动，不询问）
         ↓
2c  从 PDF 提取参考文献 → 二次搜索
         ↓
2d  补充搜索（填补缺口维度）
```

### 2a — 找锚点

用核心关键词搜索，按以下标准选取 4-6 篇锚点：

| 优先 | 说明 |
|------|------|
| 期刊层级 | A+/A 优先 |
| 被引量 | >500 或领域经典 |
| 直接相关 | 与研究问题核心关联 |
| 来源多样 | 不能全是同一作者/团队；中英文各 ≥1 篇 |

**完成**：锚点论文 4-6 篇已选定，每篇有选取理由。

### 2b — 下载锚点 PDF

锚点论文**自动下载**，不询问用户。

下载渠道优先级（每渠道超时 30 秒）：

| 优先级 | 渠道 | 工具 |
|--------|------|------|
| 1 | Sci-Hub 镜像 | `download_scihub(identifier=DOI, base_url=mirror)` |
| 2 | Semantic Scholar OA | `download_semantic(paper_id="DOI:...")` |
| 3 | Tavily PDF 搜索 | `tavily_search("{title} filetype:pdf")` → curl |
| 4 | 源原生 | `download_arxiv` / `download_biorxiv` 等 |

Sci-Hub 镜像顺序：`sci-hub.st` → `sci-hub.ru` → `sci-hub.se`。

`save_path` = `"papers/<project>/literature/pdfs"`

下载后验证：
1. `file <路径>` — 必须含 `PDF document`
2. 重命名为 `{年份}_{简化标题}.pdf`

失败处理：标记 `[锚点下载失败-需手动]`，继续流程但在报告中提醒。

**完成**：锚点 PDF 已下载到 `literature/pdfs/`，失败的已标记。

### 2c — 参考文献提取与二次搜索

对每篇已下载的锚点 PDF：

1. **提取参考文献**：用 `markitdown` 提取 PDF 全文，定位 References/参考文献 部分
2. **识别高相关论文**：从参考文献中筛选与研究问题直接相关的论文
3. **二次搜索**：用 `search_crossref` 或 `search_semantic` 查找这些论文
4. **元数据验证**：用 `get_crossref_paper_by_doi(DOI)` 确认

**提取命令**：
```bash
markitdown "path/to/paper.pdf" | grep -A 500 -i "references\|参考文献"
```

或 Python：
```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("path/to/paper.pdf")
# 在 result.text_content 中搜索 References 部分
```

提取重点：
- 锚点论文引用的理论奠基作（如 RBV 锚点引用的 Barney, Teece 等）
- 锚点论文引用的方法论先驱
- 与研究问题相关的实证研究

**完成**：每篇锚点的参考文献已提取，高相关论文已二次搜索并验证。

### 2d — 补充搜索

检查当前候选池的覆盖：
- 理论文献是否充足？
- 方法论文献是否有？
- 中英文是否均衡？
- 是否有明显缺口维度？

针对缺口执行补充搜索。

**完成**：候选池已覆盖理论、方法、实证三类，无明显缺口。

---

## Step 3 — 筛选

| 维度 | 纳入 | 排除 |
|------|------|------|
| 相关性 | 与研究问题直接相关 | 仅标题相似 |
| 时效性 | 近 10 年（核心近 5 年）| 过时且无奠基价值 |
| 质量 | 同行评审期刊/会议 | 未审稿文章 |

**期刊层级**：A+（顶刊）、A（SSCI Q1-Q2）、B（Q2-Q3）、经典（被引>1000）。

**完成**：纳入列表已确定，每篇有相关度和层级标注。

---

## Step 4 — 验证引用

**禁止凭记忆生成引用。标题必须来自检索结果原文。**

| 状态 | 标准 |
|------|------|
| ✓ 已验证 | ≥2 源一致 或 CrossRef DOI 确认 |
| △ 单源 | 仅 1 源但有完整 DOI |
| ✗ 存疑 | 信息不一致，需用户确认 |

**完成**：所有论文有验证状态，存疑已标记。

---

## Step 5 — 写报告

### `paper_search.md` 结构

```markdown
# 文献搜索报告

## 一、搜索策略
关键词、工具、锚点深搜路径；
漏斗：检索 X 篇 → 锚点扩展 Y 篇 → 纳入 N 篇。

## 二、研究空白
现有研究的 2-3 个空白；有无竞争论文。

## 三、核心锚点论文（4-6 篇）
| # | 标题 | 作者 | 年份 | 期刊 | 层级 | 被引 | 选入理由 | PDF状态 |

## 四、二次扩展论文
从锚点参考文献中发现的重要论文。

## 五、完整文献列表
| # | 标题 | 作者 | 年份 | 期刊 | 层级 | 相关度 | 被引 | 状态 | DOI |
```

**完成**：五节均已填写，锚点有 PDF 状态标注。

---

## Step 6 — 询问下载（非锚点）

锚点已在 Step 2b 自动下载。此步询问其他论文：

```
✅ 文献搜索完成

📄 literature/paper_search.md
  漏斗: 检索 X 篇 → 锚点扩展 Y 篇 → 纳入 N 篇
  锚点: [已下载 M 篇 / 失败 K 篇]

📊 研究空白: [简述]

其他 [N-M] 篇论文需要下载吗？
  A. 下载全部
  B. 指定下载
  C. 暂不下载（推荐，需要时再下）
```

---

## 工具分工

| 目标 | 首选 | 备选 |
|------|------|------|
| 精确查找 | CrossRef | OpenAlex |
| 主题探索 | Semantic Scholar | Google Scholar |
| 元数据验证 | CrossRef `get_crossref_paper_by_doi` | — |
| 中文论文 | Tavily `site:cnki.net` | — |
| PDF 下载 | Sci-Hub → Semantic → Tavily | — |

**禁止**：`download_with_fallback`（会匹配无关文献）

---

## 质量 Checklist

- [ ] 锚点 4-6 篇，有选取理由
- [ ] 锚点 PDF 已下载（失败的已标记）
- [ ] 从锚点参考文献做了二次搜索
- [ ] 所有引用来自实际检索，标题完整
- [ ] 每篇有验证状态和 DOI
- [ ] 存疑引用已告知用户
