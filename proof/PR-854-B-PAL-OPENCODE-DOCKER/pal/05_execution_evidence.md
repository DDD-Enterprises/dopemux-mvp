# PAL-5 — Execution Evidence

## stage
PAL-5 Execution Evidence

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE (Claude Sonnet)

## model
claude-sonnet-4-6

## head_sha
15f235b8c60c473c301713f6e2f6251a449d07cf

---

## verify-pal result
**PASS** (exit 0)
- ✅ opencode.jsonc exists
- ✅ PAL behavior guide exists
- ✅ PAL agents exist
- ⚠️ opencode CLI not found in PATH — skipping runtime config check (expected, not a block)
- ✅ Basic wiring verification complete.
Log: `VERIFY_PAL.log`

---

## build result
**PASS** (exit 0)
- Image `dopemux-pal-stdio:pr854` built from `docker/mcp-servers-source/pal-stdio/Dockerfile`
- Build context: `.` (repo root)
- CMD confirmed: `/app/.venv/bin/python server.py` (runs real PAL server, not proxy)
Log: `PAL_STDIO_BUILD.log`

---

## stdin-attached result
**BLOCKED_PAL_STDIO_WITH_STDIN_FAIL**

Root cause:
```
clink.registry.RegistryLoadError: CLI type 'openrouter' is not supported by clink 
(supported: gemini, codex, claude)
```
Triggered by: `conf/cli_clients/openrouter-audit.json` with `"runner": "openrouter"` which
is not in `clink/constants.py` `INTERNAL_DEFAULTS`.

Also at risk: `conf/cli_clients/xai-grok-audit.json` with `"runner": "grok"` (also not in INTERNAL_DEFAULTS)

File on main: **NO** — `openrouter-audit.json` exists on PR branch but not in main.

Key finding: `pal_stdio_proxy.py` stub (Full SSE streaming not implemented) is NOT the active entrypoint.
The Dockerfile CMD runs `server.py` directly. The proxy file is present but unused at runtime.

Container exits < 3 seconds after start.
Log: `PAL_STDIO_WITH_STDIN.log`

---

## no-stdin result
CAPTURED — exit_code=124 (timeout; container alive after 10s using STALE CACHED image)

**Investigation finding**: Initial test used pre-existing `dopemux-pal-stdio:latest` (image `459c3d76c23f`)
which was built from an older version of the PAL server that handled `openrouter` correctly.
When forced rebuild is used, the no-stdin test also exits immediately with the same crash.
Log: `PAL_STDIO_NO_STDIN.log`

---

## compose restart result
**BLOCKED_RESTART_LOOP** — `restart_count=8` observed in 30 seconds

```
state=restarting exit=1 restarting=true restart_count=8
```

Initial compose test used stale cached image and showed `restart_count=0` (false pass).
Fresh `docker compose up -d --build pal-stdio` confirms the restart loop.
The container crashes on startup (same clink error) and `restart: unless-stopped` causes
immediate restart → restart loop.
Log: `PAL_STDIO_COMPOSE_RESTART_TEST.log`

---

## root_cause_analysis
**Bug**: `conf/cli_clients/openrouter-audit.json` defines `"runner": "openrouter"` but
`clink/constants.py` `INTERNAL_DEFAULTS` only supports `{"gemini", "codex", "claude"}`.

The PAL pal-mcp-server clink module was updated to enforce strict type checking against
`INTERNAL_DEFAULTS`, but the cli_clients config files were expanded with new runner types
(`openrouter`, `grok`) that were not added to `INTERNAL_DEFAULTS`.

**Fix needed** (BLOCKED_NEEDS_NEW_PACKET — cannot edit source files in this packet):
- Either: add `openrouter` and `grok` to `clink/constants.py` `INTERNAL_DEFAULTS`
- Or: remove `openrouter-audit.json` and `xai-grok-audit.json` from `conf/cli_clients/`

---

## Docker Scout classification
See: `DOCKER_SCOUT_CLASSIFICATION.md` (Phase 7)

## PR Steward latest-head state
See: `PR_STEWARD_LATEST_HEAD.md` (Phase 8)

---

## blockers
1. **BLOCKED_PAL_STDIO_WITH_STDIN_FAIL** — server.py crashes on startup (clink unsupported type)
2. **BLOCKED_RESTART_LOOP** — restart_count=8 under compose (same root cause)

## evidence_ledger
- verify_pal_pass: OBSERVED (logs)
- build_pass: OBSERVED (logs)
- stdin_crash: OBSERVED (container exit < 3s, full traceback)
- crash_root_cause: OBSERVED (registry.py:137 + openrouter-audit.json runner field)
- compose_restart_loop: OBSERVED (restart_count=8 in 30s)
- stale_cached_image_masking: OBSERVED (old `:latest` worked, fresh `--build` shows loop)
- file_not_on_main: OBSERVED (git show main: NOT FOUND)

## confidence
certain (all key facts OBSERVED with command evidence)

## verdict
BLOCKED — two hard stop conditions triggered
