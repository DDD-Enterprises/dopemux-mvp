# Auditor Report — TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001

**TP**: TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001
**PR**: DDD-Enterprises/dopemux-mvp#1165
**Subject**: Admission of the exact AGY auditor model `gemini-3.1-pro-high` to the canonical embedded-audit proof schema
**Auditor**: AGY (Google Antigravity CLI) v1.1.11, `--model gemini-3.1-pro-high`
**Invocation**: `agy --model gemini-3.1-pro-high --mode plan --effort high --output-format json --print '<bounded read-only embedded-audit prompt + full content-head diff>'`
**Exit code**: 0
**Status**: PASS
**Date**: 2026-08-10

---

## Verdict

**PASS.** Two audit rounds were run. Round 1 returned `VERDICT: FAIL` with three risks;
two produced code changes and one was a prompt-scope defect on the producer's side. Round 2,
against the repaired head, returned `VERDICT: PASS` with an empty `RISKS:` list — 10/10
questions PASS, zero FAIL, zero UNCERTAIN.

Both raw runner transcripts are committed unedited alongside this report. The failing round
is published, not discarded.

## Audit binding

| | Round 1 | Round 2 (controlling) |
|---|---|---|
| audited content head | `491e59a8686b50782aee5b1bc245eb9c36dd2fd2` | `02c915d8006ca5cddba9247ba9bf440581be7257` |
| base (main) | `5d694cc9898e5046b5da03319f20f48599c40ca8` | `5d694cc9898e5046b5da03319f20f48599c40ca8` |
| prompt sha256 | `38dc613b63f4a7884055df1851e9c1e384737a25b9964f13629e80c6bfc22f28` | `642b741baaf05a6ee13ee089649cbd17a3265c7820aaf8fb5a1fd61240a4d637` |
| diff sha256 | `bcc5eb0881bc6fcc37d1779dfeb0549f216ce54f8203f16bf0a2efc552d09d85` | `1fdb9ffa408bea91a4efdf38e547cf02944e66b7b2a56d9b351716ea650ef837` |
| verdict | FAIL (3 risks) | **PASS** (0 risks) |
| transcript | `review_bundle/agy-audit-round1-491e59a868.json` | `review_bundle/agy-audit-round2-02c915d800.json` |

Session properties for both rounds: fresh single-turn session (`num_turns: 1`), read-only
`--mode plan`, no repository code executed, no repository writes.

## Ordering disclosure — what the auditor did and did not see

This report is the audit's own output, so it cannot exist in the tree that was audited.
The ordering is **forced**, not chosen:

- the trusted schema requires `report_path` to match `^proof/[^/]+/AUDITOR(_REPAIR(_[0-9]+)?)?_REPORT\.md$`,
  i.e. a single directory under `proof/`;
- proof-only closure (`scripts/audit/local_audit_acceptance.py`, `PROOF_DIR_TEMPLATE`)
  confines the successor commit to `proof/pr_merge/embedded-audit/pr-1165/`.

Those two constraints cannot both be satisfied by a report placed in the proof-only commit,
so the canonical report must live in the content lineage. Concretely:

- AGY audited head `02c915d800` in full.
- The audited head recorded in `PROOF.json` is the report commit that sits directly on top
  of it. The delta between them is **only** this report and the audit's own raw transcripts
  and runner-evidence captures under `review_bundle/` — verifiable with
  `git diff --name-only 02c915d8006ca5cddba9247ba9bf440581be7257..<PROOF head_sha>`.
- No schema, test, packet, documentation, or workflow byte changed after the audit.

Do not read this report as evidence that the auditor reviewed itself.

## Model-selection evidence

Captured at audit time (`review_bundle/AGY_VERSION_AUDIT_20260810.txt`,
`review_bundle/AGY_MODELS_AUDIT_20260810.txt`):

- AGY version **1.1.11**
- `gemini-3.1-pro-high` — **present** in the model list
- `gemini-3.1-pro-preview` — **absent** from the model list
- `agy --model gemini-3.1-pro-preview` aborts with
  `model gemini-3.1-pro-preview is not recognized as a known model`; selector validation is
  fail-closed, so silent substitution to another model is not possible.
- `provider_attested: false` — identity rests on local AGY CLI evidence only. No
  credentialed provider call was made and none is claimed.

## Round 2 findings — 10/10 PASS

| Q | Subject | Result |
|---|---|---|
| Q1 | exact model admitted and bound to `auditor_tool: agy`; conditional cannot pass vacuously | PASS |
| Q2 | `gemini-3.1-pro-preview` absent from every enum; residual mentions are rejection or labelled history | PASS |
| Q3 | generic `auditor_model: gemini` still valid | PASS |
| Q4 | no gate weakened (signature, signers, namespace, repo/PR match, head binding, ancestry, proof-only closure, passing status, trusted schema) | PASS |
| Q5 | no credentials, secrets, workflow changes, or Grok support | PASS |
| Q6 | packets internally consistent with enacted bytes | PASS |
| Q7 | `ACCEPTED_DESIGN_BOUNDARY` statement is true of the schema as written, and the test asserts what it claims | PASS |
| Q8 | canonical report path satisfies the schema pattern | PASS |
| Q9 | no overstated claims (attestation, runtime proof) | PASS |
| Q10 | adjudication of all three round-1 risks | PASS |

## Round 1 risks and their disposition

**R1 — `if/then` conditional could pass vacuously when `auditor_tool` is absent.**
Status: **RESOLVED.** The risk was never reachable, because `auditor_tool` is in the
schema's top-level `required` array — the auditor itself hedged on this ("unless caught by
a global constraint elsewhere"), and the global constraint exists. It was nonetheless closed
directly: `"required": ["auditor_tool"]` was added to the `then` clause so the conditional
is self-contained and cannot be weakened by an unrelated edit to the top-level list. This is
a strict tightening — no proof that validated before changes verdict. Covered by
`tests/audit/test_agy_gemini31_model.py::test_exact_model_requires_auditor_tool_to_be_present`.
Round 2 Q1/Q10(a): PASS.

**R2 — `AUDITOR_REPORT.md` absent from the audited head.**
Status: **RESOLVED — producer prompt defect, not a change defect.** Round 1 was asked to
check an invariant against a tree that by construction cannot contain the audit's own
output. Round 2 was given the ordering constraint explicitly and instructed to still flag
any file claiming the report already existed. It found none. See the ordering disclosure
above. Round 2 Q6/Q10(b): PASS.

**R3 — `pal-mcp-clink` "quietly added" to the `auditor_tool` enum.**
Status: **REFUTED.** `pal-mcp-clink` is already present in the trusted schema on `main`
(`schemas/proof/embedded_audit.schema.json`); this change does not touch the `auditor_tool`
enum at all. The documentation line had omitted it, and the diff corrects that omission.
Round 1 saw only the diff, not `main`, so it could not distinguish a documentation catch-up
from an enum addition. The documentation now says so explicitly. Round 2, shown the full
schema hunk, confirmed the enum is untouched. Round 2 Q10(c): PASS.

## Remaining risks

1. **`provider_attested: false`.** Exact-selector identity is established by local AGY CLI
   evidence and fail-closed selector rejection, not by a credentialed provider attestation.
   No hosted credential was added, and none is claimed.
2. **Bootstrap representation.** This PR's own proof records `auditor_model: "gemini"` —
   the generic value valid under the pre-change trusted schema on `main` — while the
   invocation and this report establish `gemini-3.1-pro-high`. The new enum value does not
   bootstrap its own admission. Verified: `gemini-3.1-pro-high` is absent from
   `origin/main:schemas/proof/embedded_audit.schema.json` at `5d694cc989`.
3. **Schema does not prove runtime execution.** Recorded as
   `ACCEPTED_DESIGN_BOUNDARY: SCHEMA_BINDS_DECLARED_TOOL_MODEL_PAIR; RUNTIME_SELECTOR_PROVEN_BY_EXECUTION_EVIDENCE`
   in `docs/ops/embedded-audit-proof.md` and pinned by
   `test_schema_does_not_constrain_invocation_string`.
4. **Validator scope gap (pre-existing, out of scope here).** `proof/.validator_scope.json`
   includes only `proof/TP-DMX-*/PROOF.json` and skips `proof/pr_merge/**` under
   `default_when_unmatched: "skip_with_warning"`. That is how the previous head's
   nonconformant `report_path` passed CI. This PR repairs its own proof and validates it
   with a direct `scripts/audit/validate_audit_proof.py` run rather than relying on the
   scanned sweep, but the scope gap itself is outside this packet's allowlist and remains
   open as follow-up work.

## Validation performed on the audited content

| Check | Result |
|---|---|
| `pytest tests/audit tests/governance tests/pr_steward tests/auditor_router` | PASS (637 tests) |
| canonical dopetask packet schema, both packets | PASS — 0 errors |
| `pre-commit --from-ref origin/main --to-ref HEAD` | PASS — exit 0, 13 hooks |
| `scripts/audit/validate_audit_proof.py --all proof` | PASS — 71/71 |
| `git diff --check` | PASS |
