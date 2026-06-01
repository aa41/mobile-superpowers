from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_component_contract_check.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_component_contract_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileComponentContractCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "project"
        self.project_dir.mkdir()
        (self.project_dir / "lib" / "features").mkdir(parents=True)
        (self.project_dir / "lib" / "common").mkdir(parents=True)

    def test_flutter_forbidden_direct_use_reports_feature_violations(self) -> None:
        self.project_dir.joinpath("lib/features/profile_page.dart").write_text(
            "\n".join(
                [
                    "import 'package:flutter/material.dart';",
                    "class ProfilePage extends StatelessWidget {",
                    "  const ProfilePage({super.key});",
                    "  Widget build(BuildContext context) {",
                    "    return AlertDialog(content: Text('Bad'), backgroundColor: Color(0xFFFFFFFF));",
                    "  }",
                    "}",
                ]
            ),
            encoding="utf-8",
        )
        self.project_dir.joinpath("lib/common/common_text.dart").write_text(
            "Widget commonText() => Text('allowed in base component');",
            encoding="utf-8",
        )
        module = load_module()

        result = module.check_component_contract(project_dir=self.project_dir, platform="flutter")

        self.assertEqual(result["validation"]["errors"], [])
        self.assertGreaterEqual(len(result["violations"]), 3)
        files = {Path(item["file"]).as_posix() for item in result["violations"]}
        self.assertIn("lib/features/profile_page.dart", files)
        self.assertNotIn("lib/common/common_text.dart", files)
        forbidden = {item["forbidden"] for item in result["violations"]}
        self.assertIn("AlertDialog", forbidden)
        self.assertIn("Text(", forbidden)
        self.assertIn("Color(0x", forbidden)

    def test_flutter_clean_project_passes(self) -> None:
        self.project_dir.joinpath("lib/features/profile_page.dart").write_text(
            "\n".join(
                [
                    "class ProfilePage {",
                    "  final title = CommonText('Profile');",
                    "  final action = CommonButton(label: 'Save');",
                    "}",
                ]
            ),
            encoding="utf-8",
        )
        module = load_module()

        result = module.check_component_contract(project_dir=self.project_dir, platform="flutter")

        self.assertEqual(result["violations"], [])
        self.assertEqual(result["summary"]["status"], "passed")

    def test_cli_returns_nonzero_for_violations(self) -> None:
        self.project_dir.joinpath("lib/features/profile_page.dart").write_text(
            "Widget build(BuildContext context) => Text('Bad');",
            encoding="utf-8",
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--platform",
                "flutter",
                "--json",
            ],
            check=False,
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["violations"][0]["forbidden"], "Text(")


if __name__ == "__main__":
    unittest.main()
