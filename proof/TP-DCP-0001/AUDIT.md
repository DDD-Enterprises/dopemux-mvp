# TP-DCP-0001 Embedded Audit (Opus auditor, distinct from Sonnet implementer)

**Worktree:** `/Users/hue/code/dopemux-mvp-wt-dcp-build`
**Branch:** `dcp/core-contracts-tp-0001`
**Audit date (env):** 2026-06-03
**Method:** Independent re-run of all tests + direct read of every implemented file + ground-truth checks against `origin/main` + negative (mutation) tests of the lint/guard logic. Auditor did NOT edit any implemented file.

## Verdict: ACCEPT_WITH_RISKS

7 of 8 criteria fully PASS. C3 is PARTIAL: the fixture half is enforced (test `c` is green) and PROVISIONAL is a permitted enum member in every external/invented schema, but no schema **const-pins** `validation_state` to `PROVISIONAL_UNVERIFIED_ENFORCEMENT` — the contract would equally accept `REPO_CROSS_CHECKED`. Enforcement of PROVISIONAL lives only at fixture/test level, not in the schema. No invariant or red line is violated; the gap is a strict-reading enforcement nuance, not a correctness or safety failure.

## Criteria results (C1–C8)

| # | Criterion | Result | Evidence (file:line) |
|---|-----------|--------|----------------------|
| C1 | All 6 schemas valid JSON, draft-07, `additionalProperties:false` top-level, `schema_version` const ending `.v0`, top-level provenance+validation blocks | **PASS** | All 6 read directly. `$schema` draft-07 line 2 each; `additionalProperties:false` at top level (taxonomy:7, snapshot:7, pointer:7, evidence:7, chronicle:7, helper:7); `schema_version` is `const` ending `.v0` (e.g. pointer:28 `dcp-proof-pointer.v0`); `provenance`+`validation` declared in `properties` and listed in `required` for all 6. Test `(b)` lines 130-160 + `sanity` 422-439 green. |
| C2 | Provenance coverage is a SEPARATE assertion from fixture round-trip (non-circular) | **PASS** | `test_schema_round_trip` (test:81-114) is pure jsonschema validation — source contains **no** reference to `field_provenance` or provenance presence (verified via `inspect.getsource` → `field_provenance? False`). `test_provenance_presence_lint` (121-193) and `test_per_field_provenance_coverage` (349-415) are distinct functions. **Negative test:** deleting one `field_provenance` entry → round-trip (a) STILL PASSES, but coverage (b2) correctly FAILS (`Data field 'pointer_id' is absent from field_provenance`). Non-circularity proven empirically. |
| C3 | External/invented contracts have `validation_state == PROVISIONAL_UNVERIFIED_ENFORCEMENT` in schema AND fixture | **PARTIAL** | **Fixture half: PASS** — all 5 external/invented instances carry `validation_state`/`validation.state == PROVISIONAL_UNVERIFIED_ENFORCEMENT` (fixture:106,136,154,207,245), enforced by test `(c)` 200-236 (green). **Schema half: WEAK** — top-level `validation_state` is an **enum of 3** (`REPO_CROSS_CHECKED\|PROVISIONAL_UNVERIFIED_ENFORCEMENT\|DEFERRED`), NOT `const` (evidence:103-106, pointer:121-125, chronicle:107-111, helper:108-112). `dcp_control_snapshot` has **no** top-level `validation_state` at all — only `validation.state` enum (snapshot:47-53). PROVISIONAL is a permitted member everywhere but the contract does not REQUIRE it. The "in schema" obligation is met by declaration + enum-inclusion + description, not by const-enforcement. |
| C4 | `dcp_proof_pointer`: `auditor_verdict` and `validation_state` are SEPARATE fields (not the same field) | **PASS** | `dcp_proof_pointer.schema.json`: `validation_state` declared at 121-125, `auditor_verdict` declared at 126-129 — distinct sibling properties, both in `required` (17,18). Descriptions explicitly state they are DISTINCT and "must never be conflated/proxied" (124, 128). Test `(d)` 243-300 asserts both in properties + required, distinct descriptions, and fixture values differ (`auditor_verdict="PENDING"` 155 ≠ `validation_state="PROVISIONAL_UNVERIFIED_ENFORCEMENT"` 154). Green. |
| C5 | `DCP-RED-MERGE-SEAM-0001` present in fixture, names BOTH merge-seam paths | **PASS** | fixture:17 lane id `DCP-RED-MERGE-SEAM-0001`; `paths_forbidden` (21-24) names `src/dopemux_pr_merge_specialist/queue_drain.py` AND `scripts/batch_resolve_and_merge.py`; gate `hard_block` (19); provenance_tag `REPO_VALIDATED_BY_AUDIT` (20). **Ground-truth:** `git cat-file -e origin/main:<path>` confirms BOTH paths PRESENT in origin/main and `steward_gate.py` ABSENT — exactly matching the fixture's audit claim (25). |
| C6 | Defer guard: `dcp_mutation_class` / `dcp_approval_artifact` / `dcp_project_resource_map` schemas ABSENT from `schemas/dcp/` | **PASS** | Filesystem check: all 3 stems return no matches in `schemas/dcp/`. Test `(e)` 307-324 green. **Negative test:** planting a fake `dcp_mutation_class.schema.json` → guard correctly FAILS (`Deferred contracts found ... this stops the packet`); cleanup verified. |
| C7 | No live SHA computed in tests/schemas; fixture sha/digest values are obvious placeholders | **PASS** | `grep -niE "hashlib\|sha256(\|hexdigest\|subprocess\|popen\|check_output\|run("` across `tests/dcp/` + `schemas/dcp/` → only match is the substring `execute_or_dry_run(...)` inside a fixture **notes** string (descriptive, not executable). No hashing/subprocess imports anywhere. All digest values are literal `sha256:PLACEHOLDER-illustrative-not-computed` (fixture:145,150); `_sha_notice` banner (fixture:3). No 40/64-char real hex digest present. |
| C8 | Net-new files only; nothing outside TP allowlist; no edit to merge-seam files; implementer/auditor distinct | **PASS** | `git status --porcelain`: only `??` (untracked) entries; **nothing** tracked-modified/deleted. All 10 net-new files matched against the TP `commit.allowlist` programmatically → every one ALLOWED, none OUTSIDE. `git status --porcelain src/dopemux_pr_merge_specialist/ scripts/batch_resolve_and_merge.py` → empty (untouched). Implementer = Sonnet (`helper_model: claude-sonnet-4-6`, fixture:259), auditor = Opus (this actor) — distinctness asserted by orchestration + fixture field (see residual #2). `git diff --check` exits 0. |

**Score: 7/8 full PASS, 1 PARTIAL (C3 schema-enforcement half).**

## Test run (command + actual output tail)

```
$ python3 tests/dcp/test_dcp_contracts.py
DCP Core Contract Tests — TP-DCP-0001
  schemas dir : /Users/hue/code/dopemux-mvp-wt-dcp-build/schemas/dcp
  fixtures dir: /Users/hue/code/dopemux-mvp-wt-dcp-build/tests/dcp/fixtures

  PASS  (a) schema_round_trip
  PASS  (b) provenance_presence_lint
  PASS  (b2) per_field_provenance_coverage
  PASS  (c) external_invented_contracts_are_provisional
  PASS  (d) proof_pointer_auditor_verdict_distinct
  PASS  (e) deferred_contracts_absent
  PASS  sanity: all_schemas_have_v0_version

7 tests: 7 passed, 0 failed
[exit 0]

$ python3 -m pytest tests/dcp -q
.......                                                                  [100%]
[exit 0]   # 7 passed

$ git status --short
?? schemas/dcp/
?? task-packets/TP-DCP-0001.json
?? tests/dcp/

$ git diff --check
[exit 0]   # no whitespace/conflict-marker errors
```

Environment: `jsonschema 4.26.0` confirmed installed — round-trip test (a) is genuinely executed, NOT silently skipped via the `_HAS_JSONSCHEMA` fallback.

Negative (mutation) tests run by auditor, results:
- C2 non-circularity: drop one `field_provenance` key → (a) PASS, (b2) FAIL ✔ (lint catches gap independent of schema validity).
- C6 defer-guard: plant `dcp_mutation_class.schema.json` → (e) FAIL ✔ (guard is real, not vacuous). Workspace restored clean afterward.

## Residual risks / UNKNOWNs

1. **C3 schema-level enforcement gap (the one downgrade).** `validation_state` is enum-permitted, not `const`-pinned, in the 5 external/invented schemas; `dcp_control_snapshot` lacks a top-level `validation_state` entirely. A future instance could set `REPO_CROSS_CHECKED` and still pass jsonschema — only the fixture + test `(c)` currently prevent that. If the intent is that the contract itself must forbid non-PROVISIONAL for `.v0` external/invented shapes, add `"const": "PROVISIONAL_UNVERIFIED_ENFORCEMENT"` (or an enum of one) to those schemas in a follow-up. Not blocking for a contract-locking floor, but it is the difference between schema-enforced and convention-enforced.
2. **Implementer/auditor distinctness is asserted, not cryptographically provable from repo state.** It rests on (a) the orchestration that spawned a Sonnet implementer and this Opus auditor as separate actors, and (b) the fixture field `helper_model: claude-sonnet-4-6` (fixture:259). The repo artifacts alone cannot prove two distinct models authored vs audited; supervisor sign-off must be recorded separately in the proof bundle per invariant §12.
3. **`proof/TP-DCP-0001/PROOF.json` is ABSENT.** It is on the allowlist but the implementer produced no proof bundle — only this `AUDIT.md` exists in `proof/TP-DCP-0001/`. This is an incomplete implementer deliverable / open item, not a C8 allowlist violation. Supervisor should require PROOF.json before merge.
4. **Redundant mirror field (cosmetic).** 4 of 5 contracts carry a top-level `validation_state` that mirrors `validation.state`; `dcp_control_snapshot` carries only `validation.state`. Harmless under test `(c)`'s dual-check model, but the inconsistency + redundancy is worth normalizing in a later revision.
5. **Ground-truth scope.** Merge-seam path existence was verified against `origin/main` as it stands at audit time; the line numbers in the fixture note (queue_drain.py:617/2006/2017) were NOT independently re-counted (out of scope — the invariant is path-level non-import, which holds: this packet imports/wires nothing).

## Implementer identity: Sonnet | Auditor identity: Opus
