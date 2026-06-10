# DMX-DCP-MODEL-ROUTING-MVP-0000 — SLASH_COMMAND_INVENTORY.md

## Slash Command Surface (Partial — .claude/commands/ + src/dopemux/commands/)

| Command | Path | Purpose | Inputs | Outputs | Side effects | Safe automation class | Evidence | Unknowns |
|---------|------|---------|--------|---------|--------------|-----------------------|----------|----------|
| /dx:load | .claude/commands/ (inferred) | Session context load | ConPort active_context | Session state | Read | Read | .claude/commands/ ls | Full list not enumerated |
| /dx:save | .claude/commands/ (inferred) | Session context save | Session state | ConPort update | Write (ConPort) | Write | .claude/commands/ ls | Write contract UNKNOWN |
| /dx:implement | .claude/commands/ (inferred) | 25min ADHD session | Task spec | Implementation + auto-save | Write (files) | Write | .claude/commands/ ls | Mutation surface UNKNOWN |
| /sc:analyze | src/dopemux/commands/ (inferred) | Code analysis | Code path | Quality/security/performance report | Read | Read | src/dopemux/commands/ ls | PAL thinkdeep delegation |
| /sc:brainstorm | src/dopemux/commands/ (inferred) | Requirements discovery | Prompt | Structured requirements | Read | Read | src/dopemux/commands/ ls | Socratic dialogue |
| /sc:implement | src/dopemux/commands/ (inferred) | Feature implementation | Feature spec | Code + tests | Write (files) | Write | src/dopemux/commands/ ls | Magic + Context7 + PAL |
| /sc:review | src/dopemux/commands/ (inferred) | Code review | PR diff | Review report | Read | Read | src/dopemux/commands/ ls | PAL codereview |
| /sc:research | src/dopemux/commands/ (inferred) | Deep research | Query | Multi-source report | Read | Read | src/dopemux/commands/ ls | GPT-Researcher + PAL |
| /sc:troubleshoot | src/dopemux/commands/ (inferred) | Bug investigation | Error + context | Diagnosis + fix | Read + write (proposed) | Write (proposed) | src/dopemux/commands/ ls | PAL debug |
| extract_commands | src/dopemux/commands/extract_commands.py | Extraction orchestration | Run ID + phase | Extraction artifacts | Write (extraction/) | Write | src/dopemux/commands/ | 27 command modules observed |

**Total Slash Commands Enumerated**: 10 (representative sample)
**Full Enumeration**: .claude/commands/ contains 52 .md files; src/dopemux/commands/ contains 27 Python modules — complete listing deferred to SLASH_COMMAND_INVENTORY_FULL.md
**Write-Posture Commands**: 4 (save, implement, sc:implement, extract_commands)
