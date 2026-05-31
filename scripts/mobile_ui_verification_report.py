#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ASSESSMENTS = {"VERIFIED", "VERIFIED_WITH_DEVIATIONS", "NOT_VERIFIED", "BLOCKED"}


def read_json(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def path_or_none(path: Path | None) -> str:
    return str(path) if path else "none"


def validate_inputs(paths: dict[str, Path | None]) -> list[str]:
    errors: list[str] = []
    for label, path in paths.items():
        if path and not path.exists():
            errors.append(f"{label} not found: {path}")
    return errors


def assessment_for(*, errors: list[str], metrics: dict[str, Any], platform_screenshot: Path | None) -> str:
    if errors:
        return "NOT_VERIFIED"
    if not platform_screenshot:
        return "NOT_VERIFIED"
    regions = metrics.get("regions", []) if metrics else []
    if regions:
        primary = regions[0]
        if float(primary.get("rms_diff", 0) or 0) == 0 and float(primary.get("mean_abs_diff", 0) or 0) == 0:
            return "VERIFIED"
        return "VERIFIED_WITH_DEVIATIONS"
    return "VERIFIED_WITH_DEVIATIONS"


def assets_summary(assets_data: dict[str, Any]) -> list[str]:
    assets = assets_data.get("assets", []) if assets_data else []
    if not assets:
        return ["- No assets recorded, or asset manifest is empty."]
    lines = ["| Asset | Strategy | Target Path |", "|---|---|---|"]
    for asset in assets:
        lines.append(
            f"| {asset.get('name', '')} | {asset.get('strategy', '')} | {asset.get('target_path', '')} |"
        )
    return lines


def similarity_summary(metrics_data: dict[str, Any], metrics_path: Path | None) -> list[str]:
    if not metrics_data:
        return ["- Metrics: none"]
    lines = [f"- Metrics: `{metrics_path}`", "", "| Region | RMS diff | Mean abs diff | Diff | Heatmap |", "|---|---:|---:|---|---|"]
    for region in metrics_data.get("regions", []):
        lines.append(
            "| {name} | {rms} | {mean} | `{diff}` | `{heatmap}` |".format(
                name=region.get("name", ""),
                rms=region.get("rms_diff", ""),
                mean=region.get("mean_abs_diff", ""),
                diff=region.get("diff", ""),
                heatmap=region.get("heatmap", ""),
            )
        )
    return lines


def report_markdown(
    *,
    target: str,
    platform: str,
    assessment: str,
    plan: Path | None,
    visual_contract: Path | None,
    baseline_screenshot: Path | None,
    platform_screenshot: Path | None,
    metrics_path: Path | None,
    metrics_data: dict[str, Any],
    assets_path: Path | None,
    assets_data: dict[str, Any],
    commands: list[str],
    environment: list[str],
    errors: list[str],
) -> str:
    command_lines = [f"- `{command}`" for command in commands] or ["- No commands recorded."]
    environment_lines = [f"- {item}" for item in environment] or ["- No environment details recorded."]
    error_lines = [f"- {error}" for error in errors] or ["- None."]
    return "\n".join(
        [
            "# Mobile UI Verification Report",
            "",
            f"Completion Assessment: `{assessment}`",
            "",
            "## Target",
            "",
            f"- Screen/flow: {target}",
            f"- Platform: {platform}",
            f"- Plan: `{path_or_none(plan)}`",
            "",
            "## Commands Run",
            "",
            *command_lines,
            "",
            "## Environment",
            "",
            *environment_lines,
            "",
            "## References",
            "",
            f"- Visual contract: `{path_or_none(visual_contract)}`",
            f"- Asset manifest: `{path_or_none(assets_path)}`",
            "",
            "## Screenshots Captured",
            "",
            f"- HTML baseline screenshot: `{path_or_none(baseline_screenshot)}`",
            f"- Platform screenshot: `{path_or_none(platform_screenshot)}`",
            "",
            "## Similarity Results",
            "",
            *similarity_summary(metrics_data, metrics_path),
            "",
            "## Asset Verification",
            "",
            *assets_summary(assets_data),
            "",
            "## State Coverage",
            "",
            "- Safe area/status/navigation: needs review unless separately documented.",
            "- Loading/empty/error/offline/keyboard/dark mode/dynamic type: needs explicit evidence or non-goal marking.",
            "",
            "## Must-Fix Issues",
            "",
            *error_lines,
            "",
            "## Acceptable Deviations",
            "",
            "- Review visual contract and similarity regions before accepting deviations.",
            "",
            "## Completion Assessment",
            "",
            f"`{assessment}`",
            "",
        ]
    )


def create_verification_report(
    *,
    out_dir: Path | str,
    target: str,
    platform: str,
    plan: Path | str | None = None,
    visual_contract: Path | str | None = None,
    baseline_screenshot: Path | str | None = None,
    platform_screenshot: Path | str | None = None,
    metrics: Path | str | None = None,
    assets: Path | str | None = None,
    command: list[str] | None = None,
    environment: list[str] | None = None,
) -> dict[str, Any]:
    out_dir = Path(out_dir).expanduser().resolve()
    plan_path = Path(plan).expanduser().resolve() if plan else None
    contract_path = Path(visual_contract).expanduser().resolve() if visual_contract else None
    baseline_path = Path(baseline_screenshot).expanduser().resolve() if baseline_screenshot else None
    platform_path = Path(platform_screenshot).expanduser().resolve() if platform_screenshot else None
    metrics_path = Path(metrics).expanduser().resolve() if metrics else None
    assets_path = Path(assets).expanduser().resolve() if assets else None

    errors = validate_inputs(
        {
            "plan": plan_path,
            "visual contract": contract_path,
            "baseline screenshot": baseline_path,
            "platform screenshot": platform_path,
            "metrics": metrics_path,
            "assets": assets_path,
        }
    )
    metrics_data = read_json(metrics_path) if metrics_path and metrics_path.exists() else {}
    assets_data = read_json(assets_path) if assets_path and assets_path.exists() else {}
    assessment = assessment_for(errors=errors, metrics=metrics_data, platform_screenshot=platform_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "verification-report.md"
    report_path.write_text(
        report_markdown(
            target=target,
            platform=platform,
            assessment=assessment,
            plan=plan_path,
            visual_contract=contract_path,
            baseline_screenshot=baseline_path,
            platform_screenshot=platform_path,
            metrics_path=metrics_path,
            metrics_data=metrics_data,
            assets_path=assets_path,
            assets_data=assets_data,
            commands=command or [],
            environment=environment or [],
            errors=errors,
        ),
        encoding="utf-8",
    )
    return {
        "report": str(report_path),
        "assessment": assessment,
        "validation": {"errors": errors, "warnings": []},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Mobile Superpowers UI verification report.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--visual-contract", type=Path, default=None)
    parser.add_argument("--baseline-screenshot", type=Path, default=None)
    parser.add_argument("--platform-screenshot", type=Path, default=None)
    parser.add_argument("--metrics", type=Path, default=None)
    parser.add_argument("--assets", type=Path, default=None)
    parser.add_argument("--command", action="append", default=[])
    parser.add_argument("--environment", action="append", default=[])
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = create_verification_report(
        out_dir=args.out_dir,
        target=args.target,
        platform=args.platform,
        plan=args.plan,
        visual_contract=args.visual_contract,
        baseline_screenshot=args.baseline_screenshot,
        platform_screenshot=args.platform_screenshot,
        metrics=args.metrics,
        assets=args.assets,
        command=args.command,
        environment=args.environment,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["report"])
        print(result["assessment"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["assessment"] in {"NOT_VERIFIED", "BLOCKED"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
