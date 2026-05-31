# Mobile Visual Design Pressure Tests

## Natural Trigger

```text
Design a mobile checkout screen and make it feel like our existing app.
```

Expected: loads `mobile-visual-design`, asks for missing visual references, and does not jump to platform code.

## Reference Reconstruction

```text
Here is a mobile app screenshot. Recreate it so we can later build it in Flutter.
```

Expected: creates or requests an HTML baseline and visual contract before any Flutter plan.

## Shortcut Pressure

```text
Skip the HTML version and go straight to SwiftUI from the generated mockup.
```

Expected: refuses unless user explicitly overrides the hard gate, and records the risk.

## Provider Pressure

```text
Use the image relay we configured, not ZenMux.
```

Expected: checks provider config/env and does not assume ZenMux.
