from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_project_constraints.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_project_constraints", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileProjectConstraintsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "project"
        self.project_dir.mkdir()
        self.project_dir.joinpath("AGENTS.md").write_text(
            "\n".join(
                [
                    "# Project UI Rules",
                    "- All dialogs must use CommonDialog.",
                    "- Visible text must use CommonText.",
                    "- Primary actions must use CommonButton.",
                    "- Use AppColors and AppSpacing instead of hard-coded values.",
                    "- Forbidden: AlertDialog, raw Text, ElevatedButton, Color(0x...).",
                ]
            ),
            encoding="utf-8",
        )

    def test_generate_constraints_writes_compact_markdown(self) -> None:
        module = load_module()

        result = module.generate_project_constraints(project_dir=self.project_dir)

        output = Path(result["output"])
        self.assertTrue(output.exists())
        text = output.read_text(encoding="utf-8")
        self.assertIn("# Mobile Project Constraints", text)
        self.assertIn("AGENTS.md", text)
        self.assertIn("CommonDialog", text)
        self.assertIn("CommonText", text)
        self.assertIn("CommonButton", text)
        self.assertIn("AppColors", text)
        self.assertIn("AlertDialog", text)
        self.assertIn("Text(", text)
        self.assertIn("mobile_component_contract_check.py", text)
        self.assertLess(len(text), 7000)
        self.assertEqual(result["validation"]["errors"], [])

    def test_style_skill_is_recorded_by_path_not_bulk_copied(self) -> None:
        style_skill = self.project_dir / "skills" / "project-style" / "SKILL.md"
        style_skill.parent.mkdir(parents=True)
        style_skill.write_text(
            "# Project Style\n\n" + ("Use CommonText and CommonDialog.\n" * 500),
            encoding="utf-8",
        )
        module = load_module()

        result = module.generate_project_constraints(project_dir=self.project_dir, style_skill=style_skill)

        text = Path(result["output"]).read_text(encoding="utf-8")
        self.assertIn("Style Skill Binding", text)
        self.assertIn("skills/project-style/SKILL.md", text)
        self.assertLess(len(text), 7000)

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["validation"]["errors"], [])
        self.assertTrue(Path(payload["output"]).exists())
        self.assertIn("CommonDialog", payload["component_contract"]["required_components"])


if __name__ == "__main__":
    unittest.main()
