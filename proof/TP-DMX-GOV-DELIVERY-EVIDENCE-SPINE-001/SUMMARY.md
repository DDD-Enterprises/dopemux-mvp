# TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001 — Proof Summary (repair cycle 1)

```text
PACKET_ID=TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001
RISK_LANE=L2_MATERIAL
REPAIR_CYCLE=1

BASE_SHA=d40e43dd70307d2c000a4efd581be7c11248728c
CONTENT_HEAD=657dc5b22244d59e9504b3734adebfec04ba63a6
CONTENT_TREE=1735f7b51b4370ec9725b0b4b88dcf57d71ce7da
SUPERSEDED_CONTENT_HEAD=8c309d764a55896c3363bd803404f64d4e277185
CHANGED_FILES=23 (vs base)   REPAIR_DELTA=13 files, +2384/-449

VALIDATION_STATUS=PASS
GOV_AUD_F1=PASS
AUDIT_VERDICT=NOT_RUN
PR_STEWARD_READINESS=NOT_RUN
PROOF_ONLY_EQUIVALENCE=NOT_APPLICABLE
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
```

These four are recorded separately and are never collapsed into a single PASS:
`VALIDATION_STATUS`, `AUDIT_VERDICT`, `PR_STEWARD_READINESS`, `MERGE_AUTHORITY`.

## Why this cycle exists

The independent L2 audit **FAILED** content head `8c309d76` with 3 blocking
findings and 1 must-fix. That audit binds to that head and **cannot be reused**.
This is the authorized bounded repair; it makes substantive code and contract
changes, so it is a new content head requiring a **new** independent audit — it
is explicitly *not* claiming the proof-only path.

Neither `8c309d76` nor its proof commit `caac1544` was rewritten. The lineage is
`d40e43dd → 8c309d76 → caac1544 → 657dc5b2`.

## The four findings

**GOV-AUD-001 — cross-role governance laundering.** The aggregate discarded
document provenance and counted values bundle-wide, so a risk could be dropped
from the document the operator and PR Steward actually read and re-encoded in one
with no authority; a checked-in positive test *required* that swap to pass.
Assertions are now keyed by a **tuple** `(document_role, field)` — never a
concatenated string — with the role **derived** from the path basename through a
closed table.

The table is **injective**: one role per document kind, 23 of them. A first draft
grouped `AUDITOR_REPORT.md`, `AUDIT.md`, `AGY_AUDIT.md` and
`AUDITOR_REPAIR_REPORT.md` under one role; probing showed a swap between two of
them still passed, which is this same finding at finer grain for any consumer
reading only one. §08 rules ambiguous semantic status substantive, so grouping was
refused. Splitting can only reject more. Relocation preserves the basename, so it
still passes.

**GOV-AUD-002 — attestations standing in for proof.** Every structural conjunct
now carries a basis, and **only `OBSERVED_GIT` supports a PASS**. Facts come from
a deterministic git observer behind a shape-validated read-only allowlist. The
`raw_diff_contains_no_substantive_source_change` attestation is **removed** and
derived from two observed facts. Absent-on-both digests are an unmade comparison,
not an unchanged one. The receipt carries an `observation_digest` so a later
auditor re-runs the observer instead of trusting the receipt.

**GOV-AUD-003 — READY from an incomplete ledger.** The ledger carries §05's
`policy.required_gate_set`, defaulting to all fifteen classes; a required class
with no entry becomes a synthetic `UNKNOWN` and blocks. Phase advances only
through the longest satisfied prefix.

**GOV-AUD-004 — absence treated as compatibility.** A required dimension unbound
on either side now denies. The profile is **declared** — operator flags, then the
packet's `repo_binding.required_identity_dimensions` — and only falls back to
inference, because inference is weakest exactly when the expected identity is
sparse.

## Three defects found while repairing

Probing the repair with executed attacks, not re-reading it, surfaced three
defects — all fixed before freeze:

- **REPAIR-P1 (HIGH).** `derive_phase` stepped over a gate *present* with a
  failing state when policy did not require it, so `SCOPE=UNSATISFIED` between two
  satisfied gates still reported `REVIEW`. That is GOV-AUD-003's own defect class
  reintroduced *inside its own repair*. Now only `NOT_APPLICABLE`, or a class both
  absent and not required, may be stepped over: "not required" excuses an absence,
  never a visible failure.
- **REPAIR-P2 (MEDIUM).** The excluded-tree digest hashed only `(path, oid)`. A
  `chmod +x` on a source file, and retyping a regular file whose content is
  `/etc/passwd` into a symlink pointing there, both preserve the blob oid
  **exactly** — reproduced in a scratch repo. The path conjunct caught both, so no
  PASS was reachable, but these are meant to be *independent* checks. The digest
  now covers `mode type oid`.
- **REPAIR-P3 (LOW).** Abbreviated object ids were accepted into a receipt whose
  purpose is exact-head binding; and a hand-written PASS receipt could omit its
  observation provenance and still validate. Both closed.

## Validation

| Check | Result |
|---|---|
| `git diff --check` | PASS (exit 0) |
| `ruff check` | PASS (exit 0) |
| Focused suite | **PASS — 265 passed** (204 at the failed head) |
| Full `tests/unit` + `tests/repository_planner` | 2090 passed, 1 failed, 2 skipped |
| `validate_change_contract.py` | **PASS** — `max_lane=L2`, `paths=23` (exit 0) |
| `pre-commit` on the 13 repair files | PASS_CLEAN — no hook modified a file |
| 7 schemas, draft-07 | PASS — 7/7 |
| Packet vs canonical spec | PASS — 8/8 required fields, 0 undeclared, 6 clean steps |
| Secret scan | NO_REAL_SECRETS — 9 matches, all the `sk-` substring of `task-…` |
| PAL expert model validation | **NOT_RUN** |

The one broader-suite failure,
`test_pm_source_events::…rejects_bare_non_repo_workspace_root`, is
**pre-existing and not attributable to this work** — re-confirmed this cycle by
running it in the primary worktree on an unrelated branch where this package does
not exist. It fails identically there.

PAL expert validation is **NOT_RUN**, not PASS. All three configured providers
failed again, matching cycle 1 exactly: OpenAI `credit_balance_exhausted`, Gemini
region quota `0`, Grok could not read the changeset. The findings above are
self-derived — but *executed* rather than reasoned: each claimed result comes from
running a constructed attack and reading the output.

## Scope

13 files touched, every one inside the audit's `ALLOWED_REPAIR_SURFACES`.
`src/dopemux/governed_delivery/__init__.py` was **not** touched — it is absent
from the repair allowlist — and no new module file was created, so all new code
lives in the five authorized modules.

## What is not authorized

Merge is **not** authorized. PR #1268 stays **draft**. The next step is exactly
one **new** independent L2 audit against `657dc5b2`; the implementer has not and
must not self-audit, and the auditor route remains an operator input
(B-ROUTE-001). Nothing here has been pushed.
