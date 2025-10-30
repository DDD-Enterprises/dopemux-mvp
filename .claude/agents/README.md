# Dopemux Agent Personas

Use these prompt files when launching Claude Code agents from the orchestrator
console (or manually). Each prompt configures the agent with a focused mission,
toolkit, and reporting expectations so it collaborates smoothly with the
Codex-based orchestrator.

## Available Personas

| Prompt File                 | Mission                                                |
|-----------------------------|--------------------------------------------------------|
| `builder.md`                | Implement code, run tests, update sandbox status       |
| `reviewer.md`               | Review changes, highlight risks, summarize outcomes    |
| `doc_writer.md`             | Update documentation, READMEs, changelogs              |
| `researcher.md`             | Gather context via Zen, MAS, Exa; propose strategies   |

## Launch Examples

```bash
# From orchestrator pane
dopemux start --no-recovery \
  --prompt .claude/agents/builder.md \
  --decision <CONPORT_DECISION_ID>

# Dual-agent mode (second pane)
dopemux start --no-recovery \
  --prompt .claude/agents/reviewer.md \
  --decision <CONPORT_DECISION_ID>
```

> All agents inherit `DOPEMUX_DEFAULT_LITELLM=1`, so they route through the
> LiteLLM/OpenRouter stack (DeepSeek, xAI Grok, GPT‑4o). Ensure the relevant API
> keys are available before launching.

Each persona prompt instructs the agent to:

- Respect orchestrator directives.
- Use `sr <query>` (Serena) for code navigation when possible.
- Log progress back to ConPort (via `conport.log_progress` or CLI wrappers).
- Keep the orchestrator updated using `dopemux tmux send orchestrator:control`.

Customize these prompts as needed for your workflow—add specialized tool
commands, link to project docs, or inject project-specific conventions.***
