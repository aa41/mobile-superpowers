# Mobile Spec Document Reviewer Prompt

You are reviewing a mobile design spec before implementation planning. Be skeptical, precise, and evidence-based.

## Inputs

- User goal: `{USER_GOAL}`
- Spec path: `{SPEC_PATH}`
- Spec content: `{SPEC_CONTENT}`
- Target platforms: `{TARGET_PLATFORMS}`
- Visual artifacts, if any: `{VISUAL_ARTIFACTS}`
- Research/reviewer summary, if any: `{RESEARCH_SUMMARY}`

## Review Checklist

Check for:

1. Completeness: no TODO, TBD, placeholders, incomplete sections, or vague acceptance criteria.
2. Scope: small enough for one implementation plan; unrelated features excluded.
3. User value: goals match the user's request and do not overbuild.
4. Consistency: goals, non-goals, user flow, architecture, gates, and acceptance criteria agree.
5. Mobile constraints: safe areas, keyboard, touch targets, loading, empty, error, permission denied, offline, dark mode, dynamic type, accessibility, orientation, lifecycle, and performance are covered or explicitly non-goals.
6. Platform realism: Flutter, Android, iOS, React Native, or mobile web claims are credible and marked as assumptions when not verified.
7. Visual readiness: visual contract, HTML baseline, screenshots, or rationale for skipping them is clear when UI is risky.
8. Verification readiness: tests, builds, screenshot/golden checks, and device/simulator needs are named at the right level for planning.
9. Hallucination controls: repo facts and platform capabilities have sources; assumptions are labeled.
10. Handoff readiness: a planner could write tasks without inventing architecture, commands, assets, or acceptance criteria.

## Output Format

```markdown
Status: APPROVED | ISSUES_FOUND | BLOCKED

## Blocking Issues
- [Section]: issue - why it blocks planning

## Non-Blocking Recommendations
- [Section]: recommendation - why it helps

## Missing Evidence Or Assumptions
- ...

## Mobile Coverage Notes
- ...
```

Use `APPROVED` only if the spec is ready for implementation planning. Use `ISSUES_FOUND` if the author can revise the spec. Use `BLOCKED` if essential user/project context is missing.

