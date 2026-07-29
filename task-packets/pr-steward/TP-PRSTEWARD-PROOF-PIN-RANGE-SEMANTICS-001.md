# TP-PRSTEWARD-PROOF-PIN-RANGE-SEMANTICS-001

## Identity

- Repository: `DDD-Enterprises/dopemux-mvp`
- Base: current `origin/main` at packet creation, `72af781e42e0702d9047946e0f5a250e7dff0fa5`
- Branch: `fix/pr-steward-proof-pin-range-semantics`
- Risk: HIGH
- System: PR Steward trust root
- Execution authority: this packet plus explicit operator continuation

## Objective

Repair proof self-reference validation so a normal implementation PR may end with one or more explicitly declared proof-only final commits without requiring the entire PR diff to be proof-only.

The implementation commit being proven remains the recorded `proof_head_sha`. The current PR head may differ only by a validated contiguous suffix of proof-only commits. Runtime, source, tests, schemas, workflows, configuration, or other non-proof changes after the proven implementation head must fail closed.

## Observed defect

Current `tools/pr_steward/classifier.py::_valid_self_reference_exception` compares `self_reference_exception.changed_files` against the entire PR changed-file inventory and requires every PR path to start with `proof/`.

That permits proof-only PRs but rejects the intended ordinary pattern:

1. implementation and tests reach validated head `I`;
2. independent audit evaluates `I`;
3. final commit `P` updates only proof artifacts and makes PR head `P`;
4. proof records `I`, because `P` cannot contain its own SHA.

PR #1140 currently exhibits this contradiction: the final commit changes only `PROOF.json`, but the PR also contains policy code and tests, so the existing whole-PR-path check cannot validate it.

## Scope IN

- `tools/pr_steward/collector.py`, only if additional commit metadata is required
- `tools/pr_steward/classifier.py`
- focused tests and fixtures under `tests/pr_steward/` and `tests/fixtures/pr_steward/`
- this task packet
- proof and embedded-audit artifacts for this packet

## Scope OUT

- changing audit verdict semantics
- weakening exact-head, CI, reviewer, thread, harvest, or security-release gates
- accepting arbitrary stale proof
- accepting non-proof changes after the recorded implementation head
- changing DCP, runtime services, MCP topology, product behavior, branch protection, or merge policy
- merging or closing any PR

## Required semantics

A self-reference exception is valid only when all conditions hold:

1. `proof_freshness.status == CURRENT_WITH_SELF_REFERENCE_EXCEPTION`.
2. `self_reference_exception.supervisor_accepted == true`.
3. Embedded audit is `PASS` or non-blocking `PASS_WITH_RISKS`.
4. `proof_head_sha` and current PR `head_sha` are full 40-character hexadecimal SHAs.
5. `proof_head_sha` is an ancestor of current PR head.
6. The commit range `proof_head_sha..pr_head_sha` is non-empty and contiguous on the PR first-parent lineage.
7. Every changed path in that commit range is under `proof/`.
8. The complete range path set exactly matches `self_reference_exception.changed_files` after normalization.
9. No commit in the suffix is a merge commit.
10. No path is deleted or renamed out of `proof/` without retaining proof-only classification.
11. The suffix contains no runtime, source, test, schema, workflow, configuration, task-packet, or documentation change outside `proof/`.
12. Missing commit-range evidence, API failure, malformed SHA, ancestry ambiguity, duplicate path, or mismatch fails closed.
13. The whole PR diff may contain implementation paths before `proof_head_sha`; those paths must not be mistaken for post-validation changes.

## Evidence design

Do not trust a caller-supplied Boolean claiming the suffix is proof-only.

Collector must provide deterministic suffix evidence derived from Git/GitHub state, including:

- recorded implementation SHA
- current PR head SHA
- ancestry result
- ordered suffix commits
- parent counts
- per-commit changed paths and statuses
- normalized union of suffix paths
- command/API errors

Classifier must validate that evidence and the declared exception independently.

If the existing architecture can derive the range safely inside the classifier without shelling out, an equivalent deterministic design is acceptable. Document the authority source.

## Mandatory tests

Add focused tests for:

1. proof-only PR remains accepted under the existing contract;
2. code PR plus one proof-only final commit is accepted;
3. code PR plus multiple proof-only final commits is accepted when contiguous;
4. source change after the recorded implementation head is rejected;
5. test change after the recorded implementation head is rejected;
6. schema/workflow/config change after the recorded head is rejected;
7. merge commit in the suffix is rejected;
8. recorded SHA is not an ancestor of PR head;
9. malformed or abbreviated SHA;
10. missing range evidence;
11. changed-file declaration omits a suffix path;
12. declaration includes an extra path;
13. rename from `proof/` to non-proof is rejected;
14. duplicate path or inconsistent status fails closed;
15. audit `FAIL`, `SKIPPED`, or `NEEDS_SUPERVISOR` blocks;
16. `supervisor_accepted=false` blocks;
17. ordinary stale proof without the explicit exception blocks;
18. PR #1140-shaped fixture, with implementation paths in the whole PR but only `proof/PROOF.json` after the proven head, reaches no stale-proof blocker.

## Validation gates

Run and record exact exit codes for:

```bash
python -m compileall -q tools/pr_steward
uv run pytest -q tests/pr_steward/test_classifier_proof_status.py
uv run pytest -q tests/pr_steward/
git diff --check
pre-commit run --files <all changed files>
```

Run a live PR Steward intake against the repair PR exact head when credentials are available. It may remain blocked by trust-root security approval, but it must not fabricate freshness.

## Proof requirements

Capture:

- repository identity
- base and head SHAs
- status before and after
- changed-file inventory
- relevant full diff
- commands and exit codes
- tests
- proof schema validation
- exact independent-audit invocation and model
- audited implementation head
- findings, fixes, residual risks
- PR URL

## Independent audit

Required. This changes proof authority and merge readiness.

AGY/Gemini Flash may implement mechanical changes but may not be the sole auditor. Use an independently invoked approved route with exact tool/model evidence. Verdict must be `PASS` or non-blocking `PASS_WITH_RISKS` against the final implementation head.

## PR relationship

- This repair is a prerequisite for truthful readiness evaluation of PR #1140.
- Do not modify or merge #1140 until this repair is independently audited and merged, or until a supervisor approves an alternative exact proof design.
- Re-run #1140 proof, audit freshness, CI, and PR Steward against its then-current head afterward.

## Forbidden actions

- no force push
- no history rewrite
- no branch deletion
- no merge
- no PR closure
- no weakening to filename-only or caller-asserted proof
- no runtime mutation

## Stop conditions

Stop with `NEEDS_SUPERVISOR` if:

- GitHub cannot prove ancestry or suffix paths;
- more than one defensible authority interpretation remains;
- existing schemas cannot represent the required evidence without broader migration;
- tests reveal another trust-root dependency;
- diff escapes the allowlist;
- audit identity or audited head is unknown.

## Expected result

A draft PR whose implementation is bounded, fail-closed, independently audited, and capable of distinguishing:

- stale proof;
- an authorized proof-only final suffix;
- forbidden post-validation changes.

No merge-readiness claim is authorized by this packet alone.
