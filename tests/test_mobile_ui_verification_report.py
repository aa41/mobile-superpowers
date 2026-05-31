from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_ui_verification_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_ui_verification_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileUIVerificationReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "verification"
        self.workspace.mkdir()
        self.plan = self.workspace / "plan.md"
        self.plan.write_text("# Plan\n", encoding="utf-8")
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text("# Visual Contract\n", encoding="utf-8")
        self.baseline = self.workspace / "baseline-screenshot.png"
        self.platform = self.workspace / "flutter-web-screenshot.png"
        self.baseline.write_bytes(b"baseline")
        self.platform.write_bytes(b"platform")
        self.assets = self.workspace / "assets.json"
        self.assets.write_text(
            json.dumps(
                {
                    "assets": [
                        {"name": "avatar", "strategy": "image_asset", "target_path": "assets/images/avatar.png"}
                    ]
                }
            ),
            encoding="utf-8",
        )
        self.metrics = self.workspace / "platform-metrics.json"
        self.metrics.write_text(
            json.dumps(
                {
                    "regions": [
                        {
                            "name": "full",
                            "rms_diff": 12.5,
                            "mean_abs_diff": 4.25,
                            "diff": str(self.workspace / "platform-full-diff.png"),
                            "heatmap": str(self.workspace / "platform-full-heatmap.png"),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_report_with_metrics_and_assets_is_verified_with_deviations(self) -> None:
        module = load_module()

        result = module.create_verification_report(
            out_dir=self.workspace,
            target="Profile Screen",
            platform="Flutter Web",
            plan=self.plan,
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            platform_screenshot=self.platform,
            metrics=self.metrics,
            assets=self.assets,
            command=["flutter test", "flutter build web"],
            environment=["Chrome mobile viewport 390x844"],
        )

        report = Path(result["report"])
        self.assertTrue(report.exists())
        text = report.read_text(encoding="utf-8")
        self.assertIn("# Mobile UI Verification Report", text)
        self.assertIn("Completion Assessment: `VERIFIED_WITH_DEVIATIONS`", text)
        self.assertIn("platform-metrics.json", text)
        self.assertIn("avatar", text)
        self.assertEqual(result["assessment"], "VERIFIED_WITH_DEVIATIONS")

    def test_missing_platform_screenshot_is_not_verified(self) -> None:
        module = load_module()

        result = module.create_verification_report(
            out_dir=self.workspace,
            target="Profile Screen",
            platform="Flutter Web",
            plan=self.plan,
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            platform_screenshot=self.workspace / "missing.png",
            metrics=self.metrics,
            assets=self.assets,
        )

        self.assertEqual(result["assessment"], "NOT_VERIFIED")
        self.assertIn("platform screenshot not found", result["validation"]["errors"][0])

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--out-dir",
                str(self.workspace),
                "--target",
                "Profile Screen",
                "--platform",
                "Flutter Web",
                "--plan",
                str(self.plan),
                "--visual-contract",
                str(self.contract),
                "--baseline-screenshot",
                str(self.baseline),
                "--platform-screenshot",
                str(self.platform),
                "--metrics",
                str(self.metrics),
                "--assets",
                str(self.assets),
                "--command",
                "flutter test",
                "--environment",
                "Chrome mobile viewport 390x844",
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["assessment"], "VERIFIED_WITH_DEVIATIONS")
        self.assertTrue(Path(payload["report"]).exists())


if __name__ == "__main__":
    unittest.main()
