# AUDITOR_REPORT — PR #1215 / TP-DMX-DEPENDABOT-VULN-REPAIR-001

## Verdict
PASS_WITH_RISKS

## Summary
Independent Claude Code CLI (sonnet 2.1.226) formal audit of Dependabot security-floor
repair PR #1215. Primary audit of product content confirmed patched floors close the 86
open alerts (critical fastmcp 3.4.6, aiohttp/cryptography/mcp/h2/mako/setuptools, Next
15.5.21, npm/pnpm transitive overrides). Follow-up audit of yaml-scoping fix confirmed
override is 1.x-only so vite optional peer yaml@^2.4.2 is no longer forced to 1.10.3,
while cosmiconfig's yaml 1.x consumer remains on 1.10.3 (GHSA-closed). Residual: ecdsa
via python-jose has no upstream patch; full multi-service integration suite NOT_RUN.

## Findings

### F-001 — Full Dependabot alert coverage
- severity: LOW
- status: ACCEPTED_RISK
- body: Live Dependabot API inventory (86 = 1c/48h/31m/6l) matched; all manifests with
  open alerts were updated; every package met or exceeded first_patched_version.

### F-002 — mcp pinned >=1.28.1,<2
- severity: LOW
- status: ACCEPTED_RISK
- body: Resolved 1.29.0; avoids unreviewed mcp 2.x major jump.

### F-003 — Task-packet schema fixed in-branch
- severity: LOW
- status: RESOLVED
- body: agent enum and undeclared risk_lane corrected; schema-valid.

### F-004 — Full service integration NOT_RUN
- severity: MEDIUM
- status: ACCEPTED_RISK
- body: fastmcp 2→3 major; unit tests + FastMCP smoke PASS; fleet integration not run.

### F-005 — yaml override scoped to 1.x (Copilot review fix)
- severity: LOW
- status: RESOLVED
- body: Replaced blanket yaml:1.10.3 with yaml@^1.0.0 / yaml@1 selectors; vite no longer
  peers to yaml@1.10.3; peerDependencyRules ignore missing optional vite yaml peer.

## Remaining risks
- ecdsa via python-jose (GHSA-wj6h-64fc-37mp) — no upstream patch
- Full multi-service integration suite NOT_RUN after fastmcp 3.x
- Local signed attestation is operator attestation, not CI-executed model audit

## Fixes applied by auditor
- none (audit-only)

## Evidence reviewed
- Live Dependabot alerts API, pyproject/package overrides, uv/npm/pnpm locks, TP + VALIDATION
- ui-dashboard yaml scoping delta vs prior unscoped override
- Secret scan clean

## Model identity
- tool: claude-code-cli
- model: sonnet
- version: 2.1.226
- implementer: grok-4.5 (distinct session)
