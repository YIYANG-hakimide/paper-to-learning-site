# Paper to Learning Site

> Turn papers and difficult long-form articles into interactive, bilingual learning websites.
>
> 把论文和难读长文变成可阅读、可交互、可部署的双语学习网站。

[![Version](https://img.shields.io/badge/version-v0.1.0-2563eb)](https://github.com/YIYANG-hakimide/paper-to-learning-site/releases/tag/v0.1.0)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](./SKILL.md)
[![Static Site](https://img.shields.io/badge/output-static%20HTML-16a34a)](#what-it-builds--它会生成什么)

## 中文介绍

`paper-to-learning-site` 是一个 Codex skill，用来把一篇学术论文、PDF、研究报告或难读长文，转成一个完整的交互式学习网页。

它的目标不是生成一页“论文总结”，也不是把 PDF 简单嵌进网页了事，而是做成一个真正能帮助人读懂内容的阅读产品：

- 网页里能直接读到原文，而不是只能跳转 PDF。
- 非中文材料提供中英对照；中文材料保留原文，并补充“说人话”解释。
- 关键术语跟随正文出现，点击即可展开解释。
- 图表和实验结果放在对应论证位置，而不是堆在页面最后。
- 每个难点尽量配 Image 2 生成的解释图、流程图、示意图或类比图。
- 默认面向“没有专业背景的大学生”，从基础概念讲起。

## 它适合什么场景

- 想把一篇论文做成可分享的学习网页。
- 想帮助非专业读者理解 AI、计算机、社会科学、商业、设计等领域的复杂文章。
- 想把 PDF 阅读体验改造成“章节地图 + 双语正文 + 旁注 + 术语弹窗 + 图表解读”的交互式阅读器。
- 想生成一个可本地打开、也可部署到 Vercel 的静态 HTML 网站。

## 它会生成什么

默认产物是一个静态网页项目，通常长这样：

```text
learn-paper-title/
  index.html
  assets/
    figures/      # 原论文图表、截图、裁剪后的子图
    diagrams/     # Image 2 生成的解释图、流程图、示意图
    screenshots/  # 页面检查或视觉证据
  data/           # 可选：章节、段落、术语、图表的结构化数据
```

网页体验默认包括：

- 章节地图或章节切换阅读器
- 原文 / 中文翻译 / 说人话解释
- 跟随正文出现的术语弹窗
- 跟随段落变化的旁注或学习面板
- 图表抽屉、图表热点或左右对照解读
- 每章逻辑总结、学习检查点和下一章衔接
- 桌面与移动端可读的响应式布局

## 核心标准

这个 skill 会强制关注这些质量线：

1. **必须能读原文**
   不能只给摘要，也不能把 PDF iframe 当作主要阅读方式。

2. **必须解释难点**
   术语解释按这个顺序来：术语本义 -> 说人话 -> 本文指代 -> 作者怎么用 -> 常见误解。

3. **必须讲清图表**
   每个图表都要解释：它是什么、怎么看、相比谁、结论是什么、为什么重要、不能推出什么。

4. **必须有视觉化辅助**
   每章至少一张解释图；重要难点尽量用 Image 2 生成流程图、系统图、类比图或报告式图解。

5. **必须做可用性检查**
   交互要能打开和关闭，文字不能遮挡，图表不能断链，英文长段不能只有很短中文解释。

## 安装

推荐安装到 Codex 全局 skill 目录：

```bash
git clone https://github.com/YIYANG-hakimide/paper-to-learning-site.git ~/.codex/skills/paper-to-learning-site
```

如果你使用 skills CLI，也可以尝试：

```bash
npx skills add -g YIYANG-hakimide/paper-to-learning-site
```

安装后建议新开一个 Codex 对话，或重启 Codex，让 skill 出现在可用能力列表中。

## 使用方式

在 Codex 中可以这样说：

```text
Use $paper-to-learning-site to turn this paper into an interactive bilingual learning website.
默认读者是没有专业背景的大学生。请先做本地 HTML，不用部署。
```

中文也可以：

```text
用 $paper-to-learning-site 把这篇论文做成一个交互式学习网站。
需要中英文对照，重点解释术语、实验和图表。
读者默认是没有 AI / 计算机背景的大学生。
先给我本地 HTML，确认后再部署 Vercel。
```

启动时，skill 会优先确认三个问题：

1. 有没有想重点探讨、重点解释或特别关注的内容？
2. 是先返回本地 HTML，还是需要部署到 Vercel？
3. 默认按“无专业背景大学生”的认知水平解释，可以吗？

如果你说“直接按默认开始”，它会默认完整解释难点和实验，先生成本地静态 HTML。

## 自检脚本

仓库内置了一个基础静态站点检查脚本：

```bash
python3 ~/.codex/skills/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html>
```

它会检查：

- 本地图片是否缺失
- `id` 是否重复
- 图片是否缺少 `alt`
- 是否把 PDF iframe 当成主要阅读方式
- 是否缺少明显的“原文”或“说人话”阅读层

这个脚本不是完整 QA，但能提前抓住一些很容易破坏阅读体验的问题。

## 维护与更新

如果你是在本机维护这个 skill：

```bash
cd ~/.codex/skills/paper-to-learning-site
git pull
# 修改 SKILL.md / references / scripts
git add .
git commit -m "Improve paper learning site guidance"
git push
```

发布新版本时，可以打 tag：

```bash
git tag v0.1.1
git push origin main v0.1.1
```

---

## English Introduction

`paper-to-learning-site` is a Codex skill for transforming academic papers, PDFs, research reports, and dense long-form articles into complete interactive learning websites.

It is not meant to produce a thin summary page or a PDF wrapper. It is designed to create a guided reading product where learners can read the source text, follow bilingual explanations, explore terms, inspect figures, and understand the argument step by step.

## Best For

- Turning a paper into a shareable learning website.
- Helping non-specialist readers understand complex AI, computer science, social science, business, or design materials.
- Replacing passive PDF reading with a chapter-map reader, bilingual text, margin notes, term popovers, and figure explanations.
- Producing a local static HTML site that can later be deployed to Vercel.

## What It Builds

The default output is a static website:

```text
learn-paper-title/
  index.html
  assets/
    figures/      # original paper figures, screenshots, cropped subfigures
    diagrams/     # generated explanatory diagrams
    screenshots/  # validation screenshots or visual evidence
  data/           # optional structured chapter/paragraph/term/figure data
```

The reader experience usually includes:

- chapter map or section-switching reader
- original text, Chinese translation, and plain-language explanation
- inline term popovers
- synchronized side notes or learning panel
- figure drawers, figure hotspots, or side-by-side figure interpretation
- chapter logic summaries, learning checkpoints, and next-chapter bridges
- responsive layout for desktop and mobile

## Quality Bar

The skill pushes for these standards:

1. **Source text must be readable in-page**
   A PDF iframe cannot be the primary reading experience.

2. **Hard concepts must be explained from first principles**
   Term explanations should cover: field definition, plain-language analogy, paper-specific meaning, how the author uses it, and common misunderstandings.

3. **Figures and tables must be explained near the argument**
   Each figure/table should answer: what it is, how to read it, what it compares against, what conclusion it supports, why it matters, and what it does not prove.

4. **Visual teaching aids are expected**
   Use Image 2 or another available image-generation model for flowcharts, system maps, metaphors, report-style diagrams, and experiment explainers.

5. **The site must be usable**
   Interactions need open/close states, text must not overlap, images must load, and long English passages need proportional Chinese explanation.

## Installation

Install into the global Codex skills directory:

```bash
git clone https://github.com/YIYANG-hakimide/paper-to-learning-site.git ~/.codex/skills/paper-to-learning-site
```

If you use a skills CLI, you can also try:

```bash
npx skills add -g YIYANG-hakimide/paper-to-learning-site
```

After installation, start a new Codex conversation or restart Codex so the skill can be discovered.

## Usage

Example prompt:

```text
Use $paper-to-learning-site to turn this paper into an interactive bilingual learning website.
The default reader is a college student without domain expertise.
Create a local static HTML version first; do not deploy yet.
```

The skill will usually ask:

1. Are there topics or sections you want to emphasize?
2. Do you want a local HTML site first, or should it be deployed to Vercel?
3. Is the default reader level, a non-specialist college student, acceptable?

If you ask it to proceed with defaults, it will explain hard concepts and experimental evidence thoroughly, then create a local static HTML site first.

## Static Audit Script

Run:

```bash
python3 ~/.codex/skills/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html>
```

The script checks for missing local image assets, duplicate IDs, weak image alt text, PDF iframe patterns, and missing source/plain-language reading layers.

## Status

Current release: `v0.1.0`.

This is an early but usable version focused on the workflow and quality standards. Future versions may add stronger templates, extraction utilities, sample sites, and richer validation.
