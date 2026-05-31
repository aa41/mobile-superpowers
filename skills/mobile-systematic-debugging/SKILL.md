---
name: mobile-systematic-debugging
description: Use when mobile tests, builds, simulators, devices, screenshots, visual comparisons, providers, or platform behavior fail unexpectedly
---

# Mobile Systematic Debugging

## Overview

Mobile failures have layers: app code, framework, platform project, simulator/device, build tool, signing, assets, provider API, and screenshot environment. Guessing across layers burns time.

**Core principle:** reproduce, locate the failing layer, form one hypothesis, test it, then fix the root cause.

## Hard Gate

No fix before evidence. If you have not reproduced or collected the failing command, logs, device state, and recent changes, do not propose a fix.

## Phase 1: Reproduce And Capture Evidence

Record:

- Exact command or user steps.
- Full error output and exit code.
- Platform target: Flutter, Android, iOS, React Native, mobile web.
- Device/simulator/emulator/browser, OS version, orientation, theme, font scale.
- Recent code/config/asset/provider changes.
- Whether failure is deterministic.

Useful evidence:

| Area | Evidence |
|---|---|
| Flutter | `flutter doctor -v`, `flutter analyze`, `flutter test`, `flutter run -v` |
| Android | Gradle output, `adb devices`, `adb logcat`, manifest/activity info |
| iOS | `xcodebuild` output, `xcrun simctl list`, simulator logs, bundle id |
| Visual | reference screenshot, candidate screenshot, diff, metrics, viewport |
| Provider | base URL, model names, HTTP status, response body shape, request id if available |

Do not paste secrets. Redact API keys and tokens.

## Phase 2: Isolate The Layer

Ask which boundary fails:

- Does pure logic test pass?
- Does build pass without launching?
- Does app install?
- Does launch succeed?
- Does target screen render?
- Does screenshot capture work?
- Does comparison fail because of image content, viewport, density, font, asset, or implementation?

Compare with a working screen or previous artifact in the same repo.

## Phase 3: One Hypothesis

State one hypothesis:

```text
Hypothesis: <root cause> because <evidence>.
Test: <small command/change that can prove or disprove it>.
```

Test one variable at a time. If it fails, update the hypothesis instead of stacking fixes.

After three failed fix attempts, stop and reassess the architecture, plan, or environment.

## Phase 4: Fix With Regression Proof

Before fixing, create the smallest regression test, screenshot expectation, fixture, or validation command that fails. Then:

1. Implement one root-cause fix.
2. Re-run the narrow verification.
3. Re-run broader platform checks from the plan.
4. Update verification report if UI was affected.

## Common Mobile Failure Patterns

| Symptom | Likely layers to inspect |
|---|---|
| Flutter Web screenshot mismatch | viewport, font loading, asset paths, CanvasKit/html renderer, safe area assumptions |
| Android blank screenshot | launch activity, app not foreground, permissions, wait timing, emulator state |
| iOS install/launch failure | bundle id, signing, simulator target, build output path |
| Golden diff too high | density, dynamic type, anti-aliasing, missing assets, theme mode |
| Provider HTML reconstruction failure | model config, response content shape, image URL/base64, relay compatibility |
| Keyboard layout bug | focus timing, resize behavior, safe area/insets, scroll view constraints |

## Red Flags

- Changing code before reading the full error.
- Trying multiple fixes at once.
- Treating simulator/device setup failure as app correctness.
- Ignoring density, safe area, font scale, or theme differences in screenshot diffs.
- Saying "probably provider issue" without HTTP evidence.
- Claiming a visual bug fixed without a new screenshot.

