# TP-DMX-MCP-PR1150-REVIEW-REPAIR-001 Implementation Notes

## Scope

Repair all actionable unresolved review threads on PR #1150 without
implementing P-24, M11, or unrelated fleet migrations.

## Authority

- `AGENTS.md`
- `claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md`
- `claudedocs/mcp-fleet-multi-instance-evidence-2026-07-28.md`
- `claudedocs/mcp-legacy-launch-path-worklist-2026-07-28.md`
- runtime code, compose wiring, active entrypoints, and tests
- live unresolved GitHub review threads on PR #1150

Runtime inspection corrected two target-state claims:

- compose `mcp-pal` and `mcp-pal-stdio` remain active until blocked M5 runs;
- lettered A-E allocation remains active for `dopemux start` and
  `dopemux instances`, while MCP sidecars use hash identity.

P-24 ADR and M11 consumer sweep exist only on stacked draft PR #1161. P-24 is
`proposed`; M11 is evidence. Neither authorizes implementation in this packet.

## Root Causes

1. `scripts/setup.sh --skip-docker` mapped a user-facing install mode onto
   `INSTALLER_TEST_MODE=1`, which skips package install, shell integration, and
   verification.
2. Deleting the legacy launcher removed its external-network initialization,
   but bare compose-backed `dopemux mcp up` did not inherit that prerequisite.
3. Remediation prose conflated repo-aware MCP lifecycle with compose-backed
   compatibility behavior and conflated the Python port-8000 service with the
   Kotlin port-7890 service.
4. Health remediation interpolated repository paths without POSIX shell
   quoting.
5. Design target state was presented as current runtime state before migration
   gates landed.
6. Task Orchestrator documentation presented `/mcp` as a GET-style health URL
   instead of a Streamable HTTP `POST initialize` probe.

## Changes

- Added `DOPEMUX_SKIP_DOCKER=1` as a distinct installer mode.
  - Docker dependency checks, Docker environment setup, network setup, compose
    work, and Docker verification are skipped.
  - Python package install, shell integration, and four non-Docker verification
    checks still run.
- `scripts/setup.sh --skip-docker` now delegates using that mode and does not
  enable installer test mode.
- Bare compose-backed `dopemux mcp up` now creates missing
  `dopemux-network` through the existing cold-start helper before compose.
- Health hook uses `shlex.quote()` for displayed `--repo` paths.
- Installer stop guidance uses repo-aware `dopemux mcp stop`.
- Legacy validator remediation uses `dopemux mcp ensure --full`, which covers
  its PAL, Serena, and dope-context checks.
- Port-8000 recovery explicitly uses
  `dopemux mcp up --services task-orchestrator` from the product root and warns
  that repo-aware `mcp start` targets the separate Kotlin MCP service.
- Corrected PAL and A-E runtime/target-state documentation.
- Replaced both Task Orchestrator health URL claims with a protocol-correct
  Streamable HTTP initialization request.

## TDD Evidence

Focused regressions were added first and observed failing:

- setup shim did not pass a real no-Docker mode;
- installer entered Docker-only setup and verification;
- bare `mcp up` ran compose before external-network creation;
- health remediation emitted an unquoted repo path.

After minimal implementation, all five focused tests passed.

## Validation

### PASS

- Task Packet schema:
  `mise exec -- python -m jsonschema -i task-packets/TP-DMX-MCP-PR1150-REVIEW-REPAIR-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Target and surrounding suites:
  `94 passed, 1 skipped in 4.56s`
- Skip reason:
  `tests/mcp/test_discovery_gate.py` cannot bind TCP in this sandbox.
- Shell syntax:
  `bash -n` passed for all changed shell scripts.
- Python bytecode compile passed for changed Python/test files.
- Scoped docs validation passed for all changed canonical docs.
- Configured pre-commit hooks passed on every allowlisted changed file.
- `git diff --check` passed.
- Ruff check passed for new test and changed hook.
- ShellCheck found no changed-line error.

### FAIL

- Full-tree `scripts/docs_validator.py` reports six unchanged legacy errors:
  three deprecated-status ADRs and three archived Claude docs lacking valid
  type metadata. Scoped changed-doc validation passes.

### NOT_RUN

- Full repository test suite: blast radius covered by MCP, hook, CLI startup,
  lifecycle, installer, and P-22 suites; full suite remains CI responsibility.
- Formal embedded audit refresh: must run after final code commit and must bind
  to that exact head. External Claude review was blocked by environment privacy
  policy.
- PR Steward/final readiness: requires pushed repair and refreshed proof.

## Codereview

- AGY read-only review returned exit 0 with no report; not accepted as evidence.
- External Claude CLI review was blocked before execution by environment privacy
  policy.
- Local diff review found no remaining in-scope correctness issue.
- Pre-existing Ruff and ShellCheck findings outside changed lines were not
  broadened into this packet.

## Rollback

Revert the repair commit. This restores prior installer/remediation prose and
behavior. No database, schema, Docker runtime, lease registry, or generated MCP
configuration is mutated by this packet.
