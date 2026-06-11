# Handoff — PR-854-B-PAL-OPENCODE-DOCKER

## Packet
`DMX-DCP-PR854-B-PROOF-STEWARDSHIP-001-CC`

## Executor
Claude Sonnet (claude-sonnet-4-6) — proof executor only, not merge authority

## Target
PR #854 (`dcp/chatgpt-mcp-ro-0006-dope-context-and-task-orchestrat`) @ head `15f235b8c60c473c301713f6e2f6251a449d07cf`

## Status
**BLOCKED**

---

## What was done

This packet collected runtime evidence for five B-items in PR #854. All evidence was captured fresh against the live PR branch; no stale uploaded proof files were used as authority.

### B-item results

| Item | Verdict | Key finding |
|---|---|---|
| 1 — pal-stdio runtime | **BLOCKED** | server.py crashes on startup (clink RegistryLoadError: openrouter unsupported) |
| 2 — OpenCode + PAL wiring | PASS (structural only) | verify-pal.sh exit 0; opencode CLI absent so runtime wiring NOT_VERIFIED |
| 3 — Docker Scout | SECURITY_ACCEPTED_WITH_RISKS | litellm CVE FIXED; CI Scout all 9 PASS; base OS inherited CVEs operator-accepted |
| 4 — PR #854 combined scope | OBSERVED | Mixed-scope confirmed; PR #862 clean 0001 carve confirmed |
| 5 — Readiness posture | BLOCKED_NOT_REQUESTED | merge_readiness remains BLOCKED_NOT_REQUESTED; no authority granted |

---

## Hard stops triggered

### BLOCKED_PAL_STDIO_WITH_STDIN_FAIL

pal-stdio `server.py` crashes immediately on startup:

```
clink.registry.RegistryLoadError: CLI type 'openrouter' is not supported by clink
(supported: gemini, codex, claude)
```

- Trigger file: `docker/mcp-servers/pal/pal-mcp-server/conf/cli_clients/openrouter-audit.json`
- Field: `"runner": "openrouter"` — not in `clink/constants.py` INTERNAL_DEFAULTS
- Secondary: `xai-grok-audit.json` with `"runner": "grok"` — also unsupported
- File on main: NO (introduced by PR branch)
- Container exit time: < 3 seconds

### BLOCKED_RESTART_LOOP

Under `docker compose up -d --build pal-stdio`:
```
state=restarting exit=1 restarting=true restart_count=8
```
(restart_count=8 observed in 30 seconds)

`restart: unless-stopped` causes immediate restart on crash → restart loop.

---

## Fix required

BLOCKED_NEEDS_NEW_PACKET — source file edits are forbidden in this packet.

**Fix options:**
- A: Add `openrouter` and `grok` to `clink/constants.py` INTERNAL_DEFAULTS
- B: Remove `openrouter-audit.json` and `xai-grok-audit.json` from `conf/cli_clients/`

Must also address `xai-grok-audit.json` (runner=grok) in the same fix.

---

## Remaining risks

1. pal-stdio startup crash — fix in new packet required before runtime is usable
2. xai-grok-audit.json secondary blocker (runner=grok)
3. verify-pal check 5 NOT confirmed (opencode CLI absent)
4. Docker Scout base OS inherited CVEs — operator acceptance required (documented in PR body)
5. PR #854 mixed-scope — clean 0001 in PR #862
6. CI check `review / review` FAILING at head `15f235b8c`
7. PAL chain same-tool (non-independent) — supervisor review mandatory

---

## Supervisor required

GPT-5.5 Pro must independently review this handoff before any merge decision.

All evidence files are in `proof/PR-854-B-PAL-OPENCODE-DOCKER/`. PROOF.json is the machine-readable index.

---

## What executor did NOT do

- Did not edit any source, config, docker, or script files
- Did not merge or request merge
- Did not self-certify
- Did not use dope-memory branch as proof authority
- Did not write to ConPort, dope-memory, dope-context, or task-orchestrator
- Did not perform model-routing runtime implementation or LiteLLM repair
