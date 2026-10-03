# Tier-1 audit: DCP runner convergence (R6)

**Subject:** `2ee540d49` against base `f9ea7d1af`. I checked it in a detached worktree.

## The pasted diff is not the candidate

The diff in the request does not match `f9ea7d1af..2ee540d49`. It also shows deletions of PR #1389 proof bundles, reverts of the #1389 doc edits and a revert of the `--paths` fail-closed fix. It looks like it was generated against a stale or different base.

The real range is 14 files, 1045 insertions and 0 deletions. All 14 are inside the allowlist, and I did not audit the pasted diff itself.

## Criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Only allowlisted files changed | **Met.** 0 files fall outside the packet allowlist. The untracked `proof/TP-DMX-MD-R6-…/` is allowlisted and not in the commit. |
| 2 | Runner contract and `InertRunnerAdapter` | **Met.** `RunnerAdapter` is a runtime-checkable protocol. `execute_runner_plan` always returns `NOT_RUN`, the dataclasses reject `invocation_authorized=True`, and an AST test forbids subprocess, network and bridge imports. |
| 3 | Capability registry wired to config | **Met.** `_DEFAULT_PATH` points to `config/dcp/runner_capabilities.json`. The loader fails closed if any global or per-runner flag is not `false`. |
| 4 | Manifest has 35 unique contracts | **Met.** 35 entries, 35 unique IDs. The two new contracts are listed once each, and `tests/dcp` consistency passed. |
| 5 | Unit tests, no network | **Met.** The new tests and the rest of `tests/unit/dcp` and `tests/dcp` give 470 passed and 1 failed (see below). |
| 6 | `test_dcp_0004_control_snapshot` test_18 | **Met.** It passes, and the full 0004 file passes with 22 tests. |
| 7 | Produced-dict-vs-schema test | **Met.** Both new test files validate real output against the Draft-7 schemas, with and without the optional `timeout_seconds`. |
| 8 | Docs frontmatter | **Met.** `docs_frontmatter_guard.py` passes on all four docs. The repo-wide `docs_validator.py` exits 1, but the output I saw lists only archive docs, not the DCP files. |
| 9 | No extra dependencies | **Met.** No `pyproject.toml` or lockfile changes. |
| 10 | `git diff --check` | **Met.** It exits 0 for `f9ea7d1af..2ee540d49`. |

## Findings (non-blocking)

1. **`test_16_no_forbidden_files_modified` fails, but not because of this candidate.**
   - `tests/dcp/test_dcp_0002_contract_derivation.py::test_16_no_forbidden_files_modified` fails identically on the bare base `f9ea7d1af`.
   - The test diffs against a base SHA pinned in `task-packets/TP-DCP-0002.md`. That SHA is stale, so the test flags workflow and `pr_merge_specialist` files changed by unrelated merges.
   - It needs a separate fix. It should not gate this slice.
2. **The registry loader raises the wrong error for malformed input.**
   - `load_runner_capabilities` does not validate against its JSON schema at load time.
   - A runner entry without `runner_id` raises a bare `KeyError` instead of `CapabilityRegistryError`.
   - It still fails closed, so this is a low-severity robustness issue.
3. **The worktree HEAD is not the audited commit.**
   - The worktree HEAD is `d237da2b5`, a rebase onto `07b21e82a` (#1389).
   - I audited `2ee540d49` as specified, via a detached worktree.
   - Between the two commits, `src/`, `config/`, `schemas/`, `docs/03-reference/dcp`, `tests/unit/dcp` and the task packet differ only by 3 files, in `src/.claude/claude.md` and two other files. These are probably the #1389 changes.
   - Re-confirm the head before merge.

None of these block the slice. The verdict is based on the pinned head `2ee540d49`, not the pasted diff.

```json
{
  "verdict": "PASS",
  "confidence": "MEDIUM",
  "summary": "Pinned head 2ee540d49 over base f9ea7d1af changes 14 files, all allowlisted, with git diff --check clean. The inert runner contract, capability registry (all invocation flags forced false), 35-unique-contract manifest, schema-conformance tests and DCP docs frontmatter all verify, and tests/unit/dcp plus tests/dcp pass except one failure that also occurs on the bare base. The diff pasted in the request does not correspond to this commit range (it shows stale-base reverts such as deleting #1389 proofs) and was disregarded. Confidence is MEDIUM because of that mismatch and because the worktree HEAD (d237da2b5) is a rebase of the audited commit.",
  "findings": [
    {
      "severity": "LOW",
      "blocking": false,
      "title": "Pre-existing failure: tests/dcp test_16_no_forbidden_files_modified",
      "detail": "Fails identically on base f9ea7d1af because it diffs against a stale SHA pinned in task-packets/TP-DCP-0002.md. Unrelated to this candidate; needs a separate fix."
    },
    {
      "severity": "LOW",
      "blocking": false,
      "title": "Capability registry loader skips schema validation",
      "detail": "src/dopemux/dcp/runner_capability_registry.py load_runner_capabilities uses hand validation only; a runner entry missing runner_id raises KeyError rather than CapabilityRegistryError. Still fails closed."
    },
    {
      "severity": "INFO",
      "blocking": false,
      "title": "Pasted diff does not match the audited commit range; worktree HEAD differs from the pinned head",
      "detail": "The supplied diff reflects a stale base and was ignored. Worktree HEAD d237da2b5 is a rebase of 2ee540d49 onto 07b21e82a; re-confirm the head before merge."
    }
  ]
}
```
