# Paper to Learning Deck

> Turn difficult papers into visual-first teaching decks and explainer-image sequences.
>
> 把难读论文变成一套真正讲得清楚的视觉讲解图集。

[![Version](https://img.shields.io/badge/version-v0.2.0-2563eb)](https://github.com/YIYANG-hakimide/paper-to-learning-site)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827)](./SKILL.md)
[![Output](https://img.shields.io/badge/output-HTML%20%7C%20PNG%20%7C%20PDF%20%7C%20Vercel-16a34a)](#输出)

## 中文介绍

`paper-to-learning-site` 现在以“论文视觉讲解图集”为主产品：先完整理解论文，再把它重构成一套面向非专业读者的 16:9 网页式讲解 PPT。每一页回答一个具体问题，并通过 Image 2 或其他生图模型生成的解释图、论文原图、数据证据、公式拆解和通俗说明，带读者一步步看懂整篇论文。

它不是摘要生成器，也不是把 PDF 塞进网页。目标是做出比普通教学 PPT 更清楚、比漂亮信息图更可信的学习材料。

## 核心能力

- 完整提取论文主文，建立章节、概念、图表和论点证据清单。
- 按读者真正会提出的问题重组叙事，不机械照搬论文目录。
- 默认面向“无专业背景大学生”，从先修概念开始解释。
- 一页解决一个认知问题，复杂内容自动拆成多页。
- 重点使用 Image 2 / `gpt-image-2` 或其他可用生图模型生成讲解图。
- 每篇论文根据题材选择视觉风格，不套统一模板。
- 论文小镇、Agent、游戏世界可以用像素风；历史主题可以使用克制的古籍、档案、地图或水墨语言；生物、系统、社会科学等各自选择更合适的视觉表达。
- 重要图表逐张、逐面板解释：怎么看、相比谁、结论、意义与限制。
- 生成图只负责解释，论文原文、图表、公式和实验才负责证明。
- 交付可翻页 HTML、逐页 PNG、PDF，并可部署到 Vercel。
- 需要精读时，可额外生成完整中英对照原文阅读器。

## 输出

```text
learn-paper-title/
  index.html
  assets/
    visuals/       # 生图模型生成的讲解图
    evidence/      # 论文图表、公式、截图和证据
    exports/       # 可选 PNG/PDF
  data/
    source-inventory.json
    learning-deck-manifest.json
  qa/
    screenshots/
    qa-report.json
```

默认生成 18-36 页阅读型图集，支持键盘翻页、目录概览、进度、全屏和直接跳页。内容复杂时增加页数，不通过缩小文字强塞。

## 讲解标准

每个难点按以下顺序解释：

1. 专业术语本身是什么意思。
2. 用生活化方式怎么理解。
3. 它在本文中具体指什么。
4. 作者在哪里、怎样使用它。
5. 最容易产生什么误解。

每个重要结论必须说明：相比什么、衡量什么、结果如何变化、证据在哪里，以及不能推出什么。

## 图片标准

- 每个重大难点只要适合可视化，就生成一张或多张解释图。
- 复杂机制拆成多张小图，不制作一张看不清的巨型海报。
- 中文读者默认使用中文主导的图内标签。
- 图内只保留短标签和少量提示，长解释与精确数据放在 HTML 中。
- 图片必须保存为本地 PNG/JPEG/WebP 并真实嵌入成品。
- 如果没有 Image 2，可接入其他真实生图模型；必须记录实际模型名称。
- 没有任何生图路线时会明确报告，不会偷偷用占位图或 SVG 冒充。

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
用 $paper-to-learning-site 把这篇论文做成一套视觉讲解图集。
默认面向没有专业背景的大学生，多用 Image 2 生成解释图。
先生成本地 HTML 和逐页 PNG/PDF，不用部署。
```

如果希望精读原文：

```text
除了视觉讲解图集，再增加完整的中英文对照原文证据层。
```

开始前，skill 默认确认：重点关注内容、交付方式、读者认知水平。

## 自检

```bash
python3 ~/.codex/skills/paper-to-learning-site/scripts/preflight_learning_site.py --source <paper.pdf>
python3 ~/.codex/skills/paper-to-learning-site/scripts/audit_learning_deck.py <deck-dir-or-index.html> --strict
```

完整阅读器模式额外运行：

```bash
python3 ~/.codex/skills/paper-to-learning-site/scripts/audit_learning_site.py <site-dir-or-index.html> --strict
```

## English

`paper-to-learning-site` is now a visual-first paper teaching skill. It inventories the full paper, reconstructs its logic around learner questions, and produces a reading-first 16:9 HTML deck with generated explainer images, source evidence, figure/table interpretation, and novice-friendly teaching.

The default outputs are an interactive HTML deck, per-slide PNGs, and an optional PDF or Vercel deployment. Image 2 / `gpt-image-2` is preferred when available, but the workflow supports other configured image models and records the actual model used. A complete bilingual source reader remains available as an optional evidence layer.
