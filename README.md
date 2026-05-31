# Mobile Superpowers

Personal mobile app workflow skills for Claude Code and Codex.

This plugin starts with two skills:

- `using-mobile-superpowers` - bootstrap rules for selecting mobile workflow skills before acting.
- `mobile-brainstorming` - multi-agent mobile design workflow with independent proposals, review, and final spec synthesis.
- `mobile-visual-design` - draw-ui-inspired visual workflow: provider-configured mockup generation, HTML baseline, similarity check, and visual contract.
- `mobile-writing-plans` - converts approved mobile specs and visual contracts into task-by-task implementation plans.
- `mobile-using-git-worktrees` - prepares or verifies an isolated mobile implementation workspace before edits.
- `mobile-executing-plans` - executes approved mobile implementation plans task by task with tests, screenshots, and verification gates.
- `mobile-test-driven-development` - requires failing mobile behavior, state, visual, or artifact expectations before production code.
- `mobile-systematic-debugging` - investigates mobile build, test, device, screenshot, visual diff, and provider failures before fixes.
- `mobile-ui-verification` - verifies implemented mobile UI with platform screenshots, baseline comparison, and visual evidence.
- `mobile-verification-before-completion` - checks plan coverage, tests/builds, UI evidence, artifacts, and secrets before completion claims.
- `mobile-requesting-code-review` - prepares focused mobile review context after implementation or before review/merge readiness.
- `mobile-receiving-code-review` - verifies and applies mobile review feedback one item at a time.
- `mobile-finishing-a-development-branch` - handles verified mobile branch merge, PR, preservation, cleanup, or discard decisions.

## Install

Clone the plugin:

```bash
git clone https://github.com/aa41/mobile-superpowers.git
cd mobile-superpowers
python3 -m unittest discover -s tests
python3 scripts/mobile_plugin_check.py --plugin-root . --json
python3 scripts/mobile_full_chain_check.py --plugin-root . --json
```

### Claude Code

Enable the plugin directory in Claude Code using the local `mobile-superpowers/` checkout. The plugin includes:

- `.claude-plugin/plugin.json`
- `hooks/session-start`
- `hooks/hooks.json`

After enabling, start a clean Claude Code session and send:

```text
Let's make a mobile todo list
```

Expected first behavior:

```text
Using using-mobile-superpowers to select the mobile workflow.
```

The agent should then choose `mobile-brainstorming` before writing code.

### Codex

Enable the plugin from:

```text
mobile-superpowers/.codex-plugin/plugin.json
```

The manifest exposes:

```json
{
  "skills": "./skills/"
}
```

Start a clean Codex session and send:

```text
Let's make a mobile todo list
```

The agent should select `using-mobile-superpowers`, then `mobile-brainstorming`, before implementation.

## Provider Configuration

Do not commit API keys. Configure visual providers with environment variables or local config.

Environment example:

```bash
export MOBILE_VISUAL_BASE_URL="https://fushengyunsuan.cn/v1"
export MOBILE_VISUAL_API_KEY="<your-api-key>"
export MOBILE_VISUAL_MODEL="gpt-image-2"
export MOBILE_VISUAL_VISION_MODEL="gpt-5.5"
```

Check configuration without exposing the key:

```bash
python3 scripts/mobile_visual_config.py --check
```

Generated visual artifacts and verification outputs are ignored by default:

- `docs/mobile-superpowers/visual/`
- `docs/mobile-superpowers/verification/`

## Visual Tooling

The local scripts support configuration, visual artifacts, provider execution, HTML reconstruction, screenshots, and comparison:

```bash
python3 mobile-superpowers/scripts/mobile_visual_config.py --check
python3 mobile-superpowers/scripts/mobile_visual_artifacts.py --topic "Checkout Flow"
python3 mobile-superpowers/scripts/mobile_visual_provider.py --topic "Checkout Flow" --prompt "Design a mobile checkout screen." --dry-run
python3 mobile-superpowers/scripts/mobile_visual_provider.py --topic "Checkout Flow" --prompt "Design a mobile checkout screen." --execute
python3 mobile-superpowers/scripts/mobile_visual_baseline.py --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json"
python3 mobile-superpowers/scripts/mobile_visual_reconstruct.py --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json" --force
python3 mobile-superpowers/scripts/mobile_visual_assets.py --baseline "docs/mobile-superpowers/visual/<date-topic>/baseline.html"
python3 mobile-superpowers/scripts/mobile_visual_screenshot.py --baseline "docs/mobile-superpowers/visual/<date-topic>/baseline.html"
python3 mobile-superpowers/scripts/mobile_visual_deps.py --install
python3 mobile-superpowers/scripts/mobile_visual_compare.py --reference "docs/mobile-superpowers/visual/<date-topic>/reference.png" --candidate "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png"
```

Provider execution is explicit. Use `--dry-run` for metadata only, or `--execute` to call an OpenAI-compatible `/images/generations` endpoint. Execution may spend provider credits. GPT image generation defaults to `gpt-image-2`.

After `generated-mockup.png` exists, the multimodal HTML reconstruction adapter can call an OpenAI-compatible `/chat/completions` endpoint and write the returned HTML into `baseline.html`:

```bash
python3 mobile-superpowers/scripts/mobile_visual_reconstruct.py \
  --metadata "docs/mobile-superpowers/visual/<date-topic>/generated-mockup.png.json" \
  --force \
  --execute \
  --vision-model gpt-5.5
```

`--vision-model` is separate from the image generation model. Use it for the chat/vision model that reads the mockup image and writes HTML. The default is `gpt-5.5`; override it with `--vision-model`, `MOBILE_VISUAL_VISION_MODEL`, or `visual.vision_model` in config.

Create a mobile implementation plan scaffold from a visual contract and asset manifest:

```bash
python3 mobile-superpowers/scripts/mobile_plan_scaffold.py \
  --feature "Profile Screen" \
  --platform Flutter \
  --spec "docs/specs/profile.md" \
  --visual-contract "docs/mobile-superpowers/visual/<date-topic>/visual-contract.md" \
  --assets "docs/mobile-superpowers/visual/<date-topic>/assets.json"
```

Create a verification report after platform screenshots and metrics exist:

```bash
python3 mobile-superpowers/scripts/mobile_ui_verification_report.py \
  --out-dir "docs/mobile-superpowers/verification/<date-topic>" \
  --target "Profile Screen" \
  --platform "Flutter Web" \
  --visual-contract "docs/mobile-superpowers/visual/<date-topic>/visual-contract.md" \
  --baseline-screenshot "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png" \
  --platform-screenshot "docs/mobile-superpowers/verification/<date-topic>/flutter-web-screenshot.png" \
  --metrics "docs/mobile-superpowers/verification/<date-topic>/platform-metrics.json" \
  --assets "docs/mobile-superpowers/visual/<date-topic>/assets.json"
```

For Flutter Web, the adapter can run build, serve, screenshot, compare, and report:

```bash
python3 mobile-superpowers/scripts/mobile_flutter_web_verify.py \
  --project-dir "<flutter-project>" \
  --target "Profile Screen" \
  --visual-contract "docs/mobile-superpowers/visual/<date-topic>/visual-contract.md" \
  --baseline-screenshot "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png" \
  --assets "docs/mobile-superpowers/visual/<date-topic>/assets.json" \
  --plan "docs/mobile-superpowers/plans/<plan>.md" \
  --dry-run \
  --json
```

For Android, the adapter can build/install/launch/screenshot/compare/report when a device is ready:

```bash
python3 mobile-superpowers/scripts/mobile_android_verify.py \
  --project-dir "<android-project>" \
  --target "Profile Screen" \
  --visual-contract "docs/mobile-superpowers/visual/<date-topic>/visual-contract.md" \
  --baseline-screenshot "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png" \
  --assets "docs/mobile-superpowers/visual/<date-topic>/assets.json" \
  --plan "docs/mobile-superpowers/plans/<plan>.md" \
  --apk "app/build/outputs/apk/debug/app-debug.apk" \
  --launch-activity "com.example/.MainActivity" \
  --dry-run \
  --json
```

For iOS, the adapter can build/install/launch/screenshot/compare/report when a simulator is ready:

```bash
python3 mobile-superpowers/scripts/mobile_ios_verify.py \
  --project-dir "<ios-project>" \
  --target "Profile Screen" \
  --visual-contract "docs/mobile-superpowers/visual/<date-topic>/visual-contract.md" \
  --baseline-screenshot "docs/mobile-superpowers/visual/<date-topic>/baseline-screenshot.png" \
  --assets "docs/mobile-superpowers/visual/<date-topic>/assets.json" \
  --plan "docs/mobile-superpowers/plans/<plan>.md" \
  --app "build/ios/iphonesimulator/Runner.app" \
  --bundle-id "com.example.app" \
  --dry-run \
  --json
```

If the active Python cannot create a venv, pass an explicit interpreter:

```bash
python3 mobile-superpowers/scripts/mobile_visual_deps.py --install --python /usr/local/bin/python3
```

## Supported Harnesses

- Claude Code: via `.claude-plugin/` metadata and `hooks/session-start`.
- Codex: via `.codex-plugin/plugin.json` and the shared `skills/` directory.

Validate manifests, hook injection, and acceptance docs:

```bash
python3 mobile-superpowers/scripts/mobile_plugin_check.py \
  --plugin-root mobile-superpowers \
  --json
```

Acceptance test prompt:

```text
Let's make a mobile todo list
```

Expected result: the agent selects `using-mobile-superpowers`, then uses `mobile-brainstorming` before writing code. See `docs/acceptance.md`.

## Design Notes

This is a personal plugin, not a contribution to Superpowers core. Mobile app workflows are domain-specific and should evolve here before being shared more broadly.
