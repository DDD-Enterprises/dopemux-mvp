# RTE-MACRO-PKT-REMAINING-PARALLEL-001 Wave Plan

## Macro Status

Status: `GATE0_AND_COLLISION_ANALYSIS_COMPLETE`

This macro is in Gate 0 plus collision-analysis mode. No subpacket worktrees were created and no subpacket implementation was executed.

## Base Mode

`BASE_MODE=MAIN_AFTER_MERGE`

Evidence: PR #654 reports `state=MERGED`, and the macro worktree starts from `origin/main` at `fbf1b5df333e815db718ec05b4bc324ebf7d9af6`.

Correction: the prompt stated PR #654 is open. Observed GitHub state says PR #654 is merged.

## Gate 0 Result

`PASS_WITH_CORRECTION`

| Check | Observed |
| --- | --- |
| Source `pwd` | `/Users/hue/.codex/worktrees/134f/dopemux-mvp` |
| Source root | `/Users/hue/.codex/worktrees/134f/dopemux-mvp` |
| Source branch | detached HEAD |
| Source HEAD | `d64d5f15e46e68373e3bed1160fbc3df2807db59` |
| Source status | `## HEAD (no branch)` |
| Macro worktree | `/Users/hue/.codex/worktrees/rte-macro-pkt-remaining-parallel-001/dopemux-mvp` |
| Macro branch | `codex/rte-macro-pkt-remaining-parallel-001` |
| Macro HEAD | `fbf1b5df333e815db718ec05b4bc324ebf7d9af6` |
| Remote | `origin` and `mvp` point to `https://github.com/DDD-Enterprises/dopemux-mvp.git` |
| Repo markers | `pyproject.toml`, `services/repo-truth-extractor/run_extraction_v5.py`, and `src/dopemux/cli.py` present |
| PR #654 | `MERGED`, head `codex/rte-pkt-15-failed-sidecars-clean`, head OID `eb351aab7cbc009ab73ca397062eed03a5edb80d` |
| PR #654 file scope | only `out/rte-pkt-15-failed-sidecars/**`, `services/repo-truth-extractor/output_safety.py`, `services/repo-truth-extractor/run_extraction_v5.py`, and RTE-PKT-15 tests |
| PR #654 unrelated UX audit files | none observed |

## Accepted Prerequisite State

The latest operator instruction accepts:

- `RTE-PKT-00-SOURCE-CLOSURE`
- `RTE-PKT-01-LIVE-GATE`
- `RTE-PKT-02-PAYLOAD-REDACTION`
- `RTE-PKT-15-FAILED-SIDECARS`

Required carried residuals:

- `services/repo-truth-extractor/llm_runtime.py:1625` comparison-lane `.FAILED.txt` writer remains follow-up risk.
- Legacy v3 failed sidecar fixtures remain unchanged evidence surfaces.
- Packet 00 proof root absence remains a chain-of-custody weakness.
- No live/provider/batch operations were run.

## Parallel Groups

Collision evidence does not support running the whole tempting first wave in parallel.

Approved initial parallel groups, subject to operator acceptance of this macro:

```text
Subwave 1A:
  RTE-PKT-08-XAI-BATCH-STATIC
  RTE-PKT-10-PROOF-CONTRACT

Subwave 1B:
  RTE-PKT-03-PRESCAN-STALE

Subwave 1C:
  RTE-PKT-07-XAI-METADATA

Subwave 1D:
  RTE-PKT-05-PROVENANCE-FIELDS
```

Rationale: `RTE-PKT-08` and `RTE-PKT-10` have no expected write-scope collision. `RTE-PKT-03`, `RTE-PKT-05`, `RTE-PKT-07`, and `RTE-PKT-08` all likely touch `run_extraction_v5.py`; `RTE-PKT-07` also touches `llm_runtime.py`.

## Dependent Waves

```text
Wave 2A:
  RTE-PKT-04-PRESCAN-INFLUENCE after RTE-PKT-03
  RTE-PKT-06-TRUTH-LABELS after RTE-PKT-05

Wave 2B:
  RTE-PKT-13-ROUTE-FINGERPRINT after RTE-PKT-07

Wave 2C:
  RTE-PKT-12-OPENROUTER-XAI after RTE-PKT-07 and RTE-PKT-13

Wave 2D plan-only:
  RTE-PKT-09-LIVE-VALIDATION-PLAN after RTE-PKT-07 and RTE-PKT-08

Wave 3 aggregation:
  RTE-PKT-11-RISK-DASHBOARD after RTE-PKT-01/02/03/04/05/06/07/08/10/12/13/15

Wave 4 polish:
  RTE-PKT-14-PRICING-VISIBILITY after RTE-PKT-11
  RTE-PKT-16-CLI-LEGACY-UX remains PLAN_ONLY_UNTIL_SOURCE_RESOLVED
```

## Worktree And Branch Policy

For each executable subpacket:

| Field | Pattern |
| --- | --- |
| Branch | `codex/rte-remain-pkt-<nn>-<short-name>` |
| Worktree | `/Users/hue/.codex/worktrees/rte-remain-pkt-<nn>-<short-name>/dopemux-mvp` |
| Proof root | `out/<packet-id-lowercase>/` plus a governance proof root if requested |
| PR | one PR per subpacket |

Do not reuse existing local branches with prior RTE packet names.

## Stop Conditions

Stop before implementation if:

- A branch already exists with unrelated drift.
- A subpacket needs promptsets, schemas, model maps, route policies, retry logic, or repair semantics outside explicit scope.
- A subpacket needs live provider calls or batch submit/poll/retrieve/cancel.
- Two parallel subpackets want the same runtime file.
- Proof artifacts would quote secret-shaped values.

## Next Operator Action

Approve Subwave 1A execution, or adjust packet order before any subpacket worktrees are created.
