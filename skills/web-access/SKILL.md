---
name: web-access
description: |
  PaperPilot 的底层联网能力层。所有联网操作（搜索、网页抓取、文件下载、登录后操作）统一由此 skill 调度。
  各阶段 skill（选题/文献/数据/写作）通过声明搜索意图调用本 skill，本 skill 负责通道选择和实际执行。
version: "1.0.0"
based_on: "eze-is/web-access v2.5.3 (MIT License, Author: 一泽Eze)"
triggers:
  - "搜索"
  - "下载"
  - "访问网页"
  - "web search"
  - "fetch"
  - "download"
---

# Web Access Skill

> 基于 [eze-is/web-access](https://github.com/eze-is/web-access) v2.5.3 (MIT)
> 适配为 PaperPilot 内置底层能力层，兼容所有 Agent 平台

## 定位

```
各阶段 skill（选题/文献/数据/分析/写作）
   │ 声明：搜索意图 + 判断标准 + 输出格式
   ▼
web-access（本 skill — 底层能力层）
   │ 执行：通道选择 + 实际获取 + 文件下载 + 站点经验
   ▼
工具层（WebSearch / WebFetch / curl / paper-search-mcp / CDP）
```

**职责边界**：
- 本 skill 负责"怎么联网"——通道选择、执行策略、站点经验、失败处理
- 上游 skill 负责"搜什么"——搜索维度、关键词、结果判断标准、输出格式

---

## 前置检查

在开始联网操作前，检查可用能力层级：

| 层级 | 能力 | 依赖 |
|------|------|------|
| 1（基础） | WebSearch + WebFetch + curl 下载 | 无（Agent 内置） |
| 2（增强） | + paper-search-mcp + tavily | MCP 配置 |
| 3（完整） | + CDP 浏览器自动化 | Node.js 22+ + 浏览器调试 |

CDP 模式检查：

```bash
node "skills/web-access/scripts/check-deps.mjs"
```

- `exit 0` → CDP 可用
- `exit 2` → 需询问用户浏览器偏好
- `exit 1` → CDP 不可用，降级到层级 1-2

**层级 1-2 足够完成绝大多数研究任务。** CDP 主要用于需要登录态或反爬严格的站点。

---

## 浏览哲学

**像人一样思考，兼顾高效与适应性地完成任务。**

**① 拿到请求** — 明确成功标准：什么算完成了？

**② 选择起点** — 根据任务性质选最可能直达的方式验证。

**③ 过程校验** — 每步结果都是证据。方向错了立即调整，不反复重试同一方式。

**④ 完成判断** — 对照成功标准确认完成，不过度操作。

---

## 联网工具选择

**核心原则：搜索不是终点，获取到文件/数据才是。一手信息优于二手信息。**

### 多平台工具映射

| 能力 | Kiro | Claude Code | Cursor / 其他 |
|------|------|-------------|--------------|
| WebSearch | `remote_web_search` / `mcp_tavily_tavily_search` | WebSearch | 内置搜索 |
| WebFetch | `web_fetch` (4种模式) | WebFetch | 内置 fetch |
| 文件下载 | `execute_bash` + `curl -L -o` | bash + curl | terminal + curl |
| 学术搜索 | `mcp_paper_search_*` | paper-search-mcp | paper-search-mcp |
| 高级搜索/提取 | `mcp_tavily_tavily_search/extract/crawl` | tavily | tavily |
| 浏览器CDP | `execute_bash` + CDP Proxy API | CDP Proxy API | CDP Proxy API |

### 场景→通道决策

| 场景 | 工具 |
|------|------|
| 搜索摘要或关键词结果，发现信息来源 | **WebSearch** |
| URL 已知，定向提取特定信息 | **WebFetch** |
| URL 已知，需要原始 HTML（meta、JSON-LD） | **curl** |
| **下载文件（PDF/Excel/CSV/数据集）** | **curl -L -o \<path\> \<url\>** |
| 学术论文搜索/元数据/PDF下载 | **paper-search-mcp** |
| 非公开内容 / 反爬严格的平台 | **浏览器 CDP** |
| 需要登录态、交互操作 | **浏览器 CDP** |
| 动态页面 / JS 渲染 | WebFetch(rendered) → CDP |

**Jina**（可选，节省 token）：`r.jina.ai/example.com`，网页转 Markdown。适合文章/文档；不适合数据面板。限 20 RPM。


---

## 文件下载规范

**搜到 URL 后必须实际下载，不能止步于列清单。**

```bash
# 下载
curl -L -H "User-Agent: Mozilla/5.0" -o "<目标路径>" "<url>"

# 验证
file <downloaded_file>   # 确认类型
wc -c <downloaded_file>  # 确认非零
```

失败处理：
- 403/登录墙 → 标记"需用户手动获取"，给具体步骤
- 0字节/HTML内容（应为PDF） → 换来源或升级到 CDP
- 超时 → 重试一次

---

## 阶段策略扩展点

各阶段 skill 通过以下模式声明搜索需求，web-access 负责执行：

### 策略声明格式

```markdown
### web-access 搜索策略

**搜索意图**: [学术文献 / 数据源定位 / 信息侦察 / 文件获取]
**成功标准**: [什么算完成]
**优先源**: [paper-search-mcp / 巨潮资讯网 / 政府官网 / ...]
**输出要求**: [下载到data/raw/ / 提取文本 / 结构化为CSV / ...]
**失败降级**: [换什么源 / 标记为手动]
```

### 各阶段典型策略

| 阶段 | 搜索意图 | 首选通道 | 成功标准 |
|------|---------|---------|---------|
| 选题探索 | 信息侦察（验证方向） | WebSearch + WebFetch | 获得方向判断依据 |
| 文献调研 | 学术文献检索 + PDF下载 | paper-search-mcp + curl | 论文元数据+PDF存入raw/ |
| 数据搜集 | 数据源定位 + 文件下载 | WebSearch → WebFetch → curl | 数据文件存入data/raw/ |
| 实证分析 | 方法论参考 | paper-search-mcp + WebFetch | 找到模型设定参考 |
| 论文写作 | 规范查询（期刊格式） | WebFetch 直达 | 获取格式要求 |

---

## 浏览器 CDP 模式

通过 CDP Proxy 直连用户日常浏览器（Chrome / Edge），天然携带登录态。

### 启动

```bash
node "skills/web-access/scripts/check-deps.mjs"
```

### Proxy API（localhost:3456）

```bash
curl -s http://localhost:3456/targets                              # 列出 tab
curl -s -X POST --data-raw '<url>' http://localhost:3456/new       # 新建 tab
curl -s -X POST "http://localhost:3456/eval?target=ID" -d '<js>'   # 执行 JS
curl -s "http://localhost:3456/screenshot?target=ID&file=<path>"   # 截图
curl -s -X POST "http://localhost:3456/click?target=ID" -d '<sel>' # 点击
curl -s "http://localhost:3456/scroll?target=ID&direction=bottom"  # 滚动
curl -s -X POST --data-raw '<url>' "http://localhost:3456/navigate?target=ID"  # 导航
curl -s "http://localhost:3456/close?target=ID"                    # 关闭 tab
```

### 何时用 CDP

- 需要登录态（巨潮资讯网会员区、知网全文等）
- 反爬严格（动态加载、需交互才显示内容）
- WebFetch rendered 模式仍失败
- 需要填表、翻页等交互操作

### 操作原则

- 不操作用户已有 tab，在自建后台 tab 中操作
- 完成后 `/close` 自建 tab
- 先了解页面结构，再决定下一步
- GUI 交互产生的链接是可靠的（携带完整上下文）

---

## 并行调研：子 Agent 分治

多个独立目标时，分发子 Agent 并行执行。

| 适合分治 | 不适合分治 |
|----------|-----------|
| 目标独立、互不依赖 | 目标有依赖关系 |
| 每个子任务量足够大 | 简单查询 |
| 需要 CDP 或长时间运行 | 轻量搜索 |

子 Agent prompt 要求：描述目标（获取、调研、了解），不暗示具体手段。

---

## 信息核实

核实的目标是**一手来源**，非二手报道。

| 信息类型 | 一手来源 |
|----------|---------|
| 政策/法规 | 发布机构官网 |
| 企业公告/财报 | 交易所/企业官网 |
| 学术声明 | 原始论文/机构官网 |
| 行业数据 | 数据发布方 |

找不到官方原文时，标明来源局限性。

---

## 站点经验

按域名存储在 `skills/web-access/references/site-patterns/` 下。

- 确定目标网站后，检查是否有匹配经验文件
- 经验是"可能有效的提示"，非保证
- 操作成功后，发现新模式主动写入经验文件

---

## References 索引

| 文件 | 何时加载 |
|------|---------|
| `skills/web-access/references/cdp-api.md` | 需要 CDP API 详细参考时 |
| `skills/web-access/references/site-patterns/{domain}.md` | 确定目标网站后 |
| `skills/web-access/references/migration-2.5.3.md` | 遇到旧写法迁移提示时 |

---

## 行为准则

1. **搜索不是终点**：搜到 URL 后必须获取内容或下载文件
2. **能自动化的不推给用户**：只有登录态/验证码/付费墙才标记"需手动"
3. **下载后验证**：file + wc -c
4. **失败时切换通道**：不在同一方式上反复重试
5. **记录来源**：所有获取的数据记录 URL 和时间
6. **不静默降级**：降级时告知用户原因
7. **站点经验积累**：成功操作后更新经验文件
