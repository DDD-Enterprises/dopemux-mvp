# TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001

## Identity

```text
PACKET_ID=TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001
PROGRAM=DMX-MCP-MULTIPROJECT
REPOSITORY=DDD-Enterprises/dopemux-mvp
RISK_LANE=L2
STAGE=IMPLEMENTATION_CONTRACT_FREEZE
DEPENDENCY=G0_RATIFIED
R2_PACKAGE_SHA256=fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996
```

## Objective

Freeze the ratified R2 identity, sharing-class, service-topology, lease, ownership, event-namespace,
runner-materialization and protocol-independence contracts as strict design-only schemas and static tests.

## IN

- exact packet/ADR/reference publication paths listed in `01_TASK_PACKET.json`;
- design-only schemas under `schemas/mcp/*v2*` and the named new schema files;
- one architecture test file;
- final proof/audit artifacts after substantive content freeze.

## OUT

- runtime identity implementation;
- current `mcp_catalog.yaml` or bundled v1 catalog mutation;
- MCP CLI or renderer implementation;
- lease allocator implementation;
- any service code, compose, Docker, Redis, database or runner-global config mutation;
- ConPort Wave 2;
- Task Orchestrator project-scope implementation;
- dope-memory/redis-events/Serena topology migration;
- MCP SDK upgrade;
- merge or activation.

## Execution recommendation

```yaml
execution_recommendation:
  stage: implementation
  runner:
    preferred: Codex CLI
    availability: UNKNOWN
  agent:
    logical_role: bounded P0 contract implementer
    custom_agent: null
    authority_ceiling: exact P0 allowlist; contracts only; no runtime/service mutation
  model:
    preferred: UNKNOWN
    effort: high
  fallback:
    runner: null
    model: null
    trigger: requested implementer route unavailable or identity unproven
  audit:
    required: true
    runner: live-discovered independent route
    model: UNKNOWN
    independence: UNKNOWN
```

The `execution.agent="codex"` value in the machine packet is the current Task Packet logical agent class.
It is not a claim that a specific Codex model or authenticated runtime is currently available.

## Governing authority

- operator G0 ratification reported at `2026-09-03T20:42:12-07:00`;
- ratified R2 package SHA-256 `fa78556b2d51cd3b22d8c42ff36bd6c3964172ddee6a75662cde61db438e3996`;
- current accepted ConPort CRS v2 stable-identity boundary;
- current Task Packet and proof/audit governance;
- current runtime/source remains evidence and must not be silently rewritten by this contract packet.

## Allowed files

The machine-readable exact allowlist in `01_TASK_PACKET.json` is authoritative for this packet.

## Forbidden files and surfaces

At minimum:

```text
mcp_catalog.yaml
src/dopemux/mcp/**
src/dopemux/commands/mcp_commands.py
services/**
docker/**
compose.yml
compose.*.yml
.mcp.json
uv.lock
poetry.lock
package-lock.json
~/.claude.json
~/.codex/**
~/.config/opencode/**
live Docker/container state
live Redis/database state
live lease registry
```

If a required semantic fix needs a forbidden runtime path, stop P0 and return to the supervisor. Do not
widen the packet in place.

## Validation gates

1. Task Packet schema validation.
2. Focused `tests/arch/test_mcp_multiproject_contracts.py`.
3. Relevant complete MCP catalog/runtime-registry suite.
4. Exact source hashes for R2 topology and falsification reference.
5. Exact changed-file allowlist and forbidden-path check.
6. `git diff --check`.
7. Changed-file pre-commit.
8. Secret scan for changed/proof output.
9. One final independent L2 audit on the frozen substantive head.
10. Current exact-head proof/finality and PR Steward.
11. Stop for operator merge decision.

## Repair budget

One bounded substantive repair is permitted if the final audit identifies a fix inside the existing P0
authority and file allowlist. Then freeze a new content head and perform one new final independent audit.
Deterministic packaging/schema/frontmatter fixes stay in the active packet and do not create packet
recursion.

## Return block

```text
PACKET_ID=TP-DMX-MCP-MULTIPROJECT-P0-IDENTITY-SHARING-CONTRACT-001
RETURN_STATUS=PASS_P0_FROZEN_FOR_OPERATOR_MERGE_DECISION|BLOCKED_P0_<REASON>|FAIL_P0_<REASON>
BASE_MAIN_SHA=${RUNTIME_SHA}
CONTENT_HEAD_SHA=${RUNTIME_SHA}
CONTENT_TREE=${RUNTIME_SHA}
ALLOWED_FILE_COUNT=25
FOCUSED_TESTS=${RUNTIME_RESULT}
RELEVANT_SUITE=${RUNTIME_RESULT}
FINAL_INDEPENDENT_AUDIT=${RUNTIME_VERDICT}
AUDITOR_IDENTITY=${RUNTIME_IDENTITY_OR_UNKNOWN}
PROOF_VALIDATION=${RUNTIME_RESULT}
PR_STEWARD=${RUNTIME_RESULT}
REPOSITORY_MUTATION=ALLOWLIST_ONLY
RUNTIME_MUTATION=NONE
CONPORT_WAVE2_AUTHORIZED=NO
MERGE_AUTHORIZED=NO
ACTIVATION_AUTHORIZED=NO
NEXT_GATE=OPERATOR_MERGE_DECISION_OR_BOUNDED_REPAIR
```
