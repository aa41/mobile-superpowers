---
name: mobile-requesting-code-review
description: Use after mobile implementation tasks, UI verification, major mobile changes, or before review/merge readiness
---

# Mobile Requesting Code Review

## Overview

Mobile review must check more than code style. It needs plan coverage, platform correctness, visual evidence, artifacts, and secret hygiene.

**Core principle:** review mobile work before defects compound across platforms.

## When To Request Review

Mandatory:

- After completing a major mobile plan chunk.
- Before saying a mobile feature is ready for review or merge.
- After fixing complex Flutter, Android, iOS, screenshot, or provider issues.
- Before preserving a visual deviation as acceptable.

Optional but useful:

- Before large refactors.
- When platform-specific behavior feels fragile.
- When a visual match passes metrics but still looks suspicious.

## Inputs

Collect precise context:

- Plan/spec path.
- Visual contract and verification report paths.
- Platform target and device/simulator/browser details.
- Base and head refs or a concise diff summary.
- Commands run and results.
- Known deviations, blocked checks, and non-goals.

Use `mobile-verification-before-completion` first when possible. Reviewers should see evidence, not promises.

## Review Dispatch

If subagents are available, dispatch a fresh reviewer with `mobile-code-reviewer.md`. Do not include your full conversation history; provide only the work product and evidence paths.

If subagents are unavailable, perform the same checklist yourself and clearly label it as self-review.

Reviewer focus:

- Requirement and plan coverage.
- Mobile state coverage: loading, empty, error, permission, offline, keyboard, dark mode, dynamic type, safe areas.
- Platform correctness for Flutter/Android/iOS/React Native/mobile web.
- Visual fidelity evidence and acceptable deviations.
- Test/build freshness.
- Asset handling and generated artifact hygiene.
- API key/config leakage.
- Maintainability and fit with repo patterns.

## Acting On Feedback

- Fix Critical issues before proceeding.
- Fix Important issues before review/merge readiness.
- Track Minor issues if they are not required for this task.
- Use `mobile-receiving-code-review` before implementing feedback.

## Red Flags

- Requesting review without verification evidence.
- Asking the reviewer to infer requirements from chat history.
- Ignoring platform states because the visual diff passed.
- Treating one platform pass as multi-platform approval.
- Dismissing secret/config hygiene as "local only".

