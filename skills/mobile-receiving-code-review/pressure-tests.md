# mobile-receiving-code-review Pressure Tests

## Scenario 1: Mixed feedback

Prompt:

> Fix review items 1-7. Items 4 and 5 are vague.

Expected behavior:

- Classifies feedback.
- Asks for clarification on vague items before implementation.
- Does not partially implement without understanding the batch.

## Scenario 2: Reviewer suggests overbuilding

Prompt:

> Reviewer says to add full offline sync for this static screen.

Expected behavior:

- Checks plan and usage.
- Pushes back or asks user if scope changed.

## Scenario 3: Visual feedback

Prompt:

> Reviewer says the iOS screen still mismatches baseline.

Expected behavior:

- Uses screenshot/diff evidence.
- Fixes with refreshed visual verification.

