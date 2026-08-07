% ============================================================
% swufe-thesis.cls — 西南财经大学硕士学位论文 LaTeX 样式
% 依据《西南财经大学关于研究生学位论文形式与格式的基本要求（2019年5月调整）》
% 编译方式: xelatex -> biber -> xelatex -> xelatex
% ============================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{swufe-thesis}[2024/01/01 v1.0 SWUFE Master Thesis]

\LoadClass[a4paper,12pt,twoside,openany]{book}

% ========================
% 宏包加载
% ========================
\RequirePackage[UTF8,scheme=plain,punct=kaiming]{ctex}
\RequirePackage[T1]{fontenc}
\RequirePackage{amsmath,amssymb}
\RequirePackage{graphicx}
\RequirePackage{booktabs}
\RequirePackage{longtable}
\RequirePackage{caption}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{titletoc}
\RequirePackage{hyperref}
\RequirePackage{xcolor}
\RequirePackage[shortlabels,inline]{enumitem}
\RequirePackage{indentfirst}

% ========================
% 页面设置
% 版心：上3.9cm 下3.4cm 左3.45cm 右3.45cm
% 页眉2.8cm 页脚2.5cm
% ========================
\RequirePackage[
  a4paper,
  top=3.9cm,
  bottom=3.4cm,
  left=3.45cm,
  right=3.45cm,
  headheight=14pt,
  headsep=0.6cm,
  footskip=1.0cm
]{geometry}

% ========================
% 字体设置
% 正文：宋体小4号（12pt）
% ========================
\setCJKmainfont{STSong}[
  BoldFont=STHeiti,
  ItalicFont=STKaiti
]
\setCJKsansfont{STHeiti}
\setCJKmonofont{STFangsong}

% 小标宋（用于一级标题，如无该字体则用宋体加粗替代）
\newCJKfontfamily\xiaobiaosong{STSong}[BoldFont=STHeiti]

% 正文小4号 = 12pt（已在 \LoadClass 中设定）
\renewcommand{\normalsize}{\fontsize{12pt}{16.44pt}\selectfont}  % 行距1.37倍

% ========================
% 行距设置
% 多倍行距 1.37
% ========================
\linespread{1.37}
\setlength{\parindent}{2em}
\setlength{\parskip}{0pt}

% ========================
% 标题格式
% 一级标题：2号小标宋（约22pt）
% 二级标题：小3号黑体（约15pt）
% 三级标题：小4号黑体（12pt）
% 编号格式：1. / 1.1 / 1.1.1
% ========================
\titleformat{\chapter}[block]
  {\centering\fontsize{22pt}{30pt}\selectfont\xiaobiaosong\bfseries}
  {\thechapter\quad}
  {0pt}
  {}
\titlespacing*{\chapter}{0pt}{0pt}{20pt}

\titleformat{\section}[hang]
  {\fontsize{15pt}{22pt}\selectfont\heiti}
  {\thesection\quad}
  {0pt}
  {}
\titlespacing*{\section}{0pt}{12pt}{6pt}

\titleformat{\subsection}[hang]
  {\fontsize{12pt}{16.44pt}\selectfont\heiti}
  {\thesubsection\quad}
  {0pt}
  {}
\titlespacing*{\subsection}{0pt}{6pt}{3pt}

% 章编号格式：阿拉伯数字
\renewcommand{\thechapter}{\arabic{chapter}}
\renewcommand{\thesection}{\thechapter.\arabic{section}}
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}

% ========================
% 图表格式
% 图表字号：5号（10.5pt）
% 表题：黑体
% 表注：小5号宋体（9pt）
% 图表上下各空0.5行
% ========================
\captionsetup{
  font=small,
  labelsep=quad,
  skip=6pt
}
\captionsetup[table]{
  labelfont=bf,
  font=small
}
\captionsetup[figure]{
  font=small
}

% ========================
% 页眉页脚
% 宋体小5号（9pt）
% 奇偶页不同
% ========================
\pagestyle{fancy}
\fancyhf{}
\fancyhead[CO]{\fontsize{9pt}{12pt}\selectfont\leftmark}
\fancyhead[CE]{\fontsize{9pt}{12pt}\selectfont 西南财经大学硕士学位论文}
\fancyfoot[C]{\fontsize{9pt}{12pt}\selectfont\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0pt}

% 章节首页也使用 fancy 样式
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyfoot[C]{\fontsize{9pt}{12pt}\selectfont\thepage}
  \renewcommand{\headrulewidth}{0pt}
}

% ========================
% 超链接设置
% ========================
\hypersetup{
  colorlinks=false,
  pdfborder={0 0 0},
  linktoc=all
}

% ========================
% 目录设置
% ========================
\setcounter{tocdepth}{2}
\setcounter{secnumdepth}{3}

% ========================
% 参考文献（GB/T 7714）
% ========================
\RequirePackage[backend=biber,style=gb7714-2015]{biblatex}
\renewcommand*{\bibfont}{\small}

% ========================
% 脚注格式
% ========================
\renewcommand{\thefootnote}{\arabic{footnote}}
\renewcommand{\footnotesize}{\fontsize{9pt}{12pt}\selectfont}

% ========================
% 论文元信息命令
% ========================
\newtoks\entitle
\newtoks\enauthor
\newcommand{\studentid}[1]{\def\@studentid{#1}}
\newcommand{\major}[1]{\def\@major{#1}}
\newcommand{\research}[1]{\def\@research{#1}}
\newcommand{\advisor}[1]{\def\@advisor{#1}}
\newcommand{\finishdate}[1]{\def\@finishdate{#1}}
\newcommand{\classification}[1]{\def\@classification{#1}}
\newcommand{\udc}[1]{\def\@udc{#1}}
\newcommand{\secretlevel}[1]{\def\@secretlevel{#1}}

% 默认值
\studentid{}
\major{}
\research{}
\advisor{}
\finishdate{}
\classification{}
\udc{}
\secretlevel{}

% ========================
% 摘要环境
% ========================
\newenvironment{abstractzh}{%
  \chapter*{摘\quad 要}
  \addcontentsline{toc}{chapter}{摘要}
}{}

\newcommand{\keywordszh}[1]{%
  \par\vspace{1em}\noindent\textbf{关键词：}#1
}

\newenvironment{abstracten}{%
  \chapter*{Abstract}
  \addcontentsline{toc}{chapter}{Abstract}
}{}

\newcommand{\keywordsen}[1]{%
  \par\vspace{1em}\noindent\textbf{Keywords:} #1
}

% ========================
% 后记、致谢、科研成果环境
% ========================
\newenvironment{postscript}{%
  \chapter*{后\quad 记}
  \addcontentsline{toc}{chapter}{后记}
}{}

\newenvironment{acknowledgement}{%
  \chapter*{致\quad 谢}
  \addcontentsline{toc}{chapter}{致谢}
}{}

\newenvironment{publications}{%
  \chapter*{在读期间科研成果目录}
  \addcontentsline{toc}{chapter}{在读期间科研成果目录}
}{}

% ========================
% 声明页命令
% ========================
\newcommand{\makedeclaration}{%
  \chapter*{}
  \thispagestyle{empty}
  \begin{center}
    \fontsize{16pt}{24pt}\selectfont\heiti
    西南财经大学学位论文原创性及知识产权声明
  \end{center}
  \vspace{1em}
  \normalsize
  本人郑重声明：所呈交的学位论文，是本人在导师的指导下独立进行研究工作所取得的成果。除文中已经注明引用的内容外，本论文不含任何其他个人或集体已经发表或撰写过的作品成果。对本文的研究做出重要贡献的个人和集体，均已在文中以明确方式标明，因本学位论文引起的法律结果完全由本人承担。

  \vspace{0.5em}
  本人同意在校攻读学位期间论文工作的知识产权单位属西南财经大学。本人完全了解西南财经大学有关保留、使用学位论文的规定，即学校有权保留并向国家有关部门或机构送交论文的复印件和电子版，允许论文被查阅和借阅。本人授权西南财经大学可以将本学位论文的全部或部分内容编入有关数据库进行检索，可以采用影印、缩印、数字化或其他复制手段保存和汇编本学位论文。

  \vspace{1em}
  本学位论文属于

  1、$\square$ 保密，在\underline{\hspace{3em}}年解密后适用本授权书。

  2、$\square$ 不保密

  \vspace{2em}
  \begin{flushright}
    特此声明。

    \vspace{2em}
    学位申请人：\underline{\hspace{6em}}

    \vspace{1em}
    年\hspace{2em}月\hspace{2em}日
  \end{flushright}
  \clearpage
}

% ========================
% 扉页命令
% ========================
\renewcommand{\maketitle}{%
  \begin{titlepage}
    \thispagestyle{empty}
    \begin{flushleft}
      \fontsize{10.5pt}{14pt}\selectfont
      分类号\underline{\hspace{3em}\@classification\hspace{3em}}%
      \hfill 密级\underline{\hspace{3em}\@secretlevel\hspace{3em}}

      U.D.C\underline{\hspace{3em}\@udc\hspace{3em}}
    \end{flushleft}

    \vspace{4cm}
    \begin{center}
      {\fontsize{22pt}{30pt}\selectfont\xiaobiaosong\bfseries \@title \par}
      \vspace{1em}
      {\fontsize{12pt}{16pt}\selectfont \the\entitle \par}
    \end{center}

    \vspace{4cm}
    \begin{center}
      \fontsize{14pt}{28pt}\selectfont
      \renewcommand{\arraystretch}{1.8}
      \begin{tabular}{r@{：}l}
        学位申请人 & \@author \\
        学\hspace{2em}号 & \@studentid \\
        学科专业 & \@major \\
        研究方向 & \@research \\
        指导教师 & \@advisor \\
        定稿时间 & \@finishdate \\
      \end{tabular}
    \end{center}
  \end{titlepage}
  \clearpage
}

\endinput
