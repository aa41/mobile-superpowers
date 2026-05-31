from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_plan_scaffold.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_plan_scaffold", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobilePlanScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "project"
        self.project_dir.mkdir()
        self.visual_dir = self.project_dir / "docs" / "mobile-superpowers" / "visual" / "2026-05-31-profile"
        self.visual_dir.mkdir(parents=True)
        self.contract = self.visual_dir / "visual-contract.md"
        self.contract.write_text("# Profile Visual Contract\n", encoding="utf-8")
        self.assets = self.visual_dir / "assets.json"
        self.assets.write_text(
            json.dumps(
                {
                    "assets": [
                        {
                            "name": "avatar",
                            "strategy": "image_asset",
                            "source": "generated-mockup.png",
                            "target_path": "assets/images/avatar.png",
                            "dimensions": "160x160",
                            "platform_notes": "Profile portrait",
                        },
                        {
                            "name": "hero-background",
                            "strategy": "regenerate",
                            "source": "visual prompt",
                            "target_path": "assets/images/hero-background.png",
                            "dimensions": "390x220",
                            "platform_notes": "Soft gradient illustration",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_create_plan_scaffold_includes_asset_matrix(self) -> None:
        module = load_module()

        result = module.create_plan_scaffold(
            project_dir=self.project_dir,
            feature="Profile Screen",
            platform="Flutter",
            spec="docs/specs/profile.md",
            visual_contract=self.contract,
            assets=self.assets,
            date="2026-05-31",
        )

        plan = Path(result["plan"])
        self.assertTrue(plan.exists())
        text = plan.read_text(encoding="utf-8")
        self.assertIn("# Profile Screen Mobile Implementation Plan", text)
        self.assertIn("**Asset Manifest:**", text)
        self.assertIn("## Asset Implementation Matrix", text)
        self.assertIn("| avatar | image_asset |", text)
        self.assertIn("pubspec.yaml", text)
        self.assertIn("Task 1: Prepare Visual Assets", text)
        self.assertIn("assets/images/hero-background.png", text)

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--feature",
                "Profile Screen",
                "--platform",
                "Flutter",
                "--spec",
                "docs/specs/profile.md",
                "--visual-contract",
                str(self.contract),
                "--assets",
                str(self.assets),
                "--date",
                "2026-05-31",
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["validation"]["errors"], [])
        self.assertTrue(Path(payload["plan"]).exists())


if __name__ == "__main__":
    unittest.main()
