# AUDIT-01 — Final audit record and coordinator adjudication

**Authority**: NONE. **Subject**: `fix/cmd-repair-001` head `70eb50363f2cb1ff59758a9321faf9d033684b40` (frozen diff sha256 `3ed3a84060ece85437cc68f99c46dc9378c473c77b18d237cab046ea62a253cc`, base `95e95bee88cae5e6c95e6e34f7c28bb423ad9496`).
**Auditor verdict**: `FAIL` (1 BLOCKING, 1 HIGH, 2 MEDIUM, 1 LOW). The one authorized audit attempt is spent. No retry has been made.

## Route (operator-approved packet-specific fallback)

- **Approval**: operator chat 2026-10-16: "Approve a packet-specific fallback auditor for MACRO-DMX-CMD-REPAIR-001: agy --model gemini-4-argon-high, input limited to the frozen diff at 70eb50363 plus the audit contract, no repo mount, no secrets, recorded as auditor_model gemini with a note that exact-model evidence is unavailable."
- **Why a fallback**: the documented exact model `gemini-3.1-pro-high` is absent from `agy models` (v1.3.6).
- **Tool and model**: `auditor_tool: agy`; `auditor_model: gemini` (generic). The init event echoed `gemini-4-argon-high`; the model's self-report was "Gemini (Google; exact version string not verifiable)". **Exact-model evidence is unavailable.**
- **Invocation**: `INVOCATION.txt`. Run from a sealed directory outside the repo, with `--sandbox --disable-slash-commands --output-format stream-json`. `--mode plan` had no effect with slash commands disabled (agy warning in `agy_err.txt`).
- **Input**: `AUDIT_PROMPT.txt` (sha256 `c5366bb6…`), containing the contract and the frozen diff only. No repo mount.
- **Scan**: the diff was scanned for secrets before sending; the only hits were `task-orchestrator` false positives.
- **Run**: started 2026-10-16T20:27Z local, 209.7 s, 1 turn, `SUCCESS`; 32,942 in / 20,531 out tokens.
- **Containment (structural)**: the stream has 924 events: `init` ×1, `step_update` ×924 (one `user_input`, 923 `agent_response`), `result` ×1. **No tool step** appears, and the auditor declared `tools_used: none`. The global MCP servers were reachable but unused.
- **Independence**: different model family from the Claude implementers. Independence class DIFFERENT_FAMILY; provider-attested model UNKNOWN.

## Findings and adjudication

The auditor was sealed to the diff, so some "UNKNOWN" answers are resolvable from the repo. The adjudication below uses repo source.

| ID | Auditor sev | Adjudication | Evidence |
|---|---|---|---|
| F1 | BLOCKING | **CONFIRMED** (coordinator view: MEDIUM, pre-existing semantics but missed by W01). `mem-search.md` and `mem-query.md` still say "decisions and caveats" using `search_content`, which searches only decisions and progress. Caveats live in custom_data (`get_custom_data`, category `caveats`). | `enhanced_server.py:1452` handler ("decision/progress records"); `server.py` docstring; the two files' text |
| F2 | HIGH | **CONFIRMED**. `_SCRIPT_REF`'s lookbehind excludes `/`, so `./scripts/x.sh` is never matched. The base `safe.md:63` used `./scripts/set-profile.sh`, which the gate misses. W04's base-tree control therefore undercounted check 4 (3 found; set-profile was the 4th). | Ran the regex: `./scripts/set-profile.sh` → no match, `python scripts/x.py` → match |
| F3 | MEDIUM | **CONFIRMED**. `_MCP_REF` cannot see `mcp__<server>__*` wildcards, so `dope-memory` and `dope-context` wildcard refs (`mem/recap.md:6,19`, `ctx/search-here.md:22`) go unchecked. A hyphenated suffix is truncated (`get_context-foo` → `get_context`). `/mcp <server> <tool>` prose is not checked. | Regex run; `rg` of wildcard refs |
| F4 | MEDIUM | **PARTLY RESOLVED**. `create_work_tree` exists in `mcp_tool_surfaces.json:263`. `pal` vs `pal-stdio`: `dx/implement.md` and `dx/note.md` use `mcp__pal__*`, while the catalog and the live session use `pal-stdio`. That mismatch was already listed out of scope in the issuance record and is pre-existing. `plan.md` and `plan-tasks.md` name tools in prose, so check 1 doesn't cover them. | `mcp_tool_surfaces.json:263`; `rg mcp__pal__` |
| F5 | LOW | **CONFIRMED, partly disclosed**. `search_content` has no `limit`, so "read the top N" does not cap the payload. `runbook-update.md:6` still says "small `limit` (3–5)". Category dumps through `get_custom_data` are a documented trade-off of R2/R3/R6. | `runbook-update.md:6`; server signatures |
| Q7 | UNKNOWN | **RESOLVED PASS** by repo evidence. `tests/arch` passes 195, and the snapshot equals `mcp_tool_surfaces.json` and `server.py` exactly. | pytest run; set comparison |
| Q1/Q4/Q8/Q9 | PASS | Concur (coordinator verified Q1/Q4 against allowlists and the pin diff). | |

**Coordinator note**: F1 is in part a coordination miss. The same fix as `caveat.md` (R6) was not applied to `mem-search.md` and `mem-query.md`, whose diffs showed only renames.

## Disposition

- **Immediate-return trigger fired**: final audit FAIL.
- **No repair has been made**. A repair would change the frozen subject and invalidate this audit. A second model audit is outside the single authorized audit.
- **§9 proof bundle**: NOT_RUN. It would freeze a failing subject. It will be built after a repair and re-audit, or recorded as FAIL if the operator stops here.
- **Repair candidate (needs operator authorization, W06)** — files: `mem-search.md`, `mem-query.md`, `runbook-update.md`, `tests/arch/test_claude_command_references.py`.
  - F1: caveats via `get_custom_data`; decisions via `search_content`.
  - F5: drop the stale "limit" advice.
  - F2: fix the lookbehind so `./scripts/…` matches.
  - F3: accept `*` and `_` in the right places; reject hyphen-truncation; also scan `/mcp <server> <tool>`.
  - Both regex fixes need fresh negative controls that include `./scripts/set-profile.sh` and a wildcard ref.
  - Then: re-run the gates and the arch suite, then one fresh final audit (a second model call — needs approval).
