from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_ios_verify.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_ios_verify", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileIOSVerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project_dir = Path(self.tmp.name) / "project"
        self.project_dir.mkdir()
        self.visual_dir = self.project_dir / "docs" / "mobile-superpowers" / "visual" / "2026-05-31-profile"
        self.visual_dir.mkdir(parents=True)
        self.baseline = self.visual_dir / "baseline-screenshot.png"
        self.baseline.write_bytes(b"baseline")
        self.contract = self.visual_dir / "visual-contract.md"
        self.contract.write_text("# Contract\n", encoding="utf-8")
        self.assets = self.visual_dir / "assets.json"
        self.assets.write_text(json.dumps({"assets": []}), encoding="utf-8")
        self.plan = self.project_dir / "docs" / "mobile-superpowers" / "plans" / "profile.md"
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text("# Plan\n", encoding="utf-8")
        self.app = self.project_dir / "build" / "ios" / "iphonesimulator" / "Runner.app"
        self.app.mkdir(parents=True)

    def test_dry_run_returns_simctl_screenshot_compare_report_plan(self) -> None:
        module = load_module()

        result = module.verify_ios(
            project_dir=self.project_dir,
            target="Profile Screen",
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            assets=self.assets,
            plan=self.plan,
            app=self.app,
            bundle_id="com.example.app",
            build_command="xcodebuild -scheme App -destination 'platform=iOS Simulator,name=iPhone 15'",
            dry_run=True,
        )

        self.assertTrue(result["dry_run"])
        self.assertIn(["xcrun", "simctl", "install", "booted", str(self.app.resolve())], result["commands"])
        self.assertIn(["xcrun", "simctl", "launch", "booted", "com.example.app"], result["commands"])
        self.assertIn(["xcrun", "simctl", "io", "booted", "screenshot", result["platform_screenshot"]], result["commands"])
        self.assertIn("platform-metrics.json", result["metrics"])
        self.assertIn("verification-report.md", result["report"])

    def test_execute_with_fake_adapters_runs_pipeline(self) -> None:
        module = load_module()
        calls: list[str] = []

        def fake_runner(command, *, cwd=None, timeout=None):
            calls.append(" ".join(command))
            if command[:5] == ["xcrun", "simctl", "io", "booted", "screenshot"]:
                Path(command[5]).write_bytes(b"png")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        def fake_compare(**kwargs):
            metrics = Path(kwargs["out_dir"]) / "baseline-metrics.json"
            metrics.write_text(
                json.dumps(
                    {
                        "regions": [
                            {
                                "name": "full",
                                "rms_diff": 2.0,
                                "mean_abs_diff": 1.0,
                                "diff": "diff.png",
                                "heatmap": "heatmap.png",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            return {"validation": {"errors": []}, "metrics": str(metrics), "regions": [{"name": "full"}]}

        def fake_report(**kwargs):
            self.assertTrue(Path(kwargs["metrics"]).exists())
            self.assertIn("baseline-metrics.json", str(kwargs["metrics"]))
            report = Path(kwargs["out_dir"]) / "verification-report.md"
            report.write_text("# report\n", encoding="utf-8")
            return {"validation": {"errors": []}, "report": str(report), "assessment": "VERIFIED_WITH_DEVIATIONS"}

        result = module.verify_ios(
            project_dir=self.project_dir,
            target="Profile Screen",
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            assets=self.assets,
            plan=self.plan,
            app=self.app,
            bundle_id="com.example.app",
            build_command="xcodebuild -scheme App",
            execute=True,
            runner=fake_runner,
            compare=fake_compare,
            report=fake_report,
            xcrun_available=lambda: True,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertEqual(result["assessment"], "VERIFIED_WITH_DEVIATIONS")
        self.assertTrue(Path(result["platform_screenshot"]).exists())
        self.assertTrue(Path(result["metrics"]).exists())
        self.assertTrue(Path(result["report"]).exists())
        self.assertTrue(any("xcrun simctl io booted screenshot" in call for call in calls))

    def test_cli_dry_run_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--target",
                "Profile Screen",
                "--visual-contract",
                str(self.contract),
                "--baseline-screenshot",
                str(self.baseline),
                "--assets",
                str(self.assets),
                "--plan",
                str(self.plan),
                "--app",
                str(self.app),
                "--bundle-id",
                "com.example.app",
                "--dry-run",
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["validation"]["errors"], [])


if __name__ == "__main__":
    unittest.main()
