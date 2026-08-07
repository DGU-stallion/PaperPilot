# 自定义模板 (Custom Templates)

此目录用于存放你自己的论文模板。该目录已被 `.gitignore` 忽略，不会被提交到 PaperPilot 主仓库。

## 如何创建自定义模板

### 方法一：基于现有预设修改

```bash
# 复制一个内置预设作为起点
cp -r ../presets/empirical-zh/ ./my-template/

# 修改 manifest.json 中的元信息
# 修改 .cls、.tex 等文件适配你的需求
```

### 方法二：从零创建

在此目录下新建文件夹，结构如下：

```
my-template/
├── manifest.json        ← 必须，模板元信息
├── main.tex             ← 主文件
├── sections/            ← 章节文件
│   ├── 01_xxx.tex
│   ├── 02_xxx.tex
│   └── ...
├── tables/              ← 表格模板（可选）
├── image/               ← 图片资源（可选）
└── *.cls / *.sty        ← 样式文件（可选）
```

### manifest.json 格式

```json
{
  "name": "my-template",
  "display_name": "我的自定义模板",
  "description": "适用场景描述",
  "type": "journal | thesis | conference",
  "language": "zh | en",
  "methodology": ["empirical", "qualitative", "mixed"],
  "sections": ["01_introduction", "02_xxx", "..."],
  "compiler": "xelatex | pdflatex | lualatex",
  "bib_tool": "biber | bibtex",
  "cls_file": "your-style.cls",
  "main_file": "main.tex"
}
```

### 字段说明

| 字段 | 必须 | 说明 |
|------|------|------|
| `name` | ✓ | 模板标识符（英文，用于匹配） |
| `display_name` | ✓ | 显示名称（用户可见） |
| `description` | ✓ | 适用场景简述 |
| `type` | ✓ | 论文类型：journal / thesis / conference |
| `language` | ✓ | 主要语言：zh / en |
| `methodology` |  | 适用研究方法 |
| `sections` |  | 章节文件列表（不含扩展名） |
| `compiler` |  | LaTeX 编译器，默认 xelatex |
| `bib_tool` |  | 参考文献工具，默认 biber |
| `cls_file` |  | 样式文件名 |
| `main_file` |  | 主 tex 文件名，默认 main.tex |

## 使用自定义模板

进入写作阶段时，PaperPilot 会列出所有可用模板（内置 + 自定义），询问你使用哪一个。你也可以直接告诉 Agent：

> 用我自己的模板 my-template

Agent 会从 `templates/custom/my-template/` 加载模板文件。

## 贡献模板

如果你的模板对其他人也有用，欢迎将其移到 `templates/presets/` 并提交 PR。
