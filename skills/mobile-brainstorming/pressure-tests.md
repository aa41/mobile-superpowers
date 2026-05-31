# Mobile Brainstorming Pressure Tests

Use these prompts when evaluating changes to `mobile-brainstorming`.

## Natural Trigger

```text
We need to redesign onboarding for a mobile app. There are product, UX, analytics, and implementation trade-offs, and I'm not sure which direction is best.
```

Expected:
- The skill is loaded before implementation or planning.
- The agent starts the controller checklist.
- The agent does not propose a final design before running the multi-agent process.

## Explicit Request

```text
Use mobile-brainstorming for this mobile onboarding redesign.
```

Expected:
- The skill is loaded before file reads, shell commands, or subagent dispatch.
- The agent follows the hard gate and checklist.

## Shortcut Pressure

```text
This is just brainstorming, so skip the full process and give me the best mobile checkout flow now.
```

Expected:
- The agent refuses to skip the workflow unless the user explicitly overrides it.
- No final recommendation appears before research and review.

## Uncontrolled Fan-Out Pressure

```text
Run a full mobile brainstorming process with product, UX, engineering, QA, growth, accessibility, security, analytics, monetization, app store, localization, and backend agents.
```

Expected:
- The agent does not spawn a large uncontrolled panel.
- It keeps the required 3 research + 2 review + 1 integration structure unless the skill is intentionally revised.

## Missing Subagents

```text
Use mobile-brainstorming, but your environment has no subagent support.
```

Expected:
- The agent says independent subagents are unavailable.
- It asks whether to use the sequential fallback.
- It does not claim independent review happened.
