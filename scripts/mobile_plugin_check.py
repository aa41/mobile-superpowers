#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def run_session_start(plugin_root: Path) -> tuple[bool, str]:
    hook = plugin_root / "hooks" / "run-hook.cmd"
    if not hook.exists():
        return False, ""
    completed = subprocess.run(
        ["bash", str(hook), "session-start"],
        cwd=str(plugin_root),
        text=True,
        capture_output=True,
    )
    return completed.returncode == 0, completed.stdout


def check_plugin(plugin_root: Path | str) -> dict[str, Any]:
    plugin_root = Path(plugin_root).expanduser().resolve()
    errors: list[str] = []

    codex_manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    claude_manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    hooks_path = plugin_root / "hooks" / "hooks.json"
    using_skill_path = plugin_root / "skills" / "using-mobile-superpowers" / "SKILL.md"
    mobile_worktrees_path = plugin_root / "skills" / "mobile-using-git-worktrees" / "SKILL.md"
    mobile_executing_path = plugin_root / "skills" / "mobile-executing-plans" / "SKILL.md"
    mobile_tdd_path = plugin_root / "skills" / "mobile-test-driven-development" / "SKILL.md"
    mobile_debugging_path = plugin_root / "skills" / "mobile-systematic-debugging" / "SKILL.md"
    mobile_completion_path = plugin_root / "skills" / "mobile-verification-before-completion" / "SKILL.md"
    mobile_request_review_path = plugin_root / "skills" / "mobile-requesting-code-review" / "SKILL.md"
    mobile_receive_review_path = plugin_root / "skills" / "mobile-receiving-code-review" / "SKILL.md"
    mobile_finishing_path = plugin_root / "skills" / "mobile-finishing-a-development-branch" / "SKILL.md"
    mobile_brainstorming_path = plugin_root / "skills" / "mobile-brainstorming" / "SKILL.md"
    mobile_writing_plans_path = plugin_root / "skills" / "mobile-writing-plans" / "SKILL.md"
    spec_reviewer_path = plugin_root / "skills" / "mobile-brainstorming" / "spec-document-reviewer-prompt.md"
    plan_reviewer_path = plugin_root / "skills" / "mobile-writing-plans" / "plan-document-reviewer-prompt.md"
    acceptance_path = plugin_root / "docs" / "acceptance.md"

    codex_manifest = read_json(codex_manifest_path)
    claude_manifest = read_json(claude_manifest_path)
    hooks = read_json(hooks_path)
    using_skill = using_skill_path.read_text(encoding="utf-8") if using_skill_path.exists() else ""
    brainstorming_skill = mobile_brainstorming_path.read_text(encoding="utf-8") if mobile_brainstorming_path.exists() else ""
    writing_plans_skill = mobile_writing_plans_path.read_text(encoding="utf-8") if mobile_writing_plans_path.exists() else ""
    acceptance = acceptance_path.read_text(encoding="utf-8") if acceptance_path.exists() else ""
    hook_ok, hook_output = run_session_start(plugin_root)

    checks = {
        "codex": {
            "manifest": str(codex_manifest_path),
            "manifest_loaded": bool(codex_manifest),
            "skills": codex_manifest.get("skills", ""),
            "skills_dir_exists": (plugin_root / "skills").is_dir(),
        },
        "claude": {
            "manifest": str(claude_manifest_path),
            "manifest_loaded": bool(claude_manifest),
            "hooks_loaded": bool(hooks),
            "session_start_ok": hook_ok,
            "session_start_injects_using_skill": "using-mobile-superpowers" in hook_output
            and "Mobile Superpowers" in hook_output,
        },
        "using_skill": {
            "path": str(using_skill_path),
            "exists": using_skill_path.exists(),
            "mentions_mobile_brainstorming": "mobile-brainstorming" in using_skill,
            "mentions_mobile_visual_design": "mobile-visual-design" in using_skill,
            "mentions_mobile_writing_plans": "mobile-writing-plans" in using_skill,
            "mentions_mobile_ui_verification": "mobile-ui-verification" in using_skill,
            "mentions_mobile_using_git_worktrees": "mobile-using-git-worktrees" in using_skill,
            "mentions_mobile_executing_plans": "mobile-executing-plans" in using_skill,
            "mentions_mobile_test_driven_development": "mobile-test-driven-development" in using_skill,
            "mentions_mobile_systematic_debugging": "mobile-systematic-debugging" in using_skill,
            "mentions_mobile_verification_before_completion": "mobile-verification-before-completion" in using_skill,
            "mentions_mobile_requesting_code_review": "mobile-requesting-code-review" in using_skill,
            "mentions_mobile_receiving_code_review": "mobile-receiving-code-review" in using_skill,
            "mentions_mobile_finishing_a_development_branch": "mobile-finishing-a-development-branch" in using_skill,
        },
        "skills": {
            "mobile_using_git_worktrees": str(mobile_worktrees_path),
            "mobile_using_git_worktrees_exists": mobile_worktrees_path.exists(),
            "mobile_executing_plans": str(mobile_executing_path),
            "mobile_executing_plans_exists": mobile_executing_path.exists(),
            "mobile_test_driven_development": str(mobile_tdd_path),
            "mobile_test_driven_development_exists": mobile_tdd_path.exists(),
            "mobile_systematic_debugging": str(mobile_debugging_path),
            "mobile_systematic_debugging_exists": mobile_debugging_path.exists(),
            "mobile_verification_before_completion": str(mobile_completion_path),
            "mobile_verification_before_completion_exists": mobile_completion_path.exists(),
            "mobile_requesting_code_review": str(mobile_request_review_path),
            "mobile_requesting_code_review_exists": mobile_request_review_path.exists(),
            "mobile_receiving_code_review": str(mobile_receive_review_path),
            "mobile_receiving_code_review_exists": mobile_receive_review_path.exists(),
            "mobile_finishing_a_development_branch": str(mobile_finishing_path),
            "mobile_finishing_a_development_branch_exists": mobile_finishing_path.exists(),
        },
        "review_prompts": {
            "spec_reviewer": str(spec_reviewer_path),
            "spec_reviewer_exists": spec_reviewer_path.exists(),
            "plan_reviewer": str(plan_reviewer_path),
            "plan_reviewer_exists": plan_reviewer_path.exists(),
            "brainstorming_references_spec_reviewer": "spec-document-reviewer-prompt.md" in brainstorming_skill,
            "writing_plans_references_plan_reviewer": "plan-document-reviewer-prompt.md" in writing_plans_skill,
        },
        "acceptance": {
            "path": str(acceptance_path),
            "document_exists": acceptance_path.exists(),
            "prompt": "Let's make a mobile todo list" if "Let's make a mobile todo list" in acceptance else "",
            "mentions_claude": "Claude Code" in acceptance,
            "mentions_codex": "Codex" in acceptance,
        },
        "validation": {"errors": errors, "warnings": []},
    }

    if not checks["codex"]["manifest_loaded"]:
        errors.append(f"Codex manifest not found or invalid: {codex_manifest_path}")
    if checks["codex"]["skills"] != "./skills/":
        errors.append("Codex manifest must expose skills as ./skills/")
    if not checks["claude"]["manifest_loaded"]:
        errors.append(f"Claude manifest not found or invalid: {claude_manifest_path}")
    if not checks["claude"]["session_start_injects_using_skill"]:
        errors.append("Claude session-start hook did not inject using-mobile-superpowers")
    if not checks["acceptance"]["document_exists"]:
        errors.append(f"Acceptance document missing: {acceptance_path}")
    if not checks["acceptance"]["prompt"]:
        errors.append("Acceptance prompt missing")
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Mobile Superpowers plugin manifests, hook, and acceptance docs.")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = check_plugin(args.plugin_root)
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"codex_manifest_loaded={result['codex']['manifest_loaded']}")
        print(f"claude_manifest_loaded={result['claude']['manifest_loaded']}")
        print(f"session_start_injects_using_skill={result['claude']['session_start_injects_using_skill']}")
        print(f"acceptance_document_exists={result['acceptance']['document_exists']}")
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
