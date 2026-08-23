# Auditor Report — TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001

**TP**: TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001
**PR**: DDD-Enterprises/dopemux-mvp#1165
**Subject**: Admission of the exact AGY auditor model `gemini-3.1-pro-high` to the canonical embedded-audit proof schema
**Auditor**: AGY (Google Antigravity CLI) v1.1.11, `--model gemini-3.1-pro-high`
**Invocation**: `agy --model gemini-3.1-pro-high --mode plan --effort high --output-format json --print '<bounded read-only embedded-audit prompt + full content-head diff>'`
**Exit code**: 0
**Status**: PASS (round 4 controlling)
**Date**: 2026-08-10

---

## Verdict

**PASS.** Four audit rounds were run. Round 1 returned `VERDICT: FAIL` with three risks;
two produced code changes and one was a prompt-scope defect on the producer's side. Round 2,
against the repaired head, returned `VERDICT: PASS` with an empty `RISKS:` list. Round 3 was
required because a reviewer found a real defect *after* round 2 passed — the trusted
local-attestation gate did not enforce the very contract this PR establishes — and it
returned `VERDICT: PASS` with an empty `RISKS:` list, 11/11 questions PASS. Round 4 was then
required because round 3 **missed a defect that a reviewer found** — the canonical-schema
refactor had silently dropped a non-schema acceptance gate — and it returned `VERDICT: PASS`
with an empty `RISKS:` list, 10/10 questions PASS.

**Round 4 is the controlling authority.** Rounds 1-3 are historical evidence only: the
audited tree changed after each of them, so they are stale and are not signed as current.

All four raw runner transcripts are committed unedited alongside this report. The failing
round is published, not discarded, and so is the round that returned a clean PASS over a
tree that still contained a real defect.

## Audit binding

| | Round 1 | Round 2 | Round 3 | Round 4 (controlling) |
|---|---|---|---|---|
| AUDITED_TREE | `491e59a868` | `02c915d800` | `d2d3ff808e` | `ca3ff647f8bdfd3cc85f6a15b5404d12617708b7` |
| base (main) | `5d694cc989` | `5d694cc989` | `5d694cc989` | `5d694cc9898e5046b5da03319f20f48599c40ca8` |
| prompt sha256 | `38dc613b63f4a788…` | `642b741baaf05a6e…` | `3419d9e49f17b693…` | `1a94f8b4d83399b911869747b2df166011f30ec7d80f94c011fd57c3b91bdcab` |
| diff sha256 | `bcc5eb0881bc6fcc…` | `1fdb9ffa408bea91…` | `2508bc82dcfe94b1…` | `290846cc7b8d5cd4e99b48ce5b7d6eb67f13d7527da7d24d397c5d751674c360` |
| verdict | FAIL (3 risks) | PASS (0 risks) | PASS (0 risks, 11/11) | **PASS** (0 risks, 10/10) |
| transcript | `review_bundle/agy-audit-round1-491e59a868.json` | `review_bundle/agy-audit-round2-02c915d800.json` | `review_bundle/agy-audit-round3-d2d3ff808e.json` | `review_bundle/agy-audit-round4-ca3ff647f8.json` |

Session properties for all four rounds: fresh single-turn session (`num_turns: 1`),
read-only `--mode plan`, no repository code executed, no repository writes.

## Round 4 — a gate the refactor dropped, and what that says about round 3

Round 3 passed 11/11 over a tree that still contained a real defect, and it was asked the
relevant question directly. Its Q4 covered gate preservation and answered PASS. It was
wrong. `@chatgpt-codex-connector`, reviewing the pushed head, found it.

**The defect.** The old hand-rolled validator carried a check the canonical schema cannot
express: `embedded_audit.required` must be `true`. The schema types `required` as a plain
boolean, so `required: false` with `status: PASS` is schema-**valid**. Replacing the
structural check with canonical schema execution therefore silently removed the gate.

It is not cosmetic. Measured end to end: `build_embedded_audit_proof` promotes an accepted
local attestation to `executed: true`, and `enforce_independent_audit_proof` checks the
verdict but not this flag — so the mandatory embedded-audit gate went **green** for a proof
declaring the audit was not required.

**The response.** Rather than fix only the reported field, all nine checks the pre-refactor
implementation performed were enumerated and tested against the refactored path:

| Old check | Now enforced by | Regression? |
|---|---|---|
| required keys present | schema `required` | no — and `report_path` is now covered too |
| `status` in enum · `auditor_tool` in enum · `auditor_model` in enum | schema `enum` | no |
| `findings`/`fixes_applied`/`remaining_risks` are lists | schema `type: array` | no |
| `exit_code` int-or-null · `invocation` string-or-null | schema `type` | no |
| status is a passing verdict | `policy_errors()` | no |
| **`required` is `true`** | **`policy_errors()` — was dropped, now restored** | **yes** |

`required` was the only loss. The two gate classes are now explicitly separated —
schema-expressible checks in `schema_validation_errors()`, everything else in
`policy_errors()` — and `POLICY_ONLY_REJECTIONS` pins fixtures the schema accepts but
acceptance must not, so the next refactor cannot drop one quietly.

### Round 4 findings — 10/10 PASS

| Q | Subject | Result |
|---|---|---|
| Q1 | `required: true` gate restored and applied on the acceptance path | PASS |
| Q2 | no other pre-refactor check left uncovered (the crux of this round) | PASS |
| Q3 | `allOf`, `additionalProperties`, `report_path` still enforced | PASS |
| Q4 | wrong-tool exact-model fixture still rejected | PASS |
| Q5 | fail-closed on absent `jsonschema` intact | PASS |
| Q6 | tests genuinely pin the restored gate and fail if it is dropped | PASS |
| Q7 | schema and non-schema gates cleanly separated, none orphaned | PASS |
| Q8 | no overstated claims | PASS |
| Q9 | no credentials, Grok support, Steward or signer-roster changes | PASS |
| Q10 | no remaining path to accept a schema-rejected or not-required proof | PASS |

**Standing caution recorded for future cycles:** a clean audit verdict is evidence, not
proof. Round 3 returned 11/11 with an empty risk list over a tree carrying a live gate
regression. Replacing a validator is a change class where enumerating the old behaviour
check-by-check is worth more than any single verdict.

## Round 3 — trusted local-attestation enforcement

### The defect, reproduced before repair

`scripts/audit/local_audit_acceptance.py` validated a signed `embedded_audit` object with a
hand-rolled stdlib check: `required` keys, a few enum memberships, a few types. It never
walked `allOf`, so **no** schema conditional was enforced on the signed local-attestation
route — not this PR's exact-model conditional, and not the pre-existing `SKIPPED`
conditionals either, which were caught only incidentally by the separate passing-verdict
policy check. It also exempted `report_path` outright.

Measured, not argued (`review_bundle/DEFECT_REPRODUCTION_ROUND3.txt`):

| Validator | Verdict on `{PASS, gemini-3.1-pro-high, claude-code-cli}` |
|---|---|
| canonical `Draft7Validator` | `'agy' was expected` |
| `origin/main` acceptance route | **ACCEPTED** — the defect |
| repaired acceptance route | `local_audit_schema_invalid: /auditor_tool: 'agy' was expected` |

The gap sat behind the signature trust boundary: it let a *trusted signer* record a pairing
the schema forbids, not an untrusted party in. That bound is real and is stated rather than
used to minimise the defect — PR #1165 exists to establish an exact model-to-tool trust
contract, and a contract the trusted path does not enforce is not a contract.

### The repair

The canonical schema is now the single policy engine on both validation routes, executed
with real Draft 7 semantics rather than mirrored by hand. A conditional added to the schema
is therefore enforced the day it lands, with no second implementation to update. Verdict
policy stays separate — the schema admits `FAIL` and `SKIPPED` because CI also emits
diagnostic proofs, while local attestation accepts passing verdicts only. `report_path` is
no longer exempt. Absent `jsonschema` the route fails closed and never falls back.

### Round 3 findings — 11/11 PASS

| Q | Subject | Result |
|---|---|---|
| Q1 | canonical schema actually executed, not re-implemented | PASS |
| Q2 | wrong-tool exact-model fixture now rejected | PASS |
| Q3 | `report_path` validated; no exemption survives, including in docstrings | PASS |
| Q4 | non-schema gates preserved (verdict, repo, PR, signature, principal, ancestry, proof-only closure) | PASS |
| Q5 | fail-closed when `jsonschema` is unavailable | PASS |
| Q6 | workflow step changes no gating semantics, adds no credential, ordered before the gate | PASS |
| Q7 | new tests prove what they claim | PASS |
| Q8 | verdict policy correctly separated from schema validity | PASS |
| Q9 | no overstated claims | PASS |
| Q10 | no credentials, no Grok support, no Steward or signer-roster changes | PASS |
| Q11 | the sweep/pre-commit scope gap is accurately declared still open | PASS |

Round 3 volunteered, in answer to Q7, that three positive-path tests would still pass if the
repair were reverted: `test_exact_model_bound_to_agy_is_accepted_end_to_end`,
`test_skipped_proof_is_schema_valid_but_policy_rejected`, and
`test_generic_gemini_backward_compatible`. That is correct and expected — they assert
backward compatibility, not enforcement. The revert-sensitive tests are
`test_exact_model_with_wrong_tool_is_rejected_end_to_end`,
`test_rejects_report_path_outside_schema_pattern`, `test_unknown_key_is_rejected`, and the
`PARITY_CORPUS` parametrisation. Recorded here rather than omitted, since a reader should
know which tests carry the weight.

## Audit topology

An audit cannot audit its own output, so the heads are named rather than conflated:

| Term | Meaning | Round 3 |
|---|---|---|
| `AUDITED_TREE` | exact substantive tree sent to AGY | `ca3ff647f8bdfd3cc85f6a15b5404d12617708b7` |
| `AUDIT_EVIDENCE_HEAD` | successor adding only the report, raw transcript, runner evidence | this commit |
| `SIGNED_PROOF_HEAD` | successor adding/replacing only signed proof artefacts | the PR head |

## Ordering disclosure — what the auditor did and did not see

This report is the audit's own output, so it cannot exist in the tree that was audited.
The ordering is **forced**, not chosen:

- the trusted schema requires `report_path` to match `^proof/[^/]+/AUDITOR(_REPAIR(_[0-9]+)?)?_REPORT\.md$`,
  i.e. a single directory under `proof/`;
- proof-only closure (`scripts/audit/local_audit_acceptance.py`, `PROOF_DIR_TEMPLATE`)
  confines the successor commit to `proof/pr_merge/embedded-audit/pr-1165/`.

Those two constraints cannot both be satisfied by a report placed in the proof-only commit,
so the canonical report must live in the content lineage. Concretely:

- AGY audited `AUDITED_TREE` = `ca3ff647f8bdfd3cc85f6a15b5404d12617708b7` in full.
- The head recorded in `PROOF.json` is `AUDIT_EVIDENCE_HEAD`, the commit sitting directly on
  top of it. The delta between them is **only** this report and the audit's own raw
  transcript, defect reproduction, and runner-evidence captures under `review_bundle/` —
  verifiable with
  `git diff --name-only ca3ff647f8bdfd3cc85f6a15b5404d12617708b7..<PROOF head_sha>`.
- No schema, validator, test, packet, documentation, or workflow byte changed after the
  audit.

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
4. **Validator scope gap — confirmed, still open, and NOT closed by this repair.**
   `proof/.validator_scope.json` includes only `proof/TP-DMX-*/PROOF.json` and skips
   `proof/pr_merge/**` under `default_when_unmatched: "skip_with_warning"`; the pre-commit
   proof hook has the same blind spot independently via `files: ^proof/[^/]+/PROOF\.json$`.
   That is how the previous head's nonconformant `report_path` passed CI green. Repairing
   `local_audit_acceptance.py` closes the **signed local-attestation route only** — it does
   not make the deterministic sweep or pre-commit look at `proof/pr_merge/**`, and this
   report does not claim otherwise. Observed again during this cycle: the pre-commit hook
   "Validate proof bundle embedded_audit schema" reported *no files to check* while this
   PR's own proof was in the diff. This proof is therefore validated by a **direct**
   `scripts/audit/validate_audit_proof.py` run, which is the controlling result. The scope
   gap is filed as `TP-DMX-EMBEDDED-AUDIT-VALIDATOR-SCOPE-PARITY-001`, whose first step is a
   census of existing nonconformance so widening scope does not convert legacy proof debt
   into an unbounded repair campaign.

## Validation performed on the audited content

| Check | Result |
|---|---|
| `pytest tests/audit tests/governance tests/pr_steward tests/auditor_router` | PASS (664 tests) |
| canonical dopetask packet schema, all three packets | PASS — 0 errors |
| `change-contract-preflight` | PASS — `max_lane=L3`, operator gate satisfied by explicit authorization |
| `pre-commit --from-ref origin/main --to-ref HEAD` | PASS — exit 0 |
| defect reproduction (main vs repaired validator) | PASS — see `review_bundle/DEFECT_REPRODUCTION_ROUND3.txt` |
| `git diff --check` | PASS |

The `--all proof` sweep is deliberately **not** cited as evidence for this proof while its
`pr_merge` scope gap remains open.
