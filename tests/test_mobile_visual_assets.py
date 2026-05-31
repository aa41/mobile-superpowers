from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_assets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualAssetsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "visual"
        self.workspace.mkdir()
        self.baseline = self.workspace / "baseline.html"
        self.baseline.write_text(
            """
<!doctype html>
<html>
<body>
  <img class="avatar" src="./assets/avatar.png" alt="Profile portrait">
  <div data-asset-strategy="regenerate" data-asset-name="hero-illustration"></div>
  <div class="placeholder">Generated mockup reference</div>
</body>
</html>
""",
            encoding="utf-8",
        )
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text(
            "# Profile Visual Contract\n\n## Asset Strategy\n\n- Not recorded yet.\n\n## Platform Handoff Notes\n\n- Not recorded yet.\n",
            encoding="utf-8",
        )

    def test_analyze_assets_writes_manifest_and_contract(self) -> None:
        module = load_module()

        result = module.analyze_assets(baseline=self.baseline)

        assets_path = self.workspace / "assets.json"
        self.assertEqual(result["assets"], str(assets_path.resolve()))
        self.assertTrue(assets_path.exists())
        payload = json.loads(assets_path.read_text(encoding="utf-8"))
        strategies = {asset["strategy"] for asset in payload["assets"]}
        self.assertIn("image_asset", strategies)
        self.assertIn("regenerate", strategies)
        self.assertIn("review_placeholder", strategies)
        contract = self.contract.read_text(encoding="utf-8")
        self.assertIn("assets.json", contract)
        self.assertIn("hero-illustration", contract)
        self.assertIn("Profile portrait", contract)

    def test_cli_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--baseline",
                str(self.baseline),
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["validation"]["errors"], [])
        self.assertIn("assets.json", payload["assets"])


if __name__ == "__main__":
    unittest.main()
