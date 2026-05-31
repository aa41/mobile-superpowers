# Mobile Superpowers Acceptance

Use this document to verify that the plugin is discoverable and the startup workflow is active.

## Claude Code

1. Install or enable the plugin from `mobile-superpowers/`.
2. Start a clean Claude Code session.
3. Send exactly:

```text
Let's make a mobile todo list
```

Expected:

- Session startup injects `using-mobile-superpowers`.
- The agent says it is using `using-mobile-superpowers` to select the mobile workflow.
- The agent selects `mobile-brainstorming` before writing code.
- No implementation files are edited before brainstorming/spec approval.

## Codex

1. Install or enable the plugin from `mobile-superpowers/.codex-plugin/plugin.json`.
2. Confirm the plugin exposes `skills: ./skills/`.
3. Start a clean Codex session.
4. Send exactly:

```text
Let's make a mobile todo list
```

Expected:

- `using-mobile-superpowers` is available as a skill.
- The agent selects the mobile workflow before acting.
- The agent uses `mobile-brainstorming` for the new mobile feature.
- If subagents are unavailable, the agent states the limitation and runs the closest sequential brainstorming workflow.

## Local Preflight

Run these before clean-session harness testing:

```bash
python3 mobile-superpowers/scripts/mobile_plugin_check.py \
  --plugin-root mobile-superpowers \
  --json

python3 mobile-superpowers/scripts/mobile_full_chain_check.py \
  --plugin-root mobile-superpowers \
  --json

python3 -m unittest discover -s mobile-superpowers/tests
```

Expected:

- Plugin check has no validation errors.
- Full-chain check reports all workflow gates as `true`.
- Unit tests pass.

The full-chain check verifies local structure and hook readiness. It does not replace the clean Claude Code and Codex session acceptance prompts above.
