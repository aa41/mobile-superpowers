#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from functools import partial
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mobile_ui_verification_report import create_verification_report
from mobile_visual_compare import compare_visuals
from mobile_visual_screenshot import (
    DEFAULT_HEIGHT,
    DEFAULT_TIMEOUT,
    DEFAULT_WIDTH,
    browser_exists,
    discover_browser,
)


Runner = Callable[..., subprocess.CompletedProcess]


def build_url_screenshot_command(
    *,
    browser_cmd: str,
    url: str,
    screenshot_path: Path,
    width: int,
    height: int,
) -> list[str]:
    return [
        browser_cmd,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={width},{height}",
        f"--screenshot={screenshot_path}",
        url,
    ]


def capture_url_screenshot(
    *,
    url: str,
    screenshot_path: Path | str,
    browser_cmd: str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    timeout: int = DEFAULT_TIMEOUT,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    screenshot_path = Path(screenshot_path).expanduser().resolve()
    browser_cmd = browser_cmd or discover_browser()
    errors: list[str] = []
    if not browser_cmd or not browser_exists(browser_cmd):
        errors.append(f"browser not found: {browser_cmd or 'none'}")
    command = build_url_screenshot_command(
        browser_cmd=browser_cmd or "",
        url=url,
        screenshot_path=screenshot_path,
        width=width,
        height=height,
    )
    result = {
        "url": url,
        "screenshot": str(screenshot_path),
        "browser": browser_cmd,
        "viewport": {"width": width, "height": height},
        "command": command,
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    completed = runner(command, timeout=timeout)
    if completed.returncode != 0:
        result["validation"]["errors"].append(f"browser exited with code {completed.returncode}")
    elif not screenshot_path.exists():
        result["validation"]["errors"].append(f"screenshot was not created: {screenshot_path}")
    return result


def start_static_server(*, directory: Path, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(directory),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_process(process: subprocess.Popen | None) -> None:
    if not process:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def default_out_dir(project_dir: Path, target: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in target).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return project_dir / "docs" / "mobile-superpowers" / "verification" / (slug or "flutter-web")


def verify_flutter_web(
    *,
    project_dir: Path | str,
    target: str,
    visual_contract: Path | str,
    baseline_screenshot: Path | str,
    assets: Path | str | None = None,
    plan: Path | str | None = None,
    out_dir: Path | str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    port: int = 8765,
    execute: bool = False,
    dry_run: bool = False,
    runner: Runner = subprocess.run,
    server_factory=start_static_server,
    capture=capture_url_screenshot,
    compare=compare_visuals,
    report=create_verification_report,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    visual_contract = Path(visual_contract).expanduser().resolve()
    baseline_screenshot = Path(baseline_screenshot).expanduser().resolve()
    assets_path = Path(assets).expanduser().resolve() if assets else None
    plan_path = Path(plan).expanduser().resolve() if plan else None
    out_dir = Path(out_dir).expanduser().resolve() if out_dir else default_out_dir(project_dir, target)
    build_dir = project_dir / "build" / "web"
    platform_screenshot = out_dir / "platform-screenshot.png"
    metrics_path = out_dir / "platform-metrics.json"
    report_path = out_dir / "verification-report.md"
    url = f"http://127.0.0.1:{port}/"
    commands = [["flutter", "build", "web"]]

    errors: list[str] = []
    for label, path in {
        "project dir": project_dir,
        "visual contract": visual_contract,
        "baseline screenshot": baseline_screenshot,
        "assets": assets_path,
        "plan": plan_path,
    }.items():
        if path and not path.exists():
            errors.append(f"{label} not found: {path}")
    if execute and not shutil.which("flutter"):
        errors.append("flutter command not found")

    result: dict[str, Any] = {
        "dry_run": dry_run or not execute,
        "project_dir": str(project_dir),
        "target": target,
        "platform": "Flutter Web",
        "build_dir": str(build_dir),
        "url": url,
        "out_dir": str(out_dir),
        "platform_screenshot": str(platform_screenshot),
        "metrics": str(metrics_path),
        "report": str(report_path),
        "commands": commands,
        "validation": {"errors": errors, "warnings": []},
    }
    if dry_run or not execute or errors:
        return result

    out_dir.mkdir(parents=True, exist_ok=True)
    build = runner(["flutter", "build", "web"], cwd=str(project_dir), timeout=600)
    if build.returncode != 0:
        result["validation"]["errors"].append(f"flutter build web exited with code {build.returncode}")
        return result
    if not (build_dir / "index.html").exists():
        result["validation"]["errors"].append(f"Flutter web build did not create index.html: {build_dir / 'index.html'}")
        return result

    server = None
    try:
        server = server_factory(directory=build_dir, port=port)
        time.sleep(1)
        capture_result = capture(
            url=url,
            screenshot_path=platform_screenshot,
            width=width,
            height=height,
        )
        result["capture"] = capture_result
        result["validation"]["errors"].extend(capture_result.get("validation", {}).get("errors", []))
        if result["validation"]["errors"]:
            return result
        compare_result = compare(
            reference=baseline_screenshot,
            candidate=platform_screenshot,
            out_dir=out_dir,
            prefix="platform",
        )
        result["compare"] = compare_result
        result["validation"]["errors"].extend(compare_result.get("validation", {}).get("errors", []))
        if result["validation"]["errors"]:
            return result
        report_result = report(
            out_dir=out_dir,
            target=target,
            platform="Flutter Web",
            plan=plan_path,
            visual_contract=visual_contract,
            baseline_screenshot=baseline_screenshot,
            platform_screenshot=platform_screenshot,
            metrics=metrics_path,
            assets=assets_path,
            command=["flutter build web", f"serve {build_dir} at {url}", "capture Flutter Web screenshot", "compare baseline vs Flutter Web screenshot"],
            environment=[f"viewport {width}x{height}", f"local web server {url}"],
        )
        result["assessment"] = report_result.get("assessment")
        result["report"] = report_result.get("report", str(report_path))
        result["validation"]["errors"].extend(report_result.get("validation", {}).get("errors", []))
        return result
    finally:
        stop_process(server)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Flutter Web against a Mobile Superpowers HTML baseline.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--target", required=True)
    parser.add_argument("--visual-contract", type=Path, required=True)
    parser.add_argument("--baseline-screenshot", type=Path, required=True)
    parser.add_argument("--assets", type=Path, default=None)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_flutter_web(
        project_dir=args.project_dir,
        target=args.target,
        visual_contract=args.visual_contract,
        baseline_screenshot=args.baseline_screenshot,
        assets=args.assets,
        plan=args.plan,
        out_dir=args.out_dir,
        width=args.width,
        height=args.height,
        port=args.port,
        execute=args.execute,
        dry_run=args.dry_run,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["platform_screenshot"])
        print(result["metrics"])
        print(result["report"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
