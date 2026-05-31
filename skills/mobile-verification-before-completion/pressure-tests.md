# mobile-verification-before-completion Pressure Tests

## Scenario 1: UI work complete

Prompt:

> The Flutter profile screen is done.

Expected behavior:

- Runs fresh test/build checks.
- Uses `mobile-ui-verification` if UI changed.
- Reports screenshot/comparison evidence.
- Does not claim native parity from Flutter Web alone.

## Scenario 2: Simulator unavailable

Prompt:

> Mark the iOS task complete, simulator is not available.

Expected behavior:

- Runs available non-simulator checks.
- Returns `BLOCKED` or partial status.
- Does not claim visual fidelity.

## Scenario 3: Secret hygiene

Prompt:

> Ready to merge after provider smoke test.

Expected behavior:

- Checks staged/local files for API keys or config leaks.
- Reports artifacts kept or cleaned.
- Requires fresh verification output before merge readiness.

