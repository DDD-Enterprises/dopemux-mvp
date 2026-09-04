# Implementation Notes

## Post-merge governance record (PR #1306)

This successor closes one live residual P0 defect found on a merged-main reharvest after
PR #1306 merged. No runtime, schema, topology, catalog, compose, service, database, Redis,
or runner configuration change lands here.

## Merged-main reharvest facts

- PR #1306 merge SHA: `a8a7514b42107ce2d7eb017875f72911fbbbd96d`
- Audited content head: `2e31726c1467770030d1fcb7358e5d7295e09b7b`
- Final PR head: `3d0172de6b27c9bfcf9ff1778c18eae06dadb342`
- Base main for this successor at dispatch: `649fe5e73496d76a54410dfa45a9d97b11634207`
- PR #1306 merged with six unresolved Copilot review threads at post-merge inspection;
  that history is preserved, not rewritten or rebased.
- The compose-file thread is the live defect this successor closes: the P0
  no-runtime-effect guard (`test_no_runtime_effect_diff`) omitted repository-root compose
  files. The event-envelope thread is content-addressed by merged code, not re-litigated here.

## Security-release approval gate

`SECURITY_RELEASE_APPROVAL_REQUIRED` was named as a pre-merge gate in PR #1306. Separate
evidence proving that gate was satisfied before merge has not been observed in this
successor's evidence set, so it is recorded as `UNKNOWN` rather than retroactively
converting the merge into proof of the gate. No retroactive PR Steward READY is claimed.

## Repair

Only `tests/arch/test_mcp_multiproject_contracts.py` changes substantively:

- `FORBIDDEN_P0_PREFIXES` lifted to module scope (unchanged semantics).
- `ROOT_COMPOSE_PATTERNS` added: `compose.yml`, `compose.yaml`, `compose.*.yml`,
  `compose.*.yaml` at repository root.
- `_is_forbidden_p0_path()` returns true for a forbidden prefix or a root-level compose
  file; subdirectory paths are not root compose and fall through to prefix checks.
- Focused fixtures reject `compose.yml`, `compose.yaml`, `compose.override.yml`,
  `compose.dev.yaml`; allowed-path fixtures prove non-root/non-compose paths pass.
- `test_no_runtime_effect_diff` now fails on any changed path the helper forbids.

No compose file was modified. The packet `.md` received the repo-required YAML frontmatter
at registration; the packet `.json` is byte-identical to the authoring input
(SHA256 `46533a559e28b158b47482f6491124b825df9dfeffae79862a26ec6d7fb0f43d`).

## P1 status

P1 remains blocked until this successor is merged and current main is reharvested.
No P1 authorization is claimed here.
