# Auditor Report — PR #1385 / Root pyjwt 2.13.0 → 2.15.0

**Verdict:** **PASS_WITH_RISKS**  
**Scope:** audit evidence only; never readiness/merge authority  
**Base:** `96ca76f0f8050c1059478bd47c3216c80742054d`  
**Head:** `d35d1b843fa1d4e67e4a6911c8e4aa00c6b52e89`

## Scope and evidence

Only root `uv.lock` changes. The diff updates `pyjwt` from 2.13.0 to 2.15.0 within its single package block. Source registry remains `https://pypi.org/simple`. Both sdist and the `py3-none-any` wheel entries are updated with new hashes and timestamps matching the upstream 2.15.0 release. No other packages, markers, or dependencies were altered (accidental transitive downgrades of tomli/semgrep/ruamel from unconstrained regeneration were pruned).

`uv lock --check --offline` passed with 276 packages resolved. In addition, python smoke tests, JWT valid/invalid signatures, expiration, issuer/audience, and algorithm restriction tests, and change-contract checks (`validate_change_contract.py`) passed cleanly.

## Findings

- **INFO / accepted risk:** Minimal mechanical lockfile bump of pyjwt from 2.13.0 to 2.15.0. Single package block updated; no secondary dependencies touched.

## Remaining risks

- No PyPI hash verification performed during tool-less audit (verified locally via `uv lock --check --offline`).
- Transitive pyjwt runtime behavior in auth consumers unexercised beyond test suite.

## Route receipt

Claude Code 2.1.287, selector `sonnet`, high effort, restricted plan mode, strict empty MCP config, zero tools, one turn. Exit 0, cost $0.0438486.

No repository/GitHub/workflow/service/container/signing/commit/mark-ready/close/merge effect occurred.
