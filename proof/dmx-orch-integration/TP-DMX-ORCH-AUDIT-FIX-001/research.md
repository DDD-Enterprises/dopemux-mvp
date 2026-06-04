# TP-DMX-ORCH-AUDIT-FIX-001 Research

## Scope

Audit the landed DMX-ORCH integration fixes and repair only observed misses that affect packet schema/proof validation, active runtime port authority, or destructive dope-context safety.

## Authority Used

- `AGENTS.md`: requires repo truth, Task Packets, validation, and proof before completion.
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`: active strict Task Packet schema.
- `compose.yml`, `services/task-orchestrator/Dockerfile`, and `services/task-orchestrator/app/main.py`: active task-orchestrator runtime uses `app.main` and port `8000`.
- `src/dopemux/pm/adapters/orchestrator.py`: PM adapter defaults to `http://localhost:8000`.
- `src/dopemux/orchestrator/validation/proof.py`: existing proof contract validator.

## Observations

- All 28 `task-packets/generated/TP-DMX-ORCH*.json` packets validated against the active schema in the audit run.
- Two ORCH proof bundles failed the existing proof validator: `proof/dmx-orch-integration/TP-DMX-ORCH-002/PROOF.json` and `proof/orchestrator/TP-DMX-ORCH-DOCS-003/PROOF.json`.
- `services/dope-context/src/mcp/server.py` exposed `_clear_index_impl` and `clear_index` with `workspace_path` and `target` only; deletion happened without a proof id, approval phrase, or repo-side guard.
- Active task-orchestrator runtime authority is port `8000`, but active or active-looking code still referenced port `3014` in startup output, integration tests, instance env mapping, `services/mcp-integration-bridge/main.py`, and monitoring-dashboard dope-context port extraction.
- `scripts/mcp/wire_claude_mcp.py` still contains a legacy Gradle/stdout task-orchestrator launch command with `--port=3014`. This packet does not rewrite that launcher because the correct replacement is a portable MCP launch contract, not a numeric port substitution.
- Historical docs, generated scans, and archive evidence contain many `3014` mentions. Those are not edited by this packet unless they are direct runtime consumers.

## Red Path

- `uv run python -m dopemux.cli orchestrator proof validate proof/dmx-orch-integration/TP-DMX-ORCH-002/PROOF.json --json-output` fails before proof normalization.
- `uv run python -m dopemux.cli orchestrator proof validate proof/orchestrator/TP-DMX-ORCH-DOCS-003/PROOF.json --json-output` fails before proof normalization.
- `PYTHONPATH=services/dope-context uv run pytest services/dope-context/tests/test_mcp_server.py::test_clear_index_tool -q` passes before this packet, proving the old helper deletes with no approval requirement.

## Planned Fixes

1. Normalize only the two failing proof bundles to the existing proof contract shape.
2. Add deterministic `proof_id` and exact `approval_phrase` requirements to `dope-context.clear_index`.
3. Update active task-orchestrator port consumers to port `8000`, while preserving non-default multi-instance port isolation.
4. Correct monitoring-dashboard dope-context health-port extraction from internal `3014` to internal `3010`.
5. Add this packet to `task-packets/INDEX.md`.

## Risks

- Changing `clear_index` is intentionally breaking for unguarded callers. The safety requirement outweighs compatibility because the tool deletes indexes.
- Instance B-E task-orchestrator host ports remain offset-based; only default instance A aligns with canonical `8000`.
- Archive and generated evidence still mention `3014`; this is accepted to avoid mutating historical records.
- The Claude MCP wiring script remains a legacy-path risk and needs the existing portable launch repair lane rather than an opportunistic port edit.
