# Independent L3 Audit — TP-DMX-TRUST-GATE-FAIL-CLOSED-001

**Audited commit (C1)**: `352a3d888d1ce5116b9af65d696fe62373728a7c`
**Parent / execution base**: `3e8fcc1c70c5b859dd651a1cd33c85eab837c93e`
**Auditor**: Claude Code `quality-engineer` subagent (Sonnet 5), independent of the implementer session — spawned with no prior conversation context, given only the repo, the commit SHA, and the task packet.
**Deviation from packet §9 preference**: The packet's preferred auditor is AGY `gemini-3.1-pro-high`. No live AGY invocation tool was available in this environment/session. Per the packet's own fallback rule ("If unavailable, use the repository's next permitted independent audit route and record the exact deviation"), the audit was routed through an independent Claude Code subagent instead. This deviation is recorded here explicitly.

## Verdict: PASS_WITH_RISKS

Both flagged risks are explicitly non-blocking. See full auditor output below, verbatim.

---

Confirmed `live_write_ready_status` default `UNDEFINED_AND_BLOCKING` is untouched by the diff (not in the changed hunks) — invariant 5 holds.

## Verdict: PASS_WITH_RISKS

**Commit audited:** `352a3d888d1ce5116b9af65d696fe62373728a7c` in `/Users/hue/code/dopemux-mvp-worktrees/tp-trust-gate-fail-closed-001`

### Files touched (14) — allowlist compliance: 14/14 in scope

| File | Allowlist match |
|---|---|
| `src/dopemux/dcp/control_snapshot.py` | explicit |
| `src/dopemux/dcp/red_lane_scanner.py` | explicit |
| `task-packets/TP-DMX-TRUST-GATE-FAIL-CLOSED-001.json` | explicit |
| `task-packets/TP-DMX-TRUST-GATE-FAIL-CLOSED-001.md` | explicit |
| `tests/dcp/fixtures/tp_dcp_0004_missing_tp0002_evidence/proof/TP-DCP-0001/PROOF.json` | `tests/dcp/fixtures/tp_dcp_0004_*/**` |
| `tests/dcp/fixtures/.../proof/TP-DCP-0003/MERGE_READINESS.json` | same glob |
| `tests/dcp/fixtures/.../proof/TP-DCP-0003/PROOF.json` | same glob |
| `tests/dcp/fixtures/.../schemas/dcp/README.md` | same glob |
| `tests/dcp/fixtures/.../schemas/dcp/dcp_control_snapshot.schema.json` | same glob |
| `tests/dcp/fixtures/.../task-packets/TP-DCP-0001.json` | same glob |
| `tests/dcp/fixtures/.../task-packets/TP-DCP-0003.json` | same glob |
| `tests/dcp/fixtures/.../task-packets/TP-DCP-0004.json` | same glob |
| `tests/dcp/test_dcp_0004_control_snapshot.py` | explicit |
| `tests/dcp/test_dcp_0005_red_lane_scanner.py` | explicit |

No `red_lane.py`, `proof_family.py`, `test_dcp_0003_proof_family_dispatch.py`, or `proof/TP-DMX-TRUST-GATE-FAIL-CLOSED-001/**` were touched at audit time — not required by the allowlist, and their absence is not a defect. Zero out-of-allowlist files. No scope creep found: both diffs are surgically confined to the identity-classification branch (`red_lane_scanner.py:213-234`, plus new MALFORMED_PROOF handling at 174-196) and the `_readiness` loop's new `elif` (`control_snapshot.py:491-495`). No unrelated refactors, no schema changes, no version bumps.

### F001 — independently verified closed

- Empty `{}` proof: `report.status = UNKNOWN`, `self_certification_status = UNKNOWN` (was `PASS`/`NONE` on parent — reproduced empirically).
- Missing implementer or missing auditor identity alone: same, `UNKNOWN`/`UNKNOWN`.
- Malformed JSON: now raises an explicit `MALFORMED_PROOF` `BLOCKER` finding (`red_lane_scanner.py:174-184`) instead of silently `continue`-ing past it, confirmed via `test_malformed_proof_json_does_not_return_pass`.
- Non-dict JSON root (e.g. a JSON array): new guard at `red_lane_scanner.py:186-196`, not explicitly tested but logically sound.
- Positive path (no regression): both identities present and distinct → `status = PASS`, `self_certification_status = NONE` — verified live via a standalone repro script, matching `test_distinct_identities_still_produce_none_self_certification`.
- CLI (`main()`) exits non-zero for the incomplete-proof case — verified by `test_cli_exits_nonzero_on_incomplete_proof`, which actually subprocess-invokes the module (not a mocked call).

**Parent-commit comparison (ran the pre-fix scanner against identical inputs):**
```
OLD single empty proof            -> status: PASS   self_cert: NONE
OLD order [complete-then-empty]   -> status: PASS   self_cert: NONE
OLD order [empty-then-complete]   -> status: PASS   self_cert: NONE
NEW single empty proof            -> status: UNKNOWN self_cert: UNKNOWN
NEW order [complete-then-empty]   -> status: UNKNOWN self_cert: UNKNOWN
NEW order [empty-then-complete]   -> status: PASS   self_cert: NONE   (see R1)
```
This proves the commit is a strict monotone improvement: every input that used to reach an unsupported PASS now either blocks or is unchanged from a legitimately-passing state. No input got *more* permissive.

### F002 — independently verified closed

- Constructed a live fixture (copy of `tp_dcp_0004_missing_tp0002_evidence`, which has zero artifacts of any kind for TP-DCP-0002) and ran `generate_control_snapshot()`: `snapshot_status = BLOCKED`, `blocking_reasons = ["TP-DCP-0002 evidence is incomplete or unproven (state=UNKNOWN)"]` (test `test_22_missing_prerequisite_packet_evidence_blocks_readiness` also asserts this).
- Additionally constructed the **CLAIMED** case not covered by the packet's own new test — a proof file present for TP-DCP-0002 with **no** task-packet file — and confirmed it is also caught: `snapshot_status = BLOCKED`, `blocking_reasons = ["TP-DCP-0002 evidence is incomplete or unproven (state=CLAIMED)"]`. This is the harder edge case the audit brief specifically asked to check, and it is handled by the same `elif state["state"] in (UNKNOWN, CLAIMED)` clause.
- Positive path (no regression): ran `generate_control_snapshot()` against `tests/dcp/fixtures/tp_dcp_0004_valid_snapshot_inputs` — `snapshot_status = READY`, `blocking_reasons = []`. Confirmed the fix does not over-block a genuinely complete prerequisite chain.

### Tests actually run

```
python3.12 -m pytest -v tests/dcp/test_dcp_0003_proof_family_dispatch.py \
  tests/dcp/test_dcp_0004_control_snapshot.py tests/dcp/test_dcp_0005_red_lane_scanner.py
→ 69 passed in 0.20s
```
Read every new test body (7 scanner tests + 1 snapshot test). None are vacuous — each asserts a specific `status`/`guard`/`blocking_reasons` value tied to a concrete input, and the positive-path test (`test_distinct_identities_still_produce_none_self_certification`) guards against over-blocking regression, satisfying invariant 9 directly in the test suite, not just the auditor's own repro.

### Risks (both non-blocking)

- **R1 — multi-proof-path last-writer-wins aggregation.** `_scan_artifacts` overwrites `guards.self_certification_status` (and similarly `live_write_status`, `merge_seam_status`) per proof file in the loop with no aggregation across multiple `proof_paths`. If an incomplete proof is listed *before* a complete one, the incomplete file's `UNKNOWN` is silently overwritten by the later complete file's `NONE`, and the whole scan reaches `PASS`. Empirically confirmed above. **This is a pre-existing defect, not introduced by this commit** — the parent commit exhibited the same overwrite pattern for every ordering (and was strictly worse, since it reached PASS in the `complete, empty` order too, which the new code correctly blocks). Not in scope for F001/F002 (both findings concern single-proof identity classification), and fixing it would require aggregation logic beyond the allowlisted files' minimal-change mandate. Recommend a follow-up finding (e.g. DMX-W1-04-F003) to make guard aggregation a monotone worst-of across all supplied proof paths rather than last-write-wins.
- **R2 — pre-existing UNKNOWN→PRESERVED/NONE normalization, untouched by this diff.** `red_lane_scanner.py:245-271` (not modified in this commit) converts `merge_seam_status`, `dopetask_execution_status`, `external_write_status`, `github_mutation_status` from `UNKNOWN` to `PRESERVED`/`NONE` purely on the absence of specific finding categories — which is the same "no missing guard silently converted to NONE without positive evidence" pattern named in invariant 6. This block is outside the two named findings and outside the allowlisted diff, so it is not treated as a defect of *this* commit, but invariant 6 should be read as confirmed only for the specific guard this commit touches (`self_certification_status`), not for the whole `GuardsInfo` surface.

### Invariants — explicit confirm/deny

1. **PASS/READY only from positively-established evidence** — CONFIRMED for the two repaired paths (self-certification, prerequisite-packet readiness); NOT fully confirmed repo-wide (see R2).
2. **Missing evidence remains UNKNOWN** — CONFIRMED (empty proof, missing identity, absent prerequisite packet all → UNKNOWN).
3. **Malformed/contradictory evidence remains CONFLICTING or blocking** — CONFIRMED (`MALFORMED_PROOF` BLOCKER added; `CONFLICTING` packet state already blocked pre-existing, untouched).
4. **Stale required evidence blocks** — CONFIRMED, pre-existing behavior untouched by this diff (`control_snapshot.py:489`, `red_lane_scanner.py:202-210`).
5. **UNDEFINED_AND_BLOCKING semantics unchanged** — CONFIRMED; `red_lane.py:108` default (`GuardsInfo.live_write_ready_status = "UNDEFINED_AND_BLOCKING"`) is not touched anywhere in the diff.
6. **No missing guard silently converted to NONE/PRESERVED without positive evidence** — CONFIRMED for `self_certification_status` (the repaired guard); NOT fully repo-wide — see R2 (pre-existing, out of scope, non-blocking).
7. **Missing implementer OR auditor identity must not prove absence of self-certification** — CONFIRMED, this is the core fix and is directly verified.
8. **RedLaneScanner.main() exits zero only for legitimate complete PASS** — CONFIRMED via `test_cli_exits_nonzero_on_incomplete_proof` (real subprocess invocation, not mocked).
9. **Valid previously-passing complete proof fixtures still reach PASS/READY** — CONFIRMED, both for the scanner (distinct-identity test) and for control-snapshot (`tp_dcp_0004_valid_snapshot_inputs` → READY, verified live).
10. **No merge/production/live-write authority introduced** — CONFIRMED; grepped the added lines for subprocess/requests/gh/git-push/write patterns, none found; all additions are pure classification/`Finding`-append logic.

### Bottom line

Both F001 and F002 are genuinely closed, verified independently (not just by trusting the packet's tests) with live reproductions against both the new and parent commit code. The allowlist is fully respected, no scope creep, no write-authority introduced, and the positive path shows no regression. The one real gap found (R1, last-writer-wins guard aggregation across multiple proof paths) is empirically proven to be a **pre-existing** defect that this commit **strictly improves** rather than introduces or leaves untouched in the worse direction, so it does not block this commit — but it should be filed as a follow-up finding since it is a real, non-hypothetical fail-open path in the current codebase.
