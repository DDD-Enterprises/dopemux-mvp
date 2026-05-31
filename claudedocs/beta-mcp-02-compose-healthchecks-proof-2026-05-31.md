# BETA-MCP-02 Compose Healthchecks Proof

## Status

VERIFIED_TARGETED for local validation. Commit SHA and PR URL are recorded in the final response after Git/GitHub mutation.

## Task Packet

- ID: `TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS`
- Path: `task-packets/generated/TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS.json`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-beta-mcp-02`
- Branch: `fix/beta-mcp-02-compose-healthchecks`
- Base commit: `69f17d066945a323f817557fc1d7a1e7d41a5a21`

## Authority Used

- Latest user instruction: `go`, following the previously identified next target, BETA-MCP-02.
- `AGENTS.md`
- `.claude/claude.md`
- `.claude/modules/shared/governance-principles.md`
- `claudedocs/codex-remaining-work-prompt-2026-05-30.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Runtime/config truth: `compose.yml`, `docker/mcp-servers/conport/Dockerfile`, `docker/mcp-servers/conport/start_with_info.sh`, `docker/mcp-servers/conport/enhanced_server.py`

## Analysis Performed

Observed targeted `depends_on` references before changes:

- `conport` used bare-list dependencies for `postgres` and `redis-primary`.
- `litellm` used a bare-list dependency for `postgres`.
- `task-orchestrator` used bare-list dependencies for `redis-primary` and `conport`.
- `adhd-engine` used a bare-list dependency for `redis-primary`.
- Existing `dopecon-bridge` and `dope-memory` `postgres` dependencies already used `condition: service_healthy`.
- `leantime` and `mysql_leantime` service blocks were not changed.

Observed target healthcheck status:

- `postgres`: healthcheck present, fail-closed with `pg_isready ... || exit 1`.
- `redis-primary`: healthcheck present with `redis-cli ping`.
- `conport`: healthcheck present but fail-open before this change because it used `curl -f http://localhost:3004/health || exit 0`.

Trace evidence:

- `docker/mcp-servers/conport/Dockerfile` already defines a fail-closed container healthcheck for `http://localhost:3004/health`.
- `docker/mcp-servers/conport/start_with_info.sh` starts `enhanced_server.py` on port `3004`.
- `docker/mcp-servers/conport/enhanced_server.py` registers `/health` and checks database plus Redis connectivity.

## Change Summary

- Converted affected `compose.yml` bare-list dependencies to mapping form.
- Set `service_healthy` for:
  - `conport -> postgres`
  - `conport -> redis-primary`
  - `litellm -> postgres`
  - `task-orchestrator -> redis-primary`
  - `task-orchestrator -> conport`
  - `adhd-engine -> redis-primary`
- Preserved non-target dependencies in the same blocks with explicit `condition: service_started`.
- Changed ConPort compose healthcheck from fail-open to fail-closed.
- Registered the Task Packet in `task-packets/INDEX.md`.

## Validation Performed

PASS:

```text
python -m json.tool task-packets/generated/TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS.json >/dev/null
exit: 0
```

```text
python -m jsonschema -i task-packets/generated/TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit: 0
note: jsonschema CLI emitted a deprecation warning only.
```

```text
python - <<'PY'
import yaml
from pathlib import Path
yaml.safe_load(Path('compose.yml').read_text())
PY
exit: 0
```

```text
targeted_compose_assertions: PASS
exit: 0
```

```text
docker compose -f compose.yml config --quiet
exit: 0
note: compose emitted unset environment variable warnings for ANTHROPIC_API_KEY, HOST_CODE_PARENT_DIR, HOST_PROJECT_RELATIVE_PATH, and LEANTIME_TOKEN.
```

```text
git diff --check
exit: 0
```

FAIL:

- None.

NOT_RUN:

- `docker compose up` / live service startup: not required for this packet and would mutate local runtime state.
- Live service health probes: not authorized for this packet.
- Task Orchestrator MCP context: attempted, but the MCP transport returned `Transport closed`.

## Precommit Status

PASS:

```text
pre-commit run --files compose.yml task-packets/INDEX.md task-packets/generated/TP-BETA-MCP-02-COMPOSE-HEALTHCHECKS.json claudedocs/beta-mcp-02-compose-healthchecks-proof-2026-05-31.md
exit: 0
```

Hooks reported PASS for documentation validators, markdownlint, trailing whitespace, end-of-file checks, and root hygiene. YAML hook had no matching files in this file set.

## Codereview Status

PASS: self-review of final diff found no out-of-allowlist edits and no mixed-form `depends_on` blocks. Non-target dependencies in modified blocks retain explicit `condition: service_started`.

## Commit / PR

- Commit SHA: recorded in final response after commit creation.
- PR URL: recorded in final response after PR creation.

## Remaining Uncertainty / Risk

- This validates compose syntax and dependency declarations, not actual cold-start behavior under a live Docker run.
- ConPort readiness now depends on its `/health` endpoint reaching database and Redis; that endpoint was traced in code but not exercised live.
- The hardcoded LiteLLM healthcheck token remains intentionally unchanged for the separate security packet.

## Rollback Plan

Revert the single commit for this branch, or restore the prior `compose.yml` `depends_on` blocks and ConPort healthcheck line, then remove the Task Packet/index/proof additions.
