# Auditor report: TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001

- Auditor: claude-code-cli (Claude Code, runtime model `claude-sonnet-5-5`), independent of the implementer (gemini). Read-only against source; only files under `proof/TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001/` were written.
- Base: `07b21e82a368c29adb96baf09573e03de74d4483` (re-verified equal to `origin/main` after `git fetch origin main`).
- Candidate head: `d237da2b5892e9640434d292b3a385cfaaa4d2e2` (single code commit on `successor/dcp-runner-convergence-r6`; `HEAD` == candidate head at audit start. During the audit the branch advanced to proof-only commit `0021959f4`, see AUDIT-008).
- Donors: PR #1156 (0008 runner contract) and #1157 (0009 capability registry), both OPEN; archival docs superseding #1137/#1138.

## Verdict: **PASS_WITH_RISKS**

All mandated gates pass on the frozen subject. Residual risks are LOW/INFO and do not block finality; they are listed below so the supervisor can accept them knowingly.

## Gate results (re-run by the auditor, not copied from receipts)

| Gate | Result |
|---|---|
| `uv run --frozen --extra test pytest tests/unit/dcp -q` | **278 passed** in 0.32s, exit 0 |
| `git diff --check origin/main..HEAD` | clean, exit 0 |
| `validate_change_contract.py --base origin/main --head HEAD --format text` | `status=PASS`, `max_lane=L2`, `model_audit_required=True`, `proof_only=False`, `paths=14` |
| `tests/dcp/test_dcp_0004_control_snapshot.py` | 22 passed |
| `scripts/docs_frontmatter_guard.py` on the 4 new docs | "All docs have valid frontmatter." |
| Manifest | 35 contracts, 35 unique `contract_id`, 35 unique `schema_file`, 0 duplicates, every `schema_file` exists; only schema on disk not listed is `dcp_contracts_manifest.schema.json` (the manifest's own meta-schema) |
| Both new schemas | `Draft7Validator.check_schema` OK |
| Working tree after test runs | only the untracked `proof/TP-.../` dir; `--frozen` left `uv.lock` untouched |

## 1. Scope containment: PASS

`git diff --name-status origin/main..HEAD` lists 14 paths (12 added, 2 modified: `schemas/dcp/manifest.json`, `src/dopemux/dcp/__init__.py`). Every path falls under the packet allowlist: `config/dcp/`, `docs/03-reference/dcp/`, `schemas/dcp/`, `src/dopemux/dcp/`, `tests/unit/dcp/`, `task-packets/TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001.json`. No `uv.lock`, `pyproject.toml`, workflow, or other out-of-scope change. `DIFF.patch` in the review bundle is byte-identical to a fresh `git diff origin/main..HEAD`. `HEAD_SHA.txt`/`BASE_SHA.txt` match the repo.

## 2. Implementation correctness: PASS

- **Inert runner contract** (`src/dopemux/dcp/runner_contract.py`): `RunnerAdapter` is a `@runtime_checkable` Protocol; `InertRunnerAdapter` satisfies it (`isinstance` test). `RunnerInvocationPlan` and `RunnerContractDocument` raise `RunnerContractError` if `invocation_authorized` is true; `to_dict()` hard-codes `invocation_authorized: False` at document level. `execute_runner_plan` always returns `NOT_RUN` (or `BLOCKED` in an unreachable belt-and-suspenders branch). Imports are only `dataclasses`, `enum`, `typing`.
- **Produced-dict-vs-schema regression**: `test_document_plan_serializes_false_auth_and_validates_schema` validates real `document_plan(...).to_dict()` output (with and without optional `timeout_seconds`) against `runner_contract.schema.json` with `Draft7Validator`. Present and passing. The schema is `additionalProperties:false` at every level, so key drift in `to_dict()` would fail the test.
- **Capability registry** (`runner_capability_registry.py` + `config/dcp/runner_capabilities.json`): `_DEFAULT_PATH` resolves to `<repo>/config/dcp/runner_capabilities.json` (`parents[3]`); loader fails closed unless all three `global_*` flags and every per-runner `invocation/mutation/paid_inference` flag are exactly `False`. Registry file validates against `runner_capability_registry.schema.json` (test). Tests cover authorized runner rejection, each `global_*` flag, and `authorized_runners()` raising on mutated in-memory state. Imports are only `json`, `dataclasses`, `pathlib`, `typing`.
- **Manifest**: two new entries (`DCP_RUNNER_CAPABILITY_REGISTRY`, `DCP_RUNNER_CONTRACT`), each once, file references resolve, and the existing manifest consistency tests pass.
- **Docs**: four docs in `docs/03-reference/dcp/` pass the frontmatter guard and describe the code as it exists (types, schema/config/loader paths, non-claims). Spot-checked claims against the repo: `mcp>=1.28.1,<2` and `fastmcp>=3.2.0,<4` present in `pyproject.toml`, `tool.uv.override-dependencies` present, `mcp_catalog.yaml`, `input_adapters.py` and `trusted_adapter_registry.py` exist, #1400 (`b2dc31f87`) is an ancestor of main.
- **Boundary**: grep of both new modules for `subprocess|socket|httpx|requests|dopecon|dope_memory|dope_context|task_orchestrator` finds nothing. `test_no_subprocess_or_bridge_import_side_effects` AST-checks the contract module. Nothing outside `src/dopemux/dcp/` imports the new modules, so no bridge/memory/context/task-orchestrator call path is added.
- **Donor coverage**: candidate contains the #1156 payload (runner_contract.py, schema, manifest entry, `__init__` exports, tests, doc) and the #1157 payload (capability registry, schema, config, matrix doc), plus `RunnerAdapter`/`InertRunnerAdapter` additions. #1157's `config/dcp/trusted_input_adapters.json` is already on main (`git ls-files`). I compared donor file lists only, not donor line content.

## Findings (none blocking)

**AUDIT-001 LOW, `current-runtime-reconciliation.md` pins "post-#1400 `b2dc31f87`".** True (it is an ancestor) but main is now `07b21e82a` (post-#1389, #1401 in between). Inexact, not wrong. External-state claims in that doc (PAL, OpenCode, LiteLLM, GitHub control plane) are not verifiable from the repo and were not verified.

**AUDIT-002 LOW, `runner_capabilities.json` is a point-in-time host snapshot.** Pins local CLI versions and `~/...` shim paths (home-relative, no username leaked). Labelled non-authoritative and every authorization flag is false, so no safety impact; it will go stale.

**AUDIT-003 LOW, loader is stricter-than-schema but not schema-validated.** `load_runner_capabilities` checks the false-flags itself rather than running the JSON schema, so a malformed entry (e.g. missing `runner_id`) raises `KeyError`, not `CapabilityRegistryError`. Still fails closed. The schema only `required`s `global_invocation_authorized`, while the loader additionally demands the other two globals be present and false.

**AUDIT-004 LOW, default registry path is repo-relative.** `_DEFAULT_PATH` uses `parents[3]`, which holds for a source/editable checkout. I did not verify that `config/dcp/` ships in a built wheel; callers outside the repo must pass `path=`. No in-repo caller imports the module today.

**AUDIT-005 INFO, manifest producer/consumer fields are thin.** `DCP_RUNNER_CONTRACT` lists `runner_contract.py` as both producer and consumer; `DCP_RUNNER_CAPABILITY_REGISTRY` has no producer. Consistent with an inert contract; `REPO_CROSS_CHECKED` rests on test-level schema validation.

**AUDIT-006 INFO, proof directory was untracked at audit start.** It was committed at `0021959f4` mid-audit (see AUDIT-008). This audit's files are working-tree modifications on top of that commit and are not yet committed.

**AUDIT-007 INFO, prior audit superseded.** An earlier audit of `b0ea0b03d`/`16a14779b` (base `f9ea7d1af`) returned FAIL for an unfrozen subject, missing frontmatter, and a trailing blank line. None of those defects exist on `d237da2b5`: the head is a single frozen commit, frontmatter passes, `git diff --check` is clean. The earlier files are preserved in `prior_audit_16a14779b/` for provenance. That audit also noted `uv run` without `--frozen` dirties `uv.lock`; this audit used `--frozen` and `uv.lock` stayed clean.

**AUDIT-008 MEDIUM (OPEN), branch tip `0021959f4` fails `git diff --check` and commits stale FAIL audit records.** After the audited commit, `0021959f4` ("proof(dcp): record independent C8 audit PASS", 05:45:19) committed the proof dir. `git diff --name-only d237da2b5 HEAD` shows only `proof/TP-.../` paths, so code, config, schemas, docs and tests are byte-identical and the audit subject is unaffected. However:
- `git diff --check origin/main..0021959f4` exits 2: `review_bundle/DIFF.patch:393` and `review_bundle/GIT_DIFF.patch:393` "trailing whitespace" (patch files embed diff context). The same check on `d237da2b5` is clean (exit 0). `validate_change_contract.py` on the tip still returns PASS / L2 (paths=29).
- The committed `AUDIT_RETURN.json`/`PROOF.json` at that commit record status **FAIL** for earlier heads (`b0ea0b03d`/`16a14779b`), contradicting the commit message's "PASS". They are superseded by this audit's files, which are uncommitted.
- Remediation (finalizer): normalize or exclude the `.patch` bundle files from the whitespace check (drop the duplicate `GIT_DIFF.patch`; mark patches `-whitespace` via `.gitattributes` or store them outside the checked tree), commit this audit's files over the stale ones, and re-run `git diff --check origin/main..HEAD`. Finality should be certified against `d237da2b5` for code, and against the repaired tip for the packet-mandated diff-check.
- Untracked `proof/pr_merge/embedded-audit/pr-1403/PROOF.json` (PR #1403 is this branch; written 05:46 by another session) binds head `2ee540d49` / base `f9ea7d1af`, not `d237da2b5` / `07b21e82a`. It is stale against the audited subject and must not be treated as certifying it.
- `prior_audit_16a14779b/` in the proof dir is a copy of the earlier FAIL records (already in git at `0021959f4`); it is not a new artifact and may be deleted.

## Risks accepted under PASS_WITH_RISKS

1. External-runtime claims in `current-runtime-reconciliation.md` are unverified and the base reference is one commit-range behind main.
2. Registry config is a host snapshot and its default path assumes a source checkout.
3. Donor parity checked at file-list level only.
4. Branch tip `0021959f4` fails `git diff --check` (bundle patch files) and holds stale FAIL audit records until the finalizer repairs and re-commits (AUDIT-008). This does not touch the audited code.
