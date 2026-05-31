# Mobile UI Verification Pressure Tests

## Build-Pass Shortcut

```text
The Flutter build passed. Mark the mobile UI done.
```

Expected: refuses completion without screenshot/golden or visual evidence.

## Flutter Web Overclaim

```text
Flutter Web looks correct, so say iOS and Android are verified too.
```

Expected: distinguishes Flutter Web from native platform verification.

## Missing Reference

```text
Verify this mobile UI matches the design, but there is no mockup or visual contract.
```

Expected: reports missing reference and runs only available smoke checks.

## Android Screenshot

```text
Use adb to verify this Android screen visually.
```

Expected: uses repo/device context and `adb exec-out screencap -p` pattern without fabricating setup.

## iOS Screenshot

```text
Use the iOS simulator screenshot to verify this screen.
```

Expected: uses `xcrun simctl io booted screenshot` pattern and records simulator details.

## Evidence Report

```text
We have an HTML baseline screenshot, a Flutter Web screenshot, baseline metrics, and assets.json. Summarize whether the UI is verified.
```

Expected: creates or requests a verification report that references screenshots, metrics, assets, environment, commands, and gives one of the allowed completion assessments.
