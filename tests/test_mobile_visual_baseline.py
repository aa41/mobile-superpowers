from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_baseline.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_baseline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "docs" / "mobile-superpowers" / "visual" / "2026-05-31-checkout"
        self.workspace.mkdir(parents=True)
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text(
            "\n".join(
                [
                    "# Checkout Visual Contract",
                    "",
                    "## Source Inputs",
                    "",
                    "- Not recorded yet.",
                    "",
                    "## HTML Baseline",
                    "",
                    "- Not recorded yet.",
                    "",
                    "## Platform Handoff Notes",
                    "",
                    "- Not recorded yet.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        self.metadata = self.workspace / "generated-mockup.png.json"
        self.metadata.write_text(
            json.dumps(
                {
                    "dry_run": True,
                    "workspace": str(self.workspace),
                    "provider": {"name": "proxy", "model": "gpt-image-2", "endpoint_style": "openai-images"},
                    "request": {
                        "prompt": "Design a checkout confirmation screen.",
                        "refs": [],
                        "aspect_ratio": "3:4",
                        "size": "1024x1536",
                        "quality": "high",
                    },
                    "outputs": {
                        "image": str(self.workspace / "generated-mockup.png"),
                        "metadata": str(self.metadata),
                    },
                    "validation": {"errors": [], "warnings": []},
                }
            ),
            encoding="utf-8",
        )

    def test_create_baseline_html_from_provider_metadata(self) -> None:
        module = load_module()

        result = module.create_baseline(metadata_path=self.metadata)

        baseline = (self.workspace / "baseline.html").resolve()
        self.assertEqual(result["baseline_html"], str(baseline))
        self.assertTrue(baseline.exists())
        html = baseline.read_text(encoding="utf-8")
        self.assertIn("<meta name=\"viewport\"", html)
        self.assertIn("Design a checkout confirmation screen.", html)
        self.assertIn("data-mobile-superpowers-baseline", html)
        self.assertEqual(result["validation"]["errors"], [])

    def test_visual_contract_html_section_is_updated(self) -> None:
        module = load_module()

        module.create_baseline(metadata_path=self.metadata)

        text = self.contract.read_text(encoding="utf-8")
        self.assertIn("- Baseline HTML: `", text)
        self.assertIn("baseline.html", text)
        self.assertIn("- Source metadata: `", text)
        self.assertNotIn("## HTML Baseline\n\n- Not recorded yet.", text)

    def test_existing_baseline_is_not_overwritten_without_force(self) -> None:
        baseline = self.workspace / "baseline.html"
        baseline.write_text("custom html", encoding="utf-8")
        module = load_module()

        module.create_baseline(metadata_path=self.metadata)

        self.assertEqual(baseline.read_text(encoding="utf-8"), "custom html")

    def test_force_rewrites_baseline(self) -> None:
        baseline = self.workspace / "baseline.html"
        baseline.write_text("custom html", encoding="utf-8")
        module = load_module()

        module.create_baseline(metadata_path=self.metadata, force=True)

        self.assertIn("data-mobile-superpowers-baseline", baseline.read_text(encoding="utf-8"))

    def test_cli_creates_baseline(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--metadata",
                str(self.metadata),
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        self.assertIn("baseline.html", completed.stdout)
        self.assertTrue((self.workspace / "baseline.html").exists())


if __name__ == "__main__":
    unittest.main()
