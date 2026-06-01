from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_artifacts.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_artifacts", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "project"
        self.project_dir.mkdir()

    def test_create_visual_workspace_writes_contract_scaffold(self) -> None:
        module = load_module()

        result = module.create_visual_workspace(
            project_dir=self.project_dir,
            topic="Checkout Flow V2!",
            date="2026-05-31",
        )

        workspace = (
            self.project_dir / "docs" / "mobile-superpowers" / "visual" / "2026-05-31-checkout-flow-v2"
        ).resolve()
        self.assertEqual(result["workspace"], str(workspace))
        self.assertTrue(workspace.is_dir())
        contract = workspace / "visual-contract.md"
        self.assertTrue(contract.exists())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("# Checkout Flow V2 Visual Contract", text)
        self.assertIn("## HTML Baseline", text)
        self.assertIn("Use `code` for layout primitives", text)
        self.assertIn("image_asset", text)
        self.assertIn("## Platform Handoff Notes", text)
        self.assertEqual(result["artifacts"]["baseline_html"], str(workspace / "baseline.html"))

    def test_existing_contract_is_not_overwritten_without_force(self) -> None:
        module = load_module()
        first = module.create_visual_workspace(
            project_dir=self.project_dir,
            topic="Profile",
            date="2026-05-31",
        )
        contract = Path(first["artifacts"]["visual_contract"])
        contract.write_text("custom notes", encoding="utf-8")

        module.create_visual_workspace(project_dir=self.project_dir, topic="Profile", date="2026-05-31")

        self.assertEqual(contract.read_text(encoding="utf-8"), "custom notes")

    def test_force_rewrites_contract(self) -> None:
        module = load_module()
        first = module.create_visual_workspace(
            project_dir=self.project_dir,
            topic="Profile",
            date="2026-05-31",
        )
        contract = Path(first["artifacts"]["visual_contract"])
        contract.write_text("custom notes", encoding="utf-8")

        module.create_visual_workspace(
            project_dir=self.project_dir,
            topic="Profile",
            date="2026-05-31",
            force=True,
        )

        self.assertIn("# Profile Visual Contract", contract.read_text(encoding="utf-8"))

    def test_cli_outputs_workspace_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--topic",
                "Settings Screen",
                "--date",
                "2026-05-31",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("2026-05-31-settings-screen", completed.stdout)
        self.assertTrue(
            (self.project_dir / "docs" / "mobile-superpowers" / "visual" / "2026-05-31-settings-screen").is_dir()
        )

    def test_project_constraints_are_recorded_in_contract(self) -> None:
        constraints = self.project_dir / "docs" / "mobile-superpowers" / "project-constraints.md"
        constraints.parent.mkdir(parents=True)
        constraints.write_text("# Mobile Project Constraints\n", encoding="utf-8")
        module = load_module()

        result = module.create_visual_workspace(
            project_dir=self.project_dir,
            topic="Profile",
            date="2026-05-31",
            project_constraints=constraints,
        )

        text = Path(result["artifacts"]["visual_contract"]).read_text(encoding="utf-8")
        self.assertIn("## Project Constraints", text)
        self.assertIn("project-constraints.md", text)
        self.assertIn("data-platform-component", text)
        self.assertEqual(result["artifacts"]["project_constraints"], str(constraints.resolve()))


if __name__ == "__main__":
    unittest.main()
