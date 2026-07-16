# pal-stdio "No module named 'utils.model_context'" — Diagnosis (2026-07-16)

**Reported symptom:** During the installer audit (earlier session 59c47fc6, 2026-07-16), every
pal-stdio workflow tool call (planner / codereview / precommit) failed server-side with
`No module named 'utils.model_context'`, blocking the mandated PAL chain (recorded in memory
`installer-audit-2026-07-16`, line 20). Hypotheses to test: stale venv/image, or source-layout
change removing `utils/model_context` from PYTHONPATH.

## Verdict

Both hypotheses **DISPROVEN** as persistent causes. The current running container is healthy;
the module is present, is a proper package, imports correctly at startup and lazily, and there
is **no `sys.path`/PYTHONPATH mutation in the request path** that could shadow it. There is
**no static code/image/layout defect to patch.**

**Root cause of the audit-time error: UNKNOWN.** I did not demonstrate the mechanism that
produced it. What is proven: the three named hypotheses are false, the current server is healthy
end-to-end, and the audit-time traceback was not retained in the container log — so the trigger
is unresolved. The container was already healthy when this investigation began (externally
restarted ~18:15, ~4 min before the first probe). **No fix was applied by me** — I diagnosed and
verified; I did not repair.

A **separate, current** blocker was discovered and is the real thing standing between the user
and a working PAL chain: native provider credentials are broken (OpenAI key 401, Gemini quota
hard-zero); only OpenRouter works. This blocks real PAL model calls even though the import path
is fine.

## Launch path

`~/.claude.json` → `mcpServers.pal-stdio`:
```
docker exec -i mcp-pal-stdio /app/.venv/bin/python server.py
```
- Container `mcp-pal-stdio`, image `dopemux-pal-stdio:latest` (id 3cf5521b, built 2026-07-03).
- Image bakes the full PAL server via `COPY docker/mcp-servers/pal/pal-mcp-server/ .`
  (`docker/mcp-servers-source/pal-stdio/Dockerfile`). **No bind mounts** — code is a build-time snapshot.
- WorkingDir=/app, PYTHONPATH unset. `python server.py` ⇒ `sys.path[0]='/app'` (absolute, robust).

## Evidence (all current, this session)

| Check | Result |
|---|---|
| `/app/utils/model_context.py` present + `utils/__init__.py` present | YES (proper package) |
| `find_spec('utils.model_context')` in container | `/app/utils/model_context.py` |
| Import at server startup | Succeeds (server logs `utils.model_context` DEBUG lines) |
| Container `model_context.py` vs host source | **byte-identical** |
| Container `tools/workflow/workflow_mixin.py` vs host source | **byte-identical** |
| git history of `utils/model_context.py` | only a deps bump; no rename/move |
| pal source tree dirty? | clean |
| `os.chdir` / subprocess / threadpool in workflow path | none (import is fully in-process) |
| `sys.path.insert/append` / PYTHONPATH writes in request path | none (only in tests + docker healthcheck; `chat.working_directory` does expanduser + file-write only, no chdir/path-insert) |
| Container recreated today? | No — created 2026-07-04; only restarted 18:15 (ExitCode=0) |
| All 3 pal containers restart time | ~18:15 together = Docker-daemon/compose restart, not a crash |
| `listmodels` | PASS |
| single-step `planner` (self-contained, no model call) | PASS |
| single-step `codereview` → `_call_expert_analysis` → provider | Reached provider (no ModuleNotFound); failed only on OpenAI 401 |

## Why the import error can't be a persistent path defect

`server.py` is launched as a script from WorkingDir `/app`, so `sys.path[0]` is the absolute
`/app`. It stays `/app` regardless of any later `os.chdir` (and there is none). The module is a
real package on that path. Startup and lazy in-process imports both resolve. There is no
subprocess/executor that would run the import under a different `sys.path`. So normal operation
cannot yield `No module named 'utils.model_context'`. The audit-time occurrence was transient
(most plausibly a Docker daemon/container state hiccup; the audit-time traceback was not retained
in `/app/logs/mcp_server.log`, which only held older Gemini-429 tracebacks).

## Separate current blocker: provider credentials

- OpenAI (native): `401 Incorrect API key` (`sk-svcac…6K4A`).
- Gemini (native): `429 RESOURCE_EXHAUSTED`, `quota_limit_value: 0` in region `us-south1`
  (hard-zero quota, not transient rate limiting).
- OpenRouter: **works** — clean `chat` success with `openai/gpt-5-nano` (provider_used=openrouter).
  (Note: `anthropic/claude-3.5-haiku` slug returns OpenRouter 404 "no endpoints" — auth is fine,
  slug unavailable.)

**Implication:** PAL chain runs today only via OpenRouter model slugs. Native OpenAI/Gemini
model selections will fail with provider errors (different from the import error). Fixing the
native keys is a secrets/env change (update `.env`/compose, recreate container) — for the user
to authorize.

## Recommended actions

1. **No code/image change required** for the import error itself — verified healthy.
2. **Durability (prevent recurrence):** the pal-stdio/pal containers are fragile (see memory
   `reference-pal-mcp-container`). Add an idempotent ensure/restart step so a degraded container
   self-heals rather than surfacing as a cryptic import error. Interim recovery = restart the
   container: `docker restart mcp-pal-stdio`.
3. **Provider creds:** refresh the native OpenAI key and Gemini project quota, OR pin PAL to
   OpenRouter model slugs, so the chain isn't silently blocked at the model layer.

## Actions taken (2026-07-16 follow-up, user approved items 1/2/3)

1. **Import error (item 1):** nothing to patch — verified healthy. Recovery path is now the
   ensure-script below (or `docker restart mcp-pal-stdio`).
2. **Provider creds (item 2):** did NOT modify secret values (I can't enter/rotate API keys).
   - The invalid key lives in `.env` `OPENAI_API_KEY=sk-svcacct…` (401); `GEMINI_API_KEY` maps to
     the quota-0 project. Both come into the container via `compose.yml` service `pal-stdio`.
   - No clean *server-side* reroute exists: PAL tools require an explicit `model` arg, so
     `DEFAULT_MODEL` won't redirect bare native names (`gpt-5-mini` → native OpenAI → 401).
   - **Verified working today:** a full single-step `codereview` (workflow expert-analysis path)
     completed end-to-end with `openai/gpt-5-nano` (`provider_used: openrouter`). So the PAL chain
     is usable now via OpenRouter slugs (`openai/…`, `google/…`). User action to restore native
     providers: replace `OPENAI_API_KEY` in `.env` with a valid key + fix the Gemini project quota,
     then `docker compose up -d pal-stdio` to recreate with the new env.
3. **Durability (item 3):** added `scripts/ensure_pal_stdio.sh` — idempotent, fail-closed:
   ensures the container is up, probes real stdio health via an MCP `initialize`, restarts once and
   re-probes if degraded, exits non-zero if still broken. Also extended
   `scripts/mcp_health_check.sh` with a read-only stdio check for `mcp-pal-stdio` (the port-based
   script previously couldn't see the exec-based server at all) and made all checks non-fatal so the
   scan reports every server instead of aborting on the first HTTP failure.

## Files touched

- `claudedocs/pal-stdio-model-context-diagnosis-2026-07-16.md` (this report)
- `scripts/ensure_pal_stdio.sh` (new, executable)
- `scripts/mcp_health_check.sh` (added stdio check; checks made non-fatal)
