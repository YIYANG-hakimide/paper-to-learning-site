# Presentation Production

## Authoritative Toolchain

In Codex, read the currently installed official `Presentations` skill before every PPT run and follow its current implementation requirements. Do not copy an old presentation recipe from this repository when the installed skill has newer instructions.

- Use its editable presentation engine and supported JavaScript workflow.
- Keep deck titles, slide titles, body copy, tables, charts, shapes, citations, and layout objects editable.
- Generated teaching illustrations may be embedded as high-resolution raster assets.
- Never build the editable PPTX from full-slide screenshots, PDF pages, or flattened HTML renders.
- Use the user's reference PPTX as the sole template/style source when one is provided. Otherwise create a source-specific direction or use the official presentation skill's current layout library.

Outside Codex, require an equivalent editable deck engine. If none is available, do not promise PPT mode; offer the learning album instead.

## Narrative First

Before slide construction, lock a complete storyboard that answers:

1. What does the source examine?
2. Why does the problem matter?
3. What answer, contribution, or framework does it offer?
4. How does the argument progress from premise to evidence to conclusion?
5. What prerequisite knowledge is needed before the method or argument?
6. Which mechanisms, experiments, figures, tables, and boundaries need dedicated pages?

The opening one to three pages must establish the source, answer, and reasoning route. Do not begin with a generic agenda or a decorative cover followed by isolated details.

## Page Composition

- Use conclusion-led titles that state the page's actual judgment.
- Give each page one communication job and one dominant teaching object.
- Vary the silhouette according to the job: overview map, full-width mechanism, evidence zoom, worked example, comparison, timeline, architecture, table-led analysis, source close reading, synthesis, or boundary page.
- For a roughly twenty-page deck, use at least six real composition families. Similar geometry must not repeat more than twice in sequence.
- Do not use UI dashboards, repeated card grids, pills, tabs, or decorative panels as the default visual language.
- Do not leave the lower half unused while a few short text boxes sit at the top. Use the canvas to explain, compare, show evidence, or enlarge the main visual.
- A cover needs a coherent main visual or deliberate editorial typography. Do not place an arbitrary screenshot beside an unrelated title block.

## Visual Routing

Choose the method per object:

| Teaching object | Preferred implementation |
| --- | --- |
| Quantitative evidence | Native editable chart |
| Exact table, formula, quotation | Deterministic editable layout |
| Simple process or comparison | Native editable slide shapes |
| Complex network/topology | Graphviz |
| Sketch-like explanation | Excalidraw |
| Abstract mechanism, scene, metaphor, high-aesthetic educational visual | Real ImageGen call |
| Original experimental evidence | Tight crop, split, enlarge, and annotate the source object |

ImageGen is mandatory whenever the storyboard routes an object to generated or image-to-image explanation. In Codex, use the system `imagegen` skill first. Do not replace it with SVG, CSS, Canvas, Pillow, generic icons, or primitive shapes and still call the asset generated.

Source screenshots are evidence, not explanation. A normal teaching page should not let a raw source crop occupy more than about 40% of the page unless it is a dedicated close-reading or figure-analysis page. On a close-reading page, enlarge the object enough to read and explain the relevant panel, row, axis, baseline, metric, result, and limitation beside or below it.

## Editability And Typography

- Use stable Chinese fonts available in the environment, preferring Source Han Sans / Noto Sans CJK or another verified family.
- Keep slide titles on their intended line count; change copy or layout instead of shrinking until unreadable.
- Use the current Presentations skill's minimum font sizes unless the user's template supplies a stronger system.
- Check that PPTX titles and body text exist as editable text objects, not only pixels in a background image.
- Charts, tables, and simple flows should remain editable whenever their exact values or labels matter.

## Review And Fallback

Render the actual PPTX, not merely an HTML implementation source. Review:

1. A full contact sheet for narrative rhythm and layout repetition.
2. Every page at full size for overlaps, wrapping, crop, evidence readability, and unused canvas.
3. PPTX and PDF side by side for order, fonts, object placement, and visual parity.
4. Editable-object checks for the cover title, representative body pages, charts/tables, and simple diagrams.
5. At least two repair rounds by visual-design, information-completeness, and novice-comprehension reviewers.

If the deck still fails after two repair rounds, do not ship it as complete. Ask the user whether to continue PPT repair or begin a separate native learning-album workflow. Do not switch modes silently, and do not rename slide screenshots as an image album.
