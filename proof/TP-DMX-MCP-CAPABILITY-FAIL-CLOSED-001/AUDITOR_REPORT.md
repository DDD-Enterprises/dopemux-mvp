# Auditor Report — TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001

**Controlling audit**: pass 2, verdict `PASS_WITH_RISKS`, audited commit `40783797fe30325766a2cb6f53aaa53254785712` (C1).

**Auditor identity**: OpenAI GPT-5 Codex, ChatGPT/Codex API runtime, invoked via the `codex:codex-rescue`
subagent — a different model family/runtime from the implementer (Claude Sonnet 5). Independence is
`OBSERVED`, not merely claimed: the auditor ran in its own sandboxed environment, with no access to the
implementer's reasoning beyond the audit prompt, and self-identified its runtime explicitly in both passes.

**Two audit passes were run** (both against the exact final substantive head, in sequence — no
unaudited content was published):

1. **Pass 1** (`c1fbf8e6ce15535e6bfe1c215c874736da2b8ea3`): `NEEDS_SUPERVISOR`. Identified a real,
   in-scope defect — `InstanceResolver.resolve()` did not reset per-call state, so a reused resolver
   instance could let stale `repo_profile` provenance leak across calls, an authority-broadening path
   created by combining the F018 fix with pre-existing state reuse. See
   `review_bundle/audit_pass_1_needs_supervisor.md`.

2. **Repair**: implementer added a state-reset at the top of `resolve()` plus a new regression test
   (`test_reused_resolver_does_not_leak_stale_provenance`), amended C1 to
   `40783797fe30325766a2cb6f53aaa53254785712`.

3. **Pass 2** (`40783797fe30325766a2cb6f53aaa53254785712`, final): `PASS_WITH_RISKS`. Confirmed the
   state-reset closes the identified path without introducing a caller regression, re-confirmed F018/F019
   correctness, confirmed scope confinement, found no remaining fail-open/authority-broadening path. The
   only risk: the auditor's own sandbox could not execute pytest (tempdir permission restriction),
   so it could not itself confirm pass/fail counts. See `review_bundle/audit_pass_2_pass_with_risks.md`.

**Risk disposition**: `NON_BLOCKING`. The unresolved item is a limitation of the auditor's execution
sandbox, not a finding against the code under audit. The implementer independently executed the exact
same test suites against the exact same commit in the real (non-sandboxed) repository environment:

- `tests/mcp/test_resolver.py` + `tests/mcp/test_discovery_gate_strict.py`: 16 passed
- `tests/mcp` (full relevant suite): 63 passed

Both runs include the new reuse-regression test the auditor could not itself execute. See
`review_bundle/focused_tests_output.txt` and `review_bundle/relevant_suite_output.txt`.

**Final verdict for this packet**: `PASS_WITH_RISKS`, all risks explicit and non-blocking per packet
section 6 (S6) acceptance criteria. Advances to proof-only closure (S7). Publication and merge remain
separately gated (not authorized by this packet).
