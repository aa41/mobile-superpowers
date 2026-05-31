#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def read_metadata(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"metadata must be a JSON object: {path}")
    return data


def html_scaffold(metadata: dict[str, Any]) -> str:
    request = metadata.get("request", {})
    provider = metadata.get("provider", {})
    prompt = html.escape(str(request.get("prompt", "")))
    provider_name = html.escape(str(provider.get("name", "")))
    model = html.escape(str(provider.get("model", "")))
    size = html.escape(str(request.get("size", "")))
    aspect_ratio = html.escape(str(request.get("aspect_ratio", "")))

    return f"""<!doctype html>
<html lang="en" data-mobile-superpowers-baseline>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Mobile Visual Baseline</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #0f172a;
      color: #111827;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #111827;
    }}
    .device {{
      width: min(390px, 100vw);
      min-height: min(844px, 100vh);
      background: #f8fafc;
      padding: max(20px, env(safe-area-inset-top)) 20px max(20px, env(safe-area-inset-bottom));
    }}
    .status {{
      height: 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      font-weight: 600;
      color: #111827;
    }}
    .content {{
      margin-top: 24px;
      display: grid;
      gap: 16px;
    }}
    .placeholder {{
      border: 1px dashed #94a3b8;
      border-radius: 8px;
      padding: 16px;
      background: #ffffff;
    }}
    .label {{
      color: #475569;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    h1 {{
      margin: 8px 0 0;
      font-size: 24px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    p {{
      margin: 8px 0 0;
      line-height: 1.45;
      color: #334155;
    }}
  </style>
</head>
<body>
  <main class="device" aria-label="Mobile visual baseline">
    <div class="status" aria-hidden="true">
      <span>9:41</span>
      <span>LTE 100%</span>
    </div>
    <section class="content">
      <div class="placeholder">
        <div class="label">Provider</div>
        <h1>{provider_name} {model}</h1>
        <p>Requested size: {size}; aspect ratio: {aspect_ratio}</p>
      </div>
      <div class="placeholder">
        <div class="label">Visual Prompt</div>
        <p>{prompt}</p>
      </div>
    </section>
  </main>
</body>
</html>
"""


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


def update_visual_contract(*, contract_path: Path, baseline_html: Path, metadata_path: Path) -> None:
    if not contract_path.exists():
        return
    text = contract_path.read_text(encoding="utf-8")
    updated = replace_section(
        text,
        "HTML Baseline",
        [
            f"- Baseline HTML: `{baseline_html}`",
            f"- Source metadata: `{metadata_path}`",
            "- Screenshot status: not captured yet.",
            "- Similarity metrics status: not captured yet.",
        ],
    )
    contract_path.write_text(updated, encoding="utf-8")


def create_baseline(*, metadata_path: Path | str, force: bool = False) -> dict[str, Any]:
    metadata_path = Path(metadata_path).expanduser().resolve()
    metadata = read_metadata(metadata_path)
    workspace = Path(str(metadata.get("workspace", metadata_path.parent))).expanduser().resolve()
    baseline_html = workspace / "baseline.html"
    contract_path = workspace / "visual-contract.md"

    errors = list(metadata.get("validation", {}).get("errors", []))
    if force or not baseline_html.exists():
        baseline_html.write_text(html_scaffold(metadata), encoding="utf-8")

    update_visual_contract(contract_path=contract_path, baseline_html=baseline_html, metadata_path=metadata_path)

    return {
        "workspace": str(workspace),
        "baseline_html": str(baseline_html),
        "visual_contract": str(contract_path),
        "metadata": str(metadata_path),
        "validation": {
            "errors": errors,
            "warnings": list(metadata.get("validation", {}).get("warnings", [])),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an HTML baseline scaffold from provider metadata.")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = create_baseline(metadata_path=args.metadata, force=args.force)
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["baseline_html"])
        print(result["visual_contract"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
