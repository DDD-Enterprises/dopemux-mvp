# MACRO-DMX-CMD-REPAIR-002 — MacroPacket (follow-up to MACRO-DMX-CMD-REPAIR-001)

Issued by: control tower supervisor (this session). Authority: NONE beyond the operator chat task
("Follow-up to MACRO-DMX-CMD-REPAIR-001 ... No push or merge."). Base: fix/cmd-repair-001 @ f082007ff.
Forbidden: push, merge, PR, force-push, history rewrite, signing, audit-route changes.

## Workstreams (disjoint write surfaces, serialized W07 -> W08 because W08's real-repo test needs W07 done)

| WS | Objective | Write allowlist | Route |
|---|---|---|---|
| W07 | Retire `.claude/commands/zen.md` and `zen-continue.md` (server `zen` exists nowhere; renamed pal, PAL has no `execute_workflow`); repoint `mcp__pal__*` to `mcp__pal-stdio__*` in `dx/implement.md`, `dx/note.md`; fix stale snapshot paragraph in `docs/02-how-to/mcp-integration-guide.md` | the 2 deleted files, `.claude/commands/dx/implement.md`, `.claude/commands/dx/note.md`, `docs/02-how-to/mcp-integration-guide.md` | local supervisor (Sonnet 5.5) |
| W08 | Enable `/mcp <server> <tool>` prose scan in `tests/arch/test_claude_command_references.py` with negative controls; tighten `_MCP_REF` (underscore servers, trailing boundary); recompute `UNVERIFIED_SERVERS` | `tests/arch/test_claude_command_references.py` | local supervisor (Sonnet 5.5) |

TP_ROUTE (both): runner Claude Code, model claude-sonnet-5-5, effort runner-default (observed UNKNOWN). Why: edits are
mechanical (<10 lines each, 5 files); spawning a child costs more context than doing the work. Exception to
cost-first delegation recorded: no child dispatched. Advisor: supervisor-side only.

## Acceptance
`pytest tests/arch` green; black/flake8 clean on touched Python; `validate_change_contract` preflight PASS;
one commit per workstream with explicit pathspec; final independent audit via operator-approved route = NOT_RUN
(operator gate; gemini-3.1-pro-high availability UNKNOWN). Aggregate authority: NONE.
