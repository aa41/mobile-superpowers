---
name: mobile-executing-plans
description: Use when executing an approved mobile implementation plan for Flutter, Android, iOS, React Native, or mobile web
---

# Mobile Executing Plans

## Overview

Execute approved mobile plans task by task, with workspace isolation and platform evidence. A plan is not complete until its tests, builds, screenshots, and verification gates have actually run or are explicitly blocked.

Announce at start:

> I'm using the mobile-executing-plans skill to implement this mobile plan.

## Hard Gate

Do not execute from an idea or draft. You need an approved written plan from `mobile-writing-plans` or an equivalent user-approved plan.

Before editing, use `mobile-using-git-worktrees` unless the user explicitly says to work in the current checkout.

If the plan is UI-heavy and has no visual contract or recorded user override, stop and return to `mobile-visual-design` or `mobile-writing-plans`. Do not silently implement visually significant UI from text alone.

Before implementation steps that change behavior or UI, use `mobile-test-driven-development`.

## Step 1: Load And Challenge The Plan

Read the plan fully. Check:

- Spec path and visual contract paths exist or are intentionally absent.
- Target platform is clear.
- Files and responsibilities are named.
- Commands are real for this repo or marked for confirmation.
- UI tasks include screenshot/golden/manual evidence.
- Asset tasks are resolved before UI completion.
- Project constraints exist when referenced, and required base components are named in UI tasks.

If a plan has critical gaps, stop and ask for a plan update. Do not silently invent architecture, commands, assets, or platform targets.

## Step 2: Create Execution Tracker

Create a task list from the plan. Keep exactly one task in progress.

For each task, track:

- Plan task title
- Files touched
- Test or visual expectation
- Command run
- Result
- Follow-up issue, if any

## Step 3: Execute Each Task

For every plan task:

1. Mark the task in progress.
2. Re-read the relevant plan section.
3. Use `mobile-test-driven-development` to write the failing behavior test, widget test, golden expectation, screenshot expectation, or missing-artifact check first when the task changes behavior or UI.
4. Verify the failure or missing artifact.
5. Implement the smallest change that satisfies the task.
6. Run the task's specified checks.
7. Capture UI evidence when UI changed.
8. Run the component contract check when the plan references project constraints.
9. Update the plan checkbox only after verification.

If a task is documentation-only or configuration-only, state why TDD does not apply and still run the closest validation.

## Step 4: Failure Handling

When a command, test, build, simulator step, screenshot, or comparison fails:

- Stop the current task.
- Record the exact command and failure.
- Reproduce once if the failure may be transient.
- Gather platform evidence before changing code.
- Use `mobile-systematic-debugging` if available; otherwise follow the same discipline manually: reproduce, inspect evidence, form one hypothesis, test it, then fix.

Do not guess-fix mobile failures. Logcat, simctl output, xcodebuild output, Flutter logs, and screenshot diffs are evidence.

## Step 5: Mobile UI Verification

For any UI-affecting task, run the strongest available verification:

1. Unit/widget tests.
2. Build/analyze check.
3. Platform render check.
4. Screenshot or golden capture.
5. Baseline comparison.
6. `mobile-ui-verification` report.

If the plan includes an HTML baseline, use the relevant adapter:

- Flutter: `mobile_flutter_web_verify.py`
- Android: `mobile_android_verify.py`
- iOS: `mobile_ios_verify.py`

If the target device or simulator is unavailable, mark verification `BLOCKED` with the missing dependency. Do not claim visual fidelity.

## Project Component Contract

When `docs/mobile-superpowers/project-constraints.md` or a project style skill is referenced:

- Read the compact constraints before editing UI files.
- Use required base components and tokens, for example `CommonText`, `CommonDialog`, `CommonButton`, `AppColors`, or `AppSpacing`.
- Keep direct platform primitives inside base component/theme folders when the project contract requires wrappers.
- For Flutter, run:

```bash
python3 mobile-superpowers/scripts/mobile_component_contract_check.py \
  --project-dir "<project-dir>" \
  --platform flutter \
  --contract "docs/mobile-superpowers/project-constraints.md"
```

If the checker reports violations, fix them or record an explicit exception approved by the user before claiming the UI task is complete.

## Step 6: Final Completion Gate

Before saying the work is complete:

- All plan tasks are checked or explicitly blocked.
- Required tests/builds were run and results are reported.
- UI changes have screenshots or a reason they could not be captured.
- Visual contract deviations are listed.
- Project component contract violations are fixed or explicitly approved.
- Generated assets, screenshots, diffs, and reports are either intentionally saved or cleaned.
- API keys and local config files are not staged.
- Remaining risks are explicit.

After final verification, use `mobile-requesting-code-review` for substantial mobile work. Use `mobile-finishing-a-development-branch` after review issues are resolved or intentionally deferred.

Use `mobile-verification-before-completion` before making any final completion, fixed, verified, ready-for-review, or ready-to-merge claim.

## Stop Conditions

Stop and ask when:

- The plan is not approved.
- The plan omits a critical command, asset, or platform target.
- Baseline tests fail before implementation.
- Device/emulator/simulator access is required but unavailable.
- Verification fails repeatedly.
- The user changes scope mid-plan.

## Red Flags

- Editing before workspace isolation.
- Treating a build pass as UI completion.
- Skipping screenshots because the code "looks right".
- Using raw `Text`, dialogs, buttons, or hard-coded colors after the plan requires project base components.
- Marking a task done before its command runs.
- Changing plan scope without updating the plan.
- Leaving generated mobile artifacts or secrets unstaged/uncategorized.
