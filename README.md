# Paper to Learning

> 把难读论文变成看得懂、讲得清、具有设计感的学习内容。

[![Version](https://img.shields.io/badge/version-v0.5.0-2563eb)](https://github.com/YIYANG-hakimide/paper-to-learning-site)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](./SKILL.md)
[![Outputs](https://img.shields.io/badge/output-Images%20%7C%20Presentation%20PDF%20%7C%20Interactive%20HTML-16a34a)](#三种输出)

`paper-to-learning-site` 是一个面向论文和复杂长文的 Codex skill。它会先理解原文、术语、方法、图表和证据，再为没有深入专业背景的本科生制作清晰、生动、可追溯的学习内容。

## 三种输出

- **图片**：由 Image 2 或其他生图模型直接生成的一组高信息量中文信息图，并附画册 PDF。每张图可独立看懂，整套又有明确顺序。
- **PPT**：可独立阅读的 16:9 咨询报告式 PDF，包含总览、基础知识、方法、关键图表和实验解释；需要时可提供可编辑 PPTX。
- **HTML**：默认提供完整原文、中文对照、术语解释、图表解读和论证路径；超长论文经确认后可制作标明删减的精选阅读版，并可部署到 Vercel。

图片和 PPT 支持三种规模：精简（6-10）、中等（11-20）、详细（21 以上），也可以根据论文长度和难度自动判断。

## 特点

- 默认面向本科水平、但没有相关专业背景的读者。
- 从基础概念开始解释术语、方法、公式和实验。
- 每篇论文根据题材选择视觉风格，不套统一模板。
- 图片模式的最终页面由 Image 2 / `gpt-image-2` 或其他可用生图模型原生生成，不用后期模板拼接冒充信息图。
- PPT 使用原生文字、真实图表和生成式解释图共同讲解，默认交付 PDF。
- 逐张解释论文图表：怎么看、相比谁、结论是什么、有什么限制。
- 保留论文原文与证据来源，生成图不会冒充实验依据。
- 先组织完整讲解逻辑，再生成图片或页面，避免内容堆砌。
- 开头先给论文总览和论证地图，再补背景、拆方法、读实验和结论。
- 教学图在生成前规划中文标签、阅读顺序和图中含义，避免只有漂亮画面没有解释。

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

Skill 会一次性询问输出形式、重点、认知水平、规模和视觉偏好。选好输出后，回复“其余全部默认”即可直接开始。

## English

`paper-to-learning-site` turns academic papers and difficult long-form content into three distinct learning products: native model-generated infographic albums, reading-first visual consulting reports delivered as PDF, or interactive bilingual HTML readers with complete source text. It is designed for college-level readers without deep domain expertise and keeps explanations linked to the paper's real evidence.
