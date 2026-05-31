from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_full_chain_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_full_chain_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileFullChainCheckTests(unittest.TestCase):
    def test_full_chain_reports_all_workflow_gates(self) -> None:
        module = load_module()

        result = module.check_full_chain(ROOT)

        self.assertEqual(result["validation"]["errors"], [])
        self.assertTrue(result["workflow"]["bootstrap"])
        self.assertTrue(result["workflow"]["design"])
        self.assertTrue(result["workflow"]["spec_review"])
        self.assertTrue(result["workflow"]["visual"])
        self.assertTrue(result["workflow"]["planning"])
        self.assertTrue(result["workflow"]["plan_review"])
        self.assertTrue(result["workflow"]["execution"])
        self.assertTrue(result["workflow"]["quality"])
        self.assertTrue(result["workflow"]["ui_verification"])
        self.assertTrue(result["workflow"]["completion"])
        self.assertTrue(result["workflow"]["review"])
        self.assertTrue(result["workflow"]["finishing"])
        self.assertIn("Let's make a mobile todo list", result["acceptance"]["prompt"])

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--plugin-root", str(ROOT), "--json"],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["validation"]["errors"], [])
        self.assertTrue(payload["workflow"]["completion"])


if __name__ == "__main__":
    unittest.main()
