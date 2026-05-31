from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_compare.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_compare", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualCompareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "workspace"
        self.workspace.mkdir()
        self.reference = self.workspace / "reference.png"
        self.candidate = self.workspace / "baseline-screenshot.png"
        self.reference.write_bytes(b"reference")
        self.candidate.write_bytes(b"candidate")
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text(
            "\n".join(
                [
                    "# Demo Visual Contract",
                    "",
                    "## Screenshot And Metrics",
                    "",
                    "- Baseline screenshot: `baseline-screenshot.png`",
                    "",
                    "## Platform Handoff Notes",
                    "",
                    "- Not recorded yet.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def fake_comparer(self, *, reference, candidate, out_dir, prefix, clips):
        full_candidate = out_dir / f"{prefix}-full-candidate.png"
        diff = out_dir / f"{prefix}-full-diff.png"
        heatmap = out_dir / f"{prefix}-full-heatmap.png"
        full_candidate.write_bytes(b"candidate")
        diff.write_bytes(b"diff")
        heatmap.write_bytes(b"heatmap")
        return {
            "reference": str(reference),
            "candidate": str(candidate),
            "reference_size": [390, 844],
            "candidate_size_original": [390, 844],
            "candidate_size_compared": [390, 844],
            "regions": [
                {
                    "name": "full",
                    "size": [390, 844],
                    "rms_diff": 1.25,
                    "mean_abs_diff": 0.75,
                    "candidate": str(full_candidate),
                    "diff": str(diff),
                    "heatmap": str(heatmap),
                }
            ],
            "clips": clips,
        }

    def test_compare_visuals_writes_metrics_and_updates_contract(self) -> None:
        module = load_module()

        result = module.compare_visuals(
            reference=self.reference,
            candidate=self.candidate,
            comparer=self.fake_comparer,
            clips=["cta:0,600,390,120"],
        )

        metrics_path = (self.workspace / "baseline-metrics.json").resolve()
        self.assertEqual(result["metrics"], str(metrics_path))
        self.assertTrue(metrics_path.exists())
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertEqual(metrics["regions"][0]["rms_diff"], 1.25)
        self.assertEqual(metrics["clips"], ["cta:0,600,390,120"])
        contract_text = self.contract.read_text(encoding="utf-8")
        self.assertIn("- Baseline metrics: `", contract_text)
        self.assertIn("baseline-metrics.json", contract_text)
        self.assertIn("full-heatmap.png", contract_text)

    def test_missing_reference_reports_error(self) -> None:
        module = load_module()

        result = module.compare_visuals(
            reference=self.workspace / "missing.png",
            candidate=self.candidate,
            comparer=self.fake_comparer,
        )

        self.assertIn("reference image not found", result["validation"]["errors"][0])

    def test_missing_pillow_dependency_has_clear_error(self) -> None:
        module = load_module()

        result = module.compare_visuals(reference=self.reference, candidate=self.candidate)

        if module.pillow_available():
            self.assertEqual(result["validation"]["errors"], [])
        else:
            self.assertIn("Pillow is required", result["validation"]["errors"][0])

    def test_cli_reports_json_result(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--reference",
                str(self.reference),
                "--candidate",
                str(self.candidate),
                "--json",
            ],
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertIn("validation", payload)
        if load_module().pillow_available():
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(payload["validation"]["errors"], [])
        else:
            self.assertEqual(completed.returncode, 1)
            self.assertIn("Pillow is required", payload["validation"]["errors"][0])


if __name__ == "__main__":
    unittest.main()
