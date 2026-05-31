---
name: using-mobile-superpowers
description: Use when starting mobile app work, mobile UI implementation, native or cross-platform mobile debugging, simulator/device workflows, or mobile-specific testing in a repository with mobile-superpowers available
---

# Using Mobile Superpowers

## Overview

Mobile work fails when agents treat phones like small desktops: no safe areas, no keyboard states, no touch ergonomics, no device verification. Mobile Superpowers makes mobile-specific workflow checks mandatory before action.

<HARD-GATE>
Before answering or acting on any mobile-related task, read this full skill and state:
"Using using-mobile-superpowers to select the mobile workflow."

Then identify which downstream mobile skill applies. Do not inspect files, run commands, launch simulators, dispatch agents, or edit code before this selection step.
</HARD-GATE>

## Priority

User instructions are highest priority. Mobile Superpowers controls how you work, not what the user wants built.

If user instructions conflict with this skill, follow the user and say which workflow requirement was overridden.

## Required Skill Check

If there is even a small chance a mobile-superpowers skill applies, use it before proceeding.

Use `mobile-brainstorming` when the task involves:
- A new mobile feature, app flow, screen, navigation pattern, interaction model, or product direction
- Ambiguous requirements, competing UX/technical approaches, or a request to "design" before building
- iOS, Android, Flutter, React Native, SwiftUI, Kotlin, mobile web, simulator/device behavior, permissions, offline behavior, safe areas, keyboard handling, gestures, accessibility, or mobile release concerns

Use `mobile-visual-design` when the task involves:
- Mobile UI mockups, visual direction, screen design, screenshot reconstruction, or reference matching
- Creating an HTML visual baseline before mobile implementation
- Provider selection for GPT Image, Gemini, Imagen, built-in image generation, or an OpenAI-compatible image relay
- Converting a visual idea into a `visual-contract.md`

Use `mobile-writing-plans` when the task involves:
- Turning an approved mobile spec into implementation tasks
- Planning Flutter, Android, iOS, React Native, or mobile web work
- Referencing visual contracts, HTML baselines, screenshots, or mobile verification gates in a plan

Use `mobile-using-git-worktrees` when the task involves:
- Starting mobile implementation work that may modify app code, platform code, assets, build files, generated screenshots, or verification reports
- Executing a mobile plan in a safer isolated workspace
- Preparing a branch/worktree for Flutter, Android, iOS, React Native, or mobile web changes

Use `mobile-executing-plans` when the task involves:
- Executing an approved mobile implementation plan
- Continuing task-by-task mobile implementation from a saved plan
- Turning plan checkboxes into code, tests, screenshots, and verification evidence

Use `mobile-test-driven-development` when the task involves:
- Implementing mobile behavior, UI states, platform flows, or bug fixes before production code
- Adding Flutter widget tests, Android tests, iOS XCTest, screenshot/golden expectations, or mobile state tests
- Creating a failing expectation before implementing a mobile plan task

Use `mobile-systematic-debugging` when the task involves:
- Mobile test failures, build failures, simulator/emulator/device issues, screenshot failures, visual diff failures, or provider/API failures
- Unexpected Flutter, Android, iOS, React Native, or mobile web behavior
- Any tempting quick fix without a confirmed root cause

Use `mobile-ui-verification` when the task involves:
- Claiming mobile UI work is complete
- Checking visual fidelity, screenshot diffs, golden tests, simulator/emulator screenshots, or HTML baseline similarity
- Verifying Flutter Web, Android adb screenshots, iOS simulator screenshots, React Native screenshots, or mobile web screenshots

Use `mobile-verification-before-completion` when the task involves:
- Claiming mobile work is done, fixed, passing, verified, ready for review, or ready to merge
- Finishing a mobile implementation plan
- Producing final evidence across tests, builds, screenshots, artifacts, and secret hygiene

Use `mobile-requesting-code-review` when the task involves:
- Requesting review after mobile implementation, UI verification, a major mobile plan chunk, or before review/merge readiness
- Preparing independent review context for Flutter, Android, iOS, React Native, mobile web, visual, asset, or provider work

Use `mobile-receiving-code-review` when the task involves:
- Acting on mobile code review feedback
- Evaluating reviewer claims about platform behavior, UI fidelity, tests, artifacts, or maintainability before making changes

Use `mobile-finishing-a-development-branch` when the task involves:
- Mobile work is verified and needs merge, PR, branch preservation, artifact cleanup, or discard decisions
- Preparing mobile PR evidence or safely cleaning an implementation worktree

When multiple skills apply, use the earliest workflow gate:

```text
unclear idea -> mobile-brainstorming
visual direction or mockup -> mobile-visual-design
approved spec -> mobile-writing-plans
UI-heavy spec without visual contract -> mobile-visual-design
approved plan before edits -> mobile-using-git-worktrees
execute approved plan -> mobile-executing-plans
implementation task -> mobile-test-driven-development
failure or unexpected behavior -> mobile-systematic-debugging
implemented UI -> mobile-ui-verification
completion claim -> mobile-verification-before-completion
request review -> mobile-requesting-code-review
review feedback -> mobile-receiving-code-review
merge/PR/cleanup -> mobile-finishing-a-development-branch
```

Future mobile-superpowers skills may cover debugging, release work, and platform-specific implementation. When available, select the most specific applicable skill.

## Platform Adaptation

Skills may mention Claude Code tool names:

| Skill reference | Codex equivalent |
|---|---|
| `Skill` tool | Native skill loading, then follow the skill |
| `TodoWrite` | `update_plan` |
| `Task` subagent | `spawn_agent`, then `wait_agent` and `close_agent` |
| `Read`, `Write`, `Edit`, `Bash` | Native file and shell tools |

If multi-agent tools are unavailable, say so and fall back to the closest sequential workflow. Do not pretend independent agents ran.

## Default Response Pattern

When this skill activates:

1. Announce the workflow selection sentence from the hard gate.
2. Name the downstream skill you will use, or explain why none applies.
3. Load and follow that downstream skill before taking action.

## Red Flags

These thoughts mean stop and re-check skills:

- "This is just a small screen."
- "It looks fine from code."
- "No need to test on mobile sizes."
- "The simulator or screenshot is optional."
- "Keyboard, safe area, loading, error, empty, or accessibility states can wait."
- "The HTML baseline can be skipped."
- "Flutter Web proves iOS and Android too."
- "The provider is always ZenMux."
- "The user asked for speed, so I can skip mobile workflow checks."
- "I remember the mobile skill well enough."

All of these mean: use the relevant mobile-superpowers skill before acting.

## Common Rationalizations

| Excuse | Reality |
|---|---|
| "Mobile is just responsive UI." | Mobile has touch, keyboard, viewport, permission, lifecycle, and platform constraints. |
| "I'll verify visually later." | Late visual checks find layout failures after decisions have hardened. |
| "This is only a prototype." | Prototypes still teach the wrong behavior if mobile constraints are ignored. |
| "I know the framework." | Framework knowledge does not replace project context or device-state checks. |
| "No mobile-specific skill is needed." | If the work touches mobile behavior or UX, check first. |

## Stop Condition

This skill ends only after the downstream skill has been selected and loaded, or after you explicitly state that no mobile-superpowers skill applies and why.
