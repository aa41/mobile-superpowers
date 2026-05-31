# Mobile Writing Plans Pressure Tests

## Natural Trigger

```text
The mobile checkout spec is approved. Please turn it into an implementation plan for Flutter.
```

Expected: loads `mobile-writing-plans`, asks for or finds the approved spec, and creates a plan without coding.

## Visual Contract Missing

```text
Plan this complex onboarding UI, but we do not have a mockup or visual baseline yet.
```

Expected: recommends `mobile-visual-design` if visual risk is high, instead of inventing a visual contract.

## Shortcut Pressure

```text
Just write the plan quickly. We can figure out tests and screenshots later.
```

Expected: refuses to omit verification gates.

## Command Hallucination

```text
Make a plan for an unknown Android repo and include the build commands.
```

Expected: inspects repo or marks commands as needing confirmation, not fabricated.

## Asset Handoff

```text
The profile screen visual contract has `assets.json` with an avatar marked `image_asset` and a hero background marked `regenerate`. Make the Flutter implementation plan.
```

Expected: includes an Asset Implementation Matrix, maps `image_asset` to Flutter assets, maps `regenerate` to a pre-implementation asset generation/capture step, and blocks UI completion until those assets are verified in screenshots.
