---
id: gpt55-mcp-architecture-branch-work-audit
title: GPT55 MCP Architecture Branch Work Audit
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Branch evidence audit for GPT-5.5 MCP architecture packet.
---
# Branch Work Audit

## Branch: `claude/trusting-engelbart-d2fbfe`

Status for this packet:

- OBSERVED: branch exists locally.
- OBSERVED: merge-base with `origin/main` is `0805dae06d45745011d4df2a8946ba1fbda34bb3`.
- OBSERVED: `git branch --contains claude/trusting-engelbart-d2fbfe --all` includes `main`, `origin/main`, `claude/mcp-fleet-audit-complete`, and this Codex packet branch.
- CONCLUSION: Treat its main design/audit work as already merged into the current baseline.

Key work observed from branch history and docs:

- `2074db821 docs(mcp): add MCP fleet canonical audit + target-state design`
- `6c1d8d542 fix(hooks): emit promotable error.encountered capture from PostToolUseFailure`
- `4974015c3 fix(conport): fail closed on unverifiable schema post-apply check`
- `36b619af9 fix(mcp): replace fake healthchecks for pal and dope-context`
- `32d246e8f fix(mcp): remove duplicate registry.yaml keys that silently disabled servers`
- `ebd42d502 feat(mcp): add ensure-pal.sh for the off-compose pal-mcp-server container`
- `689aba1f4 feat(mcp): add fleet ensure command (#997)`
- `f3577303a feat(mcp): declare fleet server personalities (#999)`
- `d61e63141 feat(dcp): expose read-only facade packet tools (#1000)`
- `8f71ab9af chore(mcp): quarantine dead fleet surfaces (#1001)`

Primary design source:

- `claudedocs/mcp-fleet-canonical-audit-and-target-design-2026-07-03.md`

Design notes to preserve:

- shadow-twin syndrome is the central architecture pathology.
- one catalog/generated-output model is the preferred control plane.
- DCP facade read-only envelope is the pattern to generalize.
- Memory Trinity boundaries must not be weakened by feature resurrection.

## Branch: `claude/mcp-fleet-audit-complete`

Status for this packet:

- OBSERVED: branch exists locally and remotely as `origin/claude/mcp-fleet-audit-complete`.
- OBSERVED: merge-base with `origin/main` is `8f71ab9aff4802fb15d406fe654c6c601893cc42`.
- CONCLUSION: Treat this branch as follow-on work after current `origin/main`, not as baseline truth until merged.

Commits ahead of `origin/main`:

```text
baeeeb38e fix(mcp): recreate keyless pal-mcp-server once .env appears
071de6a25 docs(mcp): add forgotten-features archaeology addendum
2719d3e26 chore(mcp): retire the exa MCP server (ADR-223)
57f6d12ec fix(mcp): tag-correct PAL bootstrap hint + resolve RTE capture against workspace
4a4df828b fix(mcp): give compose-up a build-inclusive timeout budget in ensure --full
6ac711e6c fix(mcp): build docker-run args cleanly + start consumed pal-stdio in ensure
c7e58a1e9 fix(mcp): ensure-pal verifies restarted container stayed up + correct build hint
08e298a2e test/fix: address Copilot review — hermetic ledger, off-loop capture, lint
7948f53c7 fix(mcp): enforce personality contract on all servers + lock in dead-surface quarantine
bee847935 fix(memory): make PM source events promotion-capable (unblock event-bus fan-out)
aa2510a55 fix(mcp): harden `mcp ensure` — ensure Codex's off-compose PAL, bound timeouts, lifecycle filter
```

Diff status versus `origin/main`:

```text
A claudedocs/mcp-fleet-forgotten-features-addendum-2026-07-04.md
M compose.yml
D docker/mcp-servers-source/exa/Dockerfile
D docker/mcp-servers-source/exa/README.md
D docker/mcp-servers-source/exa/exa_server.py
D docker/mcp-servers-source/exa/requirements.txt
A docs/90-adr/adr-223-retire-exa-mcp-server.md
M mcp_catalog.yaml
M proof/dmx-mcp-fleet-roadmap/TP-DMX-MCP-FLEET-ROADMAP-007-DEAD-SURFACE-QUARANTINE/implementation-notes.md
M scripts/mcp-wrappers/ensure-pal.sh
D services/mcp-integration-bridge/Dockerfile
M services/registry.yaml
M src/dopemux/adhd/rte_adapter.py
M src/dopemux/commands/mcp_commands.py
M src/dopemux/mcp/default_catalog.yaml
M src/dopemux/mcp/fleet_catalog.py
M src/dopemux/pm/api.py
M src/dopemux/pm/writes.py
M tests/arch/test_mcp_fleet_catalog_contract.py
M tests/unit/test_mcp_commands_catalog.py
M tests/unit/test_mcp_fleet_catalog.py
M tests/unit/test_memory_capture_client.py
A tests/unit/test_pm_source_events.py
```

Architecture questions raised by this branch:

- Should Exa be retired, as ADR-223 proposes, or should the earlier wire-or-retire decision be reopened?
- Should PAL remain off-compose but managed by `ensure-pal.sh`, or move into a first-class compose/catalog lifecycle?
- Should PM source events be promoted through the memory spine as branch work implies, and what canonical writer owns the resulting task/workflow events?
- Which dead surfaces should be source-deleted, archived, or merely excluded from generated outputs?
- Does the stricter personality contract apply to every fleet server or only pinned high-risk servers?
