---
name: empirical-analysis
description: Causal identification — use when the user wants to run regressions, choose an identification strategy, test parallel trends, run robustness checks, or interpret empirical results. Looks for research question and identification strategy in 00_research_proposal.md, data path in 02_data_report.md; asks user if either is absent.
version: 7.0.0
produces:
  - analysis/03_analysis_report.md
output_dir: analysis/
optional: true
---

# Empirical Analysis

## 职责边界

**所需信息**：研究问题 + 识别策略 + 数据文件路径。  
**产出**：`analysis/output/` 下的回归表格和图形 + `analysis/03_analysis_report.md`。  
**完成标准**：基准回归完成，至少 3 种稳健性检验通过，关键识别假设有检验支撑（如平行趋势）。  
**不做**：数据清洗（→ data-collector）、结果写入论文正文（→ paper-writer）。

---

## Step 1 — 收集所需信息

查找顺序：

1. **研究问题 + 识别策略**：读取 `papers/<project>/topics/00_research_proposal.md`（如存在）
2. **数据文件路径**：读取 `papers/<project>/data/02_data_report.md`（如存在），或查找 `data/clean/` 下的数据文件
3. 上述来源仍缺失时，接受用户直接提供：
   - 用户直接描述研究问题和识别策略
   - 用户指定数据文件路径（任意路径，不限于 `data/clean/`）
   - 用户上传或粘贴数据说明
4. 仍缺失时，向用户追问——一次只问一个问题：
   - "研究问题是什么？用的是什么识别策略（FE/DID/IV/RDD等）？"
   - （确认后）"数据文件在哪里？格式是什么？"

信息收集完成后，向用户确认模型设定：

```
"根据你的研究设计：
  - Y: [变量]
  - D: [变量]  
  - 识别策略: [方法]
  - 数据: [N]×[T] 面板 / [N] 截面

我建议的分析路线是：
  1. 描述性统计 → 2. 基准回归 → 3. 稳健性检验 → 4. 异质性分析 → 5. 机制分析（可选）

你有特殊的模型设定想法吗？还是按标准路线走？"
```

**完成标准**：Y/D 变量、识别策略、数据文件路径均已确认，模型路线已确认。

---

## Step 2 — 模型选择

根据识别策略和数据特征选择具体模型：

```
识别策略已确定？
├── FE（固定效应）
│   ├── 数据: 面板数据（N>T 为佳）
│   ├── 基准: xtreg / PanelOLS, entity FE + time FE
│   ├── 检验: Hausman (FE vs RE), F-test for FE significance
│   └── 注意: 不随时间变化的变量会被吸收
│
├── DID（双重差分）
│   ├── 标准 DID (2期2组)
│   │   ├── 模型: Y = α + β(Treat×Post) + γX + FE + ε
│   │   ├── 关键检验: 平行趋势
│   │   └── 注意: 预期效应、处理时点选择
│   ├── 多期 DID (Staggered)
│   │   ├── 问题: TWFE 在异质处理效应下有偏
│   │   ├── 推荐: Callaway-Sant'Anna / Sun-Abraham / BJS
│   │   └── 检验: 事件研究图 (event study plot)
│   └── 共同趋势检验
│       ├── 事前趋势图
│       ├── 安慰剂检验 (placebo test)
│       └── PSM-DID (如组间差异大)
│
├── IV（工具变量）
│   ├── 模型: 2SLS
│   ├── 一阶段: D = π*Z + ... → F-statistic > 10 (Stock-Yogo)
│   ├── 排他性: 理论论证 + 过度识别检验 (Hansen J, 多工具时)
│   ├── 弱工具变量: Anderson-Rubin / CLR (弱IV稳健推断)
│   └── 常见工具: 地理距离、历史变量、Bartik shift-share
│
├── RDD（断点回归）
│   ├── Sharp RDD: 门槛处 treatment 从 0 跳到 1
│   ├── Fuzzy RDD: 门槛处 treatment 概率跳跃
│   ├── 带宽选择: CCT optimal bandwidth (rdrobust)
│   ├── 检验: McCrary density test (manipulation)
│   ├── 检验: 预定变量在断点处的连续性
│   └── 可视化: 断点两侧的散点图 + 拟合线
│
└── 其他
    ├── Synthetic Control: 比较案例研究
    ├── Bunching: 税收/规制门槛处的聚集
    └── Double ML: 高维控制变量
```

---

## Step 3 — 执行分析

### 描述性统计

```
输出:
- 全样本描述性统计表 (N, mean, sd, min, p25, median, p75, max)
- 核心变量的相关系数矩阵
- 分组统计（如处理组/控制组对比）
- 时间趋势图（Y 和 D 的年度均值）
```

### 基准回归

```
标准报告内容:
- 逐步加入控制变量（展示系数稳定性）
  Col(1): Y = β*D + FE
  Col(2): Y = β*D + X₁ + FE
  Col(3): Y = β*D + X₁ + X₂ + FE（完整模型）
- 报告: 系数、标准误(聚类层级)、显著性、N、R²、F-stat
- 标准误选择: 通常聚类到处理分配的层级
```

### 稳健性检验

```
必做检验（根据识别策略选择）:
┌─────────────────────────────────────────────────────┐
│ 通用                                                 │
│  - 替换核心变量度量方式                                │
│  - 缩尾处理 (winsorize 1%/99%)                        │
│  - 排除异常样本                                       │
│  - 更换标准误聚类层级                                  │
│  - 加入更多/更少控制变量                               │
├─────────────────────────────────────────────────────┤
│ DID 专用                                             │
│  - 平行趋势检验 (事前各期系数不显著)                    │
│  - 安慰剂检验 (虚假处理时间)                           │
│  - 排除其他同期政策干扰                                │
│  - PSM-DID (如组间差异大)                              │
├─────────────────────────────────────────────────────┤
│ IV 专用                                              │
│  - 弱工具变量检验 (一阶段 F > 10)                      │
│  - 过度识别检验 (Hansen J, 如有多工具)                  │
│  - 排除约束检验                                       │
│  - 替代工具变量                                       │
├─────────────────────────────────────────────────────┤
│ RDD 专用                                             │
│  - 不同带宽的敏感性分析                                │
│  - McCrary 密度检验                                   │
│  - 预定变量连续性                                     │
│  - 高阶多项式拟合                                     │
└─────────────────────────────────────────────────────┘
```

### 异质性分析

```
常见异质性维度:
- 地区异质性（东/中/西部，发达/欠发达）
- 规模异质性（大/中小企业）
- 时间异质性（前期/后期）
- 群体异质性（按某特征分组）
- 程度异质性（门槛效应 / 分位数回归）
```

### 机制分析（可选）

```
常用方法:
- 中介效应: Y = c'D + bM + e; M = aD + e（逐步法 / bootstrap）
- 调节效应: Y = β₁D + β₂D×Moderator + ...
- 渠道检验: 将 Y 替换为中间变量，检验 D 是否显著
```

**完成标准**：基准回归完成，≥3 种稳健性检验通过，关键识别假设（如平行趋势）有检验支撑。

---

## Backend Tiers

| Tier | 安装方式 | 可用方法 |
|------|---------|---------|
| **builtin** | `pip install paperpilot[standard]` | FE, DID (interaction), Threshold (Hansen grid) |
| **diff-diff** | `pip install diff-diff` | Callaway-Sant'Anna, Staggered DID, Synthetic DID |
| **statspai** | `pip install statspai` | IV, RDD, Synthetic Control, Double ML |

无任何 backend 时：进入**指导模式**——生成模型设定说明和 Stata/R/Python 代码模板，但不执行。

---

## 结果解读

每个回归结果，主动给出解读：

```
"基准回归结果：
  - D 的系数为 [β]，在 [1%/5%/10%] 水平显著
  - 经济含义: D 每增加一个单位/标准差，Y [增加/减少] [X] 个单位/[Y%]
  - 系数在加入控制变量后 [稳定/有变化]，说明 [遗漏变量偏误可能性]
  - R² = [X]，模型解释力 [判断]"
```

---

## 质量 Checklist

- [ ] 模型设定有理论依据
- [ ] 标准误选择合理（聚类层级正确）
- [ ] 至少 3 种稳健性检验
- [ ] 关键识别假设有检验支撑（如平行趋势）
- [ ] 结果表格格式规范（系数、标准误、显著性、N、R²）
- [ ] 所有回归结果可复现（代码 + 种子已记录）
- [ ] 异质性分析维度与理论一致
- [ ] 不存在 p-hacking 嫌疑（不挑选显著的子样本报告）

---

## 输出

```
papers/<project>/analysis/output/      ← 表格和图（语义命名，如 baseline_regression.tex、fig_event_study.pdf）
papers/<project>/analysis/scripts/     ← 可复现分析脚本（按步骤编号，如 01_descriptive.py）
papers/<project>/analysis/03_analysis_report.md
```

**命名规则**：每个项目只输出一个 md 文件，编号 `03_`，固定放在 `analysis/` 目录根部。`output/` 下的表格和图按语义命名，不使用数字前缀。

---

## 行为准则

1. 所有回归结果标记为 `executed` — LLM 估算的数字绝不标记为 executed
2. 记录随机种子（placebo test 等随机性检验）
3. 缺少依赖时返回安装提示而非报错，降级为指导模式
4. 不做 p-hacking：不因为某子样本恰好显著就只报告该结果
5. 标准误选择必须有依据，不默认用最"好看"的
