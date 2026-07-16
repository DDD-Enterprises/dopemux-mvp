# TP-DCP-MCP-RO-0011-REMEDIATION-01 Command Log

All commands below ran in the dedicated worktree on branch
`codex/dcp-mcp-ro-0011-identity-remediation`. The implementation commit is
`6c5fc5ed6bdde8733d126864680e8c6ec2d1415c`.

| Command | Result |
| --- | --- |
| `unzip -t dopemux-multi-provider-mcp-supervisor-package.zip` | PASS |
| Manifest SHA-256 verification after extraction | PASS |
| `uv run --frozen pytest -q services/dcp-readonly-facade/tests/test_runtime_catalog_join.py` | PASS, 13 tests |
| `uv run --frozen pytest -q services/dcp-readonly-facade/tests` | PASS, live optional test skipped |
| `uv run --frozen pytest -q tests/unit/test_mcp_lifecycle.py::test_task_orchestrator_container_name_matches_wrapper_state_id` | PASS, 1 test |
| `uv run --frozen python -m compileall -q services/dcp-readonly-facade/src` | PASS |
| Task packet JSON schema validation | PASS |
| `dopemux orchestrator packet validate ...REMEDIATION-01.json` | PASS |
| AST purity scan for runtime join I/O imports/calls | PASS |
| `git diff --check` and `git diff --cached --check` | PASS; unrelated fsmonitor IPC warning emitted |
| `pre-commit run --files <implementation allowlist>` | PASS after first-run packet front-matter normalization |
| Read-only Codex differential review | NOT_RUN; see `AUDITOR_REPORT.md` |
| `grok -p` read-only differential audit | PASS_WITH_RISKS; see `GROK_AUDIT.md` |
| `agy --prompt=<read-only audit prompt> --mode=plan --sandbox --model=Gemini 3.1 Pro (High)` | PASS_WITH_RISKS at `c159c646a`; see `AGY_AUDIT.md` |

No live DCP facade, provider, transport, container, backend, or credential
operation was run.
