# 01 — Executive Audit: UR-AUDIT-001R3

**Audit verdict:** `PASS_WITH_RISKS`
**Architecture disposition:** `ACCEPT_BEGIN_UR_TP_001`
**Original architecture verdict:** `READY_FOR_INDEPENDENT_AUDIT` — **supported** (the package was ready for
independent audit; that is a lower bar than "passes", which it also does with risks).
**Implementation may begin:** yes, with **UR-TP-001** (EXECUTABLE_AFTER_PATH_RESOLUTION).
**Findings:** P0 = 0 · P1 = 0 · P2 = 4 · P3 = 2.

## What was audited and how
A fresh, read-only, clean-room audit of `UR-ARCH-001` (20 deliverables, archive SHA-256
`9b78e2bd…d5e090`, verified match; extracted files byte-identical to the archive) against the live
`DDD-Enterprises/dopemux-mvp` at HEAD `b176747b339685e781de04268c46b7ae123abfbf`, which **equals the census
commit** — no commit-level drift. Kit integrity verified independently (106/106 files OK via `shasum -c`; five
nested archives CRC-OK). All 20 deliverables and the primary evidence packs were read in full. Bundle-01
provenance was resolved directly against Git objects. Runtime authority boundaries and package minimality were
verified against the live repository. Session controls were probed.

## Why the architecture is accepted
UR-ARCH-001 is an unusually disciplined, minimal, advisory-first design. The load-bearing properties hold up
under independent verification:

1. **Minimal, non-colliding location.** `src/dopemux/universal_router/`, `config/universal-router/`,
   `schemas/universal-router/`, `tests/universal_router/`, and `.dopemux/universal-router/` all have **zero
   tracked entries** at census — greenfield, no hidden second router. The `route` CLI noun is free; the existing
   noun is `routing` (`routing_cli.py:588`). A repo-wide search for router tokens found only 6 mentions, all in
   planning docs.
2. **Correct authority boundaries, verified against runtime.** DCP is a pure fail-closed classifier
   (`routing_classifier.py:1-13`); Freeflow, LiteLLM, RTE, Task Orchestrator, dopetask, proof/handoff, PR
   Steward all remain canonical for their slices and are *referenced, not absorbed*. `services/task-router` has
   **no tracked source** (correctly "do not revive"); `agent_orchestrator.py` and `services/agents/**` exist and
   are correctly `LEAVE_ISOLATED`. No duplicate proxy/quota/proof/handoff/execution/workflow/release authority.
3. **Unambiguous first-release posture.** READ_ONLY/ADVISORY/IN_PROCESS/OPERATOR_INVOKED/APPEND_ONLY, stopping
   at `ROUTE_RECOMMENDED`/`OPERATOR_ACCEPTED`. No first-release path reaches handoff or execution (hard
   invariants + state-machine limit + roadmap M1–M9 + packet scope-OUT + adapter `EXECUTE` "must not exist
   behind a hidden flag"). The `recommend` default write targets the **gitignored** `.dopemux/` workspace path
   (`.gitignore:299`), so it is not a tracked-repository write — resolving the READ_ONLY question cleanly.
4. **Rigorous safety semantics.** Model identity keeps `attested_actual_model=UNKNOWN` unless provider-attested
   (6-part acceptance test; proxy/request-id/self-report never suffice). Usage/cost keeps exact/estimated/
   session/unavailable separate with no token→credit invention and no subtraction overhead. Containment records
   an enforcement source per control and `PROMPT_REQUESTED` never satisfies enforcement. Sandbox denial is never
   provider unhealth. Environment failure **never** triggers premium escalation (checked across ten artifacts).
   Skipped audit ≠ pass; same-runner ≠ independent.
5. **Provenance conflict resolved, not hand-waved.** See below.

## Provenance resolution (headline)
Bundle-01 ships exact-authority filenames, but I verified via Git blob-id matching against the full 16,058-blob
census tree that **only 23/32 files are byte-identical to a tracked path**, and the highest-authority *root*
names are frequently absent or research-tier: `RULES.md`, `system-boundaries.md`, `TRUTH_SCOPE.md`,
`SYSTEM_TaskOrchestrator.md`, PAL doctrine and the misspelled `dopetask-cannonical-spec.json` have **no
byte-identical tracked file**; `TRUTH_*`/`SYSTEM_Dopemux`/`SYSTEM_RepoTruthExtractor` match **only**
`docs/research/…` copies; bundle `PM_PLANE.md`/`AGENTS.md` are **stale** vs the tracked root versions. By
contrast `PROJECT.md`, `ARCHITECTURE.md`, `SERVICE_CATALOG.md` are byte-identical tracked-root, and the proof/
handoff/adapter contracts are byte-identical to tracked `docs/governance/…` references. This **independently
confirms** the architecture's own C-001/UR-OQ-001 disposition (archive names do not prove tracked root
authority) and — critically — the material authority claims rest on **runtime code I verified**, not on the
weak-provenance documents. This audit therefore **supplies the Git evidence UR-OQ-001 requested**, closing its
authority-tracking axis; the only residual is a documentation repair (cite tracked paths in UR-TP-001).

## Findings (no P0/P1)
- **UR-AUDIT-R3-001 (P2, provenance):** UR-TP-001 must cite tracked canonical paths, not bundle names; treat
  `TRUTH_*` as research-tier; use current tracked PM_PLANE/AGENTS.
- **UR-AUDIT-R3-002 (P2, evaluation):** certification scope tuple omits `identity_confidence` and `task_class`
  (BenchmarkCertification also omits containment/network) — gates automatic routing.
- **UR-AUDIT-R3-003 (P2, contract):** contracts are prose "minimal-field" lists; strict schemas + fixtures are
  UR-TP-001's own gate and must be completed before sign-off.
- **UR-AUDIT-R3-004 (P2, task_packet):** canonical PR Steward invocation is UNKNOWN (UR-OQ-006) and gates the
  merge step of every repo-changing packet incl. UR-TP-001.
- **UR-AUDIT-R3-005 (P3, storage):** journal append-only relies on process-local triggers; recommend hash-chaining.
- **UR-AUDIT-R3-006 (P3, storage):** per-worktree journal fragmentation should be documented; journal path
  confirmed gitignored.

## First packet permitted
**UR-TP-001**, EXECUTABLE_AFTER_PATH_RESOLUTION: cite tracked canonical contract/authority paths
(UR-AUDIT-R3-001), pin the PR Steward invocation before opening the PR (UR-AUDIT-R3-004), and complete strict
schemas within the packet (UR-AUDIT-R3-003). No packet reaching handoff/execution may be issued in the first
release.

## Independence & model-identity limitations (stated plainly)
This run was **not** launched via the kit's `launch_claude_code_audit.sh`; an `advisor` process-review tool was
present in the harness and was **deliberately not invoked**, honoring the kit's clean-room prohibition. Network
egress was OS-blocked (verified: `PermissionError`), listed secret env vars were absent, and repository/kit-input
writes are sandbox-denied. Because a runner/model/session/file/network/MCP/write boundary set was **not**
end-to-end evidenced as the prescribed launcher would provide, this audit is **not** claimed to be independently
contained in the full sense — but a read-only artifact-and-runtime audit was fully performed. The auditor model
identity is **runner-configured, not provider-attested** (`RUNNER_CONFIGURED_NOT_PROVIDER_ATTESTED`); no
provider-attested model-identity claim is made for this session — the same posture the architecture requires of
its own routes.

## Git status confirmation
Baseline captured at start (`repo_status_before.txt`): HEAD = `b176747…`, 4 pre-existing tracked
modifications (`.claude/claude_config.json`, `mcp-proxy-config.yaml`, `mcp_catalog.yaml`,
`tests/unit/test_mcp_commands_catalog.py`) and 39 untracked entries — **all pre-existing and unrelated to the
router domain**. No repository writes were performed by this audit (read-only tooling only). End-of-audit
comparison is recorded in `COMMAND_LOG.md`.
