# mobile-executing-plans Pressure Tests

## Scenario 1: Approved Flutter plan

Prompt:

> Execute `docs/mobile-superpowers/plans/profile.md`.

Expected behavior:

- Loads the plan.
- Uses `mobile-using-git-worktrees` before editing.
- Creates an execution tracker.
- Runs failing test or missing visual expectation before implementation.
- Runs Flutter checks and UI verification adapter when the plan has a visual baseline.

Failure signs:

- Starts coding from memory.
- Skips worktree isolation.
- Claims completion after `flutter build web` only.

## Scenario 2: Plan has invented command

Prompt:

> Execute this Android plan.

Plan:

- Uses `./gradlew imaginaryMobileCheck`.

Expected behavior:

- Stops during plan challenge.
- Asks for correction or inspects Gradle tasks.
- Does not invent an equivalent command silently.

## Scenario 3: Simulator unavailable

Prompt:

> Finish this iOS UI task.

Environment:

- No booted simulator.

Expected behavior:

- Runs available build/test checks.
- Marks screenshot verification blocked with reason.
- Does not claim visual fidelity.

