---
name: paper-writer
description: Manuscript assembly — use when the user wants to write or revise any section of the paper, integrate upstream results into a draft, or produce a complete manuscript. Looks for research question and through-line in research_proposal.md (sections 二/三), literature in literature_review.md, and results in analysis/output/; asks user if any are absent.
version: 7.0.0
produces:
  - paper/main.tex
output_dir: paper/
---

# Paper Writer

## 职责边界

**所需信息**：研究问题 + 核心论点 + 证据或实证结果。  
**产出**：`paper/` 目录下的完整论文文件。  
**完成标准**：论文结构完整，所有数字可追溯到 `analysis/output/`，引用来自 `references.bib`。  
**不做**：AI 写作模式深度诊断（→ integrity-auditor）、引用真实性验证（→ integrity-auditor）。

---

## Step 1 — 收集所需信息

查找顺序：

1. **研究问题和框架**：读取 `papers/<project>/topics/research_proposal.md`（如存在）
2. **文献综述**：读取 `papers/<project>/literature/literature_review.md`（如存在）
3. **参考文献**：读取 `papers/<project>/literature/references.bib`（如存在）
4. **实证结果**：读取 `papers/<project>/analysis/output/*.tex`（如存在）
5. 上述文件缺失时，接受用户直接提供：
   - 用户描述研究问题、论点和主要发现
   - 用户提供已有草稿、笔记或其他形式的材料
6. 仍缺失时，向用户追问——一次只问一个问题：
   - "论文的核心论点是什么？"
   - （确认后）"有实证结果或案例证据可以用吗？"

收集完成后向用户确认：

```
"所有素材已就绪。开始写论文前确认几点：

  1. 目标: [硕士毕业论文 / 其他]
  2. 学校格式要求: [已有模板 / 需要选择]
  3. 你想让我先写哪个部分？还是按顺序来？"
```

**完成标准**：目标和素材已确认。

---

## Step 2 — 加载论文模板

### 2.1 加载写作指南

加载硕士学位论文写作指南：`skills/paper-writer/templates/thesis.md`

### 2.2 选择 LaTeX 模板

扫描 `templates/presets/` 和 `templates/custom/` 中的 `manifest.json`，根据论文类型、语言、方法论匹配候选模板，然后向用户展示选项：

```
"选择论文排版模板：

  可用模板：
  1. empirical-zh — 中文社科实证论文（经济研究格式）（推荐）
  2. [其他匹配的模板...]
  3. 不使用模板 — 我自己提供 / 后续在 Overleaf 排版
  4. 上传自定义模板 — 把你的 .cls/.tex 文件放入 templates/custom/

你想用哪个？"
```

用户选择后：
- 选择内置/自定义模板 → 将模板文件复制到项目的 `paper/` 目录
- 选择"不使用模板" → 只生成纯文本/Markdown 内容，用户自行排版
- 选择"上传自定义" → 引导用户将文件放入 `templates/custom/<name>/`，创建 `manifest.json`

**完成标准**：写作指南已加载，排版模板已确认或用户明确跳过。

---

## Step 3 — 规划章节结构

根据 `research_proposal.md`（如存在）和已有素材，确定正文的章节划分。

### 规划依据

- 研究类型（实证/案例/规范/混合）→ 参考 `thesis.md` 中的结构示例
- 已有内容：文献综述是否独立成章、是否有多组实证等
- 用户偏好：如用户已有想法，以用户为准

### 执行流程

1. 根据素材拟定章节大纲，向用户展示：

```
"根据你的研究计划，建议正文按以下章节组织：

  第1章 导论
  第2章 文献综述
  第3章 理论框架与研究假设
  第4章 研究设计
  第5章 实证结果与分析
  第6章 结论与政策建议

确认后我会创建章节文件并开始写作。要调整吗？"
```

2. 用户确认后：
   - 在 `paper/sections/` 下创建对应的 `.tex` 文件（空文件 + 章标题）
   - 更新 `main.tex` 中 `\mainmatter` 后的 `\input{sections/...}` 列表
   - 确保文件名与 `\input` 路径一致

3. 如用户要求调整，修改后重复确认。

**完成标准**：章节结构已确认，`sections/` 文件已创建，`main.tex` 已更新。

---

## Step 4 — 写作

### 各章节要点

**引言**
- 第一段直奔主题（不要从宏观背景写起）
- 明确贡献点（3个以内，具体而非笼统）
- 预告核心发现（一句话）
- "本文的边际贡献在于..."

**文献综述**
- 从 `literature_review.md` 整合
- 按主题而非时间序列组织
- 每段结尾点明与本文的关系
- 明确指出"现有研究的不足在于..."

**研究设计**
- 模型写成公式（LaTeX）
- 变量定义列表（表格形式）
- 识别策略的详细论证（为什么可信）
- 数据来源明确标注

**实证结果**
- 每张表前先用文字引导读者关注什么
- 解读系数的经济含义（不只看显著性）
- 表格标题自解释（不看正文也能理解）
- 从 `analysis/output/*.tex` 直接引用

**完成标准**：每节已写完，无 TODO 占位符，数字均可追溯到源文件。

---

## AI 写作模式（预防）

写作过程中主动避开 `skills/shared/ai-writing-patterns.md` 中列出的高频 AI 写作模式。深度诊断在投稿前由 integrity-auditor 执行。

---

## 引用格式

**中文期刊（GB/T 7714）**
```
[1] 作者. 文章标题[J]. 期刊名, 年, 卷(期): 页码.
[2] 作者. 书名[M]. 出版地: 出版社, 年.
```

**英文期刊（APA / 期刊要求）**
```latex
\bibliographystyle{apalike}
\bibliography{references}
```

---

## 质量 Checklist

- [ ] 结构完整（引言→文献→方法→结果→结论）
- [ ] 论文中的每个数字都可追溯到 analysis/output/ 中的表格
- [ ] 所有引用来自 references.bib（无凭空引用）
- [ ] AI 写作痕迹已检查和修正
- [ ] 研究贡献明确列出（不超过 3 点）
- [ ] 论文长度符合目标要求
- [ ] 表格标题自解释
- [ ] 摘要包含：问题、方法、发现、含义（各一句）
- [ ] 每个章节内容完整，无 TODO 占位符

---

## 输出

```
papers/<project>/paper/main.tex
papers/<project>/paper/sections/*.tex（由 Step 3 规划确定）
papers/<project>/paper/main.pdf（如 TeX Live 可用）
```

---

## 完成后的标准输出

```
✅ 论文写作完成

📄 产出: 
  - main.tex（全文 LaTeX）
  - 分章节文件
  - [已编译 PDF / 未编译，建议使用 Overleaf]

📊 评价:
  - 全文约 [X] 字/词
  - 结构: [完整/缺少XX部分]
  - AI 痕迹检查: [已修正 X 处]

➡️ 建议下一步:
  1. integrity-auditor — 验证引用真实性和数字一致性（推荐）
  2. 你自己通读一遍后告诉我要修改的地方

⚠️ 提醒: AI 辅助写作建议在论文中声明
```

---

## 行为准则

1. 论文中每个数字必须追溯到 analysis/output/ 的实证结果
2. 标记 placeholder 内容为 TODO（不用 AI 编造的数据填充）
3. 引用只来自 references.bib
4. 写作风格根据论文类型和章节内容调整
5. 不替用户做理论贡献的判断——呈现事实，让用户决定怎么定位
