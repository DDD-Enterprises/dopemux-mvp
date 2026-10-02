# Auditor Report — PR #1363 / Root anyio 4.13.0 → 4.14.2

**Verdict:** **PASS_WITH_RISKS**  
**Scope:** audit evidence only; never readiness/merge authority  
**Base:** `d39b691c7d420a95a1a1372a793623840b4e84b0`  
**Head:** `28e65967f8572382fe673efc062873cea153e6fa`

## Scope and evidence

Only root `uv.lock` changes. The diff updates `anyio` from 4.13.0 to 4.14.2 within its single package block. Source registry remains `https://pypi.org/simple`. Both sdist and the `py3-none-any` wheel entries are updated with new hashes and timestamps matching the upstream 4.14.2 release. Dependencies (`idna`, `typing-extensions` for Python < 3.13) are unchanged. No other packages, markers, or dependencies were altered.

`uv lock --check --offline` passed with 276 packages resolved. In addition, `git diff --check origin/main...HEAD`, change-contract validation (`validate_change_contract.py`), and `import anyio` smoke test passed cleanly.

## Findings

- **F-001 (INFO / RESOLVED):** Change is confined to a single anyio package block in uv.lock. The diff touches only the anyio entry in the root `uv.lock`. No `pyproject.toml`, source, or workflow files change. The governance validator's L2 / one-path classification matches the diff.
- **F-002 (INFO / RESOLVED):** Dependency set and markers are unchanged. The dependency list and the `python_full_version < '3.13'` marker on `typing-extensions` are identical before and after. The lock still resolves 276 packages and `uv lock --check --offline` passes.
- **F-003 (LOW / ACCEPTED_RISK):** Artifact hashes not independently verified against the PyPI registry. `uv lock --check --offline` confirms consistency with project metadata, not that the new sha256 values match the files PyPI serves. URLs follow the standard files.pythonhosted.org layout and upload timestamps (2026-07-12) are mutually consistent. `uv sync` re-verifies hashes at install time, so a mismatch would fail loudly. No anomaly was observed, but registry-side verification was not performed.
- **F-004 (LOW / ACCEPTED_RISK):** Minor-version bump validated only by import smoke test. None of the supplied checks exercise downstream consumers of anyio under 4.14.2. Minor releases can alter cancellation, task-group, or exception-group behavior that an import check cannot detect. Mitigated by anyio's 4.x compatibility policy and the repository's normal test suite, which was not run or reviewed in this audit.
- **F-005 (INFO / ACCEPTED_RISK):** Possible transient version skew with nested lock. A separate bump (#1364) moves anyio to 4.14.2 in `docker/mcp-servers-source/pal/pal-mcp-server`. Until both PRs land, the two independently deployed locks may pin different anyio versions. Not a defect in this PR.

## Remaining risks

- New sdist/wheel sha256 values were not cross-checked against PyPI; integrity relies on uv's install-time hash verification.
- Runtime compatibility of anyio 4.14.2 with downstream packages was not exercised beyond `import anyio`.
- Transient version skew with the nested pal-mcp-server lock until #1364 and #1363 are both merged.

## Route receipt

Claude Code 2.1.287, selector `sonnet`, high effort, restricted plan mode, strict empty MCP config, zero tools, one turn. Exit 0, cost $0.0582366. Session ID: `734733ea-37fd-4d15-a29d-d0081fc2aa61`.

No repository/GitHub/workflow/service/container/signing/commit/mark-ready/close/merge effect occurred.
