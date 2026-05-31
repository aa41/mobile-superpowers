# Codex Tool Mapping

Mobile Superpowers skills may use Claude Code terminology. In Codex:

| Skill reference | Codex equivalent |
|---|---|
| `Task` | `spawn_agent` |
| Wait for subagent | `wait_agent` |
| Close subagent | `close_agent` |
| `TodoWrite` | `update_plan` |
| `Skill` | Native skill loading |
| File and shell tools | Native Codex tools |

For skills that require subagents, Codex needs multi-agent support enabled. If subagents are unavailable, state the limitation and run the closest sequential version instead. Do not claim independent agent review happened unless it actually did.
