# Auditor Report — PR #1384 / Root urllib3 2.7.0 → 2.8.0

**Verdict:** **PASS_WITH_RISKS**  
**Scope:** audit evidence only; never readiness/merge authority  
**Base:** `949d485d066f697a011a385122bb4ecd03313454`  
**Head:** `7efa4bb1dcb0f23565c987a910c34de3e2af60ab`

## Scope and evidence

Only root `uv.lock` changes. The diff updates `urllib3` from 2.7.0 to 2.8.0 within its single package block. Source registry remains `https://pypi.org/simple`. Both sdist and the `py3-none-any` wheel entries are updated with new hashes and timestamps matching the upstream 2.8.0 release. No other packages, markers, or dependencies were altered.

`uv lock --check --offline` passed with 276 packages resolved. In addition, python smoke tests (`test_extract_local_smoke.py`, `test_cli_smoke.py`), offline urllib3 negative connection/scheme tests, and change-contract checks (`validate_change_contract.py`) passed cleanly.

## Findings

- **INFO / accepted risk:** Minimal mechanical lockfile bump of urllib3 from 2.7.0 to 2.8.0. Single package block updated; no secondary dependencies touched.

## Remaining risks

- No PyPI hash verification performed during tool-less audit (verified locally via `uv lock --check --offline`).
- Transitive urllib3 runtime behavior in HTTP consumers unexercised beyond smoke tests.

## Route receipt

Claude Code 2.1.287, selector `sonnet`, high effort, restricted plan mode, strict empty MCP config, zero tools, one turn. Exit 0, cost $0.0430782.

No repository/GitHub/workflow/service/container/signing/commit/mark-ready/close/merge effect occurred.
