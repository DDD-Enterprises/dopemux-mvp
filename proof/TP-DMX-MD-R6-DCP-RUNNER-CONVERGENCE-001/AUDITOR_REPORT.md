TOOL_ACCESS=FULL
CUSTODY=MATCH head=9d036fb3308fea5ff63aa3b7691165cfe755f615 base=efb0ad8924a3c1c813fc4492f60c87896bd975ea
VERDICT=PASS_WITH_RISKS

# Embedded audit: TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001

**Subject:** `9d036fb33`, which is a single commit on top of `efb0ad892`. `git rev-parse HEAD` and `git merge-base HEAD origin/main` both match the pinned SHAs. I ran every check below myself in `/Users/hue/code/dopemux-r6-dcp`. I did not rely on `VALIDATION_RECEIPTS.json`.

## Criteria results

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Bounded allowlist | **PASS** | The diff has 14 paths, all under the packet allowlist: 4 docs, 1 config, 3 schema paths (2 new, 1 modified), 3 `src/dopemux/dcp` files, 2 test files and the task packet. There are 0 paths outside it. None of the forbidden prefixes are touched: `.github/workflows/`, `src/dopemux_pr_merge_specialist/` and `scripts/batch_resolve_and_merge.py`. `validate_change_contract.py --base origin/main --head HEAD` returned `status=PASS`, max lane L2, `model_audit_required=True`, 14 paths. |
| 2 | Inert runner contract | **PASS** | `RunnerAdapter` is a `@runtime_checkable` Protocol and `InertRunnerAdapter` implements it. `RunnerInvocationPlan` and `RunnerContractDocument` raise `RunnerContractError` if `invocation_authorized` is true. `document.to_dict()` hard-codes `invocation_authorized: False`. `execute_runner_plan` only ever returns `NOT_RUN` or `BLOCKED`. The module has no `subprocess`, network, asyncio or bridge imports. A test checks this by walking the module's AST. |
| 3 | Capability registry wired to config | **PASS** | `_DEFAULT_PATH` resolves to `config/dcp/runner_capabilities.json`. `_validate` fails closed unless all three global flags and every runner's three permission flags are exactly `False`. The loader then hard-codes `False` on the objects it builds. The config lists 6 runners (codex, claude, opencode, gemini, agy, grok), all with permissions false. |
| 4 | Manifest | **PASS** | `schemas/dcp/manifest.json` has 35 contracts, up from 33 on the base. It has 35 unique `contract_id` values and 35 unique `schema_file` values, with 0 duplicates. Every referenced schema, instance, producer and consumer file exists. The manifest validates against `dcp_contracts_manifest.schema.json`. That schema is the manifest's own meta-schema and already existed on the base, so it is correctly not listed as a contract. Every other `*.schema.json` in `schemas/dcp/` is listed. |
| 5 | Unit tests, no network or daemon | **PASS** | `pytest tests/unit/dcp -q` gave **278 passed in 0.19s** on Python 3.12.13. The new tests use only in-process objects, `tmp_path` and the repo JSON files. |
| 6 | Produced-dict-vs-schema regression | **PASS** | `test_document_plan_serializes_false_auth_and_validates_schema` validates `document_plan(...).to_dict()` against `runner_contract.schema.json` with a Draft7 validator. It covers both with and without `timeout_seconds`. `test_default_registry_conforms_to_schema` validates the shipped config against the registry schema. Both pass. |
| 7 | Docs and frontmatter | **PASS_WITH_RISKS** | `docs_frontmatter_guard.py` reports "All docs have valid frontmatter" for the 4 files. See risks R2–R4 below for content findings. |
| 8 | `git diff --check origin/main..HEAD` | **PASS** | Exit 0, no output. |

## Risks and findings (none blocking)

- **R1 (low): lint on new files.**
  - `flake8` reports F401 for unused `Mapping` in `src/dopemux/dcp/runner_contract.py:16`.
  - It reports another F401 for unused `RunnerContractDocument` in `tests/unit/dcp/test_runner_contract.py:12`.
  - `mypy` reports no errors in the two new modules. The 15 mypy errors it prints are in other files (`routing_classifier.py`, `control_snapshot.py` and others) that this commit does not touch.
  - Trivial to clean up. The change-contract and test gates don't catch it.
- **R2 (low): schema is not enforced at runtime.**
  - `load_runner_capabilities` does hand-rolled checks and never validates against `runner_capability_registry.schema.json`.
  - The schema is only checked in tests. A malformed registry that passes the manual flag checks would load. For example, a runner entry without `runner_id` would raise `KeyError` rather than `CapabilityRegistryError`.
  - It still fails closed on the authorization flags, which is the property that matters.
- **R3 (low–medium): docs staleness and thinness.**
  - `current-runtime-reconciliation.md` says it reconciles against "current `main` (post-#1400 `b2dc31f87…`)". The frozen base is `efb0ad892`, which is after #1401 and #1402. That anchor is stale by two merged PRs.
  - The doc also claims "Supersedes PR #1137" and `series-lineage.md` claims "Supersedes PR #1138". I did not verify those PRs' state.
  - `runner-capability-matrix.md` is titled a "matrix" but contains no per-runner rows. It only lists global flags and sources.
  - Statements that I did check hold: `mcp>=1.28.1,<2`, `fastmcp>=3.2.0,<4`, `requires-python >=3.11,<3.14` and `override-dependencies` are all in `pyproject.toml`.
- **R4 (low): unverifiable config provenance.**
  - `runner_capabilities.json` hard-codes `installed: true`, absolute-ish paths and version strings such as `codex-cli 0.145.0` and `claude 2.1.220`. These come from a local probe on the author's machine.
  - No probe artifact in the diff backs them. The notes call them "evidence-backed".
  - They are inert and non-authoritative, so this is only a provenance and drift concern.
- **R5 (environmental, not caused by this candidate): red-lane test failure.**
  - Running the full `tests/dcp` suite myself gave **1 failed, 192 passed**. The failure is `test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified`.
  - That test diffs `<base from task-packets/TP-DCP-0002.md>...HEAD`. The old pinned base is far behind, so it flags many unrelated `.github/workflows/*` and `dopemux_pr_merge_specialist` files.
  - This candidate touches 0 of the forbidden prefixes.
  - The author's receipt deselects this test, and I confirmed the failure is reproducible when it is not deselected.
  - Reviewers should know the unfiltered `tests/dcp` red-lane suite is red by design of that stale pin. I did not run it against `origin/main` to confirm it also fails there, so "pre-existing" rests on the diff evidence above.
- **R6 (process): uncommitted changes in the worktree.**
  - `git status` shows `M uv.lock`, `M .claude/.dopemux-advisor-cache.json` and untracked `proof/TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001/`.
  - None of these are in the audited commit, and I audited `HEAD` only.
  - `uv.lock` is outside the allowlist. It must not be committed into the subject.
  - The proof directory is allowlisted but still untracked.
  - Per CLAUDE.md `H4`, the TRACK-tier proof artifacts need `git add -f` and a proof-only successor commit. Per policy, a proof-only successor doesn't automatically invalidate this audit.

## Not performed

- I did not run the full `pytest tests/` suite or the CI workflows.
- I did not check the live state of PRs #1137, #1138, #1156 and #1157.
- `validate_dcp_p0_contract_semantics.py` requires a `--fixtures` argument I don't have, so I did not run it.
- This is a single-model audit, with no cross-model second opinion.

## Verdict rationale

All 8 required criteria are met on direct evidence. The R5 red-lane failure and the R1–R4 content nits do not undermine the inert-boundary guarantees. Hence **PASS_WITH_RISKS**, not PASS.

```json
{
  "tool_access": "FULL",
  "custody": {"match": true, "head": "9d036fb3308fea5ff63aa3b7691165cfe755f615", "base": "efb0ad8924a3c1c813fc4492f60c87896bd975ea"},
  "verdict": "PASS_WITH_RISKS",
  "criteria": {
    "1_allowlist": "PASS",
    "2_inert_runner_contract": "PASS",
    "3_capability_registry": "PASS",
    "4_manifest_35_unique_0_dupes": "PASS",
    "5_unit_tests_no_network": "PASS",
    "6_produced_dict_vs_schema_regression": "PASS",
    "7_docs_frontmatter": "PASS_WITH_RISKS",
    "8_git_diff_check": "PASS"
  },
  "validation": {
    "pytest_tests_unit_dcp": {"status": "PASS", "passed": 278, "failed": 0},
    "pytest_tests_dcp_unfiltered": {"status": "FAIL", "passed": 192, "failed": 1, "note": "test_16_no_forbidden_files_modified fails on a stale base pin in TP-DCP-0002.md; candidate touches no forbidden prefixes"},
    "git_diff_check": {"status": "PASS"},
    "validate_change_contract": {"status": "PASS", "max_lane": "L2", "paths": 14},
    "docs_frontmatter_guard": {"status": "PASS"},
    "flake8_new_files": {"status": "FAIL_MINOR", "findings": ["F401 runner_contract.py:16 Mapping", "F401 test_runner_contract.py:12 RunnerContractDocument"]},
    "mypy_new_modules": {"status": "PASS"},
    "full_test_suite": {"status": "NOT_RUN"},
    "validate_dcp_p0_contract_semantics": {"status": "NOT_RUN"}
  },
  "blocking_findings": [],
  "risks": [
    {"id": "R1", "severity": "low", "summary": "Unused imports (flake8 F401) in new files"},
    {"id": "R2", "severity": "low", "summary": "Registry loader does not validate against its JSON schema at runtime; malformed runner entry raises KeyError not CapabilityRegistryError"},
    {"id": "R3", "severity": "low-medium", "summary": "current-runtime-reconciliation.md anchors on post-#1400 b2dc31f87 though base is efb0ad892; capability-matrix doc has no per-runner rows; supersession claims for #1137/#1138 unverified"},
    {"id": "R4", "severity": "low", "summary": "Runner install paths and version strings in config lack probe artifact in diff"},
    {"id": "R5", "severity": "medium-informational", "summary": "Unfiltered tests/dcp red-lane suite has 1 failure from a stale base pin; author receipt deselects it"},
    {"id": "R6", "severity": "process", "summary": "Worktree has uncommitted uv.lock and an advisor cache modification (both outside the audited commit) plus an untracked proof directory"}
  ],
  "audited_subject_mutated": false,
  "authority": "NONE"
}
```
