---
id: AGENT_ENABLEMENT_GUIDE
title: Agent Enablement Guide
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Agent Enablement Guide (explanation) for dopemux documentation and developer
  workflows.
---
# Agent Enablement Guide

## Instructions by Agent

### Codex / OpenAI
- Ensure `AGENTS.md` is present in the repo root.
- Skill definition resides in `templates/skills/pr-merge-specialist/SKILL.md`.

### Claude Code
- Add `.claude/agents/pr-merge-specialist.md` to your configuration.
- Reference `.claude/hooks/README.md` for lifecycle triggers.

### GitHub Copilot
- Enable repository custom instructions via `.github/copilot-instructions.md`.
- Deploy the custom agent profile in `.github/agents/pr-merge-specialist.agent.md`.

### Cursor
- Use the `.cursor/rules/pr-merge-specialist.mdc` for static context.
- Link the `skills/pr-merge-specialist/SKILL.md` for dynamic task logic.

### Gemini
- CLI: Point the agent to `GEMINI.md`.
- Code Assist: Add custom commands from `docs/skills/pr-merge-specialist/gemini/custom-commands.md`.

### Mistral Vibe
- Load the agent instructions from `.vibe/agents/pr-merge-specialist.md`.

### Jules
- Use `docs/skills/pr-merge-specialist/jules/task-template.md` for autonomous task creation.
