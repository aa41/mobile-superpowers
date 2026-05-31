# Mobile Visual Provider Configuration

Project config:

```text
.mobile-superpowers/config.json
```

User config:

```text
~/.config/mobile-superpowers/config.json
```

Environment variables:

```bash
MOBILE_VISUAL_PROVIDER=openai
MOBILE_VISUAL_MODEL=gpt-image-2
MOBILE_VISUAL_VISION_MODEL=gpt-5.5
MOBILE_VISUAL_API_KEY=...
MOBILE_VISUAL_BASE_URL=https://api.openai.com/v1
MOBILE_VISUAL_OUTPUT_DIR=~/.local/share/mobile-superpowers/visual
MOBILE_VISUAL_QUALITY=high
MOBILE_VISUAL_SIZE=1024x1536
OPENAI_API_KEY=...
GEMINI_API_KEY=...
```

Supported provider names:

| Provider | Purpose | Default key env | Notes |
|---|---|---|---|
| `builtin` | Runtime-native image generation | none | Use when Claude/Codex environment already provides image generation |
| `openai` | OpenAI Images API | `OPENAI_API_KEY` | Compatible with OpenAI image generation |
| `gemini` | Gemini-native image generation/editing | `GEMINI_API_KEY` | For Gemini image-capable models |
| `imagen` | Google Imagen generation | `GEMINI_API_KEY` | Kept separate from Gemini-native image workflows |
| `proxy` | OpenAI-compatible relay | `MOBILE_VISUAL_API_KEY` | Requires `base_url` or `MOBILE_VISUAL_BASE_URL` |

Example:

```json
{
  "visual": {
    "provider": "openai",
    "model": "gpt-image-2",
    "vision_model": "gpt-5.5",
    "base_url": "https://api.openai.com/v1",
    "output_dir": "~/.local/share/mobile-superpowers/visual",
    "quality": "high",
    "size": "1024x1536",
    "timeout_seconds": 180
  },
  "providers": {
    "openai": {
      "api_key_env": "OPENAI_API_KEY"
    },
    "gemini": {
      "api_key_env": "GEMINI_API_KEY",
      "model": "gemini-2.5-flash-image"
    },
    "imagen": {
      "api_key_env": "GEMINI_API_KEY",
      "model": "imagen-4.0-generate-001"
    },
    "proxy": {
      "api_key_env": "MOBILE_VISUAL_API_KEY",
      "base_url_env": "MOBILE_VISUAL_BASE_URL",
      "endpoint_style": "openai-images"
    }
  }
}
```

Resolve and validate config without exposing secrets:

```bash
python3 mobile-superpowers/scripts/mobile_visual_config.py --check
python3 mobile-superpowers/scripts/mobile_visual_config.py --print
```

`--print` reports `has_api_key` and `api_key_source`, never the key value.
