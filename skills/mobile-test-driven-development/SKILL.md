---
name: mobile-test-driven-development
description: Use when implementing mobile behavior, UI states, platform flows, or bug fixes before writing production code
---

# Mobile Test-Driven Development

## Overview

Mobile work needs proof before implementation: behavior tests for logic, widget/view tests for states, and screenshot or golden expectations for visual UI.

**Core principle:** write the failing mobile expectation first, watch it fail for the right reason, then implement the smallest change.

## Hard Gate

Do not write production mobile code before a failing test, missing artifact check, golden expectation, or screenshot expectation exists.

Exceptions must be explicit: throwaway prototypes, generated code, or pure documentation/config changes. State the exception and still run the closest validation.

## Mobile RED-GREEN-REFACTOR

### RED: Write The Mobile Expectation

Choose the strongest expectation that fits the task:

| Task type | RED expectation |
|---|---|
| Business logic | Unit test |
| State flow | View model/reducer/controller test |
| Flutter UI | Widget test or golden expectation |
| Android UI | Unit/instrumented test or screenshot expectation |
| iOS UI | XCTest/snapshot expectation |
| Visual conversion | Baseline screenshot comparison expectation |
| Asset work | Missing-asset or manifest verification check |

The expectation must name the mobile state: default, loading, empty, error, permission denied, offline, keyboard open, dark mode, dynamic type, orientation, or accessibility when relevant.

### Verify RED

Run the narrowest command and confirm it fails because the behavior or artifact is missing.

Examples:

```bash
flutter test test/profile_screen_test.dart
./gradlew testDebugUnitTest
xcodebuild test -scheme App -destination 'platform=iOS Simulator,name=iPhone 15'
python3 mobile-superpowers/scripts/mobile_visual_compare.py --reference ref.png --candidate candidate.png
```

If it passes immediately, the expectation is wrong or the behavior already exists. Fix the expectation before implementation.

### GREEN

Implement the smallest production change that satisfies the expectation. Do not add extra states, architecture, or visual polish beyond the task.

### REFACTOR

After GREEN only:

- Clean names and duplication.
- Align with existing project patterns.
- Keep tests and screenshots green.

## UI-Specific Rules

- Build pass is not UI proof.
- Screenshot-only is not behavior proof.
- Flutter Web proof is not native iOS/Android proof.
- A generated HTML baseline is a reference, not the final implementation.
- Asset placeholders must be resolved before UI completion.

## Platform Quick Reference

| Platform | Prefer |
|---|---|
| Flutter | `flutter test`, widget tests, golden tests, `flutter analyze` |
| Android | JVM tests, instrumented tests, Compose/UI screenshot checks, Gradle tasks |
| iOS | XCTest, snapshot tests when available, xcodebuild test |
| React Native | Jest for state, Detox/Maestro/Appium when available |
| mobile web | browser tests, mobile viewport screenshots |

Use repo-specific commands from the plan. Do not invent frameworks that are not present.

## Red Flags

- "I'll add tests after I see it working."
- "This is just UI, no test needed."
- "A screenshot diff replaces all behavior tests."
- "The emulator is unavailable, so I can claim it works."
- "The test passed immediately, good enough."
- "I'll implement all states first, then test them together."

