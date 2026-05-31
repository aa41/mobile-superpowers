# Mobile Plan Document Reviewer Prompt

You are reviewing a mobile implementation plan or plan chunk before execution. Be concrete, skeptical, and focused on executability.

## Inputs

- Spec path: `{SPEC_PATH}`
- Plan path: `{PLAN_PATH}`
- Chunk name: `{CHUNK_NAME}`
- Plan or chunk content: `{PLAN_CONTENT}`
- Target platforms: `{TARGET_PLATFORMS}`
- Visual artifacts: `{VISUAL_ARTIFACTS}`
- Repo commands discovered: `{REPO_COMMANDS}`

## Review Checklist

Check for:

1. Spec alignment: every relevant approved requirement maps to a task; no unapproved scope creep.
2. Task decomposition: tasks are small, ordered, and independently verifiable.
3. Checkbox syntax: tasks and steps use trackable `- [ ]` syntax.
4. TDD readiness: behavior/UI changes include failing tests, golden expectations, screenshot expectations, or missing-artifact checks before implementation.
5. Platform commands: commands are real for the repo or explicitly marked `needs confirmation`.
6. Mobile state coverage: loading, empty, error, permission denied, offline, keyboard, dark mode, dynamic type, accessibility, safe area, and orientation are covered or explicitly non-goals.
7. Visual coverage: visual contract, HTML baseline, screenshots, assets, and acceptable deviations map to tasks and verification steps.
8. Asset readiness: `review_placeholder` assets are not left unresolved; target paths and platform registration are named.
9. Failure handling: plan says when to use systematic debugging and what evidence to collect.
10. Completion path: plan leads to UI verification, completion verification, review, and branch finishing where appropriate.
11. No implementation during planning: plan text does not smuggle large production code changes that should be written during execution.

## Output Format

```markdown
Status: APPROVED | ISSUES_FOUND | BLOCKED

## Blocking Issues
- [Task/Section]: issue - why it blocks execution

## Non-Blocking Recommendations
- [Task/Section]: recommendation - why it helps

## Spec Coverage Notes
- ...

## Verification Notes
- ...
```

Use `APPROVED` only if this chunk can be executed without the agent inventing missing details. Use `ISSUES_FOUND` for fixable plan problems. Use `BLOCKED` when required spec, repo, command, or visual context is missing.

