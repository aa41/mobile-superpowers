#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mobile_visual_config import resolve_config, resolve_secret_value


DEFAULT_VISION_MODEL = "gpt-5.5"


def read_metadata(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"metadata must be a JSON object: {path}")
    return data


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


def read_compact_constraints(path: Path | None, limit: int = 6000) -> str:
    if not path:
        return "none"
    if not path.exists():
        return f"missing: {path}"
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n...[truncated: read the source file for complete constraints]"


def reconstruction_prompt(
    *,
    metadata: dict[str, Any],
    mockup_path: Path,
    baseline_path: Path,
    project_constraints: Path | None = None,
) -> str:
    request = metadata.get("request", {})
    prompt = request.get("prompt", "")
    size = request.get("size", "")
    aspect_ratio = request.get("aspect_ratio", "")
    constraints_text = read_compact_constraints(project_constraints)
    return f"""# Mobile HTML Reconstruction Prompt

## Source

- Mockup image: `{mockup_path}`
- Target HTML: `{baseline_path}`
- Original visual prompt: {prompt}
- Requested size: `{size}`
- Aspect ratio: `{aspect_ratio}`
- Project constraints: `{project_constraints if project_constraints else "none"}`

## Project Constraints

{constraints_text}

## Task

Reconstruct the mobile mockup as a single self-contained `baseline.html` file.

Code these elements with HTML/CSS:

- Layout, spacing, cards, buttons, input fields, bottom bars, and readable text.
- Simple icons that can be represented with CSS, inline SVG, or text-safe placeholders.
- Typography hierarchy, line-height, text block width, and mobile safe area behavior.
- Semantic placeholders for required platform components. Use `data-platform-component="CommonText"` for text mapped to project text components, `data-platform-component="CommonButton"` for action controls, and `data-platform-component="CommonDialog"` for modal/dialog surfaces when the project contract requires them.

Treat these as assets instead of forcing CSS:

- Brand marks, complex illustrations, heavy texture, glass effects, dense charts, product imagery, and decorative art.
- If an asset is needed, add a clearly named placeholder block and record the expected crop or regenerated asset in the visual contract.

Mobile constraints:

- Preserve mobile safe area with `viewport-fit=cover`.
- Use a fixed design frame close to 390x844 unless the mockup strongly implies another phone size.
- Keep text inside containers.
- Avoid nested cards.
- Keep border radius 8px or less unless the mockup clearly uses another radius.
- Do not use viewport-scaled font sizes.
- Set letter spacing to `0` unless the reference visibly requires tracking.

Verification loop:

1. Screenshot `baseline.html` at mobile viewport.
2. Compare screenshot against the mockup with `mobile_visual_compare.py`.
3. Iterate layout, typography, colors, and assets until differences are understood.
"""


def baseline_reconstruction_html(*, metadata: dict[str, Any], mockup_path: Path) -> str:
    request = metadata.get("request", {})
    prompt = html.escape(str(request.get("prompt", "")))
    mockup_uri = mockup_path.resolve().as_uri()
    return f"""<!doctype html>
<html lang="en" data-mobile-superpowers-reconstruction>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Mobile Reconstruction Baseline</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #111827;
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
    .phone {{
      width: min(390px, 100vw);
      min-height: min(844px, 100vh);
      padding: max(18px, env(safe-area-inset-top)) 18px max(18px, env(safe-area-inset-bottom));
      background: #f8fafc;
      overflow: hidden;
    }}
    .status {{
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0;
    }}
    .notice {{
      margin-top: 20px;
      padding: 14px;
      border: 1px dashed #94a3b8;
      border-radius: 8px;
      background: #ffffff;
    }}
    .notice h1 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.25;
      letter-spacing: 0;
    }}
    .notice p {{
      margin: 8px 0 0;
      color: #475569;
      font-size: 14px;
      line-height: 1.45;
      letter-spacing: 0;
    }}
    .mockup {{
      margin-top: 16px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #cbd5e1;
      background: #e2e8f0;
    }}
    .mockup img {{
      display: block;
      width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <main class="phone" aria-label="Generated mockup reconstruction baseline">
    <div class="status" aria-hidden="true">
      <span>9:41</span>
      <span>LTE 100%</span>
    </div>
    <section class="notice">
      <h1>Generated mockup reconstruction</h1>
      <p>{prompt}</p>
    </section>
    <section class="mockup" aria-label="Generated mockup reference">
      <img src="{mockup_uri}" alt="Generated mockup reference">
    </section>
  </main>
</body>
</html>
"""


def update_visual_contract(
    *,
    contract_path: Path,
    baseline_path: Path,
    prompt_path: Path,
    mockup_path: Path,
    project_constraints: Path | None = None,
) -> None:
    if not contract_path.exists():
        return
    text = contract_path.read_text(encoding="utf-8")
    updated = replace_section(
        text,
        "HTML Baseline",
        [
            f"- Baseline HTML: `{baseline_path}`",
            f"- Reconstruction prompt: `{prompt_path}`",
            f"- Generated mockup: `{mockup_path}`",
            f"- Project constraints: `{project_constraints if project_constraints else 'none'}`",
            "- Screenshot status: not captured after reconstruction yet.",
            "- Similarity metrics status: not captured after reconstruction yet.",
        ],
    )
    updated = replace_section(
        updated,
        "Project Constraints",
        [
            f"- Project constraints: `{project_constraints if project_constraints else 'none'}`",
            "- HTML reconstruction must preserve project component semantics with `data-platform-component` attributes when constraints require base components.",
        ],
    )
    contract_path.write_text(updated, encoding="utf-8")


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def build_vision_chat_payload(*, prompt_path: Path, mockup_path: Path, model: str = DEFAULT_VISION_MODEL) -> dict[str, Any]:
    prompt = prompt_path.read_text(encoding="utf-8")
    return {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url(mockup_path)}},
                ],
            }
        ],
        "temperature": 0.1,
    }


def chat_completions_transport(url: str, *, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
    return ""


def extract_html(text: str) -> str:
    stripped = text.strip()
    if "```" not in stripped:
        return stripped
    parts = stripped.split("```")
    for part in parts:
        candidate = part.strip()
        if candidate.startswith("html"):
            return candidate[4:].strip()
        if candidate.lower().startswith("<!doctype") or candidate.lower().startswith("<html"):
            return candidate
    return stripped


def execute_vision_reconstruction(
    *,
    prompt_path: Path | str,
    mockup_path: Path | str,
    baseline_path: Path | str,
    base_url: str,
    api_key: str,
    model: str = DEFAULT_VISION_MODEL,
    timeout: int = 180,
    transport=None,
) -> dict[str, Any]:
    prompt_path = Path(prompt_path).expanduser().resolve()
    mockup_path = Path(mockup_path).expanduser().resolve()
    baseline_path = Path(baseline_path).expanduser().resolve()
    errors: list[str] = []
    if not prompt_path.exists():
        errors.append(f"reconstruction prompt not found: {prompt_path}")
    if not mockup_path.exists():
        errors.append(f"mockup image not found: {mockup_path}")
    if not base_url:
        errors.append("base_url is required for vision reconstruction")
    if not api_key:
        errors.append("api_key is required for vision reconstruction")
    result = {
        "prompt": str(prompt_path),
        "mockup": str(mockup_path),
        "baseline_html": str(baseline_path),
        "provider": {"base_url": base_url, "model": model},
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result

    payload = build_vision_chat_payload(prompt_path=prompt_path, mockup_path=mockup_path, model=model)
    selected_transport = transport or chat_completions_transport
    try:
        response = selected_transport(
            f"{base_url.rstrip('/')}/chat/completions",
            payload=payload,
            api_key=api_key,
            timeout=timeout,
        )
    except urllib.error.HTTPError as error:
        try:
            body = error.read().decode("utf-8", errors="replace") if error.fp else ""
        finally:
            error.close()
        result["validation"]["errors"].append(
            f"vision provider HTTP {error.code}: {error.reason}" + (f" - {body}" if body else "")
        )
        return result
    except urllib.error.URLError as error:
        result["validation"]["errors"].append(f"vision provider URL error: {error.reason}")
        return result
    choices = response.get("choices") or []
    if not choices:
        result["validation"]["errors"].append("vision provider returned no choices")
        return result
    content = normalize_message_content(choices[0].get("message", {}).get("content", ""))
    html_output = extract_html(content)
    if "<html" not in html_output.lower() and "<!doctype" not in html_output.lower():
        result["validation"]["errors"].append("vision provider response did not contain HTML")
        return result

    baseline_path.write_text(html_output, encoding="utf-8")
    result["provider_response"] = {
        "choices": len(choices),
        "content_length": len(content),
    }
    return result


def create_reconstruction_bundle(
    *,
    metadata_path: Path | str,
    force: bool = False,
    project_constraints: Path | str | None = None,
) -> dict[str, Any]:
    metadata_path = Path(metadata_path).expanduser().resolve()
    metadata = read_metadata(metadata_path)
    workspace = Path(str(metadata.get("workspace", metadata_path.parent))).expanduser().resolve()
    mockup_path = Path(str(metadata.get("outputs", {}).get("image", workspace / "generated-mockup.png"))).expanduser().resolve()
    prompt_path = workspace / "reconstruction-prompt.md"
    baseline_path = workspace / "baseline.html"
    contract_path = workspace / "visual-contract.md"
    project_constraints_path = Path(project_constraints).expanduser().resolve() if project_constraints else None

    errors = list(metadata.get("validation", {}).get("errors", []))
    if not mockup_path.exists():
        errors.append(f"mockup image not found: {mockup_path}")
    if project_constraints_path and not project_constraints_path.exists():
        errors.append(f"project constraints not found: {project_constraints_path}")

    prompt_path.write_text(
        reconstruction_prompt(
            metadata=metadata,
            mockup_path=mockup_path,
            baseline_path=baseline_path,
            project_constraints=project_constraints_path,
        ),
        encoding="utf-8",
    )
    if force or not baseline_path.exists():
        baseline_path.write_text(
            baseline_reconstruction_html(metadata=metadata, mockup_path=mockup_path),
            encoding="utf-8",
        )

    update_visual_contract(
        contract_path=contract_path,
        baseline_path=baseline_path,
        prompt_path=prompt_path,
        mockup_path=mockup_path,
        project_constraints=project_constraints_path,
    )

    return {
        "workspace": str(workspace),
        "mockup": str(mockup_path),
        "prompt": str(prompt_path),
        "baseline_html": str(baseline_path),
        "visual_contract": str(contract_path),
        "project_constraints": str(project_constraints_path) if project_constraints_path else None,
        "validation": {"errors": errors, "warnings": list(metadata.get("validation", {}).get("warnings", []))},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a mockup-to-HTML reconstruction bundle.")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--project-constraints", type=Path, default=None)
    parser.add_argument("--execute", action="store_true", help="Call the configured vision provider to write baseline.html.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--home-dir", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--vision-model", default=None, help="Chat/vision model for mockup-to-HTML reconstruction.")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = create_reconstruction_bundle(
        metadata_path=args.metadata,
        force=args.force,
        project_constraints=args.project_constraints,
    )
    if args.execute and not result["validation"]["errors"]:
        config = resolve_config(project_dir=args.project_dir, home_dir=args.home_dir, config_path=args.config)
        api_key = resolve_secret_value(
            config["provider"]["api_key_source"],
            project_dir=args.project_dir,
            home_dir=args.home_dir,
            config_path=args.config,
        )
        execution = execute_vision_reconstruction(
            prompt_path=result["prompt"],
            mockup_path=result["mockup"],
            baseline_path=result["baseline_html"],
            base_url=config["provider"]["base_url"],
            api_key=api_key,
            model=args.vision_model or str(config["visual"].get("vision_model") or DEFAULT_VISION_MODEL),
            timeout=int(config["visual"].get("timeout_seconds") or 180),
        )
        result["vision_execution"] = execution
        result["validation"]["errors"].extend(execution["validation"]["errors"])
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["prompt"])
        print(result["baseline_html"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
