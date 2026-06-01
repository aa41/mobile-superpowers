---
name: mobile-verification-before-completion
description: Use before claiming mobile work is complete, fixed, verified, ready for review, or ready to merge
---

# Mobile Verification Before Completion

## Overview

Mobile completion requires fresh evidence across plan tasks, tests, builds, screenshots, visual comparisons, artifacts, and secrets hygiene.

**Core principle:** evidence before mobile completion claims.

## Hard Gate

Do not say mobile work is complete, fixed, passing, visually matched, ready for review, or ready to merge until this gate has run in the current turn.

## Gate Checklist

### 1. Plan Coverage

- Re-read the approved plan.
- Confirm each task is checked, blocked, or explicitly out of scope.
- Confirm accepted deviations are documented.

### 2. Test And Build Evidence

Run fresh commands appropriate to the repo:

| Platform | Evidence examples |
|---|---|
| Flutter | `flutter analyze`, `flutter test`, relevant build |
| Android | Gradle test/build command from plan |
| iOS | xcodebuild test/build command from plan |
| React Native | package tests plus e2e command when present |
| mobile web | test/build/browser checks |

Report exact commands, exit codes, and failure counts. Partial checks must be labeled partial.

### 3. UI Evidence

If UI changed, use `mobile-ui-verification` or equivalent evidence:

- reference or visual contract;
- platform screenshot or golden;
- comparison metrics when available;
- state coverage: loading, empty, error, permission denied, offline, keyboard, dark mode, dynamic type, safe area;
- must-fix issues and acceptable deviations.

No screenshot means no visual fidelity claim.

### 4. Project Component Contract

If the plan, visual contract, prompt, `AGENTS.md`, `CLAUDE.md`, or project constraints require base components, verify they were used. For Flutter:

```bash
python3 mobile-superpowers/scripts/mobile_component_contract_check.py \
  --project-dir "<project-dir>" \
  --platform flutter \
  --contract "docs/mobile-superpowers/project-constraints.md"
```

Report any violations. Do not claim completion while feature UI still uses forbidden direct primitives such as raw `Text(`, `AlertDialog`, direct buttons, or hard-coded `Color(0x...)` unless the exception is explicitly approved.

### 5. Artifact And Secret Hygiene

Check:

- API keys and local config are not staged or documented.
- Generated screenshots, diffs, reports, and assets are either intentionally saved or cleaned.
- Build artifacts are not accidentally staged.
- `git status --short` is understood.

### 6. Final Statement

Use one of these assessments:

- `VERIFIED`: all required evidence passed.
- `VERIFIED_WITH_DEVIATIONS`: evidence passed with documented acceptable deviations.
- `NOT_VERIFIED`: required evidence failed.
- `BLOCKED`: required evidence could not run; blocker is explicit.

After `VERIFIED` or `VERIFIED_WITH_DEVIATIONS`, use `mobile-requesting-code-review` before review/merge readiness for substantial mobile work. Use `mobile-finishing-a-development-branch` only after review issues are resolved or explicitly deferred.

## Completion Report

```markdown
## Mobile Completion Verification

- Assessment: `<VERIFIED|VERIFIED_WITH_DEVIATIONS|NOT_VERIFIED|BLOCKED>`
- Plan: `<path>`
- Commands run:
  - `<command>` -> `<result>`
- UI evidence: `<report/screenshot paths or none>`
- Component contract: `<passed / not applicable / violations>`
- State coverage: `<covered / non-goals / blocked>`
- Artifacts: `<kept / cleaned / needs review>`
- Secrets check: `<result>`
- Remaining risks: `<risks or none>`
```

## Red Flags

- "Tests passed earlier."
- "Build passed, so UI is done."
- "Flutter Web matched, so native is fine."
- "I cannot run the simulator, but it should be okay."
- "No need to check git status."
- "The provider key is only in docs temporarily."
- "The project says CommonText, but raw Text is visually equivalent."
