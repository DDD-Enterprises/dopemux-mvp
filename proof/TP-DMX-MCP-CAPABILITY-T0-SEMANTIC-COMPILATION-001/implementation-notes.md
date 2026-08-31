# T0 Implementation Notes

Task Packet: `TP-DMX-MCP-CAPABILITY-T0-SEMANTIC-COMPILATION-001`

## Authority

- Architecture gate: ratified before this tranche.
- Risk lane: L2, combining former M0 and M1 scope.
- Implementer: Codex, `gpt-5.6-sol`, high effort.
- Final auditor: AGY / Gemini 3.1 Pro, one invocation after substantive head freeze.
- Merge: unauthorized.
- Activation: unauthorized.
- Mark ready: unauthorized.

## Custody

- Repository: `DDD-Enterprises/dopemux-mvp`
- Base: `origin/main` at `5900c27d3c38b515204bd5dc4baed8b5e14e2a8e`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/t0-semantic-compilation-001`
- Branch: `feat/t0-semantic-compilation-001`

## Change Summary

- Added closed Draft 7 schema for shadow capability policy semantics.
- Added repository-owned policy pinned to `mode: shadow`.
- Added deterministic, side-effect-free compiler for Claude, Codex, OpenCode,
  Gemini, and Copilot decision projections.
- Added fail-closed checks for unknown policy fields, versions, clients,
  lifecycles, transports, exposures, and duplicate YAML keys.
- Added focused tests using real root catalog and policy files.
- Did not modify generated client configs, fleet catalog, runtime wiring, or
  activation surfaces.

## TDD Evidence

- Initial compiler test failed because module did not exist; passed after minimal
  compiler implementation.
- Override tests failed because lifecycle and transport precedence was absent;
  passed after explicit precedence implementation.
- Repository policy test failed because loader did not exist; passed after schema,
  policy, and read-only loader implementation.
- Duplicate-key test failed with leaked fleet-loader exception; passed after error
  normalization.
- Direct-policy bypass tests failed because compiler trusted unvalidated mappings;
  passed after closed semantic validation.
- Unknown-client test failed because undeclared agent keys were ignored; passed
  after explicit target/non-target key validation.

## Validation

| Check | Exit | Result |
| --- | ---: | --- |
| Task Packet JSON parse | 0 | PASS |
| Task Packet canonical schema | 0 | PASS; jsonschema CLI emitted deprecation warning |
| Semantic contract JSON parse | 0 | PASS |
| Focused capability compiler tests | 0 | PASS, 13 tests |
| Existing fleet catalog unit and architecture tests | 0 | PASS, 70 tests |
| Compiler compileall | 0 | PASS |
| Ruff lint | 0 | PASS |
| Ruff format check | 1 then 0 after formatting | PASS after deterministic formatter repair |
| `git diff --check` | NOT_RUN | Pending final content validation |
| Changed-contract preflight | NOT_RUN | Pending final content validation |
| Pre-commit | NOT_RUN | Pending final content validation |
| Independent frozen-head audit | NOT_RUN | Forbidden until substantive head freeze |

## Remaining Risk

- T0 emits semantic decision projections only. It does not render or apply client
  configuration.
- Five-client decisions are validated against current repository catalog, but no
  runtime/client/provider probe is part of T0.
- Final independent audit and publication remain pending.

## Rollback

Before merge, abandon branch and worktree. After any future merge authority,
revert the T0 commit; no migration, runtime state, or generated client config
requires restoration.
