# Independent L2 Audit Input — P0-R1 (TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001)

You are the independent final L2 auditor for a bounded substantive repair (P0-R1) of an
already-existing packet. You have NO prior context from the implementer. You must reach your own
verdict from the actual repository content at the frozen head.

## Audit target (frozen substantive content head)

- Repo root: `/Users/hue/code/_worktrees/mcp-multiproject-p0`
- CONTENT_HEAD_SHA: `4e72a976eec6be3e990b519cacfbaa95088d1a9f`
- CONTENT_TREE: `7e57c6f3d711813d90dc59cbeff292d48af47c19`
- PR base (main): `04be55535d1582c304cf31a02923fb9c521ab547`
- Full changed-paths list (vs base): see DIFF_NAME_STATUS.txt

Inspect the frozen head content and the diff from the PR base. Run deterministic checks where you can
(e.g. `python -m jsonschema`, `pytest`, `shasum -a 256`). Then emit your verdict.

## Required verdict shape

Return exactly one of:
- `PASS` — acceptable, no blocking findings
- `PASS_WITH_RISKS` — acceptable with non-blocking risks
- `FAIL` — blocking defect(s) found
- `NEEDS_SUPERVISOR` — cannot determine / identity unknown / head mismatch

Then list every finding (id, severity, title, status, body). A finding status is
OPEN / RESOLVED / ACCEPTED_RISK.

## You MUST challenge at least the following (P0-R1-10)

1. path / CWD / env / clientInfo / session authority creep — aliases may never become authority.
2. mutable routing under UNKNOWN / CONFLICTING identity — must be forced false.
3. fifth sharing class or `multi_project_singleton` — must be rejected.
4. lease and ownership laundering — endpoint/ownership evidence must not self-promote.
5. global runner-config rewrite — `shared_global_config_mutated` must always be false and authority PROVENANCE_ONLY.
6. ConPort Wave 2 leakage — must remain unauthorized.
7. dope-memory and Serena target drift — dope-memory V1=PROJECT_SCOPED, Serena V1=WORKTREE_SCOPED.
8. P5-before-P4 ordering — redis-events PROJECT_SCOPED must precede dope-memory consolidation.
9. R2 topology / falsification binding — topology full-file hash `df863698...`,
   falsification post-frontmatter payload hash `84b6e68...`.
10. accidental runtime effect — no runtime/service/catalog v1 path may change.
11. schema under-specification / acceptance of malformed authority-shaped fixtures.

## Key artifacts to inspect at the frozen head

- `schemas/mcp/*.schema.json` (fleet-catalog-v2, service-topology, ownership-evidence,
  service-lease-v2, runner-materialization-receipt, project-event-envelope,
  resolved-execution-identity)
- `tests/arch/test_mcp_multiproject_contracts.py`
- `docs/03-reference/mcp/multiproject-service-topology.json`
- `docs/03-reference/mcp/multiproject-falsification-contract.md`
- `docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`
- `task-packets/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001.json`
- `proof/TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001/implementation-notes.md`
