from __future__ import annotations

import importlib.util
import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_provider.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_provider", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project_dir = self.root / "project"
        self.project_dir.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()

    def write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_build_dry_run_request_uses_visual_workspace(self) -> None:
        module = load_module()

        result = module.build_dry_run_request(
            project_dir=self.project_dir,
            home_dir=self.home,
            topic="Checkout Flow",
            prompt="Design a mobile checkout confirmation screen.",
            refs=[],
            date="2026-05-31",
        )

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["provider"]["name"], "builtin")
        self.assertEqual(result["request"]["aspect_ratio"], "3:4")
        self.assertEqual(result["request"]["prompt"], "Design a mobile checkout confirmation screen.")
        self.assertIn("2026-05-31-checkout-flow", result["workspace"])
        self.assertEqual(result["outputs"]["image"], str(Path(result["workspace"]) / "generated-mockup.png"))
        self.assertEqual(result["outputs"]["metadata"], str(Path(result["workspace"]) / "generated-mockup.png.json"))
        self.assertEqual(result["validation"]["errors"], [])

    def test_openai_config_maps_endpoint_style_without_secret(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "openai", "model": "gpt-image-2"},
                "providers": {"openai": {"api_key": "sk-project-secret"}},
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            result = module.build_dry_run_request(
                project_dir=self.project_dir,
                home_dir=self.home,
                topic="Profile",
                prompt="Design a profile screen.",
                refs=[],
                date="2026-05-31",
            )

        self.assertEqual(result["provider"]["name"], "openai")
        self.assertEqual(result["provider"]["endpoint_style"], "openai-images")
        self.assertEqual(result["provider"]["model"], "gpt-image-2")
        self.assertTrue(result["provider"]["has_api_key"])
        self.assertNotIn("sk-project-secret", json.dumps(result))
        self.assertEqual(result["validation"]["errors"], [])

    def test_missing_reference_is_reported(self) -> None:
        module = load_module()

        result = module.build_dry_run_request(
            project_dir=self.project_dir,
            home_dir=self.home,
            topic="Settings",
            prompt="Design a settings screen.",
            refs=[str(self.project_dir / "missing.png")],
            date="2026-05-31",
        )

        self.assertIn("reference not found", result["validation"]["errors"][0])

    def test_cli_dry_run_writes_metadata(self) -> None:
        metadata_path = self.root / "metadata.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--home-dir",
                str(self.home),
                "--topic",
                "Search Screen",
                "--prompt",
                "Design a mobile search screen.",
                "--date",
                "2026-05-31",
                "--metadata",
                str(metadata_path),
                "--dry-run",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["request"]["prompt"], "Design a mobile search screen.")
        self.assertIn("2026-05-31-search-screen", completed.stdout)

    def test_cli_requires_explicit_mode(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--home-dir",
                str(self.home),
                "--topic",
                "Search Screen",
                "--prompt",
                "Design a mobile search screen.",
            ],
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("Use --dry-run", completed.stderr)
        self.assertIn("--execute", completed.stderr)

    def test_build_openai_images_payload_for_proxy(self) -> None:
        module = load_module()
        request = {
            "provider": {
                "name": "proxy",
                "endpoint_style": "openai-images",
                "model": "gpt-image-2",
                "base_url": "https://relay.example.test/v1",
                "has_api_key": True,
                "api_key_source": "user_config:providers.proxy.api_key",
            },
            "request": {
                "prompt": "Design a mobile profile screen.",
                "size": "1024x1536",
                "quality": "high",
                "timeout_seconds": 180,
                "refs": [],
            },
        }

        payload = module.build_openai_images_payload(request)

        self.assertEqual(payload["model"], "gpt-image-2")
        self.assertEqual(payload["prompt"], "Design a mobile profile screen.")
        self.assertEqual(payload["size"], "1024x1536")
        self.assertEqual(payload["quality"], "high")
        self.assertEqual(payload["response_format"], "b64_json")

    def test_execute_openai_images_writes_image_and_response_metadata_without_secret(self) -> None:
        module = load_module()
        image_path = self.root / "generated-mockup.png"
        metadata_path = self.root / "generated-mockup.png.json"
        request = {
            "dry_run": False,
            "provider": {
                "name": "proxy",
                "endpoint_style": "openai-images",
                "model": "gpt-image-2",
                "base_url": "https://relay.example.test/v1",
                "has_api_key": True,
                "api_key_source": "user_config:providers.proxy.api_key",
            },
            "request": {
                "prompt": "Design a mobile profile screen.",
                "size": "1024x1536",
                "quality": "high",
                "timeout_seconds": 180,
                "refs": [],
            },
            "outputs": {
                "image": str(image_path),
                "metadata": str(metadata_path),
            },
            "validation": {"errors": [], "warnings": []},
        }
        png_bytes = b"\x89PNG\r\n\x1a\nfake"
        calls = []

        def fake_transport(url, *, payload, api_key, timeout):
            calls.append({"url": url, "payload": payload, "api_key": api_key, "timeout": timeout})
            return {"data": [{"b64_json": base64.b64encode(png_bytes).decode("ascii")}], "created": 1}

        result = module.execute_openai_images_request(
            request,
            api_key="proxy-secret",
            transport=fake_transport,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertEqual(image_path.read_bytes(), png_bytes)
        self.assertEqual(calls[0]["url"], "https://relay.example.test/v1/images/generations")
        self.assertEqual(calls[0]["api_key"], "proxy-secret")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(metadata["provider"]["name"], "proxy")
        self.assertNotIn("proxy-secret", json.dumps(metadata))


if __name__ == "__main__":
    unittest.main()
