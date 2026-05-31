from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "mobile_visual_deps.py"


def load_module():
    spec = importlib.util.spec_from_file_location("mobile_visual_deps", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MobileVisualDepsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def test_default_venv_path_uses_user_cache(self) -> None:
        module = load_module()

        self.assertEqual(
            module.default_venv_path(home_dir=self.home),
            self.home / ".cache" / "mobile-superpowers" / "visual-venv",
        )

    def test_check_reports_missing_when_venv_python_absent(self) -> None:
        module = load_module()

        result = module.check_deps(venv_path=self.home / "missing-venv")

        self.assertFalse(result["ok"])
        self.assertIn("venv python not found", result["validation"]["errors"][0])

    def test_install_runs_venv_creation_then_pip_install(self) -> None:
        module = load_module()
        calls = []
        venv_path = self.home / "visual-venv"
        python_path = module.venv_python(venv_path)

        def fake_runner(command, *, text, capture_output):
            calls.append(command)
            if command[1:3] == ["-m", "venv"]:
                python_path.parent.mkdir(parents=True, exist_ok=True)
                python_path.write_text("# fake python", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

        result = module.install_deps(venv_path=venv_path, python_executable="/custom/python", runner=fake_runner)

        self.assertTrue(result["ok"])
        self.assertEqual(calls[0], ["/custom/python", "-m", "venv", str(venv_path)])
        self.assertEqual(calls[1], [str(python_path), "-m", "pip", "install", "Pillow"])

    def test_cli_check_outputs_json(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--home-dir",
                str(self.home),
                "--check",
                "--json",
            ],
            text=True,
            capture_output=True,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(payload["ok"])
        self.assertIn("visual-venv", payload["venv"])


if __name__ == "__main__":
    unittest.main()
