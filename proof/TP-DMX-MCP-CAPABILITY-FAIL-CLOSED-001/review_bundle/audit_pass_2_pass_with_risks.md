# Independent L3 Audit — Pass 2 (final, controlling)

**Auditor**: OpenAI GPT-5 Codex, ChatGPT/Codex API runtime (self-identified), `codex:codex-rescue` subagent
**Audited commit**: `40783797fe30325766a2cb6f53aaa53254785712` (C1, frozen)
**Verdict**: PASS_WITH_RISKS

## Verbatim findings

**Identity**: OpenAI GPT-5 Codex, ChatGPT/Codex API runtime (self-identified in its report).

**Diff Scope**: confirmed the diff is confined to exactly `src/dopemux/mcp/gate.py`,
`src/dopemux/mcp/resolver.py`, `task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.{json,md}`,
`tests/mcp/test_discovery_gate_strict.py`, `tests/mcp/test_resolver.py`. No scope creep.

**State-Reset Fix Review**: the `resolve()` reset of `self.resolution_report` closes the
previously-identified stale-provenance leak. Both callers (`server_manager.py` — fresh
`InstanceResolver()` per config load, one `resolve()` call; `gate.py` — resolver constructed once in
`__init__`, `resolve()` called in `run()`) do not depend on cross-call state accumulation, so the reset
introduces no regression there.

**F018/F019**: re-verified as still correct — env override preserves `repo_profile` provenance,
env-only stays `env_var`, and `gate.py` always evaluates `required_tool_globs` regardless of handshake
warning.

**Test Execution**: BLOCKED again by sandbox, not by a real code failure. Setting `TMPDIR` to the
scratchpad directory still produced `FileNotFoundError: No usable temporary directory found` before
test collection completed, for both the focused command and the full `tests/mcp` run — all failures
were setup/fixture-level tempdir errors (E), not assertion failures in the audited code. Codex
explicitly declined to create `.pytest_tmp` in the worktree itself since it was instructed
read-only/no-file-modification.

**Remaining Issues**: none found — no fail-open path, authority-broadening path, or regression
identified in the diff.

**VERDICT: PASS_WITH_RISKS** — the code-level fix and diff review are clean, but the regression test
suite still could not be executed to completion in this sandbox (tempdir permission issue persists
even with the specified TMPDIR), so the new `test_reused_resolver_does_not_leak_stale_provenance` test
has not actually been run/confirmed passing by either audit pass. Recommend re-running pytest in an
environment with a genuinely writable tempdir before treating this as fully verified.

## Implementer's corroborating evidence (risk disposition)

The implementer (Claude Sonnet 5) independently ran the full test suites in the actual, non-sandboxed
repository environment on this exact commit (`40783797fe30325766a2cb6f53aaa53254785712`):

- `python -m pytest -q tests/mcp/test_resolver.py tests/mcp/test_discovery_gate_strict.py` → 16 passed
  (see `focused_tests_output.txt`)
- `python -m pytest -q tests/mcp` → 63 passed (see `relevant_suite_output.txt`)

Both runs include `test_reused_resolver_does_not_leak_stale_provenance`, which passed. The auditor's
risk is explicit (test execution blocked by the auditor's own sandbox tempdir restriction) and
non-blocking (a limitation of the auditor's execution environment, not a finding against the code,
and independently corroborated by real execution evidence from a non-sandboxed environment).
