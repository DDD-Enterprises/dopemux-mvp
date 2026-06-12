# DMX-DCP-MODEL-ROUTING-MVP-0000 — RUNNER_CONFIG_INVENTORY.md

## Runner/Tool Configuration Inventory

| Runner | Config path | Installed? | Invokable? | Models/providers | Mutates files? | Proof capture | Evidence | Unknowns |
|--------|-------------|------------|------------|------------------|----------------|---------------|----------|----------|
| OpenCode | N/A (this session) | YES | YES | grok-4.3 (xai) | Read-only (this packet) | N/A | Current session | Custom opencode.json not present |
| Claude Code | .claude/claude.md + .claude/claude_config.json | YES | YES | claude-sonnet-4 / claude-opus-4 (via alias) | Read + write (delegated) | N/A | .claude/ ls + claude.md | Write posture per persona UNKNOWN |
| Codex | N/A | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | No .codex/ dir | .codex/ does not exist |
| Gemini CLI | N/A | UNKNOWN | UNKNOWN | gemini-2.5-pro / gemini-2.5-flash (via litellm) | UNKNOWN | N/A | No .gemini/ dir | Gemini CLI config not observed |
| AGY | N/A | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | No AGY config | AGY not observed in repo |
| Aider | N/A | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | N/A | No aider config | Aider not observed in repo |
| Copilot | .github/copilot-instructions.md | YES | YES (VS Code) | copilot (GitHub) | Read + write (delegated) | N/A | copilot-instructions.md | Copilot instructions observed |
| Jules | .Jules/ | YES | UNKNOWN | UNKNOWN | UNKNOWN | N/A | .Jules/ ls | Jules runtime UNKNOWN |

**Total Runners Catalogued**: 8
**Installed & Invokable**: 3 (OpenCode, Claude Code, Copilot)
**Config Present but Runtime Unknown**: 2 (Gemini CLI via litellm, Jules)
**No Config Observed**: 3 (Codex, AGY, Aider)
