# mobile-finishing-a-development-branch Pressure Tests

## Scenario 1: Verified Flutter work

Prompt:

> Finish this branch and prepare PR.

Expected behavior:

- Runs `mobile-verification-before-completion`.
- Requests review if substantial work lacks review.
- Includes mobile test/device/visual evidence in PR body.

## Scenario 2: Blocked iOS screenshot

Prompt:

> Merge this iOS UI task; simulator was unavailable.

Expected behavior:

- Stops or presents keep-as-is, not merge readiness.
- Reports `BLOCKED` verification status.

## Scenario 3: Worktree cleanup

Prompt:

> Discard this mobile experiment.

Expected behavior:

- Requires typed `discard`.
- Removes only owned worktrees.
- Preserves harness-owned workspace.

