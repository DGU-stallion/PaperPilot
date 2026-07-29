---
name: paper-search
description: Paper search — use when the user wants to find academic literature, build a reference list, verify citations exist, or download PDFs. Looks for research direction and keywords in 00_research_proposal.md; asks user if absent. literature-review skill reads this skill's output.
version: 1.0.0
produces:
  - literature/00_paper_search.md
  - literature/references.bib (optional, LaTeX only)
output_dir: literature/
---

# Paper Search

## 职责边界

**所需信息**：研究方向 + 核心关键词。  
**产出**：`literature/00_paper_search.md`（经验证的文献清单）+ 可选 `references.bib`。  
**完成标准**：每条引用有验证状态和完整元数据，核心锚点论文 4-6 篇已标注选取理由，研究空白已识别。  
**不做**：主题提炼、论证组织、综述写作（→ literature-review）；非学术材料（→ data-collector）；引用深度验证（→ integrity-auditor）。

**材料边界**：只处理能进入论文参考文献列表的同行评审学术文献。

---

## Step 1 — 收集所需信息

查找顺序：
1. 读取 `papers/<project>/topics/00_research_proposal.md`，提取：核心概念（2-4个）、研究问题、已提到的关键词或论文线索
2. 读取对话中用户已提供的方向或关键词
3. 仍缺失时，向用户追问——一次只问一个问题：
   - "你的研究方向是什么？想搜哪些理论或关键词？"
   - （确认后）"有没有时间范围或语言偏好？没有按默认来：近5年为主+经典不限年，优先A+/A级期刊。"

**完成标准**：研究方向已知，核心关键词（中英文）已确定，搜索偏好已确认。

---

## Step 2 — 搜索（锚点深搜）

核心逻辑：先找高质量锚点论文，再沿其参考文献和关联文献向外扩展。

```
Step 2a: 找锚点
  └─ 用核心概念关键词搜索，按质量排序，选出 4-6 篇锚点论文

Step 2b: 向外扩展（对每篇锚点论文）
  ├─ 读取参考文献列表 → 识别相关论文 → 加入候选池
  └─ 读取关联引用（被哪些论文引用）→ 加入候选池

Step 2c: 补充搜索
  └─ 针对扩展后暴露的知识缺口，补充关键词搜索
```

### 锚点论文选取标准

优先选取：期刊层级高（A+/A）、被引量高、经典著作（被引 >1000）、与研究问题直接相关。  
约束：不能全是同一作者/团队；中英文各至少 1 篇。

### 工具分工

| 搜索目标 | 首选工具 | 备选 |
|---------|---------|------|
| 精确查找已知论文 | CrossRef (`search_crossref`) | OpenAlex |
| 模糊主题探索 | Semantic Scholar (`search_semantic`) | Google Scholar |
| 引用/关联扩展 | Semantic Scholar | — |
| OA/预印本 PDF | Tavily (`tavily_search`) | — |
| 中文学术论文 | Tavily (`site:cnki.net` / `site:wanfang.com`) | — |
| 元数据权威验证 | CrossRef (`get_crossref_paper_by_doi`) | — |

元数据验证：搜索到候选论文后，用 `get_crossref_paper_by_doi(DOI)` 核实。CrossRef 是权威源，不一致时以 CrossRef 为准。

中文文献：web-access 无法自动获取知网全文时，标记"需用户在知网补充"并给出具体搜索词。

### 搜索执行顺序

```
1. 英文关键词: search_crossref → 补充 search_semantic
2. 中文关键词: tavily_search("site:cnki.net {关键词}")
3. 锚点扩展: search_semantic("{title}") — 超时降级为 CrossRef 按作者补充
4. 元数据确认: get_crossref_paper_by_doi(DOI) — 所有纳入论文
5. 补充搜索: 针对缺口维度
```

**完成标准**：候选池已建立，锚点扩展已对每篇执行，补充搜索已覆盖缺口。

---

## Step 3 — 筛选

| 维度 | 纳入 | 排除 |
|------|------|------|
| 相关性 | 与研究问题直接相关 | 仅标题相似但内容无关 |
| 时效性 | 近 10 年（核心近 5 年）| 过时且无奠基价值 |
| 质量 | 同行评审期刊/会议 | 未审稿的一般性文章 |
| 语言 | 中文、英文 | 其他（除非用户指定）|

**期刊层级**：A+（SSCI Q1顶刊 / 管理世界 / 经济研究等）、A（SSCI Q1-Q2 / CSSCI权威）、B（SSCI Q2-Q3 / CSSCI来源）、经典（被引>1000）。以用户学校目录为准，否则用通用标准。

**完成标准**：筛选后纳入论文列表已确定，每篇有相关度标注。

---

## Step 4 — 验证引用

**绝对禁止凭记忆生成引用。论文标题必须来自检索结果原文，完整准确，不得截断或改写。**

| 状态 | 标准 |
|------|------|
| ✓ 已验证 | ≥2 个源返回一致的标题+作者+年份 |
| △ 单源 | 仅 1 个源，但有完整 DOI 或发表信息 |
| ✗ 存疑 | 信息不一致或无法确认，需用户手动确认 |

**完成标准**：所有纳入论文有验证状态标注，存疑引用已告知用户。

---

## Step 5 — 写清单报告

### `00_paper_search.md` 结构

```markdown
# 文献搜索报告

## 一、搜索策略
关键词来源、搜索工具、时间范围；
结果漏斗：检索 X 篇 → 筛选后纳入 N 篇。

## 二、研究空白初判
现有研究的 2-3 个主要空白；有无高度竞争论文（如有，标注差异点）。

## 三、核心锚点论文（4-6 篇）
每篇包含：完整标题、第一作者、年份、期刊、层级、被引量、选入理由（1句）。

## 四、完整文献列表

| # | 标题（完整） | 第一作者 | 年份 | 期刊/来源 | 层级 | 相关度 | 被引量 | 状态 | DOI/URL |
|---|------------|---------|------|----------|------|--------|--------|------|---------|
```

**完成标准**：四节均已填写，每篇论文有完整元数据和验证状态。

---

## Step 6 — 询问下载

```
文献搜索完成。需要下载 PDF 吗？

  A. 只下载核心锚点论文（[X] 篇，推荐）
  B. 下载全部纳入文献（[N] 篇）
  C. 指定下载
  D. 暂不下载
```

### 下载执行（委托 web-access）

按优先级依次尝试，每个渠道超时 30 秒：

| 优先级 | 渠道 | 工具 |
|--------|------|------|
| 1 | Sci-Hub 镜像轮询 | `download_scihub(identifier=DOI, base_url=mirror)` |
| 2 | Semantic Scholar OA | `download_semantic(paper_id="DOI:...")` |
| 3 | Tavily 搜索 PDF | `tavily_search("{title} filetype:pdf")` → curl |
| 4 | 源原生下载 | `download_arxiv` / `download_biorxiv` 等（仅限来自该平台的论文） |
| 5 | curl 直下载 | 上游已发现明确 PDF URL 时 |

Sci-Hub 镜像顺序：`sci-hub.st` → `sci-hub.ru` → `sci-hub.se`。单镜像连续 3 次失败本次会话跳过；所有镜像首轮全部失败时等待 10 秒后完整重试一次。

失败兜底：标记 `[需手动下载]`，给出 DOI 链接 + 建议途径。

**禁止使用 `download_with_fallback`**（EuropePMC fallback 对社科论文会匹配到无关文献）。

`save_path` 必须显式传入 `"papers/<project>/literature/pdfs"`。

下载后三步验证：
1. `file <路径>` — 必须含 `PDF document`，否则删除切换下一渠道
2. `strings <路径> | grep -i "title\|author\|doi\|journal"` — 核实标题/作者/年份匹配
3. 重命名为 `{年份}_{标题}.pdf`（空格→下划线，去标点）

---

## 质量 Checklist

- [ ] 关键词来自 `00_research_proposal.md` 或用户确认，未凭空构造
- [ ] 中英文文献均有覆盖
- [ ] 锚点论文 4-6 篇，选取依据有说明
- [ ] 每篇锚点论文做了参考文献和关联引用扩展
- [ ] 所有引用来自实际检索，标题完整准确
- [ ] 每篇论文有验证状态和 DOI/URL
- [ ] 存疑引用已标记并告知用户
- [ ] 发现高度相似论文已告知用户并标注差异点
- [ ] 报告完成后询问了用户是否下载

---

## 完成后的标准输出

```
✅ 文献搜索完成

📄 literature/00_paper_search.md
  搜索漏斗: 检索 X 篇 → 纳入 N 篇（含锚点扩展 Y 篇）
  核心锚点: [X] 篇
  验证状态: ✓ X 篇 / △ Y 篇 / ✗ Z 篇

📊 研究空白初判:
  [方向有空间 / 拥挤需差异化 / 有竞争论文（说明）]

⚠️ [如有存疑引用或风险，在此说明]

需要下载 PDF 吗？A/B/C/D

➡️ 下一步可用:
  literature-review — 基于此清单撰写文献综述
```
