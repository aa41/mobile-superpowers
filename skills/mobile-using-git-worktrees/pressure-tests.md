# mobile-using-git-worktrees Pressure Tests

## Scenario 1: Normal repo, mobile plan execution

Prompt:

> Execute this Flutter implementation plan.

Expected behavior:

- Loads `mobile-using-git-worktrees` before editing.
- Runs worktree detection before creating anything.
- Uses harness-native isolation if available, otherwise asks or uses declared preference.
- Verifies `.worktrees/` is ignored before `git worktree add`.
- Runs Flutter baseline only if project files support it.

Failure signs:

- Jumps directly into editing.
- Creates nested worktree.
- Invents platform commands.

## Scenario 2: Existing linked worktree

Prompt:

> Continue this Android implementation task.

Environment:

- `GIT_DIR != GIT_COMMON`
- Not a submodule

Expected behavior:

- Reports existing isolation.
- Does not create another worktree.
- Runs baseline checks from the plan.

## Scenario 3: Baseline failure

Prompt:

> Start the iOS implementation.

Environment:

- `xcodebuild` command in the plan fails.

Expected behavior:

- Stops before implementation.
- Reports command and failure.
- Asks whether to diagnose or proceed with known failing baseline.

