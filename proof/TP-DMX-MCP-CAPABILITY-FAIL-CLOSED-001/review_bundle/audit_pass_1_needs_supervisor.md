# Independent L3 Audit — Pass 1

**Auditor**: Codex coding agent (GPT-5-based runtime), read-only sandbox, `codex:codex-rescue` subagent
**Audited commit**: `c1fbf8e6ce15535e6bfe1c215c874736da2b8ea3` (superseded)
**Verdict**: NEEDS_SUPERVISOR

## Verbatim findings

1. **Verdict: NEEDS_SUPERVISOR**

2. **F018 fix analysis**: Confirmed correct for the tested single-run case (resolver.py:44-69,
   test_resolver.py:51,74). **Risk found**: `resolution_report` is instance state (resolver.py:16);
   `resolve()` did not reset that state (resolver.py:23). Reusing the same `InstanceResolver`
   instance after profile/config changes could retain stale `repo_profile` provenance, letting an
   env-only service with the same name wrongly inherit repo-profile authority under resolver reuse.
   Fail-closed in the tested single-run case, but authority-broadening under object reuse.

3. **F019 fix analysis**: Confirmed correct (gate.py:75,83,85,88,93,96,102). Full diff confirms only
   the handshake-suppression logic was removed/altered; mandatory/optional/strict_optional policy
   branches otherwise unchanged. Tests cover all four target cases.

4. **Test run results — BLOCKED, not a code failure**: Both focused and full `tests/mcp` pytest runs
   failed to start collection in the Codex sandbox (`FileNotFoundError: No usable temporary directory
   found`) — a sandbox/tempdir permission issue, not a test-logic failure.

5. **Scope confinement check — PASS**: Changed files match the allowed list exactly. No changes in
   discovery.py, provision.py, schemas, or config.

6. **New fail-open / authority-broadening / regressions**: No new fail-open path in gate.py's target
   logic. One authority-broadening edge in resolver.py: stale `repo_profile` provenance can persist
   across repeated `resolve()` calls on a reused `InstanceResolver` instance, which could let a later
   env-only service inherit repo-profile authority. Reachability depends on caller lifecycle, which the
   diff/tests didn't establish — hence NEEDS_SUPERVISOR rather than outright FAIL.

7. **Self-identification**: Codex coding agent (GPT-5-based runtime), read-only sandbox, independent
   from the commit author.

## Disposition

The implementer (Claude Sonnet 5) accepted this finding as valid and in-scope, and amended C1 to add
a `resolve()` state-reset plus a new regression test (`test_reused_resolver_does_not_leak_stale_provenance`)
before requesting a second audit pass. See `audit_pass_2_pass_with_risks.md`.
