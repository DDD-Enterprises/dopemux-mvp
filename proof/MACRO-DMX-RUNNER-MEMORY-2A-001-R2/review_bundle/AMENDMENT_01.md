# MACRO-DMX-RUNNER-MEMORY-2A-001-R2 — Amendment 01: scope extension (W10)

**Operator words (verbatim, chat, 2026-10-31):** "Yes, extend 2A"

**In answer to (verbatim):** "Extend 2A to fix the two Dockerfiles and the broken CI test?"

The same extension was first asked as "Extend R2 to fix those three files (ADR-227 amendment for the Dockerfiles)?" after W06. The operator answered the second asking.

**Recorded at:** 2026-11-01 (UTC), by the team lead (Control Tower supervisor session).

## Why

Recorded in `W02_RETURN.md` (open item 1) and `W06_RETURN.md` (open item 1):

- **Neither memory image would start if rebuilt.** Both Dockerfiles copy modules one by one, and neither copies the new `auth_identity.py`, which the entry modules import unguarded. The two files are red-lane paths that ADR-227 does not exempt, and no R2 write surface lists them.
  - `services/working-memory-assistant/Dockerfile.dope-memory:47-51`
  - `docker/mcp-servers-source/conport/Dockerfile:30-38`
- **A CI-run integration test fails.** W01's two new ledger columns broke `tests/integration/test_dual_capture_convergence.py:250`: its column-less INSERT now fails on a column count. CI runs `tests/integration` (`ci-complete.yml:490`).

## What the operator authorized

1. **ADR-227 Amendment 1.** File-exact exemptions for exactly two more paths, bringing the total from 20 to 22. Every other path in those trees stays blocked.
   - `services/working-memory-assistant/Dockerfile.dope-memory`
   - `docker/mcp-servers-source/conport/Dockerfile`
2. **One `COPY` line for `auth_identity.py`** in each of those two Dockerfiles.
3. **An explicit column list** in that one integration test.
4. **A new workstream, W10,** to do this, under R2's existing authorization and gates.

## W10

| Field | Value |
|---|---|
| Packet | `task-packets/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/WORKSTREAMS/W10/TASK_PACKET.json` (copy: `W10_TASK_PACKET.json`) |
| Packet sha256 | `4594cd16023337b654b873a64a50de241373015017962548dc2e6eb9fa6aaf36` |
| Schema | `task_packet.v2` PASS |
| Depends on | W09, W01, W02 (all committed) |
| Lane | L3 |
| Route | claude-code-agent, `claude-sonnet-5-5`, effort UNKNOWN |
| Caps | 60 min, 600,000 tokens, 150 tool uses, 1 attempt + 1 retry |

`MACRO_PACKET.json` (sha256 `b7ffb083…`) is not rewritten. It pins W01-W09, and this record adds W10 beside it. R2's macro allowances absorb W10:

| Allowance | R2 cap | Used before W10 |
|---|---|---|
| Dispatches | 12 | 4 (W09, W01, W02, W06) |
| Subagent tokens | 12M | about 0.8M (W01, W02, W06), plus W09 |

## Still not authorized

The keychain procedure before W03; building or running any image; push or PR; signing; the audit route; token issuance; migrations against a real database; the enforce switch; the ADR-MCPINT-002 amendment; the live Codex run; merge.
