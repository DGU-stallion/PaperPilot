---
name: paper-writer
description: Manuscript assembly — use when the user wants to write or revise any section of the paper, integrate upstream results into a draft, or produce a complete manuscript. Looks for research question and through-line in 00_research_proposal.md (sections 二/三), literature in 01_literature_review.md, and results in analysis/output/; asks user if any are absent.
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

1. **研究问题和框架**：读取 `papers/<project>/topics/00_research_proposal.md`（如存在）
2. **文献综述**：读取 `papers/<project>/literature/01_literature_review.md`（如存在）
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

  1. 论文类型: [期刊论文/学位论文/会议论文]
  2. 目标期刊/要求: [如有]
  3. 语言: [中文/英文]
  4. 你想让我先写哪个部分？还是按顺序来？

建议的写作顺序:
  引言 → 文献综述 → 研究设计 → 实证结果 → 稳健性 → 结论 → 摘要（最后写）"
```

**完成标准**：论文类型、语言、写作起点已确认，素材已整理。

---

## Step 2 — 加载论文结构模板

根据确认的论文类型加载对应模板：

| 类型 | Context pointer |
|------|----------------|
| 中文社科期刊 | `skills/paper-writer/templates/zh-journal.md` |
| 英文经济学期刊 | `skills/paper-writer/templates/en-journal.md` |
| 学位论文 | `skills/paper-writer/templates/thesis.md` |

---

## Step 3 — 写作

### 各章节要点

**引言**
- 第一段直奔主题（不要从宏观背景写起）
- 明确贡献点（3个以内，具体而非笼统）
- 预告核心发现（一句话）
- "本文的边际贡献在于..."

**文献综述**
- 从 `01_literature_review.md` 整合
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
papers/<project>/paper/sections/01_introduction.tex
papers/<project>/paper/sections/02_literature.tex
papers/<project>/paper/sections/03_methodology.tex
papers/<project>/paper/sections/04_results.tex
papers/<project>/paper/sections/05_robustness.tex
papers/<project>/paper/sections/06_conclusion.tex
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
4. 写作风格根据目标（中文期刊/英文期刊/学位论文）调整
5. 不替用户做理论贡献的判断——呈现事实，让用户决定怎么定位
