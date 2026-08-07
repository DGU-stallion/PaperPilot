# PaperPilot 模板系统

## 目录结构

```
templates/
├── skeleton/       ← 通用项目骨架（所有论文类型共用）
├── presets/        ← 内置论文模板预设
│   └── empirical-zh/   中文社科实证论文（经济研究格式）
└── custom/         ← 用户自定义模板（已 gitignore）
```

## 工作方式

创建新论文项目时：

1. **复制 `skeleton/`** → 建立通用目录结构（topics, literature, data, analysis, paper）
2. **选择模板** → 从 `presets/` 或 `custom/` 中选择论文模板，覆盖到 `paper/` 目录

## skeleton — 通用项目骨架

所有论文项目共用的目录结构，不含任何特定格式文件：

```
skeleton/
├── topics/              选题研究、研究计划书
├── literature/          文献综述和参考文献
├── data/
│   ├── raw/             原始数据
│   ├── clean/           清洗后数据
│   └── scripts/         数据处理脚本
├── analysis/
│   └── output/          分析结果（表格、图表）
└── paper/
    ├── sections/        论文章节
    └── tables/          表格文件
```

## presets — 内置模板预设

| 模板 | 说明 | 适用场景 |
|------|------|---------|
| `empirical-zh` | 《经济研究》格式，XeLaTeX + Biber | 中文经济学/管理学实证论文 |

每个预设包含 `manifest.json` 描述元信息，Agent 根据论文类型自动匹配推荐。

## custom — 用户自定义

见 [`custom/README.md`](custom/README.md)。

自定义模板放在此目录下，不会被 git 追踪。你可以：
- 复制 `presets/` 中的模板修改
- 从零创建自己的模板
- 上传已有的 LaTeX 模板

## 模板选择流程

进入写作阶段时，PaperPilot 会：

1. 根据论文类型（实证/质性/学位论文等）自动匹配候选模板
2. 列出可用模板（内置 + 自定义），询问用户选择
3. 用户也可选择上传自己的模板文件或不使用模板

你不需要手动操作此目录。告诉 Agent "我想开始写论文" 即可。
