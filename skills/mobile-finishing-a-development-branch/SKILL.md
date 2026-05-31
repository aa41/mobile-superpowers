---
name: mobile-finishing-a-development-branch
description: Use when mobile implementation is verified and needs merge, pull request, branch preservation, artifact cleanup, or discard decisions
---

# Mobile Finishing A Development Branch

## Overview

Finish mobile work by verifying evidence, detecting workspace ownership, presenting integration options, and preserving the artifacts needed for review.

**Core principle:** verify first, then choose merge/PR/keep/discard, then clean only what is safe to clean.

Announce at start:

> I'm using the mobile-finishing-a-development-branch skill to complete this mobile branch.

## Step 1: Completion Verification

Use `mobile-verification-before-completion` before presenting branch options.

Stop if assessment is `NOT_VERIFIED` or `BLOCKED`, unless the user explicitly wants to keep the branch as-is.

## Step 2: Review Gate

If not already done, use `mobile-requesting-code-review` for substantial mobile work before merge/PR readiness.

If review returns Critical or Important issues, use `mobile-receiving-code-review` and resolve them before merge/PR.

## Step 3: Detect Workspace

Run:

```bash
git status --short
git branch --show-current
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
git rev-parse --show-toplevel
```

Classify:

| State | Meaning |
|---|---|
| `GIT_DIR == GIT_COMMON` | normal checkout |
| `GIT_DIR != GIT_COMMON` with branch | named worktree |
| `GIT_DIR != GIT_COMMON` detached | externally managed or detached workspace |

Understand every changed file before offering destructive options. Pay special attention to generated screenshots, diffs, reports, build outputs, local config, and API keys.

## Step 4: Present Options

For normal checkout or named worktree:

```text
Mobile implementation is verified. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch/worktree as-is
4. Discard this work

Which option?
```

For detached or externally managed workspace:

```text
Mobile implementation is verified. You're in a detached or externally managed workspace.

1. Push as a new branch and create a Pull Request
2. Keep as-is
3. Discard this work

Which option?
```

## Step 5: PR Content For Mobile Work

When creating a PR, include:

- Summary of mobile feature/fix.
- Target platforms.
- Test/build commands run.
- Device/simulator/browser details.
- UI verification report and screenshot paths.
- Known deviations or blocked checks.
- Artifact and secret hygiene statement.

Do not include API keys or local provider config.

## Step 6: Cleanup Rules

- Preserve worktree for PR iteration.
- Preserve verification reports/screenshots/diffs only when useful for review.
- Remove accidental build outputs and local config.
- Clean worktrees only when owned by this workflow: `.worktrees/`, `worktrees/`, or `~/.config/superpowers/worktrees/`.
- Never delete work without typed `discard` confirmation.
- After owned worktree removal, run `git worktree prune`.

## Red Flags

- Presenting merge/PR options before mobile completion verification.
- Creating PR without device/platform evidence.
- Cleaning a harness-owned worktree.
- Deleting screenshots/reports that reviewers need.
- Leaving API keys or local config in tracked changes.
- Discarding without typed confirmation.

