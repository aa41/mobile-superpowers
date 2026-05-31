# mobile-test-driven-development Pressure Tests

## Scenario 1: Flutter state change

Prompt:

> Add offline state to this Flutter profile screen.

Expected behavior:

- Writes or identifies a failing widget/state test first.
- Verifies RED before changing production code.
- Implements only the offline state.
- Runs `flutter test` or the repo equivalent.

## Scenario 2: Visual-only screen

Prompt:

> Match this HTML baseline in Android.

Expected behavior:

- Creates a screenshot/golden/missing-visual expectation before UI code.
- Does not treat `assembleDebug` as final visual proof.
- Uses `mobile-ui-verification` after implementation.

## Scenario 3: Config-only task

Prompt:

> Register these Flutter assets in pubspec.yaml.

Expected behavior:

- States why code TDD does not apply.
- Runs an asset/config validation such as `flutter pub get` or a manifest check.

