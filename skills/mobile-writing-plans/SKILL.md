---
name: mobile-writing-plans
description: Use when an approved mobile design spec or visual contract must be converted into a multi-step implementation plan before touching code
---

# Mobile Writing Plans

## Overview

Convert an approved mobile spec into executable tasks. The plan must preserve mobile UX requirements, visual baseline references, platform verification, and TDD discipline.

<HARD-GATE>
Do not write implementation code while creating the plan.

Do not create a plan from an unapproved idea. You need an approved written spec.

If the work is UI-heavy and has no visual contract, use `mobile-visual-design` before planning. Do not merely "consider" it. A UI-heavy mobile feature needs either an approved visual contract or an explicit user override recorded in the plan.
</HARD-GATE>

## Inputs Required

- Approved spec path
- Target platform: Flutter, Android, iOS, React Native, mobile web, or multiple
- Repository context and existing patterns
- Test/build commands if known
- Visual artifacts, if any:
  - HTML baseline
  - baseline screenshot
  - visual contract
  - assets.json
  - reference screenshot/mockup
- Project constraints, if any:
  - `docs/mobile-superpowers/project-constraints.md`
  - named project style `SKILL.md`
  - required base components such as `CommonText`, `CommonDialog`, `CommonButton`, `AppColors`, or `AppSpacing`

If any required input is missing, ask one question or inspect the repo. Do not invent commands, paths, or platform architecture.

## UI-Heavy Visual Gate

Before writing a plan for screens, flows, dashboards, visualizations, games, maps, charts, or 3D/animated UI:

1. Check whether a `visual-contract.md` exists.
2. If absent, stop and use `mobile-visual-design`.
3. If the user explicitly overrides visual design, record the override in the plan header and include a manual visual verification task.

Do not proceed directly from a text spec to Flutter/Android/iOS implementation for visually significant screens.

## Save Plans To

```text
docs/mobile-superpowers/plans/YYYY-MM-DD-<feature-name>.md
```

User instructions for plan location override this default.

Use the scaffold helper when a visual contract or asset manifest exists:

```bash
python3 mobile-superpowers/scripts/mobile_plan_scaffold.py \
  --feature "<feature name>" \
  --platform "<Flutter|Android|iOS|React Native|mobile web>" \
  --spec "<approved-spec-path>" \
  --visual-contract "<visual-contract.md>" \
  --assets "<assets.json>" \
  --project-constraints "docs/mobile-superpowers/project-constraints.md"
```

The helper creates the plan structure, Visual Artifacts section, Asset Implementation Matrix, and initial asset/UI tasks. Review and customize it against the repo before execution.

## Plan Header

Every plan must start with:

```markdown
# <Feature Name> Mobile Implementation Plan

> **For agentic workers:** Use task-by-task execution. Follow the mobile verification gates in this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** <one sentence>
**Target Platform:** <Flutter | Android | iOS | React Native | mobile web | multi-platform>
**Architecture:** <2-3 sentences>
**Visual Baseline:** <path or "none">
**Asset Manifest:** <path or "none">
**Project Constraints:** <path or "none">
**Verification Strategy:** <build/test/screenshot/golden plan>

---
```

## File And Responsibility Map

Before tasks, map:

- Files to create or modify
- Each file's responsibility
- Platform components/widgets/views
- State model and data flow
- Assets and generated resources
- Test files
- Verification artifacts

Prefer existing project patterns. Do not introduce a new architecture unless the spec requires it.

## Task Requirements

Each task must be small, concrete, and verifiable. For UI work, each task must cover relevant mobile states:

- Default
- Loading
- Empty
- Error
- Permission denied, if relevant
- Offline, if relevant
- Keyboard open, if relevant
- Dark mode, if relevant
- Accessibility/dynamic type, if relevant

Use TDD where behavior is testable. For visual work, include screenshot/golden/manual evidence steps.

## Plan Review Loop

Plans must be reviewed before handoff. Use `plan-document-reviewer-prompt.md` after drafting the full plan or after each logical chunk when the plan is long.

Reviewer inputs:

- Approved spec path
- Plan path
- Current chunk name or "full plan"
- Plan or chunk content
- Target platforms
- Visual artifacts
- Repo commands discovered

Required reviewer output:

- `Status: APPROVED`, `ISSUES_FOUND`, or `BLOCKED`
- Blocking issues
- Non-blocking recommendations
- Spec coverage notes
- Verification notes

If status is `APPROVED`, proceed to the next chunk or final self-review.

If status is `ISSUES_FOUND`, revise the affected chunk and re-run review before continuing.

If status is `BLOCKED`, inspect the repo or ask the user for the missing context. Do not invent commands, platform targets, or visual evidence.

For long plans, use chunk headings:

```markdown
## Chunk 1: Foundation
## Chunk 2: UI And State
## Chunk 3: Platform Verification
```

Each chunk should be small enough for a reviewer to verify against the spec without losing task detail.

## Visual Artifacts Section

If a visual contract exists, include:

```markdown
## Visual Artifacts

- Reference: `<path>`
- HTML baseline: `<path>`
- Baseline screenshot: `<path>`
- Visual contract: `<path>`
- Asset manifest: `<path to assets.json or "none">`
- Acceptable deviations: `<summary>`
- Must-fix visual differences: `<summary>`
```

If no visual artifact exists and the work is visually risky, stop and recommend `mobile-visual-design`.

## Asset Implementation Matrix

If `assets.json` exists, read it before writing tasks and include:

```markdown
## Asset Implementation Matrix

| Asset | Strategy | Source | Target Path | Platform Handling | Verification |
|---|---|---|---|---|---|
| `<name>` | `<code|icon|image_asset|crop|regenerate|review_placeholder>` | `<source>` | `<target>` | `<platform action>` | `<screenshot/golden check>` |
```

Rules:

- `code`: implement with native widgets/CSS/CustomPaint only when the visual can be faithfully recreated without bitmap assets.
- `icon`: use platform icon set, existing design-system icon, or checked-in SVG/vector asset.
- `image_asset`: copy or generate a bitmap/vector into the platform asset directory before UI completion.
- `crop`: create a pre-implementation task to crop from the reference/mockup and save the asset.
- `regenerate`: create a pre-implementation task to regenerate the asset and verify it against the visual contract.
- `review_placeholder`: do not leave it unresolved. Reclassify as `code`, `icon`, `image_asset`, `crop`, or `regenerate` before implementation tasks.

Platform target examples:

| Platform | Asset target |
|---|---|
| Flutter | `assets/images/...` plus `pubspec.yaml` registration |
| Android | `app/src/main/res/drawable*` or `app/src/main/assets` |
| iOS | `Assets.xcassets` |
| React Native | `src/assets/...` or native asset catalogs |
| mobile web | `public/assets/...` or repo asset pipeline |

UI completion is blocked until asset outputs are present and visible in platform screenshots.

## Project Component Contract

If project constraints exist, include a section that maps UI needs to required base components and forbidden direct usage. Keep it compact and reference `docs/mobile-superpowers/project-constraints.md` instead of copying full project instructions.

For Flutter plans, include this check when the project contract forbids raw platform primitives:

```bash
python3 mobile-superpowers/scripts/mobile_component_contract_check.py \
  --project-dir "<project-dir>" \
  --platform flutter \
  --contract "docs/mobile-superpowers/project-constraints.md"
```

If `CommonDialog`, `CommonText`, `CommonButton`, theme tokens, or other base-level components are required, every UI task must name where those components are used. HTML baseline semantics such as `data-platform-component="CommonText"` should be carried into platform implementation notes.

## Task Template

````markdown
### Task N: <Component or behavior>

**Files:**
- Create: `path/to/file`
- Modify: `path/to/file`
- Test: `path/to/test`
- Visual artifact: `path/to/reference` or `none`
- Asset artifact: `path/to/asset` or `none`

- [ ] **Step 1: Write failing test or visual expectation**

```text
<exact test, golden expectation, or screenshot requirement>
```

- [ ] **Step 2: Verify it fails or is missing**

Run: `<exact command>`
Expected: `<expected failure or missing screenshot>`

- [ ] **Step 3: Implement minimal code**

```text
<complete implementation guidance or code block when appropriate>
```

- [ ] **Step 4: Run platform verification**

Run: `<exact build/test command>`
Expected: `<expected pass condition>`

- [ ] **Step 5: Capture visual evidence if UI changed**

Run: `<screenshot/golden command>`
Expected: `<output path and comparison target>`

- [ ] **Step 6: Commit**

```bash
git add <paths>
git commit -m "<message>"
```
````

## Platform Verification Matrix

Include the relevant rows:

| Platform | Fast check | Visual check | Final check |
|---|---|---|---|
| Flutter | `flutter test` | `flutter build web` + screenshot or golden | target simulator/emulator screenshot |
| Android | Gradle test/build | emulator screenshot via `adb exec-out screencap -p` | release/debug APK smoke test |
| iOS | XCTest/build | simulator screenshot via `xcrun simctl io booted screenshot` | target simulator smoke test |
| React Native | unit/e2e command | Detox/Maestro/Appium screenshot | platform emulator/simulator smoke test |
| mobile web | browser tests | mobile viewport screenshot | responsive/accessibility check |

Use actual repo commands when discovered. If not discovered, mark as "needs confirmation" and ask before execution.

## Self-Review

Before presenting the plan, after the plan review loop:

1. Spec coverage: every approved requirement maps to a task.
2. Visual coverage: visual contract items map to implementation or verification tasks.
3. State coverage: mobile states are covered or explicitly non-goals.
4. Platform commands: commands are real for this repo or clearly marked for confirmation.
5. Project component contract: required base components and forbidden direct usage are represented in tasks and verification.
6. Placeholder scan: no TBD, TODO, "handle edge cases", or "write tests" without specifics.
7. File consistency: names, paths, types, widgets, and components match across tasks.

## Handoff

After saving:

> Plan complete and saved to `<path>`. Review it before execution. For implementation, use `mobile-executing-plans` with `mobile-using-git-worktrees` before edits.

Do not start implementation unless the user asks to continue.

## Red Flags

- Planning from an unapproved spec
- Ignoring visual contract paths
- Treating compile success as UI completion
- Omitting keyboard, safe area, loading, error, empty, dark mode, or accessibility states without naming them non-goals
- Ignoring required project base components after the user asks to "接入该 skill"
- Inventing platform commands
- Writing vague steps like "implement UI" or "add tests"
- Starting code during planning

## Testing This Skill

Use `pressure-tests.md` when changing this skill.
