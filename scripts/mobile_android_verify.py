#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mobile_ui_verification_report import create_verification_report
from mobile_visual_compare import compare_visuals


Runner = Callable[..., subprocess.CompletedProcess]


def default_out_dir(project_dir: Path, target: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in target).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return project_dir / "docs" / "mobile-superpowers" / "verification" / (slug or "android")


def split_command(command: str | None) -> list[str]:
    return shlex.split(command) if command else []


def default_adb_available() -> bool:
    return shutil.which("adb") is not None


def verify_android(
    *,
    project_dir: Path | str,
    target: str,
    visual_contract: Path | str,
    baseline_screenshot: Path | str,
    assets: Path | str | None = None,
    plan: Path | str | None = None,
    apk: Path | str | None = None,
    launch_activity: str | None = None,
    build_command: str | None = None,
    out_dir: Path | str | None = None,
    wait_seconds: float = 2.0,
    execute: bool = False,
    dry_run: bool = False,
    runner: Runner = subprocess.run,
    compare=compare_visuals,
    report=create_verification_report,
    adb_available=default_adb_available,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    visual_contract = Path(visual_contract).expanduser().resolve()
    baseline_screenshot = Path(baseline_screenshot).expanduser().resolve()
    assets_path = Path(assets).expanduser().resolve() if assets else None
    plan_path = Path(plan).expanduser().resolve() if plan else None
    apk_path = Path(apk).expanduser().resolve() if apk else None
    out_dir = Path(out_dir).expanduser().resolve() if out_dir else default_out_dir(project_dir, target)
    platform_screenshot = out_dir / "platform-screenshot.png"
    metrics_path = out_dir / "platform-metrics.json"
    report_path = out_dir / "verification-report.md"

    build_cmd = split_command(build_command)
    commands: list[list[str]] = []
    if build_cmd:
        commands.append(build_cmd)
    if apk_path:
        commands.append(["adb", "install", "-r", str(apk_path)])
    if launch_activity:
        commands.append(["adb", "shell", "am", "start", "-n", launch_activity])
    commands.append(["adb", "exec-out", "screencap", "-p"])

    errors: list[str] = []
    for label, path in {
        "project dir": project_dir,
        "visual contract": visual_contract,
        "baseline screenshot": baseline_screenshot,
        "assets": assets_path,
        "plan": plan_path,
        "apk": apk_path,
    }.items():
        if path and not path.exists():
            errors.append(f"{label} not found: {path}")
    if execute and not adb_available():
        errors.append("adb command not found")

    result: dict[str, Any] = {
        "dry_run": dry_run or not execute,
        "project_dir": str(project_dir),
        "target": target,
        "platform": "Android",
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
    if build_cmd:
        build = runner(build_cmd, cwd=str(project_dir), timeout=900)
        if build.returncode != 0:
            result["validation"]["errors"].append(f"build command exited with code {build.returncode}")
            return result
    if apk_path:
        install = runner(["adb", "install", "-r", str(apk_path)], timeout=300)
        if install.returncode != 0:
            result["validation"]["errors"].append(f"adb install exited with code {install.returncode}")
            return result
    if launch_activity:
        launch = runner(["adb", "shell", "am", "start", "-n", launch_activity], timeout=60)
        if launch.returncode != 0:
            result["validation"]["errors"].append(f"adb launch exited with code {launch.returncode}")
            return result
        time.sleep(wait_seconds)
    screenshot = runner(["adb", "exec-out", "screencap", "-p"], timeout=60, stdout=subprocess.PIPE)
    if screenshot.returncode != 0:
        result["validation"]["errors"].append(f"adb screencap exited with code {screenshot.returncode}")
        return result
    platform_screenshot.write_bytes(screenshot.stdout or b"")
    if not platform_screenshot.exists() or platform_screenshot.stat().st_size == 0:
        result["validation"]["errors"].append(f"android screenshot was not created: {platform_screenshot}")
        return result

    compare_result = compare(
        reference=baseline_screenshot,
        candidate=platform_screenshot,
        out_dir=out_dir,
        prefix="platform",
    )
    result["compare"] = compare_result
    metrics_path = Path(compare_result.get("metrics", metrics_path)).expanduser().resolve()
    result["metrics"] = str(metrics_path)
    result["validation"]["errors"].extend(compare_result.get("validation", {}).get("errors", []))
    if result["validation"]["errors"]:
        return result
    report_result = report(
        out_dir=out_dir,
        target=target,
        platform="Android",
        plan=plan_path,
        visual_contract=visual_contract,
        baseline_screenshot=baseline_screenshot,
        platform_screenshot=platform_screenshot,
        metrics=metrics_path,
        assets=assets_path,
        command=[" ".join(command) for command in commands],
        environment=["Android device/emulator via adb", "record device, density, font scale, theme, orientation before accepting"],
    )
    result["assessment"] = report_result.get("assessment")
    result["report"] = report_result.get("report", str(report_path))
    result["validation"]["errors"].extend(report_result.get("validation", {}).get("errors", []))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Android UI against a Mobile Superpowers HTML baseline.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--target", required=True)
    parser.add_argument("--visual-contract", type=Path, required=True)
    parser.add_argument("--baseline-screenshot", type=Path, required=True)
    parser.add_argument("--assets", type=Path, default=None)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--apk", type=Path, default=None)
    parser.add_argument("--launch-activity", default=None)
    parser.add_argument("--build-command", default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--wait-seconds", type=float, default=2.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_android(
        project_dir=args.project_dir,
        target=args.target,
        visual_contract=args.visual_contract,
        baseline_screenshot=args.baseline_screenshot,
        assets=args.assets,
        plan=args.plan,
        apk=args.apk,
        launch_activity=args.launch_activity,
        build_command=args.build_command,
        out_dir=args.out_dir,
        wait_seconds=args.wait_seconds,
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
