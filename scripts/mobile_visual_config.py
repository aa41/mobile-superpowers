#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULTS: dict[str, Any] = {
    "visual": {
        "provider": "builtin",
        "model": "",
        "vision_model": "gpt-5.5",
        "base_url": "",
        "output_dir": "docs/mobile-superpowers/visual",
        "quality": "high",
        "size": "1024x1536",
        "timeout_seconds": 180,
    },
    "providers": {
        "builtin": {
            "requires_api_key": False,
            "endpoint_style": "runtime",
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "endpoint_style": "openai-images",
        },
        "gemini": {
            "api_key_env": "GEMINI_API_KEY",
            "endpoint_style": "gemini-images",
        },
        "imagen": {
            "api_key_env": "GEMINI_API_KEY",
            "endpoint_style": "imagen-generate-images",
        },
        "proxy": {
            "api_key_env": "MOBILE_VISUAL_API_KEY",
            "base_url_env": "MOBILE_VISUAL_BASE_URL",
            "endpoint_style": "openai-images",
        },
    },
}

ENV_TO_VISUAL_KEY = {
    "MOBILE_VISUAL_PROVIDER": "provider",
    "MOBILE_VISUAL_MODEL": "model",
    "MOBILE_VISUAL_VISION_MODEL": "vision_model",
    "MOBILE_VISUAL_BASE_URL": "base_url",
    "MOBILE_VISUAL_OUTPUT_DIR": "output_dir",
    "MOBILE_VISUAL_QUALITY": "quality",
    "MOBILE_VISUAL_SIZE": "size",
    "MOBILE_VISUAL_TIMEOUT_SECONDS": "timeout_seconds",
}

FALLBACK_API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "imagen": "GEMINI_API_KEY",
    "proxy": "MOBILE_VISUAL_API_KEY",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def coerce_value(value: str, existing: Any) -> Any:
    if isinstance(existing, int):
        try:
            return int(value)
        except ValueError:
            return value
    return value


def apply_env_overrides(config: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    result = deepcopy(config)
    visual = result.setdefault("visual", {})
    for env_name, key in ENV_TO_VISUAL_KEY.items():
        raw = env.get(env_name, "").strip()
        if raw:
            visual[key] = coerce_value(raw, visual.get(key))
    return result


def expand_path(value: str, *, project_dir: Path, home_dir: Path) -> str:
    if not value:
        return value
    if value == "~" or value.startswith("~/"):
        return str(home_dir / value[2:])
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str(project_dir / path)


def first_secret(
    candidates: list[tuple[str, str]],
    *,
    env: dict[str, str],
    provider_config: dict[str, Any],
) -> tuple[bool, str]:
    for source, value in candidates:
        if source.startswith("env:"):
            env_name = source.split(":", 1)[1]
            if env.get(env_name, "").strip():
                return True, source
            continue
        if value:
            return True, source
    api_key_env = str(provider_config.get("api_key_env", "")).strip()
    if api_key_env and env.get(api_key_env, "").strip():
        return True, f"env:{api_key_env}"
    return False, ""


def resolve_provider_details(
    config: dict[str, Any],
    *,
    env: dict[str, str],
    project_config_loaded: bool,
    user_config_loaded: bool,
) -> dict[str, Any]:
    visual = config.get("visual", {})
    provider_name = str(visual.get("provider") or "builtin").strip()
    providers = config.get("providers", {})
    provider_config = providers.get(provider_name, {})
    if not isinstance(provider_config, dict):
        provider_config = {}

    fallback_env = FALLBACK_API_KEY_ENV.get(provider_name, "")
    if fallback_env and not provider_config.get("api_key_env"):
        provider_config = {**provider_config, "api_key_env": fallback_env}

    secret_candidates: list[tuple[str, str]] = []
    env_key = str(provider_config.get("api_key_env", "")).strip()
    if env_key:
        secret_candidates.append((f"env:{env_key}", ""))
    if provider_config.get("api_key"):
        origin = "project_config" if project_config_loaded else "user_config" if user_config_loaded else "config"
        secret_candidates.append((f"{origin}:providers.{provider_name}.api_key", str(provider_config["api_key"])))

    has_api_key, api_key_source = first_secret(secret_candidates, env=env, provider_config=provider_config)

    base_url = str(provider_config.get("base_url") or visual.get("base_url") or "").strip()
    base_url_env = str(provider_config.get("base_url_env", "")).strip()
    if base_url_env and env.get(base_url_env, "").strip():
        base_url = env[base_url_env].strip()
    if env.get("MOBILE_VISUAL_BASE_URL", "").strip():
        base_url = env["MOBILE_VISUAL_BASE_URL"].strip()

    return {
        "name": provider_name,
        "model": str(visual.get("model") or provider_config.get("model") or ""),
        "base_url": base_url,
        "endpoint_style": str(provider_config.get("endpoint_style") or ""),
        "has_api_key": has_api_key,
        "api_key_source": api_key_source,
    }


def validate(config: dict[str, Any], provider: dict[str, Any]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    provider_name = provider["name"]

    if provider_name not in config.get("providers", {}) and provider_name != "builtin":
        warnings.append(f"provider {provider_name} has no provider config")

    if provider_name != "builtin" and not provider["has_api_key"]:
        errors.append(f"provider {provider_name} requires api_key")

    if provider_name == "proxy" and not provider["base_url"]:
        errors.append("provider proxy requires base_url")

    return {"errors": errors, "warnings": warnings}


def resolve_config(
    *,
    project_dir: Path | str = Path.cwd(),
    home_dir: Path | str = Path.home(),
    config_path: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    project_dir = Path(project_dir).expanduser().resolve()
    home_dir = Path(home_dir).expanduser().resolve()
    env = dict(os.environ if env is None else env)

    project_config_path = project_dir / ".mobile-superpowers" / "config.json"
    user_config_path = home_dir / ".config" / "mobile-superpowers" / "config.json"

    user_config = read_json(user_config_path)
    project_config = read_json(Path(config_path).expanduser().resolve()) if config_path else read_json(project_config_path)

    config = deep_merge(DEFAULTS, user_config)
    config = deep_merge(config, project_config)
    config = apply_env_overrides(config, env)

    visual = config.setdefault("visual", {})
    visual["output_dir"] = expand_path(str(visual.get("output_dir", "")), project_dir=project_dir, home_dir=home_dir)

    provider = resolve_provider_details(
        config,
        env=env,
        project_config_loaded=bool(project_config),
        user_config_loaded=bool(user_config),
    )
    validation = validate(config, provider)

    return {
        "visual": {
            "provider": provider["name"],
            "model": provider["model"],
            "vision_model": str(visual.get("vision_model") or "gpt-5.5"),
            "base_url": provider["base_url"],
            "output_dir": visual.get("output_dir", ""),
            "quality": visual.get("quality", ""),
            "size": visual.get("size", ""),
            "timeout_seconds": visual.get("timeout_seconds", ""),
        },
        "provider": provider,
        "config_sources": {
            "project_config": str(project_config_path if config_path is None else Path(config_path).expanduser().resolve()),
            "project_config_loaded": bool(project_config),
            "user_config": str(user_config_path),
            "user_config_loaded": bool(user_config),
        },
        "validation": validation,
    }


def resolve_secret_value(
    source: str,
    *,
    project_dir: Path | str = Path.cwd(),
    home_dir: Path | str = Path.home(),
    config_path: Path | str | None = None,
    env: dict[str, str] | None = None,
) -> str:
    if not source:
        return ""
    env = dict(os.environ if env is None else env)
    if source.startswith("env:"):
        return env.get(source.split(":", 1)[1], "").strip()

    project_dir = Path(project_dir).expanduser().resolve()
    home_dir = Path(home_dir).expanduser().resolve()
    user_config_path = home_dir / ".config" / "mobile-superpowers" / "config.json"
    project_config_path = Path(config_path).expanduser().resolve() if config_path else project_dir / ".mobile-superpowers" / "config.json"

    if source.startswith("project_config:"):
        data = read_json(project_config_path)
        path = source.split(":", 1)[1]
    elif source.startswith("user_config:"):
        data = read_json(user_config_path)
        path = source.split(":", 1)[1]
    elif source.startswith("config:"):
        data = read_json(project_config_path) or read_json(user_config_path)
        path = source.split(":", 1)[1]
    else:
        return ""

    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return ""
        current = current[part]
    return str(current).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve Mobile Superpowers visual provider configuration.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--home-dir", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--config", type=Path, default=None, help="Explicit config JSON path.")
    parser.add_argument("--print", action="store_true", dest="print_config", help="Print resolved config JSON.")
    parser.add_argument("--check", action="store_true", help="Print a concise validation report.")
    return parser.parse_args()


def format_check(result: dict[str, Any]) -> str:
    visual = result["visual"]
    provider = result["provider"]
    sources = result["config_sources"]
    validation = result["validation"]

    lines = [
        f"provider={visual['provider']}",
        f"model={visual['model']}",
        f"vision_model={visual['vision_model']}",
        f"base_url={'set' if provider['base_url'] else 'unset'}",
        f"api_key={'set' if provider['has_api_key'] else 'unset'}",
        f"api_key_source={provider['api_key_source'] or 'none'}",
        f"project_config_loaded={sources['project_config_loaded']}",
        f"user_config_loaded={sources['user_config_loaded']}",
    ]
    for warning in validation["warnings"]:
        lines.append(f"WARNING: {warning}")
    for error in validation["errors"]:
        lines.append(f"ERROR: {error}")
    if not validation["errors"]:
        lines.append("OK")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    result = resolve_config(project_dir=args.project_dir, home_dir=args.home_dir, config_path=args.config)
    if args.print_config:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.check:
        print(format_check(result))
    return 1 if result["validation"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
