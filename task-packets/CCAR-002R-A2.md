---
id: CCAR-002R-A2
title: CCAR-002 PR 1176 Evidence and Test Correctness Repair
type: explanation
owner: '@hu3mann'
author: Claude Sonnet
date: '2026-08-03'
last_review: '2026-08-03'
next_review: '2026-08-31'
prelude: Narrow R3 evidence/test-correctness repair plus R4 signed exact-head Claude
  audit return for PR 1176 after CCAR-002R R2 left two surviving evidence defects
  and two surviving review defects undiagnosed by the Claude PASS_WITH_RISKS audit.
---
# Task Packet: CCAR-002R-A2 · PR #1176 · Evidence + Test Correctness Repair

════════════════════════════════════════════════════════════

## Packet Identity

| Field | Value |
|---|---|
| Packet | `CCAR-002R-A2` |
| Parent | `CCAR-002R` |
| Series | `CCAR-SERIES-001` |
| Repository | `DDD-Enterprises/dopemux-mvp` |
| Existing PR | `#1176` |
| Existing branch | `feat/CCAR-002-normalized-agent-persona-catalog` |
| Required starting PR head (R2) | `1cb80e40f0f818389307aedeb14aaaceaa3e8ed1` |
| Audited head bound by canonical proof (R1) | `41bc62071ce4e152a3b2040e408eda0c830fb215` |
| Current live blocker | Release evidence still blocked: canonical proof binds R1, not R2; R2 carries undiagnosed defects |
| Risk | Low-to-medium — proof-truthfulness + test-self-healing contract, no architecture change |
| Status | `READY_FOR_R3_REPAIR_THEN_R4_PROOF` |

This is a bounded amendment to an existing, mergeable, green-gates PR — not a reopening of the CCAR-002 architecture.

────────────────────────────────────────────────────────────

## Decision (inherited supervisor ruling)

```text
CCAR_002R_A1_NOT_COMPLETE
PR_1176_RELEASE_EVIDENCE_STILL_BLOCKED
MERGE_NOT_AUTHORIZED
CCAR_003_NOT_AUTHORIZED
```

Green gates are real. The completion claim is still not supportable: the Claude Sonnet `PASS_WITH_RISKS` audit is correctly bound to R1, not to the current R2 head, and R2 still carries defects the audit never evaluated.

### Observed blocking evidence

1. `proof/CCAR-002/SOURCE_MANIFEST.json` still contains an absolute local worktree path under `worktree`. That violates the packet's explicit no-private-absolute-path invariant.
2. `proof/CCAR-002/NORMALIZATION_REPORT.md` still records the literal string `$(date -u +%Y-%m-%dT%H:%M:%SZ)` instead of an actual timestamp. It is not truthful generated evidence.
3. `test_generation_idempotent` regenerates the catalog before running `--check`, so that test can still self-heal committed drift instead of detecting it.
4. `_scan_model_ids()` uses `re.findall()` with a capturing Claude model group, returning fragments such as `sonnet` instead of the complete match. Low risk, but an unresolved known finding.

The Claude audit did not identify these surviving defects. Its verdict therefore cannot close the previously documented review findings.

### Classification tokens (pre-repair)

```text
CCAR_002R_A1_EVIDENCE_DEFECT
CCAR_002R_A1_TEST_SELF_HEALING_DEFECT
CCAR_002R_A1_SCANNER_TRUNCATION_DEFECT
PR_1176_NOT_READY
```

────────────────────────────────────────────────────────────

## Objective

1. **R3** — Fix the two evidence defects and two review defects listed above, honestly regenerate implementation proof, and add a focused scanner regression test.
2. **R4** — Fresh Claude Sonnet audit against exact R3; finalize, sign, and verify a canonical proof-only commit under `proof/pr_merge/embedded-audit/pr-1176/**`; require local acceptance + trusted embedded audit success + PR Steward READY.

No force push, history rewrite, merge, or CCAR-003 execution.

────────────────────────────────────────────────────────────

## Authority

### Execution authority

1. Explicit operator instruction / supervisor decision
2. This active packet
3. Parent `CCAR-002R` and `CCAR-002` invariants that remain applicable
4. Current `RULES.md`, `AGENTS.md`, proof and audit contracts
5. Tool defaults

### Truth authority

1. Live PR head, Git history, current checks, workflow logs, runtime scripts, schema validation
2. Trusted `main` audit acceptance scripts and allowed-signers file
3. Current proof and embedded-audit contracts
4. Packet claims
5. Inference

Local `PASS`, local `READY`, PR description, or handoff summary cannot override contradictory repository content, and PR Steward `READY` does not override it either.

────────────────────────────────────────────────────────────

## Scope

### IN — R3 (evidence + test correctness repair)

* Remove the absolute `worktree` value from `proof/CCAR-002/SOURCE_MANIFEST.json` (no code path reads that key; drop it rather than fabricate a repo-relative substitute).
* Replace the literal `$(date -u +%Y-%m-%dT%H:%M:%SZ)` in `proof/CCAR-002/NORMALIZATION_REPORT.md` with a concrete UTC timestamp taken from an actual regeneration run of the builder.
* Reorder `test_generation_idempotent` so `--check` runs against the **committed** catalog before any regeneration, so committed drift cannot be masked.
* Change the Claude regex group in `_scan_model_ids()` to non-capturing (or switch to `finditer(...).group(0)`) so full matches are returned, not bare capture fragments.
* Add a focused regression test pinning full-match behavior of `_scan_model_ids()`.
* Regenerate `config/commandcode/normalized_agent_persona_catalog.yaml` and `proof/CCAR-002/**` implementation evidence honestly.
* Preserve all source agent/persona files **byte-for-byte**.

### IN — R4 (canonical audit return)

* Fresh **Claude Sonnet** independent audit against **exact R3** (not R2, not any prior head).
* Finalize `proof/pr_merge/embedded-audit/pr-1176/PROOF.json` completely **before** signing.
* Sign the exact final bytes; verify signature locally against trusted `main` allowed-signers.
* Require `local_audit_acceptance accepted=true` for prospective R4 head.
* Commit **only** `proof/pr_merge/embedded-audit/pr-1176/**` as R4.
* Push R3+R4; observe trusted embedded audit success and PR Steward READY.

### OUT

* Force push, rebase of pushed history, amend of any pushed commit, squash, history rewrite.
* Merge of PR #1176.
* CCAR-003 planning or implementation.
* Reopening the CCAR-002 architecture or catalog schema.
* Source agent/persona content changes.
* Runtime activation of catalog (agents, skills, hooks, MCP, DCP, Universal Router, role routing).
* Authoring the embedded audit for one's own work (Claude may not audit changes it authored in this same session — route audit per REVIEW-001).

────────────────────────────────────────────────────────────

## Invariants

1. Starting PR head must be exactly R2 = `1cb80e40f0f818389307aedeb14aaaceaa3e8ed1`. Stop if different.
2. Worktree clean before R3 content is committed (except intentional staged R3 files).
3. R3 changes only the R3 allowlist (below).
4. All agent/persona **source** files remain byte-identical across R3 and R4.
5. `proof/CCAR-002/SOURCE_MANIFEST.json` contains no absolute or private machine path under any key.
6. `proof/CCAR-002/NORMALIZATION_REPORT.md`'s `**Generated**` field is a concrete UTC timestamp, not an unexpanded shell command substitution.
7. `test_generation_idempotent` runs `--check` against the committed catalog before any regeneration.
8. `_scan_model_ids()` returns full matched tokens, never bare capture-group fragments; pinned by a focused test.
9. Existing CCAR-002 product invariants preserved: 9 base agents; persona coverage; no model IDs in catalog/schema; persona authority booleans false; no unauthorized route activation; schema `additionalProperties=false`; builder `--check` passes.
10. Fresh independent audit is bound to **exact R3**, not R4 and not any prior head.
11. `PROOF.json.head_sha` equals **R3** exactly (not R4).
12. `PROOF.json.pr_number` = `1176`; `repo` = `DDD-Enterprises/dopemux-mvp`.
13. R4 changes only `proof/pr_merge/embedded-audit/pr-1176/**` relative to R3.
14. No tracked file changes after R4.
15. `local_audit_acceptance` returns `accepted=true` for prospective R4 before push.
16. Live CI success and PR Steward READY outrank local claims.
17. No merge; no force push; no CCAR-003.

If an invariant appears impossible, stop and report.

────────────────────────────────────────────────────────────

## Allowed Files

### R3 allowlist

```text
proof/CCAR-002/SOURCE_MANIFEST.json
proof/CCAR-002/NORMALIZATION_REPORT.md
proof/CCAR-002/**
scripts/commandcode_router/build_normalized_catalog.py
tests/commandcode_router/test_normalized_catalog.py
config/commandcode/normalized_agent_persona_catalog.yaml
task-packets/CCAR-002R-A2.md
task-packets/CCAR-002R-A2.json
```

### R4 allowlist

```text
proof/pr_merge/embedded-audit/pr-1176/**
```

No other tracked file may change on R4.

────────────────────────────────────────────────────────────

## Commit Topology

```text
1cb80e40f0f818389307aedeb14aaaceaa3e8ed1   R2 (current, mergeable, canonical proof still bound to R1)
    |
    v
R3  evidence + test correctness repair
    |  fresh Claude Sonnet audit targets exact R3
    v
R4  signed canonical proof-only return
       changes only proof/pr_merge/embedded-audit/pr-1176/**
       PROOF.json.head_sha == R3
       final PR head == R4
```

Do **not** set `PROOF.json.head_sha == R4`.

────────────────────────────────────────────────────────────

## Validation Gates

### R3 gates

| Gate | Expect |
|---|---|
| `SOURCE_MANIFEST.json` has no absolute path | no `/Users/`, `/home/` under any key |
| `NORMALIZATION_REPORT.md` `**Generated**` field is a real timestamp | matches `YYYY-MM-DDTHH:MM:SSZ`, not `$(date ...)` |
| `test_generation_idempotent` checks committed catalog first | exit 0, order verified in diff |
| `_scan_model_ids()` full-match regression test | exit 0 |
| Builder `--check` | exit 0 |
| Focused `tests/commandcode_router/test_normalized_catalog.py` | exit 0 |
| Source agent/persona SHA-256 | match manifest |
| R3 path allowlist | exact |

### R4 gates

| Gate | Expect |
|---|---|
| Claude Sonnet audit bound to R3 | recorded tool/model/invocation/exit/findings |
| `PROOF.json.head_sha` | equals R3 |
| Signature verify | valid vs trusted main signers |
| `local_audit_acceptance` | `accepted=true` |
| R4 path set | only `proof/pr_merge/embedded-audit/pr-1176/**` |
| Trusted embedded audit | success on final head |
| PR Steward final readiness | READY |
| PR merge state | open, unmerged |

────────────────────────────────────────────────────────────

## Success Criteria

1. Both evidence defects and both review defects are corrected, not just re-described.
2. Fresh signed proof on exact R3; final head is proof-only R4.
3. Local acceptance true; trusted embedded audit success; Steward READY.
4. PR #1176 still open; no merge; CCAR-003 not started.

### Success tokens (only after live gates)

```text
CCAR_002R_A2_R3_REPAIR_PASS
CCAR_002R_A2_R4_AUDIT_RETURN_PASS
PR_1176_READY
CCAR_002_RELEASE_EVIDENCE_UNBLOCKED
```

Until then retain:

```text
CCAR_002R_A1_NOT_COMPLETE
PR_1176_RELEASE_EVIDENCE_STILL_BLOCKED
```

────────────────────────────────────────────────────────────

## Stop Conditions

Stop and report if:

* head is not exactly the pinned R2 SHA;
* source agent/persona bytes change;
* the focused tests fail after repair;
* Claude Sonnet audit unavailable or non-passing;
* signature verification fails;
* local acceptance false;
* live embedded audit or Steward not READY after honest R4;
* any force-push or merge pressure appears.

────────────────────────────────────────────────────────────

## Handoff Template (after R4 live gates)

```text
packet: CCAR-002R-A2
pr: 1176
start_head: 1cb80e40f0f818389307aedeb14aaaceaa3e8ed1
R3: <sha>
R4: <sha>
audit_tool/model: claude / sonnet
local_acceptance: true
trusted_embedded_audit: success
pr_steward: READY
merge: NOT_DONE
ccar_003: NOT_AUTHORIZED
```
