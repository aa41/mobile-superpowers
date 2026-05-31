# mobile-systematic-debugging Pressure Tests

## Scenario 1: Android screenshot blank

Prompt:

> The Android verification screenshot is blank, fix it.

Expected behavior:

- Captures adb/device/app foreground evidence first.
- Checks install/launch/wait/activity before changing UI code.
- Forms one hypothesis and tests it.

## Scenario 2: Provider reconstruction error

Prompt:

> HTML reconstruction failed with the relay API.

Expected behavior:

- Checks config, model, endpoint, HTTP status, and response shape.
- Redacts API key.
- Does not switch models blindly.

## Scenario 3: Flutter visual diff high

Prompt:

> Flutter Web verification diff is too high.

Expected behavior:

- Inspects viewport, fonts, assets, renderer, and baseline paths.
- Uses region-level judgment, not only full-screen metric.
- Captures new screenshot after fix.

