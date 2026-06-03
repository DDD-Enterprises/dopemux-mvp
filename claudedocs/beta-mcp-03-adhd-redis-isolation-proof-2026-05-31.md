# BETA-MCP-03 ADHD Redis Isolation Proof

## Status

VERIFIED_TARGETED for local acceptance validation. Commit SHA and PR URL are recorded in the final response after Git/GitHub mutation.

## Task Packet

- ID: `TP-BETA-MCP-03-ADHD-REDIS-ISOLATION`
- Path: `task-packets/generated/TP-BETA-MCP-03-ADHD-REDIS-ISOLATION.json`
- Worktree: `/Users/hue/code/dopemux-mvp-wt-beta-mcp-03`
- Branch: `fix/beta-mcp-03-adhd-engine-redis-isolation`
- Base commit: `69f17d066945a323f817557fc1d7a1e7d41a5a21`

## Authority Used

- Latest user instruction: `go`, following sequential remaining-work prompt execution.
- `AGENTS.md`
- `.claude/claude.md`
- `.claude/modules/shared/governance-principles.md`
- `claudedocs/codex-remaining-work-prompt-2026-05-30.md`
- `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Runtime/config truth: `compose.yml`, `src/dopemux/mcp/instance_overlay.py`, `services/adhd_engine/**`

## Analysis Performed

Observed:

- `compose.yml` exposes `DOPEMUX_INSTANCE_ID` for some MCP services but had no `ADHD_ENGINE_INSTANCE_ID` or `ADHD_ENGINE_REDIS_PREFIX` for `adhd-engine`.
- `src/dopemux/mcp/instance_overlay.py` writes `DOPEMUX_INSTANCE_ID` into per-instance env files but does not define an ADHD Redis prefix.
- ADHD Engine Redis state/cache keys were constructed as shared `adhd:*` keys in:
  - `services/adhd_engine/adhd_config_service.py`
  - `services/adhd_engine/api/routes.py`
  - `services/adhd_engine/core/activity_tracker.py`
  - `services/adhd_engine/core/engine.py`
  - `services/adhd_engine/core/feature_flags.py`
  - `services/adhd_engine/engine.py`

Chosen approach:

- Add a small deterministic helper in `services/adhd_engine/redis_keys.py`.
- Prefix keys from `ADHD_ENGINE_REDIS_PREFIX`, then `ADHD_ENGINE_INSTANCE_ID`, then `DOPEMUX_INSTANCE_ID`.
- Preserve historical unprefixed key behavior when none of those env vars is configured outside compose.
- Expose `ADHD_ENGINE_REDIS_PREFIX` in compose as `${ADHD_ENGINE_REDIS_PREFIX:-${DOPEMUX_INSTANCE_ID:-default}}`.

Rejected alternatives:

- Separate Redis databases: not selected because compose topology and Redis URL behavior would change more broadly.
- New compose overlay: rejected because `compose.yml` says normal runtime should not add overlay files.

## Change Summary

- Added `services/adhd_engine/redis_keys.py`.
- Scoped ADHD Engine attention, energy, profile, break, activity, notification, feature-flag, cache, and Pub/Sub state-change keys.
- Added `ADHD_ENGINE_REDIS_PREFIX` to the `adhd-engine` compose environment.
- Added focused tests for key prefix fallback, precedence, and config-service state reads.
- Registered the Task Packet in `task-packets/INDEX.md`.

## Validation Performed

PASS:

```text
python -m json.tool task-packets/generated/TP-BETA-MCP-03-ADHD-REDIS-ISOLATION.json >/dev/null
exit: 0
```

```text
python -m jsonschema -i task-packets/generated/TP-BETA-MCP-03-ADHD-REDIS-ISOLATION.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit: 0
note: jsonschema CLI emitted a deprecation warning only.
```

```text
python -m pytest services/adhd_engine/tests/test_redis_keys.py services/adhd_engine/tests/test_adhd_config_service.py -q
34 passed
exit: 0
```

```text
PYTHONPATH=services python -m pytest services/adhd_engine/tests/test_activity_tracker.py -q
13 passed
exit: 0
```

```text
python -m compileall services/adhd_engine
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

```text
python -m pytest services/adhd_engine/tests/test_feature_flags.py services/adhd_engine/tests/test_api_caching.py services/adhd_engine/tests/test_activity_tracker.py -q
exit: 2
reason: test_feature_flags.py collection failed with ModuleNotFoundError: No module named 'adhd_engine.feature_flags'.
```

```text
PYTHONPATH=services python -m pytest services/adhd_engine/tests/test_api_caching.py services/adhd_engine/tests/test_activity_tracker.py -q
exit: 1
reason: test_api_caching.py returned eight 503 response failures; activity tracker tests passed in the same run.
```

NOT_RUN:

- `docker compose up` / live service startup: not required for this packet and would mutate local runtime state.
- Live Redis collision test with two worktrees: not run because it requires live services.
- Full repository test suite: outside this packet's narrow validation scope.

## Codereview Status

PASS: self-review of the diff found no Redis topology changes, no dependency additions, and no changes outside the packet allowlist.

## Precommit Status

PASS:

```text
pre-commit run --files compose.yml services/adhd_engine/redis_keys.py services/adhd_engine/adhd_config_service.py services/adhd_engine/api/routes.py services/adhd_engine/core/activity_tracker.py services/adhd_engine/core/engine.py services/adhd_engine/core/feature_flags.py services/adhd_engine/engine.py services/adhd_engine/tests/test_redis_keys.py task-packets/INDEX.md task-packets/generated/TP-BETA-MCP-03-ADHD-REDIS-ISOLATION.json claudedocs/beta-mcp-03-adhd-redis-isolation-proof-2026-05-31.md
exit: 0
```

Hooks reported PASS for documentation validators, markdownlint, trailing whitespace, end-of-file checks, and root hygiene.

## Commit / PR

- Commit SHA: recorded in final response after commit creation.
- PR URL: recorded in final response after PR creation.

## Remaining Uncertainty / Risk

- Runtime isolation is validated by key construction and compose rendering, not by a live two-worktree Redis collision test.
- Existing `test_api_caching.py` harness failures remain unresolved in this packet.
- Existing `test_feature_flags.py` import-path failure remains unresolved in this packet.

## Rollback Plan

Revert the single commit for this branch, removing the compose env var, `redis_keys.py`, key helper callsites, focused tests, Task Packet/index entry, and this proof note.
