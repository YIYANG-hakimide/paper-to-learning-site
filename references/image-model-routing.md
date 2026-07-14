# Image Model Routing

## Goal

Always use a real image-generation route for planned teaching visuals unless the user explicitly approves a manual fallback.

## Route Order

1. Built-in `imagegen` / Image 2 / `gpt-image-2` capability exposed by the current agent environment.
2. An installed image-generation skill or plugin that returns a local raster file.
3. A configured OpenAI-compatible Images API or CLI using the user's existing credentials.
4. Another user-configured image model or service that can return local PNG/JPEG/WebP assets.
5. Manual SVG/CSS diagram only for PPT/HTML after explicit approval; never for image-series output.

Do not require the provider to be Codex. The skill should describe the desired image, labels, dimensions, and QA contract independently of provider-specific syntax.

## Preflight Record

Record:

- provider/tool name
- model name
- how the image is invoked
- whether a local asset path is returned
- supported aspect ratios/resolution
- support for reference images or edits
- support for Chinese labels
- known constraints

Normalize these capabilities in the manifest:

- `native_aspect_ratios`
- `max_resolution`
- `chinese_text_reliability`: high, medium, low, unknown
- `reference_image_support`
- `image_edit_support`
- `transparent_background_support`
- `local_asset_export`

Use the capability profile to adapt generation:

- no native 16:9: generate the nearest wider ratio with strong safe margins, then crop only after checking no content is lost
- low Chinese reliability: do not use that provider for final image-series pages; switch to a model that can produce readable Chinese or ask the user for another route
- reference-image support: provide paper figures or style previews only when they clarify objects or visual language, not to copy protected artwork
- edit support: useful for PPT/HTML assets; image-series mode still regenerates the complete final image when text or structure is wrong
- low maximum resolution: use the asset for a smaller focused diagram or switch providers for a full-slide hero visual

If no route can persist a local asset, stop before final delivery. A preview visible only in chat or a remote UI is not a deck asset.

## Provider-Neutral Prompt Packet

For each image, prepare a structured packet:

- concept id
- learner question
- one-sentence teaching goal
- visual type and composition
- exact short Chinese labels
- objects, actors, arrows, and relationships
- paper-specific visual style
- aspect ratio and target resolution
- safe margins
- facts and references that must be preserved
- elements that must not appear

Translate this packet into the selected provider's prompt format. Save the packet even when provider syntax differs so the image can be regenerated with another model.

## Fallback Behavior

- OCR every generated image that contains text and compare recognized labels with the expected label list. Any wrong, missing, or garbled key label fails QA.
- If Chinese text quality is weak, simplify the wording and regenerate the complete image.
- For image-series mode, do not switch to HTML labels, overlays, source annotations, or a template compositor. Switch image providers or stop and ask the user.
- For PPT/HTML, a low-text generated diagram plus exact surrounding HTML remains acceptable when it teaches more clearly.
- If factual objects are unreliable, gather reference images/information or use a more schematic visual type.
- If the selected model cannot meet the style or resolution requirement, try another configured model before asking for manual fallback.
- Never create placeholder bitmap files, screenshots of manual SVG, post-composed image-series pages, or false manifest entries to satisfy counts.

## Attribution

Record the actual model used for every asset. Use `Image 2` or `gpt-image-2` only when that model generated the final local bitmap. For other models, record their real names. Public slides do not need model attribution unless the user requests it; keep provenance in the manifest.
