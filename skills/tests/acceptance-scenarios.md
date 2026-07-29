# PaperPilot Skill 验收场景

每个场景定义：**前置状态 → 输入 → 预期行为 → 完成条件（可检验）**

---

## AGENTS.md（paperpilot 元技能）

### A1：新项目 onboarding
**前置**：`researcher_profile.json` 不存在  
**输入**：用户说"帮我写论文"  
**预期行为**：启动 Q1，等用户回答后再问 Q2，不一次抛出所有问题  
**完成条件**：`researcher_profile.json` 被创建，`user_type` 字段有值

### A2：Retrospective 触发回流
**前置**：`00_research_proposal.md` + `01_literature_review.md` 均存在，文献报告显示核心理论与研究方案不一致  
**输入**：paper-search 完成后的 Agent Guide 输出  
**预期行为**：paperpilot 输出 `🔄 发现需要回流`，列出触发来源和影响范围，询问是否立即修订  
**完成条件**：用户选 N 时，`00_research_proposal.md` 修订记录表新增一行，状态为"待处理"；用户选 Y 时，文件被修改且修订记录更新

### A3：进入 paper-writer 前对齐检测
**前置**：`00_research_proposal.md` 存在，`01_literature_review.md` 存在，`02_data_report.md` 不存在  
**输入**：用户说"开始写论文"  
**预期行为**：paperpilot 指出对齐检测未通过（数据/证据尚未搜集），推荐先完成 data-collector，不直接进入 paper-writer  
**完成条件**：paperpilot 输出包含"对齐检测"说明，推荐 data-collector，未调用 paper-writer

### A4：搜索后给判断
**前置**：任意阶段  
**输入**：完成任意搜索操作  
**预期行为**：输出包含判断性语句（如"方向拥挤""可以推进""有竞争论文"），不只列搜索结果  
**完成条件**：输出中无纯列表式的搜索结果展示

---

## topic-explorer

### T1：描述性问题升级
**前置**：`researcher_profile.json` 存在，`topics/` 目录为空  
**输入**：用户说"我想研究新易盛如何实现价值跃升"  
**预期行为**：识别为描述性问题，主动指出，引导升级到解释性或机制性层面  
**完成条件**：agent 输出中包含对描述性/解释性层次的明确区分说明，未直接生成研究方案

### T2：立即搜索
**前置**：`topics/` 目录为空  
**输入**：用户说"我想研究光通信产业"  
**预期行为**：用户给出具体方向后，agent 立即执行搜索，用搜索结果反馈领域格局，不继续追问  
**完成条件**：搜索在用户表达方向后同一轮完成，输出包含"主流研究在做""相对少人做"类判断

### T3：Through-line 一句话测试
**前置**：用户已完成 Puzzle + 问题聚焦  
**输入**：agent 引导构建 through-line  
**预期行为**：agent 要求用户做一句话测试（"本文以X为研究对象，解释Y，发现Z，对W有V启示"），并等待用户完成  
**完成条件**：`topics/00_research_proposal.md` 只在用户通过测试后创建，文件包含完整的 through-line 字段

### T4：可行性风险报告
**前置**：through-line 依赖企业一手访谈数据  
**输入**：用户表示需要访谈企业管理层  
**预期行为**：agent 指出风险，建议调整 through-line 使其依赖可得证据  
**完成条件**：`00_research_proposal.md` 的"可行性评估"节包含该风险点的记录

---

## paper-search

### L1：关键词来源验证
**前置**：`topics/00_research_proposal.md` 存在  
**输入**：开始文献搜索  
**预期行为**：搜索关键词从研究方案中提取，不自行构造  
**完成条件**：`00_paper_search.md` 的"搜索策略"节注明"关键词来源：00_research_proposal.md"，关键词与研究方案中的核心概念一致

### L2：锚点扩展验证
**前置**：找到第一篇锚点论文  
**输入**：继续文献搜索  
**预期行为**：对每篇锚点论文执行参考文献扩展，候选池在锚点基础上增加  
**完成条件**：`00_paper_search.md` 的搜索漏斗数据中，扩展论文数 > 0（"含锚点扩展 Y 篇"字段）

### L3：高度相似论文处理
**前置**：搜索发现已有论文使用相同理论框架+相同案例  
**输入**：搜索结果包含竞争论文  
**预期行为**：立即向用户报告，分析差异点，不继续推进直到用户确认差异化定位  
**完成条件**：`00_paper_search.md` 的"研究空白初判"节有竞争论文的分析，以及本研究的差异化说明

### L4：下载后验证
**前置**：用户选择下载 PDF  
**输入**：web-access 完成下载  
**预期行为**：执行 `file <path>` 验证文件类型，确认包含"PDF document"，文件命名符合 `{年份}_{标题}.pdf` 规则  
**完成条件**：`literature/pdfs/` 下的文件均为真实 PDF，命名符合规范；下载失败的标记为 `[需手动下载]`

---

## data-collector

### D1：研究类型识别
**前置**：`00_research_proposal.md` 中论文类型为案例研究  
**输入**：开始数据搜集  
**预期行为**：agent 判断研究类型为"案例证据模式"，声明搜集意图，向用户确认证据清单  
**完成条件**：`02_data_report.md` 中记录模式为"案例证据模式"，不生成面板数据清洗脚本

### D2：搜集意图声明（不含执行细节）
**前置**：案例证据模式  
**输入**：需要搜集新易盛年报  
**预期行为**：data-collector 声明搜索意图和成功标准，委托 web-access 执行；不在自身输出中包含 curl 命令或具体 URL 路径  
**完成条件**：data-collector 的输出中有意图声明，实际文件下载操作由 web-access 执行

### D3：三角验证
**前置**：搜集到一条单源证据  
**输入**：财务数据只来自年报，无第二来源  
**预期行为**：agent 标记该事实为单源，询问是否补充第二来源或接受风险  
**完成条件**：`02_data_report.md` 事件时间线中，该事实验证状态为 `△ 单源`，而非 `✓ 双源`

### D4：出口条件检查
**前置**：搜集完成  
**输入**：完成标志  
**预期行为**：检查 through-line 每个关键环节是否有对应证据/变量，存在缺口时报告  
**完成条件**：`02_data_report.md` 有明确的证据覆盖情况说明，覆盖不完整时包含缺口列表

---

## empirical-analysis

### E1：模型选择依据
**前置**：`02_data_report.md` 中识别策略为 DID  
**输入**：开始实证分析  
**预期行为**：agent 按决策树选择 DID 模型，确认平行趋势检验为必做检验  
**完成条件**：`03_analysis_report.md` 中记录平行趋势检验结果，未跳过

### E2：p-hacking 防护
**前置**：基准回归在全样本不显著，某子样本显著  
**输入**：子样本结果  
**预期行为**：agent 报告全部结果，不选择性只展示显著子样本  
**完成条件**：`analysis/output/` 中包含全样本基准回归结果文件，不只有显著子样本

---

## paper-writer

### P1：对齐检测通过后才进入
**前置**：paperpilot 对齐检测三项均通过  
**输入**：进入 paper-writer  
**预期行为**：读取论文类型后，加载对应结构模板（context pointer）  
**完成条件**：agent 明确说明加载了哪种模板（中文社科/英文/学位论文）

### P2：数字可追溯
**前置**：`analysis/output/` 中有基准回归表格  
**输入**：写作实证结果章节  
**预期行为**：正文中的回归系数直接引用 `analysis/output/*.tex`，不自行编造  
**完成条件**：`paper/sections/04_results.tex` 中的数字与 `analysis/output/` 对应文件一致；不存在 AI 自行生成的系数

### P3：无 TODO 占位符（出口条件）
**前置**：所有章节已生成  
**输入**：完成检查  
**预期行为**：扫描所有 `paper/sections/*.tex`，发现 TODO 时标记为未完成，要求填充  
**完成条件**：质量 checklist "无 TODO 占位符" 项为 ✅；如有未填充内容，paper-writer 尚未标记为完成

### P4：AI 写作预防
**前置**：写作过程中  
**输入**：生成某章节  
**预期行为**：避开 `skills/shared/ai-writing-patterns.md` 中的模式；出现时主动修正  
**完成条件**：章节中无"值得注意的是""不难发现"等 patterns 文件中列出的高频词汇

---

## integrity-auditor

### I1：引用逐一验证
**前置**：`references.bib` 包含 20 条引用  
**输入**：开始审查  
**预期行为**：对每条引用调用 paper-search-mcp，记录验证状态  
**完成条件**：`audit/citation_verification.json` 有 20 条记录，每条有状态字段（verified/unverified/suspicious/fabricated）

### I2：fabricated 引用处理
**前置**：发现一条引用在所有数据库找不到  
**输入**：验证结果  
**预期行为**：立即标记为 fabricated，告知用户，建议删除或替换，不自动删除  
**完成条件**：`04_audit_report.md` 的"需要立即修复"节包含该引用的处理建议；引用未被自动删除

### I3：AI 写作扫描使用共享清单
**前置**：`paper/main.tex` 存在  
**输入**：AI 写作检测  
**预期行为**：加载 `skills/shared/ai-writing-patterns.md`，按该文件中的每种模式逐节扫描  
**完成条件**：`04_audit_report.md` 中 AI 写作部分的检测项与 `ai-writing-patterns.md` 中的模式列表一一对应

### I4：数字一致性检查完整性
**前置**：论文中摘要有"显著正效应，系数 0.15"  
**输入**：基准回归表显示系数为 0.12  
**预期行为**：发现不一致，立即记录，精确指出位置（摘要第X句 vs 表X第Y列）  
**完成条件**：`04_audit_report.md` 包含该不一致的精确位置和两处数值的对比

---

## 跨 skill 边界测试

### X1：web-access 职责不越界
**验证方法**：检查 data-collector 和 paper-search 的完成输出，确认其中无 curl 命令、无具体镜像 URL、无 Tavily 同名词干防护逻辑  
**完成条件**：上述执行细节只出现在 web-access/SKILL.md 中

### X2：AI 写作检测 single source of truth
**验证方法**：对比 paper-writer、integrity-auditor 中的 AI 写作相关内容，确认两处均为 context pointer 指向 `skills/shared/ai-writing-patterns.md`，无独立的检测项列表  
**完成条件**：`grep -r "值得注意的是\|It is worth noting" skills/paper-writer/ skills/integrity-auditor/` 结果为空

### X3：引用验证 single source of truth
**验证方法**：paper-search 的"引用验证"只做搜索时同步验证（双源交叉），详细四级分类（verified/unverified/suspicious/fabricated）只在 integrity-auditor 中定义  
**完成条件**：integrity-auditor 中的四级分类是权威定义，paper-search 中无独立的四级分类表
