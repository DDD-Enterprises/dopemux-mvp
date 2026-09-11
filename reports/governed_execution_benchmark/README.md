# Governed Execution Benchmark (W08)

Deterministic, model-free before/after measurement harness for the
governed execution flow defined by
`MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001`. This is workstream W08:
it builds the measurement tool only. The actual before/after run against
the MacroPacket's real W01..W07 evidence is executed by the team lead
after this packet lands.

## What it is, and is not

The harness (`scripts/governed_execution/benchmark.py`) reads files with
`pathlib` only. It makes no network call, no model or MCP call, and
starts no other process. Two runs against byte-identical inputs produce
byte-identical JSON and Markdown output: every collection is sorted
before being written, and no wall-clock value is ever recorded by the
harness itself (only timestamps found *inside* the evidence files are
used, and only to compute `cycle_time`).

The harness can recommend that a relay be retired. It cannot authorize
retirement: `retirement_authorized` is always `false` and `authority` is
always `"NONE"` in every report it produces, regardless of input. Any
relay defined in the harness as an operator/nondelegable gate (invariant
I15) is never emitted in `retirement_candidates`, no matter what any
input file says.

## Running it

```
uv run python scripts/governed_execution/benchmark.py \
    --repo <repo-root> \
    --baseline-manifest scripts/governed_execution/benchmark_inputs.baseline.json \
    --after-dir <evidence-directory> \
    --out <report.json> \
    --out-md <report.md>
```

- `--repo` is the repository root that baseline manifest paths resolve
  against.
- `--baseline-manifest` is `scripts/governed_execution/benchmark_inputs.baseline.json`,
  the fixed BEFORE sample recorded at base commit
  `1c915b9141e9a5c3d835a5c7ea953381782ae875` (path + sha256 for every file,
  or `MISSING` when a listed path was absent at that commit).
- `--after-dir` is a read-only directory holding the MacroPacket's own
  W01..W07 evidence: `*_RETURN.md` return blocks (including
  `G0_RETURN.md`), `OPERATOR_DECISIONS_G0.md`,
  `OPERATOR_GATE_RECEIPT_*.md`, `W0N_REPAIR_REQUEST_*.md`,
  `W0N_FREEZE_RECEIPT*.json`, `evidence/a*-audit-run*/A*_AUDIT_RECORD.md`,
  and `W0N_VALIDATION_*.txt`.
- Exit code is `0` on success -- including when some or every metric
  comes back UNKNOWN because its evidence is absent -- and `2` only when
  `--after-dir` does not exist or is not a directory. A missing file
  inside `--after-dir`, or a baseline path recorded `MISSING` in the
  manifest, never raises; the affected metric is reported UNKNOWN.

## Metrics

Eleven metrics are computed for `baseline` (the fixed pre-v2 sample) and
`post_change` (the AFTER evidence), plus a `deltas` entry per metric
(`post_change value - baseline value`, computed only when both sides are
a KNOWN numeric value). The exact extraction rule for each metric, on
each side, is documented in its extractor function's docstring in
`scripts/governed_execution/benchmark.py`:

| Metric | Extractor functions |
| --- | --- |
| `audit_calls` | `extract_audit_calls_baseline`, `extract_audit_calls_after` |
| `cycle_time` | `extract_cycle_time_baseline`, `extract_cycle_time_after` |
| `maintenance_cost` | `extract_maintenance_cost` (one rule, both sides) |
| `model_calls` | `extract_model_calls_baseline`, `extract_model_calls_after` |
| `operator_touches` | `extract_operator_touches_baseline`, `extract_operator_touches_after` |
| `proof_churn` | `extract_proof_churn_baseline`, `extract_proof_churn_after` |
| `repair_loops` | `extract_repair_loops_baseline`, `extract_repair_loops_after` |
| `review_calls` | `extract_review_calls_baseline`, `extract_review_calls_after` |
| `safety_regressions` | `extract_safety_regressions_baseline`, `extract_safety_regressions_after` |
| `stale_head_rework` | `extract_stale_head_rework_baseline`, `extract_stale_head_rework_after` |
| `supervisor_relays` | `extract_supervisor_relays_baseline`, `extract_supervisor_relays_after` |

## UNKNOWN semantics

A count-style metric is `UNKNOWN` (`value: null`) exactly when its whole
evidence category is absent from the corpus -- for example, no
`*_RETURN.md` file at all, or no `PROOF.json` at all. When at least one
file of the relevant kind is present, the metric is a real, possibly
zero, count: a `PROOF.json` present with an empty `fixes_applied` array
contributes zero repair loops, which is different from, and reported
differently than, no `PROOF.json` being present at all. A baseline
manifest path recorded `MISSING`, or whose on-disk sha256 no longer
matches the manifest (`MISMATCH`, i.e. drifted evidence), is treated the
same way: excluded from extraction, never estimated, never silently
dropped from the corpus record.

`stale_head_rework` additionally carries a `gaps` list: an audit record
that cannot be matched to a workstream's return file (missing
`WORKSTREAM_ID=`/`SUBJECT_SHA=` fields, or no return file for that
workstream) is listed there rather than counted as either stale or
clean.

## Retirement recommendation, and what it cannot do

`retirement_candidates` scores a fixed catalog of relay types
(`supervisor_return_relay`, `independent_audit_dispatch_relay`,
`review_ci_relay`, `repair_loop_relay`, `freeze_proof_relay`) against the
AFTER metrics: `safe` (no recorded safety regression), `observable` (the
associated metric is KNOWN), `reversible` and `authority_preserving`
(constant true for every cataloged non-gate relay), and
`measurably_useful` (the metric is KNOWN and greater than zero, meaning
the relay still fires). `recommendation` is `INSUFFICIENT_EVIDENCE` when
not observable, `RECOMMEND_RETIRE` when observable, safe, and not
measurably useful, else `KEEP`. The sixth catalog entry,
`operator_decision_gate`, is an operator/nondelegable gate and is
filtered out of the list unconditionally -- it is structurally
impossible for it to appear, regardless of what any evidence file says.

This report is a recommendation, not an authorization.
`retirement_authorized` is a hardcoded `false` constant and `authority`
is a hardcoded `"NONE"` constant in every report this harness produces.
A semantic review of any recommended retirement, and any decision to act
on one, is a separate step for a human operator and, where required by
MACRO section 11, a dispatched review -- not something this harness
performs or claims to perform.
