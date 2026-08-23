# TP-DCP-MCP-RO-0011-REMEDIATION-01 Auditor Report

## Verdict

`SKIPPED` for the canonical CI embedded-audit field. That field requires a
trusted `embedded-audit.yml` proof and remains unavailable because the GitHub
runner has no configured `claude` executable.

## Attempted Review

The read-only Codex reviewer could not initialize under the filesystem sandbox
because its in-process app-server client received an `Operation not permitted`
error. An approved escalated, read-only retry traced the changed source and
related identity writer/consumer paths, but it did not emit a final findings
verdict before termination. That trace is not treated as approval.

## Local Mitigation

Manual review cross-checked the following authority paths:

- `ProjectIdentity.project_id` is the canonical generated runtime identity.
- `runtime_state.resolve_identity_view` exposes that identity to lifecycle.
- `lifecycle._registry_upsert` writes the lifecycle-generated `project_id`.
- `resolver_core` validates `.repo_id` while resolving a DCP target before the
  runtime catalog join.
- `mcp.server` makes repository `src` importable to the facade runtime.

The remediation uses the existing `ProjectIdentity` value model without
reimplementing its hash or slug algorithm. Regression tests cover both the
lifecycle-generated positive match and the simplified DCP identity rejection.

## Remaining Review Gap

A separate read-only Grok Build audit returned `PASS_WITH_RISKS`; its findings
are recorded in `GROK_AUDIT.md`. It found no runtime-join blocker, but is not a
substitute for the trusted CI proof that the current Steward gate requires.

Merge readiness therefore remains blocked on a credentialed, installed CI
auditor route and a passing audit against the current PR head.
