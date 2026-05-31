#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable


DEFAULT_WIDTH = 390
DEFAULT_HEIGHT = 844
DEFAULT_TIMEOUT = 30
DEFAULT_VIRTUAL_TIME_BUDGET = 12000
MAC_BROWSER_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
BROWSER_NAMES = ["chromium", "chromium-browser", "google-chrome", "microsoft-edge", "msedge"]


def browser_exists(browser_cmd: str) -> bool:
    if "/" in browser_cmd:
        return Path(browser_cmd).exists()
    return shutil.which(browser_cmd) is not None


def discover_browser(env: dict[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    configured = env.get("MOBILE_VISUAL_BROWSER_CMD", "").strip()
    if configured:
        return configured
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    for path in MAC_BROWSER_PATHS:
        if Path(path).exists():
            return path
    return ""


def build_browser_command(
    *,
    browser_cmd: str,
    baseline_html: Path,
    screenshot_path: Path,
    width: int,
    height: int,
    virtual_time_budget: int = DEFAULT_VIRTUAL_TIME_BUDGET,
) -> list[str]:
    command = [
        browser_cmd,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={width},{height}",
    ]
    if virtual_time_budget > 0:
        command.append(f"--virtual-time-budget={virtual_time_budget}")
    command.extend([f"--screenshot={screenshot_path}", baseline_html.resolve().as_uri()])
    return command


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


def update_visual_contract(
    *,
    contract_path: Path,
    baseline_html: Path,
    screenshot_path: Path,
    metadata_path: Path,
    width: int,
    height: int,
) -> None:
    if not contract_path.exists():
        return
    text = contract_path.read_text(encoding="utf-8")
    updated = replace_section(
        text,
        "Screenshot And Metrics",
        [
            f"- Baseline HTML: `{baseline_html}`",
            f"- Baseline screenshot: `{screenshot_path}`",
            f"- Screenshot metadata: `{metadata_path}`",
            f"- Viewport: `{width}x{height}`",
            "- Similarity metrics status: not captured yet.",
        ],
    )
    contract_path.write_text(updated, encoding="utf-8")


def capture_screenshot(
    *,
    baseline_html: Path | str,
    screenshot_path: Path | str | None = None,
    browser_cmd: str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    timeout: int = DEFAULT_TIMEOUT,
    virtual_time_budget: int = DEFAULT_VIRTUAL_TIME_BUDGET,
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, Any]:
    baseline_html = Path(baseline_html).expanduser().resolve()
    workspace = baseline_html.parent
    screenshot_path = Path(screenshot_path).expanduser().resolve() if screenshot_path else workspace / "baseline-screenshot.png"
    metadata_path = screenshot_path.with_suffix(".json")
    contract_path = workspace / "visual-contract.md"
    browser_cmd = browser_cmd or discover_browser()

    errors: list[str] = []
    if not baseline_html.exists():
        errors.append(f"baseline html not found: {baseline_html}")
    if not browser_cmd or not browser_exists(browser_cmd):
        errors.append(f"browser not found: {browser_cmd or 'none'}")

    command = build_browser_command(
        browser_cmd=browser_cmd or "",
        baseline_html=baseline_html,
        screenshot_path=screenshot_path,
        width=width,
        height=height,
        virtual_time_budget=virtual_time_budget,
    )

    result: dict[str, Any] = {
        "dry_run": dry_run,
        "baseline_html": str(baseline_html),
        "screenshot": str(screenshot_path),
        "metadata": str(metadata_path),
        "visual_contract": str(contract_path),
        "browser": browser_cmd,
        "viewport": {"width": width, "height": height},
        "virtual_time_budget": virtual_time_budget,
        "command": command,
        "validation": {"errors": errors, "warnings": []},
    }

    if dry_run or errors:
        return result

    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    completed = runner(command, timeout=timeout)
    if completed.returncode != 0:
        result["validation"]["errors"].append(f"browser exited with code {completed.returncode}")
        return result
    if not screenshot_path.exists():
        result["validation"]["errors"].append(f"screenshot was not created: {screenshot_path}")
        return result

    metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    update_visual_contract(
        contract_path=contract_path,
        baseline_html=baseline_html,
        screenshot_path=screenshot_path,
        metadata_path=metadata_path,
        width=width,
        height=height,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a mobile viewport screenshot for baseline.html.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--browser", default=None)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--virtual-time-budget", type=int, default=DEFAULT_VIRTUAL_TIME_BUDGET)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = capture_screenshot(
        baseline_html=args.baseline,
        screenshot_path=args.output,
        browser_cmd=args.browser,
        width=args.width,
        height=args.height,
        timeout=args.timeout,
        virtual_time_budget=args.virtual_time_budget,
        dry_run=args.dry_run,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["screenshot"])
        print(result["metadata"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
