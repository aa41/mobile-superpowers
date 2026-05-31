from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_config.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_config", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualConfigTests(unittest.TestCase):
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

    def test_project_config_resolves_provider_without_exposing_secret(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {
                    "provider": "openai",
                    "model": "gpt-image-2",
                    "output_dir": "~/visual-out",
                },
                "providers": {"openai": {"api_key": "sk-project-secret"}},
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["provider"], "openai")
        self.assertEqual(result["visual"]["model"], "gpt-image-2")
        self.assertEqual(result["visual"]["vision_model"], "gpt-5.5")
        self.assertEqual(result["provider"]["api_key_source"], "project_config:providers.openai.api_key")
        self.assertTrue(result["provider"]["has_api_key"])
        self.assertNotIn("sk-project-secret", json.dumps(result))
        self.assertEqual(result["validation"]["errors"], [])

    def test_vision_model_can_be_configured_separately_from_image_model(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {
                    "provider": "proxy",
                    "model": "gpt-image-2",
                    "vision_model": "gpt-5.4",
                },
                "providers": {
                    "proxy": {
                        "api_key": "proxy-secret",
                        "base_url": "https://relay.example.test/v1",
                    }
                },
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["model"], "gpt-image-2")
        self.assertEqual(result["visual"]["vision_model"], "gpt-5.4")
        self.assertNotIn("proxy-secret", json.dumps(result))

    def test_environment_overrides_vision_model(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {
                    "provider": "proxy",
                    "model": "gpt-image-2",
                    "vision_model": "gpt-5.4",
                },
                "providers": {
                    "proxy": {
                        "api_key": "proxy-secret",
                        "base_url": "https://relay.example.test/v1",
                    }
                },
            },
        )

        with mock.patch.dict(os.environ, {"MOBILE_VISUAL_VISION_MODEL": "gpt-5.5"}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["model"], "gpt-image-2")
        self.assertEqual(result["visual"]["vision_model"], "gpt-5.5")

    def test_environment_overrides_project_config_and_uses_provider_key_fallback(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "openai", "model": "gpt-image-2", "quality": "medium"},
                "providers": {"openai": {"api_key": "sk-project-secret"}},
            },
        )

        env = {
            "MOBILE_VISUAL_PROVIDER": "gemini",
            "MOBILE_VISUAL_MODEL": "gemini-2.5-flash-image",
            "MOBILE_VISUAL_QUALITY": "high",
            "GEMINI_API_KEY": "gemini-secret",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["provider"], "gemini")
        self.assertEqual(result["visual"]["model"], "gemini-2.5-flash-image")
        self.assertEqual(result["visual"]["quality"], "high")
        self.assertEqual(result["provider"]["api_key_source"], "env:GEMINI_API_KEY")
        self.assertNotIn("gemini-secret", json.dumps(result))
        self.assertEqual(result["validation"]["errors"], [])

    def test_user_config_is_used_when_project_config_is_absent(self) -> None:
        self.write_json(
            self.home / ".config" / "mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "proxy", "model": "custom-image-model"},
                "providers": {
                    "proxy": {
                        "api_key": "proxy-secret",
                        "base_url": "https://relay.example.test/v1",
                        "endpoint_style": "openai-images",
                    }
                },
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["provider"], "proxy")
        self.assertEqual(result["provider"]["base_url"], "https://relay.example.test/v1")
        self.assertEqual(result["provider"]["endpoint_style"], "openai-images")
        self.assertEqual(result["provider"]["api_key_source"], "user_config:providers.proxy.api_key")
        self.assertEqual(result["validation"]["errors"], [])

    def test_resolved_secret_value_is_available_only_in_private_config(self) -> None:
        self.write_json(
            self.home / ".config" / "mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "proxy"},
                "providers": {
                    "proxy": {
                        "api_key": "proxy-secret",
                        "base_url": "https://relay.example.test/v1",
                    }
                },
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            secret = module.resolve_secret_value(
                "user_config:providers.proxy.api_key",
                project_dir=self.project_dir,
                home_dir=self.home,
            )
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(secret, "proxy-secret")
        self.assertNotIn("proxy-secret", json.dumps(result))

    def test_proxy_requires_base_url(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "proxy", "model": "custom-image-model"},
                "providers": {"proxy": {"api_key": "proxy-secret"}},
            },
        )

        with mock.patch.dict(os.environ, {}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertIn("provider proxy requires base_url", result["validation"]["errors"])

    def test_imagen_uses_gemini_api_key_fallback(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {"visual": {"provider": "imagen", "model": "imagen-4.0-generate-001"}},
        )

        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-secret"}, clear=True):
            module = load_module()
            result = module.resolve_config(project_dir=self.project_dir, home_dir=self.home)

        self.assertEqual(result["visual"]["provider"], "imagen")
        self.assertEqual(result["provider"]["endpoint_style"], "imagen-generate-images")
        self.assertEqual(result["provider"]["api_key_source"], "env:GEMINI_API_KEY")
        self.assertNotIn("gemini-secret", json.dumps(result))
        self.assertEqual(result["validation"]["errors"], [])

    def test_cli_prints_resolved_json(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "openai"},
                "providers": {"openai": {"api_key": "sk-project-secret"}},
            },
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--home-dir",
                str(self.home),
                "--print",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["visual"]["provider"], "openai")
        self.assertNotIn("sk-project-secret", completed.stdout)

    def test_cli_check_reports_validation_without_secret(self) -> None:
        self.write_json(
            self.project_dir / ".mobile-superpowers" / "config.json",
            {
                "visual": {"provider": "proxy", "model": "custom-image-model"},
                "providers": {"proxy": {"api_key": "proxy-secret"}},
            },
        )

        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-dir",
                str(self.project_dir),
                "--home-dir",
                str(self.home),
                "--check",
            ],
            text=True,
            capture_output=True,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("provider=proxy", completed.stdout)
        self.assertIn("ERROR: provider proxy requires base_url", completed.stdout)
        self.assertNotIn("proxy-secret", completed.stdout)


if __name__ == "__main__":
    unittest.main()
