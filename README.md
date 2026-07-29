# PaperPilot

> 从选题到发表的 AI 科研协作技能包

PaperPilot 是一套以 Skills 形式运行于 Claude Code、Codex、Kiro、Cursor 等通用 Coding Agent 的科研协作系统。它不是一个独立 Agent，而是赋能已有 Agent 的技能包——安装后，你的 Agent 就变成了一个懂学术规范、能搜文献、会跑实证的研究伙伴。

[![Version](https://img.shields.io/badge/version-7.0.0-blue)](https://github.com/DGU-stallion/PaperPilot)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

---

## 安装

### 方式一：一键脚本（推荐）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/DGU-stallion/PaperPilot/main/install.sh)
```

### 方式二：让 Coding Agent 安装

将这段话复制给你的 Coding Agent（Claude Code / Kiro / Cursor / Codex）：

```text
请为我安装 PaperPilot：https://github.com/DGU-stallion/PaperPilot
读取 AGENT_INSTALL.md 完成安装和搜索能力配置，然后引导我开始。
```

安装完成后 Agent 会询问你想做什么，不会假设你已有论文项目。

---

## 它能做什么

安装后，你可以直接用自然语言和 Agent 对话：

```
"我想研究数字经济对就业的影响"
→ Agent 会先了解你的背景，再引导你一步步推进

"帮我搜一下这个方向的文献"
→ 通过学术搜索 MCP 精确检索 20+ 学术数据库

"数据清洗完了，帮我跑回归"
→ 根据你的识别策略自动设定模型并执行

"论文写好了，帮我检查引用是否真实"
→ 逐条验证 BibTeX 引用，检查数字一致性
```

---

## 核心设计

### 导师式引导

PaperPilot 不是一个等指令的工具。它会：
- **先了解你**：学历、专业、研究经验、当前想法成熟度
- **主动给建议**：基于搜索结果和学术经验判断方向可行性
- **根据你的水平调整**：新手详细解释为什么，有经验者直接给选项
- **主动报告问题**：发现高度相似论文、数据风险等不等你问就说

### Skills 架构

```
[paperpilot]  ← 论文领航员：了解用户 + 诊断 + 编排 + 主动引导
   │
   ├── topic-explorer        选题探索 (发散-收敛 → 研究计划书)
   ├── paper-search          文献搜索 (锚点深搜 → 验证 → 清单 + .bib)
   ├── literature-review     文献综述 (主题提炼 → 结构规划 → 成文)
   ├── data-collector        数据搜集 (数据源定位 → 清洗 → 面板验证)
   ├── empirical-analysis    实证分析 (FE/DID/IV/RDD + 稳健性, 可选)
   ├── paper-writer          论文写作 (结构规范 + LaTeX + AI痕迹检查)
   └── integrity-auditor     审查 (引用验证 + 数字一致性 + 可追溯性)
```

每个 skill 包含完整的执行指南：对话策略、领域知识、搜索方法、质量标准。

### 搜索能力

| 任务 | 工具 | 说明 |
|------|------|------|
| 学术文献检索 | paper-search-mcp | 20+ 学术源（arXiv、Semantic Scholar、SSRN 等），免费 |
| 信息侦察 | web-access | 选题验证、政策背景、数据源定位 |
| 兜底 | Agent 内置搜索 | 无需配置，基础可用 |

### 证据状态追踪

| 状态 | 含义 |
|------|------|
| planned | 已计划但未执行 |
| user_supplied | 研究者提供（非机器验证） |
| executed | 代码执行产生 |
| verified | 通过验证检查 |

LLM 生成内容绝不标记为 executed 或 verified。

---

## 项目结构

```
paperpilot/
├── CLAUDE.md                 # Agent 行为规范（加载入口）
├── SKILL.md                  # 项目级 skill manifest
├── AGENT_INSTALL.md          # Agent 安装契约
├── install.sh                # 一键安装脚本
│
├── skills/                   # 技能包（核心内容）
│   ├── AGENTS.md             #   paperpilot：用户画像 + 编排 + 搜索策略
│   ├── topic-explorer/       #   选题探索
│   ├── paper-search/         #   文献搜索
│   ├── literature-review/    #   文献综述写作
│   ├── data-collector/       #   数据搜集
│   ├── empirical-analysis/   #   实证分析（可选）
│   ├── paper-writer/         #   论文写作
│   └── integrity-auditor/    #   审查
│
├── scripts/                  # Python 后端
├── papers/                   # 论文项目目录
├── adapters/                 # Agent 薄适配器
└── tests/                    # 测试（80 tests）
```

---

## 开发

```bash
python3 -m pytest tests/ -v       # 运行测试
pp doctor --json                   # 检查环境
```

详见 [docs/UPGRADE_PLAN_V6.md](docs/UPGRADE_PLAN_V6.md)。

## 许可证

MIT License. 详见 [LICENSE](LICENSE).
