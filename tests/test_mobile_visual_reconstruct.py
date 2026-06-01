from __future__ import annotations

import importlib.util
import base64
import io
import json
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_reconstruct.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_reconstruct", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualReconstructTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workspace = Path(self.tmp.name) / "visual"
        self.workspace.mkdir()
        self.mockup = self.workspace / "generated-mockup.png"
        self.mockup.write_bytes(b"png")
        self.metadata = self.workspace / "generated-mockup.png.json"
        self.metadata.write_text(
            json.dumps(
                {
                    "workspace": str(self.workspace),
                    "provider": {"name": "proxy", "model": "gpt-image-2"},
                    "request": {
                        "prompt": "Design a clean profile screen.",
                        "size": "1024x1536",
                        "aspect_ratio": "3:4",
                    },
                    "outputs": {"image": str(self.mockup), "metadata": str(self.metadata)},
                    "validation": {"errors": [], "warnings": []},
                }
            ),
            encoding="utf-8",
        )
        self.contract = self.workspace / "visual-contract.md"
        self.contract.write_text(
            "# Profile Visual Contract\n\n## HTML Baseline\n\n- Not recorded yet.\n",
            encoding="utf-8",
        )

    def test_create_reconstruction_bundle_writes_prompt_and_baseline(self) -> None:
        module = load_module()

        result = module.create_reconstruction_bundle(metadata_path=self.metadata)

        prompt_path = self.workspace / "reconstruction-prompt.md"
        baseline_path = self.workspace / "baseline.html"
        self.assertEqual(result["prompt"], str(prompt_path.resolve()))
        self.assertEqual(result["baseline_html"], str(baseline_path.resolve()))
        self.assertTrue(prompt_path.exists())
        self.assertTrue(baseline_path.exists())
        prompt = prompt_path.read_text(encoding="utf-8")
        html = baseline_path.read_text(encoding="utf-8")
        self.assertIn("Design a clean profile screen.", prompt)
        self.assertIn("Code these elements with HTML/CSS", prompt)
        self.assertIn("mobile safe area", prompt)
        self.assertIn("data-mobile-superpowers-reconstruction", html)
        self.assertIn("Generated mockup", html)
        self.assertEqual(result["validation"]["errors"], [])

    def test_contract_is_updated_with_reconstruction_artifacts(self) -> None:
        module = load_module()

        module.create_reconstruction_bundle(metadata_path=self.metadata)

        text = self.contract.read_text(encoding="utf-8")
        self.assertIn("Reconstruction prompt", text)
        self.assertIn("reconstruction-prompt.md", text)
        self.assertIn("baseline.html", text)

    def test_project_constraints_are_included_in_prompt_and_contract(self) -> None:
        constraints = self.workspace / "project-constraints.md"
        constraints.write_text(
            "# Mobile Project Constraints\n\n- Use `CommonText` for visible text.\n- Forbidden: `Text(`.\n",
            encoding="utf-8",
        )
        module = load_module()

        result = module.create_reconstruction_bundle(metadata_path=self.metadata, project_constraints=constraints)

        prompt = Path(result["prompt"]).read_text(encoding="utf-8")
        contract = self.contract.read_text(encoding="utf-8")
        self.assertIn("Project Constraints", prompt)
        self.assertIn("CommonText", prompt)
        self.assertIn('data-platform-component="CommonText"', prompt)
        self.assertIn("project-constraints.md", contract)
        self.assertEqual(result["project_constraints"], str(constraints.resolve()))

    def test_existing_baseline_is_not_overwritten_without_force(self) -> None:
        baseline = self.workspace / "baseline.html"
        baseline.write_text("custom baseline", encoding="utf-8")
        module = load_module()

        module.create_reconstruction_bundle(metadata_path=self.metadata)

        self.assertEqual(baseline.read_text(encoding="utf-8"), "custom baseline")

    def test_force_overwrites_baseline(self) -> None:
        baseline = self.workspace / "baseline.html"
        baseline.write_text("custom baseline", encoding="utf-8")
        module = load_module()

        module.create_reconstruction_bundle(metadata_path=self.metadata, force=True)

        self.assertIn("data-mobile-superpowers-reconstruction", baseline.read_text(encoding="utf-8"))

    def test_cli_writes_json_result(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--metadata",
                str(self.metadata),
                "--json",
            ],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertIn("reconstruction-prompt.md", payload["prompt"])
        self.assertEqual(payload["validation"]["errors"], [])

    def test_build_vision_chat_payload_includes_image_and_prompt(self) -> None:
        module = load_module()
        prompt_path = self.workspace / "reconstruction-prompt.md"
        prompt_path.write_text("Reconstruct this mockup.", encoding="utf-8")

        payload = module.build_vision_chat_payload(
            prompt_path=prompt_path,
            mockup_path=self.mockup,
            model="gpt-5.5",
        )

        self.assertEqual(payload["model"], "gpt-5.5")
        content = payload["messages"][0]["content"]
        self.assertEqual(content[0]["type"], "text")
        self.assertIn("Reconstruct this mockup.", content[0]["text"])
        self.assertEqual(content[1]["type"], "image_url")
        self.assertIn("data:image/png;base64,", content[1]["image_url"]["url"])

    def test_execute_vision_reconstruction_writes_html_without_secret(self) -> None:
        module = load_module()
        prompt_path = self.workspace / "reconstruction-prompt.md"
        prompt_path.write_text("Reconstruct this mockup.", encoding="utf-8")
        baseline_path = self.workspace / "baseline.html"
        calls = []

        def fake_transport(url, *, payload, api_key, timeout):
            calls.append({"url": url, "payload": payload, "api_key": api_key, "timeout": timeout})
            return {
                "choices": [
                    {
                        "message": {
                            "content": "```html\n<!doctype html><html data-real-reconstruction><body>ok</body></html>\n```"
                        }
                    }
                ]
            }

        result = module.execute_vision_reconstruction(
            prompt_path=prompt_path,
            mockup_path=self.mockup,
            baseline_path=baseline_path,
            base_url="https://relay.example.test/v1",
            api_key="vision-secret",
            model="gpt-5.5",
            transport=fake_transport,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertIn("data-real-reconstruction", baseline_path.read_text(encoding="utf-8"))
        self.assertEqual(calls[0]["url"], "https://relay.example.test/v1/chat/completions")
        self.assertEqual(calls[0]["api_key"], "vision-secret")
        self.assertNotIn("vision-secret", json.dumps(result))

    def test_execute_vision_reconstruction_accepts_content_blocks(self) -> None:
        module = load_module()
        prompt_path = self.workspace / "reconstruction-prompt.md"
        prompt_path.write_text("Reconstruct this mockup.", encoding="utf-8")
        baseline_path = self.workspace / "baseline.html"

        def fake_transport(url, *, payload, api_key, timeout):
            return {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "```html\n<html data-content-blocks><body>ok</body></html>\n```"}
                            ]
                        }
                    }
                ]
            }

        result = module.execute_vision_reconstruction(
            prompt_path=prompt_path,
            mockup_path=self.mockup,
            baseline_path=baseline_path,
            base_url="https://relay.example.test/v1",
            api_key="vision-secret",
            model="gpt-5.5",
            transport=fake_transport,
        )

        self.assertEqual(result["validation"]["errors"], [])
        self.assertIn("data-content-blocks", baseline_path.read_text(encoding="utf-8"))

    def test_execute_vision_reconstruction_reports_http_errors(self) -> None:
        module = load_module()
        prompt_path = self.workspace / "reconstruction-prompt.md"
        prompt_path.write_text("Reconstruct this mockup.", encoding="utf-8")
        baseline_path = self.workspace / "baseline.html"

        def failing_transport(url, *, payload, api_key, timeout):
            raise urllib.error.HTTPError(
                url,
                503,
                "Service Unavailable",
                hdrs={},
                fp=io.BytesIO(b'{"error":{"message":"model overloaded"}}'),
            )

        result = module.execute_vision_reconstruction(
            prompt_path=prompt_path,
            mockup_path=self.mockup,
            baseline_path=baseline_path,
            base_url="https://relay.example.test/v1",
            api_key="vision-secret",
            model="gpt-5.5",
            transport=failing_transport,
        )

        self.assertFalse(baseline_path.exists())
        self.assertIn("HTTP 503", result["validation"]["errors"][0])
        self.assertIn("model overloaded", result["validation"]["errors"][0])
        self.assertNotIn("vision-secret", json.dumps(result))

    def test_default_vision_model_is_gpt_5_5(self) -> None:
        module = load_module()

        self.assertEqual(module.DEFAULT_VISION_MODEL, "gpt-5.5")

    def test_cli_uses_configured_vision_model_when_flag_is_absent(self) -> None:
        project_dir = self.workspace / "project"
        config_dir = project_dir / ".mobile-superpowers"
        config_dir.mkdir(parents=True)
        config_dir.joinpath("config.json").write_text(
            json.dumps(
                {
                    "visual": {"provider": "proxy", "vision_model": "gpt-5.4"},
                    "providers": {
                        "proxy": {
                            "api_key": "proxy-secret",
                            "base_url": "https://relay.example.test/v1",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        runner = self.workspace / "run_cli_with_fake_transport.py"
        runner.write_text(
            f"""
import importlib.util
import json
import sys
from pathlib import Path

script = Path({str(SCRIPT)!r})
spec = importlib.util.spec_from_file_location("mobile_visual_reconstruct", script)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def fake_transport(url, *, payload, api_key, timeout):
    return {{"choices": [{{"message": {{"content": "<html><body>{{}}</body></html>".format(payload["model"])}}}}]}}

module.chat_completions_transport = fake_transport
sys.argv = [
    str(script),
    "--metadata", {str(self.metadata)!r},
    "--project-dir", {str(project_dir)!r},
    "--force",
    "--execute",
    "--json",
]
raise SystemExit(module.main())
""",
            encoding="utf-8",
        )

        completed = subprocess.run(
            [sys.executable, str(runner)],
            check=True,
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["vision_execution"]["provider"]["model"], "gpt-5.4")


if __name__ == "__main__":
    unittest.main()
