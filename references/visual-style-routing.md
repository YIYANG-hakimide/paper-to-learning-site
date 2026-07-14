# Visual Style Routing

## Principle

Choose style from the paper's content, not from the generator's favorite aesthetic. Style must improve recognition, orientation, and memory while keeping evidence precise.

Every output needs an art-direction thesis. Readability is necessary but not sufficient: typography, composition, visual metaphor, palette, material, and rhythm should feel intentionally designed for this paper.

## Internalized Design Principles

- Show real-content previews when style is uncertain instead of asking for abstract adjectives.
- Derive the visual language from the paper's objects, era, figures, interfaces, and emotional tone before considering templates.
- Keep one coherent typography, palette, material, and illustration system while varying composition by teaching job.
- Make the central visual explain a relationship, mechanism, comparison, scene, or evidence-reading task; beauty without teaching value is decoration.
- Preserve chart/data semantics before beautifying presentation.
- Let generated imagery handle scenes, mechanisms, spatial relationships, and metaphors. Use deterministic composition for exact text, values, citations, formulas, and tables in PPT/HTML only; image-series pages remain untouched model outputs.
- Use a fixed composition stage for PPT and source-anchored explanations for HTML.
- Explore progressively: preview lightly, lock the direction, then expand it consistently.
- For unfamiliar historical, scientific, cultural, technical, or branded objects, gather factual and visual references before generation. Record the stable recognition cues, sources consulted, and misleading cues deliberately avoided.
- Save a provider-neutral prompt packet for every final generated visual: teaching question, exact labels, composition, objects/relationships, references, aspect ratio, safe area, forbidden elements, model, and prompt hash.

## Derivation Process

Before generating previews, identify:

- subject and era
- real objects, environments, interfaces, artifacts, organisms, or machines in the paper
- emotional tone: exploratory, rigorous, historical, intimate, speculative, clinical, playful
- source visual language: charts, code, maps, equations, screenshots, photographs, diagrams
- audience and reading density
- factual risks: what must not be visually invented or romanticized

Only generate style previews when the user asked for them. Otherwise infer one direction and proceed.

## Routing Examples

### Agents, Games, Simulated Worlds

Use pixel worlds, maps, rooms, character sprites, paths, day/night state, event chains, inventories, or dialogue bubbles when these objects exist in the paper. Pixel styling is especially effective when the source already contains a pixel-world screenshot. Keep experimental tables and exact labels crisp rather than pixelated.

### History, Classics, Archaeology

Use archival paper, restrained ink, maps, timelines, object details, seal-like accents, woodblock or manuscript-inspired composition. Do not fabricate a supposedly authentic historical scene. Mark reconstructions as explanatory illustrations and keep names, dates, routes, and quotations in HTML.

### Biology, Medicine, Chemistry

Use scientific editorial illustration, cutaways, labeled structures, layer diagrams, process sequences, microscopy-inspired textures, or specimen-board composition. Avoid decorative fantasy anatomy and verify structural cues before generation.

### Algorithms, AI, Systems

Use precise technical editorial diagrams, pipelines, architecture cutaways, token/data flows, state machines, layered stacks, or worked-example sequences. Avoid generic glowing brains, humanoid robots, neon dashboards, and meaningless circuitry.

### Economics, Business, Policy

Use evidence-first editorial reports, causal loops, stakeholder maps, timelines, scenario comparisons, and clean chart-led pages. Visual metaphors may orient the learner, but numerical claims remain in real charts and HTML.

### Humanities And Social Science

Use magazine editorial composition, argument maps, scenes, timelines, relationship maps, quotation-led pages, and conceptual contrasts. Avoid converting nuanced claims into simplistic infographics.

### Mathematics And Theory

Use notebook, blackboard, geometric construction, proof map, symbol cards, or transformation sequences. Generated imagery should support intuition; formulas and proofs must remain crisp selectable text.

## Coherence Rules

- Use one shared typography system, palette, texture family, and illustration language across the deck.
- Vary composition by teaching job rather than repeating one card template.
- Give generated visuals a large reading position.
- Keep source figures visually distinct from generated explanations so learners know what is evidence.
- Use semantic accent colors consistently for definition, process, evidence, comparison, and limitation.
- Avoid theme costumes that reduce readability or imply false historical/scientific authenticity.

## Image-Series Art Direction

- Choose the ratio from the diagram grammar: wide for pipelines, systems, and comparisons; portrait for vertical paths and layered maps.
- Allow integrated explanation, but keep one main relationship and split any image that becomes crowded.
- Make pages vivid through scenes, material, spatial hierarchy, expressive diagrams, and concrete examples.
- Alternate mechanism, scene, comparison, timeline, knowledge map, and causal/evidence-chain forms while preserving one visual world.
- Reject a sequence that repeats one social-card template with different text.
- Reject slide chrome, fixed title cards, page footers, and post-composed text/evidence layers.
- At contact-sheet scale, the series should show a clear opening and progressive deepening.

## PPT Art Direction

- Design for independent reading: conclusion-led title, immediate focal point, clear scan order, report-level density, and deliberate chapter transitions.
- Use more pages instead of shrinking text, but do not create empty keynote filler.
- Establish a clear order between judgment, explanation, evidence, and implication.
- Reserve the densest layouts for source evidence and comparison pages.
- Avoid report pages that feel like article screenshots or image-series cards placed on a 16:9 canvas.
- Keep the deck understandable asynchronously; projection is secondary.

## Preview Rules

Generate real title/content previews, not style cards. Each preview should use:

- the actual paper short title
- one real learner question
- one representative visual object
- the intended typography and palette
- no internal labels such as “方案 A”, “preview”, template name, model name, or prompt text inside the slide

Show options outside the output when alternatives were requested. Otherwise inspect the single inferred preview, lock it when it passes, and continue. Prefer the direction with the clearest evidence typography, strongest topic connection, and best fit for the selected output mode.
