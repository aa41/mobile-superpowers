#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mobile_visual_artifacts import create_visual_workspace
from mobile_visual_config import resolve_config, resolve_secret_value


DEFAULT_ASPECT_RATIO = "3:4"
DEFAULT_OPENAI_IMAGE_MODEL = "gpt-image-2"


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def normalize_refs(refs: list[str]) -> tuple[list[str], list[str]]:
    normalized: list[str] = []
    errors: list[str] = []
    for ref in refs:
        if is_url(ref):
            normalized.append(ref)
            continue
        path = Path(ref).expanduser().resolve()
        if not path.exists():
            errors.append(f"reference not found: {ref}")
        normalized.append(str(path))
    return normalized, errors


def build_dry_run_request(
    *,
    project_dir: Path | str = Path.cwd(),
    home_dir: Path | str = Path.home(),
    topic: str,
    prompt: str,
    refs: list[str] | None = None,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    date: str | None = None,
    output: Path | str | None = None,
    metadata: Path | str | None = None,
    config_path: Path | str | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    home_dir = Path(home_dir).expanduser().resolve()
    refs = refs or []

    config = resolve_config(project_dir=project_dir, home_dir=home_dir, config_path=config_path)
    workspace = create_visual_workspace(project_dir=project_dir, topic=topic, date=date)

    normalized_refs, ref_errors = normalize_refs(refs)
    validation = {
        "errors": [*config["validation"]["errors"], *ref_errors],
        "warnings": config["validation"]["warnings"],
    }

    image_path = Path(output).expanduser().resolve() if output else Path(workspace["artifacts"]["generated_mockup"])
    metadata_path = Path(metadata).expanduser().resolve() if metadata else Path(str(image_path) + ".json")

    return {
        "dry_run": True,
        "workspace": workspace["workspace"],
        "provider": {
            "name": config["provider"]["name"],
            "endpoint_style": config["provider"]["endpoint_style"],
            "model": config["provider"]["model"] or DEFAULT_OPENAI_IMAGE_MODEL,
            "base_url": config["provider"]["base_url"],
            "has_api_key": config["provider"]["has_api_key"],
            "api_key_source": config["provider"]["api_key_source"],
        },
        "request": {
            "prompt": prompt,
            "refs": normalized_refs,
            "aspect_ratio": aspect_ratio,
            "size": config["visual"]["size"],
            "quality": config["visual"]["quality"],
            "timeout_seconds": config["visual"]["timeout_seconds"],
        },
        "outputs": {
            "image": str(image_path),
            "metadata": str(metadata_path),
        },
        "validation": validation,
    }


def build_openai_images_payload(request: dict[str, Any]) -> dict[str, Any]:
    refs = request.get("request", {}).get("refs", [])
    if refs:
        raise ValueError("OpenAI-compatible image generation currently supports prompt-only requests; refs need edits support.")
    return {
        "model": request["provider"].get("model") or DEFAULT_OPENAI_IMAGE_MODEL,
        "prompt": request["request"]["prompt"],
        "size": request["request"].get("size") or "1024x1536",
        "quality": request["request"].get("quality") or "high",
        "n": 1,
        "response_format": "b64_json",
    }


def openai_images_transport(url: str, *, payload: dict[str, Any], api_key: str, timeout: int) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def execute_openai_images_request(
    request: dict[str, Any],
    *,
    api_key: str,
    transport=openai_images_transport,
) -> dict[str, Any]:
    result = json.loads(json.dumps(request))
    errors = list(result.get("validation", {}).get("errors", []))
    if not api_key:
        errors.append("api_key is required for provider execution")
    if result["provider"].get("endpoint_style") != "openai-images":
        errors.append(f"unsupported endpoint_style: {result['provider'].get('endpoint_style')}")
    base_url = str(result["provider"].get("base_url") or "").rstrip("/")
    if not base_url:
        errors.append("base_url is required for provider execution")
    if errors:
        result["validation"] = {"errors": errors, "warnings": result.get("validation", {}).get("warnings", [])}
        return result

    try:
        payload = build_openai_images_payload(result)
    except ValueError as exc:
        result["validation"] = {"errors": [str(exc)], "warnings": result.get("validation", {}).get("warnings", [])}
        return result

    url = f"{base_url}/images/generations"
    timeout = int(result["request"].get("timeout_seconds") or 180)
    response = transport(url, payload=payload, api_key=api_key, timeout=timeout)
    data = response.get("data") or []
    if not data:
        result["validation"] = {"errors": ["provider returned no image data"], "warnings": []}
        return result

    image_path = Path(result["outputs"]["image"]).expanduser().resolve()
    metadata_path = Path(result["outputs"]["metadata"]).expanduser().resolve()
    image_path.parent.mkdir(parents=True, exist_ok=True)
    first = data[0]
    if first.get("b64_json"):
        image_path.write_bytes(base64.b64decode(first["b64_json"]))
    elif first.get("url"):
        with urllib.request.urlopen(first["url"], timeout=timeout) as image_response:
            image_path.write_bytes(image_response.read())
    else:
        result["validation"] = {"errors": ["provider response missing b64_json or url"], "warnings": []}
        return result

    result["dry_run"] = False
    result["provider_response"] = {
        "created": response.get("created"),
        "data_count": len(data),
        "first_has_b64_json": bool(first.get("b64_json")),
        "first_has_url": bool(first.get("url")),
    }
    result["validation"] = {"errors": [], "warnings": result.get("validation", {}).get("warnings", [])}
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Mobile Superpowers visual provider request.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--home-dir", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--ref", action="append", default=[])
    parser.add_argument("--aspect-ratio", default=DEFAULT_ASPECT_RATIO)
    parser.add_argument("--date", default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--metadata", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Build metadata without calling a provider.")
    parser.add_argument("--execute", action="store_true", help="Call the configured provider.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dry_run and not args.execute:
        print("Use --dry-run to write metadata or --execute to call the configured provider.", file=sys.stderr)
        return 2
    if args.dry_run and args.execute:
        print("Choose only one: --dry-run or --execute.", file=sys.stderr)
        return 2

    result = build_dry_run_request(
        project_dir=args.project_dir,
        home_dir=args.home_dir,
        config_path=args.config,
        topic=args.topic,
        prompt=args.prompt,
        refs=args.ref,
        aspect_ratio=args.aspect_ratio,
        date=args.date,
        output=args.output,
        metadata=args.metadata,
    )

    if args.execute:
        api_key = resolve_secret_value(
            result["provider"]["api_key_source"],
            project_dir=args.project_dir,
            home_dir=args.home_dir,
            config_path=args.config,
        )
        result = execute_openai_images_request(result, api_key=api_key)

    metadata_path = Path(result["outputs"]["metadata"])
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(result["workspace"])
    print(result["outputs"]["metadata"])
    for error in result["validation"]["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
