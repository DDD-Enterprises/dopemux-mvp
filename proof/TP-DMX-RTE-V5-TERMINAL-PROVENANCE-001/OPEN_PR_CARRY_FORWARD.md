# Open-PR Carry-Forward Analysis — TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001

Performed after C1 (`250e46bd6b`) froze. Read-only. No branch of either PR was
mutated, rebased, retargeted, or closed.

## PR #1136 — `claude/rte-truth-program`

```
observed_head:        df25e44b4ef320f7813249a9fcbd234cfdd413e0
state:                OPEN
refreshed_at:         this analysis run
authoring-time head:  df25e44b4ef320f7813249a9fcbd234cfdd413e0  (UNCHANGED — no drift)
merge_base(main,1136): 899082ae74155b2412a2ce862376438c1d33d13
```

**Overlapping paths** (present in both this packet's changed-file set and
#1136's diff against its own base): `run_extraction_v5.py`,
`lib/batch_retriever.py`, `validate_pre_live_gate_v25.py`.

**Content check at #1136's head:**
- `get_git_sha()` (run_extraction_v5.py:4385) is byte-identical in shape to
  this packet's pre-fix version: `try: subprocess.check_output(...); except
  Exception: return "UNKNOWN"`. No identity gate exists downstream.
- No `resolve_final_run_terminal_exit_code`, `required_execution_source_identity`,
  or `BatchRetrievalIntegrationOutcome` symbol exists anywhere in #1136's tree.
- `lib/batch_retriever.py` at #1136's head still defines only the bare
  int-returning `integrate_batch_results_with_webhook` — no typed/detailed
  companion.

**Semantic classification:**
```
SEMANTIC_RELATION=COMPATIBLE
SUPERSESSION=NO
PATCH_COMPATIBILITY=UNKNOWN_UNTIL_LOCAL_SIMULATION -> now: LIKELY_MECHANICAL_CONFLICT
                                                       (large divergence since merge_base;
                                                        not attempted — read-only classification only)
CARRY_FORWARD_REQUIRED=YES
```

#1136 still retains all three targeted defects (RTE-W1-001, RTE-W1-006-v5,
RTE-W1-010) unrepaired. It does not conflict with this packet's fail-closed
invariants — it simply predates them. No CONFLICTING classification applies.

## PR #1183 — `claude/rte-truth-followup`

```
observed_head:        a8faf22b496dc6fc6135945417b6542016e13d5d
state:                OPEN
refreshed_at:         this analysis run
authoring-time head:  a8faf22b496dc6fc6135945417b6542016e13d5d  (UNCHANGED — no drift)
merge_base(main,1183): 4c5856f32fc085abfbf50ba5a4c00872f52eaf6
merge_base(1136,1183): 5f52cad52275c563567201d6377a750b8475baa
```

Note: #1183's merge-base with #1136 is an older common ancestor
(`5f52cad522`), not #1136's current head — consistent with prior operator
memory that #1136 was transplanted to a fresh base at `5f52cad522` (FROZEN)
after #1183 branched. #1183 is downstream of that same lineage, not literally
rebased onto #1136's latest commits.

**Overlapping paths:** `run_extraction_v5.py` only (`lib/batch_retriever.py`
and `validate_pre_live_gate_v25.py` are unchanged between #1136 and #1183).

**Content check at #1183's head:** same absence of
`resolve_final_run_terminal_exit_code` / `required_execution_source_identity`
/ `BatchRetrievalIntegrationOutcome` as #1136. #1183's changes are additive on
top of #1136's lineage (CLI/status-reconciliation/trace-honesty fixes) and do
not touch `get_git_sha`, the batch-outcome int contract, or the final exit
path in a way that would conflict with this packet's invariants.

**Semantic classification:**
```
SEMANTIC_RELATION=COMPATIBLE
SUPERSESSION=NO
STACKED_DEPENDENCY=YES (via shared lineage back through #1136 to 5f52cad522)
CARRY_FORWARD_REQUIRED=YES
```

## Required handling on future reconciliation

Whoever eventually merges/rebases #1136 and/or #1183 onto a `main` that
includes this packet's fix (or vice versa) must preserve, without
regression:

```
RTE-001 terminal fail-closed   — resolve_final_run_terminal_exit_code() must
                                  remain the single exit-status authority for
                                  the phase-execution path; do not reintroduce
                                  an unconditional sys.exit(0).
RTE-006 canonical-v5 typed      — BatchRetrievalIntegrationOutcome (or
         failure outcome          equivalent) must remain wired at the CLI
                                  dispatch call site; the legacy int-returning
                                  integrate_batch_results_with_webhook must
                                  stay untouched for v3's import.
RTE-010 source identity          — required_execution_source_identity() /
         fail-closed               SourceIdentityUnprovenError gate must
                                  remain ahead of certification/terminal
                                  evidence acceptance in both
                                  run_extraction_v5.py's phase-execution path
                                  and validate_pre_live_gate_v25.py's
                                  SOURCE_IDENTITY_UNPROVEN blocker.
```

No mechanical patch/merge was applied to either PR branch. Divergence since
their respective merge-bases with current `main` is large (#1136:
`899082ae74`, #1183: `4c5856f32f`), so a literal `git apply`/cherry-pick
simulation was not attempted — the overlap analysis above is content-level
(symbol presence/absence), which is sufficient to establish
COMPATIBLE/CARRY_FORWARD_REQUIRED without touching either branch, per the
packet's read-only overlap-analysis requirement (§12).

## Summary

```
PR_1136: COMPATIBLE, not superseded, carry-forward required, no conflict
PR_1183: COMPATIBLE, not superseded, carry-forward required, no conflict
```
