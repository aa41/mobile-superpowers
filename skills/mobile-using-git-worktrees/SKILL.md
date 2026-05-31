---
name: mobile-using-git-worktrees
description: Use when starting mobile implementation work, executing mobile plans, or making platform changes that need workspace isolation
---

# Mobile Using Git Worktrees

## Overview

Mobile implementation should start in an isolated workspace whenever practical. Flutter, Android, iOS, screenshots, generated assets, and verification reports can all create noisy file changes.

**Core principle:** detect existing isolation first, prefer harness-native isolation, then fall back to `git worktree`.

Announce at start:

> I'm using the mobile-using-git-worktrees skill to protect the mobile work area.

## Step 0: Detect Existing Isolation

Run before creating anything:

```bash
git rev-parse --show-toplevel
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
git rev-parse --show-superproject-working-tree 2>/dev/null
git branch --show-current
```

If `GIT_DIR != GIT_COMMON` and `show-superproject-working-tree` is empty, you are already in a linked worktree. Do not create another one.

If the checkout is detached or externally managed, continue in place and record that branch finishing may require creating a branch later.

## Step 1: Choose Isolation Mechanism

Use this order:

1. Harness-native worktree or workspace tool, if available.
2. Existing project-local `.worktrees/` or `worktrees/`.
3. Existing global `~/.config/superpowers/worktrees/<project>/`.
4. New project-local `.worktrees/`.

If no preference is already known, ask before creating a new worktree. If the user declines, work in place and report the risk.

## Step 2: Git Worktree Fallback

Only use this when no native isolation tool is available.

Before creating a project-local worktree, verify it will not be committed:

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

If neither directory is ignored, add `.worktrees/` to `.gitignore` before creating the worktree.

Create a branch name tied to the mobile task:

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
branch="mobile/<short-topic>"
path=".worktrees/$branch"
git worktree add "$path" -b "$branch"
cd "$path"
```

If `git worktree add` fails because of sandbox or filesystem restrictions, report the failure and continue in the current checkout only if the user agrees or already asked to proceed.

## Step 3: Mobile Setup Check

Detect platform files and run only commands that exist for the repo:

| Signal | Setup check |
|---|---|
| `pubspec.yaml` | `flutter pub get` |
| `android/gradlew` or `gradlew` | existing Gradle wrapper task from the plan |
| `ios/Podfile` | `pod install` from `ios/` when CocoaPods is available |
| `Package.swift` | `swift package resolve` |
| `package.json` | package manager install matching lockfile |

Do not invent mobile commands. If the plan names setup commands, use those.

## Step 4: Clean Baseline

Run the fastest relevant baseline from the plan or repo:

| Platform | Baseline examples |
|---|---|
| Flutter | `flutter analyze`, `flutter test` |
| Android | `./gradlew test`, `./gradlew assembleDebug` |
| iOS | `xcodebuild -list`, project test/build command |
| React Native | repo package test command plus platform smoke command |
| mobile web | repo test/build command |

If baseline fails, stop and report the exact failing command. Do not begin implementation until the user approves proceeding or the failure is diagnosed.

## Completion Report

Report:

```text
Mobile worktree status: <existing|created|working in place>
Path: <path>
Branch: <branch or detached HEAD>
Baseline commands: <commands run>
Result: <pass|fail|skipped with reason>
```

## Red Flags

- Creating a nested worktree after Step 0 detected isolation.
- Using `git worktree add` when a harness-native tool is available.
- Creating `.worktrees/` without ignore verification.
- Treating Flutter Web, Android, and iOS baselines as interchangeable.
- Starting mobile implementation after a failed baseline without saying so.

