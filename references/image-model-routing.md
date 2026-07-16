# Image Model Routing

## Goal

Use a real image-generation route for planned teaching visuals, prove it with persisted execution evidence, and stop cleanly when no verified route is available. Route selection must not depend on a self-confirmation flag or a hard-coded model name.

## Route Order

### Inside Codex

1. Prefer the system built-in `imagegen` / `image_gen` tool.
2. Read the actual provider and model from the newest successful receipt. Do not assume which model currently backs the system tool.
3. Use another installed tool, plugin, CLI, or API only when the built-in route has a real failure or cannot meet a required capability.

The built-in route does not need `OPENAI_API_KEY`. Do not leave a project asset only in the generated-image cache: copy the selected raster into the output package and bind that local file to the receipt hash.

### Outside Codex

Detect configured image CLIs and API credential environment-variable names. Never print credential values. A detected CLI or environment variable is only a candidate route, not proof that generation works.

If no supported tool or API configuration is detected, stop and ask the user to configure one. Do not create a placeholder, claim that generation was confirmed, or silently switch to a manual diagram.

### Manual Fallback

Manual SVG/CSS diagrams are available only for PPT/HTML after a real route failure and explicit user approval. They are never valid final pages for image-series mode.

## Canonical Resolver

Use:

```bash
python3 scripts/resolve_image_route.py \
  --runtime auto \
  --receipt raw/receipts/image-smoke-test.json \
  --route-journal raw/route-journal.json
```

For preflight:

```bash
python3 scripts/preflight_learning_site.py \
  --mode image-series \
  --image-route-receipt raw/receipts/image-smoke-test.json \
  --image-route-journal raw/route-journal.json
```

`--confirm-image-direct-output` is prohibited. It is retained only as a rejected compatibility argument and can never make preflight pass.

## Verification Contract

Image-series and PPT routes are available only when both of these artifacts exist and agree:

1. A real receipt from a successful image call.
2. A route journal containing the matching successful event.

Receipt schema version 1 requires:

- `provider`
- `tool` when available
- `model`: the actual model reported by the route
- `request_id`
- `prompt_sha256`
- `output_sha256`
- `local_asset_path`, `raw_output_path`, or `output_path`

The bound file must exist locally, be PNG/JPEG/WebP, and byte-match `output_sha256`.

The matching route-journal success event requires:

- `event`: `success`, `smoke_test_succeeded`, or `generation_succeeded`
- ISO-8601 `timestamp`
- matching `provider`, `model`, and `request_id`
- `tool`
- `route_kind`, such as `system_imagegen`, `external_api`, or a named CLI route
- `transport`, such as `built-in`, `https-api`, or `cli`
- `receipt_path`
- matching `output_sha256`

A chat preview, tool-presence check, environment variable, capability description, or boolean confirmation is not execution evidence.

## Dynamic Model Selection

Never hard-code a model as the current default.

- In Codex, select the most recently verified `system_imagegen` receipt first.
- If no verified system receipt exists, select the newest verified eligible route.
- Outside Codex, select the newest verified eligible route.
- Record the real provider/model on every asset. A model name may be written only when that model appears in the matching receipt.

This allows the runtime to adopt a newly verified model without changing the routing document or source code.

## Route Journal Safety

Never record secrets in receipts, route journals, logs, reports, or error messages.

Forbidden fields include API keys, authorization headers, bearer tokens, cookies, passwords, private keys, session keys, and provider credentials. The journal helper redacts these values before writing. A journal that already contains secret material is invalid and cannot verify a route.

It is safe to record only credential environment-variable names, for example `OPENAI_API_KEY`, as configuration hints. Never record their values.

## Transport Failure vs Model/Provider Fallback

These are different decisions and must use different journal events.

### Transport Retry Or Switch

HTTP 504 / gateway timeout is a transport failure. Keep the provider and model unchanged.

- journal transition: `transport_retry` or `transport_switch`
- allowed changes: endpoint, network path, client transport, or retry timing
- forbidden inference: the model is bad, unsupported, or should be downgraded

### Model Or Provider Fallback

Use `model_provider_fallback` only for evidence such as `unsupported_model`, `model_not_found`, `model_disabled`, provider/account unavailability, exhausted provider quota, or a verified capability mismatch.

Record the reason separately. Do not relabel a 504 as a model/provider failure. Inside Codex, a built-in `imagegen` failure never authorizes CLI/API fallback by itself: ask the user first, then record `user_confirmed: true` on the `model_provider_fallback` event before invoking the external route. The confirmation event should bind `from_route_kind: system_imagegen` to the intended `to_route_kind`, provider, and model when known.

## HTTP 504 Retry Policy

For consecutive 504 failures on the active provider/model route:

1. After the first 504, wait about 20 seconds before retrying or switching transport.
2. After the second 504, wait about 45 seconds.
3. Make at most a third attempt. After a third consecutive 504, do not issue another automatic attempt; remain in transport cooldown.
4. Use about 90 seconds as the final transport cooldown interval, while keeping the hard cap at three attempts.
5. If roughly eight minutes have elapsed from the first 504 without a success, enter `blocked_waiting_user`.

A `transport_switch` does not reset the count because the provider/model route is unchanged. A real success resets it. A deliberate `model_provider_fallback` starts a new route history and must not be confused with a transport retry.

## Provider-Neutral Prompt Packet

For each image, prepare:

- concept id
- learner question
- one-sentence teaching goal
- visual type and composition
- exact short Chinese labels
- objects, actors, arrows, and relationships
- source-specific visual style
- aspect ratio and target resolution
- safe margins
- facts and references that must be preserved
- elements that must not appear

Translate this packet into the selected provider syntax. Save the packet independently so another verified model can regenerate the asset without changing the teaching contract.

## Capability And QA Rules

Record capabilities learned from real output, not marketing assumptions:

- native aspect ratios and maximum verified resolution
- Chinese text reliability
- reference-image and image-edit support
- transparent-background support
- local asset export

OCR every generated image containing text and compare recognized labels with the expected list. Regenerate the complete image when a key label is wrong, missing, or garbled. For image-series mode, never repair text with overlays or a compositor.

If no verified route can persist a local raster, stop before delivery and ask the user to configure or approve the next route.
