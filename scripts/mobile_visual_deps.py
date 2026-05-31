#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable


PACKAGES = ["Pillow"]


Runner = Callable[..., subprocess.CompletedProcess]


def default_venv_path(*, home_dir: Path | str = Path.home()) -> Path:
    return Path(home_dir).expanduser() / ".cache" / "mobile-superpowers" / "visual-venv"


def venv_python(venv_path: Path | str) -> Path:
    venv_path = Path(venv_path).expanduser()
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def check_deps(*, venv_path: Path | str, runner: Runner = subprocess.run) -> dict:
    venv_path = Path(venv_path).expanduser()
    python_path = venv_python(venv_path)
    errors: list[str] = []
    if not python_path.exists():
        errors.append(f"venv python not found: {python_path}")
        return {
            "ok": False,
            "venv": str(venv_path),
            "python": str(python_path),
            "packages": PACKAGES,
            "validation": {"errors": errors, "warnings": []},
        }

    completed = runner(
        [str(python_path), "-c", "import PIL; print('Pillow OK')"],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        errors.append("Pillow is not importable in the visual venv")
    return {
        "ok": not errors,
        "venv": str(venv_path),
        "python": str(python_path),
        "packages": PACKAGES,
        "stdout": completed.stdout.strip(),
        "validation": {"errors": errors, "warnings": []},
    }


def install_deps(
    *,
    venv_path: Path | str,
    python_executable: str | None = None,
    runner: Runner = subprocess.run,
) -> dict:
    venv_path = Path(venv_path).expanduser()
    python_path = venv_python(venv_path)
    base_python = python_executable or sys.executable
    commands: list[list[str]] = []
    errors: list[str] = []

    if not python_path.exists():
        create_cmd = [base_python, "-m", "venv", str(venv_path)]
        commands.append(create_cmd)
        completed = runner(create_cmd, text=True, capture_output=True)
        if completed.returncode != 0:
            errors.append(f"venv creation failed with code {completed.returncode}")
            stderr = (completed.stderr or "").strip()
            if stderr:
                errors.append(stderr.splitlines()[-1])

    if not errors:
        install_cmd = [str(python_path), "-m", "pip", "install", *PACKAGES]
        commands.append(install_cmd)
        completed = runner(install_cmd, text=True, capture_output=True)
        if completed.returncode != 0:
            errors.append(f"pip install failed with code {completed.returncode}")
            stderr = (completed.stderr or "").strip()
            if stderr:
                errors.append(stderr.splitlines()[-1])

    check = check_deps(venv_path=venv_path, runner=runner) if not errors else None
    if check and not check["ok"]:
        errors.extend(check["validation"]["errors"])

    return {
        "ok": not errors,
        "venv": str(venv_path),
        "python": str(python_path),
        "base_python": base_python,
        "packages": PACKAGES,
        "commands": commands,
        "validation": {"errors": errors, "warnings": []},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage optional Mobile Superpowers visual dependencies.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--install", action="store_true")
    parser.add_argument("--home-dir", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--venv", type=Path, default=None)
    parser.add_argument("--python", default=None, help="Python executable used to create the venv.")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    venv_path = args.venv or default_venv_path(home_dir=args.home_dir)
    result = install_deps(venv_path=venv_path, python_executable=args.python) if args.install else check_deps(venv_path=venv_path)
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"venv={result['venv']}")
        print(f"python={result['python']}")
        print(f"ok={result['ok']}")
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
