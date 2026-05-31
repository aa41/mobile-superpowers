#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from functools import partial
from pathlib import Path
from typing import Any, Callable
from urllib import request
from urllib.error import HTTPError, URLError


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mobile_ui_verification_report import create_verification_report
from mobile_visual_compare import compare_visuals
from mobile_visual_screenshot import (
    DEFAULT_HEIGHT,
    DEFAULT_TIMEOUT,
    DEFAULT_VIRTUAL_TIME_BUDGET,
    DEFAULT_WIDTH,
    browser_exists,
    discover_browser,
)


Runner = Callable[..., subprocess.CompletedProcess]


def read_http_json(url: str, *, method: str = "GET", timeout: float = 2) -> dict[str, Any]:
    req = request.Request(url, method=method)
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_http_json(url: str, *, method: str = "GET", timeout: float = 2, attempts: int = 30) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return read_http_json(url, method=method, timeout=timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            time.sleep(0.2)
    raise RuntimeError(f"unable to read {url}: {last_error}")


class CdpClient:
    def __init__(self, websocket_url: str):
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(websocket_url)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        path = parsed.path
        if parsed.query:
            path += "?" + parsed.query
        sock = socket.create_connection((parsed.hostname, parsed.port or 80), timeout=5)
        request_text = "\r\n".join(
            [
                f"GET {path} HTTP/1.1",
                f"Host: {parsed.hostname}:{parsed.port or 80}",
                "Upgrade: websocket",
                "Connection: Upgrade",
                f"Sec-WebSocket-Key: {key}",
                "Sec-WebSocket-Version: 13",
                "\r\n",
            ]
        )
        sock.sendall(request_text.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            sock.close()
            raise RuntimeError("Chrome DevTools websocket handshake failed")
        self._socket = sock
        self._next_id = 0

    def close(self) -> None:
        self._socket.close()

    def send(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        self._write_json({"id": message_id, "method": method, "params": params or {}})
        while True:
            message = self._read_json()
            if message.get("id") != message_id:
                continue
            if "error" in message:
                raise RuntimeError(f"CDP {method} failed: {message['error']}")
            return message.get("result", {})

    def _write_json(self, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = bytearray([0x81])
        length = len(raw)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(length.to_bytes(2, "big"))
        else:
            header.append(0x80 | 127)
            header.extend(length.to_bytes(8, "big"))
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(raw))
        self._socket.sendall(bytes(header) + mask + masked)

    def _read_exact(self, length: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self._socket.recv(length - len(chunks))
            if not chunk:
                raise RuntimeError("CDP websocket closed")
            chunks.extend(chunk)
        return bytes(chunks)

    def _read_json(self) -> dict[str, Any]:
        first, second = self._read_exact(2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = int.from_bytes(self._read_exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._read_exact(8), "big")
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 8:
            raise RuntimeError("CDP websocket closed")
        if opcode != 1:
            return self._read_json()
        return json.loads(payload.decode("utf-8"))


def find_open_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def build_url_screenshot_command(
    *,
    browser_cmd: str,
    url: str,
    screenshot_path: Path,
    width: int,
    height: int,
    virtual_time_budget: int = DEFAULT_VIRTUAL_TIME_BUDGET,
) -> list[str]:
    command = [
        browser_cmd,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-first-run",
        "--no-default-browser-check",
        f"--window-size={width},{height}",
    ]
    if virtual_time_budget > 0:
        command.append(f"--virtual-time-budget={virtual_time_budget}")
    command.extend([f"--screenshot={screenshot_path}", url])
    return command


def capture_url_screenshot(
    *,
    url: str,
    screenshot_path: Path | str,
    browser_cmd: str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    timeout: int = DEFAULT_TIMEOUT,
    virtual_time_budget: int = DEFAULT_VIRTUAL_TIME_BUDGET,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    screenshot_path = Path(screenshot_path).expanduser().resolve()
    browser_cmd = browser_cmd or discover_browser()
    errors: list[str] = []
    if not browser_cmd or not browser_exists(browser_cmd):
        errors.append(f"browser not found: {browser_cmd or 'none'}")
    command = build_url_screenshot_command(
        browser_cmd=browser_cmd or "",
        url=url,
        screenshot_path=screenshot_path,
        width=width,
        height=height,
        virtual_time_budget=virtual_time_budget,
    )
    result = {
        "url": url,
        "screenshot": str(screenshot_path),
        "browser": browser_cmd,
        "viewport": {"width": width, "height": height},
        "virtual_time_budget": virtual_time_budget,
        "command": command,
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    completed = runner(command, timeout=timeout)
    if completed.returncode != 0:
        result["validation"]["errors"].append(f"browser exited with code {completed.returncode}")
    elif not screenshot_path.exists():
        result["validation"]["errors"].append(f"screenshot was not created: {screenshot_path}")
    return result


def capture_url_screenshot_cdp(
    *,
    url: str,
    screenshot_path: Path | str,
    browser_cmd: str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    timeout: int = DEFAULT_TIMEOUT,
    virtual_time_budget: int = DEFAULT_VIRTUAL_TIME_BUDGET,
) -> dict[str, Any]:
    screenshot_path = Path(screenshot_path).expanduser().resolve()
    browser_cmd = browser_cmd or discover_browser()
    port = find_open_port()
    errors: list[str] = []
    if not browser_cmd or not browser_exists(browser_cmd):
        errors.append(f"browser not found: {browser_cmd or 'none'}")
    command = [browser_cmd or ""]
    result = {
        "url": url,
        "screenshot": str(screenshot_path),
        "browser": browser_cmd,
        "viewport": {"width": width, "height": height},
        "virtual_time_budget": virtual_time_budget,
        "mode": "cdp",
        "command": command,
        "validation": {"errors": errors, "warnings": []},
    }
    if errors:
        return result
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mobile-superpowers-cdp-") as user_data_dir:
        command = [
            browser_cmd or "",
            f"--remote-debugging-port={port}",
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={user_data_dir}",
            "about:blank",
        ]
        result["command"] = command
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        client = None
        try:
            target = wait_for_http_json(
                f"http://127.0.0.1:{port}/json/new?{url}",
                method="PUT",
                attempts=max(5, timeout * 2),
            )
            client = CdpClient(target["webSocketDebuggerUrl"])
            client.send("Page.enable")
            client.send("Runtime.enable")
            client.send(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": True,
                    "screenWidth": width,
                    "screenHeight": height,
                },
            )
            client.send("Emulation.setTouchEmulationEnabled", {"enabled": True})
            client.send("Page.navigate", {"url": url})
            deadline = time.time() + max(1, virtual_time_budget / 1000)
            while time.time() < deadline:
                dom_ready = client.send(
                    "Runtime.evaluate",
                    {
                        "expression": "Boolean(document.querySelector('flutter-view'))",
                        "returnByValue": True,
                    },
                )
                if dom_ready.get("result", {}).get("value"):
                    break
                time.sleep(0.25)
            time.sleep(0.75)
            viewport = client.send(
                "Runtime.evaluate",
                {
                    "expression": "JSON.stringify({innerWidth,innerHeight,devicePixelRatio,view:document.querySelector('flutter-view')?.getBoundingClientRect().toJSON?.()})",
                    "returnByValue": True,
                },
            )
            result["runtime_viewport"] = json.loads(viewport.get("result", {}).get("value") or "{}")
            shot = client.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False, "fromSurface": True})
            screenshot_path.write_bytes(base64.b64decode(shot["data"]))
            if not screenshot_path.exists():
                result["validation"]["errors"].append(f"screenshot was not created: {screenshot_path}")
            return result
        except Exception as exc:
            result["validation"]["errors"].append(str(exc))
            return result
        finally:
            if client:
                client.close()
            stop_process(process)


def start_static_server(*, directory: Path, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(directory),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_process(process: subprocess.Popen | None) -> None:
    if not process:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def default_out_dir(project_dir: Path, target: str) -> Path:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in target).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return project_dir / "docs" / "mobile-superpowers" / "verification" / (slug or "flutter-web")


def verify_flutter_web(
    *,
    project_dir: Path | str,
    target: str,
    visual_contract: Path | str,
    baseline_screenshot: Path | str,
    assets: Path | str | None = None,
    plan: Path | str | None = None,
    out_dir: Path | str | None = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    port: int = 8765,
    execute: bool = False,
    dry_run: bool = False,
    runner: Runner = subprocess.run,
    server_factory=start_static_server,
    capture=capture_url_screenshot_cdp,
    compare=compare_visuals,
    report=create_verification_report,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    visual_contract = Path(visual_contract).expanduser().resolve()
    baseline_screenshot = Path(baseline_screenshot).expanduser().resolve()
    assets_path = Path(assets).expanduser().resolve() if assets else None
    plan_path = Path(plan).expanduser().resolve() if plan else None
    out_dir = Path(out_dir).expanduser().resolve() if out_dir else default_out_dir(project_dir, target)
    build_dir = project_dir / "build" / "web"
    platform_screenshot = out_dir / "platform-screenshot.png"
    metrics_path = out_dir / "platform-metrics.json"
    report_path = out_dir / "verification-report.md"
    url = f"http://127.0.0.1:{port}/"
    commands = [["flutter", "build", "web"]]

    errors: list[str] = []
    for label, path in {
        "project dir": project_dir,
        "visual contract": visual_contract,
        "baseline screenshot": baseline_screenshot,
        "assets": assets_path,
        "plan": plan_path,
    }.items():
        if path and not path.exists():
            errors.append(f"{label} not found: {path}")
    if execute and not shutil.which("flutter"):
        errors.append("flutter command not found")

    result: dict[str, Any] = {
        "dry_run": dry_run or not execute,
        "project_dir": str(project_dir),
        "target": target,
        "platform": "Flutter Web",
        "build_dir": str(build_dir),
        "url": url,
        "out_dir": str(out_dir),
        "platform_screenshot": str(platform_screenshot),
        "metrics": str(metrics_path),
        "report": str(report_path),
        "commands": commands,
        "validation": {"errors": errors, "warnings": []},
    }
    if dry_run or not execute or errors:
        return result

    out_dir.mkdir(parents=True, exist_ok=True)
    build = runner(["flutter", "build", "web"], cwd=str(project_dir), timeout=600)
    if build.returncode != 0:
        result["validation"]["errors"].append(f"flutter build web exited with code {build.returncode}")
        return result
    if not (build_dir / "index.html").exists():
        result["validation"]["errors"].append(f"Flutter web build did not create index.html: {build_dir / 'index.html'}")
        return result

    server = None
    try:
        server = server_factory(directory=build_dir, port=port)
        time.sleep(1)
        capture_result = capture(
            url=url,
            screenshot_path=platform_screenshot,
            width=width,
            height=height,
        )
        result["capture"] = capture_result
        result["validation"]["errors"].extend(capture_result.get("validation", {}).get("errors", []))
        if result["validation"]["errors"]:
            return result
        compare_result = compare(
            reference=baseline_screenshot,
            candidate=platform_screenshot,
            out_dir=out_dir,
            prefix="platform",
        )
        result["compare"] = compare_result
        metrics_path = Path(compare_result.get("metrics", metrics_path)).expanduser().resolve()
        result["metrics"] = str(metrics_path)
        result["validation"]["errors"].extend(compare_result.get("validation", {}).get("errors", []))
        if result["validation"]["errors"]:
            return result
        environment = [f"viewport {width}x{height}", f"local web server {url}"]
        runtime_viewport = capture_result.get("runtime_viewport", {})
        if runtime_viewport:
            environment.append(f"runtime viewport {json.dumps(runtime_viewport, sort_keys=True)}")
        report_result = report(
            out_dir=out_dir,
            target=target,
            platform="Flutter Web",
            plan=plan_path,
            visual_contract=visual_contract,
            baseline_screenshot=baseline_screenshot,
            platform_screenshot=platform_screenshot,
            metrics=metrics_path,
            assets=assets_path,
            command=["flutter build web", f"serve {build_dir} at {url}", "capture Flutter Web screenshot", "compare baseline vs Flutter Web screenshot"],
            environment=environment,
        )
        result["assessment"] = report_result.get("assessment")
        result["report"] = report_result.get("report", str(report_path))
        result["validation"]["errors"].extend(report_result.get("validation", {}).get("errors", []))
        return result
    finally:
        stop_process(server)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify Flutter Web against a Mobile Superpowers HTML baseline.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--target", required=True)
    parser.add_argument("--visual-contract", type=Path, required=True)
    parser.add_argument("--baseline-screenshot", type=Path, required=True)
    parser.add_argument("--assets", type=Path, default=None)
    parser.add_argument("--plan", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_flutter_web(
        project_dir=args.project_dir,
        target=args.target,
        visual_contract=args.visual_contract,
        baseline_screenshot=args.baseline_screenshot,
        assets=args.assets,
        plan=args.plan,
        out_dir=args.out_dir,
        width=args.width,
        height=args.height,
        port=args.port,
        execute=args.execute,
        dry_run=args.dry_run,
    )
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["platform_screenshot"])
        print(result["metrics"])
        print(result["report"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}")
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
