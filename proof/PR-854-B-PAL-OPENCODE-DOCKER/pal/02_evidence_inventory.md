# PAL-2 — Evidence Inventory

## stage
PAL-2 Evidence Inventory

## tool_or_mode
UNAVAILABLE_MANUAL_STAGE (Claude Sonnet)

## model
claude-sonnet-4-6

## inputs_read
- opencode.jsonc
- scripts/opencode/verify-pal.sh
- config/instructions/pal-opencode-guide.md
- .opencode/agents/pal-planner.md
- .opencode/agents/pal-reviewer.md
- docker/mcp-servers-source/pal-stdio/Dockerfile (and docker/mcp-servers/pal-stdio/Dockerfile — IDENTICAL)
- docker/mcp-servers-source/pal-stdio/pal_stdio_proxy.py
- docker/mcp-servers/pal/pal-mcp-server/server.py (existence confirmed)
- docker/mcp-servers-source/pal/pal-mcp-server/start-pal.sh
- compose.yml pal-stdio service
- proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json (existing)

---

## 1. opencode.jsonc
- **Status**: OBSERVED
- File exists: `opencode.jsonc` (707 bytes, Jun 11)
- Registers local "pal" MCP server via `sh -lc docker/mcp-servers-source/pal/pal-mcp-server/start-pal.sh`
- Environment: OPENAI_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY, XAI_API_KEY as `{env:*}` placeholders (no secrets leaked to proof)
- Includes `pal-opencode-guide.md` in instructions
- Permission: `pal_*` → ask
- **Claim from PR body**: "opencode.jsonc registers local pal via docker/mcp-servers-source/pal/pal-mcp-server/start-pal.sh" → **VERIFIED_OBSERVED**

## 2. scripts/opencode/verify-pal.sh
- **Status**: OBSERVED
- File exists, executable (1699 bytes, Jun 11)
- Checks:
  1. opencode.jsonc exists → ✅
  2. config/instructions/pal-opencode-guide.md exists → ✅
  3. .opencode/agents/pal-planner.md exists → ✅
  4. .opencode/agents/pal-reviewer.md exists → ✅
  5. If `opencode` CLI in PATH: `opencode debug config`, checks for `"pal"` in output → ⚠️ best-effort (CLI may not be installed)
- **Claim from PR body**: "verify-pal.sh now passes fully" → **CLAIMED_ONLY** until fresh VERIFY_PAL.log captured (checks 1–4 structural, check 5 depends on opencode CLI)

## 3. config/instructions/pal-opencode-guide.md
- **Status**: OBSERVED
- File exists (2113 bytes, Jun 11)
- Contains full tool usage table, core chain, rules — real behavioral guide

## 4. .opencode/agents/pal-planner.md + pal-reviewer.md
- **Status**: OBSERVED
- Both files exist (319, 259 bytes)
- These are the agents that were added to satisfy verify-pal.sh check 3/4

## 5. docker/mcp-servers-source/pal-stdio/Dockerfile
- **Status**: OBSERVED
- File exists (667 bytes)
- docker/mcp-servers/pal-stdio/Dockerfile — **IDENTICAL** (diff confirmed)
- Compose.yml uses `docker/mcp-servers/pal-stdio/Dockerfile` — this path is valid
- CMD: `/app/.venv/bin/python server.py` — runs PAL `server.py` directly on stdio
- Copies from `docker/mcp-servers/pal/pal-mcp-server/` — server.py **CONFIRMED EXISTS** at that path

## 6. pal_stdio_proxy.py (CRITICAL DISTINCTION)
- **Status**: OBSERVED
- File exists at `docker/mcp-servers-source/pal-stdio/pal_stdio_proxy.py` (3553 bytes)
- **Contains known stub**: `"[PAL Proxy] Tool '{tool_name}' invoked. Full SSE streaming not yet implemented in proxy."`
- **CRITICAL**: The `pal_stdio_proxy.py` is NOT the Dockerfile entrypoint. The Dockerfile CMD runs `server.py` (real PAL HTTP server) not the proxy.
- The proxy file is present in the directory but unused as a runtime entrypoint.
- **Claim status**: "PAL stdio proxy stub risk" → **OBSERVED stub code but NOT active entrypoint** — risk is lower than stated in packet preamble
- **Residual risk**: Proxy file exists and could confuse future integrators; documentation should clarify it's not the active CMD

## 7. docker/mcp-servers-source/pal/pal-mcp-server/start-pal.sh
- **Status**: OBSERVED
- File exists (at `docker/mcp-servers-source/pal/pal-mcp-server/start-pal.sh`)
- Real launcher: sources `$REPO_ROOT/.env`, activates `.venv`, `exec python server.py`
- **Claim from PR body**: "start-pal.sh is real launcher" → **VERIFIED_OBSERVED**

## 8. compose.yml pal-stdio service
- **Status**: OBSERVED
- Service `pal-stdio`:
  - `build.dockerfile: docker/mcp-servers/pal-stdio/Dockerfile` (context: `.`)
  - `container_name: mcp-pal-stdio`
  - `restart: unless-stopped`
  - NO `stdin_open: true` / `tty`
  - NO ports exposed
  - Comment: "Docker MCP Toolkit execs into container for stdio transport"
- **Claim from PR body**: "No stdin_open; toolkit exec model; no restart loop in attached test" → **CLAIMED_ONLY** until compose restart test log captured

## 9. proof/DMX-DCP-MODEL-ROUTING-MVP-0001/PROOF.json (existing)
- **Status**: OBSERVED — STALE
- `source_reconstruction.warning`: "Do not treat this as a merge-readiness artifact until final capture is regenerated in the target checkout after staging."
- `b_items_status_on_854`: describes all 5 B items as provided, but all are CLAIMED descriptions, no attached log files
- `merge_readiness`: **BLOCKED_NOT_REQUESTED** ✓ (correct state preserved)
- `auditor_verdict`: PASS_WITH_RISKS (from prior dual audit on 0001 domain model, not B items)
- Does NOT contain a `pr854_b_evidence` section → **needs update in this packet**

---

## summary

| Item | File Status | Claim Status |
|---|---|---|
| opencode.jsonc | OBSERVED | VERIFIED |
| verify-pal.sh | OBSERVED | CLAIMED_ONLY (needs fresh VERIFY_PAL.log) |
| pal-opencode-guide.md | OBSERVED | VERIFIED |
| pal-planner.md + pal-reviewer.md | OBSERVED | VERIFIED |
| pal-stdio Dockerfile | OBSERVED (both paths identical) | VERIFIED (server.py path confirmed) |
| pal_stdio_proxy.py stub | OBSERVED | stub text confirmed BUT NOT active CMD |
| start-pal.sh (real launcher) | OBSERVED | VERIFIED |
| compose.yml pal-stdio service | OBSERVED | CLAIMED_ONLY (restart behavior needs test) |
| PROOF.json b_items_status | OBSERVED | STALE / NEEDS UPDATE |

---

## assumptions
- `pal_stdio_proxy.py` presence in the directory is legacy/documentation artifact — active CMD is `server.py`
- No secrets in any inspected file (env placeholders only)
- compose restart behavior is the primary unknown to prove

## risks
- Proxy file confusion (not the runtime, but misleading)
- verify-pal check 5 (opencode debug config) may warn rather than fail if opencode CLI absent
- Compose restart test is the most operationally uncertain test

## confidence
high

## next_action
Proceed to PAL-3: write runtime test plan
