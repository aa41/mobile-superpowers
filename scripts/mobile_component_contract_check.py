#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FLUTTER_FORBIDDEN = [
    {"pattern": "AlertDialog", "regex": r"(?<![A-Za-z0-9_])AlertDialog\b", "required": "CommonDialog"},
    {"pattern": "Dialog(", "regex": r"(?<![A-Za-z0-9_])Dialog\s*\(", "required": "CommonDialog"},
    {"pattern": "Text(", "regex": r"(?<![A-Za-z0-9_])Text\s*\(", "required": "CommonText"},
    {"pattern": "ElevatedButton", "regex": r"(?<![A-Za-z0-9_])ElevatedButton\b", "required": "CommonButton"},
    {"pattern": "FilledButton", "regex": r"(?<![A-Za-z0-9_])FilledButton\b", "required": "CommonButton"},
    {"pattern": "Color(0x", "regex": r"(?<![A-Za-z0-9_])Color\s*\(\s*0x", "required": "AppColors or project theme tokens"},
]

DEFAULT_ALLOWED_PREFIXES = [
    "lib/common/",
    "lib/components/",
    "lib/component/",
    "lib/theme/",
    "lib/design_system/",
    "lib/design-system/",
    "test/",
]


def relpath(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def is_allowed_path(relative: str) -> bool:
    return any(relative.startswith(prefix) for prefix in DEFAULT_ALLOWED_PREFIXES)


def scan_flutter(project_dir: Path) -> list[dict[str, Any]]:
    root = project_dir / "lib"
    if not root.exists():
        return []
    violations: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.dart")):
        relative = relpath(path, project_dir)
        if is_allowed_path(relative):
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines, start=1):
            for rule in FLUTTER_FORBIDDEN:
                if re.search(rule["regex"], line):
                    violations.append(
                        {
                            "file": relative,
                            "line": index,
                            "forbidden": rule["pattern"],
                            "required": rule["required"],
                            "snippet": line.strip()[:220],
                        }
                    )
    return violations


def check_component_contract(
    *,
    project_dir: Path | str,
    platform: str,
    contract: Path | str | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    contract_path = Path(contract).expanduser().resolve() if contract else None
    errors: list[str] = []
    normalized = platform.strip().lower()
    if not project_dir.exists():
        errors.append(f"project dir not found: {project_dir}")
    if normalized != "flutter":
        errors.append(f"unsupported platform for component contract check: {platform}")
    if contract_path and not contract_path.exists():
        errors.append(f"contract not found: {contract_path}")
    violations = [] if errors else scan_flutter(project_dir)
    status = "blocked" if errors else ("failed" if violations else "passed")
    return {
        "project_dir": str(project_dir),
        "platform": normalized,
        "contract": str(contract_path) if contract_path else None,
        "summary": {
            "status": status,
            "violation_count": len(violations),
            "allowed_prefixes": DEFAULT_ALLOWED_PREFIXES,
        },
        "violations": violations,
        "validation": {"errors": errors, "warnings": []},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check mobile project component contract usage.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--platform", default="flutter")
    parser.add_argument("--contract", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_component_contract(
        project_dir=args.project_dir,
        platform=args.platform,
        contract=args.contract,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status: {result['summary']['status']}")
        for violation in result["violations"]:
            print(
                "{file}:{line}: {forbidden} -> {required}".format(
                    file=violation["file"],
                    line=violation["line"],
                    forbidden=violation["forbidden"],
                    required=violation["required"],
                )
            )
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] or result["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
