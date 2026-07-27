# PaperPilot Agent 安装契约

本文档供 Claude Code、Codex、Kiro、Cursor、OpenCode 等 Coding Agent 执行。用户不应被要求手动完成 Agent 可以安全完成的命令。

## 安全边界

1. 默认只在当前项目目录内操作，并使用隔离虚拟环境 `.venv`。
2. 不要上传用户的论文、原始数据、清洗数据、密钥或本地路径。
3. 不要把 API Key 写入仓库、日志或示例文件。
4. 安装 TeX Live、R、Stata、Node 等大型或系统级软件前必须说明体积、用途和替代方案，并获得用户确认。
5. 不要静默修改 Agent 的全局配置；优先使用仓库级配置。
6. 检测行为不得隐式下载 MCP 或启动长期后台进程。

## 标准安装流程

### 1. 获取仓库

如果当前目录不是 PaperPilot 仓库，克隆：

```bash
git clone https://github.com/DGU-stallion/PaperPilot.git
cd PaperPilot
```

如果仓库已存在，先检查工作区；不要覆盖用户未提交的修改。

### 2. 运行无修改诊断

```bash
python3 install/bootstrap.py --check --profile standard --json
```

读取 JSON 中的 `status`、`capabilities` 和 `recommendations`。不要仅根据命令退出码宣称所有能力均已就绪。

### 3. 安装 Standard 环境

Standard 是默认档位，包含 pandas 数据处理、Excel/Parquet 和 PanelOLS/DID 分析能力。

macOS/Linux：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r install/requirements-standard.txt
```

Windows PowerShell：

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r install\requirements-standard.txt
```

### 4. 重新诊断

```bash
.venv/bin/python install/bootstrap.py --check --profile standard --json
```

### 5. 搜索能力检测与配置

安装完成后，检测以下搜索能力：

#### paper-search-mcp（学术文献检索 — 推荐安装）

用途：精确搜索学术论文、追踪引用链、批量获取论文元数据、下载 PDF。覆盖 arXiv、Semantic Scholar、PubMed、Crossref、OpenAlex、SSRN 等 20+ 学术源。

检测方式：

```bash
pip show paper-search-mcp 2>/dev/null && echo "已安装" || echo "未安装"
```

安装方式（如未安装，向用户说明用途后推荐安装）：

```bash
pip install paper-search-mcp
```

MCP 配置（根据用户的 Agent 平台选择对应格式）：

Kiro（`.kiro/settings/mcp.json`）：
```json
{
  "mcpServers": {
    "paper-search": {
      "command": "python",
      "args": ["-m", "paper_search_mcp.server"],
      "env": {
        "SCHOLAR_SEARCH_ENABLE_SEMANTIC_SCHOLAR": "true",
        "SCHOLAR_SEARCH_ENABLE_ARXIV": "true"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Claude Code：
```bash
claude mcp add paper-search -- python -m paper_search_mcp.server
```

所有 API Key 均为可选。无 Key 即可使用基础功能，有 Key 可提升速率限制。

#### web-access（联网与数据获取 — 项目内置）

用途：提供 WebSearch / WebFetch / curl下载 / CDP浏览器 四层通道调度，用于选题验证、数据源定位、网页数据爬取、文件下载等。是数据搜集阶段实际获取文件和结构化数据的关键能力。

**本 skill 已内置于项目 `skills/web-access/` 中，无需额外安装。** Agent 读取 `skills/web-access/SKILL.md` 即可获得完整联网策略。

基础能力检测（层级 1-2，无额外依赖）：

```bash
# 检查 curl 可用性（macOS/Linux 默认自带）
which curl && echo "✓ curl 可用" || echo "✗ curl 不可用"
```

增强能力检测（层级 3，CDP 浏览器自动化，可选）：

```bash
# 检查 Node.js 版本（需要 22+）
node --version 2>/dev/null | grep -E "v(2[2-9]|[3-9][0-9])" && echo "✓ Node.js 22+" || echo "△ Node.js <22 或未安装，CDP 模式不可用（不影响基础功能）"
```

CDP 模式前置配置（仅在需要登录态/动态交互时使用）：
1. 在浏览器地址栏打开：Chrome `chrome://inspect/#remote-debugging` 或 Edge `edge://inspect/#remote-debugging`
2. 勾选 "Allow remote debugging for this browser instance"

**层级 1-2（WebSearch + WebFetch + curl）已足够完成绝大多数研究任务。** CDP 模式为可选增强，仅在需要登录态或反爬严格的站点时使用。

#### 能力降级说明

| 缺少 | 影响 | 替代方案 |
|------|------|---------|
| paper-search-mcp | 学术文献搜索降为通用搜索 | web-access 通过 WebSearch 访问 Google Scholar / Semantic Scholar |
| Node.js 22+ | CDP 浏览器模式不可用 | web-access 层级 1-2 仍可完成大部分任务（WebSearch + WebFetch + curl） |
| 两者都无 | 搜索能力受限 | 需要用户手动提供文献列表和数据源 |

### 6. 加载 Skill

读取 `CLAUDE.md` 了解行为契约。不同 Agent 的适配器在 `adapters/` 中提供。

### 7. 验证和报告

至少运行：

```bash
.venv/bin/python -m unittest tests/test_bootstrap.py -v
```

### 8. 报告并引导下一步

向用户报告：

- 安装档位和仓库路径
- 已启用能力（含搜索能力）
- 未启用能力及影响
- 测试结果

**然后引导用户选择下一步**（不要假设用户已有论文项目）：

```
PaperPilot 安装完成。你想：

1. 开始一篇新论文 — 我会先了解你的背景和研究想法
2. 导入已有论文项目 — 告诉我项目路径，我来诊断状态
3. 看一下 Demo — 了解完整流程是什么样的
```

只有用户选择 2（导入已有项目）时，才执行 `pp inspect`。
选择 1 时，进入 paper-agent 的 onboarding 对话流程。

不要把"脚本运行成功"表述为"全部研究能力可用"；以 Doctor 的能力矩阵为准。
