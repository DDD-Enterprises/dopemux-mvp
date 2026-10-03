# Tier-1 audit: DCP runner convergence (R6)

**Subject:** base `f9ea7d1af`, head `2fbcfd89a`. The head matches the stated candidate.

**Verdict: FAIL.** The candidate breaks an existing DCP guard test that passes on base. Most other criteria pass.

## Blocking finding

`tests/dcp/test_dcp_0004_control_snapshot.py::test_18_no_bridge_memory_context_or_task_orchestrator_call_path` passes on base and fails on the candidate.

- That test reads every `src/dopemux/dcp/*.py` file and fails if the text contains the substring `subprocess`.
- `src/dopemux/dcp/runner_contract.py` contains it three times. Two are prose, in the module docstring (line 8) and the `execute_runner_plan` docstring (line 190). The third is the runtime string `"no_subprocess_executed"` (line 86), which is also asserted in `test_runner_contract.py`.
- The packet's verify command is `pytest tests/unit/dcp -q`. It passes (278 passed) but does not cover `tests/dcp/`, so it misses this regression.

**Fix:**
- Reword the two docstrings to avoid the literal `subprocess`, for example "no process spawning".
- Rename the non-claim token to something like `no_process_spawned`, and update `tests/unit/dcp/test_runner_contract.py:60` to match.
- Alternatively, split the string the way the guard tests do (`"sub" + "process"`), but that is worse for a non-claim string that is serialized.
- Then rerun `tests/dcp` as well as `tests/unit/dcp`.

## Criteria results

| # | Criterion | Result |
|---|---|---|
| 1 | Allowlist | Pass. All 14 committed paths fall under the allowlist. The change-contract validator listed 14 paths, with no violations visible in the tail I read. |
| 2 | Inert runner contract | Pass. `RunnerAdapter` is a `runtime_checkable` Protocol, `InertRunnerAdapter` conforms, and `execute_runner_plan` always returns `NOT_RUN` or `BLOCKED`. `invocation_authorized=True` raises. |
| 3 | Capability registry | Pass. `runner_capability_registry.py` is wired to `config/dcp/runner_capabilities.json` and is fail-closed on all global and per-runner flags. The config validates against its schema in a test. |
| 4 | Manifest | Pass. 35 contracts, 35 unique IDs, 35 unique schema files, and every file exists. The manifest validates against `dcp_contracts_manifest.schema.json`. That schema is the manifest's own schema and is not listed in the manifest, which is the same on base. |
| 5 | Unit tests | Pass. `tests/unit/dcp` gives 278 passed in 0.17s, and the new tests use no network or daemon. |
| 6 | Produced-dict vs schema | Pass. `document_plan(...).to_dict()` validates with Draft7 with and without `timeout_seconds`. I confirmed this independently. |
| 7 | Docs frontmatter | Partial. All four docs have consistent frontmatter. I did not run a docs-lint tool, because none was found under `scripts/`. |
| 8 | No extraneous deps | Pass for the commit. `uv.lock` has an uncommitted working-tree diff (adds `pypdf`, `python-magic`, `tiktoken`), so the lockfile must not be staged into this slice. |
| 9 | `git diff --check` | Pass. It returned rc 0 on `f9ea7d1af..2fbcfd89a`. |

## Non-blocking observations

- `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified` also fails here. It fails identically on base, because it diffs against a stale packet base ref that pulls in unrelated `.github/workflows` and `dopemux_pr_merge_specialist` files. It is pre-existing and not attributable to this candidate.
- `src/dopemux/dcp/__init__.py` has a stray blank line inside `__all__`, and its imports are not isort-ordered (`runner_contract` before `runner_capability_registry`).
- `config/dcp/runner_capabilities.json` records `version_text` and install paths as static observations. Install paths are `~`-relative, as the note says they were genericized. Nothing is verified against a live probe, which is acceptable for a non-authoritative registry.
- The `proof/TP-DMX-MD-R6-DCP-RUNNER-CONVERGENCE-001/` directory is untracked and not part of the audited commit. Its contents were not audited.

```json
{
  "verdict": "FAIL",
  "confidence": "HIGH",
  "summary": "Allowlist, inert contract, registry, manifest (35 unique), produced-dict schema test, tests/unit/dcp (278 pass) and git diff --check all verify. However, the candidate regresses the existing guard test tests/dcp/test_dcp_0004_control_snapshot.py::test_18_no_bridge_memory_context_or_task_orchestrator_call_path (passes on base f9ea7d1af, fails on head) because runner_contract.py contains the literal substring 'subprocess' in two docstrings and the 'no_subprocess_executed' non-claim string. The packet's verify command only runs tests/unit/dcp and so misses it.",
  "findings": [
    {
      "severity": "BLOCKING",
      "file": "src/dopemux/dcp/runner_contract.py",
      "lines": [8, 86, 190],
      "issue": "Literal 'subprocess' in src/dopemux/dcp/*.py trips tests/dcp/test_dcp_0004_control_snapshot.py::test_18 (passes on base, fails on head).",
      "remediation": "Reword the docstrings, rename the 'no_subprocess_executed' non-claim (and update tests/unit/dcp/test_runner_contract.py), then run both tests/dcp and tests/unit/dcp."
    },
    {
      "severity": "INFO",
      "file": "tests/dcp/test_dcp_0002_contract_derivation.py",
      "issue": "test_16_no_forbidden_files_modified fails on both base and head due to a stale packet base ref; pre-existing, not attributable to this candidate."
    },
    {
      "severity": "INFO",
      "file": "uv.lock",
      "issue": "Uncommitted working-tree changes (pypdf, python-magic, tiktoken); must not be staged into this slice."
    },
    {
      "severity": "INFO",
      "file": "src/dopemux/dcp/__init__.py",
      "issue": "Stray blank line inside __all__ and non-isort import order."
    }
  ]
}
```
