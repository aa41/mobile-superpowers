---
name: mobile-visual-design
description: Use when mobile app screens, flows, UI mockups, visual references, design screenshots, or mobile visual direction need to be created, reconstructed, or compared before implementation
---

# Mobile Visual Design

## Overview

Create a mobile visual baseline before implementation. The baseline is HTML first: generate or reconstruct a visual direction, verify it against the reference, then record a visual contract for platform implementation.

<HARD-GATE>
Do not jump directly from generated mockup to Flutter, Android, iOS, or React Native implementation.

First create or identify an HTML visual baseline and verify its similarity to the original reference or approved direction. Platform implementation plans may only reference a baseline that has a visual contract.
</HARD-GATE>

## When To Use

Use when:
- The user asks for mobile UI design, screen mockups, visual exploration, or "draw this screen"
- `mobile-brainstorming` determines visual comparison would improve the design
- There is an existing screenshot/design that must be reconstructed or matched
- A mobile implementation plan needs visual artifacts before coding
- Multiple screens need visual consistency across a flow

Do not use when:
- The task is non-visual backend/data/sync work
- The user already supplied a complete approved visual contract
- The user only asks a factual platform API question

## Workflow

1. Collect the minimum visual brief.
2. Select provider strategy.
3. Generate or reconstruct the reference visual.
4. Build or request an HTML baseline.
5. Screenshot the HTML baseline.
6. Compare the HTML screenshot with the original reference or approved mockup.
7. Iterate until the baseline is acceptable or document remaining differences.
8. Record asset strategy for photos, avatars, product imagery, brand marks, complex illustrations, textures, glass effects, and dense charts.
9. Write `visual-contract.md`.
10. Hand off to `mobile-writing-plans` only after the contract exists.

## Visual Brief

Ask only for missing blockers:

- Screen or flow name and core user task
- Target platform: iOS, Android, Flutter, React Native, mobile web, or unknown
- Target device or approximate aspect ratio
- Existing screenshots, mockups, brand references, or clean frame
- Regions that must stay unchanged: status bar, navigation, bottom tab, design system chrome
- Required states: loading, empty, error, permission denied, offline, keyboard open, dark mode
- Whether multiple screens must remain visually consistent

## Provider Strategy

Prefer built-in image generation if the runtime provides it. Use scripted providers only when a fixed local output path, repeatable metadata, or a specific provider is required.

Provider configuration priority:

1. Explicit command or user instruction
2. `MOBILE_VISUAL_*` environment variables
3. Project config: `.mobile-superpowers/config.json`
4. User config: `~/.config/mobile-superpowers/config.json`
5. Provider defaults

Expected provider families:

| Provider | Use when |
|---|---|
| OpenAI GPT Image | High-quality generation/editing or official OpenAI path |
| Gemini / Imagen | Gemini-native image generation, editing, or style transfer |
| OpenAI-compatible proxy | User needs a custom `base_url` or relay |
| Built-in runtime tool | Available and sufficient without extra dependency |

Never hard-code ZenMux or any single relay as the only path.

For GPT image generation, use `gpt-image-2` unless the user explicitly overrides the model. Do not use older GPT image model names in examples, config templates, or provider metadata.

Before using a scripted provider, validate configuration:

```bash
python3 mobile-superpowers/scripts/mobile_visual_config.py --check
```

For full resolved metadata without secret values:

```bash
python3 mobile-superpowers/scripts/mobile_visual_config.py --print
```

See `config-reference.md` for supported providers and config keys.

## HTML Baseline Requirement

The HTML baseline is the visual contract source, not the final mobile implementation.

Required artifacts:

```text
docs/mobile-superpowers/visual/YYYY-MM-DD-<topic>/
  reference.png                    # optional if no reference exists
  generated-mockup.png             # optional if user supplied reference only
  baseline.html
  assets.json
  baseline-screenshot.png
  baseline-metrics.json
  visual-contract.md
```

Create this workspace before producing baseline artifacts:

```bash
python3 mobile-superpowers/scripts/mobile_visual_artifacts.py --topic "<topic>"
```

Build a provider request in dry-run mode before any real image generation call:

```bash
python3 mobile-superpowers/scripts/mobile_visual_provider.py \
  --topic "<topic>" \
  --prompt "<visual prompt>" \
  --dry-run
```

Dry-run writes metadata only. It does not call OpenAI, Gemini, Imagen, or any proxy.

To call an OpenAI-compatible provider such as `proxy`, use explicit execution:

```bash
python3 mobile-superpowers/scripts/mobile_visual_provider.py \
  --topic "<topic>" \
  --prompt "<visual prompt>" \
  --execute
```

`--execute` sends a real `/images/generations` request and may spend provider credits. The adapter writes `generated-mockup.png` and provider response metadata without storing the API key.

Create the initial HTML baseline scaffold from provider metadata:

```bash
python3 mobile-superpowers/scripts/mobile_visual_baseline.py \
  --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json"
```

This creates `baseline.html` and records the source in `visual-contract.md`. It is a scaffold; visual fidelity still requires screenshot capture and similarity comparison.

Create a mockup-to-HTML reconstruction bundle:

```bash
python3 mobile-superpowers/scripts/mobile_visual_reconstruct.py \
  --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json" \
  --force
```

This writes `reconstruction-prompt.md` and a reconstruction-oriented `baseline.html`. It organizes draw-ui reconstruction rules, but does not claim the HTML is visually matched until screenshot comparison passes.

To let a multimodal model read the generated mockup and write the actual HTML baseline, explicitly execute the reconstruction adapter:

```bash
python3 mobile-superpowers/scripts/mobile_visual_reconstruct.py \
  --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json" \
  --force \
  --execute \
  --vision-model gpt-5.5
```

`--execute` sends a real OpenAI-compatible `/chat/completions` request and may spend provider credits. `--vision-model` is the chat/vision model for HTML reconstruction; it defaults to `gpt-5.5` and is separate from the GPT Image generation model (`gpt-image-2`). Configure it with `--vision-model`, `MOBILE_VISUAL_VISION_MODEL`, or `visual.vision_model` in config. The adapter sends `reconstruction-prompt.md` plus the generated mockup image, writes returned HTML into `baseline.html`, accepts plain text or content-block responses, and records non-secret execution metadata.

Record asset strategy after the HTML baseline exists:

```bash
python3 mobile-superpowers/scripts/mobile_visual_assets.py \
  --baseline "docs/mobile-superpowers/visual/<date-topic>/baseline.html"
```

This writes `assets.json` and updates the `Asset Strategy` section of `visual-contract.md`. Use `image_asset` for photos, avatars, product imagery, brand marks, complex illustrations, textures, glass effects, and dense charts instead of forcing CSS reconstruction. Use `crop` when an asset should be cut from the reference/mockup, and `regenerate` when it should be recreated by an image model.

Capture the HTML baseline at a mobile viewport:

```bash
python3 mobile-superpowers/scripts/mobile_visual_screenshot.py \
  --baseline "docs/mobile-superpowers/visual/<date-topic>/baseline.html"
```

The screenshot helper discovers `MOBILE_VISUAL_BROWSER_CMD`, command-line Chrome/Chromium/Edge, then macOS Chrome/Edge app paths. Use `--dry-run --json` to inspect the browser command without capturing.

Compare the reference image against the HTML baseline screenshot:

```bash
python3 mobile-superpowers/scripts/mobile_visual_compare.py \
  --reference "docs/mobile-superpowers/visual/<date-topic>/reference.png" \
  --candidate "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png" \
  --clip "cta:0,600,390,120"
```

The compare helper requires Pillow for actual image comparison. If Pillow is unavailable, it fails with a dependency message rather than inventing metrics.

Install optional visual dependencies into a user-cache venv:

```bash
python3 mobile-superpowers/scripts/mobile_visual_deps.py --install
```

If the current Python cannot create a working venv, choose another interpreter:

```bash
python3 mobile-superpowers/scripts/mobile_visual_deps.py \
  --install \
  --python /usr/local/bin/python3
```

Then run comparison with the venv Python if system Python does not have Pillow:

```bash
~/.cache/mobile-superpowers/visual-venv/bin/python \
  mobile-superpowers/scripts/mobile_visual_compare.py \
  --reference "docs/mobile-superpowers/visual/<date-topic>/reference.png" \
  --candidate "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png"
```

If the baseline cannot be produced in the current environment, stop and explain what is missing. Do not continue to platform implementation planning with an imaginary baseline.

## Similarity Check

Compare:

- Original reference vs HTML baseline screenshot
- Key regions as clips when possible: status/navigation, primary content, CTA area, bottom tab, empty/loading/error states

Record:

- Metrics file path
- Heatmap/diff paths if available
- Human visual notes
- Acceptable deviations
- Issues that must be fixed before platform implementation

Pixel metrics assist judgment; they do not replace human visual review.

## Visual Contract

`visual-contract.md` must include:

```markdown
# <Topic> Visual Contract

## Source Inputs
## Target Platform Assumptions
## HTML Baseline
## Screenshot And Metrics
## Layout Structure
## Visual Tokens
## Component Inventory
## State Coverage
## Asset Strategy
## Mobile Constraints
## Acceptable Deviations
## Must-Fix Differences
## Platform Handoff Notes
```

## Mobile Handoff Rules

Before calling `mobile-writing-plans`, identify which targets need verification:

| Target | Expected verification |
|---|---|
| Flutter | Flutter Web screenshot first, then native/golden if needed |
| Android | APK/emulator screenshot through adb |
| iOS | Simulator screenshot through simctl |
| React Native | Detox/Maestro/Appium or platform screenshot |

## Red Flags

- Starting Flutter/Android/iOS implementation before HTML baseline verification
- Treating a generated mockup as an implementation spec without visual contract
- Skipping reference comparison because the image "looks close"
- Ignoring safe area, keyboard, loading, empty, error, or dark mode states
- Hard-coding one image provider when config should select it
- Claiming a platform conversion will match without a screenshot plan

## Testing This Skill

Use `pressure-tests.md` when changing this skill.
