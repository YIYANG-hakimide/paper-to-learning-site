# Paper to Learning

> 把难读论文变成看得懂、讲得清、具有设计感的学习内容。

[![Version](https://img.shields.io/badge/version-v0.3.0-2563eb)](https://github.com/YIYANG-hakimide/paper-to-learning-site)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](./SKILL.md)
[![Outputs](https://img.shields.io/badge/output-Images%20%7C%20PDF%20%7C%20HTML-16a34a)](#三种输出)

`paper-to-learning-site` 是一个面向论文和复杂长文的 Codex skill。它会先理解原文、术语、方法、图表和证据，再为没有深入专业背景的本科生制作清晰、生动、可追溯的学习内容。

## 三种输出

- **图片**：一组有顺序、高信息量、适合阅读和分享的讲解信息图。
- **PPT**：具有完整演示逻辑和视觉节奏的 16:9 PDF 演示稿。
- **HTML**：可交互、可中英对照、可部署到 Vercel 的论文学习网页。

图片和 PPT 支持三种规模：精简（6-10）、中等（11-20）、详细（21 以上），也可以根据论文长度和难度自动判断。

## 特点

- 默认面向本科水平、但没有相关专业背景的读者。
- 从基础概念开始解释术语、方法、公式和实验。
- 每篇论文根据题材选择视觉风格，不套统一模板。
- 使用 Image 2 / `gpt-image-2` 或其他可用生图模型制作讲解图。
- 逐张解释论文图表：怎么看、相比谁、结论是什么、有什么限制。
- 保留论文原文与证据来源，生成图不会冒充实验依据。
- 先组织完整讲解逻辑，再生成图片或页面，避免内容堆砌。

## 安装

```bash
git clone https://github.com/YIYANG-hakimide/paper-to-learning-site.git ~/.codex/skills/paper-to-learning-site
```

也可以尝试：

```bash
npx skills add -g YIYANG-hakimide/paper-to-learning-site
```

## 使用

```text
用 $paper-to-learning-site 帮我讲解这篇论文。
```

skill 会询问希望生成图片、PPT（PDF）还是 HTML，以及希望采用精简、中等、详细或自动规模。

## English

`paper-to-learning-site` turns academic papers and difficult long-form content into one of three designed learning formats: an ordered explainer-image series, a presentation-style PDF deck, or an interactive bilingual HTML learning site. It is designed for college-level readers without deep domain expertise and keeps explanations linked to the paper's real evidence.
