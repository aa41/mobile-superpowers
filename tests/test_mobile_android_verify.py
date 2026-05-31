from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_android_verify.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_android_verify", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileAndroidVerifyTests(unittest.TestCase):
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
        self.apk = self.project_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        self.apk.parent.mkdir(parents=True)
        self.apk.write_bytes(b"apk")

    def test_dry_run_returns_adb_screenshot_compare_report_plan(self) -> None:
        module = load_module()

        result = module.verify_android(
            project_dir=self.project_dir,
            target="Profile Screen",
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            assets=self.assets,
            plan=self.plan,
            apk=self.apk,
            launch_activity="com.example/.MainActivity",
            build_command="./gradlew assembleDebug",
            dry_run=True,
        )

        self.assertTrue(result["dry_run"])
        self.assertIn(["./gradlew", "assembleDebug"], result["commands"])
        self.assertIn(["adb", "install", "-r", str(self.apk.resolve())], result["commands"])
        self.assertIn(["adb", "exec-out", "screencap", "-p"], result["commands"])
        self.assertIn("platform-screenshot.png", result["platform_screenshot"])
        self.assertIn("platform-metrics.json", result["metrics"])
        self.assertIn("verification-report.md", result["report"])

    def test_execute_with_fake_adapters_runs_pipeline(self) -> None:
        module = load_module()
        calls: list[str] = []

        def fake_runner(command, *, cwd=None, timeout=None, stdout=None):
            calls.append(" ".join(command))
            if command[:4] == ["adb", "exec-out", "screencap", "-p"]:
                return subprocess.CompletedProcess(command, 0, stdout=b"png", stderr=b"")
            return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

        def fake_compare(**kwargs):
            metrics = Path(kwargs["out_dir"]) / "platform-metrics.json"
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
            report = Path(kwargs["out_dir"]) / "verification-report.md"
            report.write_text("# report\n", encoding="utf-8")
            return {"validation": {"errors": []}, "report": str(report), "assessment": "VERIFIED_WITH_DEVIATIONS"}

        result = module.verify_android(
            project_dir=self.project_dir,
            target="Profile Screen",
            visual_contract=self.contract,
            baseline_screenshot=self.baseline,
            assets=self.assets,
            plan=self.plan,
            apk=self.apk,
            launch_activity="com.example/.MainActivity",
            build_command="./gradlew assembleDebug",
            execute=True,
            runner=fake_runner,
            compare=fake_compare,
            report=fake_report,
            adb_available=lambda: True,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertEqual(result["assessment"], "VERIFIED_WITH_DEVIATIONS")
        self.assertTrue(Path(result["platform_screenshot"]).exists())
        self.assertEqual(Path(result["platform_screenshot"]).read_bytes(), b"png")
        self.assertTrue(Path(result["metrics"]).exists())
        self.assertTrue(Path(result["report"]).exists())
        self.assertTrue(any("adb exec-out screencap -p" in call for call in calls))

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
                "--apk",
                str(self.apk),
                "--launch-activity",
                "com.example/.MainActivity",
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
