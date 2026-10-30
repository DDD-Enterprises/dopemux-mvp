# AGY final audit (CORROBORATING) - run record (MACRO-DMX-ROUTE-LEDGER-001-R3, W03): STOPPED, NO VERDICT

Facts only. No answer text of the real run exists to be read: the stream holds the init event and the completed user-input step and nothing else.

**Subject**: content head `4fcdc97615d7a736cd1199bb854bf63fcdbf39f0`, prompt `AUDIT_PROMPT.txt` (135,918 bytes, committed in `c02748b05`; the sealed copy was byte-identical by cmp).
**Route**: `agy` CLI, model `gemini-4-argon-high` (the exact id listed by `agy models`; the init event of every run shows it; in probe 2 the model called itself "Gemini 4 Argon (High)", a claim, not attestation). Authorized by the operator's verbatim R3 gate line (`..._AUDIT_ROUTE_AGY_GEMINI_4_ARGON_HIGH=YES`).
**Outcome**: ONE audit attempt was made and CONSUMED WITHOUT A VERDICT. The coordinator stopped the process on 2026-10-30T09:34:56Z (SIGTERM; agy exited at 09:35:01Z with `error: interrupted`, exit 1) because the operator retargeted the R3 audit subject to include current `main` (relayed by session `local_901ed6d9-e250-47e7-bd52-6f2fdc18ca3c`: the operator answered "Run it in order"; a signed proof binds to the audited head, so an audit of `4fcdc9761` alone is stale before it finishes). Zero retries, no fallback. This is a coordinator STOP, not an auditor result and not an audit failure.

## Containment evidence

- Probes 1 and 2 (2 of 2 allowed): exit 0; step types only `user_input` and `agent_response`; no tool step. The init event reports `permission_mode = request-review`.
- **agy cannot be made tool-less.** The init event lists 60 built-in tools (including `run_command`, `call_mcp_tool`, `write_to_file`, `search_web`, browser tools) and no flag removes them. In probe 2 the model listed `run_command`, `call_mcp_tool` and 7 MCP servers as available (a self-report). `agy mcp list` shows 11 global MCP servers enabled (a Docker gateway, desktop-commander, conport, dope-memory, serena, pal-stdio, task-orchestrator and others).
- The operator's SAVED agy settings are `toolPermission = always-proceed`, `allowNonWorkspaceAccess = true` and an allow list that includes `git commit` and `gh`. `--settings` (session-only, never saved) cannot set `mcpServers`, so the global servers could not be removed; it CAN set `toolPermission`, `allowNonWorkspaceAccess` and `permissions`. The coordinator ran with `toolPermission=request-review`, `allowNonWorkspaceAccess=false`, `permissions.allow=[]` (a refinement of the packet's recipe, recorded in AGY_INVOCATION.txt) and read `permission_mode = request-review` back from the init event. Nothing persistent was changed.
- Real run: the stream has 3 lines (init, the completed `user_input` step, the interruption); no `agent_response`, no tool step, no result event.
- Sealed directory: only the prompt (and the content-free probe prompt for the probes); environment `env -i HOME PATH`; no repository mount; no `--add-dir`. agy keeps its own conversation history under `~/.gemini/antigravity-cli`, so the prompt text is stored there (a residual, the diff only).

## Allowances used (PROPOSED caps)

Audit attempts 1 of 1 (consumed, no verdict); retries 0; probes 2 of 2; wall clock 09:31Z to 09:35Z; probe tokens 12,963 and 13,480; real-run tokens and cost UNKNOWN (no usage event); coordinator advisor calls 0.

## Custody

All artifacts were copied flat into this bundle and committed. Hashes: SHA256SUMS_AGY.txt. `AGY_AUDIT_RESPONSE_RAW.txt` does not exist because no result event was produced.
