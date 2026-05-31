---
name: mobile-receiving-code-review
description: Use when receiving mobile code review feedback before changing Flutter, Android, iOS, React Native, mobile web, visual, or verification work
---

# Mobile Receiving Code Review

## Overview

Mobile review feedback must be verified against repo reality, platform constraints, and the approved plan before implementation.

**Core principle:** evaluate feedback technically, then fix one verified item at a time.

## Response Pattern

1. Read all feedback.
2. Classify each item: Critical, Important, Minor, Question, or Wrong/Needs Pushback.
3. Verify against code, plan, visual contract, platform behavior, and existing patterns.
4. Clarify unclear items before implementing.
5. Implement one item at a time.
6. Run the narrow test/verification for that item.
7. Run broader mobile completion verification after all accepted items.

## Mobile Evaluation Checklist

For each review item ask:

- Does it map to an approved requirement or real defect?
- Does it apply to the target platform?
- Would the change break another platform or state?
- Is there existing repo architecture that explains the current approach?
- Does it affect visual fidelity, assets, safe areas, keyboard, accessibility, dynamic type, offline, or permissions?
- Does it require updated screenshots, diffs, golden files, or verification reports?
- Is it YAGNI for this mobile feature?

## Handling Feedback

| Feedback type | Action |
|---|---|
| Critical and verified | Fix immediately with test/verification |
| Important and verified | Fix before readiness |
| Minor | Fix if cheap or record as follow-up |
| Unclear | Ask before implementing |
| Wrong or risky | Push back with evidence |
| Conflicts with user decision | Stop and ask the user |

Do not performatively agree. State the technical action or evidence.

## Implementation Rules

- Use `mobile-test-driven-development` for behavior/UI changes.
- Use `mobile-systematic-debugging` if feedback reports a failure.
- Use `mobile-ui-verification` when UI output changes.
- Use `mobile-verification-before-completion` before saying feedback is resolved.

## Red Flags

- Implementing all feedback in one batch with one final test.
- Accepting reviewer claims without checking the code.
- Updating UI without refreshing screenshots.
- Changing mobile architecture to satisfy an unused hypothetical.
- Saying "done" after code edits but before verification.

