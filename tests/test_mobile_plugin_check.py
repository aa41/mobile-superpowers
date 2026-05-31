from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_plugin_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_plugin_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobilePluginCheckTests(unittest.TestCase):
    def test_check_plugin_reports_claude_codex_and_acceptance(self) -> None:
        module = load_module()

        result = module.check_plugin(ROOT)

        self.assertEqual(result["validation"]["errors"], [])
        self.assertTrue(result["codex"]["manifest_loaded"])
        self.assertEqual(result["codex"]["skills"], "./skills/")
        self.assertTrue(result["claude"]["manifest_loaded"])
        self.assertTrue(result["claude"]["session_start_injects_using_skill"])
        self.assertTrue(result["acceptance"]["document_exists"])
        self.assertIn("Let's make a mobile todo list", result["acceptance"]["prompt"])
        self.assertTrue(result["using_skill"]["mentions_mobile_using_git_worktrees"])
        self.assertTrue(result["using_skill"]["mentions_mobile_executing_plans"])
        self.assertTrue(result["using_skill"]["mentions_mobile_test_driven_development"])
        self.assertTrue(result["using_skill"]["mentions_mobile_systematic_debugging"])
        self.assertTrue(result["using_skill"]["mentions_mobile_verification_before_completion"])
        self.assertTrue(result["using_skill"]["mentions_mobile_requesting_code_review"])
        self.assertTrue(result["using_skill"]["mentions_mobile_receiving_code_review"])
        self.assertTrue(result["using_skill"]["mentions_mobile_finishing_a_development_branch"])
        self.assertTrue(result["skills"]["mobile_using_git_worktrees_exists"])
        self.assertTrue(result["skills"]["mobile_executing_plans_exists"])
        self.assertTrue(result["skills"]["mobile_test_driven_development_exists"])
        self.assertTrue(result["skills"]["mobile_systematic_debugging_exists"])
        self.assertTrue(result["skills"]["mobile_verification_before_completion_exists"])
        self.assertTrue(result["skills"]["mobile_requesting_code_review_exists"])
        self.assertTrue(result["skills"]["mobile_receiving_code_review_exists"])
        self.assertTrue(result["skills"]["mobile_finishing_a_development_branch_exists"])
        self.assertTrue(result["review_prompts"]["spec_reviewer_exists"])
        self.assertTrue(result["review_prompts"]["plan_reviewer_exists"])
        self.assertTrue(result["review_prompts"]["brainstorming_references_spec_reviewer"])
        self.assertTrue(result["review_prompts"]["writing_plans_references_plan_reviewer"])

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--plugin-root", str(ROOT), "--json"],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["validation"]["errors"], [])
        self.assertTrue(payload["acceptance"]["document_exists"])


if __name__ == "__main__":
    unittest.main()
