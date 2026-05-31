#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


def replace_section(text: str, section: str, replacement_lines: list[str]) -> str:
    marker = f"## {section}"
    start = text.find(marker)
    if start == -1:
        return text.rstrip() + "\n\n" + marker + "\n\n" + "\n".join(replacement_lines) + "\n"
    next_start = text.find("\n## ", start + len(marker))
    replacement = marker + "\n\n" + "\n".join(replacement_lines) + "\n"
    if next_start == -1:
        return text[:start] + replacement
    return text[:start] + replacement + text[next_start:]


class AssetHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[dict[str, str]] = []
        self._placeholder_depth = 0
        self._placeholder_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {name: value or "" for name, value in attrs}
        if tag == "img":
            self.assets.append(
                {
                    "name": asset_name(attr.get("alt") or attr.get("class") or attr.get("src") or "image"),
                    "strategy": "image_asset",
                    "source": attr.get("src", ""),
                    "target_path": "",
                    "dimensions": "",
                    "acceptable_deviation": "preserve crop, aspect ratio, and visual identity",
                    "platform_notes": attr.get("alt", ""),
                }
            )
        strategy = attr.get("data-asset-strategy", "").strip()
        if strategy:
            self.assets.append(
                {
                    "name": asset_name(attr.get("data-asset-name") or strategy),
                    "strategy": strategy,
                    "source": attr.get("data-asset-source", ""),
                    "target_path": attr.get("data-asset-target", ""),
                    "dimensions": attr.get("data-asset-dimensions", ""),
                    "acceptable_deviation": attr.get("data-asset-deviation", "document before platform handoff"),
                    "platform_notes": attr.get("data-asset-notes", ""),
                }
            )
        classes = attr.get("class", "")
        if "placeholder" in classes.split():
            self._placeholder_depth += 1
            self._placeholder_text = []

    def handle_data(self, data: str) -> None:
        if self._placeholder_depth:
            cleaned = " ".join(data.split())
            if cleaned:
                self._placeholder_text.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if self._placeholder_depth:
            self._placeholder_depth -= 1
            if not self._placeholder_depth:
                text = " ".join(self._placeholder_text).strip() or "placeholder"
                self.assets.append(
                    {
                        "name": asset_name(text),
                        "strategy": "review_placeholder",
                        "source": "baseline.html placeholder",
                        "target_path": "",
                        "dimensions": "",
                        "acceptable_deviation": "must be classified as code, crop, regenerate, or image_asset",
                        "platform_notes": text,
                    }
                )


def asset_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "asset"


def dedupe_assets(assets: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    result: list[dict[str, str]] = []
    for asset in assets:
        key = (asset.get("name", ""), asset.get("strategy", ""), asset.get("source", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(asset)
    return result


def parse_assets(html_text: str) -> list[dict[str, str]]:
    parser = AssetHTMLParser()
    parser.feed(html_text)
    return dedupe_assets(parser.assets)


def update_visual_contract(*, contract_path: Path, assets_path: Path, assets: list[dict[str, str]]) -> None:
    if not contract_path.exists():
        return
    lines = [
        f"- Asset manifest: `{assets_path}`",
        "- Use `code` for layout primitives, cards, buttons, simple dividers, simple backgrounds, and text.",
        "- Use `icon` for platform/system icons or simple SVG/lucide-style pictograms.",
        "- Use `image_asset` for photos, avatars, product imagery, brand marks, complex illustrations, textures, glass effects, and dense charts.",
        "- Use `crop` when the asset should be cut from the reference or generated mockup.",
        "- Use `regenerate` when the asset should be recreated by an image model before platform implementation.",
        "",
        "| Asset | Strategy | Source | Target Path | Dimensions | Notes |",
        "|---|---|---|---|---|---|",
    ]
    if assets:
        for asset in assets:
            lines.append(
                "| {name} | {strategy} | {source} | {target_path} | {dimensions} | {notes} |".format(
                    name=asset.get("name", ""),
                    strategy=asset.get("strategy", ""),
                    source=asset.get("source", ""),
                    target_path=asset.get("target_path", ""),
                    dimensions=asset.get("dimensions", ""),
                    notes=asset.get("platform_notes", "") or asset.get("acceptable_deviation", ""),
                )
            )
    else:
        lines.append("| None detected. |  |  |  |  |  |")
    text = contract_path.read_text(encoding="utf-8")
    contract_path.write_text(replace_section(text, "Asset Strategy", lines), encoding="utf-8")


def analyze_assets(*, baseline: Path | str, out_dir: Path | str | None = None) -> dict[str, Any]:
    baseline = Path(baseline).expanduser().resolve()
    workspace = Path(out_dir).expanduser().resolve() if out_dir else baseline.parent
    assets_path = workspace / "assets.json"
    contract_path = workspace / "visual-contract.md"

    errors: list[str] = []
    if not baseline.exists():
        errors.append(f"baseline html not found: {baseline}")

    result = {
        "baseline_html": str(baseline),
        "assets": str(assets_path),
        "visual_contract": str(contract_path),
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result

    assets = parse_assets(baseline.read_text(encoding="utf-8"))
    workspace.mkdir(parents=True, exist_ok=True)
    assets_path.write_text(
        json.dumps({"baseline_html": str(baseline), "assets": assets}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    update_visual_contract(contract_path=contract_path, assets_path=assets_path, assets=assets)
    return {**result, "asset_count": len(assets)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze baseline HTML assets and update visual contract.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze_assets(baseline=args.baseline, out_dir=args.out_dir)
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["assets"])
        print(result["visual_contract"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
