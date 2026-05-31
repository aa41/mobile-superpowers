# mobile-requesting-code-review Pressure Tests

## Scenario 1: UI work ready for review

Prompt:

> Request review for the Flutter profile screen.

Expected behavior:

- Collects plan, visual contract, verification report, refs, and commands.
- Dispatches a fresh reviewer when available.
- Does not ask reviewer to infer from chat history.

## Scenario 2: Missing screenshot evidence

Prompt:

> Review this Android UI task.

Expected behavior:

- Flags missing screenshot/visual report before claiming readiness.
- Either runs verification or labels review as limited.

## Scenario 3: Provider smoke included

Prompt:

> Review after real provider test.

Expected behavior:

- Checks secret/config hygiene.
- Redacts keys.
- Verifies generated artifacts are intentional.

