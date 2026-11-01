---
id: ADR-227
title: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for the memory-spine identity files (dope-memory, ConPort, dopecon-bridge callers)
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-10-31'
last_review: '2026-10-31'
next_review: '2027-01-31'
prelude: Narrow DCP-RED-MERGE-SEAM-0001 carve-out that exempts exactly 20 named files under services/working-memory-assistant/, docker/mcp-servers-source/conport/ and services/dopecon-bridge/ so Runner Memory Wave 2A can add verified runner identity to dope-memory and ConPort (adr) for dopemux documentation and developer workflows.
status: accepted
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - MACRO-DMX-RUNNER-MEMORY-2A-001
    - ADR-224
    - ADR-226
    - ADR-MCPINT-002
---
# ADR-227: Narrow DCP-RED-MERGE-SEAM-0001 carve-out for the memory-spine identity files

════════════════════════════════════════════════════════════

## Status

* Accepted by the operator on 2026-10-31 (chat, verbatim "Accept ADR-227"; recorded in
  `proof/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/review_bundle/ADR227_ACCEPTANCE.md`). The text
  accepted is this file at commit `95c54c4ec`; only this status entry and the front-matter
  `status` changed on acceptance.
* Drafted by `TP-DMX-RUNNERMEM2A-R2-W09-REDLANE-CARVEOUT-001` (workstream W09 of
  `MACRO-DMX-RUNNER-MEMORY-2A-001-R2`). No workstream (W01, W02, W05) edited a red-lane path
  before this acceptance (design section 5.6, packet invariant C12).
* The operator chose this route on 2026-10-31 (`OPERATOR_RULINGS_R2.md`, ruling 1: "Narrow
  carve-out ADR (Recommended)").

## Date

* 2026-10-31

## Owners

* Supervisor (DDD-Enterprises); drafted by the W09 implementer (Claude agent session) for
  `MACRO-DMX-RUNNER-MEMORY-2A-001-R2`.

────────────────────────────────────────────────────────────

## Context

`DCP-RED-MERGE-SEAM-0001` is a PreToolUse hard-deny red lane
(`.claude/hooks/dcp_surface_guard.py`, backed by
`src/dopemux/dcp/red_lane_rules.py::FORBIDDEN_PATHS`). Three of its blanket patterns cover
the whole of:

* `services/working-memory-assistant/` (dope-memory),
* `docker/mcp-servers-source/conport/` (the ConPort server image source), and
* `services/dopecon-bridge/`.

PR Steward also classifies a PR that touches those trees as `dcp_boundary`.

Runner Memory Parity Wave 2A (design `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md`,
revision 2) gives dope-memory and ConPort verified per-runner identity on HTTP writes
(goals G1 and G2). The W00 go/no-go findings
(`proof/MACRO-DMX-RUNNER-MEMORY-2A-001/review_bundle/W00_FINDINGS.md`) found that W01
(dope-memory) and W02 (ConPort) are NO_GO for a Claude Code runner because every file they
must change is inside the blanket patterns, and that the in-repo ConPort callers under
`services/dopecon-bridge/` (W05) are in the same position. Packet invariant C07 makes that a
stop, not something to route around.

Precedent for relief is ADR-224 (two workflow files) and ADR-226 (dope-context eval
harness and a short list of service files). Both use a negative lookahead anchored with
`\Z` inside the existing deny pattern, and both keep `red_lane_scanner.py` content scanning
fully active.

Constraints:

* The exemption must be file-exact. A directory exemption would let the whole tree be edited
  and would need a `..` traversal companion rule (as ADR-226 needed for `eval/`).
* Every other path in the three trees stays blocked, including same-named files in other
  directories, suffix, prefix and case variants, and anything the allowlists do not name.
* `services/task-orchestrator/` is a non-goal of Wave 2A and stays fully blocked.
* The exemption is for the files Wave 2A needs; it is not a general lift of the seam.

────────────────────────────────────────────────────────────

## Decision

Replace three blanket patterns in `FORBIDDEN_PATHS` with the same patterns plus file-exact
negative lookaheads, each anchored with `\Z` and compiled with `re.DOTALL` (the ADR-224/226
construction):

```python
re.compile(
    r"^services/working-memory-assistant/"
    r"(?!dope_memory_main\.py\Z)"
    r"...  # nine files in total, listed below
    r".*\Z",
    re.DOTALL,
)
```

The same shape applies to `^docker/mcp-servers-source/conport/` (nine files) and
`^services/dopecon-bridge/` (two files).

### The 20 exempted files

**W01: dope-memory (`services/working-memory-assistant/`, 9 files)**

| File | Why (design section; W00 evidence) |
|---|---|
| `services/working-memory-assistant/dope_memory_main.py` | Server entry: required ids on HTTP writes, workspace binding check, auth mode, health capability (5.1, 5.5). |
| `services/working-memory-assistant/mcp_http.py` | The streamable HTTP surface and `POST /tools/*` write routes that carry the verified principal (5.1). The CI-run endpoint test pins this file. |
| `services/working-memory-assistant/auth_identity.py` | New file: bearer verification against the hashed token directory (5.2). |
| `services/working-memory-assistant/eventbus_consumer.py` | Ledger writer fed from Redis; records its self-asserted internal principal (5.3, operator ruling 3). |
| `services/working-memory-assistant/chronicle/store.py` | SQLite ledger store: writes the principal column and applies migrations on first use (5.8; W00 design change 6). |
| `services/working-memory-assistant/chronicle/schema.sql` | Canonical schema gains the nullable principal column (5.8). |
| `services/working-memory-assistant/chronicle/sqlite_migrations.py` | Registers the new automatic migration (5.8; W00 design change 6). |
| `services/working-memory-assistant/chronicle/migrations/v1_3_0_add_write_principal.sql` | New migration file: nullable `write_principal`, default `unverified` (5.8). |
| `services/working-memory-assistant/tests/test_mcp_http_endpoint.py` | The one dope-memory test CI runs (`ci-complete.yml`, W00 design change 13); it must be updated and stay green. |

**W02: ConPort (`docker/mcp-servers-source/conport/`, 9 files)**

| File | Why |
|---|---|
| `docker/mcp-servers-source/conport/server.py` | REST and SSE surface: auth on every mutating route, the in-image SSE proxy forwards tokens, adds the streamable HTTP app beside `sse_app()` (5.1, 5.4; W00 design changes 8, 14). |
| `docker/mcp-servers-source/conport/enhanced_server.py` | Enhanced tool surface that shares the write paths (5.1). |
| `docker/mcp-servers-source/conport/instance_detector.py` | Instance binding and the `shared` instance value (5.1). |
| `docker/mcp-servers-source/conport/conport_mcp_stdio.py` | The in-image stdio proxy forwards the caller's token to REST (5.3). |
| `docker/mcp-servers-source/conport/auth_identity.py` | New file: bearer verification (5.2). |
| `docker/mcp-servers-source/conport/schema.sql` | Canonical schema gains the principal column (5.8). |
| `docker/mcp-servers-source/conport/migrations/008_write_principal.sql` | New migration (5.8). |
| `docker/mcp-servers-source/conport/migrations/008_rollback.sql` | Its rollback: drop the column (5.8). |
| `docker/mcp-servers-source/conport/migrations/conport_migration_gate.py` | Extend `REQUIRED_MIGRATIONS` if the gate requires it (5.8). |

**W05: internal ConPort callers (`services/dopecon-bridge/`, 2 files)**

| File | Why |
|---|---|
| `services/dopecon-bridge/dopecon_bridge/clients.py` | ConPort REST writers (`/api/decisions`, `/api/progress`, `/api/custom_data`, `/api/custom_data/claim`) must send their principal's token (5.3; W00 internal-caller list). |
| `services/dopecon-bridge/ddg_mcp_stdio.py` | ConPort REST writers (`/api/instance/fork`, `/api/progress/promote`, `/api/progress/promote_all`) (5.3; W00 internal-caller list). |

Some of these files do not exist yet (the `auth_identity.py` pair, the `v1_3_0` and `008`
migrations); they are exempt by name so the workstream can create them.

### Invariants

* **No directory exemption.** Each lookahead names one file and ends in `\Z`, so there is
  no directory exemption and no `..` companion rule is needed (unlike ADR-226's
  `services/dope-context/eval/`). The existing traversal behaviour holds: a path spelled
  with `..` inside the tree does not match a lookahead and stays blocked on its lexical
  reading.
* Every other path under `services/working-memory-assistant/`,
  `docker/mcp-servers-source/conport/` and `services/dopecon-bridge/` stays hard-blocked,
  including near-miss names (`mcp_http.py.bak`, `xmcp_http.py`), same-named files in other
  directories (`services/dopecon-bridge/clients.py`, `.../sub/server.py`), case variants and
  embedded or trailing newlines.
* `services/task-orchestrator/` and `src/conport/` stay fully blocked. Of the 20 file names,
  `auth_identity.py` and `server.py` recur across trees; each is exempt only at its exact
  path.
* `red_lane_scanner.py` content rules (`TEXT_RULES`: merge-seam calls, Dopetask execution,
  network and subprocess calls, external-write endpoints, `LIVE_WRITE_READY`) are untouched
  and still apply to every exempted file. This ADR is a path-level exemption only.
* `tools/pr_steward/security_release_gate.py` imports `FORBIDDEN_PATHS` from
  `red_lane_rules.py` and therefore follows this change automatically: the gate stops
  classifying edits to exactly these 20 files as `dcp_boundary` and keeps classifying every
  other path in the three trees. No change to the gate is made or needed.
* `_FALLBACK_COMPILED` in `.claude/hooks/dcp_surface_guard.py` is unchanged; it never
  covered these trees, so the fallback-subset-of-live invariant still holds.
* The guard's control-character short-circuit and its case-folded and realpath candidates
  are unchanged. The case-folded reading can only add denials, so it never widens this
  exemption.

### Non-goals

* No content of any exempted file is changed by this ADR; the edits belong to W01, W02 and
  W05 after acceptance.
* No new exemption for any other file in these trees, for `services/task-orchestrator/`, or
  for the sibling files that stay blocked (for example
  `services/working-memory-assistant/conport_client.py`, which W00 found to be a mock and
  which is excluded from Wave 2A). A new exemption needs its own ADR or an amendment here.
* No change to `red_lane_scanner.py`, `dcp_surface_guard.py` or the PR Steward gate.

────────────────────────────────────────────────────────────

## Alternatives Considered

**A. Run W01, W02 and W05 on a non-Claude runner with a recorded `dcp_boundary` approval.**
Keeps the guard untouched, but leaves the seam as an obstacle for Claude Code on exactly
the files the memory-parity work lives in, and splits one feature across runners. The
operator chose the carve-out instead (ruling 1).

**B. Exempt the directories or whole trees.** Rejected: it reopens the entire dope-memory,
ConPort and bridge surface (including the unreviewed read and routing code) and needs a
traversal companion rule for every directory.

**C. A runtime allowlist file the guard reads.** Rejected on the ADR-224 grounds: a mutable
authority surface for a hard-deny boundary.

**D. Do nothing.** Wave 2A's memory-spine goals (G1, G2) cannot be met by Claude Code.

────────────────────────────────────────────────────────────

## Consequences

* **Easier**: W01, W02 and W05 can edit exactly their named files through the normal Edit
  and Write tools.
* **Unchanged**: the blocked set shrinks by exactly 20 exact paths.
* **Effectiveness depends on the session cwd.** The PreToolUse guard builds its repo
  root from the hook process's current directory (`NativeHookAdapter.project_root`,
  `src/dopemux/claude/native_hooks.py:275`) and loads `FORBIDDEN_PATHS` from the git
  top-level of that directory (`.claude/hooks/run_native_hooks.sh`). A session whose cwd is
  this worktree's root therefore uses the worktree's rules. The carve-out needs no change on
  `main` for work done in that worktree.
* **Failure modes introduced**: none identified. A lookahead that was written wrongly
  would fail closed (extra denial) rather than open, and the tests pin both directions.
* **Operator obligation**: accept this ADR before W01, W02 or W05 is dispatched.

────────────────────────────────────────────────────────────

## Migration Strategy

1. W09 lands this ADR (status `proposed`), the `red_lane_rules.py` change and the tests
   (`tests/test_dcp_surface_guard.py`, `tests/unit/runner_memory_2a_r2_w09/`).
2. The operator accepts the ADR text (status becomes `accepted`, with a decision date).
3. W01, W02 and W05 edit only the files listed above.
4. When Wave 2A is complete the exemptions stay in force for maintenance of those files; an
   operator may narrow or remove them with a later ADR.

Rollback: `git revert` the W09 commit. That restores the three blanket patterns and removes
the tests and this ADR. Nothing is pushed or deployed by this change.

────────────────────────────────────────────────────────────

## Verification

* `uv run --frozen --extra test pytest -q tests/unit/runner_memory_2a_r2_w09/ tests/test_dcp_surface_guard.py`
  (`tests/test_dcp_surface_guard.py` sits at the `tests/` root, which CI does not run, so it
  is run explicitly).
* Every exempted path is allowed for `Edit`, `Write` and `NotebookEdit`. Near-misses (same
  name in another directory, suffix and prefix variants, case variants, embedded and
  trailing newlines, trailing slashes at the regex layer, `..` segments, a symlink at an
  exempt name) stay blocked. At least five other files in each of the three trees stay
  blocked, and so does `services/task-orchestrator/`.

## Notes

* Related: ADR-224 and ADR-226 (precedents), ADR-MCPINT-002 (agent exposure and read plane;
  amended separately by Wave 2A for the memory servers), design
  `docs/91-rfc/rfc-2026-10-30-runner-memory-parity-2a.md` section 5.6 (revision 2).
* The guard reduces a trailing slash with `pathlib.Path`, so `file.py/` reaches it as
  `file.py`. A write to that spelling fails with `ENOTDIR`; the regex layer still treats the
  slash variant as not exempt.
