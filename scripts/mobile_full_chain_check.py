#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


SKILL_PATHS = {
    "bootstrap": "skills/using-mobile-superpowers/SKILL.md",
    "design": "skills/mobile-brainstorming/SKILL.md",
    "visual": "skills/mobile-visual-design/SKILL.md",
    "planning": "skills/mobile-writing-plans/SKILL.md",
    "worktree": "skills/mobile-using-git-worktrees/SKILL.md",
    "execution": "skills/mobile-executing-plans/SKILL.md",
    "tdd": "skills/mobile-test-driven-development/SKILL.md",
    "debugging": "skills/mobile-systematic-debugging/SKILL.md",
    "ui_verification": "skills/mobile-ui-verification/SKILL.md",
    "completion": "skills/mobile-verification-before-completion/SKILL.md",
    "request_review": "skills/mobile-requesting-code-review/SKILL.md",
    "receive_review": "skills/mobile-receiving-code-review/SKILL.md",
    "finishing": "skills/mobile-finishing-a-development-branch/SKILL.md",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_plugin_check(plugin_root: Path):
    script = plugin_root / "scripts" / "mobile_plugin_check.py"
    spec = importlib.util.spec_from_file_location("mobile_plugin_check", script)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def check_full_chain(plugin_root: Path | str) -> dict[str, Any]:
    plugin_root = Path(plugin_root).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    plugin_check = load_plugin_check(plugin_root).check_plugin(plugin_root)
    errors.extend(plugin_check["validation"]["errors"])

    contents = {name: read_text(plugin_root / path) for name, path in SKILL_PATHS.items()}
    exists = {name: bool(contents[name]) for name in SKILL_PATHS}

    workflow = {
        "bootstrap": exists["bootstrap"] and all(
            token in contents["bootstrap"]
            for token in [
                "mobile-brainstorming",
                "mobile-visual-design",
                "mobile-writing-plans",
                "mobile-using-git-worktrees",
                "mobile-executing-plans",
                "mobile-test-driven-development",
                "mobile-systematic-debugging",
                "mobile-ui-verification",
                "mobile-verification-before-completion",
                "mobile-requesting-code-review",
                "mobile-receiving-code-review",
                "mobile-finishing-a-development-branch",
            ]
        ),
        "design": exists["design"] and "3 research agent + 2 review agent + 1 integration agent" in contents["design"],
        "spec_review": exists["design"] and "spec-document-reviewer-prompt.md" in contents["design"],
        "visual": exists["visual"] and "visual-contract.md" in contents["visual"],
        "planning": exists["planning"] and "mobile_plan_scaffold.py" in contents["planning"],
        "plan_review": exists["planning"] and "plan-document-reviewer-prompt.md" in contents["planning"],
        "worktree": exists["worktree"] and "git worktree" in contents["worktree"],
        "execution": exists["execution"] and "mobile-using-git-worktrees" in contents["execution"],
        "quality": exists["execution"]
        and "mobile-test-driven-development" in contents["execution"]
        and "mobile-systematic-debugging" in contents["execution"],
        "ui_verification": exists["ui_verification"]
        and "mobile_flutter_web_verify.py" in contents["ui_verification"]
        and "mobile_android_verify.py" in contents["ui_verification"]
        and "mobile_ios_verify.py" in contents["ui_verification"],
        "completion": exists["completion"] and "mobile-ui-verification" in contents["completion"],
        "review": exists["request_review"]
        and exists["receive_review"]
        and "mobile-code-reviewer.md" in contents["request_review"],
        "finishing": exists["finishing"] and "mobile-verification-before-completion" in contents["finishing"],
    }

    for gate, ok in workflow.items():
        if not ok:
            errors.append(f"Workflow gate not ready: {gate}")

    prompt_path = plugin_root / "docs" / "acceptance.md"
    acceptance = read_text(prompt_path)

    harness = {
        "claude_path": shutil.which("claude") or "",
        "codex_path": shutil.which("codex") or "",
        "clean_session_required": True,
        "automated_clean_session_ran": False,
    }
    if not harness["claude_path"]:
        warnings.append("Claude CLI not found on PATH; Claude clean-session acceptance must run elsewhere.")
    if not harness["codex_path"]:
        warnings.append("Codex CLI not found on PATH; Codex clean-session acceptance must run elsewhere.")

    return {
        "plugin": plugin_check,
        "workflow": workflow,
        "acceptance": {
            "path": str(prompt_path),
            "prompt": "Let's make a mobile todo list" if "Let's make a mobile todo list" in acceptance else "",
            "requires_clean_session": True,
            "expected_first_skill": "using-mobile-superpowers",
            "expected_downstream_skill": "mobile-brainstorming",
        },
        "harness": harness,
        "validation": {"errors": errors, "warnings": warnings},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Mobile Superpowers full workflow chain readiness.")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_full_chain(args.plugin_root)
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for gate, ok in result["workflow"].items():
            print(f"{gate}={'ok' if ok else 'missing'}")
        print(f"claude_path={result['harness']['claude_path'] or 'missing'}")
        print(f"codex_path={result['harness']['codex_path'] or 'missing'}")
    for warning in result["validation"]["warnings"]:
        print(f"WARNING: {warning}")
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
