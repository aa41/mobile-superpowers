---
name: mobile-ui-verification
description: Use when mobile UI work is claimed complete, visual fidelity must be checked, platform screenshots are needed, or HTML baselines must be compared against Flutter, Android, iOS, React Native, or mobile web implementations
---

# Mobile UI Verification

## Overview

Verify mobile UI with evidence. Build success is not visual success. A mobile UI is not complete until platform screenshots or golden evidence have been compared against the approved spec, visual contract, or HTML baseline.

<HARD-GATE>
Do not claim mobile UI work is done based only on code review, build success, or visual intuition.

Run the appropriate platform verification, capture evidence, compare against the approved reference, and report actual differences before making completion claims.
</HARD-GATE>

## Inputs

- Approved spec or plan
- Visual contract, if available
- HTML baseline screenshot, if available
- Asset manifest (`assets.json`), if available
- Similarity metrics (`baseline-metrics.json` or platform metrics), if available
- Platform target: Flutter, Android, iOS, React Native, mobile web
- Build/test commands from the repo
- Device/emulator/simulator target

If there is no approved reference, say so. You can still run smoke checks, but do not claim visual fidelity.

## Verification Ladder

Use the strongest available evidence:

1. Unit/widget tests for behavior
2. Build/compile check
3. Platform render check
4. Screenshot or golden capture
5. Similarity comparison against HTML baseline or reference
6. Human-readable visual regression report

Use the report helper after screenshots and metrics exist:

```bash
python3 mobile-superpowers/scripts/mobile_ui_verification_report.py \
  --out-dir "docs/mobile-superpowers/verification/<date-topic>" \
  --target "<screen or flow>" \
  --platform "<Flutter Web|Android|iOS|React Native|mobile web>" \
  --plan "<plan.md>" \
  --visual-contract "<visual-contract.md>" \
  --baseline-screenshot "<baseline-screenshot.png>" \
  --platform-screenshot "<platform-screenshot.png>" \
  --metrics "<baseline-metrics.json>" \
  --assets "<assets.json>" \
  --command "<command actually run>" \
  --environment "<device/browser/simulator details>"
```

The helper writes `verification-report.md` and returns one completion assessment: `VERIFIED`, `VERIFIED_WITH_DEVIATIONS`, `NOT_VERIFIED`, or `BLOCKED`.

## Platform Recipes

Use repo-specific commands when available. These are patterns, not commands to invent blindly.

### Flutter

Fast checks:

```bash
flutter test
flutter analyze
```

HTML baseline transition:

```bash
flutter build web
```

Then serve `build/web`, capture browser screenshot at the target mobile viewport, and compare with the HTML baseline.

Use the Flutter Web adapter when the repo is a Flutter project and a visual baseline exists:

```bash
python3 mobile-superpowers/scripts/mobile_flutter_web_verify.py \
  --project-dir "<flutter-project>" \
  --target "<screen or flow>" \
  --visual-contract "<visual-contract.md>" \
  --baseline-screenshot "<baseline-screenshot.png>" \
  --assets "<assets.json>" \
  --plan "<plan.md>" \
  --execute
```

The adapter runs `flutter build web`, serves `build/web`, captures a mobile viewport screenshot, compares it with the HTML baseline screenshot, and writes `verification-report.md`. Use `--dry-run --json` first to inspect planned paths and commands.

Native final checks may use golden tests or simulator/emulator screenshots.

### Android

Common screenshot pattern:

```bash
adb exec-out screencap -p > android-screen.png
```

Use the Android adapter when an emulator/device is prepared and a visual baseline exists:

```bash
python3 mobile-superpowers/scripts/mobile_android_verify.py \
  --project-dir "<android-project>" \
  --target "<screen or flow>" \
  --visual-contract "<visual-contract.md>" \
  --baseline-screenshot "<baseline-screenshot.png>" \
  --assets "<assets.json>" \
  --plan "<plan.md>" \
  --apk "<app-debug.apk>" \
  --launch-activity "<package/.Activity>" \
  --execute
```

The adapter can optionally run `--build-command "<repo build command>"`, install an APK, launch an activity, capture `adb exec-out screencap -p`, compare against the HTML baseline screenshot, and write `verification-report.md`. Use `--dry-run --json` first to inspect planned commands.

Before screenshot:

- Install or run the app
- Navigate to the target screen
- Wait for loading/animation to settle
- Fix device, density, font scale, theme, and orientation where possible

### iOS

Common simulator screenshot pattern:

```bash
xcrun simctl io booted screenshot ios-screen.png
```

Use the iOS adapter when a simulator is prepared and a visual baseline exists:

```bash
python3 mobile-superpowers/scripts/mobile_ios_verify.py \
  --project-dir "<ios-project>" \
  --target "<screen or flow>" \
  --visual-contract "<visual-contract.md>" \
  --baseline-screenshot "<baseline-screenshot.png>" \
  --assets "<assets.json>" \
  --plan "<plan.md>" \
  --app "<Runner.app>" \
  --bundle-id "<bundle.id>" \
  --execute
```

The adapter can optionally run `--build-command "<repo build command>"`, install an app into a simulator, launch a bundle id, capture `xcrun simctl io <device> screenshot`, compare against the HTML baseline screenshot, and write `verification-report.md`. Use `--dry-run --json` first to inspect planned commands. The default device is `booted`.

Before screenshot:

- Boot the intended simulator
- Install or run the app
- Navigate to the target screen
- Wait for stable state
- Record device model, iOS version, appearance, text size, and orientation

### React Native

Use the repo's e2e stack when present: Detox, Maestro, Appium, or platform-native screenshots. If none exists, use Android/iOS screenshot recipes after launching the app.

### Mobile Web

Use browser mobile viewport screenshots and compare against the HTML baseline or approved reference.

## Similarity Comparison

Compare these when available:

| Comparison | Purpose |
|---|---|
| Reference vs HTML baseline | Baseline fidelity |
| HTML baseline vs platform screenshot | Platform conversion fidelity |
| Reference vs platform screenshot | Accumulated drift |

For each comparison, record:

- Candidate screenshot path
- Reference path
- Diff/heatmap path if generated
- Metrics path if generated
- Region notes: header/status area, content, primary CTA, bottom navigation, state-specific area
- Acceptable deviations
- Must-fix deviations

Do not rely on one full-screen metric. Use region-level judgment for important UI areas.

## Mobile State Checklist

Verify or explicitly mark non-goal:

- Safe area and status/navigation bars
- Keyboard open
- Loading
- Empty
- Error
- Permission denied
- Offline
- Dark mode
- Dynamic type/font scale
- Screen reader labels for interactive controls
- Touch target size
- Orientation, if relevant

## Report Format

```markdown
# Mobile UI Verification Report

## Target
## Commands Run
## Environment
## References
## Screenshots Captured
## Similarity Results
## Asset Verification
## State Coverage
## Must-Fix Issues
## Acceptable Deviations
## Completion Assessment
```

Completion assessment must be one of:

- `VERIFIED`
- `VERIFIED_WITH_DEVIATIONS`
- `NOT_VERIFIED`
- `BLOCKED`

## Red Flags

- "The build passed, so UI is done."
- "It looks right from the code."
- "Screenshots are unnecessary."
- "Flutter Web matched, so native must match."
- "One full-screen diff metric is enough."
- "Status bar, safe area, keyboard, and font scale do not matter."
- "I cannot run the simulator, but it should be fine."

All of these mean: stop and gather evidence or state the real limitation.

## Testing This Skill

Use `pressure-tests.md` when changing this skill.
