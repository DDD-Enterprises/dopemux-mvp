# TP-DCP-MCP-RO-0012 Command Log

All commands below ran locally in the dedicated worktree on branch
`codex/dcp-mcp-ro-0012-target-contract`. The implementation commit is
`f0d9452852dbc3883317cbae71f70d9a59f54d8e`.

| Command | Result |
| --- | --- |
| Package ZIP integrity and manifest verification | PASS before child-packet implementation; source package hash recorded in `PROOF.json` |
| `uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_tools_v2.py services/dcp-readonly-facade/tests/test_mcp_server.py` | PASS, 8 tests |
| `uv run --frozen pytest -q services/dcp-readonly-facade/tests` | PASS; one intentionally opt-in live test skipped |
| `uv run --frozen python -m compileall -q services/dcp-readonly-facade/src` | PASS |
| Task packet JSON schema validation | PASS; jsonschema emitted only its CLI deprecation warning |
| `pre-commit run --files <TP-0012 implementation allowlist>` | PASS |
| `git diff --check` and cached allowlist review | PASS; unrelated fsmonitor IPC warning emitted |
| `agy --prompt=<read-only TP-0012 audit prompt>` | PASS_WITH_RISKS; see `AGY_AUDIT.md` |
| `python -m json.tool PROOF.json` and `python scripts/audit/validate_audit_proof.py PROOF.json` | PASS |
| `pre-commit run --files proof/TP-DCP-MCP-RO-0012/*` | PASS |
| Trusted embedded audit / PR Steward | NOT_RUN; local-only direction, no runner or credentials, and no trusted Claude auditor route |

No live facade, provider, connector, tunnel, backend, container, credential,
or runtime lifecycle operation was run.
