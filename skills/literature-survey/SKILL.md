---
name: literature-survey
description: Search and synthesize academic literature using anchor-and-expand strategy. Produces a literature review report with core paper recommendations, full reference list, and thematic synthesis.
version: 7.0.0
triggers:
  - "帮我搜文献"
  - "写文献综述"
  - "literature review"
  - "找相关论文"
consumes:
  - topics/00_research_proposal.md
produces:
  - literature/01_literature_review.md
  - literature/references.bib (optional, LaTeX only)
output_dir: literature/
---

# Literature Survey

## 职责边界

**入口条件**：研究方案已确定（`00_research_proposal.md` 存在）。  
**产出**：`literature/01_literature_review.md` + 可选 `references.bib`。  
**出口条件**：每条引用有验证状态，核心论文4-6篇已标注选取理由，研究空白已识别。  
**不负责**：PDF 下载执行细节（→ web-access）、引用深度验证（→ integrity-auditor）。

## 角色

严谨的文献调研助手。每一条引用必须来自实际检索，绝不凭空生成，论文标题必须完整准确。

---

## 进入本阶段

1. 读取 `topics/00_research_proposal.md`，从中提取：
   - 核心概念（2-4 个）
   - 研究问题和故事线
   - 已提到的关键词或论文线索

2. 询问用户偏好（一句话）：
   ```
   "开始文献调研之前，有没有特定偏好？（时间范围、中英文比例、期刊层级要求等）
   没有的话按默认来：近5年为主+经典不限年，优先A+/A级期刊。"
   ```

3. 向用户确认搜索维度（基于研究提案动态生成，不套模板），等用户确认后开始。

---

## 搜索策略：锚点深搜（树状）

**核心逻辑**：先找高质量锚点论文，再沿其参考文献和关联文献向外扩展，而不是先广撒网再筛选。

```
Step 1: 找锚点
  └─ 用核心概念关键词搜索，按质量排序，选出 4-6 篇锚点论文

Step 2: 向外扩展（对每篇锚点论文）
  ├─ 读取其参考文献列表 → 识别相关论文 → 加入候选池
  └─ 读取其关联引用（被哪些论文引用）→ 识别相关论文 → 加入候选池

Step 3: 补充搜索
  └─ 针对扩展后暴露的知识缺口，补充关键词搜索
```

### 锚点论文选取标准

综合排序，优先选取：
- 期刊层级高（A+/A 级，或 SSCI Q1/CSSCI 权威期刊）
- 被引量高（该领域相对基准）
- 经典著作（被引 >1000 或公认奠基性工作，不受年份限制）
- 与研究问题直接相关

选取约束：不能全是同一作者/团队；中英文各至少 1 篇。

### 工具分工

| 搜索目标 | 首选工具 | 备选 | 说明 |
|---------|---------|------|------|
| 精确查找已知论文（有标题/作者/DOI） | CrossRef (`search_crossref`) | OpenAlex | 结构化元数据最完整，命中率最高 |
| 模糊主题探索 | Semantic Scholar (`search_semantic`) | Google Scholar | 语义相关性好 (可能限流，超时时降级为 CrossRef) |
| 引用/关联扩展 | Semantic Scholar | — | 获取参考文献列表和被引列表 |
| 发现 OA/预印本 PDF 链接 | Tavily (`tavily_search`) | — | 补充 OA 链接发现 |
| 中文学术论文 | Tavily (`site:cnki.net` / `site:wanfang.com`) | — | WebSearch + WebFetch 访问中文数据库 |
| 元数据权威验证 | CrossRef (`get_crossref_paper_by_doi`) | — | 所有论文的 DOI/卷期页/出版商以 CrossRef 为准 |

**元数据验证规则**：搜索到候选论文后，用 `get_crossref_paper_by_doi(DOI)` 核实元数据（标题、作者、年份、期刊），确认无误后再进入下载流程。CrossRef 是元数据权威源。

**中文文献说明**：如 web-access 无法自动获取知网全文，标记为"需用户在知网补充"并给出具体搜索词。如已安装 cnki-mcp，优先使用。

### 搜索执行

```
1. 关键词搜索（英文）
   首选: search_crossref(query="...", max_results=10)  ← 元数据最精确
   补充: search_semantic(query="...")                   ← 语义相关性好，但可能超时
   排序依据：被引量 + 期刊层级

2. 关键词搜索（中文）
   web-access: tavily_search("site:cnki.net {关键词}") — 提取标题、作者、期刊、被引量

3. 锚点扩展（对每篇锚点论文）
   锚点扩展: search_semantic("{title}") — 识别引用关系；超时时降级为 CrossRef 按作者补充

4. 元数据确认
   对所有纳入论文: get_crossref_paper_by_doi(DOI) → 核实标题/作者/年份/期刊
   CrossRef 为权威源，与搜索结果不一致时以 CrossRef 为准

5. 补充搜索
   针对缺口维度补充 1-2 轮关键词搜索
```

---

## 筛选标准

| 维度 | 纳入 | 排除 |
|------|------|------|
| 相关性 | 与研究问题直接相关 | 仅标题相似但内容无关 |
| 时效性 | 近 10 年（核心近 5 年）| 过时且无奠基价值 |
| 质量 | 同行评审期刊/会议 | 未审稿的一般性文章 |
| 语言 | 中文、英文 | 其他（除非用户指定）|

### 期刊层级

| 等级 | 标准 |
|------|------|
| A+ | 用户学校目录A+，或 SSCI Q1 顶刊（SMJ、AMR、管理世界、经济研究等）|
| A  | 用户学校目录A，或 SSCI Q1-Q2 / CSSCI 权威期刊 |
| B  | SSCI Q2-Q3 / CSSCI 来源期刊 |
| 其他 | 有同行评审但不在核心索引 |
| 经典 | 被引 >1000 或公认奠基性著作，层级覆盖以上所有 |

以用户学校期刊目录为准（如提供）；否则用通用标准。

---

## 引用验证

**绝对禁止凭记忆生成引用。论文标题必须来自检索结果原文，完整准确，不得截断或改写。**

每条引用双源交叉验证：

| 状态 | 标准 |
|------|------|
| ✓ 已验证 | ≥2 个源返回一致的标题+作者+年份 |
| △ 单源 | 仅 1 个源，但有完整 DOI 或发表信息 |
| ✗ 存疑 | 信息不一致或无法确认，需用户手动确认 |

---

## 输出文件

```
papers/<project>/literature/01_literature_review.md
papers/<project>/literature/references.bib          （可选，用户使用 LaTeX 时生成）
```

### `01_literature_review.md` 结构

```markdown
# 文献调研报告

## 一、搜索策略与结果概述
关键词（来源：00_research_proposal.md）、搜索工具、维度；
结果漏斗：检索 X 篇 → 筛选后纳入 N 篇。

## 二、研究空白与本研究定位
现有研究的 2-3 个主要空白；有无高度竞争论文（如有，分析差异）；
本研究的定位和贡献点。

## 三、核心论文推荐（4-6 篇）
精选的锚点论文，每篇包含：
- 完整标题、第一作者、年份、期刊、期刊层级、被引量
- 选入理由（1-2 句）
- 对本研究的参考价值（1 句）

## 四、完整文献列表

| # | 标题（完整） | 第一作者 | 年份 | 期刊/来源 | 层级 | 相关度 | 被引量 | 状态 | DOI/URL |
|---|------------|---------|------|----------|------|--------|--------|------|---------|

## 五、主题式文献综述
按主题组织，不逐篇罗列。每节末说明与本研究的关系。
```

---

## 报告完成后：询问下载

报告写完后，**必须**询问用户：

```
文献报告已完成。需要我帮你下载 PDF 吗？

  A. 只下载核心论文（[X] 篇，推荐）
  B. 下载全部纳入文献（[N] 篇）
  C. 指定下载（告诉我要哪几篇）
  D. 暂不下载

PDF 下载到 literature/pdfs/ 目录。
```

**下载执行委托 web-access skill，分"发现 PDF"和"下载文件"两阶段执行。**

**阶段一：获取 PDF（按优先级依次尝试，每个渠道超时 30 秒）**

| 优先级 | 渠道 | 工具 | 说明 |
|--------|------|------|------|
| 1 | **Sci-Hub 多镜像轮询** | `download_scihub(identifier=DOI, base_url=mirror)` | 覆盖最广，DOI 直达；镜像按列表顺序尝试 |
| 2 | Semantic Scholar OA | `download_semantic(paper_id="DOI:...")` | 补充 OA / 预印本 |
| 3 | Tavily 搜索机构仓库 PDF | `tavily_search("{title} filetype:pdf")` → 筛选可信域名 → `curl -L -o` | 补充 Google Scholar [PDF] 发现能力 |
| 4 | 对应源原生下载 | `download_arxiv` / `download_biorxiv` 等 | 仅限论文来源为该预印本平台 |
| 5 | curl 直下载 | `curl -L -H "User-Agent: Mozilla/5.0" -o <path> <url>` | 上游已发现明确 PDF URL 时 |

**Sci-Hub 镜像轮询策略**：
- 镜像列表：`sci-hub.st` → `sci-hub.ru` → `sci-hub.se`（按近期可用性排序，定期更新）
- 每个镜像超时 30 秒，失败立即切下一个
- 单个镜像连续 3 次失败 → 本次会话内跳过该镜像
- **重试规则**：如果所有镜像首轮全部失败，等待 10 秒后进行一次完整重试（Sci-Hub 节点存在瞬时不可用的情况，实测同一 DOI 前一次失败后一次可成功）

Tavily 搜索 PDF 的执行策略见 `skills/web-access/SKILL.md` — web-access 负责渠道选择和同名干扰防护。

**阶段二：失败兜底**
- 所有渠道均失败 → 标记为 `[需手动下载]`，给出 DOI 链接 + 建议下载途径（校内数据库/出版商页面）

**禁止使用 `download_with_fallback`**，除非论文明确来自以下数据源且 paper_id 格式正确：arXiv、bioRxiv、medRxiv、IACR。该工具的 EuropePMC fallback 会对社科/管理学论文匹配到无关文献。

**save_path 配置**：所有下载工具调用必须显式传入 `save_path`：
```
save_path = "papers/<project>/literature/pdfs"
```
不得使用工具默认的 `./downloads` 路径。

**下载后必须执行以下三步，不得跳过：**

**步骤一：验证文件是真正的 PDF（非 HTML 伪装）**
- 用 `file <路径>` 命令检查文件类型
- 输出必须包含 `PDF document`，否则视为下载失败，删除文件，切换下一渠道
- 同时检查页数：正式期刊论文通常 ≥10 页，页数 <5 页需进一步核查内容

**步骤二：验证下载内容与目标论文一致**
- 用 `strings <路径> | grep -i "title\|author\|doi\|journal"` 提取元数据
- 与目标论文的元数据逐一比对（标题、作者、年份三项均需匹配）
- 不一致时：删除错误文件，重新定位正确来源后再下载

**步骤三：按论文标题重命名文件**
- 命名规则：`{年份}_{标题}.pdf`
- 标题使用完整标题，将空格替换为下划线，去掉标点符号
- 示例：`2005_The_Governance_of_Global_Value_Chains.pdf`
- 示例：`2021_全球价值链攀升与数字经济转型.pdf`
- 文件存入 `literature/pdfs/` 目录

---

## 质量 Checklist

- [ ] 关键词来自 `00_research_proposal.md`，未凭空构造
- [ ] 中英文文献均有覆盖
- [ ] 锚点论文 4-6 篇，选取依据（期刊层级+被引量+相关度）有说明
- [ ] 每篇锚点论文做了参考文献和关联引用扩展
- [ ] 所有引用来自实际检索，标题完整准确
- [ ] 每篇论文有验证状态和 DOI/URL
- [ ] 存疑引用已标记并告知用户
- [ ] 发现高度相似论文已告知用户并分析差异
- [ ] 文献综述按主题组织，未逐篇罗列
- [ ] 报告完成后询问了用户是否下载

---

## 完成后的标准输出

```
✅ 文献调研完成

📄 literature/01_literature_review.md
  搜索漏斗: 检索 X 篇 → 纳入 N 篇（含滚雪球扩展 Y 篇）
  核心论文: [X] 篇
  验证状态: ✓ X 篇 / △ Y 篇 / ✗ Z 篇

📊 研究空白:
  [判断：方向有空间 / 拥挤需差异化 / 有竞争论文（说明）]

🔖 核心论文（[X] 篇）:
  1. [完整标题] ([年份], [层级], 被引 X) — [选入理由]
  2. ...

⚠️ [如有风险或存疑引用，在此说明]

---
需要帮你下载 PDF 吗？A/B/C/D
```

---

## 行为准则

1. 引用必须来自实际检索，标题完整准确，不截断、不改写
2. 搜索策略：先找高质量锚点，再树状扩展，而非广撒网
3. 英文用 paper-search-mcp，中文用 web-access 访问知网/万方/维普
4. 搜完给判断，不只列结果
5. 发现高度相似论文立即告知，不藏着
6. 报告完成后必须询问下载需求
