# Final Independent L3 Audit — TP-DMX-CI-AUDIT-EVIDENCE-GATE-001-A5-R3-PROVENANCE-CLOSURE-001

**Verdict: PASS_WITH_RISKS** (0 blocking findings; 3 MEDIUM, 3 LOW, 3 INFO)

- subject_head: `a54eb4ab151ba1d4c015648c9f111868b6d1fbf2`
- subject_tree: `43191a12172bc254ca494d37bf91725511e538b7`
- manifest_sha256: `f786e2320366b86904f82e7b496db49966dbc85927f68d5522a38694496406c4` (44 files, **not recomputed** — no execution)
- comparison base: `13562c8df1bc6621229eb4a38473da42be199825`; PR base `6a728f74c0311967f83213513308f97613e3f28d`

This is a no-tools, source-only audit. No commands were run. Test and hook outcomes are treated as the supplied local receipts, not as observations of mine.

---

## 1. What the change actually does

The packet closes the recorded P1: a proof asserting *audit-not-required* could previously be accepted at finalization without being bound to the exact subject. Four coordinated changes implement the closure.

1. **Canonical validator** (`scripts/audit/run_embedded_audit.py`). `independent_audit_errors` gains `expected_base_sha`. `_not_required_proof_errors` now (a) requires all four caller identity values to be present and well-typed, (b) compares proof `repo` / `pr_number` / `head_sha` to the caller tuple using `type(...) is not type(expected) or ... != expected` (so `True` cannot masquerade as an int PR number), and (c) binds the nested `provenance.change_contract.head_sha` and `base_sha` to the caller head and base. This is the specific gap the architecture-return receipt identified.
2. **Gate** (`steward_gate.py`, four copies). `FINALIZATION` now requires a complete caller tuple up front (`DENY_MISSING_CALLER_IDENTITY`), and when the proof's audit status is `SKIPPED` it delegates to the canonical validator, returning `DENY_AUDIT_PROVENANCE` on any error and `DENY_AUDIT_VALIDATOR_UNAVAILABLE` if the validator cannot be imported.
3. **Callers.** `queue_drain._merge_prepared_result` supplies `expected_repo=client.repo` and `expected_pr/expected_base_sha` from the live `PullRequestState`; `collector.collect_from_github` supplies `baseRefOid` from the live `gh pr view` payload; `pr-steward gate` gains explicit `--repo/--pr/--base-sha`; both CI hard gates propagate a trusted base from validated GitHub metadata.
4. **Docs** (`steward-merge-gate.md`, `pr-acceptance.md`) are updated to match, including the statement that proof fields never supply missing expected values and that a base change invalidates not-required evidence even when the head is unchanged.

Critically, the expected values now come from **live GitHub state or explicit operator input**, not from the artifacts being validated. That is precisely the architectural objection recorded in `ARCHITECTURE_RETURN.json` ("deriving expected identity from same supplied artifacts proves agreement, not independent authority"), and it is resolved. `test_live_queue_finalization_uses_client_repo_and_exact_pr_state` proves it operationally by setting `args.repo` to `"untrusted-argument/repo"` and still allowing only when `client.repo` matches — if the argparse value were authoritative that test would fail.

## 2. Counterexample analysis (source-level)

I traced each required counterexample class through all three consumers by hand.

- **Six nested mutations** (`head_sha`/`base_sha` x foreign/missing/malformed): all reach the binding loop at the end of `_not_required_proof_errors`. Statuses are untouched by the mutations, so `finalization_audit_evidence_allowed` still returns `True` and the deny is reached specifically through the provenance branch — matching the tests' `DENY_AUDIT_PROVENANCE` assertion on both gates.
- **Original P1 bytes**: the test pins the literal JSON and additionally asserts byte-equality with `json.dumps(_audit_proof(...))`; I re-derived that equality from the helper's key insertion order and `json.dumps` defaults. Denial arises from `audit_provenance_missing` plus identity/shape errors. The exact same bytes are fed to the canonical validator, the direct gate and the queue consumer, with a post-run `read_bytes()` equality assertion — a genuinely same-bytes matrix, not three re-serialisations.
- **Missing / mismatched identity**: `None`, `""`, and `{"bad":"shape"}` are all rejected, in the gate by `DENY_MISSING_CALLER_IDENTITY` and in the validator by `audit_not_required_identity_missing`.
- **Mixed and malformed evidence**: because `_evidence` deliberately does **not** upper-case statuses for `FINALIZATION`, `"pass"`/`"skipped"` are rejected; `required is False` is an identity test so `0`/`"false"`/`[]`/`{}`/absent all fail; `test_public_finalization_gates_preserve_raw_audit_metadata` confirms raw values are echoed rather than coerced.
- **Strict PASS / PASS_WITH_RISKS**: PASS acceptance and PASS_WITH_RISKS denial (`DENY_AUDIT_NOT_STRICT_PASS`, both orders) are preserved. REMEDIATION is untouched.
- **Backward compatibility**: for every executed-audit proof (`audit_source` = ci-executed / ci-unavailable / signed-imported-evidence, or any `_skipped_audit` diagnostic where `required` is `True`), `not_required_claimed` is `False` and `expected_base_sha` is ignored. The CI gates therefore did not change behaviour for PASS proofs.

The workflow test is unusually strong evidence: it *extracts and executes* each workflow's inline enforcement heredoc against a real emitter-produced proof, rather than string-matching the YAML. That closes the usual gap between "the workflow text mentions the parameter" and "the workflow actually binds it".

## 3. Principal residual risk

**The strict-PASS finalization branch remains unvalidated.** In `steward_gate`, the canonical validator is invoked only when `evidence["proof_embedded_audit_status"] == "SKIPPED"`. `_evidence` never reads `executed`, `dry_run`, `repo`, `pr_number` or `provenance`. Consequently a locally present `PROOF.json` whose status is `"PASS"` is accepted with `executed: false`, `dry_run: true`, a foreign repo/PR, or absent provenance — provided only that the head SHA matches and the timestamps are fresh. Fork commits share SHAs with upstream, so head equality is not repo-disambiguating.

This is **pre-existing and explicitly out of the frozen contract** (packet invariant: preserve ordinary executed PASS semantics; docs: "executed-audit proof semantics remain unchanged"). It is not a regression. But it means the hardening is asymmetric: an actor able to write the policy-path artifacts — the same capability required to forge NOT_REQUIRED evidence — can simply assert `PASS` and bypass every check this packet adds. That asymmetry is the reason this audit returns PASS_WITH_RISKS rather than PASS, and it is the obvious next packet.

A second, related risk: `scripts/` is not in the `pyproject.toml` packages list, so the mirrored gate copies can only reach the canonical validator from a repo checkout. In a packaged deployment the NOT_REQUIRED path denies (correct, fail-closed) while the weaker PASS path keeps working — an availability asymmetry pointing in the wrong direction. `collector._independent_audit_errors` performs the same import with no guard, so an ImportError there propagates instead of degrading to `NEEDS_SUPERVISOR`. Both are pre-existing.

Third: **no supplied artifact binds the frozen head.** `PROOF.json` carries `head_sha: null` and `independent_audit_status: NOT_RUN`; the "post-commit freeze receipt" it references is not among the 44 files. That does not affect code correctness — the packet proof is documentary and is not the artifact the gates consume — but the acceptance criterion "proof is current to the PR head SHA" is not evidenced for `a54eb4ab`, and `change_contract_preflight` itself states a rerun on the frozen head is required.

## 4. Delta separation and receipt hygiene

The three deltas are cleanly separable and honestly labelled:

- **Provenance closure** — validator, gate x4, queue x4, collector, CLI, two workflows, two docs, five test files.
- **Pre-existing baseline repairs** — `pyproject.toml` adds only `"dopemux.dcp"` (proved structurally by `verify_closure.py`, which inserts that single entry into the parsed pre-change TOML and asserts dict equality), and the stale doctor expectation is realigned to already-implemented behaviour. No production doctor code changed.
- **Integration fixture alignment** — exactly two `repo=None` substitutions in one named positive test, with all four original assertions intact.

Historical failures are preserved rather than laundered: the baseline stop, the scope stop (`sha256 dbd594cc…`), both scope preflights and the architecture return retain their non-PASS statuses, their deterministic tool failures, and `final_substantive_head: null`. `ARCHITECTURE_RETURN.json` records `provider_attested_identity: UNKNOWN` and that the parent session ran at `high` when `ultra` was requested — no substituted success claim. The prior Gemini PASS on `8826b717…` is explicitly demoted to history. `verify_closure.py` is a well-designed receipt: its structural YAML comparison (restore the modified step, assert whole-document equality) is what makes "triggers and permissions unchanged" a structural rather than textual claim.

Proof privacy is clean: no credentials or absolute user paths; the four untracked `proof/pr_merge/run_*` artifacts are quarantined from export and absent from the subject.

## 5. Disposition

The provenance repair is correct, fail-closed at every new branch, backward-compatible for executed-audit proofs, mirrored byte-identically across all four copies, and does not touch triggers, permissions, model/provider routing, or branch protection. No new authority bypass was found.

It is returned **PASS_WITH_RISKS** with three explicit remaining risks: (1) the unvalidated strict-PASS finalization branch, (2) the unpackaged canonical validator and unguarded collector import, and (3) the missing frozen-head proof binding. None is blocking for this packet; (3) must be resolved by a supervisor-recorded freeze receipt before any closeout, and (1) should be authorized as the next packet. Under `docs/ops/steward-merge-gate.md`, PASS_WITH_RISKS does not authorize automated finalization for this PR.