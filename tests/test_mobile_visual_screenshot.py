from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_screenshot.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_screenshot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualScreenshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "workspace"
        self.workspace.mkdir()
        self.baseline = self.workspace / "baseline.html"
        self.baseline.write_text("<!doctype html><title>Baseline</title><main>Hello</main>", encoding="utf-8")
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text(
            "\n".join(
                [
                    "# Demo Visual Contract",
                    "",
                    "## HTML Baseline",
                    "",
                    "- Baseline HTML: `baseline.html`",
                    "",
                    "## Screenshot And Metrics",
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

    def test_build_browser_command_uses_mobile_viewport_and_file_url(self) -> None:
        module = load_module()

        command = module.build_browser_command(
            browser_cmd="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            baseline_html=self.baseline,
            screenshot_path=self.workspace / "baseline-screenshot.png",
            width=390,
            height=844,
        )

        joined = " ".join(command)
        self.assertIn("--headless", joined)
        self.assertIn("--window-size=390,844", joined)
        self.assertIn("--virtual-time-budget=12000", joined)
        self.assertIn("--screenshot=", joined)
        self.assertIn(self.baseline.resolve().as_uri(), command[-1])

    def test_capture_screenshot_with_fake_runner_writes_metadata_and_contract(self) -> None:
        module = load_module()
        calls = []

        def fake_runner(command, *, timeout):
            calls.append((command, timeout))
            output = self.workspace / "baseline-screenshot.png"
            output.write_bytes(b"png")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        result = module.capture_screenshot(
            baseline_html=self.baseline,
            browser_cmd="/bin/echo",
            width=390,
            height=844,
            runner=fake_runner,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertEqual(calls[0][1], 30)
        self.assertTrue((self.workspace / "baseline-screenshot.png").exists())
        self.assertTrue((self.workspace / "baseline-screenshot.json").exists())
        contract_text = self.contract.read_text(encoding="utf-8")
        self.assertIn("- Baseline screenshot: `", contract_text)
        self.assertIn("baseline-screenshot.png", contract_text)

    def test_dry_run_returns_command_without_creating_screenshot(self) -> None:
        module = load_module()

        result = module.capture_screenshot(
            baseline_html=self.baseline,
            browser_cmd="/bin/echo",
            dry_run=True,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertIn("/bin/echo", result["command"][0])
        self.assertFalse((self.workspace / "baseline-screenshot.png").exists())

    def test_missing_browser_reports_error(self) -> None:
        module = load_module()

        result = module.capture_screenshot(
            baseline_html=self.baseline,
            browser_cmd="/does/not/exist",
        )

        self.assertIn("browser not found", result["validation"]["errors"][0])

    def test_cli_dry_run_prints_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--baseline",
                str(self.baseline),
                "--browser",
                "/bin/echo",
                "--dry-run",
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["viewport"], {"width": 390, "height": 844})

    def test_default_screenshot_path_matches_baseline_workspace(self) -> None:
        module = load_module()

        result = module.capture_screenshot(
            baseline_html=self.baseline,
            browser_cmd="/bin/echo",
            dry_run=True,
        )

        self.assertEqual(result["screenshot"], str((self.workspace / "baseline-screenshot.png").resolve()))
        self.assertEqual(result["metadata"], str((self.workspace / "baseline-screenshot.json").resolve()))


if __name__ == "__main__":
    unittest.main()
