#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date as date_type
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "mobile-plan"


def read_assets(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    assets = data.get("assets", [])
    return assets if isinstance(assets, list) else []


def platform_asset_handling(platform: str, asset: dict[str, Any]) -> str:
    strategy = str(asset.get("strategy", ""))
    target = str(asset.get("target_path", ""))
    normalized = platform.strip().lower()
    if strategy == "code":
        return "Implement with platform-native drawing/widgets; no bitmap asset should be required."
    if strategy == "icon":
        return "Use existing platform/design-system icon or checked-in vector asset."
    if strategy == "crop":
        return f"Crop from the reference/mockup and save to `{target}` before UI implementation."
    if strategy == "regenerate":
        return f"Regenerate the image asset, save to `{target}`, then compare against the visual contract."
    if strategy == "review_placeholder":
        return "Reclassify before implementation; do not leave this placeholder unresolved."
    if normalized == "flutter":
        return f"Place under `{target or 'assets/images/...'}` and register it in `pubspec.yaml`."
    if normalized == "android":
        return f"Place under `{target or 'app/src/main/res/drawable'}` or `app/src/main/assets`."
    if normalized == "ios":
        return f"Place in `{target or 'Assets.xcassets'}`."
    if normalized == "react native":
        return f"Place under `{target or 'src/assets/...'}` and reference from the component."
    if normalized == "mobile web":
        return f"Place under `{target or 'public/assets/...'}` or the repo asset pipeline."
    return f"Place in the platform asset pipeline at `{target or 'needs target path'}`."


def asset_matrix(platform: str, assets: list[dict[str, Any]]) -> str:
    lines = [
        "## Asset Implementation Matrix",
        "",
        "| Asset | Strategy | Source | Target Path | Platform Handling | Verification |",
        "|---|---|---|---|---|---|",
    ]
    if not assets:
        lines.append("| none | none | none | none | No asset manifest entries. | Confirm no bitmap assets are required in screenshot review. |")
    for asset in assets:
        name = str(asset.get("name", "asset"))
        strategy = str(asset.get("strategy", "review_placeholder"))
        source = str(asset.get("source", ""))
        target = str(asset.get("target_path", ""))
        handling = platform_asset_handling(platform, asset)
        verification = "Verify the asset is present and visually correct in the platform screenshot/golden."
        lines.append(f"| {name} | {strategy} | {source} | {target} | {handling} | {verification} |")
    return "\n".join(lines)


def plan_markdown(
    *,
    feature: str,
    platform: str,
    spec: str,
    visual_contract: Path | None,
    assets_path: Path | None,
    assets: list[dict[str, Any]],
) -> str:
    visual_dir = visual_contract.parent if visual_contract else None
    baseline = visual_dir / "baseline.html" if visual_dir else None
    screenshot = visual_dir / "baseline-screenshot.png" if visual_dir else None
    reference = visual_dir / "reference.png" if visual_dir else None
    needs_asset_task = bool(assets)
    return f"""# {feature} Mobile Implementation Plan

> **For agentic workers:** Use task-by-task execution. Follow the mobile verification gates in this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement {feature} from the approved mobile spec.
**Target Platform:** {platform}
**Architecture:** Follow existing repository patterns. Keep UI state, assets, and verification artifacts explicit in each task.
**Visual Baseline:** `{baseline if baseline else "none"}`
**Asset Manifest:** `{assets_path if assets_path else "none"}`
**Verification Strategy:** Run platform tests/builds, capture a mobile screenshot, and compare against the HTML baseline and visual contract.

---

## Source Inputs

- Approved spec: `{spec}`
- Visual contract: `{visual_contract if visual_contract else "none"}`

## File And Responsibility Map

- UI files: inspect repo and fill exact files before implementation.
- State/data files: inspect repo and fill exact files before implementation.
- Asset files: use the Asset Implementation Matrix below.
- Test files: inspect repo and fill exact test targets before implementation.
- Verification artifacts: screenshot/golden outputs and visual comparison metrics.

## Visual Artifacts

- Reference: `{reference if reference else "none"}`
- HTML baseline: `{baseline if baseline else "none"}`
- Baseline screenshot: `{screenshot if screenshot else "none"}`
- Visual contract: `{visual_contract if visual_contract else "none"}`
- Asset manifest: `{assets_path if assets_path else "none"}`
- Acceptable deviations: read from visual contract before implementation.
- Must-fix visual differences: read from visual contract before implementation.

{asset_matrix(platform, assets)}

## Tasks

### Task 1: Prepare Visual Assets

**Files:**
- Create: platform asset files listed in the Asset Implementation Matrix
- Modify: platform asset registry/config if required
- Test: asset presence or snapshot/golden target
- Visual artifact: `{visual_contract if visual_contract else "none"}`
- Asset artifact: `{assets_path if assets_path else "none"}`

- [ ] **Step 1: Write failing test or visual expectation**

```text
Assets in the matrix must exist at their target paths and appear in the platform screenshot.
```

- [ ] **Step 2: Verify it fails or is missing**

Run: `needs repo inspection: asset existence check or platform screenshot command`
Expected: missing assets or screenshot mismatch before preparation.

- [ ] **Step 3: Implement minimal code**

```text
Prepare crop/regenerate/image_asset/icon outputs. For Flutter, register image assets in pubspec.yaml.
```

- [ ] **Step 4: Run platform verification**

Run: `needs repo inspection: platform asset/build check`
Expected: asset registry/build accepts the files.

- [ ] **Step 5: Capture visual evidence if UI changed**

Run: `needs repo inspection: platform screenshot command`
Expected: assets are visible and match the visual contract.

### Task 2: Implement UI Structure

**Files:**
- Create: exact platform UI files after repo inspection
- Modify: existing route/screen/widget files after repo inspection
- Test: exact platform test files after repo inspection
- Visual artifact: `{baseline if baseline else "none"}`
- Asset artifact: `{assets_path if assets_path else "none"}`

- [ ] **Step 1: Write failing test or visual expectation**

```text
The screen structure, safe areas, typography, spacing, and states must match the visual contract.
```

- [ ] **Step 2: Verify it fails or is missing**

Run: `needs repo inspection: platform test or screenshot command`
Expected: screen is absent or visual comparison fails before implementation.

- [ ] **Step 3: Implement minimal code**

```text
Implement the screen using existing project patterns and the prepared assets.
```

- [ ] **Step 4: Run platform verification**

Run: `needs repo inspection: platform build/test command`
Expected: tests/build pass.

- [ ] **Step 5: Capture visual evidence if UI changed**

Run: `needs repo inspection: platform screenshot/golden command`
Expected: screenshot is saved and compared against the HTML baseline.

## Platform Verification Matrix

| Platform | Fast check | Visual check | Final check |
|---|---|---|---|
| Flutter | `flutter test` if available | `flutter build web` + screenshot or golden | target simulator/emulator screenshot |
| Android | Gradle test/build if available | emulator screenshot via `adb exec-out screencap -p` | release/debug APK smoke test |
| iOS | XCTest/build if available | simulator screenshot via `xcrun simctl io booted screenshot` | target simulator smoke test |
| React Native | unit/e2e command if available | Detox/Maestro/Appium screenshot | platform emulator/simulator smoke test |
| mobile web | browser tests if available | mobile viewport screenshot | responsive/accessibility check |

## Self-Review

- [ ] Every approved requirement maps to a task.
- [ ] Every asset is classified and has a target path or explicit follow-up.
- [ ] Visual contract differences are mapped to implementation or verification.
- [ ] Platform commands are real for this repo or marked for confirmation.
- [ ] No unresolved `review_placeholder` assets remain before UI implementation.
"""


def create_plan_scaffold(
    *,
    project_dir: Path | str,
    feature: str,
    platform: str,
    spec: str,
    visual_contract: Path | str | None = None,
    assets: Path | str | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    visual_contract_path = Path(visual_contract).expanduser().resolve() if visual_contract else None
    assets_path = Path(assets).expanduser().resolve() if assets else None
    errors: list[str] = []
    if visual_contract_path and not visual_contract_path.exists():
        errors.append(f"visual contract not found: {visual_contract_path}")
    if assets_path and not assets_path.exists():
        errors.append(f"assets manifest not found: {assets_path}")
    day = date or date_type.today().isoformat()
    plan_dir = project_dir / "docs" / "mobile-superpowers" / "plans"
    plan_path = plan_dir / f"{day}-{slugify(feature)}.md"
    result = {"plan": str(plan_path), "validation": {"errors": errors, "warnings": []}}
    if errors:
        return result
    loaded_assets = read_assets(assets_path)
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        plan_markdown(
            feature=feature,
            platform=platform,
            spec=spec,
            visual_contract=visual_contract_path,
            assets_path=assets_path,
            assets=loaded_assets,
        ),
        encoding="utf-8",
    )
    return {**result, "asset_count": len(loaded_assets)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a mobile implementation plan scaffold.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--feature", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--visual-contract", type=Path, default=None)
    parser.add_argument("--assets", type=Path, default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = create_plan_scaffold(
        project_dir=args.project_dir,
        feature=args.feature,
        platform=args.platform,
        spec=args.spec,
        visual_contract=args.visual_contract,
        assets=args.assets,
        date=args.date,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["plan"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
